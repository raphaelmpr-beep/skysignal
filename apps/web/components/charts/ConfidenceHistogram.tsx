'use client'

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

interface ConfidenceHistogramProps {
  data: Array<{ tier: string; count: number }>
  height?: number
}

const TIER_COLORS: Record<string, string> = {
  VERIFIED: '#2E9E5B',
  HIGH: '#00B4C8',
  MEDIUM: '#F0A500',
  LOW: '#E05C1A',
  UNVERIFIED: '#EF4444',
}

const TIER_LABELS: Record<string, string> = {
  VERIFIED: 'Verified',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
  UNVERIFIED: 'Unverified',
}

export function ConfidenceHistogram({ data, height = 200 }: ConfidenceHistogramProps) {
  const formattedData = data.map((d) => ({
    ...d,
    label: TIER_LABELS[d.tier] || d.tier,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }} barSize={28}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: '#8A9BB5', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          contentStyle={{
            background: '#1a2436',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#E8EDF5',
          }}
        />
        <Bar dataKey="count" radius={[3, 3, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={TIER_COLORS[d.tier] || '#8A9BB5'} opacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
