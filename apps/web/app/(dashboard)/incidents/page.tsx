'use client'

import { useState, useEffect } from 'react'
import { Search, X, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { IncidentTable } from '@/components/incidents/IncidentTable'
import { fetchIncidents } from '@/lib/api'
import type { Incident, PaginatedResponse, IncidentFilters } from '@/lib/types'

const US_STATES: { abbr: string; name: string }[] = [
  { abbr: 'AL', name: 'Alabama' }, { abbr: 'AK', name: 'Alaska' }, { abbr: 'AZ', name: 'Arizona' },
  { abbr: 'AR', name: 'Arkansas' }, { abbr: 'CA', name: 'California' }, { abbr: 'CO', name: 'Colorado' },
  { abbr: 'CT', name: 'Connecticut' }, { abbr: 'DE', name: 'Delaware' }, { abbr: 'FL', name: 'Florida' },
  { abbr: 'GA', name: 'Georgia' }, { abbr: 'HI', name: 'Hawaii' }, { abbr: 'ID', name: 'Idaho' },
  { abbr: 'IL', name: 'Illinois' }, { abbr: 'IN', name: 'Indiana' }, { abbr: 'IA', name: 'Iowa' },
  { abbr: 'KS', name: 'Kansas' }, { abbr: 'KY', name: 'Kentucky' }, { abbr: 'LA', name: 'Louisiana' },
  { abbr: 'ME', name: 'Maine' }, { abbr: 'MD', name: 'Maryland' }, { abbr: 'MA', name: 'Massachusetts' },
  { abbr: 'MI', name: 'Michigan' }, { abbr: 'MN', name: 'Minnesota' }, { abbr: 'MS', name: 'Mississippi' },
  { abbr: 'MO', name: 'Missouri' }, { abbr: 'MT', name: 'Montana' }, { abbr: 'NE', name: 'Nebraska' },
  { abbr: 'NV', name: 'Nevada' }, { abbr: 'NH', name: 'New Hampshire' }, { abbr: 'NJ', name: 'New Jersey' },
  { abbr: 'NM', name: 'New Mexico' }, { abbr: 'NY', name: 'New York' }, { abbr: 'NC', name: 'North Carolina' },
  { abbr: 'ND', name: 'North Dakota' }, { abbr: 'OH', name: 'Ohio' }, { abbr: 'OK', name: 'Oklahoma' },
  { abbr: 'OR', name: 'Oregon' }, { abbr: 'PA', name: 'Pennsylvania' }, { abbr: 'RI', name: 'Rhode Island' },
  { abbr: 'SC', name: 'South Carolina' }, { abbr: 'SD', name: 'South Dakota' }, { abbr: 'TN', name: 'Tennessee' },
  { abbr: 'TX', name: 'Texas' }, { abbr: 'UT', name: 'Utah' }, { abbr: 'VT', name: 'Vermont' },
  { abbr: 'VA', name: 'Virginia' }, { abbr: 'WA', name: 'Washington' }, { abbr: 'WV', name: 'West Virginia' },
  { abbr: 'WI', name: 'Wisconsin' }, { abbr: 'WY', name: 'Wyoming' }, { abbr: 'DC', name: 'District of Columbia' },
]

export default function IncidentsPage() {
  const [searchTerm, setSearchTerm]       = useState('')
  const [severity, setSeverity]           = useState('')
  const [incidentType, setIncidentType]   = useState('')
  const [confidenceTier, setConfidenceTier] = useState('')
  const [reviewStatus, setReviewStatus]   = useState('')
  const [dateFrom, setDateFrom]           = useState('')
  const [dateTo, setDateTo]               = useState('')
  const [country, setCountry]             = useState('')
  const [usState, setUsState]             = useState('')
  const [page, setPage]                   = useState(1)

  const [data, setData]           = useState<PaginatedResponse<Incident> | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const f: IncidentFilters & { country?: string; region?: string } = { per_page: 50, page }
    if (searchTerm)     f.search           = searchTerm
    if (severity)       f.severity         = [severity as 'CRITICAL']
    if (incidentType)   f.incident_type    = [incidentType as 'SIGHTING']
    if (confidenceTier) f.confidence_tier  = [confidenceTier as 'HIGH']
    if (reviewStatus)   f.review_status    = [reviewStatus as 'PENDING']
    if (dateFrom)       f.date_from        = dateFrom
    if (dateTo)         f.date_to          = dateTo
    if (country)        f.country          = country
    // US state maps to the region field on the backend
    if (usState)        f.region           = usState

    setIsLoading(true)
    fetchIncidents(f as IncidentFilters)
      .then(setData)
      .catch(console.error)
      .finally(() => setIsLoading(false))
  }, [searchTerm, severity, incidentType, confidenceTier, reviewStatus, dateFrom, dateTo, country, usState, page])

  const clearFilters = () => {
    setSearchTerm(''); setSeverity(''); setIncidentType('')
    setConfidenceTier(''); setReviewStatus('')
    setDateFrom(''); setDateTo('')
    setCountry(''); setUsState('')
    setPage(1)
  }

  const hasFilters = searchTerm || severity || incidentType || confidenceTier ||
    reviewStatus || dateFrom || dateTo || country || usState

  const incidents = data?.items || []
  const total     = data?.total || 0
  const pages     = data?.pages || 1

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Incidents</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{total.toLocaleString()} total incidents</p>
        </div>
        {isLoading && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4 space-y-3">
          {/* Row 1: search + severity + type + confidence + status */}
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="Search title, location, city, state…"
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1) }}
                className="pl-9"
              />
            </div>

            <Select value={severity} onValueChange={(v) => { setSeverity(v === '_all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_all">All Severities</SelectItem>
                <SelectItem value="CRITICAL">Critical</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
              </SelectContent>
            </Select>

            <Select value={incidentType} onValueChange={(v) => { setIncidentType(v === '_all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_all">All Types</SelectItem>
                <SelectItem value="SIGHTING">Sighting</SelectItem>
                <SelectItem value="NEAR_MISS">Near Miss</SelectItem>
                <SelectItem value="SURVEILLANCE_ISR">Surveillance / ISR</SelectItem>
                <SelectItem value="SMUGGLING">Smuggling</SelectItem>
                <SelectItem value="INCURSION">Incursion</SelectItem>
                <SelectItem value="COLLISION">Collision</SelectItem>
                <SelectItem value="ELECTRONIC_WARFARE">Electronic Warfare</SelectItem>
                <SelectItem value="ATTACK">Attack</SelectItem>
              </SelectContent>
            </Select>

            <Select value={confidenceTier} onValueChange={(v) => { setConfidenceTier(v === '_all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Confidence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_all">All Confidence</SelectItem>
                <SelectItem value="VERIFIED">Verified</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
                <SelectItem value="UNVERIFIED">Unverified</SelectItem>
              </SelectContent>
            </Select>

            <Select value={reviewStatus} onValueChange={(v) => { setReviewStatus(v === '_all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_all">All Statuses</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Row 2: date range + country + US state + clear */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground whitespace-nowrap">From</label>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setPage(1) }}
                className="w-40"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground whitespace-nowrap">To</label>
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setPage(1) }}
                className="w-40"
              />
            </div>

            <Select value={country} onValueChange={(v) => { setCountry(v === '_all' ? '' : v); setUsState(''); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_all">All Countries</SelectItem>
                <SelectItem value="US">United States</SelectItem>
                <SelectItem value="CA">Canada</SelectItem>
                <SelectItem value="GB">United Kingdom</SelectItem>
                <SelectItem value="AU">Australia</SelectItem>
                <SelectItem value="DE">Germany</SelectItem>
                <SelectItem value="FR">France</SelectItem>
                <SelectItem value="IL">Israel</SelectItem>
                <SelectItem value="UA">Ukraine</SelectItem>
              </SelectContent>
            </Select>

            {/* US State — only shown when country = US or no country selected */}
            {(country === '' || country === 'US') && (
              <Select value={usState} onValueChange={(v) => { setUsState(v === '_all' ? '' : v); setPage(1) }}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="US State" />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  <SelectItem value="_all">All States</SelectItem>
                  {US_STATES.map((s) => (
                    <SelectItem key={s.abbr} value={s.abbr}>{s.abbr} — {s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1.5">
                <X className="w-3.5 h-3.5" />
                Clear filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <IncidentTable incidents={incidents} loading={isLoading} />
        </CardContent>
      </Card>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {page} of {pages} &mdash; {total.toLocaleString()} results
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(page - 1)} disabled={page <= 1}>
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={page >= pages}>
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
