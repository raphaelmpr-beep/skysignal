"""
Evidence router — match candidates + analyst link/unlink actions.

GET  /evidence/match-candidates/{incident_id}
     Returns ranked candidate incidents that likely describe the same event
     as a given unconfirmed evidence item, scored by the 6-attribute
     official_validation_service match algorithm.

POST /evidence/link
     Analyst confirms two evidence items describe the same incident.
     Upgrades DISCOVERY → CORROBORATION, inserts the new evidence,
     and triggers ConfidenceService.recompute().

POST /evidence/unlink/{evidence_id}
     Removes a previously linked evidence item and recomputes.

GET  /evidence/{incident_id}
     All evidence rows for an incident.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_org_id
from app.models import Incident, IncidentEvidence, Source
from app.services.confidence_service import ConfidenceService
from app.services.official_validation_service import SCORE_WEIGHTS

router = APIRouter(prefix="/evidence", tags=["evidence"])

_confidence_svc = ConfidenceService()


# ── Pydantic schemas ────────────────────────────────────────────────────────

class LinkEvidenceRequest(BaseModel):
    """Analyst confirms that a news/GDELT item describes an existing incident."""
    incident_id: str          # target incident to attach evidence to
    source_id: Optional[str] = None
    role: str                 # CORROBORATION | OFFICIAL_CONFIRMATION | DISCOVERY
    title: Optional[str] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None
    # If supplied, this is the raw credibility score override for this evidence item
    credibility_score_override: Optional[int] = None


class MatchCandidate(BaseModel):
    incident_id: str
    title: str
    occurred_at: Optional[datetime]
    location_name: Optional[str]
    city: Optional[str]
    region: Optional[str]
    incident_type: str
    confidence_score: int
    confidence_tier: str
    match_score: int           # 0-100 how well it matches the query
    match_breakdown: dict      # per-attribute scores


# ── Helpers ─────────────────────────────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in metres between two lat/lon points."""
    import math
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _score_match(candidate: Incident, query: dict) -> tuple[int, dict]:
    """
    Score how well `candidate` matches the query attributes.
    query keys: occurred_at, latitude, longitude, location_name,
                city, region, incident_type, summary
    Returns (total_score 0-100, breakdown dict).
    """
    breakdown = {k: 0 for k in SCORE_WEIGHTS}
    score = 0

    # Date match
    q_date = query.get("occurred_at")
    if q_date and candidate.occurred_at:
        if isinstance(q_date, str):
            try:
                q_date = datetime.fromisoformat(q_date)
            except ValueError:
                q_date = None
        if q_date:
            if q_date.tzinfo is None:
                q_date = q_date.replace(tzinfo=timezone.utc)
            diff = abs((candidate.occurred_at - q_date).total_seconds())
            if diff < 86_400:       # same day
                pts = SCORE_WEIGHTS["date_match"]
            elif diff < 604_800:    # within 7 days
                pts = SCORE_WEIGHTS["date_match"] // 2
            else:
                pts = 0
            score += pts
            breakdown["date_match"] = pts

    # Location match (lat/lon)
    q_lat, q_lon = query.get("latitude"), query.get("longitude")
    c_lat, c_lon = candidate.latitude, candidate.longitude
    if q_lat and q_lon and c_lat and c_lon:
        try:
            dist = _haversine(float(q_lat), float(q_lon), float(c_lat), float(c_lon))
            if dist < 1_000:
                pts = SCORE_WEIGHTS["location_match"]
            elif dist < 5_000:
                pts = SCORE_WEIGHTS["location_match"] // 2
            elif dist < 25_000:
                pts = SCORE_WEIGHTS["location_match"] // 4
            else:
                pts = 0
            score += pts
            breakdown["location_match"] = pts
        except Exception:
            pass

    # Location match fallback — city/region text
    if breakdown["location_match"] == 0:
        q_city   = (query.get("city") or "").lower().strip()
        q_region = (query.get("region") or "").lower().strip()
        c_city   = (candidate.city or "").lower().strip()
        c_region = (candidate.region or "").lower().strip()
        if q_city and c_city and q_city == c_city:
            pts = SCORE_WEIGHTS["location_match"] // 2
            score += pts
            breakdown["location_match"] = pts
        elif q_region and c_region and q_region == c_region:
            pts = SCORE_WEIGHTS["location_match"] // 4
            score += pts
            breakdown["location_match"] = pts

    # Facility match — location_name substring
    q_loc = (query.get("location_name") or "").lower()
    c_loc = (candidate.location_name or "").lower()
    if q_loc and c_loc:
        if q_loc in c_loc or c_loc in q_loc:
            pts = SCORE_WEIGHTS["facility_match"]
            score += pts
            breakdown["facility_match"] = pts

    # Incident type match
    q_type = (query.get("incident_type") or "").upper()
    c_type = (str(candidate.incident_type) if candidate.incident_type else "").upper()
    if q_type and c_type and q_type == c_type:
        pts = SCORE_WEIGHTS["incident_type_match"]
        score += pts
        breakdown["incident_type_match"] = pts

    # Jurisdiction match
    q_region2 = (query.get("region") or "").lower()
    if q_region2 and c_region and q_region2 == c_region:
        pts = SCORE_WEIGHTS["jurisdiction_match"]
        score += pts
        breakdown["jurisdiction_match"] = pts

    # Named entity match — check summary overlap
    q_summary = (query.get("summary") or "").lower()
    c_summary = (candidate.summary or "").lower()
    if q_summary and c_summary:
        # Look for shared tokens ≥ 5 chars (avoids stopword matches)
        q_tokens = {t for t in q_summary.split() if len(t) >= 5}
        c_tokens = {t for t in c_summary.split() if len(t) >= 5}
        if q_tokens & c_tokens:
            pts = SCORE_WEIGHTS["named_entity_match"]
            score += pts
            breakdown["named_entity_match"] = pts

    return min(score, 100), breakdown


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("/match-candidates/{incident_id}", response_model=list[MatchCandidate])
def get_match_candidates(
    incident_id: str,
    limit: int = 10,
    min_score: int = 40,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
):
    """
    For a PENDING incident, find existing APPROVED incidents that likely
    describe the same event. Returns candidates ranked by match_score desc.

    Uses the 6-attribute scoring algorithm:
      date(25) + location(25) + facility(20) + type(15) + jurisdiction(10) + entity(5)
    """
    # Load the query incident
    query_inc = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.organization_id == org_id)
        .first()
    )
    if not query_inc:
        raise HTTPException(404, "Incident not found")

    # Build query dict from the incident attributes
    query_attrs = {
        "occurred_at":     query_inc.occurred_at,
        "latitude":        query_inc.latitude,
        "longitude":       query_inc.longitude,
        "location_name":   query_inc.location_name,
        "city":            query_inc.city,
        "region":          query_inc.region,
        "incident_type":   str(query_inc.incident_type) if query_inc.incident_type else None,
        "summary":         query_inc.summary,
    }

    # Narrow the search window: ±30 days, same region if available
    window_start = None
    window_end   = None
    if query_inc.occurred_at:
        window_start = query_inc.occurred_at - timedelta(days=30)
        window_end   = query_inc.occurred_at + timedelta(days=30)

    candidates_q = db.query(Incident).filter(
        Incident.organization_id == org_id,
        Incident.id != incident_id,
        Incident.review_status == "APPROVED",
    )
    if window_start and window_end:
        candidates_q = candidates_q.filter(
            Incident.occurred_at >= window_start,
            Incident.occurred_at <= window_end,
        )
    if query_inc.region:
        candidates_q = candidates_q.filter(Incident.region == query_inc.region)

    candidates = candidates_q.limit(500).all()  # score top 500 in window

    # Score each candidate
    results: list[MatchCandidate] = []
    for cand in candidates:
        match_score, breakdown = _score_match(cand, query_attrs)
        if match_score >= min_score:
            results.append(
                MatchCandidate(
                    incident_id=str(cand.id),
                    title=cand.title or "",
                    occurred_at=cand.occurred_at,
                    location_name=cand.location_name,
                    city=cand.city,
                    region=cand.region,
                    incident_type=str(cand.incident_type) if cand.incident_type else "UNKNOWN",
                    confidence_score=cand.confidence_score or 0,
                    confidence_tier=str(cand.confidence_tier) if cand.confidence_tier else "UNVERIFIED",
                    match_score=match_score,
                    match_breakdown=breakdown,
                )
            )

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[:limit]


@router.post("/link")
def link_evidence(
    req: LinkEvidenceRequest,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
):
    """
    Analyst confirms this evidence describes an existing incident.
    Steps:
      1. Verify incident belongs to org
      2. Duplicate check — same URL or source_id already linked?
      3. If role is CORROBORATION or OFFICIAL_CONFIRMATION:
         upgrade existing DISCOVERY rows to CORROBORATION
      4. Insert new evidence row
      5. Recompute incident confidence
    """
    # Validate incident
    inc = (
        db.query(Incident)
        .filter(Incident.id == req.incident_id, Incident.organization_id == org_id)
        .first()
    )
    if not inc:
        raise HTTPException(404, "Incident not found")

    role = req.role.upper()
    valid_roles = {"DISCOVERY", "CORROBORATION", "OFFICIAL_CONFIRMATION",
                   "CONTRADICTION", "DUPLICATE", "REJECTION_SUPPORT"}
    if role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be one of: {valid_roles}")

    # Duplicate detection
    is_dup = _confidence_svc.check_duplicate(
        req.incident_id, req.url, req.source_id, db
    )
    if is_dup:
        role = "DUPLICATE"

    # Upgrade DISCOVERY → CORROBORATION if this is a confirming role
    upgraded = 0
    if role in ("CORROBORATION", "OFFICIAL_CONFIRMATION") and not is_dup:
        upgraded = _confidence_svc.upgrade_discovery_to_corroboration(
            req.incident_id, db
        )

    # Resolve credibility score from source
    credibility = req.credibility_score_override
    if credibility is None and req.source_id:
        src = db.query(Source).filter(Source.id == req.source_id).first()
        credibility = src.credibility_score if src else 40
    if credibility is None:
        credibility = 40

    # Insert evidence
    ev = IncidentEvidence(
        id=str(uuid.uuid4()),
        incident_id=req.incident_id,
        source_id=req.source_id,
        role=role,
        title=req.title,
        url=req.url,
        excerpt=req.excerpt,
        published_at=req.published_at,
        credibility_score=credibility,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # Recompute confidence
    new_score = _confidence_svc.recompute(req.incident_id, db)

    return {
        "evidence_id": str(ev.id),
        "role_assigned": role,
        "discovery_rows_upgraded": upgraded,
        "new_confidence_score": new_score,
        "new_confidence_tier": db.query(Incident)
            .filter(Incident.id == req.incident_id)
            .first()
            .confidence_tier,
        "was_duplicate": is_dup,
    }


@router.delete("/unlink/{evidence_id}")
def unlink_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
):
    """Remove a linked evidence row and recompute confidence."""
    ev = db.query(IncidentEvidence).filter(IncidentEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(404, "Evidence not found")

    # Verify org ownership via incident
    inc = (
        db.query(Incident)
        .filter(Incident.id == ev.incident_id, Incident.organization_id == org_id)
        .first()
    )
    if not inc:
        raise HTTPException(403, "Not authorized")

    incident_id = str(ev.incident_id)
    db.delete(ev)
    db.commit()

    new_score = _confidence_svc.recompute(incident_id, db)
    return {"deleted": evidence_id, "new_confidence_score": new_score}


@router.get("/{incident_id}")
def get_evidence(
    incident_id: str,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
):
    """All evidence rows for an incident, with source metadata."""
    inc = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.organization_id == org_id)
        .first()
    )
    if not inc:
        raise HTTPException(404, "Incident not found")

    evidences = (
        db.query(IncidentEvidence)
        .filter(IncidentEvidence.incident_id == incident_id)
        .order_by(IncidentEvidence.created_at)
        .all()
    )

    source_ids = [e.source_id for e in evidences if e.source_id]
    sources_by_id = {}
    if source_ids:
        sources_by_id = {
            s.id: s
            for s in db.query(Source).filter(Source.id.in_(source_ids)).all()
        }

    result = []
    for ev in evidences:
        src = sources_by_id.get(ev.source_id) if ev.source_id else None
        result.append({
            "id": str(ev.id),
            "role": ev.role,
            "title": ev.title,
            "url": ev.url,
            "excerpt": ev.excerpt,
            "published_at": ev.published_at,
            "credibility_score": ev.credibility_score,
            "official_match_score": ev.official_match_score,
            "source": {
                "id": str(src.id) if src else None,
                "name": src.name if src else None,
                "source_type": src.source_type if src else None,
                "credibility_score": src.credibility_score if src else None,
                "is_official": src.is_official if src else False,
            } if src else None,
            "created_at": ev.created_at,
        })

    return {
        "incident_id": incident_id,
        "evidence_count": len(result),
        "confidence_score": inc.confidence_score,
        "confidence_tier": inc.confidence_tier,
        "evidence": result,
    }
