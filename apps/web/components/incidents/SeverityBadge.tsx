import { cn, getSeverityBg } from '@/lib/utils'
import type { Severity } from '@/lib/types'

interface SeverityBadgeProps {
  severity: Severity
  className?: string
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide',
        getSeverityBg(severity),
        className
      )}
    >
      {severity}
    </span>
  )
}
