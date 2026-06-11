"""
SALUTE Reports router — /api/salute
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Incident, SaluteReport
from app.schemas import (
    SaluteReportCreate,
    SaluteReportRead,
    SaluteReportUpdate,
)

router = APIRouter()


def _salute_or_404(report_id: str, org_id: str, db: Session) -> SaluteReport:
    r = (
        db.query(SaluteReport)
        .filter(SaluteReport.id == report_id, SaluteReport.org_id == org_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="SALUTE report not found")
    return r


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_salute_reports(
    skip: int = 0,
    limit: int = 50,
    incident_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(SaluteReport).filter(SaluteReport.org_id == org_id)
    if incident_id:
        q = q.filter(SaluteReport.incident_id == incident_id)
    total = q.count()
    items = q.order_by(SaluteReport.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [SaluteReportRead.model_validate(r) for r in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Create — optionally auto-create a PENDING incident
# ---------------------------------------------------------------------------

@router.post("", response_model=SaluteReportRead, status_code=status.HTTP_201_CREATED)
def create_salute_report(
    body: SaluteReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    incident_id = body.incident_id

    if not incident_id:
        # Auto-create a PENDING incident from SALUTE fields
        title = (
            f"SALUTE Report — {body.activity or 'Unknown Activity'} "
            f"at {body.location or 'Unknown Location'}"
        )
        summary_parts = []
        if body.size:
            summary_parts.append(f"Size/Shape: {body.size}")
        if body.activity:
            summary_parts.append(f"Activity: {body.activity}")
        if body.unit:
            summary_parts.append(f"Unit: {body.unit}")
        if body.equipment:
            summary_parts.append(f"Equipment: {body.equipment}")
        if body.additional_notes:
            summary_parts.append(f"Notes: {body.additional_notes}")

        incident = Incident(
            org_id=org_id,
            title=title,
            summary="\n".join(summary_parts),
            review_status="PENDING",
            confidence_score=10,
            confidence_tier="UNVERIFIED",
            lat=body.lat,
            lon=body.lon,
            location_name=body.location,
            occurred_at=body.time_observed,
            incident_type="SIGHTING",
        )
        db.add(incident)
        db.flush()  # get the ID
        incident_id = incident.id

    report = SaluteReport(
        org_id=org_id,
        incident_id=incident_id,
        reported_by=body.reported_by,
        size=body.size,
        activity=body.activity,
        location=body.location,
        unit=body.unit,
        time_observed=body.time_observed,
        equipment=body.equipment,
        lat=body.lat,
        lon=body.lon,
        additional_notes=body.additional_notes,
        attachments=body.attachments or [],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return SaluteReportRead.model_validate(report)


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

@router.get("/{report_id}", response_model=SaluteReportRead)
def get_salute_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    r = _salute_or_404(report_id, current_user["org_id"], db)
    return SaluteReportRead.model_validate(r)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@router.patch("/{report_id}", response_model=SaluteReportRead)
def update_salute_report(
    report_id: str,
    body: SaluteReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    r = _salute_or_404(report_id, current_user["org_id"], db)
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return SaluteReportRead.model_validate(r)
