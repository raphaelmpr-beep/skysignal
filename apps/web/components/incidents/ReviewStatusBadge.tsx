import { cn, getStatusBg } from '@/lib/utils'
import type { ReviewStatus } from '@/lib/types'

interface ReviewStatusBadgeProps {
  status: ReviewStatus
  className?: string
}

const statusLabel: Record<ReviewStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  UNDER_REVIEW: 'Under Review',
}

export function ReviewStatusBadge({ status, className }: ReviewStatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium',
        getStatusBg(status),
        className
      )}
    >
      {statusLabel[status] || status}
    </span>
  )
}
