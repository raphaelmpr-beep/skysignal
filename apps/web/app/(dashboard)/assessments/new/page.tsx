'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  MapPin, Search, Loader2, ArrowRight, Info, CrosshairIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { createAssessment, geocodeAddress } from '@/lib/api'

const RADIUS_OPTIONS = [
  { label: '1 mile', value: '1' },
  { label: '5 miles', value: '5' },
  { label: '10 miles', value: '10' },
  { label: '25 miles', value: '25' },
]

const TIME_OPTIONS = [
  { label: '30 days', value: '30' },
  { label: '90 days', value: '90' },
  { label: '180 days', value: '180' },
  { label: '1 year', value: '365' },
  { label: '3 years', value: '1095' },
]

export default function AssessNewPage() {
  const router = useRouter()
  const [facilityName, setFacilityName] = useState('')
  const [address, setAddress] = useState('')
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')
  const [radius, setRadius] = useState('10')
  const [customRadius, setCustomRadius] = useState('')
  const [timeWindow, setTimeWindow] = useState('365')
  const [geocoding, setGeocoding] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resolvedAddress, setResolvedAddress] = useState('')

  async function handleGeocode() {
    if (!address.trim()) return
    setGeocoding(true)
    try {
      const result = await geocodeAddress(address)
      if (!result) {
        setError('Address not found. Try a more specific address.')
        return
      }
      setLat(result.lat.toString())
      setLon(result.lon.toString())
      setResolvedAddress(result.display_name)
      setError(null)
    } catch {
      setError('Geocoding failed. Please enter coordinates manually.')
    } finally {
      setGeocoding(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const latNum = parseFloat(lat)
    const lonNum = parseFloat(lon)
    const radiusNum = radius === 'custom' ? parseFloat(customRadius) : parseFloat(radius)

    if (!facilityName.trim()) {
      setError('Facility name is required')
      return
    }
    if (isNaN(latNum) || isNaN(lonNum)) {
      setError('Valid coordinates are required. Use the geocode button or enter manually.')
      return
    }
    if (isNaN(radiusNum) || radiusNum <= 0) {
      setError('A valid radius is required')
      return
    }

    setLoading(true)
    try {
      const assessment = await createAssessment({
        facility_name: facilityName,
        address: resolvedAddress || address,
        latitude: latNum,
        longitude: lonNum,
        radius_miles: radiusNum,
        time_window_days: parseInt(timeWindow),
      })
      router.push(`/assessments/${assessment.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assessment failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <CrosshairIcon className="w-5 h-5 text-teal" />
          <h1 className="text-xl font-bold text-foreground">Assess Location</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Run a Threat Reality Score assessment for any facility. Analyzes drone incidents within the specified radius and time window.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Facility info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Facility Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="facilityName">Facility Name <span className="text-red-400">*</span></Label>
              <Input
                id="facilityName"
                placeholder="e.g. Hoover Dam, LAX Airport, Tesla Gigafactory"
                value={facilityName}
                onChange={(e) => setFacilityName(e.target.value)}
                required
              />
            </div>

            {/* Address with geocode */}
            <div className="space-y-1.5">
              <Label htmlFor="address">Address</Label>
              <div className="flex gap-2">
                <Input
                  id="address"
                  placeholder="Enter address to geocode coordinates"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleGeocode}
                  disabled={geocoding || !address.trim()}
                >
                  {geocoding ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  Geocode
                </Button>
              </div>
              {resolvedAddress && (
                <p className="text-xs text-teal flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {resolvedAddress}
                </p>
              )}
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <div className="flex-1 h-px bg-white/[0.08]" />
              <span>or enter coordinates directly</span>
              <div className="flex-1 h-px bg-white/[0.08]" />
            </div>

            {/* Coordinates */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="lat">Latitude</Label>
                <Input
                  id="lat"
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 36.0160"
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="lon">Longitude</Label>
                <Input
                  id="lon"
                  type="number"
                  step="0.0001"
                  placeholder="e.g. -114.7376"
                  value={lon}
                  onChange={(e) => setLon(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Assessment params */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Assessment Parameters</CardTitle>
            <CardDescription>
              Define the geographic radius and time window for incident analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* Radius */}
              <div className="space-y-1.5">
                <Label>Search Radius</Label>
                <Select value={radius} onValueChange={setRadius}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RADIUS_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                    <SelectItem value="custom">Custom...</SelectItem>
                  </SelectContent>
                </Select>
                {radius === 'custom' && (
                  <Input
                    type="number"
                    placeholder="Miles"
                    value={customRadius}
                    onChange={(e) => setCustomRadius(e.target.value)}
                    className="mt-2"
                  />
                )}
              </div>

              {/* Time window */}
              <div className="space-y-1.5">
                <Label>Time Window</Label>
                <Select value={timeWindow} onValueChange={setTimeWindow}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIME_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Info box */}
            <div className="flex gap-2 p-3 rounded-lg bg-teal/[0.06] border border-teal/20 text-xs text-teal/90">
              <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>
                The Threat Reality Score (TRS) analyzes incident frequency, severity, confidence, 
                proximity, and source quality within the specified radius and time window using 7 weighted factors.
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Submit */}
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={loading || !facilityName}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Running assessment...
            </>
          ) : (
            <>
              Run Assessment
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </Button>
      </form>
    </div>
  )
}
