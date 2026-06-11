'use client'

import dynamic from 'next/dynamic'
import type { Incident, HeatmapPoint, WatchZone } from '@/lib/types'

export interface IncidentMapProps {
  incidents?: Incident[]
  heatmapPoints?: HeatmapPoint[]
  watchZones?: WatchZone[]
  centerLat?: number
  centerLng?: number
  radiusMiles?: number
  showHeatmap?: boolean
  onIncidentClick?: (incident: Incident) => void
  height?: string
  zoom?: number
}

const IncidentMapInner = dynamic(
  () => import('./IncidentMapInner').then((mod) => mod.IncidentMapInner),
  {
    ssr: false,
    loading: () => (
      <div
        className="flex items-center justify-center bg-navy border border-white/[0.08] rounded-lg"
        style={{ height: '100%', minHeight: '400px' }}
      >
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-teal/30 border-t-teal rounded-full animate-spin mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">Loading map...</p>
        </div>
      </div>
    ),
  }
)

export function IncidentMap(props: IncidentMapProps) {
  return <IncidentMapInner {...props} />
}
