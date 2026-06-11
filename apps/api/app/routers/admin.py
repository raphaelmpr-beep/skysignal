"""
Admin router — /api/admin
Review queue and incident management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import AuditLog, Incident
from app.schemas import IncidentListItem, IncidentRead
from app.services.confidence_service import ConfidenceService

router = APIRouter()
conf_svc = ConfidenceService()

VALID_REVIEW_ACTIONS = {
    "approve": "VERIFIED",
    "reject": "DISMISSED",
    "merge_duplicate": "DISMISSED",
    "request_more_review": "NEEDS_REVIEW",
}


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
        user_id=current_user.get("user_id"),
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
        user_id=current_user.get("user_id"),
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
