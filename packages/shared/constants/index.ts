/**
 * SkySignal Shared Constants
 *
 * Enumerations, weights, and lookup data shared between web and API clients.
 * All values mirror the PostgreSQL enums and scoring algorithm exactly.
 */

export const INCIDENT_TYPES = [
  'KINETIC_ATTACK',
  'SURVEILLANCE_ISR',
  'NEAR_MISS',
  'SMUGGLING',
  'SIGNAL_INTERFERENCE',
  'COLLISION',
  'PRIVACY_VIOLATION',
  'NUISANCE',
  'UNKNOWN',
] as const

export const SEVERITY_LEVELS = [
  'CRITICAL',
  'HIGH',
  'MEDIUM',
  'LOW',
  'INFORMATIONAL',
] as const

export const CONFIDENCE_TIERS = [
  'VERIFIED',
  'HIGH',
  'MEDIUM',
  'LOW',
  'UNVERIFIED',
] as const

export const REVIEW_STATUSES = [
  'PENDING',
  'IN_REVIEW',
  'APPROVED',
  'REJECTED',
  'NEEDS_MORE_REVIEW',
] as const

export const OPERATIONAL_SECTORS = [
  'AVIATION',
  'MILITARY',
  'CRITICAL_INFRA',
  'BORDER_SECURITY',
  'CORRECTIONS',
  'LAW_ENFORCEMENT',
  'MARITIME',
  'GOVERNMENT',
  'STADIUM_VENUE',
  'VIP_PROTECTION',
  'MEDIA',
  'NATURE_RESERVE',
  'ENTERPRISE',
  'RESIDENTIAL',
  'TRANSPORTATION',
  'HEALTHCARE',
  'EDUCATION',
  'LOCAL_GOVERNMENTAL',
] as const

export const CISA_SECTORS = [
  'CHEMICAL',
  'COMMERCIAL_FACILITIES',
  'COMMUNICATIONS',
  'CRITICAL_MANUFACTURING',
  'DAMS',
  'DEFENSE_INDUSTRIAL_BASE',
  'EMERGENCY_SERVICES',
  'ENERGY',
  'FINANCIAL_SERVICES',
  'FOOD_AND_AGRICULTURE',
  'GOVERNMENT_FACILITIES',
  'HEALTHCARE_PUBLIC_HEALTH',
  'INFORMATION_TECHNOLOGY',
  'NUCLEAR',
  'TRANSPORTATION_SYSTEMS',
  'WATER_WASTEWATER',
] as const

export const SOURCE_TYPES = [
  'MANUAL',
  'GDELT',
  'RSS',
  'FAA',
  'OFFICIAL_PRESS',
  'SENSOR',
  'NEWSAPI',
] as const

export const EVIDENCE_ROLES = [
  'DISCOVERY',
  'CORROBORATION',
  'OFFICIAL_CONFIRMATION',
  'CONTRADICTION',
  'DUPLICATE',
  'REJECTION_SUPPORT',
] as const

// ---------------------------------------------------------------------------
// Threat Score
// ---------------------------------------------------------------------------

export const THREAT_SCORE_TIERS = {
  MINIMAL: { min: 0, max: 20, label: 'Minimal Signal', color: '#607080' },
  LOW: { min: 21, max: 40, label: 'Low Signal', color: '#3B82F6' },
  MODERATE: { min: 41, max: 60, label: 'Moderate Signal', color: '#F0A500' },
  ELEVATED: { min: 61, max: 80, label: 'Elevated Signal', color: '#E05C1A' },
  HIGH: { min: 81, max: 100, label: 'High Signal', color: '#DC2626' },
} as const

export const THREAT_SCORE_WEIGHTS = {
  evidence_confidence: 0.30,
  incident_density: 0.20,
  recency: 0.15,
  facility_proximity: 0.15,
  severity: 0.10,
  sector_sensitivity: 0.05,
  repeat_pattern: 0.05,
} as const

export const THREAT_SCORE_FACTOR_LABELS: Record<keyof typeof THREAT_SCORE_WEIGHTS, string> = {
  evidence_confidence: 'Evidence Confidence',
  incident_density: 'Incident Density',
  recency: 'Recency',
  facility_proximity: 'Facility Proximity',
  severity: 'Severity',
  sector_sensitivity: 'Sector Sensitivity',
  repeat_pattern: 'Repeat Pattern',
}

// ---------------------------------------------------------------------------
// Official Match Score component weights
// ---------------------------------------------------------------------------

export const OFFICIAL_MATCH_SCORE_WEIGHTS = {
  date_match: 25,
  location_match: 25,
  facility_match: 20,
  incident_type_match: 15,
  jurisdiction_match: 10,
  named_entity_match: 5,
} as const

/** Threshold above which official_match_score triggers confidence boost */
export const OFFICIAL_MATCH_AUTO_BOOST_THRESHOLD = 80

// ---------------------------------------------------------------------------
// Assessment form options
// ---------------------------------------------------------------------------

export const RADIUS_OPTIONS = [1, 5, 10, 25] as const
export const TIME_WINDOW_OPTIONS = [30, 90, 180, 365, 1095] as const

export const TIME_WINDOW_LABELS: Record<number, string> = {
  30: '30 days',
  90: '90 days',
  180: '6 months',
  365: '1 year',
  1095: '3 years',
}

// ---------------------------------------------------------------------------
// Severity display metadata
// ---------------------------------------------------------------------------

export const SEVERITY_META = {
  CRITICAL: { label: 'Critical', color: '#DC2626', score: 100 },
  HIGH: { label: 'High', color: '#E05C1A', score: 75 },
  MEDIUM: { label: 'Medium', color: '#F0A500', score: 50 },
  LOW: { label: 'Low', color: '#3B82F6', score: 25 },
  INFORMATIONAL: { label: 'Info', color: '#607080', score: 10 },
} as const

// ---------------------------------------------------------------------------
// Confidence display metadata
// ---------------------------------------------------------------------------

export const CONFIDENCE_META = {
  VERIFIED: { label: 'Verified', color: '#16A34A', minScore: 80 },
  HIGH: { label: 'High', color: '#65A30D', minScore: 60 },
  MEDIUM: { label: 'Medium', color: '#CA8A04', minScore: 40 },
  LOW: { label: 'Low', color: '#EA580C', minScore: 20 },
  UNVERIFIED: { label: 'Unverified', color: '#6B7280', minScore: 0 },
} as const

// ---------------------------------------------------------------------------
// Incident type display metadata
// ---------------------------------------------------------------------------

export const INCIDENT_TYPE_LABELS: Record<string, string> = {
  KINETIC_ATTACK: 'Kinetic Attack',
  SURVEILLANCE_ISR: 'Surveillance / ISR',
  NEAR_MISS: 'Near Miss',
  SMUGGLING: 'Smuggling',
  SIGNAL_INTERFERENCE: 'Signal Interference',
  COLLISION: 'Collision',
  PRIVACY_VIOLATION: 'Privacy Violation',
  NUISANCE: 'Nuisance',
  UNKNOWN: 'Unknown',
}

// ---------------------------------------------------------------------------
// Map defaults
// ---------------------------------------------------------------------------

export const MAP_DEFAULTS = {
  lat: 39.8283,
  lng: -98.5795,
  zoom: 4,
} as const

export const MAP_CLUSTER_MAX_ZOOM = 14
export const MAP_HEATMAP_RADIUS = 25

// ---------------------------------------------------------------------------
// Pagination defaults
// ---------------------------------------------------------------------------

export const DEFAULT_PAGE_SIZE = 25
export const MAX_PAGE_SIZE = 100

// ---------------------------------------------------------------------------
// API paths
// ---------------------------------------------------------------------------

export const API_PATHS = {
  auth: {
    login: '/api/auth/login',
  },
  incidents: {
    list: '/api/incidents',
    detail: (id: string) => `/api/incidents/${id}`,
    evidence: (id: string) => `/api/incidents/${id}/evidence`,
  },
  assessments: {
    create: '/api/assessments',
    list: '/api/assessments',
    detail: (id: string) => `/api/assessments/${id}`,
  },
  map: {
    incidents: '/api/map/incidents',
    heatmap: '/api/map/heatmap',
  },
  analytics: {
    kpi: '/api/analytics/kpi',
    sankey: '/api/analytics/sankey',
    timeline: '/api/analytics/timeline',
  },
  admin: {
    reviewQueue: '/api/admin/review-queue',
    approve: (id: string) => `/api/admin/incidents/${id}/approve`,
    reject: (id: string) => `/api/admin/incidents/${id}/reject`,
  },
  salute: {
    submit: '/api/salute',
    list: '/api/salute',
  },
  reports: {
    generate: '/api/reports',
    list: '/api/reports',
    download: (id: string) => `/api/reports/${id}/pdf`,
  },
  sources: {
    list: '/api/sources',
    create: '/api/sources',
    detail: (id: string) => `/api/sources/${id}`,
  },
} as const
