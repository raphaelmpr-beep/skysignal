'use client'

import { X, MapPin, Calendar, ExternalLink, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SeverityBadge } from '@/components/incidents/SeverityBadge'
import { ConfidenceBadge } from '@/components/incidents/ConfidenceBadge'
import { ReviewStatusBadge } from '@/components/incidents/ReviewStatusBadge'
import { formatDate, formatRelativeTime } from '@/lib/utils'
import type { Incident } from '@/lib/types'
import Link from 'next/link'

interface IncidentDrawerProps {
  incident: Incident | null
  onClose: () => void
}

export function IncidentDrawer({ incident, onClose }: IncidentDrawerProps) {
  if (!incident) return null

  return (
    <div className="absolute right-0 top-0 h-full w-80 bg-[#0d1829] border-l border-white/[0.08] z-[1000] flex flex-col overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-white/[0.08]">
        <div className="flex-1 min-w-0 pr-2">
          <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wider">Incident</p>
          <h3 className="text-sm font-semibold text-foreground line-clamp-2">{incident.title}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Badges */}
      <div className="px-4 py-3 border-b border-white/[0.08] flex flex-wrap gap-1.5">
        <SeverityBadge severity={incident.severity} />
        <ConfidenceBadge tier={incident.confidence_tier} score={incident.confidence_score} />
        <ReviewStatusBadge status={incident.review_status} />
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Summary */}
        {incident.summary && (
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Summary</p>
            <p className="text-sm text-foreground/90 leading-relaxed">{incident.summary}</p>
          </div>
        )}

        {/* Metadata */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <Calendar className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
            <span className="text-muted-foreground">
              {formatDate(incident.occurred_at)} &middot; {formatRelativeTime(incident.occurred_at)}
            </span>
          </div>
          {(incident.location_name || incident.latitude) && (
            <div className="flex items-center gap-2 text-xs">
              <MapPin className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              <span className="text-muted-foreground">
                {incident.location_name ||
                  `${incident.latitude?.toFixed(4)}, ${incident.longitude?.toFixed(4)}`}
              </span>
            </div>
          )}
          {incident.sector && (
            <div className="flex items-center gap-2 text-xs">
              <AlertTriangle className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              <span className="text-muted-foreground">Sector: {incident.sector}</span>
            </div>
          )}
        </div>

        {/* Type */}
        <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <p className="text-muted-foreground mb-0.5">Type</p>
              <p className="text-foreground font-medium">{incident.incident_type?.replace(/_/g, ' ')}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Confidence</p>
              <p className="text-foreground font-medium tabular-nums">
                {Math.round(incident.confidence_score * 100)}%
              </p>
            </div>
          </div>
        </div>

        {/* Evidence count */}
        {incident.evidence && incident.evidence.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
              Evidence ({incident.evidence.length})
            </p>
            <div className="space-y-1.5">
              {incident.evidence.slice(0, 2).map((ev) => (
                <div key={ev.id} className="p-2 rounded bg-white/[0.03] border border-white/[0.05]">
                  <p className="text-xs text-foreground/80 line-clamp-2">{ev.excerpt || ev.source_name}</p>
                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-teal hover:underline flex items-center gap-1 mt-1"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      View source
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/[0.08]">
        <Button asChild className="w-full" size="sm">
          <Link href={`/incidents/${incident.id}`}>
            View Full Details
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  )
}
