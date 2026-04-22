"use client";

import React, { ReactNode } from "react";
import { ErrorBoundary, ErrorBoundaryProps } from "./ErrorBoundary";

interface PageErrorBoundaryProps extends Omit<ErrorBoundaryProps, "level"> {
  children: ReactNode;
}

/**
 * PageErrorBoundary wraps entire pages to provide full-page error recovery.
 * Shows complete error UI with "Go Home" navigation option.
 */
export function PageErrorBoundary({ children, ...props }: PageErrorBoundaryProps) {
  return (
    <ErrorBoundary level="page" {...props}>
      {children}
    </ErrorBoundary>
  );
}
