"""
SQLAlchemy 2.0 ORM models for SkySignal.
Python attribute names are chosen to match what the routers expect (org_id, lat, lon).
DB column names are mapped via mapped_column("actual_col_name") where they differ.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[Optional[str]] = mapped_column(String(50), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="organization")
    assessments: Mapped[list["FacilityAssessment"]] = relationship("FacilityAssessment", back_populates="organization")
    watch_zones: Mapped[list["WatchZone"]] = relationship("WatchZone", back_populates="organization")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="organization")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="organization")
    sources: Mapped[list["Source"]] = relationship("Source", back_populates="organization")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # DB column: organization_id → Python attr: org_id
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # DB column: name → Python attr: full_name
    full_name: Mapped[Optional[str]] = mapped_column("name", String(255))
    # DB column: password_hash → hashed_password (used by auth router)
    hashed_password: Mapped[Optional[str]] = mapped_column("password_hash", String(255))
    role: Mapped[str] = mapped_column(String(50), default="ANALYST")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # DB: organization_id → org_id
    org_id: Mapped[Optional[str]] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(1000))
    # DB: feed_url → url (for SourceRead schema compatibility)
    url: Mapped[Optional[str]] = mapped_column("feed_url", String(1000))
    # DB: credibility_score → reliability_score (for SourceRead schema compatibility)
    reliability_score: Mapped[Optional[int]] = mapped_column("credibility_score", Integer, default=50)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_config: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="sources")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="source")


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # DB: organization_id → org_id
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    incident_type: Mapped[Optional[str]] = mapped_column(String(100), default="UNKNOWN")
    operational_sector: Mapped[Optional[str]] = mapped_column(String(100))
    severity: Mapped[Optional[str]] = mapped_column(String(20), default="MEDIUM")
    confidence_score: Mapped[int] = mapped_column(Integer, default=20)
    confidence_tier: Mapped[str] = mapped_column(String(20), default="UNVERIFIED")
    review_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # DB: latitude → lat
    lat: Mapped[Optional[float]] = mapped_column("latitude", Float)
    # DB: longitude → lon
    lon: Mapped[Optional[float]] = mapped_column("longitude", Float)
    location_name: Mapped[Optional[str]] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(100), default="US")
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    source_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("sources.id"))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    drone_type: Mapped[Optional[str]] = mapped_column(String(100))
    drone_make: Mapped[Optional[str]] = mapped_column(String(100))
    drone_model: Mapped[Optional[str]] = mapped_column(String(100))
    altitude_agl: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text), default=list)
    classification_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    official_match_score: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Virtual/computed properties for schema compatibility (not in DB)
    @property
    def cisa_sector(self):
        return None

    @property
    def facility_name(self):
        return None

    @property
    def proximity_score(self):
        return None

    @property
    def reported_at(self):
        return self.detected_at

    @property
    def external_id(self):
        return None

    organization: Mapped["Organization"] = relationship("Organization", back_populates="incidents")
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="incidents")
    evidence: Mapped[list["IncidentEvidence"]] = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan")
    salute_reports: Mapped[list["SaluteReport"]] = relationship("SaluteReport", back_populates="incident")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="incident")


# ---------------------------------------------------------------------------
# Incident Evidence
# ---------------------------------------------------------------------------

class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("sources.id", ondelete="SET NULL"))
    # DB: role → evidence_type alias
    evidence_type: Mapped[str] = mapped_column("role", String(50), default="DISCOVERY")
    title: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence")
    source: Mapped[Optional["Source"]] = relationship("Source")


# ---------------------------------------------------------------------------
# SALUTE Reports
# ---------------------------------------------------------------------------

class SaluteReport(Base):
    __tablename__ = "salute_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="SET NULL"))
    # DB: organization_id → org_id
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    # DB: submitted_by → reported_by
    reported_by: Mapped[Optional[str]] = mapped_column("submitted_by", UUID(as_uuid=False), ForeignKey("users.id"))

    # SALUTE fields — mapped from DB columns
    size: Mapped[Optional[str]] = mapped_column("s_physical_description", Text)
    activity: Mapped[Optional[str]] = mapped_column("a_flight_behavior", Text)
    location: Mapped[Optional[str]] = mapped_column("l_observer_position", Text)
    unit: Mapped[Optional[str]] = mapped_column("u_operator_identity", Text)
    time_observed: Mapped[Optional[datetime]] = mapped_column("t_first_observed_at", DateTime(timezone=True))
    equipment: Mapped[Optional[str]] = mapped_column("e_payload_equipment", Text)

    # DB: l_uas_latitude / l_uas_longitude → lat / lon
    lat: Mapped[Optional[float]] = mapped_column("l_uas_latitude", Float)
    lon: Mapped[Optional[float]] = mapped_column("l_uas_longitude", Float)
    additional_notes: Mapped[Optional[str]] = mapped_column(Text)
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    incident: Mapped[Optional["Incident"]] = relationship("Incident", back_populates="salute_reports")


# ---------------------------------------------------------------------------
# Watch Zones
# ---------------------------------------------------------------------------

class WatchZone(Base):
    __tablename__ = "watch_zones"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # DB: organization_id → org_id
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    assessment_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("facility_assessments.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    facility_name: Mapped[Optional[str]] = mapped_column(String(500))
    address: Mapped[Optional[str]] = mapped_column(String(1000))
    # DB: latitude → lat
    lat: Mapped[float] = mapped_column("latitude", Float, nullable=False)
    # DB: longitude → lon
    lon: Mapped[float] = mapped_column("longitude", Float, nullable=False)
    radius_miles: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    alert_on_new_incident: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    cisa_sector: Mapped[Optional[str]] = mapped_column(String(100))
    operational_sector: Mapped[Optional[str]] = mapped_column(String(100))
    alert_threshold: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="watch_zones")
    assessment: Mapped[Optional["FacilityAssessment"]] = relationship("FacilityAssessment", back_populates="watch_zones")


# ---------------------------------------------------------------------------
# Facility Assessments
# ---------------------------------------------------------------------------

class FacilityAssessment(Base):
    __tablename__ = "facility_assessments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # DB: organization_id → org_id
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    facility_name: Mapped[Optional[str]] = mapped_column(String(500))
    address: Mapped[Optional[str]] = mapped_column(String(1000))
    # DB: latitude → lat
    lat: Mapped[float] = mapped_column("latitude", Float, nullable=False)
    # DB: longitude → lon
    lon: Mapped[float] = mapped_column("longitude", Float, nullable=False)
    radius_miles: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    time_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    # DB: threat_reality_score → threat_score alias
    threat_score: Mapped[Optional[int]] = mapped_column("threat_reality_score", Integer, default=0)
    # DB: score_tier → threat_tier alias
    threat_tier: Mapped[Optional[str]] = mapped_column("score_tier", String(20), default="MINIMAL")

    # Factor scores (DB names use factor_ prefix)
    evidence_confidence_score: Mapped[Optional[int]] = mapped_column("factor_evidence_confidence", Integer, default=0)
    incident_density_score: Mapped[Optional[int]] = mapped_column("factor_incident_density", Integer, default=0)
    recency_score: Mapped[Optional[int]] = mapped_column("factor_recency", Integer, default=0)
    facility_proximity_score: Mapped[Optional[int]] = mapped_column("factor_facility_proximity", Integer, default=0)
    severity_score: Mapped[Optional[int]] = mapped_column("factor_severity", Integer, default=0)
    sector_sensitivity_score: Mapped[Optional[int]] = mapped_column("factor_sector_sensitivity", Integer, default=0)
    repeat_pattern_score: Mapped[Optional[int]] = mapped_column("factor_repeat_pattern", Integer, default=0)

    incident_count: Mapped[int] = mapped_column(Integer, default=0)
    nearby_incident_ids: Mapped[Optional[list]] = mapped_column(ARRAY(UUID(as_uuid=False)), default=list)
    cisa_sector: Mapped[Optional[str]] = mapped_column(String(100))
    operational_sector: Mapped[Optional[str]] = mapped_column(String(100))
    # DB: score_explanation → explanation alias
    explanation: Mapped[Optional[str]] = mapped_column("score_explanation", Text)
    raw_factors: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    # nearby_incidents_summary is not in DB — provide as property
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED")
    watch_zone_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("watch_zones.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def nearby_incidents_summary(self):
        return []

    organization: Mapped["Organization"] = relationship("Organization", back_populates="assessments")
    watch_zones: Mapped[list["WatchZone"]] = relationship("WatchZone", back_populates="assessment")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="assessment")


# ---------------------------------------------------------------------------
# Infrastructure Assets
# ---------------------------------------------------------------------------

class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[Optional[str]] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[Optional[str]] = mapped_column(String(100))
    cisa_sector: Mapped[Optional[str]] = mapped_column(String(100))
    lat: Mapped[Optional[float]] = mapped_column("latitude", Float)
    lon: Mapped[Optional[float]] = mapped_column("longitude", Float)
    address: Mapped[Optional[str]] = mapped_column(String(1000))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    watch_zone_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("watch_zones.id"))
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id"))
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="alerts")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("facility_assessments.id"))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), default="FACILITY_ASSESSMENT")
    # DB: file_path
    pdf_path: Mapped[Optional[str]] = mapped_column("file_path", String(1000))
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    generated_by: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="reports")
    assessment: Mapped[Optional["FacilityAssessment"]] = relationship("FacilityAssessment", back_populates="reports")


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[Optional[str]] = mapped_column(
        "organization_id",
        UUID(as_uuid=False),
        ForeignKey("organizations.id"),
    )
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id"))
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[str]] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column("new_values", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    incident: Mapped[Optional["Incident"]] = relationship("Incident", back_populates="audit_logs")


# ---------------------------------------------------------------------------
# Sector CISA Mapping
# ---------------------------------------------------------------------------

class SectorCisaMapping(Base):
    __tablename__ = "sector_cisa_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operational_sector: Mapped[str] = mapped_column(String(100), nullable=False)
    cisa_sector: Mapped[str] = mapped_column(String(100), nullable=False)
    sensitivity_weight: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
