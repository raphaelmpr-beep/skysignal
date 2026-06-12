"""
Admin router — /api/admin
Review queue and incident management.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import AuditLog, Incident, User
from app.schemas import IncidentListItem, IncidentRead
from app.services.confidence_service import ConfidenceService
from app.services.gdelt_service import GDELTService

router = APIRouter()
conf_svc = ConfidenceService()
gdelt_svc = GDELTService()

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

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)

    date_from = start_dt.strftime("%Y%m%d%H%M%S")
    date_to = end_dt.strftime("%Y%m%d%H%M%S")

    results = gdelt_svc.search(
        query=query,
        date_from=date_from,
        date_to=date_to,
        limit=max_records,
    )
    incident_ids = gdelt_svc.create_candidate_incidents(
        results=results,
        org_id=current_user["org_id"],
        db=db,
    )

    log = AuditLog(
        org_id=current_user["org_id"],
        user_id=_audit_user_id_or_none(db, current_user),
        action="INGEST_GDELT",
        entity_type="incident",
        entity_id=incident_ids[0] if incident_ids else None,
        details={
            "query": query,
            "days": days,
            "max_records": max_records,
            "date_from": date_from,
            "date_to": date_to,
            "fetched": len(results),
            "created": len(incident_ids),
        },
    )
    db.add(log)
    db.commit()

    return {
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
        "incident_ids": incident_ids,
    }
