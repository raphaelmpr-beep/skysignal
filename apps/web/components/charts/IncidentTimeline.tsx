'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { formatDate } from '@/lib/utils'
import type { TimelineDataPoint } from '@/lib/types'

interface IncidentTimelineProps {
  data: TimelineDataPoint[]
  stacked?: boolean
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a2436] border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <p className="font-medium text-foreground mb-2">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground capitalize">{p.name}:</span>
          <span className="font-semibold text-foreground">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

export function IncidentTimeline({ data, stacked = false }: IncidentTimelineProps) {
  const formattedData = data.map((d) => ({
    ...d,
    date: formatDate(d.date, 'MMM d'),
  }))

  if (stacked) {
    return (
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="critGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#E05C1A" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#E05C1A" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="medGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F0A500" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#F0A500" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="lowGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00B4C8" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00B4C8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '11px', color: '#8A9BB5', paddingTop: '8px' }}
          />
          <Area type="monotone" dataKey="critical" stackId="1" stroke="#EF4444" fill="url(#critGrad)" strokeWidth={1.5} />
          <Area type="monotone" dataKey="high" stackId="1" stroke="#E05C1A" fill="url(#highGrad)" strokeWidth={1.5} />
          <Area type="monotone" dataKey="medium" stackId="1" stroke="#F0A500" fill="url(#medGrad)" strokeWidth={1.5} />
          <Area type="monotone" dataKey="low" stackId="1" stroke="#00B4C8" fill="url(#lowGrad)" strokeWidth={1.5} />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00B4C8" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#00B4C8" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="date" tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#00B4C8"
          fill="url(#totalGrad)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
