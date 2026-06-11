"""
Assessments router — /api/assessments
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import FacilityAssessment, Organization, Report, WatchZone
from app.schemas import (
    AssessmentCreate,
    AssessmentRead,
    ReportRead,
    WatchZoneCreate,
    WatchZoneRead,
)
from app.services.threat_score_service import ThreatScoreService
from app.services.report_generation_service import ReportGenerationService

router = APIRouter()
threat_svc = ThreatScoreService()
report_svc = ReportGenerationService()


def _assessment_or_404(assessment_id: str, org_id: str, db: Session) -> FacilityAssessment:
    a = (
        db.query(FacilityAssessment)
        .filter(
            FacilityAssessment.id == assessment_id,
            FacilityAssessment.org_id == org_id,
        )
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return a


# ---------------------------------------------------------------------------
# Create assessment — runs threat score computation
# ---------------------------------------------------------------------------

@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(
    body: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]

    # Run threat score
    result = threat_svc.compute_score(
        lat=body.lat,
        lon=body.lon,
        radius_miles=body.radius_miles,
        time_window_days=body.time_window_days,
        db=db,
        org_id=org_id,
    )

    assessment = FacilityAssessment(
        org_id=org_id,
        facility_name=body.facility_name,
        address=body.address,
        lat=body.lat,
        lon=body.lon,
        radius_miles=body.radius_miles,
        time_window_days=body.time_window_days,
        threat_score=result.score,
        threat_tier=result.tier,
        evidence_confidence_score=result.factors.get("evidence_confidence"),
        incident_density_score=result.factors.get("incident_density"),
        recency_score=result.factors.get("recency"),
        facility_proximity_score=result.factors.get("facility_proximity"),
        severity_score=result.factors.get("severity"),
        sector_sensitivity_score=result.factors.get("sector_sensitivity"),
        repeat_pattern_score=result.factors.get("repeat_pattern"),
        incident_count=result.incident_count,
        explanation=result.explanation,
        nearby_incidents_summary=result.factors,  # stored as JSONB
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return AssessmentRead.model_validate(assessment)


# ---------------------------------------------------------------------------
# List assessments
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_assessments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(FacilityAssessment).filter(FacilityAssessment.org_id == org_id)
    total = q.count()
    items = q.order_by(FacilityAssessment.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [AssessmentRead.model_validate(a) for a in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Get single assessment
# ---------------------------------------------------------------------------

@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    a = _assessment_or_404(assessment_id, current_user["org_id"], db)
    return AssessmentRead.model_validate(a)


# ---------------------------------------------------------------------------
# Create watch zone from assessment
# ---------------------------------------------------------------------------

@router.post("/{assessment_id}/watch-zone", response_model=WatchZoneRead, status_code=status.HTTP_201_CREATED)
def create_watch_zone(
    assessment_id: str,
    body: WatchZoneCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    a = _assessment_or_404(assessment_id, current_user["org_id"], db)
    wz = WatchZone(
        org_id=current_user["org_id"],
        assessment_id=assessment_id,
        name=body.name,
        description=body.description,
        lat=body.lat if body.lat else a.lat,
        lon=body.lon if body.lon else a.lon,
        radius_miles=body.radius_miles if body.radius_miles else a.radius_miles,
        alert_threshold=body.alert_threshold,
    )
    db.add(wz)
    db.commit()
    db.refresh(wz)
    return WatchZoneRead.model_validate(wz)


# ---------------------------------------------------------------------------
# Generate report (HTML stub — PDF via weasyprint if available)
# ---------------------------------------------------------------------------

@router.post("/{assessment_id}/report", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def generate_report(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    a = _assessment_or_404(assessment_id, current_user["org_id"], db)
    org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()

    # Get nearby incidents summary (stored as JSONB list or fall back to [])
    nearby = a.nearby_incidents_summary if isinstance(a.nearby_incidents_summary, list) else []

    html = report_svc.generate_html(
        assessment=a,
        nearby_incidents=nearby,
        org=org,
    )

    rpt = Report(
        org_id=current_user["org_id"],
        assessment_id=assessment_id,
        report_type="FACILITY_ASSESSMENT",
        title=f"Threat Assessment — {a.facility_name}",
        html_content=html,
        generated_by=current_user.get("email"),
    )
    db.add(rpt)
    db.commit()
    db.refresh(rpt)
    return ReportRead.model_validate(rpt)
