'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Icon displayed on the left inside the input */
  prefixIcon?: React.ReactNode;
  /** Icon or element displayed on the right inside the input */
  suffixIcon?: React.ReactNode;
  /** Show error styling and message */
  error?: string;
  /** Helper text below input */
  hint?: string;
  /** Label above input */
  label?: string;
  /** Wrapper className */
  wrapperClassName?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      wrapperClassName,
      type = 'text',
      prefixIcon,
      suffixIcon,
      error,
      hint,
      label,
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const hasPrefix = Boolean(prefixIcon);
    const hasSuffix = Boolean(suffixIcon);

    return (
      <div className={cn('flex flex-col gap-1.5', wrapperClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-text-2 select-none"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {hasPrefix && (
            <span className="absolute left-3 flex items-center text-text-3 pointer-events-none z-10">
              {prefixIcon}
            </span>
          )}

          <input
            id={inputId}
            ref={ref}
            type={type}
            disabled={disabled}
            className={cn(
              // Base
              'w-full h-9 rounded-lg text-sm text-text-1 bg-surface-1',
              'border border-white/[0.08]',
              'placeholder:text-text-3',
              // Padding
              hasPrefix ? 'pl-9' : 'pl-3',
              hasSuffix ? 'pr-9' : 'pr-3',
              // Focus
              'outline-none',
              'focus:border-primary/50 focus:shadow-glow-sm',
              'transition-all duration-150',
              // Disabled
              'disabled:opacity-40 disabled:cursor-not-allowed',
              // Error
              error && 'border-danger/60 focus:border-danger/80 focus:shadow-none',
              className
            )}
            {...props}
          />

          {hasSuffix && (
            <span className="absolute right-3 flex items-center text-text-3 z-10">
              {suffixIcon}
            </span>
          )}
        </div>

        {error && (
          <p className="text-xs text-danger leading-snug">{error}</p>
        )}
        {!error && hint && (
          <p className="text-xs text-text-3 leading-snug">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
