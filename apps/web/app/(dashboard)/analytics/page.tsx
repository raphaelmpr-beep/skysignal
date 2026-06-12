'use client'

import { useState, useEffect } from 'react'
import { AlertTriangle, Clock, Zap, Building2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KPICard } from '@/components/dashboard/KPICard'
import { IncidentTimeline } from '@/components/charts/IncidentTimeline'
import { SectorDistribution } from '@/components/charts/SectorDistribution'
import { ConfidenceHistogram } from '@/components/charts/ConfidenceHistogram'
import { SourcePieChart } from '@/components/charts/SourcePieChart'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import dynamic from 'next/dynamic'
import {
  fetchAnalyticsKPI,
  fetchTimeline,
  fetchSectorDistribution,
  fetchConfidenceDistribution,
  fetchSourceDistribution,
  fetchSankeyData,
} from '@/lib/api'
import type {
  KPIData, TimelineDataPoint, SectorDistributionItem, SankeyData,
} from '@/lib/types'

const SankeyChart = dynamic(
  () => import('@/components/charts/SankeyChart').then((m) => m.SankeyChart),
  { ssr: false, loading: () => <Skeleton className="h-72 w-full" /> }
)

export default function AnalyticsPage() {
  const [kpi, setKpi] = useState<KPIData | null>(null)
  const [timeline, setTimeline] = useState<TimelineDataPoint[]>([])
  const [sector, setSector] = useState<SectorDistributionItem[]>([])
  const [confidence, setConfidence] = useState<{ tier: string; count: number }[]>([])
  const [sources, setSources] = useState<{ source: string; count: number }[]>([])
  const [sankey, setSankey] = useState<SankeyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timelineDays, setTimelineDays] = useState('90')

  useEffect(() => {
    async function load() {
      setLoading(true)
      const results = await Promise.allSettled([
        fetchAnalyticsKPI(),
        fetchTimeline(parseInt(timelineDays)),
        fetchSectorDistribution(),
        fetchConfidenceDistribution(),
        fetchSourceDistribution(),
        fetchSankeyData(),
      ])
      if (results[0].status === 'fulfilled') setKpi(results[0].value)
      if (results[1].status === 'fulfilled') setTimeline(results[1].value)
      if (results[2].status === 'fulfilled') setSector(results[2].value)
      if (results[3].status === 'fulfilled') setConfidence(results[3].value)
      if (results[4].status === 'fulfilled') setSources(results[4].value)
      if (results[5].status === 'fulfilled') setSankey(results[5].value)
      setLoading(false)
    }
    load()
  }, [timelineDays])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Signal intelligence overview</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard title="Total Incidents" value={kpi?.total_incidents ?? '—'} icon={AlertTriangle} iconColor="text-orange-alert" loading={loading && !kpi} />
        <KPICard title="Pending Review" value={kpi?.pending_review ?? '—'} icon={Clock} iconColor="text-amber-pending" loading={loading && !kpi} />
        <KPICard title="Avg Confidence" value={kpi ? `${Math.round(kpi.avg_confidence)}%` : '—'} icon={Zap} iconColor="text-teal" loading={loading && !kpi} />
        <KPICard title="High Signal Facilities" value={kpi?.high_signal_facilities ?? '—'} icon={Building2} iconColor="text-green-confirmed" loading={loading && !kpi} />
      </div>

      {/* Timeline */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Incident Timeline</CardTitle>
          <Select value={timelineDays} onValueChange={setTimelineDays}>
            <SelectTrigger className="w-32 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="180">Last 180 days</SelectItem>
              <SelectItem value="365">Last 365 days</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-56 w-full" />
          ) : (
            <IncidentTimeline data={timeline} />
          )}
        </CardContent>
      </Card>

      {/* Sankey */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Signal Flow — Source → Type → Sector → Outcome</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-72 w-full" />
          ) : sankey && sankey.nodes.length > 0 ? (
            <SankeyChart data={sankey} height={320} />
          ) : (
            <div className="h-72 flex items-center justify-center text-muted-foreground text-sm">
              No flow data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Bottom row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sector */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">By Sector</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-48 w-full" /> : <SectorDistribution data={sector} height={200} />}
          </CardContent>
        </Card>

        {/* Confidence */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Confidence Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-48 w-full" /> : <ConfidenceHistogram data={confidence} height={200} />}
          </CardContent>
        </Card>

        {/* Sources */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">By Source Type</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-48 w-full" /> : <SourcePieChart data={sources} height={200} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
