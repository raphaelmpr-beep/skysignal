'use client'

import { getTierColor, getTierBg, getThreatTierFromScore } from '@/lib/utils'
import type { ThreatTier } from '@/lib/types'
import { cn } from '@/lib/utils'

interface ThreatScoreGaugeProps {
  score: number
  tier?: ThreatTier
  size?: 'sm' | 'md' | 'lg'
}

const SIZE_CONFIG = {
  sm: { container: 'w-24 h-24', text: 'text-2xl', label: 'text-xs', stroke: 6, r: 38, view: 100 },
  md: { container: 'w-36 h-36', text: 'text-3xl', label: 'text-xs', stroke: 8, r: 54, view: 130 },
  lg: { container: 'w-48 h-48', text: 'text-5xl', label: 'text-sm', stroke: 10, r: 80, view: 190 },
}

export function ThreatScoreGauge({ score, tier, size = 'md' }: ThreatScoreGaugeProps) {
  const resolvedTier = tier || getThreatTierFromScore(score)
  const color = getTierColor(resolvedTier)
  const config = SIZE_CONFIG[size]
  
  const cx = config.view / 2
  const cy = config.view / 2
  const r = config.r
  const circumference = 2 * Math.PI * r
  // Arc covers 270 degrees (3/4 of circle) starting at 225 degrees
  const arcLength = circumference * 0.75
  const dashOffset = arcLength - (score / 100) * arcLength

  const tierLabels: Record<ThreatTier, string> = {
    MINIMAL: 'MINIMAL THREAT',
    LOW: 'LOW THREAT',
    MODERATE: 'MODERATE THREAT',
    ELEVATED: 'ELEVATED THREAT',
    HIGH: 'HIGH THREAT',
  }

  return (
    <div className={cn('relative flex flex-col items-center', config.container)}>
      <svg
        viewBox={`0 0 ${config.view} ${config.view}`}
        className="w-full h-full -rotate-[225deg]"
      >
        {/* Background track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={config.stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
        />
        {/* Score arc */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={config.stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn('font-bold tabular-nums', config.text)} style={{ color }}>
          {Math.round(score)}
        </span>
        <span className={cn('font-semibold mt-0.5', config.label)} style={{ color }}>
          {tierLabels[resolvedTier]}
        </span>
      </div>
    </div>
  )
}
