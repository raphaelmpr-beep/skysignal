-- ============================================================
-- SkySignal MVP — SALUTE Schema Enhancements
-- Migration: 003_salute_schema.sql
-- ============================================================

-- PostGIS geography column removed (using lat/lng floats instead)

CREATE INDEX salute_reports_incident_idx ON salute_reports(incident_id);
CREATE INDEX salute_reports_org_idx      ON salute_reports(organization_id);
CREATE INDEX salute_reports_status_idx   ON salute_reports(review_status);

-- ============================================================
-- SALUTE REPORT ATTACHMENTS
-- ============================================================

CREATE TABLE salute_attachments (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  salute_report_id UUID NOT NULL REFERENCES salute_reports(id) ON DELETE CASCADE,
  uploaded_by      UUID REFERENCES users(id),
  file_name        TEXT NOT NULL,
  file_type        TEXT NOT NULL,
  file_size_bytes  INTEGER,
  storage_path     TEXT NOT NULL,
  public_url       TEXT,
  description      TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX salute_attachments_report_idx ON salute_attachments(salute_report_id);

-- ============================================================
-- SALUTE REPORT TEMPLATES
-- ============================================================

CREATE TABLE salute_templates (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  created_by      UUID REFERENCES users(id),
  name            TEXT NOT NULL,
  description     TEXT,
  template_data   JSONB NOT NULL DEFAULT '{}',
  is_default      BOOLEAN NOT NULL DEFAULT false,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX salute_templates_org_idx ON salute_templates(organization_id);

-- ============================================================
-- UPDATED_AT TRIGGER (reusable)
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
CREATE TRIGGER organizations_updated_at
  BEFORE UPDATE ON organizations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER sources_updated_at
  BEFORE UPDATE ON sources
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER incidents_updated_at
  BEFORE UPDATE ON incidents
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER salute_reports_updated_at
  BEFORE UPDATE ON salute_reports
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER watch_zones_updated_at
  BEFORE UPDATE ON watch_zones
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER facility_assessments_updated_at
  BEFORE UPDATE ON facility_assessments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER salute_templates_updated_at
  BEFORE UPDATE ON salute_templates
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- AUDIT LOG TRIGGER FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION audit_log_changes()
RETURNS TRIGGER AS $$
DECLARE
  v_old_values JSONB;
  v_new_values JSONB;
BEGIN
  IF TG_OP = 'DELETE' THEN
    v_old_values := to_jsonb(OLD);
    v_new_values := NULL;
    INSERT INTO audit_logs (entity_type, entity_id, action, old_values, new_values)
    VALUES (TG_TABLE_NAME, OLD.id, TG_OP, v_old_values, v_new_values);
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    v_old_values := to_jsonb(OLD);
    v_new_values := to_jsonb(NEW);
    INSERT INTO audit_logs (entity_type, entity_id, action, old_values, new_values)
    VALUES (TG_TABLE_NAME, NEW.id, TG_OP, v_old_values, v_new_values);
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    v_old_values := NULL;
    v_new_values := to_jsonb(NEW);
    INSERT INTO audit_logs (entity_type, entity_id, action, old_values, new_values)
    VALUES (TG_TABLE_NAME, NEW.id, TG_OP, v_old_values, v_new_values);
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Enable auditing on incidents and salute_reports
CREATE TRIGGER incidents_audit
  AFTER INSERT OR UPDATE OR DELETE ON incidents
  FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

CREATE TRIGGER salute_reports_audit
  AFTER INSERT OR UPDATE OR DELETE ON salute_reports
  FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

-- ============================================================
-- VIEWS
-- ============================================================

-- Incident summary view with CISA sector
CREATE OR REPLACE VIEW v_incident_summary AS
SELECT
  i.id,
  i.organization_id,
  o.name AS organization_name,
  i.title,
  i.incident_type,
  i.operational_sector,
  i.cisa_sector,
  i.severity,
  i.confidence_score,
  i.confidence_tier,
  i.review_status,
  i.occurred_at,
  i.latitude,
  i.longitude,
  i.location_name,
  i.city,
  i.region,
  i.country,
  i.drone_type,
  i.drone_make,
  i.drone_model,
  i.tags,
  i.is_public,
  i.created_at,
  i.updated_at
FROM incidents i
JOIN organizations o ON o.id = i.organization_id;

-- Watch zone alert summary
CREATE OR REPLACE VIEW v_watch_zone_alerts AS
SELECT
  wz.id AS watch_zone_id,
  wz.organization_id,
  wz.name AS zone_name,
  wz.facility_name,
  wz.latitude,
  wz.longitude,
  wz.radius_miles,
  wz.cisa_sector,
  wz.operational_sector,
  COUNT(a.id) AS unread_alert_count,
  MAX(a.created_at) AS last_alert_at
FROM watch_zones wz
LEFT JOIN alerts a ON a.watch_zone_id = wz.id AND a.is_read = false
WHERE wz.is_active = true
GROUP BY wz.id;
