"use client";

import React, { ReactNode } from "react";
import { ErrorBoundary, ErrorBoundaryProps } from "./ErrorBoundary";

interface SectionErrorBoundaryProps extends Omit<ErrorBoundaryProps, "level"> {
  children: ReactNode;
  title?: string;
}

/**
 * SectionErrorBoundary wraps page sections or cards to isolate errors.
 * Shows compact error UI that doesn't break the entire page layout.
 */
export function SectionErrorBoundary({
  children,
  title = "Section",
  ...props
}: SectionErrorBoundaryProps) {
  return (
    <ErrorBoundary
      level="section"
      {...props}
      fallback={(error, reset) =>
        props.fallback ? (
          props.fallback(error, reset)
        ) : (
          <div className="p-6 rounded-lg border border-destructive/20 bg-destructive/5">
            <div className="flex flex-col gap-3">
              <div>
                <h3 className="text-sm font-semibold text-text-primary mb-1">{title}</h3>
                <p className="text-xs text-text-secondary">{error.message}</p>
              </div>
              <button
                onClick={reset}
                className="px-3 py-2 text-xs font-medium bg-primary text-white rounded hover:bg-primary/90 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        )
      }
    >
      {children}
    </ErrorBoundary>
  );
}
