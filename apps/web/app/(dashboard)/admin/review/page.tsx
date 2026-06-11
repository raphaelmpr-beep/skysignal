'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { CheckCircle, XCircle, Eye, GitMerge, Clock, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { SeverityBadge } from '@/components/incidents/SeverityBadge'
import { ConfidenceBadge } from '@/components/incidents/ConfidenceBadge'
import { fetchIncidents, reviewIncident } from '@/lib/api'
import { formatDate, truncate } from '@/lib/utils'
import type { Incident } from '@/lib/types'

export default function ReviewQueuePage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const data = await fetchIncidents({ review_status: ['PENDING'], per_page: 100 })
      setIncidents(data.items)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleAction(
    id: string,
    action: 'approve' | 'reject' | 'request_review' | 'merge'
  ) {
    setActionLoading(id + action)
    try {
      await reviewIncident(id, action)
      setIncidents((prev) => prev.filter((i) => i.id !== id))
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Review Queue</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {incidents.length} incident{incidents.length !== 1 ? 's' : ''} pending review
          </p>
        </div>
        {incidents.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-pending/10 border border-amber-pending/20">
            <Clock className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-semibold text-amber-400">{incidents.length} pending</span>
          </div>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : incidents.length === 0 ? (
            <div className="text-center py-16">
              <CheckCircle className="w-10 h-10 text-green-confirmed/30 mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">Queue is clear</p>
              <p className="text-xs text-muted-foreground mt-1">All incidents have been reviewed</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Incident</TableHead>
                  <TableHead className="w-28">Date</TableHead>
                  <TableHead className="w-24">Severity</TableHead>
                  <TableHead className="w-32">Confidence</TableHead>
                  <TableHead className="w-52 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {incidents.map((incident) => {
                  const isLoading = actionLoading?.startsWith(incident.id)
                  return (
                    <TableRow key={incident.id}>
                      <TableCell>
                        <Link
                          href={`/incidents/${incident.id}`}
                          className="text-sm font-medium text-foreground hover:text-teal transition-colors block"
                        >
                          {truncate(incident.title, 60)}
                        </Link>
                        {incident.summary && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {truncate(incident.summary, 80)}
                          </p>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(incident.occurred_at)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <SeverityBadge severity={incident.severity} />
                      </TableCell>
                      <TableCell>
                        <ConfidenceBadge
                          tier={incident.confidence_tier}
                          score={incident.confidence_score}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => handleAction(incident.id, 'approve')}
                            disabled={!!isLoading}
                          >
                            {isLoading && actionLoading === incident.id + 'approve' ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <CheckCircle className="w-3.5 h-3.5" />
                            )}
                            Approve
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleAction(incident.id, 'reject')}
                            disabled={!!isLoading}
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            Reject
                          </Button>
                          <Button
                            variant="outline"
                            size="icon-sm"
                            onClick={() => handleAction(incident.id, 'request_review')}
                            disabled={!!isLoading}
                            title="Request more review"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            variant="outline"
                            size="icon-sm"
                            onClick={() => handleAction(incident.id, 'merge')}
                            disabled={!!isLoading}
                            title="Merge duplicate"
                          >
                            <GitMerge className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
