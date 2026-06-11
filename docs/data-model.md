# SkySignal Data Model

This document describes every database table, its purpose, key fields, and inter-table relationships.
The schema lives in `packages/database/migrations/` and is managed via numbered SQL migration files.
The ORM layer is SQLAlchemy 2.0 mapped classes in `apps/api/app/models.py`.

---

## Overview

```
organizations ──┬── users
                ├── incidents ──── incident_evidence ──── sources
                │               └── salute_reports
                ├── watch_zones
                ├── facility_assessments ──── watch_zones (FK)
                ├── reports
                ├── alerts
                └── audit_logs
```

---

## Tables

### `organizations`

Multi-tenancy anchor. Every piece of data belongs to exactly one org.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | TEXT | Display name |
| `slug` | TEXT UNIQUE | URL-safe identifier |
| `plan` | TEXT | `starter`, `pro`, `enterprise` |
| `is_active` | BOOLEAN | Soft-disable without deletion |
| `settings` | JSONB | Org-level feature flags / config |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `users`

Individuals with access to an organization's SkySignal workspace.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | Cascade delete |
| `email` | TEXT UNIQUE | Login credential |
| `name` | TEXT | Display name |
| `password_hash` | TEXT | bcrypt; null for SSO-only users |
| `role` | `user_role` ENUM | `SUPER_ADMIN`, `ORG_ADMIN`, `ANALYST`, `VIEWER` |
| `is_active` | BOOLEAN | |
| `last_login_at` | TIMESTAMPTZ | |

**Roles:**
- `SUPER_ADMIN` — platform operator; cross-org access
- `ORG_ADMIN` — full org access; can invite users and manage review queue
- `ANALYST` — read/write incidents, submit SALUTE, run assessments
- `VIEWER` — read-only; cannot approve/reject incidents

---

### `sources`

Named data sources with reliability metadata. Evidence records link to sources.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | Null = platform-global source |
| `name` | TEXT | Human-readable label |
| `source_type` | `source_type` ENUM | `MANUAL`, `GDELT`, `RSS`, `FAA`, `OFFICIAL_PRESS`, `SENSOR`, `NEWSAPI` |
| `base_url` | TEXT | Source homepage |
| `feed_url` | TEXT | RSS/API endpoint used for ingestion |
| `credibility_score` | INTEGER [0–100] | Platform-assigned reliability score |
| `is_official` | BOOLEAN | Boosts confidence when true (govt/LEA sources) |
| `is_active` | BOOLEAN | Disable without deleting |
| `last_fetched_at` | TIMESTAMPTZ | Set by ingestion cron |
| `fetch_config` | JSONB | Source-specific ingestion parameters |

---

### `incidents`

Core entity. Represents a single UAS-related event of potential security significance.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `title` | TEXT | Short descriptor |
| `summary` | TEXT | Analyst-written summary |
| `description` | TEXT | Extended detail / raw source text |
| `incident_type` | `incident_type` ENUM | `KINETIC_ATTACK`, `SURVEILLANCE_ISR`, `NEAR_MISS`, `SMUGGLING`, `SIGNAL_INTERFERENCE`, `COLLISION`, `PRIVACY_VIOLATION`, `NUISANCE`, `UNKNOWN` |
| `operational_sector` | `sector_enum` ENUM | 18-value operational taxonomy |
| `cisa_sector` | `cisa_sector_enum` ENUM | Auto-populated via trigger from `operational_sector` |
| `cisa_subsector` | TEXT | Optional finer classification |
| `severity` | `severity_level` ENUM | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL` |
| `confidence_score` | INTEGER [0–100] | Computed by `ConfidenceService`; updated on evidence changes |
| `confidence_tier` | `confidence_tier` ENUM | `VERIFIED`, `HIGH`, `MEDIUM`, `LOW`, `UNVERIFIED` |
| `review_status` | `review_status` ENUM | `PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `NEEDS_MORE_REVIEW` |
| `is_public` | BOOLEAN | Reserved for future cross-org sharing |
| `occurred_at` | TIMESTAMPTZ | When the incident took place |
| `detected_at` | TIMESTAMPTZ | When the system first recorded it |
| `latitude` | DOUBLE PRECISION | WGS-84 decimal degrees |
| `longitude` | DOUBLE PRECISION | WGS-84 decimal degrees |
| `location` | GEOGRAPHY(POINT,4326) | PostGIS column for spatial queries |
| `location_name` | TEXT | Human-readable place name |
| `country` / `region` / `city` | TEXT | Administrative breakdown |
| `source_id` | UUID FK → sources | Primary source that produced this incident |
| `source_url` | TEXT | Direct link to source article or document |
| `raw_payload` | JSONB | Original ingest payload (GDELT row, RSS item, etc.) |
| `drone_type`, `drone_make`, `drone_model` | TEXT | Platform details when known |
| `altitude_agl` | INTEGER | Altitude above ground level in feet |
| `tags` | TEXT[] | Free-form labels for filtering |
| `classification_json` | JSONB | ML/NLP classification output |
| `official_match_score` | INTEGER | Score from `official_validation_service.py` (0–100) |

**Key indexes:** `location` (GIST), `occurred_at DESC`, `review_status`, `confidence_tier`, `cisa_sector`

---

### `incident_evidence`

Individual evidence items attached to an incident. Multiple pieces of evidence accumulate to drive the confidence score.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `incident_id` | UUID FK → incidents | Cascade delete |
| `source_id` | UUID FK → sources | Which source this evidence came from |
| `role` | `evidence_role` ENUM | `DISCOVERY`, `CORROBORATION`, `OFFICIAL_CONFIRMATION`, `CONTRADICTION`, `DUPLICATE`, `REJECTION_SUPPORT` |
| `title` | TEXT | Headline or document title |
| `url` | TEXT | Link to source article |
| `excerpt` | TEXT | Relevant quote or passage |
| `published_at` | TIMESTAMPTZ | When the evidence was published |
| `credibility_score` | INTEGER [0–100] | Per-evidence quality rating |
| `official_match_score` | INTEGER [0–100] | How closely this evidence matches an official account |
| `raw_data` | JSONB | Parsed raw data from the source |
| `added_by` | UUID FK → users | Who attached this evidence |

**Evidence roles and their confidence effect (see `confidence_service.py`):**
- `OFFICIAL_CONFIRMATION` from official source: +40 pts
- `CORROBORATION` from official source: +20 pts
- `CORROBORATION` from non-official source: +10 pts
- `CONTRADICTION`: −15 pts
- Multiple corroborating sources: +5 each (up to +20 bonus)

---

### `salute_reports`

Extended SALUTE framework (Size–Activity–Location–Unit–Time–Equipment) reports for UAS sightings.
These can be linked to an existing incident or stand alone pending triage.

Key field groups:
- **S (Size/System):** `s_ua_type`, `s_number_of_uas`, `s_size_class`, `s_physical_description`, `s_registration`, `s_manufacturer`, `s_model`
- **A (Activity):** `a_flight_behavior`, `a_flight_profile`, `a_direction_of_travel`, `a_duration_observed`, `a_suspected_mission`, `a_swarm_behavior`, `a_payload_suspected`
- **L (Location):** `l_observer_position`, `l_uas_latitude`, `l_uas_longitude`, `l_uas_location` (GIST), `l_altitude`, `l_affected_facility`
- **U (Unit/Identity):** `u_operator_identity`, `u_remote_id_broadcast`, `u_remote_id_data` (JSONB)
- **T (Time):** `t_first_observed_at`, `t_last_observed_at`, `t_total_duration_minutes`, `t_lighting_conditions`
- **E (Equipment):** `e_rf_frequencies`, `e_payload_equipment`, `e_electronic_signatures`
- **T2 (Threat Assessment):** `t2_threat_level`, `t2_coa`, `t2_priority`
- **CR (Countermeasure/Response — reporting only):** `cr_response_actions`, `cr_agencies_notified`
- **PIA (Post-Incident Actions):** `pia_evidence_collected`, `pia_follow_up_required`

---

### `salute_attachments`

Files attached to a SALUTE report (photos, video clips, sensor logs).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `salute_report_id` | UUID FK → salute_reports | Cascade delete |
| `uploaded_by` | UUID FK → users | |
| `file_name` / `file_type` / `file_size_bytes` | TEXT/INTEGER | |
| `storage_path` | TEXT | Object-store path (S3, Supabase Storage, etc.) |
| `public_url` | TEXT | CDN URL when accessible |

---

### `watch_zones`

Saved geographic areas of interest. When new APPROVED incidents fall within a watch zone's radius, alerts are generated.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `name` | TEXT | e.g. "Downtown Substation" |
| `latitude` / `longitude` | DOUBLE PRECISION | Center point |
| `center` | GEOGRAPHY(POINT,4326) | PostGIS spatial column |
| `radius_miles` | DOUBLE PRECISION | Alert radius |
| `alert_on_new_incident` | BOOLEAN | Toggle alerting |
| `is_active` | BOOLEAN | |
| `cisa_sector` / `operational_sector` | TEXT/ENUM | For sector-specific alerting |

---

### `facility_assessments`

Point-in-time Drone Threat Reality Score calculation for a specific location.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `facility_name` / `address` | TEXT | |
| `latitude` / `longitude` | DOUBLE PRECISION | Assessment center |
| `radius_miles` | DOUBLE PRECISION | Search radius |
| `time_window_days` | INTEGER | How far back to look |
| `threat_reality_score` | INTEGER [0–100] | Final composite score |
| `score_tier` | TEXT | `MINIMAL`, `LOW`, `MODERATE`, `ELEVATED`, `HIGH` |
| `factor_*` | INTEGER | Per-factor component scores (7 columns) |
| `incident_count` | INTEGER | Incidents found in radius/window |
| `nearby_incident_ids` | UUID[] | IDs of contributing incidents |
| `score_explanation` | TEXT | Human-readable explanation text |
| `raw_factors` | JSONB | Full factor breakdown JSON |

---

### `infrastructure_assets`

Reference dataset of known critical infrastructure locations. Used to enrich incident context.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | TEXT | Facility name |
| `asset_type` | TEXT | e.g. `POWER_PLANT`, `WATER_TREATMENT` |
| `cisa_sector` | TEXT | CISA sector classification |
| `latitude` / `longitude` | DOUBLE PRECISION | |
| `location` | GEOGRAPHY(POINT,4326) | Spatial index |
| `city` / `state` | TEXT | |
| `is_public` | BOOLEAN | Whether sourced from public data |
| `metadata` | JSONB | Additional attributes |

---

### `alerts`

System-generated notifications triggered when new incidents hit a watch zone.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `watch_zone_id` | UUID FK → watch_zones | Which zone triggered |
| `incident_id` | UUID FK → incidents | Triggering incident |
| `alert_type` | TEXT | e.g. `NEW_INCIDENT_IN_ZONE`, `SCORE_THRESHOLD_BREACH` |
| `message` | TEXT | Human-readable alert text |
| `is_read` | BOOLEAN | Acknowledgement state |

---

### `reports`

Metadata for generated PDF/HTML Drone Threat Reality Score reports.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `assessment_id` | UUID FK → facility_assessments | Source assessment |
| `created_by` | UUID FK → users | |
| `title` | TEXT | |
| `report_type` | TEXT | `FACILITY_ASSESSMENT` |
| `file_path` | TEXT | Server-side PDF path |
| `file_url` | TEXT | CDN/public URL |
| `html_content` | TEXT | Generated HTML (inline preview) |
| `metadata` | JSONB | Generation parameters |

---

### `audit_logs`

Immutable change trail for all incident and assessment mutations.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organization_id` | UUID FK → organizations | |
| `user_id` | UUID FK → users | Who made the change |
| `entity_type` | TEXT | e.g. `incident`, `assessment` |
| `entity_id` | UUID | PK of the affected record |
| `action` | TEXT | e.g. `APPROVED`, `REJECTED`, `CONFIDENCE_UPDATED` |
| `old_values` | JSONB | State before the change |
| `new_values` | JSONB | State after the change |
| `ip_address` | TEXT | Requester IP |

---

### `sector_cisa_mapping`

Lookup table mapping the 18 operational sectors to CISA's 16 critical infrastructure sectors.
Drives the `auto_assign_cisa_sector()` trigger and sector sensitivity scoring.

| Column | Type | Notes |
|---|---|---|
| `operational_sector` | `sector_enum` PK | |
| `default_cisa_sector` | `cisa_sector_enum` | CISA classification |
| `cisa_subsectors` | TEXT[] | Optional finer subsectors |
| `notes` | TEXT | Classification rationale |

---

## Enumerations

| Type | Values |
|---|---|
| `user_role` | `SUPER_ADMIN`, `ORG_ADMIN`, `ANALYST`, `VIEWER` |
| `review_status` | `PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `NEEDS_MORE_REVIEW` |
| `confidence_tier` | `VERIFIED`, `HIGH`, `MEDIUM`, `LOW`, `UNVERIFIED` |
| `incident_type` | `KINETIC_ATTACK`, `SURVEILLANCE_ISR`, `NEAR_MISS`, `SMUGGLING`, `SIGNAL_INTERFERENCE`, `COLLISION`, `PRIVACY_VIOLATION`, `NUISANCE`, `UNKNOWN` |
| `severity_level` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL` |
| `source_type` | `MANUAL`, `GDELT`, `RSS`, `FAA`, `OFFICIAL_PRESS`, `SENSOR`, `NEWSAPI` |
| `evidence_role` | `DISCOVERY`, `CORROBORATION`, `OFFICIAL_CONFIRMATION`, `CONTRADICTION`, `DUPLICATE`, `REJECTION_SUPPORT` |
| `sector_enum` | 18 operational sectors (see constants) |
| `cisa_sector_enum` | 16 CISA sectors (see constants) |
