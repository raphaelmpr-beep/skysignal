import { getAuthHeaders } from './auth'
import type {
  Incident,
  Assessment,
  Source,
  Report,
  KPIData,
  TimelineDataPoint,
  SankeyData,
  SectorDistributionItem,
  HeatmapPoint,
  PaginatedResponse,
  IncidentFilters,
  MapFilters,
  CreateAssessmentInput,
  WatchZone,
} from './types'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers as Record<string, string> || {}),
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }

  return res.json() as Promise<T>
}

function buildQuery(params: Record<string, unknown>): string {
  const parts: string[] = []
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) {
      value.forEach((v) => parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(v))}`))
    } else {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    }
  }
  return parts.length > 0 ? `?${parts.join('&')}` : ''
}

// Auth
export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Login failed')
  }
  return res.json() as Promise<{ access_token: string; user: { id: string; email: string; name: string; role: string; org_name?: string } }>
}

// Incidents
export async function fetchIncidents(params: IncidentFilters = {}): Promise<PaginatedResponse<Incident>> {
  const query = buildQuery(params as Record<string, unknown>)
  return apiFetch<PaginatedResponse<Incident>>(`/api/incidents${query}`)
}

export async function fetchIncident(id: string): Promise<Incident> {
  return apiFetch<Incident>(`/api/incidents/${id}`)
}

export async function reviewIncident(
  id: string,
  action: 'approve' | 'reject' | 'request_review' | 'merge',
  note?: string
): Promise<Incident> {
  return apiFetch<Incident>(`/api/incidents/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ action, note }),
  })
}

export async function addIncidentNote(id: string, note: string): Promise<void> {
  return apiFetch<void>(`/api/incidents/${id}/notes`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  })
}

export async function addEvidence(id: string, evidence: {
  url?: string
  excerpt?: string
  role: string
  source_name?: string
}): Promise<void> {
  return apiFetch<void>(`/api/incidents/${id}/evidence`, {
    method: 'POST',
    body: JSON.stringify(evidence),
  })
}

// Map
export async function fetchMapIncidents(params: MapFilters = {}): Promise<{ incidents: Incident[]; total: number }> {
  const query = buildQuery(params as Record<string, unknown>)
  // Backend returns a plain array of {id, lat, lon, ...} — wrap and normalize lat/lon field names
  const raw = await apiFetch<Array<Record<string, unknown>> | { incidents: Incident[]; total: number }>(`/api/map/incidents${query}`)
  if (Array.isArray(raw)) {
    const incidents = raw.map(r => ({
      ...r,
      latitude: r.latitude ?? r.lat,
      longitude: r.longitude ?? r.lon,
    })) as unknown as Incident[]
    return { incidents, total: incidents.length }
  }
  return raw as { incidents: Incident[]; total: number }
}

export async function fetchHeatmap(params: MapFilters = {}): Promise<HeatmapPoint[]> {
  const query = buildQuery(params as Record<string, unknown>)
  // Backend returns { lat, lon, weight } — normalize to { lat, lng, intensity }
  const raw = await apiFetch<Array<{ lat: number; lon?: number; lng?: number; weight?: number; intensity?: number }>>(`/api/map/heatmap${query}`)
  return raw.map(p => ({ lat: p.lat, lng: p.lng ?? p.lon ?? 0, intensity: p.intensity ?? p.weight ?? 0.5 }))
}

export async function fetchWatchZones(): Promise<WatchZone[]> {
  const raw = await apiFetch<{ items: WatchZone[] } | WatchZone[]>('/api/watch-zones')
  return Array.isArray(raw) ? raw : (raw as { items: WatchZone[] }).items ?? []
}

// Assessments
export async function createAssessment(data: CreateAssessmentInput): Promise<Assessment> {
  return apiFetch<Assessment>('/api/assessments', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function fetchAssessment(id: string): Promise<Assessment> {
  return apiFetch<Assessment>(`/api/assessments/${id}`)
}

export async function fetchAssessments(): Promise<Assessment[]> {
  // Backend returns paginated { total, items } — unwrap and normalize lat/lon → latitude/longitude
  const raw = await apiFetch<{ items: Record<string, unknown>[] } | Record<string, unknown>[]>('/api/assessments')
  const items: Record<string, unknown>[] = Array.isArray(raw) ? raw : (raw as { items: Record<string, unknown>[] }).items ?? []
  return items.map((a) => ({
    ...a,
    latitude: a.latitude ?? a.lat,
    longitude: a.longitude ?? a.lon,
  })) as unknown as Assessment[]
}

export async function saveWatchZone(assessmentId: string): Promise<WatchZone> {
  return apiFetch<WatchZone>(`/api/assessments/${assessmentId}/watch-zone`, {
    method: 'POST',
  })
}

export async function generateReport(assessmentId: string): Promise<{ report_id: string; html_url: string }> {
  return apiFetch<{ report_id: string; html_url: string }>(`/api/assessments/${assessmentId}/report`, {
    method: 'POST',
  })
}

// Analytics
export async function fetchAnalyticsKPI(): Promise<KPIData> {
  return apiFetch<KPIData>('/api/analytics/kpi')
}

export async function fetchTimeline(days = 90): Promise<TimelineDataPoint[]> {
  return apiFetch<TimelineDataPoint[]>(`/api/analytics/timeline?days=${days}`)
}

export async function fetchSankeyData(): Promise<SankeyData> {
  return apiFetch<SankeyData>('/api/analytics/sankey')
}

export async function fetchSectorDistribution(): Promise<SectorDistributionItem[]> {
  // Backend returns { cisa_sector: {ENERGY: N, ...}, operational_sector: {...} }
  // Normalize to SectorDistributionItem[] using operational_sector
  const raw = await apiFetch<Record<string, Record<string, number>> | SectorDistributionItem[]>('/api/analytics/sector-distribution')
  if (Array.isArray(raw)) return raw
  const sectorMap = (raw as Record<string, Record<string, number>>).operational_sector
    ?? (raw as Record<string, Record<string, number>>).cisa_sector
    ?? {}
  const total = Object.values(sectorMap).reduce((s, n) => s + n, 0) || 1
  return Object.entries(sectorMap)
    .map(([sector, count]) => ({ sector, count, percentage: (count / total) * 100 }))
    .sort((a, b) => b.count - a.count)
}

export async function fetchConfidenceDistribution(): Promise<{ tier: string; count: number }[]> {
  // Backend route is confidence-histogram, returns { HIGH: N, MEDIUM: N, ... }
  const raw = await apiFetch<Record<string, number> | { tier: string; count: number }[]>('/api/analytics/confidence-histogram')
  if (Array.isArray(raw)) return raw
  const ORDER = ['VERIFIED', 'HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']
  return ORDER
    .filter(t => (raw as Record<string, number>)[t] !== undefined)
    .map(tier => ({ tier, count: (raw as Record<string, number>)[tier] }))
}

export async function fetchSourceDistribution(): Promise<{ source: string; count: number }[]> {
  const raw = await apiFetch<Record<string, number> | { source: string; count: number }[]>('/api/analytics/source-distribution')
  if (Array.isArray(raw)) return raw
  // Normalize dict { FAA: 100, GDELT: 20 } → [{source, count}]
  return Object.entries(raw as Record<string, number>)
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count)
}

// Sources
export async function fetchSources(): Promise<Source[]> {
  // Backend returns paginated { total, items } — unwrap
  const raw = await apiFetch<{ items: Source[] } | Source[]>('/api/sources')
  return Array.isArray(raw) ? raw : (raw as { items: Source[] }).items ?? []
}

export async function updateSourceActive(id: string, is_active: boolean): Promise<Source> {
  return apiFetch<Source>(`/api/sources/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active }),
  })
}

// Reports
export async function fetchReports(): Promise<Report[]> {
  // Backend returns paginated { total, items } — unwrap
  const raw = await apiFetch<{ items: Report[] } | Report[]>('/api/reports')
  return Array.isArray(raw) ? raw : (raw as { items: Report[] }).items ?? []
}

export async function fetchReport(id: string): Promise<Report> {
  return apiFetch<Report>(`/api/reports/${id}`)
}

// Geocoding (Nominatim - free, no token needed)
export async function geocodeAddress(address: string): Promise<{ lat: number; lon: number; display_name: string } | null> {
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
    { headers: { 'User-Agent': 'SkySignal/1.0' } }
  )
  const data = await res.json() as Array<{ lat: string; lon: string; display_name: string }>
  if (!data.length) return null
  return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon), display_name: data[0].display_name }
}
