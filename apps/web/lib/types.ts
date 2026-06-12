// Core domain types for SkySignal

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'UNDER_REVIEW'
export type ConfidenceTier = 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'VERY_LOW'
export type ThreatTier = 'MINIMAL' | 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH'
export type IncidentType = 
  | 'SIGHTING' | 'NEAR_MISS' | 'COLLISION' | 'ELECTRONIC_WARFARE' 
  | 'SURVEILLANCE' | 'INCURSION' | 'ATTACK' | 'UNKNOWN'
export type EvidenceRole = 'OFFICIAL_CONFIRMATION' | 'CORROBORATION' | 'DISCOVERY' | 'CONTRADICTION'
export type SourceType = 'OFFICIAL' | 'NEWS' | 'SOCIAL_MEDIA' | 'AVIATION' | 'GOV_DATASET' | 'TIPLINE'

export interface Incident {
  id: string
  title: string
  summary: string
  description?: string
  incident_type: IncidentType
  severity: Severity
  confidence_score: number
  confidence_tier: ConfidenceTier
  review_status: ReviewStatus
  latitude?: number
  longitude?: number
  location_name?: string
  city?: string
  region?: string
  country?: string
  tags?: string[]
  source_url?: string | null
  sector?: string
  occurred_at: string
  created_at: string
  updated_at: string
  source_ids?: string[]
  salute_report?: SALUTEReport
  classification_json?: Record<string, unknown>
  evidence?: Evidence[]
  audit_trail?: AuditEntry[]
  nearby_count?: number
}

export interface Evidence {
  id: string
  incident_id: string
  role: EvidenceRole
  url?: string
  excerpt?: string
  credibility_score?: number
  source_name?: string
  source_type?: SourceType
  published_at?: string
}

export interface AuditEntry {
  id: string
  incident_id: string
  action: string
  actor?: string
  note?: string
  created_at: string
}

export interface SALUTEReport {
  size?: string
  activity?: string
  location?: string
  unit?: string
  time?: string
  equipment?: string
}

export interface Assessment {
  id: string
  facility_name: string
  address?: string
  latitude: number
  longitude: number
  radius_miles: number
  time_window_days: number
  threat_score: number
  threat_tier: ThreatTier
  incident_count: number
  factors: AssessmentFactor[]
  nearby_incidents?: Incident[]
  created_at: string
  watch_zone_id?: string
}

export interface AssessmentFactor {
  factor_name: string
  score: number
  weight: number
  weighted_contribution: number
  description?: string
}

export interface WatchZone {
  id: string
  name: string
  latitude: number
  longitude: number
  radius_miles: number
  assessment_id?: string
  created_at: string
}

export interface Source {
  id: string
  name: string
  source_type: SourceType
  credibility_score: number
  is_official: boolean
  url?: string
  last_fetched?: string
  is_active: boolean
  incident_count?: number
}

export interface Report {
  id: string
  title: string
  facility_name?: string
  assessment_id?: string
  html_content?: string
  pdf_url?: string
  created_at: string
}

export interface KPIData {
  total_incidents: number
  pending_review: number
  avg_confidence: number
  high_signal_facilities: number
  total_incidents_change?: number
  pending_review_change?: number
  avg_confidence_change?: number
  high_signal_facilities_change?: number
}

export interface TimelineDataPoint {
  date?: string     // legacy field
  period?: string   // backend returns 'period' e.g. '2024-W12'
  count: number
  avg_confidence?: number
  critical?: number
  high?: number
  medium?: number
  low?: number
}

export interface SankeyData {
  nodes: Array<{ id: string; name: string }>
  links: Array<{ source: string; target: string; value: number }>
}

export interface SectorDistributionItem {
  sector: string
  count: number
  percentage: number
}

export interface HeatmapPoint {
  lat: number
  lng: number       // normalized from 'lon'
  intensity: number // normalized from 'weight'
}

export interface InfrastructureAsset {
  id: string
  name: string
  asset_type: string
  latitude: number
  longitude: number
  sector?: string
}

export interface MapIncidentsResponse {
  incidents: Incident[]
  total: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface IncidentFilters {
  search?: string
  severity?: Severity[]
  incident_type?: IncidentType[]
  confidence_tier?: ConfidenceTier[]
  review_status?: ReviewStatus[]
  sector?: string[]
  source_type?: SourceType[]
  date_from?: string
  date_to?: string
  country?: string
  region?: string
  source_tag?: 'faa' | 'gdelt' | 'osint' | 'dfend' | 'manual'
  page?: number
  per_page?: number
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  limit?: number
}

export interface MapFilters {
  severity?: string
  incident_type?: string
  sector?: string
  source_type?: string
  review_status?: string
  date_from?: string
  date_to?: string
}

export interface CreateAssessmentInput {
  facility_name: string
  address?: string
  latitude: number
  longitude: number
  radius_miles: number
  time_window_days: number
}
