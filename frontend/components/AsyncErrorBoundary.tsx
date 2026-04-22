"use client";

import React, { ReactNode, Suspense } from "react";
import { ErrorBoundary } from "./ErrorBoundary";

interface AsyncErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, componentStack: string) => void;
  suspenseFallback?: ReactNode;
}

/**
 * AsyncErrorBoundary handles errors from async operations and components.
 * Combines ErrorBoundary with Suspense for comprehensive async error handling.
 *
 * Use cases:
 * - Components that throw promises (with React.lazy)
 * - Async data fetching with Suspense
 * - Error boundaries for streaming components
 */
export function AsyncErrorBoundary({
  children,
  fallback,
  onError,
  suspenseFallback = <div className="p-4 text-center">Loading...</div>,
}: AsyncErrorBoundaryProps) {
  return (
    <ErrorBoundary level="component" fallback={fallback} onError={onError}>
      <Suspense fallback={suspenseFallback}>{children}</Suspense>
    </ErrorBoundary>
  );
}

/**
 * Hook to throw errors from async operations that will be caught by ErrorBoundary.
 * Use in async components or event handlers.
 *
 * @example
 * function MyComponent() {
 *   const throwError = useErrorHandler();
 *
 *   const fetchData = async () => {
 *     try {
 *       const result = await api.fetch();
 *     } catch (error) {
 *       throwError(error); // Will be caught by ErrorBoundary
 *     }
 *   };
 * }
 */
export function useErrorHandler() {
  const [, setError] = React.useState();

  return React.useCallback((error: unknown) => {
    setError(() => {
      throw error;
    });
  }, []);
}
