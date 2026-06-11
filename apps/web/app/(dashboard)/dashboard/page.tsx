'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { AlertTriangle, Clock, Zap, Building2, MapPin, ArrowRight, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KPICard } from '@/components/dashboard/KPICard'
import { IncidentTable } from '@/components/incidents/IncidentTable'
import { SectorDistribution } from '@/components/charts/SectorDistribution'
import { Skeleton } from '@/components/ui/skeleton'
import {
  fetchAnalyticsKPI,
  fetchIncidents,
  fetchAssessments,
  fetchSectorDistribution,
} from '@/lib/api'
import type { KPIData, Incident, Assessment, SectorDistributionItem } from '@/lib/types'
import { formatDate, getTierColor, getThreatTierFromScore } from '@/lib/utils'

export default function DashboardPage() {
  const [kpi, setKpi] = useState<KPIData | null>(null)
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [sectorData, setSectorData] = useState<SectorDistributionItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [kpiData, incData, assessData, secData] = await Promise.allSettled([
          fetchAnalyticsKPI(),
          fetchIncidents({ limit: 5, review_status: ['APPROVED'], per_page: 5 }),
          fetchAssessments(),
          fetchSectorDistribution(),
        ])

        if (kpiData.status === 'fulfilled') setKpi(kpiData.value)
        if (incData.status === 'fulfilled') setIncidents(incData.value.items || [])
        if (assessData.status === 'fulfilled') setAssessments((assessData.value as Assessment[]).slice(0, 3))
        if (secData.status === 'fulfilled') setSectorData(secData.value)
      } catch {
        // Silent fail — show skeleton state
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Threat intelligence overview</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" asChild>
            <Link href="/map">
              <MapPin className="w-4 h-4" />
              View Map
            </Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/assessments/new">
              <Plus className="w-4 h-4" />
              Assess Location
            </Link>
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard
          title="Total Incidents"
          value={kpi?.total_incidents ?? '—'}
          trend={kpi?.total_incidents_change}
          icon={AlertTriangle}
          iconColor="text-orange-alert"
          description="all time"
          loading={loading && !kpi}
        />
        <KPICard
          title="Pending Review"
          value={kpi?.pending_review ?? '—'}
          trend={kpi?.pending_review_change}
          icon={Clock}
          iconColor="text-amber-pending"
          description="awaiting action"
          loading={loading && !kpi}
        />
        <KPICard
          title="Avg Confidence"
          value={kpi ? `${Math.round(kpi.avg_confidence * 100)}%` : '—'}
          trend={kpi?.avg_confidence_change}
          icon={Zap}
          iconColor="text-teal"
          description="signal quality"
          loading={loading && !kpi}
        />
        <KPICard
          title="High Signal Facilities"
          value={kpi?.high_signal_facilities ?? '—'}
          trend={kpi?.high_signal_facilities_change}
          icon={Building2}
          iconColor="text-green-confirmed"
          description="assessed locations"
          loading={loading && !kpi}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent incidents */}
        <div className="xl:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">Recent Incidents</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/incidents" className="text-xs text-muted-foreground hover:text-foreground">
                  View all
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : (
                <IncidentTable incidents={incidents} compact />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Recent assessments */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">Recent Assessments</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/assessments/new" className="text-xs text-muted-foreground hover:text-foreground">
                  New
                  <Plus className="w-3.5 h-3.5" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              {loading ? (
                <>
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </>
              ) : assessments.length === 0 ? (
                <div className="text-center py-6">
                  <p className="text-sm text-muted-foreground">No assessments yet</p>
                  <Button size="sm" variant="outline" className="mt-3" asChild>
                    <Link href="/assessments/new">Run first assessment</Link>
                  </Button>
                </div>
              ) : (
                assessments.map((a) => {
                  const tier = getThreatTierFromScore(a.threat_score)
                  const color = getTierColor(tier)
                  return (
                    <Link
                      key={a.id}
                      href={`/assessments/${a.id}`}
                      className="block p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:border-white/10 hover:bg-white/[0.05] transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{a.facility_name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{formatDate(a.created_at)}</p>
                        </div>
                        <div
                          className="text-xl font-bold tabular-nums shrink-0"
                          style={{ color }}
                        >
                          {Math.round(a.threat_score)}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>{a.incident_count} incidents</span>
                        <span>{a.radius_miles}mi radius</span>
                      </div>
                    </Link>
                  )
                })
              )}
            </CardContent>
          </Card>

          {/* Sector chart */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">By Sector</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <Skeleton className="h-40 w-full" />
              ) : sectorData.length === 0 ? (
                <div className="text-center py-6 text-sm text-muted-foreground">No data</div>
              ) : (
                <SectorDistribution data={sectorData} height={160} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* CTA */}
      <Card className="border-teal/20 bg-teal/[0.05]">
        <CardContent className="p-5 flex items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold text-foreground">Assess a New Location</h3>
            <p className="text-sm text-muted-foreground mt-0.5">
              Run a threat reality assessment for any facility using coordinates or address.
            </p>
          </div>
          <Button size="lg" asChild className="shrink-0">
            <Link href="/assessments/new">
              <MapPin className="w-4 h-4" />
              Start Assessment
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
