'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft, MapPin, Calendar, CheckCircle, XCircle, Eye, AlertOctagon,
  Plus, FileText, ExternalLink, Clock, User, Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { SeverityBadge } from '@/components/incidents/SeverityBadge'
import { ConfidenceBadge } from '@/components/incidents/ConfidenceBadge'
import { ReviewStatusBadge } from '@/components/incidents/ReviewStatusBadge'
import { fetchIncident, reviewIncident } from '@/lib/api'
import {
  formatDate, formatDateTime, getEvidenceRoleBg, cn,
} from '@/lib/utils'
import type { Incident } from '@/lib/types'
import dynamic from 'next/dynamic'

const IncidentMap = dynamic(
  () => import('@/components/map/IncidentMap').then((m) => m.IncidentMap),
  { ssr: false }
)

export default function IncidentDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    fetchIncident(id)
      .then(setIncident)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  async function handleAction(action: 'approve' | 'reject' | 'request_review' | 'merge') {
    setActionLoading(true)
    try {
      const updated = await reviewIncident(id, action)
      setIncident(updated)
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-4">
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
          <Skeleton className="h-80 w-full" />
        </div>
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Incident not found</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/incidents">Back to incidents</Link>
        </Button>
      </div>
    )
  }

  const evidenceRoleLabel: Record<string, string> = {
    OFFICIAL_CONFIRMATION: 'Official',
    CORROBORATION: 'Corroboration',
    DISCOVERY: 'Discovery',
    CONTRADICTION: 'Contradiction',
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link href="/incidents">
          <ArrowLeft className="w-4 h-4" />
          Incidents
        </Link>
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <SeverityBadge severity={incident.severity} />
            <ConfidenceBadge tier={incident.confidence_tier} score={incident.confidence_score} />
            <ReviewStatusBadge status={incident.review_status} />
          </div>
          <h1 className="text-2xl font-bold text-foreground">{incident.title}</h1>
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              {formatDateTime(incident.occurred_at)}
            </span>
            {incident.location_name && (
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" />
                {incident.location_name}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {incident.review_status === 'PENDING' || incident.review_status === 'UNDER_REVIEW' ? (
            <>
              <Button
                variant="success"
                size="sm"
                onClick={() => handleAction('approve')}
                disabled={actionLoading}
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                Approve
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleAction('reject')}
                disabled={actionLoading}
              >
                <XCircle className="w-4 h-4" />
                Reject
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction('request_review')}
              disabled={actionLoading}
            >
              <Eye className="w-4 h-4" />
              Request Review
            </Button>
          )}
          <Button variant="outline" size="sm">
            <AlertOctagon className="w-4 h-4" />
            Escalate
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main */}
        <div className="xl:col-span-2 space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground/90 leading-relaxed">{incident.summary}</p>
              {incident.description && (
                <p className="text-sm text-foreground/80 leading-relaxed mt-3">{incident.description}</p>
              )}
            </CardContent>
          </Card>

          {/* Metadata grid */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[
                  { label: 'Incident Type', value: incident.incident_type?.replace(/_/g, ' ') },
                  { label: 'Severity', value: <SeverityBadge severity={incident.severity} /> },
                  { label: 'Confidence', value: <ConfidenceBadge tier={incident.confidence_tier} score={incident.confidence_score} /> },
                  { label: 'Review Status', value: <ReviewStatusBadge status={incident.review_status} /> },
                  { label: 'Sector', value: incident.sector || '—' },
                  { label: 'Location', value: incident.location_name || (incident.latitude ? `${incident.latitude?.toFixed(4)}, ${incident.longitude?.toFixed(4)}` : '—') },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <p className="text-xs text-muted-foreground mb-1">{label}</p>
                    <div className="text-sm font-medium text-foreground">{value}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* SALUTE fields */}
          {incident.salute_report && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">SALUTE Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {[
                    ['S — Size', incident.salute_report.size],
                    ['A — Activity', incident.salute_report.activity],
                    ['L — Location', incident.salute_report.location],
                    ['U — Unit', incident.salute_report.unit],
                    ['T — Time', incident.salute_report.time],
                    ['E — Equipment', incident.salute_report.equipment],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">{label}</p>
                      <p className="text-sm text-foreground">{value || '—'}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Evidence */}
          {incident.evidence && incident.evidence.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">Evidence Stack ({incident.evidence.length})</CardTitle>
                <Button variant="outline" size="sm">
                  <Plus className="w-4 h-4" />
                  Add Evidence
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                {incident.evidence.map((ev) => (
                  <div key={ev.id} className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className={cn(
                        'inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium',
                        getEvidenceRoleBg(ev.role as 'OFFICIAL_CONFIRMATION' | 'CORROBORATION' | 'DISCOVERY' | 'CONTRADICTION')
                      )}>
                        {evidenceRoleLabel[ev.role] || ev.role}
                      </span>
                      {ev.credibility_score !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          Credibility: {Math.round(ev.credibility_score * 100)}%
                        </span>
                      )}
                    </div>
                    {ev.excerpt && (
                      <p className="text-sm text-foreground/80 leading-relaxed mb-2">&quot;{ev.excerpt}&quot;</p>
                    )}
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {ev.source_name && <span>{ev.source_name}</span>}
                      {ev.published_at && <span>{formatDate(ev.published_at)}</span>}
                      {ev.url && (
                        <a
                          href={ev.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-teal hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Source
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Audit trail */}
          {incident.audit_trail && incident.audit_trail.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Audit Trail</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {incident.audit_trail.map((entry) => (
                    <div key={entry.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-6 h-6 rounded-full bg-white/[0.08] flex items-center justify-center shrink-0">
                          <User className="w-3 h-3 text-muted-foreground" />
                        </div>
                        <div className="w-px flex-1 bg-white/[0.06] mt-1" />
                      </div>
                      <div className="pb-3">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-sm font-medium text-foreground">{entry.action}</span>
                          {entry.actor && (
                            <span className="text-xs text-muted-foreground">by {entry.actor}</span>
                          )}
                        </div>
                        {entry.note && (
                          <p className="text-xs text-muted-foreground">{entry.note}</p>
                        )}
                        <span className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                          <Clock className="w-3 h-3" />
                          {formatDateTime(entry.created_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Mini map */}
          {incident.latitude && incident.longitude && (
            <Card className="overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Location</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-48">
                  <IncidentMap
                    incidents={[incident]}
                    centerLat={incident.latitude}
                    centerLng={incident.longitude}
                    zoom={10}
                    height="192px"
                  />
                </div>
                <div className="p-3 border-t border-white/[0.08]">
                  <Button variant="outline" size="sm" className="w-full" asChild>
                    <Link href={`/map?lat=${incident.latitude}&lng=${incident.longitude}`}>
                      <MapPin className="w-4 h-4" />
                      View on Map
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Report ID</span>
                <span className="font-mono text-xs text-foreground">{incident.id.slice(0, 8)}…</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Reported</span>
                <span className="text-foreground">{formatDate(incident.created_at)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Updated</span>
                <span className="text-foreground">{formatDate(incident.updated_at)}</span>
              </div>
              {incident.nearby_count !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Nearby (50mi)</span>
                  <span className="text-foreground">{incident.nearby_count}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Plus className="w-4 h-4" />
                Add Note
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Plus className="w-4 h-4" />
                Add Evidence
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <FileText className="w-4 h-4" />
                Generate Report
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
