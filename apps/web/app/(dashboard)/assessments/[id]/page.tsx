'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft, MapPin, Calendar, Bookmark, FileText, Loader2, ExternalLink, Shield,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ThreatScoreGauge } from '@/components/assessments/ThreatScoreGauge'
import { FactorBreakdown } from '@/components/assessments/FactorBreakdown'
import { IncidentTable } from '@/components/incidents/IncidentTable'
import { useAssessment } from '@/hooks/useAssessment'
import { saveWatchZone, generateReport } from '@/lib/api'
import { formatDate, formatMiles, formatDays } from '@/lib/utils'
import { useState } from 'react'
import dynamic from 'next/dynamic'

const IncidentMap = dynamic(
  () => import('@/components/map/IncidentMap').then((m) => m.IncidentMap),
  { ssr: false }
)

export default function AssessmentDetailPage() {
  const params = useParams()
  const id = params.id as string
  const { assessment, isLoading, error } = useAssessment(id)
  const [savingZone, setSavingZone] = useState(false)
  const [zoneSaved, setZoneSaved] = useState(false)
  const [generatingReport, setGeneratingReport] = useState(false)

  async function handleSaveWatchZone() {
    if (!assessment) return
    setSavingZone(true)
    try {
      await saveWatchZone(assessment.id)
      setZoneSaved(true)
    } catch (err) {
      console.error(err)
    } finally {
      setSavingZone(false)
    }
  }

  async function handleGenerateReport() {
    if (!assessment) return
    setGeneratingReport(true)
    try {
      const result = await generateReport(assessment.id)
      if (result.html_url) {
        window.open(result.html_url, '_blank')
      }
    } catch (err) {
      console.error(err)
    } finally {
      setGeneratingReport(false)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
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

  if (error || !assessment) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">{error || 'Assessment not found'}</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/assessments/new">Run new assessment</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link href="/dashboard">
          <ArrowLeft className="w-4 h-4" />
          Dashboard
        </Link>
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-teal" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Threat Assessment
            </span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">{assessment.facility_name}</h1>
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
            {assessment.address && (
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" />
                {assessment.address}
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              Assessed {formatDate(assessment.created_at)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveWatchZone}
            disabled={savingZone || zoneSaved || !!assessment.watch_zone_id}
          >
            {savingZone ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Bookmark className="w-4 h-4" />
            )}
            {zoneSaved || assessment.watch_zone_id ? 'Watch Zone Saved' : 'Save as Watch Zone'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateReport}
            disabled={generatingReport}
          >
            {generatingReport ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            Generate Report
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/map?lat=${assessment.latitude}&lng=${assessment.longitude}&radius=${assessment.radius_miles}`}>
              <MapPin className="w-4 h-4" />
              View on Map
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main */}
        <div className="xl:col-span-2 space-y-6">
          {/* Score + summary */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-8">
                <ThreatScoreGauge
                  score={assessment.threat_score}
                  tier={assessment.threat_tier}
                  size="lg"
                />
                <div className="flex-1 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                      <p className="text-xs text-muted-foreground mb-1">Incidents Found</p>
                      <p className="text-2xl font-bold text-foreground tabular-nums">{assessment.incident_count}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                      <p className="text-xs text-muted-foreground mb-1">Search Radius</p>
                      <p className="text-2xl font-bold text-foreground tabular-nums">{formatMiles(assessment.radius_miles)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                      <p className="text-xs text-muted-foreground mb-1">Time Window</p>
                      <p className="text-xl font-bold text-foreground tabular-nums">{formatDays(assessment.time_window_days)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                      <p className="text-xs text-muted-foreground mb-1">Coordinates</p>
                      <p className="text-sm font-mono text-foreground">
                        {assessment.latitude.toFixed(4)}, {assessment.longitude.toFixed(4)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Factor breakdown */}
          {assessment.factors && assessment.factors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Factor Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <FactorBreakdown factors={assessment.factors} />
              </CardContent>
            </Card>
          )}

          {/* Nearby incidents */}
          {assessment.nearby_incidents && assessment.nearby_incidents.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Nearby Incidents ({assessment.nearby_incidents.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <IncidentTable incidents={assessment.nearby_incidents} compact />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Map */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="h-64">
                <IncidentMap
                  incidents={assessment.nearby_incidents || []}
                  centerLat={assessment.latitude}
                  centerLng={assessment.longitude}
                  radiusMiles={assessment.radius_miles}
                  zoom={10}
                  height="256px"
                />
              </div>
              <div className="p-3 border-t border-white/[0.08]">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <Link href={`/map?lat=${assessment.latitude}&lng=${assessment.longitude}&radius=${assessment.radius_miles}`}>
                    <ExternalLink className="w-4 h-4" />
                    Open in Map
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Score interpretation */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Score Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  { range: '0–20', tier: 'MINIMAL', color: '#8A9BB5' },
                  { range: '21–40', tier: 'LOW', color: '#00B4C8' },
                  { range: '41–60', tier: 'MODERATE', color: '#F0A500' },
                  { range: '61–80', tier: 'ELEVATED', color: '#E05C1A' },
                  { range: '81–100', tier: 'HIGH', color: '#EF4444' },
                ].map(({ range, tier, color }) => (
                  <div
                    key={tier}
                    className={`flex items-center justify-between p-2 rounded text-xs ${assessment.threat_tier === tier ? 'ring-1' : ''}`}
                    style={{
                      background: assessment.threat_tier === tier ? `${color}15` : 'transparent',
                      ringColor: color,
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                      <span style={{ color: assessment.threat_tier === tier ? color : '#8A9BB5' }} className="font-medium">
                        {tier}
                      </span>
                    </div>
                    <span className="text-muted-foreground font-mono">{range}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
