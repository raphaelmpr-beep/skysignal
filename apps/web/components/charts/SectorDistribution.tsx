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
import type { SectorDistributionItem } from '@/lib/types'

interface SectorDistributionProps {
  data: SectorDistributionItem[]
  height?: number
}

const COLORS = ['#00B4C8', '#2E9E5B', '#F0A500', '#E05C1A', '#EF4444', '#8B5CF6', '#EC4899', '#6366F1']

const CustomTooltip = ({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: SectorDistributionItem }>
}) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-[#1a2436] border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <p className="font-medium text-foreground">{d.sector}</p>
      <p className="text-muted-foreground mt-1">{d.count} incidents ({d.percentage.toFixed(1)}%)</p>
    </div>
  )
}

export function SectorDistribution({ data, height = 200 }: SectorDistributionProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }} barSize={20}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="sector"
          tick={{ fill: '#8A9BB5', fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={50}
        />
        <YAxis tick={{ fill: '#8A9BB5', fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="count" radius={[3, 3, 0, 0]}>
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} opacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
