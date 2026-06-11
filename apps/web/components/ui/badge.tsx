import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-teal/30 bg-teal/20 text-teal',
        secondary: 'border-white/10 bg-white/10 text-slate-400',
        destructive: 'border-red-500/30 bg-red-500/20 text-red-400',
        outline: 'border-white/15 text-foreground',
        success: 'border-green-confirmed/30 bg-green-confirmed/20 text-green-400',
        warning: 'border-amber-pending/30 bg-amber-pending/20 text-amber-400',
        orange: 'border-orange-alert/30 bg-orange-alert/20 text-orange-400',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
