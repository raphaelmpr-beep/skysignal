import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-teal disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-teal text-navy hover:bg-teal-dark shadow',
        destructive:
          'bg-orange-alert text-white hover:bg-orange-alert/90 shadow-sm',
        outline:
          'border border-white/15 bg-transparent hover:bg-white/5 text-foreground',
        secondary:
          'bg-white/10 text-foreground hover:bg-white/15 shadow-sm',
        ghost:
          'hover:bg-white/5 text-foreground',
        link:
          'text-teal underline-offset-4 hover:underline',
        danger:
          'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30',
        success:
          'bg-green-confirmed/20 text-green-400 border border-green-confirmed/30 hover:bg-green-confirmed/30',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-7 rounded px-3 text-xs',
        lg: 'h-11 rounded-md px-8 text-base',
        icon: 'h-9 w-9',
        'icon-sm': 'h-7 w-7',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
