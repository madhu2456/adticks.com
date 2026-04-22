'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap',
    'font-medium rounded-lg select-none cursor-pointer',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
    'disabled:pointer-events-none disabled:opacity-40',
    'relative overflow-hidden',
  ].join(' '),
  {
    variants: {
      variant: {
        default: [
          'bg-gradient-brand text-white',
          'shadow-glow-sm hover:shadow-glow',
          'hover:opacity-90 active:scale-[0.98]',
        ].join(' '),
        secondary: [
          'bg-surface-3 text-text-2 border border-white/[0.06]',
          'hover:bg-surface-3/80 hover:text-text-1 hover:border-white/10',
          'active:scale-[0.98]',
        ].join(' '),
        ghost: [
          'bg-transparent text-text-2',
          'hover:bg-surface-3 hover:text-text-1',
          'active:scale-[0.98]',
        ].join(' '),
        outline: [
          'bg-transparent text-text-1 border border-white/10',
          'hover:bg-surface-3 hover:border-white/[0.15]',
          'active:scale-[0.98]',
        ].join(' '),
        danger: [
          'bg-danger/10 text-danger border border-danger/20',
          'hover:bg-danger/15 hover:border-danger/30',
          'active:scale-[0.98]',
        ].join(' '),
        success: [
          'bg-success/10 text-success border border-success/20',
          'hover:bg-success/15 hover:border-success/30',
          'active:scale-[0.98]',
        ].join(' '),
        link: [
          'bg-transparent text-primary underline-offset-4',
          'hover:underline hover:text-primary/80',
          'p-0 h-auto',
        ].join(' '),
      },
      size: {
        sm:   'h-8 px-3 text-xs gap-1.5',
        md:   'h-9 px-4 text-sm',
        lg:   'h-11 px-6 text-base',
        icon: 'h-9 w-9 p-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={isDisabled}
        {...props}
      >
        {loading ? (
          <Loader2 className="animate-spin shrink-0" size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} />
        ) : leftIcon ? (
          <span className="shrink-0">{leftIcon}</span>
        ) : null}
        {size !== 'icon' && children}
        {!loading && rightIcon && (
          <span className="shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
