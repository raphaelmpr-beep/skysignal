'use client'

import dynamic from 'next/dynamic'
import { useEffect, useRef } from 'react'
import type { SankeyData } from '@/lib/types'

interface SankeyChartProps {
  data: SankeyData
  height?: number
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type G2Chart = any

function SankeyChartInner({ data, height = 350 }: SankeyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<G2Chart>(null)

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return

    containerRef.current.innerHTML = ''

    async function init() {
      const G2 = await import('@antv/g2')

      const chart = new G2.Chart({
        container: containerRef.current!,
        height,
        style: { background: 'transparent' },
      })

      chart.options({
        type: 'sankey',
        data: {
          value: {
            nodes: data.nodes,
            edges: data.links.map((l) => ({
              source: l.source,
              target: l.target,
              value: l.value,
            })),
          },
        },
        layout: {
          nodeAlign: 'justify',
          nodePadding: 0.03,
        },
        scale: {
          color: {
            range: ['#00B4C8', '#2E9E5B', '#F0A500', '#E05C1A', '#EF4444', '#8B5CF6'],
          },
        },
        style: {
          labelFontSize: 11,
          labelFill: '#8A9BB5',
          nodeFillOpacity: 0.85,
          linkFillOpacity: 0.2,
        },
      })

      await chart.render()
      chartRef.current = chart
    }

    init().catch(console.error)

    return () => {
      if (chartRef.current?.destroy) {
        chartRef.current.destroy()
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, height])

  return <div ref={containerRef} style={{ width: '100%', height }} />
}

export const SankeyChart = dynamic(
  () => Promise.resolve(SankeyChartInner),
  { ssr: false, loading: () => <div className="h-[350px] bg-white/[0.03] rounded-lg animate-pulse" /> }
)
