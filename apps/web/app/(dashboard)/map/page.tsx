'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layers, Filter, X, Thermometer } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { IncidentDrawer } from '@/components/map/IncidentDrawer'
import { fetchMapIncidents, fetchHeatmap, fetchWatchZones } from '@/lib/api'
import type { Incident, HeatmapPoint, WatchZone, MapFilters } from '@/lib/types'
import dynamic from 'next/dynamic'

const IncidentMap = dynamic(
  () => import('@/components/map/IncidentMap').then((m) => m.IncidentMap),
  { ssr: false, loading: () => <div className="flex-1 bg-navy animate-pulse" /> }
)

function MapPageInner() {
  const searchParams = useSearchParams()
  const centerLat = searchParams.get('lat') ? parseFloat(searchParams.get('lat')!) : undefined
  const centerLng = searchParams.get('lng') ? parseFloat(searchParams.get('lng')!) : undefined
  const radiusMiles = searchParams.get('radius') ? parseFloat(searchParams.get('radius')!) : undefined

  const [incidents, setIncidents] = useState<Incident[]>([])
  const [heatmapPoints, setHeatmapPoints] = useState<HeatmapPoint[]>([])
  const [watchZones, setWatchZones] = useState<WatchZone[]>([])
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [loading, setLoading] = useState(true)

  // Filters
  const [severity, setSeverity] = useState('')
  const [incidentType, setIncidentType] = useState('')
  const [sector, setSector] = useState('')
  const [reviewStatus, setReviewStatus] = useState('APPROVED')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const filters: MapFilters = {
    ...(severity && { severity }),
    ...(incidentType && { incident_type: incidentType }),
    ...(sector && { sector }),
    ...(reviewStatus && { review_status: reviewStatus }),
    ...(dateFrom && { date_from: dateFrom }),
    ...(dateTo && { date_to: dateTo }),
  }

  useEffect(() => {
    loadData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [severity, incidentType, sector, reviewStatus, dateFrom, dateTo])

  async function loadData() {
    setLoading(true)
    try {
      const [incData, wzData] = await Promise.allSettled([
        fetchMapIncidents(filters),
        fetchWatchZones(),
      ])
      if (incData.status === 'fulfilled') setIncidents(incData.value.incidents)
      if (wzData.status === 'fulfilled') setWatchZones(wzData.value)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  async function toggleHeatmap() {
    if (!showHeatmap && heatmapPoints.length === 0) {
      try {
        const pts = await fetchHeatmap(filters)
        setHeatmapPoints(pts)
      } catch {
        // silent
      }
    }
    setShowHeatmap(!showHeatmap)
  }

  return (
    <div className="fixed inset-0 left-56 top-14 flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.08] bg-navy/90 backdrop-blur-sm z-10 shrink-0">
        <span className="text-sm font-semibold text-foreground">
          {loading ? 'Loading...' : `${incidents.length} incidents`}
        </span>

        <div className="flex items-center gap-2 ml-auto">
          <Button
            variant={showHeatmap ? 'default' : 'outline'}
            size="sm"
            onClick={toggleHeatmap}
          >
            <Thermometer className="w-4 h-4" />
            Heatmap
          </Button>
          <Button
            variant={showFilters ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4" />
            Filters
          </Button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="px-4 py-3 border-b border-white/[0.08] bg-[#0d1829]/95 flex flex-wrap gap-3 shrink-0">
          <Select value={severity} onValueChange={setSeverity}>
            <SelectTrigger className="w-32 h-8 text-xs">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="CRITICAL">Critical</SelectItem>
              <SelectItem value="HIGH">High</SelectItem>
              <SelectItem value="MEDIUM">Medium</SelectItem>
              <SelectItem value="LOW">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select value={incidentType} onValueChange={setIncidentType}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="SIGHTING">Sighting</SelectItem>
              <SelectItem value="SURVEILLANCE">Surveillance</SelectItem>
              <SelectItem value="INCURSION">Incursion</SelectItem>
              <SelectItem value="NEAR_MISS">Near Miss</SelectItem>
              <SelectItem value="ATTACK">Attack</SelectItem>
            </SelectContent>
          </Select>
          <Select value={reviewStatus} onValueChange={setReviewStatus}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder="Review Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="APPROVED">Approved</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-36 h-8 text-xs"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-36 h-8 text-xs"
          />
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={() => {
              setSeverity('')
              setIncidentType('')
              setSector('')
              setDateFrom('')
              setDateTo('')
            }}
          >
            <X className="w-3.5 h-3.5" />
            Clear
          </Button>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[500] bg-[#0d1829]/90 backdrop-blur-sm border border-white/[0.08] rounded-lg p-3 text-xs">
        <p className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-teal" />
          Legend
        </p>
        <div className="space-y-1">
          {[
            { color: '#EF4444', label: 'Critical' },
            { color: '#E05C1A', label: 'High' },
            { color: '#F0A500', label: 'Medium' },
            { color: '#3B82F6', label: 'Low' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border border-white/20" style={{ background: color }} />
              <span className="text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Map + drawer */}
      <div className="flex-1 relative overflow-hidden">
        <IncidentMap
          incidents={incidents}
          heatmapPoints={heatmapPoints}
          watchZones={watchZones}
          centerLat={centerLat || 39.5}
          centerLng={centerLng || -98.35}
          radiusMiles={radiusMiles}
          showHeatmap={showHeatmap}
          onIncidentClick={setSelectedIncident}
          zoom={centerLat ? 11 : 5}
          height="100%"
        />
        <IncidentDrawer
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
        />
      </div>
    </div>
  )
}

export default function MapPage() {
  return (
    <Suspense fallback={<div className="flex-1 bg-navy animate-pulse" />}>
      <MapPageInner />
    </Suspense>
  )
}
