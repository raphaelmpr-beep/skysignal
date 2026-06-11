'use client'

import { useState, useEffect } from 'react'
import { Search, X, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { IncidentTable } from '@/components/incidents/IncidentTable'
import { fetchIncidents } from '@/lib/api'
import type { Incident, PaginatedResponse, IncidentFilters } from '@/lib/types'

export default function IncidentsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [severity, setSeverity] = useState('')
  const [incidentType, setIncidentType] = useState('')
  const [confidenceTier, setConfidenceTier] = useState('')
  const [reviewStatus, setReviewStatus] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)

  const [data, setData] = useState<PaginatedResponse<Incident> | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const f: IncidentFilters = { per_page: 50, page }
    if (searchTerm) f.search = searchTerm
    if (severity) f.severity = [severity as 'CRITICAL']
    if (incidentType) f.incident_type = [incidentType as 'SIGHTING']
    if (confidenceTier) f.confidence_tier = [confidenceTier as 'HIGH']
    if (reviewStatus) f.review_status = [reviewStatus as 'PENDING']
    if (dateFrom) f.date_from = dateFrom
    if (dateTo) f.date_to = dateTo

    setIsLoading(true)
    fetchIncidents(f)
      .then(setData)
      .catch(console.error)
      .finally(() => setIsLoading(false))
  }, [searchTerm, severity, incidentType, confidenceTier, reviewStatus, dateFrom, dateTo, page])

  const clearFilters = () => {
    setSearchTerm(''); setSeverity(''); setIncidentType('')
    setConfidenceTier(''); setReviewStatus(''); setDateFrom(''); setDateTo('')
    setPage(1)
  }

  const hasFilters = searchTerm || severity || incidentType || confidenceTier || reviewStatus || dateFrom || dateTo
  const incidents = data?.items || []
  const total = data?.total || 0
  const pages = data?.pages || 1

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
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            {/* Search */}
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="Search incidents..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1) }}
                className="pl-9"
              />
            </div>

            {/* Severity */}
            <Select value={severity} onValueChange={(v) => { setSeverity(v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="CRITICAL">Critical</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
                <SelectItem value="UNKNOWN">Unknown</SelectItem>
              </SelectContent>
            </Select>

            {/* Type */}
            <Select value={incidentType} onValueChange={(v) => { setIncidentType(v); setPage(1) }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="SIGHTING">Sighting</SelectItem>
                <SelectItem value="NEAR_MISS">Near Miss</SelectItem>
                <SelectItem value="COLLISION">Collision</SelectItem>
                <SelectItem value="ELECTRONIC_WARFARE">Electronic Warfare</SelectItem>
                <SelectItem value="SURVEILLANCE">Surveillance</SelectItem>
                <SelectItem value="INCURSION">Incursion</SelectItem>
                <SelectItem value="ATTACK">Attack</SelectItem>
              </SelectContent>
            </Select>

            {/* Confidence */}
            <Select value={confidenceTier} onValueChange={(v) => { setConfidenceTier(v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Confidence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="VERY_HIGH">Very High</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
                <SelectItem value="VERY_LOW">Very Low</SelectItem>
              </SelectContent>
            </Select>

            {/* Status */}
            <Select value={reviewStatus} onValueChange={(v) => { setReviewStatus(v); setPage(1) }}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
              </SelectContent>
            </Select>

            {/* Date range */}
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1) }}
              className="w-40"
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1) }}
              className="w-40"
            />

            {hasFilters && (
              <Button variant="ghost" size="icon" onClick={clearFilters} title="Clear filters">
                <X className="w-4 h-4" />
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page <= 1}
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page >= pages}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
