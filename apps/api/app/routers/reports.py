"""
Reports router — /api/reports
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import FacilityAssessment, Organization, Report
from app.schemas import ReportCreate, ReportRead
from app.services.report_generation_service import ReportGenerationService

router = APIRouter()
report_svc = ReportGenerationService()


def _report_or_404(report_id: str, org_id: str, db: Session) -> Report:
    r = (
        db.query(Report)
        .filter(Report.id == report_id, Report.org_id == org_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


# ---------------------------------------------------------------------------
# Generate / create report
# ---------------------------------------------------------------------------

@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]

    assessment = (
        db.query(FacilityAssessment)
        .filter(FacilityAssessment.id == body.assessment_id, FacilityAssessment.org_id == org_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    nearby = (
        assessment.nearby_incidents_summary
        if isinstance(assessment.nearby_incidents_summary, list)
        else []
    )

    html = report_svc.generate_html(
        assessment=assessment,
        nearby_incidents=nearby,
        org=org,
    )

    title = body.title or f"Threat Assessment — {assessment.facility_name}"
    rpt = Report(
        org_id=org_id,
        assessment_id=body.assessment_id,
        report_type="FACILITY_ASSESSMENT",
        title=title,
        html_content=html,
        generated_by=current_user.get("email"),
    )
    db.add(rpt)
    db.commit()
    db.refresh(rpt)
    return ReportRead.model_validate(rpt)


# ---------------------------------------------------------------------------
# List reports
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_reports(
    skip: int = 0,
    limit: int = 50,
    assessment_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(Report).filter(Report.org_id == org_id)
    if assessment_id:
        q = q.filter(Report.assessment_id == assessment_id)
    total = q.count()
    items = q.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [ReportRead.model_validate(r) for r in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Get single report
# ---------------------------------------------------------------------------

@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    r = _report_or_404(report_id, current_user["org_id"], db)
    return ReportRead.model_validate(r)
