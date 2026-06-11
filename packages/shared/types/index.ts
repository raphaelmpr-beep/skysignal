/**
 * SkySignal Shared Domain Types
 *
 * TypeScript types mirroring the PostgreSQL schema and Pydantic schemas.
 * Safe to import in both apps/web (Next.js) and any API client.
 * No runtime dependencies — types only.
 */

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

export type UserRole = 'SUPER_ADMIN' | 'ORG_ADMIN' | 'ANALYST' | 'VIEWER'

export type ReviewStatus =
  | 'PENDING'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'NEEDS_MORE_REVIEW'

export type ConfidenceTier = 'VERIFIED' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNVERIFIED'

export type IncidentType =
  | 'KINETIC_ATTACK'
  | 'SURVEILLANCE_ISR'
  | 'NEAR_MISS'
  | 'SMUGGLING'
  | 'SIGNAL_INTERFERENCE'
  | 'COLLISION'
  | 'PRIVACY_VIOLATION'
  | 'NUISANCE'
  | 'UNKNOWN'

export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFORMATIONAL'

export type SourceType =
  | 'MANUAL'
  | 'GDELT'
  | 'RSS'
  | 'FAA'
  | 'OFFICIAL_PRESS'
  | 'SENSOR'
  | 'NEWSAPI'

export type EvidenceRole =
  | 'DISCOVERY'
  | 'CORROBORATION'
  | 'OFFICIAL_CONFIRMATION'
  | 'CONTRADICTION'
  | 'DUPLICATE'
  | 'REJECTION_SUPPORT'

export type OperationalSector =
  | 'AVIATION'
  | 'MILITARY'
  | 'CRITICAL_INFRA'
  | 'BORDER_SECURITY'
  | 'CORRECTIONS'
  | 'LAW_ENFORCEMENT'
  | 'MARITIME'
  | 'GOVERNMENT'
  | 'STADIUM_VENUE'
  | 'VIP_PROTECTION'
  | 'MEDIA'
  | 'NATURE_RESERVE'
  | 'ENTERPRISE'
  | 'RESIDENTIAL'
  | 'TRANSPORTATION'
  | 'HEALTHCARE'
  | 'EDUCATION'
  | 'LOCAL_GOVERNMENTAL'

export type CisaSector =
  | 'CHEMICAL'
  | 'COMMERCIAL_FACILITIES'
  | 'COMMUNICATIONS'
  | 'CRITICAL_MANUFACTURING'
  | 'DAMS'
  | 'DEFENSE_INDUSTRIAL_BASE'
  | 'EMERGENCY_SERVICES'
  | 'ENERGY'
  | 'FINANCIAL_SERVICES'
  | 'FOOD_AND_AGRICULTURE'
  | 'GOVERNMENT_FACILITIES'
  | 'HEALTHCARE_PUBLIC_HEALTH'
  | 'INFORMATION_TECHNOLOGY'
  | 'NUCLEAR'
  | 'TRANSPORTATION_SYSTEMS'
  | 'WATER_WASTEWATER'

export type ThreatTier = 'MINIMAL' | 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH'

export type ReportType = 'FACILITY_ASSESSMENT'

export type AlertType =
  | 'NEW_INCIDENT_IN_ZONE'
  | 'SCORE_THRESHOLD_BREACH'
  | 'HIGH_CONFIDENCE_INCIDENT'

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export interface Organization {
  id: string
  name: string
  slug: string
  plan: string
  is_active: boolean
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------

export interface User {
  id: string
  organization_id: string
  email: string
  name: string | null
  role: UserRole
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface AuthUser {
  id: string
  email: string
  name: string | null
  role: UserRole
  org_id: string
  org_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------

export interface Source {
  id: string
  organization_id: string | null
  name: string
  source_type: SourceType
  base_url: string | null
  feed_url: string | null
  credibility_score: number
  is_official: boolean
  is_active: boolean
  last_fetched_at: string | null
  fetch_config: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Incident Evidence
// ---------------------------------------------------------------------------

export interface IncidentEvidence {
  id: string
  incident_id: string
  source_id: string | null
  role: EvidenceRole
  title: string | null
  url: string | null
  excerpt: string | null
  published_at: string | null
  credibility_score: number | null
  official_match_score: number | null
  raw_data: Record<string, unknown> | null
  added_by: string | null
  created_at: string
  source?: Pick<Source, 'id' | 'name' | 'source_type' | 'is_official' | 'credibility_score'>
}

// ---------------------------------------------------------------------------
// Incidents
// ---------------------------------------------------------------------------

export interface Incident {
  id: string
  organization_id: string
  title: string
  summary: string | null
  description: string | null
  incident_type: IncidentType
  operational_sector: OperationalSector | null
  cisa_sector: CisaSector | null
  cisa_subsector: string | null
  severity: SeverityLevel
  confidence_score: number
  confidence_tier: ConfidenceTier
  review_status: ReviewStatus
  is_public: boolean
  occurred_at: string
  detected_at: string
  latitude: number | null
  longitude: number | null
  location_name: string | null
  country: string
  region: string | null
  city: string | null
  source_id: string | null
  source_url: string | null
  drone_type: string | null
  drone_make: string | null
  drone_model: string | null
  altitude_agl: number | null
  tags: string[]
  official_match_score: number | null
  created_at: string
  updated_at: string
  evidence?: IncidentEvidence[]
}

/** Lighter version used in list views and map rendering */
export interface IncidentListItem
  extends Pick<
    Incident,
    | 'id'
    | 'organization_id'
    | 'title'
    | 'incident_type'
    | 'severity'
    | 'confidence_score'
    | 'confidence_tier'
    | 'review_status'
    | 'occurred_at'
    | 'latitude'
    | 'longitude'
    | 'location_name'
    | 'cisa_sector'
    | 'operational_sector'
    | 'created_at'
    | 'updated_at'
  > {}

/** Minimal projection for map marker rendering */
export interface MapIncident {
  id: string
  lat: number | null
  lon: number | null
  incident_type: IncidentType | null
  severity: SeverityLevel | null
  confidence_tier: ConfidenceTier
  occurred_at: string | null
  title: string
}

export interface HeatmapPoint {
  lat: number
  lon: number
  weight: number
}

// ---------------------------------------------------------------------------
// SALUTE Reports
// ---------------------------------------------------------------------------

export interface SaluteReport {
  id: string
  incident_id: string | null
  organization_id: string
  submitted_by: string | null

  // S: Size/System
  s_ua_type: string | null
  s_number_of_uas: number | null
  s_size_class: string | null
  s_physical_description: string | null
  s_registration: string | null
  s_manufacturer: string | null
  s_model: string | null

  // A: Activity
  a_flight_behavior: string | null
  a_flight_profile: string | null
  a_direction_of_travel: string | null
  a_duration_observed: string | null
  a_suspected_mission: string | null
  a_swarm_behavior: string | null
  a_payload_suspected: string | null

  // L: Location
  l_observer_position: string | null
  l_uas_latitude: number | null
  l_uas_longitude: number | null
  l_altitude: string | null
  l_location_precision: string | null
  l_operator_location: string | null
  l_launch_origin: string | null
  l_affected_facility: string | null

  // U: Unit/Identity
  u_operator_identity: string | null
  u_affiliation_indicators: string | null
  u_remote_id_broadcast: boolean
  u_remote_id_data: Record<string, unknown> | null
  u_insignia_markings: string | null

  // T: Time
  t_first_observed_at: string | null
  t_last_observed_at: string | null
  t_total_duration_minutes: number | null
  t_lighting_conditions: string | null

  // E: Equipment
  e_rf_frequencies: string | null
  e_payload_equipment: string | null
  e_electronic_signatures: string | null
  e_collision_avoidance: string | null

  // T2: Threat Assessment
  t2_threat_level: string | null
  t2_coa: string | null
  t2_priority: string | null

  // CR: Countermeasure/Response (reporting only — no execution)
  cr_response_actions: string | null
  cr_agencies_notified: string | null

  // PIA: Post-Incident Actions
  pia_evidence_collected: string | null
  pia_follow_up_required: boolean
  pia_notes: string | null

  review_status: ReviewStatus
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Watch Zones
// ---------------------------------------------------------------------------

export interface WatchZone {
  id: string
  organization_id: string
  created_by: string | null
  name: string
  description: string | null
  facility_name: string | null
  address: string | null
  latitude: number
  longitude: number
  radius_miles: number
  alert_on_new_incident: boolean
  is_active: boolean
  cisa_sector: string | null
  operational_sector: OperationalSector | null
  created_at: string
  updated_at: string
}

// ---------------------------------------------------------------------------
// Facility Assessments
// ---------------------------------------------------------------------------

export interface ThreatScoreFactors {
  evidence_confidence: number
  incident_density: number
  recency: number
  facility_proximity: number
  severity: number
  sector_sensitivity: number
  repeat_pattern: number
}

export interface FacilityAssessment {
  id: string
  organization_id: string
  requested_by: string | null
  facility_name: string | null
  address: string | null
  latitude: number
  longitude: number
  radius_miles: number
  time_window_days: number

  threat_reality_score: number
  score_tier: ThreatTier

  factor_evidence_confidence: number
  factor_incident_density: number
  factor_recency: number
  factor_facility_proximity: number
  factor_severity: number
  factor_sector_sensitivity: number
  factor_repeat_pattern: number

  incident_count: number
  nearby_incident_ids: string[]
  cisa_sector: string | null
  operational_sector: OperationalSector | null
  score_explanation: string | null
  raw_factors: ThreatScoreFactors | null

  status: string
  watch_zone_id: string | null
  created_at: string
  updated_at: string
}

export interface AssessmentRequest {
  facility_name: string
  address?: string
  lat: number
  lon: number
  radius_miles: number
  time_window_days: number
}

// ---------------------------------------------------------------------------
// Infrastructure Assets
// ---------------------------------------------------------------------------

export interface InfrastructureAsset {
  id: string
  organization_id: string | null
  name: string
  asset_type: string
  cisa_sector: string | null
  latitude: number
  longitude: number
  address: string | null
  city: string | null
  state: string | null
  is_public: boolean
  metadata: Record<string, unknown>
  created_at: string
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

export interface Alert {
  id: string
  organization_id: string
  watch_zone_id: string | null
  incident_id: string | null
  alert_type: AlertType
  message: string
  is_read: boolean
  created_at: string
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------

export interface Report {
  id: string
  organization_id: string
  assessment_id: string | null
  created_by: string | null
  title: string
  report_type: ReportType
  file_path: string | null
  file_url: string | null
  html_content: string | null
  metadata: Record<string, unknown>
  created_at: string
}

// ---------------------------------------------------------------------------
// Audit Logs
// ---------------------------------------------------------------------------

export interface AuditLog {
  id: string
  organization_id: string | null
  user_id: string | null
  entity_type: string
  entity_id: string | null
  action: string
  old_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface KPIData {
  total_incidents: number
  pending_review: number
  avg_confidence: number
  high_signal_count: number
  incidents_by_severity: Record<SeverityLevel, number>
  incidents_this_month: number
  incidents_last_month: number
}

export interface TimelinePeriod {
  period: string
  count: number
  avg_confidence: number
}

export interface SankeyLink {
  source: string
  target: string
  value: number
}

export interface SankeyData {
  nodes: string[]
  links: SankeyLink[]
}

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface IncidentFilters {
  incident_type?: IncidentType
  severity?: SeverityLevel
  confidence_tier?: ConfidenceTier
  review_status?: ReviewStatus
  cisa_sector?: CisaSector
  operational_sector?: OperationalSector
  search?: string
  since?: string
  until?: string
  skip?: number
  limit?: number
}
