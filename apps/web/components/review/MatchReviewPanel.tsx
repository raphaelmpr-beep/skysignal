'use client'

/**
 * MatchReviewPanel
 *
 * Shows a PENDING incident side-by-side with its top match candidate.
 * Analyst actions:
 *   "Same Event"     — links evidence at CORROBORATION role, recomputes confidence
 *   "Different Event"— dismisses this candidate, moves to next
 *   "Skip"           — defers the whole incident to later
 *
 * Confidence score is shown before/after to make the effect tangible.
 */

import { useState, useEffect, useCallback } from 'react'
import { CheckCircle, XCircle, SkipForward, ChevronRight, AlertTriangle, ShieldCheck } from 'lucide-react'
import { API_URL } from '@/lib/api'

// ── Types ──────────────────────────────────────────────────────────────────

interface IncidentSummary {
  id: string
  title: string
  occurred_at: string | null
  location_name: string | null
  city: string | null
  region: string | null
  incident_type: string
  confidence_score: number
  confidence_tier: string
  summary: string | null
  review_status: string
  tags: string[]
}

interface MatchCandidate {
  incident_id: string
  title: string
  occurred_at: string | null
  location_name: string | null
  city: string | null
  region: string | null
  incident_type: string
  confidence_score: number
  confidence_tier: string
  match_score: number
  match_breakdown: Record<string, number>
}

interface MatchReviewPanelProps {
  /** The PENDING incident being reviewed */
  incident: IncidentSummary
  /** Called when analyst takes any action (so parent can refresh the queue) */
  onAction: (incidentId: string, action: 'linked' | 'skipped') => void
}

// ── Helpers ────────────────────────────────────────────────────────────────

function tierColor(tier: string): string {
  switch (tier) {
    case 'VERIFIED':   return 'text-emerald-400'
    case 'HIGH':       return 'text-blue-400'
    case 'MEDIUM':     return 'text-yellow-400'
    case 'LOW':        return 'text-orange-400'
    default:           return 'text-zinc-500'
  }
}

function tierBg(tier: string): string {
  switch (tier) {
    case 'VERIFIED':   return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
    case 'HIGH':       return 'bg-blue-500/10 border-blue-500/30 text-blue-400'
    case 'MEDIUM':     return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
    case 'LOW':        return 'bg-orange-500/10 border-orange-500/30 text-orange-400'
    default:           return 'bg-zinc-800 border-zinc-700 text-zinc-400'
  }
}

function matchScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-400'
  if (score >= 60) return 'text-yellow-400'
  return 'text-orange-400'
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

const MATCH_LABELS: Record<string, string> = {
  date_match:          'Date',
  location_match:      'Location',
  facility_match:      'Facility',
  incident_type_match: 'Incident Type',
  jurisdiction_match:  'Jurisdiction',
  named_entity_match:  'Named Entities',
}

const MATCH_MAX: Record<string, number> = {
  date_match: 25, location_match: 25, facility_match: 20,
  incident_type_match: 15, jurisdiction_match: 10, named_entity_match: 5,
}

// ── Sub-components ─────────────────────────────────────────────────────────

function IncidentCard({
  incident,
  label,
  badge,
}: {
  incident: IncidentSummary | MatchCandidate
  label: string
  badge?: React.ReactNode
}) {
  const occurred = 'occurred_at' in incident ? incident.occurred_at : null
  return (
    <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col gap-3 min-w-0">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">{label}</span>
        {badge}
      </div>

      <h3 className="text-sm font-semibold text-white leading-snug line-clamp-3">
        {incident.title}
      </h3>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-zinc-400">
        <span><span className="text-zinc-600">Date </span>{formatDate(occurred)}</span>
        <span><span className="text-zinc-600">Type </span>{incident.incident_type}</span>
        <span className="col-span-2">
          <span className="text-zinc-600">Location </span>
          {[incident.city, incident.region].filter(Boolean).join(', ') || incident.location_name || '—'}
        </span>
      </div>

      {'summary' in incident && incident.summary && (
        <p className="text-xs text-zinc-500 line-clamp-4 leading-relaxed border-t border-zinc-800 pt-3">
          {incident.summary}
        </p>
      )}

      <div className="flex items-center gap-2 mt-auto pt-2">
        <span className={`text-xs font-bold px-2 py-0.5 rounded border ${tierBg(incident.confidence_tier)}`}>
          {incident.confidence_tier}
        </span>
        <span className={`text-xs font-mono ${tierColor(incident.confidence_tier)}`}>
          {incident.confidence_score}
        </span>
      </div>
    </div>
  )
}

function MatchBreakdownBar({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = max > 0 ? (score / max) * 100 : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-zinc-500 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${pct === 100 ? 'bg-emerald-500' : pct > 0 ? 'bg-yellow-500' : 'bg-zinc-700'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`w-8 text-right font-mono ${score > 0 ? 'text-white' : 'text-zinc-600'}`}>
        {score}/{max}
      </span>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────

export function MatchReviewPanel({ incident, onAction }: MatchReviewPanelProps) {
  const [candidates, setCandidates] = useState<MatchCandidate[]>([])
  const [candidateIndex, setCandidateIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [linking, setLinking] = useState(false)
  const [result, setResult] = useState<{ score: number; tier: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch match candidates for this incident
  useEffect(() => {
    setLoading(true)
    setResult(null)
    setError(null)
    setCandidateIndex(0)

    fetch(`${API_URL}/api/evidence/match-candidates/${incident.id}?min_score=40&limit=10`)
      .then(r => r.json())
      .then(data => {
        setCandidates(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => {
        setError('Failed to load match candidates')
        setLoading(false)
      })
  }, [incident.id])

  const currentCandidate = candidates[candidateIndex] ?? null

  // Analyst confirms: Same Event
  const handleSameEvent = useCallback(async () => {
    if (!currentCandidate || linking) return
    setLinking(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/evidence/link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: currentCandidate.incident_id,
          role: 'CORROBORATION',
          title: incident.title,
          url: null,
          excerpt: incident.summary?.slice(0, 500) ?? null,
          published_at: incident.occurred_at,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Link failed')
      setResult({
        score: data.new_confidence_score,
        tier: data.new_confidence_tier,
      })
      // Brief pause so analyst sees the result, then signal parent
      setTimeout(() => onAction(incident.id, 'linked'), 1800)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLinking(false)
    }
  }, [currentCandidate, incident, linking, onAction])

  // Analyst rejects: Different Event — move to next candidate
  const handleDifferentEvent = useCallback(() => {
    if (candidateIndex < candidates.length - 1) {
      setCandidateIndex(i => i + 1)
    } else {
      // No more candidates — skip the incident
      onAction(incident.id, 'skipped')
    }
  }, [candidateIndex, candidates.length, incident.id, onAction])

  const handleSkip = useCallback(() => {
    onAction(incident.id, 'skipped')
  }, [incident.id, onAction])

  // ── Render states ──

  if (loading) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-6 animate-pulse">
        <div className="h-4 bg-zinc-800 rounded w-1/3 mb-4" />
        <div className="flex gap-4">
          <div className="flex-1 h-48 bg-zinc-900 rounded-xl" />
          <div className="w-8 flex items-center justify-center text-zinc-700">vs</div>
          <div className="flex-1 h-48 bg-zinc-900 rounded-xl" />
        </div>
      </div>
    )
  }

  if (result) {
    return (
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 flex items-center gap-4">
        <ShieldCheck className="w-8 h-8 text-emerald-400 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-white">Evidence linked successfully</p>
          <p className="text-xs text-zinc-400 mt-0.5">
            Incident confidence updated to{' '}
            <span className={`font-bold ${tierColor(result.tier)}`}>
              {result.score} ({result.tier})
            </span>
          </p>
        </div>
      </div>
    )
  }

  if (!currentCandidate) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-6 flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-zinc-600 shrink-0" />
        <p className="text-sm text-zinc-500">
          No match candidates found for this incident. It may be a unique event.
        </p>
        <button
          onClick={handleSkip}
          className="ml-auto text-xs text-zinc-500 hover:text-white transition-colors"
        >
          Skip
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">
            Match Review
          </span>
          {candidates.length > 1 && (
            <span className="text-xs text-zinc-600">
              {candidateIndex + 1} of {candidates.length} candidates
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Match score</span>
          <span className={`text-sm font-bold font-mono ${matchScoreColor(currentCandidate.match_score)}`}>
            {currentCandidate.match_score}/100
          </span>
        </div>
      </div>

      {/* Side-by-side cards */}
      <div className="flex gap-4 p-5">
        {/* Left: PENDING (new signal) */}
        <IncidentCard
          incident={incident}
          label="New Signal (Pending)"
          badge={
            <span className="text-xs px-2 py-0.5 rounded border bg-orange-500/10 border-orange-500/30 text-orange-400">
              PENDING
            </span>
          }
        />

        {/* Arrow */}
        <div className="flex items-center justify-center shrink-0">
          <ChevronRight className="w-5 h-5 text-zinc-600" />
        </div>

        {/* Right: APPROVED (existing incident) */}
        <IncidentCard
          incident={currentCandidate}
          label="Existing Incident (Approved)"
          badge={
            <span className="text-xs px-2 py-0.5 rounded border bg-blue-500/10 border-blue-500/30 text-blue-400">
              APPROVED
            </span>
          }
        />
      </div>

      {/* Match breakdown */}
      <div className="px-5 pb-4 border-t border-zinc-800 pt-4">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">
          Match Breakdown
        </p>
        <div className="flex flex-col gap-2">
          {Object.entries(currentCandidate.match_breakdown).map(([key, score]) => (
            <MatchBreakdownBar
              key={key}
              label={MATCH_LABELS[key] ?? key}
              score={score}
              max={MATCH_MAX[key] ?? 25}
            />
          ))}
        </div>
      </div>

      {/* Scoring note */}
      <div className="px-5 pb-3">
        <p className="text-xs text-zinc-600 leading-relaxed">
          Linking as <span className="text-zinc-400 font-mono">CORROBORATION</span> will upgrade
          any existing DISCOVERY evidence to CORROBORATION and recompute the incident&apos;s
          confidence score using the corroboration formula.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mb-3 px-3 py-2 rounded bg-red-500/10 border border-red-500/30 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 px-5 pb-5">
        <button
          onClick={handleSameEvent}
          disabled={linking}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
        >
          <CheckCircle className="w-4 h-4" />
          {linking ? 'Linking…' : 'Same Event'}
        </button>

        <button
          onClick={handleDifferentEvent}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-semibold transition-colors"
        >
          <XCircle className="w-4 h-4" />
          {candidateIndex < candidates.length - 1 ? 'Different Event' : 'No Match'}
        </button>

        <button
          onClick={handleSkip}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-zinc-500 hover:text-white text-sm transition-colors ml-auto"
        >
          <SkipForward className="w-4 h-4" />
          Skip
        </button>
      </div>
    </div>
  )
}
