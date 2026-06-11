"""
SQLAlchemy 2.0 ORM models for SkySignal.
Mirrors the PostgreSQL/PostGIS schema exactly.
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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), default="free")
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="organization")
    assessments: Mapped[list["FacilityAssessment"]] = relationship("FacilityAssessment", back_populates="organization")
    watch_zones: Mapped[list["WatchZone"]] = relationship("WatchZone", back_populates="organization")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="organization")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="organization")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="analyst")  # analyst, admin, viewer
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. OFFICIAL_GOVT, NEWS, SOCIAL_MEDIA, ACADEMIC, CROWDSOURCE, INTERNAL
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    reliability_score: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped[list["IncidentEvidence"]] = relationship("IncidentEvidence", back_populates="source")


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    incident_type: Mapped[Optional[str]] = mapped_column(String(100))
    # e.g. SIGHTING, NEAR_MISS, INTERDICTION, SURVEILLANCE, SMUGGLING, INCURSION, UNKNOWN
    severity: Mapped[Optional[str]] = mapped_column(String(20))
    # CRITICAL, HIGH, MEDIUM, LOW, INFO
    review_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    # PENDING, VERIFIED, DISMISSED, ESCALATED, NEEDS_REVIEW
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence_tier: Mapped[str] = mapped_column(String(20), default="UNVERIFIED")
    # VERIFIED, HIGH, MEDIUM, LOW, UNVERIFIED
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    location_name: Mapped[Optional[str]] = mapped_column(String(500))
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cisa_sector: Mapped[Optional[str]] = mapped_column(String(100))
    operational_sector: Mapped[Optional[str]] = mapped_column(String(100))
    facility_name: Mapped[Optional[str]] = mapped_column(String(500))
    proximity_score: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="incidents")
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
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # OFFICIAL_CONFIRMATION, CORROBORATION, DISCOVERY, CONTRADICTION, MEDIA, DOCUMENT
    content: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence")
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="evidence")


# ---------------------------------------------------------------------------
# SALUTE Reports
# ---------------------------------------------------------------------------

class SaluteReport(Base):
    __tablename__ = "salute_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="SET NULL"))
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    reported_by: Mapped[Optional[str]] = mapped_column(String(255))

    # SALUTE fields
    size: Mapped[Optional[str]] = mapped_column(Text)           # S – Size/shape of the drone
    activity: Mapped[Optional[str]] = mapped_column(Text)        # A – Activity observed
    location: Mapped[Optional[str]] = mapped_column(Text)        # L – Location description
    unit: Mapped[Optional[str]] = mapped_column(Text)            # U – Unit/entity involved
    time_observed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # T
    equipment: Mapped[Optional[str]] = mapped_column(Text)       # E – Equipment/payload

    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
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
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    assessment_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("facility_assessments.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    radius_miles: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    facility_name: Mapped[str] = mapped_column(String(500), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(1000))
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    radius_miles: Mapped[float] = mapped_column(Float, default=5.0)
    time_window_days: Mapped[int] = mapped_column(Integer, default=365)

    # Threat score
    threat_score: Mapped[Optional[float]] = mapped_column(Float)
    threat_tier: Mapped[Optional[str]] = mapped_column(String(20))
    # MINIMAL, LOW, MODERATE, ELEVATED, HIGH

    # Factor scores (0-100 each)
    evidence_confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    incident_density_score: Mapped[Optional[float]] = mapped_column(Float)
    recency_score: Mapped[Optional[float]] = mapped_column(Float)
    facility_proximity_score: Mapped[Optional[float]] = mapped_column(Float)
    severity_score: Mapped[Optional[float]] = mapped_column(Float)
    sector_sensitivity_score: Mapped[Optional[float]] = mapped_column(Float)
    repeat_pattern_score: Mapped[Optional[float]] = mapped_column(Float)

    incident_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    nearby_incidents_summary: Mapped[Optional[list]] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="assessments")
    watch_zones: Mapped[list["WatchZone"]] = relationship("WatchZone", back_populates="assessment")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="assessment")


# ---------------------------------------------------------------------------
# Infrastructure Assets
# ---------------------------------------------------------------------------

class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[Optional[str]] = mapped_column(String(100))
    cisa_sector: Mapped[Optional[str]] = mapped_column(String(100))
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lon: Mapped[Optional[float]] = mapped_column(Float)
    address: Mapped[Optional[str]] = mapped_column(String(1000))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    county: Mapped[Optional[str]] = mapped_column(String(100))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="SET NULL"))
    watch_zone_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("watch_zones.id", ondelete="SET NULL"))
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
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    assessment_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("facility_assessments.id", ondelete="SET NULL"))
    report_type: Mapped[str] = mapped_column(String(50), default="FACILITY_ASSESSMENT")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(1000))
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
    org_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="SET NULL"))
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"))
    incident_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
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
