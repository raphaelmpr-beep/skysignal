'use client'

import { useRouter } from 'next/navigation'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { SeverityBadge } from './SeverityBadge'
import { ConfidenceBadge } from './ConfidenceBadge'
import { ReviewStatusBadge } from './ReviewStatusBadge'
import { formatDate, truncate } from '@/lib/utils'
import type { Incident } from '@/lib/types'
import { MapPin, ExternalLink } from 'lucide-react'

interface IncidentTableProps {
  incidents: Incident[]
  loading?: boolean
  compact?: boolean
  onRowClick?: (incident: Incident) => void
}

const SKELETON_ROWS = 5

export function IncidentTable({ incidents, loading, compact, onRowClick }: IncidentTableProps) {
  const router = useRouter()

  const handleClick = (incident: Incident) => {
    if (onRowClick) {
      onRowClick(incident)
    } else {
      router.push(`/incidents/${incident.id}`)
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: SKELETON_ROWS }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (!incidents.length) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-sm">No incidents found</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-36">Date</TableHead>
          <TableHead>Title</TableHead>
          {!compact && <TableHead>Location</TableHead>}
          <TableHead className="w-28">Type</TableHead>
          <TableHead className="w-28">Severity</TableHead>
          {!compact && <TableHead className="w-32">Confidence</TableHead>}
          <TableHead className="w-28">Status</TableHead>
          {!compact && <TableHead className="w-8" />}
        </TableRow>
      </TableHeader>
      <TableBody>
        {incidents.map((incident) => (
          <TableRow
            key={incident.id}
            className="cursor-pointer group"
            onClick={() => handleClick(incident)}
          >
            <TableCell className="text-muted-foreground text-xs">
              {formatDate(incident.occurred_at, 'MMM d, yyyy')}
            </TableCell>
            <TableCell>
              <span className="text-sm font-medium text-foreground group-hover:text-teal transition-colors line-clamp-1">
                {incident.title}
              </span>
              {!compact && incident.summary && (
                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                  {truncate(incident.summary, 80)}
                </p>
              )}
              {!compact && incident.source_url && (
                <a
                  href={incident.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1 text-xs text-teal/70 hover:text-teal mt-0.5 transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                  Source
                </a>
              )}
            </TableCell>
            {!compact && (
              <TableCell>
                {incident.location_name ? (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="w-3 h-3 shrink-0" />
                    {truncate(incident.location_name, 30)}
                  </span>
                ) : incident.latitude ? (
                  <span className="text-xs text-muted-foreground font-mono">
                    {incident.latitude.toFixed(3)}, {incident.longitude?.toFixed(3)}
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground/50">—</span>
                )}
              </TableCell>
            )}
            <TableCell>
              <span className="text-xs text-muted-foreground">
                {incident.incident_type?.replace(/_/g, ' ')}
              </span>
            </TableCell>
            <TableCell>
              <SeverityBadge severity={incident.severity} />
            </TableCell>
            {!compact && (
              <TableCell>
                <ConfidenceBadge
                  tier={incident.confidence_tier}
                  score={incident.confidence_score}
                />
              </TableCell>
            )}
            <TableCell>
              <ReviewStatusBadge status={incident.review_status} />
            </TableCell>
            {!compact && (
              <TableCell>
                <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
