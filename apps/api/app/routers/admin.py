"""
Admin router — /api/admin
Review queue and incident management.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import SessionLocal, get_db
from app.models import AuditLog, Incident, Organization, User
from app.schemas import IncidentListItem, IncidentRead
from app.services.confidence_service import ConfidenceService
from app.services.gdelt_service import GDELTService
from app.services.rss_fallback_service import RSSFallbackService

router = APIRouter()
conf_svc = ConfidenceService()
gdelt_svc = GDELTService()
rss_svc = RSSFallbackService()


@dataclass
class CacheEntry:
    expires_at: datetime
    payload: dict


INGEST_CACHE: dict[str, CacheEntry] = {}


def _env_int(name: str, default: int, *, min_value: int, max_value: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(min_value, min(value, max_value))


def _bool_env(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _cache_key(org_id: str, query: str, days: int, max_records: int) -> str:
    return f"{org_id}:{query.lower()}:{days}:{max_records}"


def _cache_get(key: str) -> dict | None:
    entry = INGEST_CACHE.get(key)
    if not entry:
        return None
    if datetime.now(timezone.utc) >= entry.expires_at:
        INGEST_CACHE.pop(key, None)
        return None
    return entry.payload


def _cache_set(key: str, payload: dict, ttl_seconds: int) -> None:
    INGEST_CACHE[key] = CacheEntry(
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        payload=payload,
    )

VALID_REVIEW_ACTIONS = {
    "approve": "VERIFIED",
    "reject": "DISMISSED",
    "merge_duplicate": "DISMISSED",
    "request_more_review": "NEEDS_REVIEW",
}


def _audit_user_id_or_none(db: Session, current_user: dict) -> str | None:
    """Return a valid user_id for audit logs, otherwise None."""
    user_id = current_user.get("user_id")
    if not user_id:
        return None
    exists = db.query(User.id).filter(User.id == user_id).first()
    return user_id if exists else None


def _latest_ingest_log(db: Session, org_id: str) -> AuditLog | None:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.org_id == org_id,
            or_(
                AuditLog.action == "INGEST_GDELT",
                AuditLog.action == "INGEST_GDELT_FALLBACK",
                AuditLog.action == "INGEST_GDELT_SCHEDULED",
            ),
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )


def _ingest_for_org(
    *,
    db: Session,
    org_id: str,
    user_id: str | None,
    query: str,
    days: int,
    max_records: int,
    source_action: str,
    force: bool = False,
) -> dict:
    cooldown_seconds = _env_int("GDELT_INGEST_COOLDOWN_SECONDS", 600, min_value=60, max_value=86400)
    cache_ttl_seconds = _env_int("GDELT_INGEST_CACHE_TTL_SECONDS", 900, min_value=60, max_value=86400)
    key = _cache_key(org_id=org_id, query=query, days=days, max_records=max_records)
    now = datetime.now(timezone.utc)

    if not force:
        latest = _latest_ingest_log(db=db, org_id=org_id)
        if latest and latest.created_at and (now - latest.created_at).total_seconds() < cooldown_seconds:
            cached = _cache_get(key)
            if cached:
                return {
                    **cached,
                    "cooldown_active": True,
                    "cooldown_seconds": cooldown_seconds,
                    "served_from_cache": True,
                    "scheduled": source_action == "INGEST_GDELT_SCHEDULED",
                }
            return {
                "query": query,
                "days": days,
                "max_records": max_records,
                "fetched": 0,
                "created": 0,
                "incident_ids": [],
                "upstream_status_code": None,
                "upstream_error": "Ingest cooldown active",
                "rate_limited": False,
                "provider_used": "cooldown",
                "cooldown_active": True,
                "cooldown_seconds": cooldown_seconds,
                "served_from_cache": False,
                "scheduled": source_action == "INGEST_GDELT_SCHEDULED",
            }

    end_dt = now
    start_dt = end_dt - timedelta(days=days)
    date_from = start_dt.strftime("%Y%m%d%H%M%S")
    date_to = end_dt.strftime("%Y%m%d%H%M%S")

    gdelt_results = gdelt_svc.search(
        query=query,
        date_from=date_from,
        date_to=date_to,
        limit=max_records,
    )

    # Always run RSS feeds in parallel — not just as fallback.
    # This maximizes coverage: GDELT provides structured geo-tagged articles,
    # RSS provides specialist defense/UAS publications with higher precision.
    rss_results = rss_svc.search(query=query, days=days, limit=max(10, min(max_records, 75)))

    if gdelt_results and rss_results:
        # Deduplicate by URL before merging
        seen = {r["url"] for r in gdelt_results}
        unique_rss = [r for r in rss_results if r.get("url") not in seen]
        results = gdelt_results + unique_rss
        provider_used = "gdelt+rss"
    elif gdelt_results:
        results = gdelt_results
        provider_used = "gdelt"
    elif rss_results:
        results = rss_results
        provider_used = "rss_multi"
    else:
        results = []
        provider_used = "none"

    incident_ids = gdelt_svc.create_candidate_incidents(
        results=results,
        org_id=org_id,
        db=db,
    )

    response_payload = {
        "query": query,
        "days": days,
        "max_records": max_records,
        "date_from": date_from,
        "date_to": date_to,
        "fetched": len(results),
        "created": len(incident_ids),
        "upstream_status_code": gdelt_svc.last_status_code,
        "upstream_error": gdelt_svc.last_error,
        "rate_limited": gdelt_svc.last_status_code == 429,
        "provider_used": provider_used,
        "incident_ids": incident_ids,
        "cooldown_active": False,
        "cooldown_seconds": cooldown_seconds,
        "served_from_cache": False,
        "scheduled": source_action == "INGEST_GDELT_SCHEDULED",
    }

    log = AuditLog(
        org_id=org_id,
        user_id=user_id,
        action=("INGEST_RSS_MULTI" if provider_used in ("rss_multi", "gdelt+rss") else source_action),
        entity_type="incident",
        entity_id=incident_ids[0] if incident_ids else None,
        details=response_payload,
    )
    db.add(log)
    db.commit()

    _cache_set(key=key, payload=response_payload, ttl_seconds=cache_ttl_seconds)
    return response_payload


def run_scheduled_ingest_cycle() -> dict:
    """Run one scheduled ingest pass across active orgs."""
    if not _bool_env("ENABLE_GDELT_SCHEDULED_INGEST", True):
        return {"enabled": False, "processed_orgs": 0}

    scheduled_days = _env_int("GDELT_SCHEDULED_DAYS", 1, min_value=1, max_value=7)
    scheduled_max_records = _env_int("GDELT_SCHEDULED_MAX_RECORDS", 25, min_value=5, max_value=100)
    scheduled_query = (
        os.getenv("GDELT_SCHEDULED_QUERY")
        or "drone OR uav OR unmanned aircraft OR quadcopter OR counter-UAS"
    ).strip()

    db = SessionLocal()
    try:
        org_ids = [r[0] for r in db.query(Organization.id).filter(Organization.is_active == True).all()]
        processed = 0
        for org_id in org_ids:
            _ingest_for_org(
                db=db,
                org_id=org_id,
                user_id=None,
                query=scheduled_query,
                days=scheduled_days,
                max_records=scheduled_max_records,
                source_action="INGEST_GDELT_SCHEDULED",
                force=False,
            )
            processed += 1

        return {
            "enabled": True,
            "processed_orgs": processed,
            "query": scheduled_query,
            "days": scheduled_days,
            "max_records": scheduled_max_records,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Review queue
# ---------------------------------------------------------------------------

@router.get("/review-queue", response_model=dict)
def review_queue(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(Incident).filter(
        Incident.org_id == org_id,
        Incident.review_status == "PENDING",
    )
    total = q.count()
    items = q.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [IncidentListItem.model_validate(i) for i in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Review action
# ---------------------------------------------------------------------------

@router.post("/review/{incident_id}", response_model=IncidentRead)
def review_incident(
    incident_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    action = (body.get("action") or "").lower()
    if action not in VALID_REVIEW_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Valid: {sorted(VALID_REVIEW_ACTIONS)}",
        )

    inc = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.org_id == current_user["org_id"],
        )
        .first()
    )
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    new_status = VALID_REVIEW_ACTIONS[action]
    inc.review_status = new_status
    notes = body.get("notes", "")

    # For merge_duplicate, record the duplicate_of_id
    details: dict = {"action": action, "new_status": new_status}
    if action == "merge_duplicate" and body.get("duplicate_of_id"):
        details["duplicate_of_id"] = body["duplicate_of_id"]
    if notes:
        details["notes"] = notes

    db.commit()
    db.refresh(inc)

    log = AuditLog(
        org_id=current_user["org_id"],
        user_id=_audit_user_id_or_none(db, current_user),
        incident_id=incident_id,
        action=f"REVIEW_{action.upper()}",
        entity_type="incident",
        entity_id=incident_id,
        details=details,
    )
    db.add(log)
    db.commit()

    return IncidentRead.model_validate(inc)


# ---------------------------------------------------------------------------
# Recompute confidence score
# ---------------------------------------------------------------------------

@router.post("/recompute/{incident_id}")
def recompute_confidence(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    inc = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.org_id == current_user["org_id"],
        )
        .first()
    )
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    new_score = conf_svc.recompute(incident_id=incident_id, db=db)

    log = AuditLog(
        org_id=current_user["org_id"],
        user_id=_audit_user_id_or_none(db, current_user),
        incident_id=incident_id,
        action="RECOMPUTE_CONFIDENCE",
        entity_type="incident",
        entity_id=incident_id,
        details={"new_score": new_score},
    )
    db.add(log)
    db.commit()

    db.refresh(inc)
    return {"incident_id": incident_id, "confidence_score": new_score, "confidence_tier": inc.confidence_tier}


# ---------------------------------------------------------------------------
# GDELT backfill / ingest
# ---------------------------------------------------------------------------

@router.post("/gdelt/ingest", response_model=dict)
def ingest_gdelt(
    body: dict | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    One-click ingestion of recent GDELT events into PENDING incidents.

    Optional body params:
      - days (int, default 7, range 1..30)
      - max_records (int, default 100, range 1..250)
      - query (str, default broad drone query)
    """
    payload = body or {}

    try:
        days = int(payload.get("days", 7))
    except (TypeError, ValueError):
        days = 7
    days = max(1, min(days, 30))

    try:
        max_records = int(payload.get("max_records", 100))
    except (TypeError, ValueError):
        max_records = 100
    max_records = max(1, min(max_records, 250))

    query = str(
        payload.get("query")
        or "drone OR uav OR unmanned aircraft OR quadcopter OR counter-UAS"
    ).strip()

    return _ingest_for_org(
        db=db,
        org_id=current_user["org_id"],
        user_id=_audit_user_id_or_none(db, current_user),
        query=query,
        days=days,
        max_records=max_records,
        source_action="INGEST_GDELT",
        force=bool(payload.get("force", False)),
    )


@router.post("/gdelt/scheduled/run", response_model=dict)
def run_scheduled_for_current_org(
    body: dict | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    payload = body or {}
    days = _env_int("GDELT_SCHEDULED_DAYS", 1, min_value=1, max_value=7)
    max_records = _env_int("GDELT_SCHEDULED_MAX_RECORDS", 25, min_value=5, max_value=100)
    query = (
        str(payload.get("query") or os.getenv("GDELT_SCHEDULED_QUERY") or "drone OR uav")
        .strip()
    )

    return _ingest_for_org(
        db=db,
        org_id=current_user["org_id"],
        user_id=_audit_user_id_or_none(db, current_user),
        query=query,
        days=days,
        max_records=max_records,
        source_action="INGEST_GDELT_SCHEDULED",
        force=bool(payload.get("force", False)),
    )


@router.get("/gdelt/scheduled/status", response_model=dict)
def scheduled_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    cooldown_seconds = _env_int("GDELT_INGEST_COOLDOWN_SECONDS", 600, min_value=60, max_value=86400)
    cache_ttl_seconds = _env_int("GDELT_INGEST_CACHE_TTL_SECONDS", 900, min_value=60, max_value=86400)
    latest = _latest_ingest_log(db=db, org_id=current_user["org_id"])
    now = datetime.now(timezone.utc)
    cooldown_remaining = 0
    if latest and latest.created_at:
        elapsed = (now - latest.created_at).total_seconds()
        if elapsed < cooldown_seconds:
            cooldown_remaining = int(cooldown_seconds - elapsed)

    return {
        "enabled": _bool_env("ENABLE_GDELT_SCHEDULED_INGEST", True),
        "scheduled_interval_seconds": _env_int("GDELT_SCHEDULE_INTERVAL_SECONDS", 900, min_value=60, max_value=86400),
        "scheduled_days": _env_int("GDELT_SCHEDULED_DAYS", 1, min_value=1, max_value=7),
        "scheduled_max_records": _env_int("GDELT_SCHEDULED_MAX_RECORDS", 25, min_value=5, max_value=100),
        "cooldown_seconds": cooldown_seconds,
        "cooldown_remaining_seconds": cooldown_remaining,
        "cache_ttl_seconds": cache_ttl_seconds,
        "last_ingest_at": latest.created_at if latest else None,
        "last_ingest_action": latest.action if latest else None,
    }


@router.get("/feeds/status", response_model=dict)
def feeds_status(
    current_user: dict = Depends(get_current_user),
):
    """Check health of all configured news feed sources (GDELT + RSS multi-feed)."""
    import httpx

    # Check GDELT API availability
    gdelt_ok = False
    gdelt_status = None
    try:
        r = httpx.get(
            "https://api.gdeltproject.org/api/v2/doc/doc?query=drone&mode=ArtList&maxrecords=1&format=json",
            timeout=8.0,
            headers={"User-Agent": "SkySignal/1.1"},
        )
        gdelt_status = r.status_code
        gdelt_ok = r.status_code == 200
    except Exception as exc:
        gdelt_status = str(exc)[:80]

    # Check all RSS feeds
    rss_feed_status = rss_svc.get_feed_status()
    rss_ok = sum(1 for f in rss_feed_status if f["ok"])

    return {
        "gdelt": {
            "ok": gdelt_ok,
            "status": gdelt_status,
        },
        "rss_feeds": {
            "total": len(rss_feed_status),
            "ok": rss_ok,
            "feeds": rss_feed_status,
        },
        "summary": f"GDELT: {'✓' if gdelt_ok else '✗'} | RSS: {rss_ok}/{len(rss_feed_status)} feeds healthy",
    }
