import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

/* ─── Card root ─────────────────────────────────────────────────────── */
const cardVariants = cva(
  'relative rounded-xl overflow-hidden',
  {
    variants: {
      variant: {
        default: [
          'bg-surface-2 border border-white/[0.06]',
          'shadow-card',
          'transition-colors duration-200',
        ].join(' '),
        glass: [
          'glass border border-white/[0.06]',
          'shadow-card',
        ].join(' '),
        gradient: [
          'bg-surface-2',
          'before:absolute before:inset-0 before:rounded-xl before:p-px',
          'before:bg-gradient-brand before:opacity-30 before:-z-10',
          'shadow-card',
        ].join(' '),
        interactive: [
          'bg-surface-2 border border-white/[0.06]',
          'shadow-card cursor-pointer',
          'hover:border-white/10 hover:shadow-popup hover:-translate-y-px',
          'transition-all duration-200',
        ].join(' '),
        flat: [
          'bg-surface-1 border border-white/[0.04]',
        ].join(' '),
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant }), className)}
      {...props}
    />
  )
);
Card.displayName = 'Card';

/* ─── CardHeader ────────────────────────────────────────────────────── */
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col gap-1 p-5 pb-0', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

/* ─── CardTitle ─────────────────────────────────────────────────────── */
const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-sm font-semibold text-text-1 leading-snug tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

/* ─── CardDescription ───────────────────────────────────────────────── */
const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-xs text-text-3 leading-relaxed', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

/* ─── CardContent ───────────────────────────────────────────────────── */
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('p-5', className)}
    {...props}
  />
));
CardContent.displayName = 'CardContent';

/* ─── CardFooter ────────────────────────────────────────────────────── */
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center px-5 py-3 border-t border-white/[0.04] bg-surface-1/40',
      className
    )}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
