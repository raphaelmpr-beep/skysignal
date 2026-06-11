import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

interface KPICardProps {
  title: string
  value: string | number
  trend?: number
  icon: LucideIcon
  iconColor?: string
  description?: string
  loading?: boolean
}

export function KPICard({
  title,
  value,
  trend,
  icon: Icon,
  iconColor = 'text-teal',
  description,
  loading,
}: KPICardProps) {
  if (loading) {
    return (
      <div className="rounded-lg border border-white/[0.08] bg-[#162030] p-5">
        <div className="flex items-start justify-between mb-4">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-9 w-9 rounded-lg" />
        </div>
        <Skeleton className="h-8 w-20 mb-1" />
        <Skeleton className="h-3 w-24" />
      </div>
    )
  }

  const trendUp = trend !== undefined && trend > 0
  const trendDown = trend !== undefined && trend < 0
  const trendFlat = trend !== undefined && trend === 0

  return (
    <div className="rounded-lg border border-white/[0.08] bg-[#162030] p-5 group hover:border-white/15 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
        <div className={cn('flex items-center justify-center w-9 h-9 rounded-lg bg-white/5', iconColor.replace('text-', 'bg-').replace('teal', 'teal/10'))}>
          <Icon className={cn('w-4 h-4', iconColor)} />
        </div>
      </div>

      <div className="text-3xl font-bold text-foreground mb-1 tabular-nums">
        {value}
      </div>

      {(trend !== undefined || description) && (
        <div className="flex items-center gap-1.5">
          {trend !== undefined && (
            <span
              className={cn(
                'flex items-center gap-0.5 text-xs font-medium',
                trendUp && 'text-green-400',
                trendDown && 'text-red-400',
                trendFlat && 'text-muted-foreground'
              )}
            >
              {trendUp && <TrendingUp className="w-3 h-3" />}
              {trendDown && <TrendingDown className="w-3 h-3" />}
              {trendFlat && <Minus className="w-3 h-3" />}
              {Math.abs(trend)}%
            </span>
          )}
          {description && (
            <span className="text-xs text-muted-foreground">{description}</span>
          )}
        </div>
      )}
    </div>
  )
}
