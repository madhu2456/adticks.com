import * as React from 'react';
import { cn } from '@/lib/utils';

/* ─── Base Skeleton ──────────────────────────────────────────────────── */
function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'skeleton',
        className
      )}
      {...props}
    />
  );
}

/* ─── SkeletonText — multiple text lines ─────────────────────────────── */
interface SkeletonTextProps {
  lines?: number;
  className?: string;
  lastLineWidth?: string;
}

function SkeletonText({ lines = 3, className, lastLineWidth = 'w-3/4' }: SkeletonTextProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn('h-3', i === lines - 1 ? lastLineWidth : 'w-full')}
        />
      ))}
    </div>
  );
}

/* ─── SkeletonCard ────────────────────────────────────────────────────── */
interface SkeletonCardProps {
  className?: string;
  showAvatar?: boolean;
}

function SkeletonCard({ className, showAvatar = false }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl bg-surface-2 border border-white/[0.06] p-5 flex flex-col gap-4',
        className
      )}
    >
      {showAvatar && (
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-9 rounded-full shrink-0" />
          <div className="flex-1 flex flex-col gap-1.5">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-2.5 w-20" />
          </div>
        </div>
      )}
      <Skeleton className="h-32 w-full rounded-lg" />
      <SkeletonText lines={2} lastLineWidth="w-2/3" />
    </div>
  );
}

/* ─── SkeletonTable ───────────────────────────────────────────────────── */
interface SkeletonTableProps {
  rows?: number;
  cols?: number;
  className?: string;
}

function SkeletonTable({ rows = 5, cols = 4, className }: SkeletonTableProps) {
  return (
    <div className={cn('flex flex-col', className)}>
      {/* Header */}
      <div className="flex gap-3 px-4 py-2.5 border-b border-white/[0.06]">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton
            key={i}
            className={cn('h-2.5', i === 0 ? 'w-1/3' : 'flex-1')}
          />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          className="flex gap-3 px-4 py-3 border-b border-white/[0.04] last:border-0"
        >
          {Array.from({ length: cols }).map((_, colIdx) => (
            <Skeleton
              key={colIdx}
              className={cn(
                'h-3',
                colIdx === 0 ? 'w-1/3' : 'flex-1',
                // vary widths subtly for realism
                colIdx > 0 && rowIdx % 2 === 0 ? 'opacity-70' : ''
              )}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export { Skeleton, SkeletonText, SkeletonCard, SkeletonTable };
