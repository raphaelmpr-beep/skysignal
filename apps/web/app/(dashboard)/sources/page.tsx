'use client'

import { useState, useEffect } from 'react'
import { Database, Globe, ExternalLink, ToggleLeft, ToggleRight, Star } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { fetchSources, updateSourceActive } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { Source } from '@/lib/types'

const SOURCE_TYPE_LABEL: Record<string, string> = {
  OFFICIAL: 'Official',
  NEWS: 'News',
  SOCIAL_MEDIA: 'Social Media',
  AVIATION: 'Aviation',
  GOV_DATASET: 'Gov Dataset',
  TIPLINE: 'Tip Line',
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSources()
      .then(setSources)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  async function toggleActive(source: Source) {
    try {
      const updated = await updateSourceActive(source.id, !source.is_active)
      setSources((prev) => prev.map((s) => (s.id === source.id ? updated : s)))
    } catch (err) {
      console.error(err)
    }
  }

  function credibilityColor(score: number) {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-teal'
    if (score >= 0.4) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Sources</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Intelligence source management</p>
        </div>
        <div className="text-sm text-muted-foreground">
          {sources.filter((s) => s.is_active).length} active / {sources.length} total
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : sources.length === 0 ? (
            <div className="text-center py-16">
              <Database className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No sources configured</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead className="w-28">Type</TableHead>
                  <TableHead className="w-28">Credibility</TableHead>
                  <TableHead className="w-20">Official</TableHead>
                  <TableHead className="w-32">Last Fetched</TableHead>
                  <TableHead className="w-16">Active</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source) => (
                  <TableRow key={source.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Globe className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-foreground">{source.name}</p>
                          {source.url && (
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-teal hover:underline flex items-center gap-1 mt-0.5"
                            >
                              {source.url.replace(/^https?:\/\//, '').slice(0, 40)}
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {SOURCE_TYPE_LABEL[source.source_type] || source.source_type}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Star className="w-3 h-3 text-amber-400" />
                        <span className={`text-sm font-semibold tabular-nums ${credibilityColor(source.credibility_score)}`}>
                          {(source.credibility_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {source.is_official ? (
                        <Badge variant="success">Official</Badge>
                      ) : (
                        <Badge variant="secondary">No</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {source.last_fetched ? formatDate(source.last_fetched) : '—'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => toggleActive(source)}
                        className="flex items-center justify-center"
                        title={source.is_active ? 'Disable source' : 'Enable source'}
                      >
                        {source.is_active ? (
                          <ToggleRight className="w-5 h-5 text-teal" />
                        ) : (
                          <ToggleLeft className="w-5 h-5 text-muted-foreground" />
                        )}
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
