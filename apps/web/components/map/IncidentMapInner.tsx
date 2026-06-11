'use client'

import { useEffect, useRef, useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { getSeverityMarkerColor, formatDate } from '@/lib/utils'
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

// Miles to meters
const milesToMeters = (miles: number) => miles * 1609.34

function HeatmapLayer({ points }: { points: HeatmapPoint[] }) {
  const map = useMap()
  const heatLayerRef = useRef<unknown>(null)

  useEffect(() => {
    if (!points.length) return
    let layer: unknown = null

    async function addHeat() {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const L = await import('leaflet') as any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await import('leaflet.heat' as any)

      const heatData = points.map((p) => [p.lat, p.lng, p.intensity])
      // eslint-disable-next-line @typescript-eslint/no-unsafe-call
      layer = L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
        gradient: {
          0.0: '#00B4C8',
          0.5: '#F0A500',
          1.0: '#EF4444',
        },
      })
      // @ts-expect-error leaflet layer
      layer.addTo(map)
      heatLayerRef.current = layer
    }

    addHeat().catch(console.error)

    return () => {
      if (heatLayerRef.current) {
        // @ts-expect-error leaflet layer
        map.removeLayer(heatLayerRef.current)
      }
    }
  }, [points, map])

  return null
}

function RadiusCircle({ lat, lng, radiusMiles }: { lat: number; lng: number; radiusMiles: number }) {
  const map = useMap()
  const circleRef = useRef<unknown>(null)

  useEffect(() => {
    let cleanup: (() => void) | null = null
    import('leaflet').then((L) => {
      const circle = L.circle([lat, lng], {
        radius: milesToMeters(radiusMiles),
        color: '#00B4C8',
        weight: 2,
        opacity: 0.6,
        fillOpacity: 0.05,
        fillColor: '#00B4C8',
        dashArray: '6 4',
      }).addTo(map)
      circleRef.current = circle
      cleanup = () => { map.removeLayer(circle) }
    }).catch(console.error)
    return () => { cleanup?.() }
  }, [lat, lng, radiusMiles, map])

  return null
}

export function IncidentMapInner({
  incidents = [],
  heatmapPoints = [],
  watchZones = [],
  centerLat = 39.5,
  centerLng = -98.35,
  radiusMiles,
  showHeatmap = false,
  onIncidentClick,
  height = '100%',
  zoom = 5,
}: IncidentMapProps) {
  const center: [number, number] = useMemo(
    () => [centerLat, centerLng],
    [centerLat, centerLng]
  )

  return (
    <div style={{ height, width: '100%', minHeight: '400px' }} className="rounded-lg overflow-hidden">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%', background: '#0F1623' }}
        zoomControl
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          className="dark-tiles"
        />

        {/* Heatmap */}
        {showHeatmap && heatmapPoints.length > 0 && (
          <HeatmapLayer points={heatmapPoints} />
        )}

        {/* Radius ring around assessment */}
        {radiusMiles && centerLat && centerLng && (
          <RadiusCircle lat={centerLat} lng={centerLng} radiusMiles={radiusMiles} />
        )}

        {/* Watch zones */}
        {watchZones.map((zone) => (
          <CircleMarker
            key={zone.id}
            center={[zone.latitude, zone.longitude]}
            radius={8}
            pathOptions={{
              color: '#F0A500',
              weight: 2,
              opacity: 0.8,
              fillOpacity: 0.15,
              fillColor: '#F0A500',
            }}
          >
            <Popup>
              <div className="text-xs font-medium">{zone.name}</div>
              <div className="text-xs text-muted-foreground">{zone.radius_miles} mile radius</div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Incident markers */}
        {incidents
          .filter((i) => i.latitude && i.longitude)
          .map((incident) => {
            const color = getSeverityMarkerColor(incident.severity)
            return (
              <CircleMarker
                key={incident.id}
                center={[incident.latitude!, incident.longitude!]}
                radius={6}
                pathOptions={{
                  color,
                  weight: 1.5,
                  opacity: 0.9,
                  fillOpacity: 0.7,
                  fillColor: color,
                }}
                eventHandlers={{
                  click: () => onIncidentClick?.(incident),
                }}
              >
                <Popup>
                  <div style={{ minWidth: '200px' }}>
                    <p style={{ fontWeight: 600, fontSize: '12px', marginBottom: '4px', color: '#E8EDF5' }}>
                      {incident.title}
                    </p>
                    <p style={{ fontSize: '11px', color: '#8A9BB5', marginBottom: '4px' }}>
                      {formatDate(incident.occurred_at)}
                    </p>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: '10px',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          background: `${color}30`,
                          color,
                          border: `1px solid ${color}50`,
                        }}
                      >
                        {incident.severity}
                      </span>
                      <span
                        style={{
                          fontSize: '10px',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          background: 'rgba(255,255,255,0.1)',
                          color: '#8A9BB5',
                        }}
                      >
                        {incident.incident_type?.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
      </MapContainer>
    </div>
  )
}
