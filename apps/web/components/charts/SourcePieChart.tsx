'use client'

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface SourcePieChartProps {
  data: Array<{ source: string; count: number }>
  height?: number
}

const COLORS = ['#00B4C8', '#2E9E5B', '#F0A500', '#E05C1A', '#EF4444', '#8B5CF6', '#EC4899']

export function SourcePieChart({ data, height = 220 }: SourcePieChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={3}
          dataKey="count"
          nameKey="source"
        >
          {data.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} opacity={0.85} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: '#1a2436',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#E8EDF5',
          }}
          formatter={(value: number, name: string) => [
            `${value} (${((value / total) * 100).toFixed(1)}%)`,
            name,
          ]}
        />
        <Legend
          wrapperStyle={{ fontSize: '11px', color: '#8A9BB5' }}
          formatter={(value) => <span style={{ color: '#8A9BB5' }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
