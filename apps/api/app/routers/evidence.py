"""
Evidence router — /api/evidence
Standalone CRUD for incident evidence (evidence can also be managed via /api/incidents/{id}/evidence).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Incident, IncidentEvidence
from app.schemas import EvidenceCreate, EvidenceRead

router = APIRouter()


def _evidence_or_404(evidence_id: str, org_id: str, db: Session) -> IncidentEvidence:
    ev = (
        db.query(IncidentEvidence)
        .join(Incident, Incident.id == IncidentEvidence.incident_id)
        .filter(IncidentEvidence.id == evidence_id, Incident.org_id == org_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


# ---------------------------------------------------------------------------
# List evidence (optionally filtered by incident)
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_evidence(
    incident_id: str | None = None,
    evidence_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = (
        db.query(IncidentEvidence)
        .join(Incident, Incident.id == IncidentEvidence.incident_id)
        .filter(Incident.org_id == org_id)
    )
    if incident_id:
        q = q.filter(IncidentEvidence.incident_id == incident_id)
    if evidence_type:
        q = q.filter(IncidentEvidence.evidence_type == evidence_type)

    total = q.count()
    items = q.order_by(IncidentEvidence.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [EvidenceRead.model_validate(e) for e in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Create evidence
# ---------------------------------------------------------------------------

@router.post("", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def create_evidence(
    body: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Verify incident belongs to org
    inc = (
        db.query(Incident)
        .filter(Incident.id == body.incident_id, Incident.org_id == current_user["org_id"])
        .first()
    )
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    ev = IncidentEvidence(**body.model_dump(exclude_none=True))
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return EvidenceRead.model_validate(ev)


# ---------------------------------------------------------------------------
# Get single evidence
# ---------------------------------------------------------------------------

@router.get("/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ev = _evidence_or_404(evidence_id, current_user["org_id"], db)
    return EvidenceRead.model_validate(ev)


# ---------------------------------------------------------------------------
# Delete evidence
# ---------------------------------------------------------------------------

@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ev = _evidence_or_404(evidence_id, current_user["org_id"], db)
    db.delete(ev)
    db.commit()
