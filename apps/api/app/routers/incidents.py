"""
Incidents router — /api/incidents
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, and_, cast, or_, text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import AuditLog, Incident, IncidentEvidence, Source
from app.schemas import (
    EvidenceCreate,
    EvidenceRead,
    IncidentCreate,
    IncidentListItem,
    IncidentRead,
    IncidentUpdate,
)

router = APIRouter()

MILES_TO_METERS = 1609.34

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_ACTIONS = {"verify", "dismiss", "escalate", "needs_review"}
ACTION_STATUS_MAP = {
    "verify": "VERIFIED",
    "dismiss": "DISMISSED",
    "escalate": "ESCALATED",
    "needs_review": "NEEDS_REVIEW",
}


def _incident_or_404(incident_id: str, org_id: str, db: Session) -> Incident:
    inc = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.org_id == org_id)
        .first()
    )
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


# ---------------------------------------------------------------------------
# List incidents
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_incidents(
    org_id: Optional[str] = None,
    review_status: Optional[str] = None,
    incident_type: Optional[str] = None,
    severity: Optional[str] = None,
    confidence_tier: Optional[str] = None,
    cisa_sector: Optional[str] = None,
    operational_sector: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="ISO date or datetime, e.g. 2024-01-01"),
    date_to: Optional[str] = Query(None, description="ISO date or datetime, e.g. 2024-12-31"),
    search: Optional[str] = None,
    country: Optional[str] = None,
    region: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_miles: Optional[float] = None,
    source_tag: Optional[str] = Query(None, description="Filter by tag: faa/gdelt/osint/dfend/manual"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from datetime import date as date_type
    import re as _re

    def _parse_dt(s: str, end_of_day: bool = False):
        """Accept YYYY-MM-DD or full ISO datetime string."""
        s = s.strip()
        if _re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            d = date_type.fromisoformat(s)
            if end_of_day:
                return datetime(d.year, d.month, d.day, 23, 59, 59)
            return datetime(d.year, d.month, d.day, 0, 0, 0)
        return datetime.fromisoformat(s.replace('Z', '+00:00'))

    effective_org_id = org_id or current_user["org_id"]
    q = db.query(Incident).filter(Incident.org_id == effective_org_id)

    if review_status:
        q = q.filter(Incident.review_status == review_status)
    if incident_type:
        q = q.filter(Incident.incident_type == incident_type)
    if severity:
        q = q.filter(Incident.severity == severity)
    if confidence_tier:
        q = q.filter(Incident.confidence_tier == confidence_tier)
    if cisa_sector:
        q = q.filter(Incident.cisa_sector == cisa_sector)
    if operational_sector:
        q = q.filter(Incident.operational_sector == operational_sector)
    if country:
        q = q.filter(Incident.country.ilike(country))
    if region:
        # 2-letter abbreviation: exact case-insensitive match
        # Longer string: partial match (full state name)
        if len(region) <= 3:
            q = q.filter(Incident.region.ilike(region))
        else:
            q = q.filter(Incident.region.ilike(f"%{region}%"))
    if date_from:
        q = q.filter(Incident.occurred_at >= _parse_dt(date_from, end_of_day=False))
    if date_to:
        q = q.filter(Incident.occurred_at <= _parse_dt(date_to, end_of_day=True))
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                Incident.title.ilike(pattern),
                Incident.summary.ilike(pattern),
                Incident.location_name.ilike(pattern),
                Incident.city.ilike(pattern),
                Incident.region.ilike(pattern),
            )
        )

    # Source tag filter
    if source_tag:
        TAG_MAP = {"faa": "faa", "gdelt": "gdelt", "osint": "osint", "dfend": "dfend", "manual": "manual-seed"}
        tag = TAG_MAP.get(source_tag.lower(), source_tag.lower())
        if tag == "gdelt":
            # Fallback for historical records where tags may be missing/incomplete.
            q = q.filter(
                or_(
                    text(":tag = ANY(tags)").bindparams(tag=tag),
                    Incident.source_url.ilike("%gdelt%"),
                    Incident.source.has(
                        or_(
                            cast(Source.source_type, String).ilike("GDELT"),
                            Source.name.ilike("%gdelt%"),
                            Source.url.ilike("%gdelt%"),
                        )
                    ),
                )
            )
        else:
            q = q.filter(text(":tag = ANY(tags)").bindparams(tag=tag))

    # Geo filter using bounding box (no PostGIS)
    if lat is not None and lon is not None and radius_miles is not None:
        deg_per_mile = 1.0 / 69.0
        margin = radius_miles * deg_per_mile * 1.2
        q = q.filter(
            Incident.lat.between(lat - margin, lat + margin),
            Incident.lon.between(lon - margin, lon + margin),
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
# Get single incident
# ---------------------------------------------------------------------------

@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    inc = _incident_or_404(incident_id, current_user["org_id"], db)
    return IncidentRead.model_validate(inc)


# ---------------------------------------------------------------------------
# Create incident
# ---------------------------------------------------------------------------

@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident(
    body: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    inc = Incident(
        org_id=current_user["org_id"],
        review_status="PENDING",
        confidence_score=0,
        confidence_tier="UNVERIFIED",
        **body.model_dump(exclude_none=True),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    _log(db, current_user, inc.id, "CREATE_INCIDENT", details={"title": inc.title})
    return IncidentRead.model_validate(inc)


# ---------------------------------------------------------------------------
# Update incident
# ---------------------------------------------------------------------------

@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: str,
    body: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    inc = _incident_or_404(incident_id, current_user["org_id"], db)
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(inc, k, v)
    db.commit()
    db.refresh(inc)
    _log(db, current_user, inc.id, "UPDATE_INCIDENT", details=updates)
    return IncidentRead.model_validate(inc)


# ---------------------------------------------------------------------------
# Add evidence
# ---------------------------------------------------------------------------

@router.post("/{incident_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def add_evidence(
    incident_id: str,
    body: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _incident_or_404(incident_id, current_user["org_id"], db)
    ev = IncidentEvidence(
        incident_id=incident_id,
        **body.model_dump(exclude={"incident_id"}, exclude_none=True),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    _log(db, current_user, incident_id, "ADD_EVIDENCE", details={"evidence_id": ev.id})
    return EvidenceRead.model_validate(ev)


# ---------------------------------------------------------------------------
# Add note
# ---------------------------------------------------------------------------

@router.post("/{incident_id}/notes", status_code=status.HTTP_201_CREATED)
def add_note(
    incident_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _incident_or_404(incident_id, current_user["org_id"], db)
    note_text = body.get("note", "")
    _log(
        db, current_user, incident_id, "ADD_NOTE",
        details={"note": note_text},
    )
    return {"status": "ok", "incident_id": incident_id}


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@router.post("/{incident_id}/actions", response_model=IncidentRead)
def incident_action(
    incident_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    action = (body.get("action") or "").lower()
    if action not in VALID_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Valid actions: {sorted(VALID_ACTIONS)}",
        )
    inc = _incident_or_404(incident_id, current_user["org_id"], db)
    new_status = ACTION_STATUS_MAP[action]
    inc.review_status = new_status
    db.commit()
    db.refresh(inc)
    _log(db, current_user, incident_id, f"ACTION_{action.upper()}", details={"new_status": new_status})
    return IncidentRead.model_validate(inc)


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------

def _log(db: Session, user: dict, incident_id: str, action: str, details: Optional[dict] = None):
    log = AuditLog(
        org_id=user.get("org_id"),
        user_id=user.get("user_id"),
        action=action,
        entity_type="incident",
        entity_id=incident_id,
        details=details or {},
    )
    db.add(log)
    db.commit()
