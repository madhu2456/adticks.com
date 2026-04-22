import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full font-medium border',
  {
    variants: {
      variant: {
        default: [
          'bg-surface-3 text-text-2 border-white/[0.05]',
        ].join(' '),
        primary: [
          'bg-primary/10 text-primary border-primary/20',
        ].join(' '),
        secondary: [
          'bg-surface-2 text-text-2 border-white/[0.08]',
        ].join(' '),
        success: [
          'bg-success/10 text-success border-success/20',
        ].join(' '),
        warning: [
          'bg-warning/10 text-warning border-warning/20',
        ].join(' '),
        danger: [
          'bg-danger/10 text-danger border-danger/20',
        ].join(' '),
        violet: [
          'bg-violet/10 text-violet border-violet/20',
        ].join(' '),
        pink: [
          'bg-pink/10 text-pink border-pink/20',
        ].join(' '),
        informational: [
          'bg-sky-500/10 text-sky-300 border-sky-400/20',
        ].join(' '),
        transactional: [
          'bg-emerald-500/10 text-emerald-300 border-emerald-400/20',
        ].join(' '),
        commercial: [
          'bg-amber-500/10 text-amber-300 border-amber-400/20',
        ].join(' '),
        navigational: [
          'bg-indigo-500/10 text-indigo-300 border-indigo-400/20',
        ].join(' '),
        p1: [
          'bg-danger/10 text-danger border-danger/20',
        ].join(' '),
        p2: [
          'bg-warning/10 text-warning border-warning/20',
        ].join(' '),
        p3: [
          'bg-violet/10 text-violet border-violet/20',
        ].join(' '),
        outline: [
          'bg-transparent text-text-2 border-white/10',
        ].join(' '),
      },
      size: {
        sm: 'text-[10px] px-2 py-0.5',
        md: 'text-xs px-2.5 py-0.5',
        lg: 'text-sm px-3 py-1',
      },
      dot: {
        true: '',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      dot: false,
    },
  }
);

/* Dot color mapping */
const dotColorMap: Record<string, string> = {
  default: 'bg-text-3',
  primary: 'bg-primary',
  secondary: 'bg-text-3',
  success:  'bg-success',
  warning:  'bg-warning',
  danger:   'bg-danger',
  violet:   'bg-violet',
  pink:     'bg-pink',
  informational: 'bg-sky-400',
  transactional: 'bg-emerald-400',
  commercial: 'bg-amber-400',
  navigational: 'bg-indigo-400',
  p1: 'bg-danger',
  p2: 'bg-warning',
  p3: 'bg-violet',
  outline:  'bg-text-3',
};

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  /** Show an animated pulse dot before the label */
  dot?: boolean;
  /** Pulse animation on dot (live status) */
  pulse?: boolean;
}

function Badge({
  className,
  variant = 'default',
  size,
  dot = false,
  pulse = false,
  children,
  ...props
}: BadgeProps) {
  const dotColor = dotColorMap[variant ?? 'default'] ?? 'bg-text-3';

  return (
    <span className={cn(badgeVariants({ variant, size, dot }), className)} {...props}>
      {dot && (
        <span className="relative inline-flex shrink-0 h-1.5 w-1.5">
          {pulse && (
            <span
              className={cn(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-60',
                dotColor
              )}
            />
          )}
          <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', dotColor)} />
        </span>
      )}
      {children}
    </span>
  );
}

Badge.displayName = 'Badge';

export { Badge, badgeVariants };
