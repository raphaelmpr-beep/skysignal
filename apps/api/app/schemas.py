"""
Pydantic v2 schemas for SkySignal API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

class _OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "analyst"
    org_id: str


class UserRead(_OrmBase):
    id: str
    org_id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class SourceCreate(BaseModel):
    name: str
    source_type: str
    url: Optional[str] = None
    is_official: bool = False
    reliability_score: Optional[int] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    is_official: Optional[bool] = None
    reliability_score: Optional[int] = None


class SourceRead(_OrmBase):
    id: str
    name: str
    source_type: str
    url: Optional[str] = None
    is_official: bool
    reliability_score: Optional[int] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceCreate(BaseModel):
    incident_id: str
    source_id: Optional[str] = None
    evidence_type: str
    content: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    collected_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class EvidenceRead(_OrmBase):
    id: str
    incident_id: str
    source_id: Optional[str] = None
    evidence_type: str
    title: Optional[str] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None
    credibility_score: Optional[int] = None
    official_match_score: Optional[int] = None
    created_at: datetime
    source: Optional[SourceRead] = None


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    cisa_sector: Optional[str] = None
    operational_sector: Optional[str] = None
    facility_name: Optional[str] = None
    proximity_score: Optional[int] = None
    tags: Optional[list] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    review_status: Optional[str] = None
    confidence_score: Optional[int] = None
    confidence_tier: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    cisa_sector: Optional[str] = None
    operational_sector: Optional[str] = None
    facility_name: Optional[str] = None
    proximity_score: Optional[int] = None
    tags: Optional[list] = None
    source_url: Optional[str] = None


class IncidentListItem(_OrmBase):
    id: str
    org_id: str
    title: str
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    review_status: str
    confidence_score: int
    confidence_tier: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None
    cisa_sector: Optional[str] = None
    operational_sector: Optional[str] = None
    facility_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncidentRead(_OrmBase):
    id: str
    org_id: str
    title: str
    summary: Optional[str] = None
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    review_status: str
    confidence_score: int
    confidence_tier: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    cisa_sector: Optional[str] = None
    operational_sector: Optional[str] = None
    facility_name: Optional[str] = None
    proximity_score: Optional[int] = None
    tags: Optional[list] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceRead] = []


# ---------------------------------------------------------------------------
# SALUTE Reports
# ---------------------------------------------------------------------------

class SaluteReportCreate(BaseModel):
    incident_id: Optional[str] = None
    reported_by: Optional[str] = None
    size: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    time_observed: Optional[datetime] = None
    equipment: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    additional_notes: Optional[str] = None
    attachments: Optional[list] = None


class SaluteReportUpdate(BaseModel):
    reported_by: Optional[str] = None
    size: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    time_observed: Optional[datetime] = None
    equipment: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    additional_notes: Optional[str] = None
    attachments: Optional[list] = None


class SaluteReportRead(_OrmBase):
    id: str
    incident_id: Optional[str] = None
    org_id: str
    reported_by: Optional[str] = None
    size: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    time_observed: Optional[datetime] = None
    equipment: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    additional_notes: Optional[str] = None
    attachments: Optional[list] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Watch Zones
# ---------------------------------------------------------------------------

class WatchZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lat: float
    lon: float
    radius_miles: float
    alert_threshold: Optional[int] = None


class WatchZoneRead(_OrmBase):
    id: str
    org_id: str
    assessment_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    lat: float
    lon: float
    radius_miles: float
    is_active: bool
    alert_threshold: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Threat Score
# ---------------------------------------------------------------------------

class ThreatScoreResult(BaseModel):
    score: float
    tier: str  # MINIMAL, LOW, MODERATE, ELEVATED, HIGH
    factors: dict[str, float]  # factor_name -> score
    weights: dict[str, float]  # factor_name -> weight
    explanation: str
    incident_count: int


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------

class AssessmentCreate(BaseModel):
    facility_name: str
    address: Optional[str] = None
    lat: float
    lon: float
    radius_miles: float = 5.0
    time_window_days: int = 365


class AssessmentRead(_OrmBase):
    id: str
    org_id: str
    facility_name: str
    address: Optional[str] = None
    lat: float
    lon: float
    radius_miles: float
    time_window_days: int
    threat_score: Optional[float] = None
    threat_tier: Optional[str] = None
    evidence_confidence_score: Optional[float] = None
    incident_density_score: Optional[float] = None
    recency_score: Optional[float] = None
    facility_proximity_score: Optional[float] = None
    severity_score: Optional[float] = None
    sector_sensitivity_score: Optional[float] = None
    repeat_pattern_score: Optional[float] = None
    incident_count: int
    explanation: Optional[str] = None
    nearby_incidents_summary: Optional[list] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Map / Geo
# ---------------------------------------------------------------------------

class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    weight: float


class MapIncident(BaseModel):
    id: str
    lat: Optional[float]
    lon: Optional[float]
    incident_type: Optional[str]
    severity: Optional[str]
    confidence_tier: str
    occurred_at: Optional[datetime]
    title: str


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AnalyticsKPI(BaseModel):
    total_incidents: int
    pending_review: int
    avg_confidence: float
    high_signal_count: int  # confidence_tier in (VERIFIED, HIGH)
    high_signal_facilities: int = 0  # alias for frontend KPI card
    incidents_by_severity: dict[str, int]
    incidents_this_month: int
    incidents_last_month: int


class TimelinePeriod(BaseModel):
    period: str
    count: int
    avg_confidence: float


class SankeyLink(BaseModel):
    source: str
    target: str
    value: int


class SankeyData(BaseModel):
    nodes: list[str]
    links: list[SankeyLink]


class AbComparison(BaseModel):
    period_a_label: str
    period_b_label: str
    period_a_count: int
    period_b_count: int
    period_a_avg_confidence: float
    period_b_avg_confidence: float
    delta_count: int
    delta_pct: float


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    assessment_id: str
    title: Optional[str] = None


class ReportRead(_OrmBase):
    id: str
    org_id: str
    assessment_id: Optional[str] = None
    report_type: str
    title: str
    html_content: Optional[str] = None
    pdf_path: Optional[str] = None
    generated_by: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
