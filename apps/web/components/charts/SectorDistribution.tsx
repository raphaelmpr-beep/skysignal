'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { SectorDistributionItem } from '@/lib/types'

interface SectorDistributionProps {
  /** Array for the currently selected tab — caller decides which dataset to pass */
  data: SectorDistributionItem[]
  /** Optional second dataset for the CISA tab */
  cisaData?: SectorDistributionItem[]
  height?: number
}

const COLORS = [
  '#00B4C8', '#2E9E5B', '#F0A500', '#E05C1A',
  '#EF4444', '#8B5CF6', '#EC4899', '#6366F1',
  '#14B8A6', '#F59E0B',
]

/** Abbreviate long sector names so they fit on the axis */
function abbreviate(sector: string): string {
  return sector
    .replace('TRANSPORTATION_SYSTEMS', 'TRANSPORT.')
    .replace('COMMERCIAL_FACILITIES', 'COMMERCIAL')
    .replace('GOVERNMENT_FACILITIES', 'GOV. FAC.')
    .replace('DEFENSE_INDUSTRIAL_BASE', 'DEF. IND.')
    .replace('EMERGENCY_SERVICES', 'EMERGENCY')
    .replace('CRITICAL_INFRA', 'CRIT. INFRA')
    .replace('BORDER_SECURITY', 'BORDER SEC.')
    .replace(/_/g, ' ')
}

const CustomTooltip = ({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: SectorDistributionItem }>
}) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-[#1a2436] border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <p className="font-medium text-foreground">{d.sector}</p>
      <p className="text-muted-foreground mt-1">
        {d.count.toLocaleString()} incidents ({d.percentage.toFixed(1)}%)
      </p>
    </div>
  )
}

/** Filter UNKNOWN, cap to top N, recompute percentages */
function prepare(raw: SectorDistributionItem[], topN = 10): SectorDistributionItem[] {
  const filtered = raw
    .filter((d) => d.sector !== 'UNKNOWN' && d.sector !== '')
    .slice(0, topN)
  const total = filtered.reduce((s, d) => s + d.count, 0) || 1
  return filtered.map((d) => ({
    ...d,
    percentage: (d.count / total) * 100,
  }))
}

export function SectorDistribution({
  data,
  cisaData,
  height = 220,
}: SectorDistributionProps) {
  const hasTabs = cisaData && cisaData.length > 0
  const [tab, setTab] = useState<'operational' | 'cisa'>('operational')

  const active = hasTabs && tab === 'cisa' ? cisaData! : data
  const prepared = prepare(active)

  if (!prepared.length) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        No sector data available
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {hasTabs && (
        <div className="flex gap-1 self-end">
          {(['operational', 'cisa'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                tab === t
                  ? 'bg-teal/20 text-teal border border-teal/30'
                  : 'text-muted-foreground hover:text-foreground border border-transparent'
              }`}
            >
              {t === 'operational' ? 'Operational' : 'CISA'}
            </button>
          ))}
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={prepared}
          margin={{ top: 5, right: 10, left: 5, bottom: 55 }}
          barSize={18}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.05)"
            vertical={false}
          />
          <XAxis
            dataKey="sector"
            tickFormatter={abbreviate}
            tick={{ fill: '#8A9BB5', fontSize: 9 }}
            tickLine={false}
            axisLine={false}
            interval={0}
            angle={-35}
            textAnchor="end"
            height={60}
          />
          <YAxis
            scale="log"
            domain={['auto', 'auto']}
            tickFormatter={(v: number) =>
              v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(Math.round(v))
            }
            tick={{ fill: '#8A9BB5', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {prepared.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                opacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-[9px] text-muted-foreground text-right pr-2 -mt-1">
        Log scale · Top {prepared.length} sectors · UNKNOWN excluded
      </p>
    </div>
  )
}
