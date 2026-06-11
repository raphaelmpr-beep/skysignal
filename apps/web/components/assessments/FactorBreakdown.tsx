import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { AssessmentFactor } from '@/lib/types'
import { cn } from '@/lib/utils'

interface FactorBreakdownProps {
  factors: AssessmentFactor[]
}

function ScoreBar({ value, max = 10 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100)
  const color =
    pct >= 80 ? '#EF4444' :
    pct >= 60 ? '#E05C1A' :
    pct >= 40 ? '#F0A500' :
    pct >= 20 ? '#00B4C8' :
    '#2E9E5B'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums w-6 text-right" style={{ color }}>
        {value.toFixed(1)}
      </span>
    </div>
  )
}

export function FactorBreakdown({ factors }: FactorBreakdownProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Factor</TableHead>
          <TableHead className="w-48">Score</TableHead>
          <TableHead className="w-16 text-right">Weight</TableHead>
          <TableHead className="w-28 text-right">Contribution</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {factors.map((factor, i) => (
          <TableRow key={i}>
            <TableCell>
              <div>
                <p className="text-sm font-medium text-foreground">{factor.factor_name}</p>
                {factor.description && (
                  <p className="text-xs text-muted-foreground mt-0.5">{factor.description}</p>
                )}
              </div>
            </TableCell>
            <TableCell>
              <ScoreBar value={factor.score} />
            </TableCell>
            <TableCell className="text-right">
              <span className="text-xs text-muted-foreground">{(factor.weight * 100).toFixed(0)}%</span>
            </TableCell>
            <TableCell className="text-right">
              <span
                className={cn(
                  'text-sm font-semibold tabular-nums',
                  factor.weighted_contribution > 7
                    ? 'text-red-400'
                    : factor.weighted_contribution > 5
                    ? 'text-orange-400'
                    : factor.weighted_contribution > 3
                    ? 'text-amber-400'
                    : 'text-teal'
                )}
              >
                {factor.weighted_contribution.toFixed(2)}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
