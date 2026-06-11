import { cn, getConfidenceBg, formatConfidence } from '@/lib/utils'
import type { ConfidenceTier } from '@/lib/types'

interface ConfidenceBadgeProps {
  tier: ConfidenceTier
  score?: number
  className?: string
}

const tierLabel: Record<ConfidenceTier, string> = {
  VERY_HIGH: 'Very High',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
  VERY_LOW: 'Very Low',
}

export function ConfidenceBadge({ tier, score, className }: ConfidenceBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-medium',
        getConfidenceBg(tier),
        className
      )}
    >
      {score !== undefined && (
        <span className="font-semibold">{formatConfidence(score)}</span>
      )}
      <span>{tierLabel[tier] || tier}</span>
    </span>
  )
}
