-- ============================================================
-- SkySignal MVP — Initial Schema
-- Migration: 001_initial_schema.sql
-- ============================================================

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'ORG_ADMIN', 'ANALYST', 'VIEWER');

CREATE TYPE review_status AS ENUM (
  'PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'NEEDS_MORE_REVIEW'
);

CREATE TYPE confidence_tier AS ENUM (
  'VERIFIED', 'HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED'
);

CREATE TYPE incident_type AS ENUM (
  'KINETIC_ATTACK', 'SURVEILLANCE_ISR', 'NEAR_MISS', 'SMUGGLING',
  'SIGNAL_INTERFERENCE', 'COLLISION', 'PRIVACY_VIOLATION', 'NUISANCE', 'UNKNOWN'
);

CREATE TYPE severity_level AS ENUM (
  'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'
);

CREATE TYPE source_type AS ENUM (
  'MANUAL', 'GDELT', 'RSS', 'FAA', 'OFFICIAL_PRESS', 'SENSOR', 'NEWSAPI'
);

CREATE TYPE evidence_role AS ENUM (
  'DISCOVERY', 'CORROBORATION', 'OFFICIAL_CONFIRMATION',
  'CONTRADICTION', 'DUPLICATE', 'REJECTION_SUPPORT'
);

CREATE TYPE sector_enum AS ENUM (
  'AVIATION', 'MILITARY', 'CRITICAL_INFRA', 'BORDER_SECURITY',
  'CORRECTIONS', 'LAW_ENFORCEMENT', 'MARITIME', 'GOVERNMENT',
  'STADIUM_VENUE', 'VIP_PROTECTION', 'MEDIA', 'NATURE_RESERVE',
  'ENTERPRISE', 'RESIDENTIAL', 'TRANSPORTATION', 'HEALTHCARE',
  'EDUCATION', 'LOCAL_GOVERNMENTAL'
);

-- ============================================================
-- ORGANIZATIONS
-- ============================================================

CREATE TABLE organizations (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name          TEXT NOT NULL,
  slug          TEXT UNIQUE NOT NULL,
  plan          TEXT NOT NULL DEFAULT 'starter',
  is_active     BOOLEAN NOT NULL DEFAULT true,
  settings      JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email           TEXT UNIQUE NOT NULL,
  name            TEXT,
  password_hash   TEXT,
  role            user_role NOT NULL DEFAULT 'ANALYST',
  is_active       BOOLEAN NOT NULL DEFAULT true,
  last_login_at   TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX users_org_idx ON users(organization_id);

-- ============================================================
-- SOURCES
-- ============================================================

CREATE TABLE sources (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  UUID REFERENCES organizations(id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  source_type      source_type NOT NULL,
  base_url         TEXT,
  feed_url         TEXT,
  credibility_score INTEGER NOT NULL DEFAULT 50 CHECK (credibility_score BETWEEN 0 AND 100),
  is_official      BOOLEAN NOT NULL DEFAULT false,
  is_active        BOOLEAN NOT NULL DEFAULT true,
  last_fetched_at  TIMESTAMPTZ,
  fetch_config     JSONB NOT NULL DEFAULT '{}',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INCIDENTS
-- ============================================================

CREATE TABLE incidents (
  id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  summary              TEXT,
  description          TEXT,
  incident_type        incident_type NOT NULL DEFAULT 'UNKNOWN',
  operational_sector   sector_enum,
  severity             severity_level NOT NULL DEFAULT 'MEDIUM',
  confidence_score     INTEGER NOT NULL DEFAULT 20 CHECK (confidence_score BETWEEN 0 AND 100),
  confidence_tier      confidence_tier NOT NULL DEFAULT 'UNVERIFIED',
  review_status        review_status NOT NULL DEFAULT 'PENDING',
  is_public            BOOLEAN NOT NULL DEFAULT false,
  occurred_at          TIMESTAMPTZ NOT NULL,
  detected_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  latitude             DOUBLE PRECISION,
  longitude            DOUBLE PRECISION,
  location             GEOGRAPHY(POINT, 4326),
  location_name        TEXT,
  country              TEXT NOT NULL DEFAULT 'US',
  region               TEXT,
  city                 TEXT,
  source_id            UUID REFERENCES sources(id),
  source_url           TEXT,
  raw_payload          JSONB,
  drone_type           TEXT,
  drone_make           TEXT,
  drone_model          TEXT,
  altitude_agl         INTEGER,
  tags                 TEXT[] NOT NULL DEFAULT '{}',
  classification_json  JSONB NOT NULL DEFAULT '{}',
  official_match_score INTEGER,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX incidents_org_idx          ON incidents(organization_id);
CREATE INDEX incidents_location_idx     ON incidents USING GIST(location);
CREATE INDEX incidents_occurred_at_idx  ON incidents(occurred_at DESC);
CREATE INDEX incidents_review_status_idx ON incidents(review_status);
CREATE INDEX incidents_confidence_tier_idx ON incidents(confidence_tier);

-- ============================================================
-- INCIDENT EVIDENCE
-- ============================================================

CREATE TABLE incident_evidence (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  incident_id       UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  source_id         UUID REFERENCES sources(id),
  role              evidence_role NOT NULL DEFAULT 'DISCOVERY',
  title             TEXT,
  url               TEXT,
  excerpt           TEXT,
  published_at      TIMESTAMPTZ,
  credibility_score INTEGER CHECK (credibility_score BETWEEN 0 AND 100),
  official_match_score INTEGER,
  raw_data          JSONB,
  added_by          UUID REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX evidence_incident_idx ON incident_evidence(incident_id);

-- ============================================================
-- SALUTE REPORTS
-- ============================================================

CREATE TABLE salute_reports (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  incident_id     UUID REFERENCES incidents(id) ON DELETE SET NULL,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  submitted_by    UUID REFERENCES users(id),

  -- S: Size/System
  s_ua_type             TEXT,
  s_number_of_uas       INTEGER DEFAULT 1,
  s_size_class          TEXT,
  s_physical_description TEXT,
  s_registration        TEXT,
  s_manufacturer        TEXT,
  s_model               TEXT,

  -- A: Activity
  a_flight_behavior     TEXT,
  a_flight_profile      TEXT,
  a_direction_of_travel TEXT,
  a_duration_observed   TEXT,
  a_suspected_mission   TEXT,
  a_swarm_behavior      TEXT,
  a_payload_suspected   TEXT,

  -- L: Location
  l_observer_position   TEXT,
  l_uas_latitude        DOUBLE PRECISION,
  l_uas_longitude       DOUBLE PRECISION,
  l_altitude            TEXT,
  l_location_precision  TEXT,
  l_operator_location   TEXT,
  l_launch_origin       TEXT,
  l_affected_facility   TEXT,

  -- U: Unit/Identity
  u_operator_identity      TEXT,
  u_affiliation_indicators TEXT,
  u_remote_id_broadcast    BOOLEAN DEFAULT false,
  u_remote_id_data         JSONB,
  u_insignia_markings      TEXT,

  -- T: Time
  t_first_observed_at     TIMESTAMPTZ,
  t_last_observed_at      TIMESTAMPTZ,
  t_total_duration_minutes INTEGER,
  t_lighting_conditions   TEXT,

  -- E: Equipment
  e_rf_frequencies         TEXT,
  e_payload_equipment      TEXT,
  e_electronic_signatures  TEXT,
  e_collision_avoidance    TEXT,

  -- T2: Threat Assessment
  t2_threat_level TEXT,
  t2_coa          TEXT,
  t2_priority     TEXT,

  -- CR: Countermeasure/Response (reporting only)
  cr_response_actions   TEXT,
  cr_agencies_notified  TEXT,

  -- PIA: Post-Incident Actions
  pia_evidence_collected   TEXT,
  pia_follow_up_required   BOOLEAN DEFAULT false,
  pia_notes                TEXT,

  -- Meta
  review_status   review_status NOT NULL DEFAULT 'PENDING',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- WATCH ZONES
-- ============================================================

CREATE TABLE watch_zones (
  id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  created_by            UUID REFERENCES users(id),
  name                  TEXT NOT NULL,
  description           TEXT,
  facility_name         TEXT,
  address               TEXT,
  latitude              DOUBLE PRECISION NOT NULL,
  longitude             DOUBLE PRECISION NOT NULL,
  center                GEOGRAPHY(POINT, 4326),
  radius_miles          DOUBLE PRECISION NOT NULL DEFAULT 5.0,
  alert_on_new_incident BOOLEAN NOT NULL DEFAULT true,
  is_active             BOOLEAN NOT NULL DEFAULT true,
  cisa_sector           TEXT,
  operational_sector    sector_enum,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX watch_zones_org_idx    ON watch_zones(organization_id);
CREATE INDEX watch_zones_center_idx ON watch_zones USING GIST(center);

-- ============================================================
-- FACILITY ASSESSMENTS
-- ============================================================

CREATE TABLE facility_assessments (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  requested_by    UUID REFERENCES users(id),
  facility_name   TEXT,
  address         TEXT,
  latitude        DOUBLE PRECISION NOT NULL,
  longitude       DOUBLE PRECISION NOT NULL,
  radius_miles    DOUBLE PRECISION NOT NULL,
  time_window_days INTEGER NOT NULL,

  -- Scores
  threat_reality_score INTEGER NOT NULL DEFAULT 0 CHECK (threat_reality_score BETWEEN 0 AND 100),
  score_tier           TEXT NOT NULL DEFAULT 'MINIMAL',

  -- Factor scores (0-100 each)
  factor_evidence_confidence INTEGER DEFAULT 0,
  factor_incident_density    INTEGER DEFAULT 0,
  factor_recency             INTEGER DEFAULT 0,
  factor_facility_proximity  INTEGER DEFAULT 0,
  factor_severity            INTEGER DEFAULT 0,
  factor_sector_sensitivity  INTEGER DEFAULT 0,
  factor_repeat_pattern      INTEGER DEFAULT 0,

  -- Context
  incident_count       INTEGER NOT NULL DEFAULT 0,
  nearby_incident_ids  UUID[] NOT NULL DEFAULT '{}',
  cisa_sector          TEXT,
  operational_sector   sector_enum,
  score_explanation    TEXT,
  raw_factors          JSONB NOT NULL DEFAULT '{}',

  -- Status
  status       TEXT NOT NULL DEFAULT 'COMPLETED',
  watch_zone_id UUID REFERENCES watch_zones(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX assessments_org_idx ON facility_assessments(organization_id);

-- ============================================================
-- INFRASTRUCTURE ASSETS
-- ============================================================

CREATE TABLE infrastructure_assets (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  asset_type      TEXT NOT NULL,
  cisa_sector     TEXT,
  latitude        DOUBLE PRECISION NOT NULL,
  longitude       DOUBLE PRECISION NOT NULL,
  location        GEOGRAPHY(POINT, 4326),
  address         TEXT,
  city            TEXT,
  state           TEXT,
  is_public       BOOLEAN NOT NULL DEFAULT true,
  metadata        JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX assets_location_idx ON infrastructure_assets USING GIST(location);

-- ============================================================
-- ALERTS
-- ============================================================

CREATE TABLE alerts (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  watch_zone_id   UUID REFERENCES watch_zones(id),
  incident_id     UUID REFERENCES incidents(id),
  alert_type      TEXT NOT NULL,
  message         TEXT NOT NULL,
  is_read         BOOLEAN NOT NULL DEFAULT false,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- REPORTS (PDF report metadata)
-- ============================================================

CREATE TABLE reports (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  assessment_id   UUID REFERENCES facility_assessments(id),
  created_by      UUID REFERENCES users(id),
  title           TEXT NOT NULL,
  report_type     TEXT NOT NULL DEFAULT 'FACILITY_ASSESSMENT',
  file_path       TEXT,
  file_url        TEXT,
  html_content    TEXT,
  metadata        JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- AUDIT LOGS
-- ============================================================

CREATE TABLE audit_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID REFERENCES organizations(id),
  user_id         UUID REFERENCES users(id),
  entity_type     TEXT NOT NULL,
  entity_id       UUID,
  action          TEXT NOT NULL,
  old_values      JSONB,
  new_values      JSONB,
  ip_address      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX audit_logs_entity_idx  ON audit_logs(entity_type, entity_id);
CREATE INDEX audit_logs_created_idx ON audit_logs(created_at DESC);
