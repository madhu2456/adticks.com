"use client";

import { useCallback, useState } from "react";

/**
 * Hook to throw errors from async operations that will be caught by ErrorBoundary.
 *
 * @returns Function to throw an error
 *
 * @example
 * function MyComponent() {
 *   const throwError = useErrorHandler();
 *
 *   const handleAsyncOperation = async () => {
 *     try {
 *       const result = await fetchData();
 *       return result;
 *     } catch (error) {
 *       throwError(error);
 *     }
 *   };
 *
 *   return <button onClick={handleAsyncOperation}>Fetch Data</button>;
 * }
 */
export function useErrorHandler() {
  const [error, setError] = useState<unknown>(null);

  if (error) {
    throw error;
  }

  return useCallback((err: unknown) => {
    setError(normalizeError(err));
  }, []);
}

/**
 * Normalize error to ensure it's always an Error instance.
 */
function normalizeError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }

  if (typeof error === "string") {
    return new Error(error);
  }

  if (typeof error === "object" && error !== null) {
    return new Error(JSON.stringify(error));
  }

  return new Error(String(error));
}

/**
 * Create error with context information for better debugging.
 *
 * @example
 * throw createContextError("Failed to fetch user data", {
 *   userId: user.id,
 *   endpoint: "/api/user",
 * });
 */
export function createContextError(message: string, context: Record<string, unknown>) {
  const error = new Error(message);
  (error as any).context = context;
  return error;
}

/**
 * Async error handler wrapper for promise-based operations.
 * Automatically catches and rethrows errors for ErrorBoundary.
 *
 * @example
 * const handleFetchUser = withAsyncErrorHandler(async () => {
 *   const response = await api.getUser();
 *   return response;
 * });
 */
export function withAsyncErrorHandler<T extends any[], R>(
  fn: (...args: T) => Promise<R>
): (...args: T) => Promise<R | undefined> {
  return async (...args: T) => {
    try {
      return await fn(...args);
    } catch (error) {
      console.error("Async error:", error);
      throw normalizeError(error);
    }
  };
}

/**
 * Error recovery utilities.
 */
export const ErrorRecovery = {
  /**
   * Retry an async operation with exponential backoff.
   */
  async retry<T>(
    fn: () => Promise<T>,
    options: {
      maxAttempts?: number;
      initialDelayMs?: number;
      maxDelayMs?: number;
      backoffMultiplier?: number;
    } = {}
  ): Promise<T> {
    const {
      maxAttempts = 3,
      initialDelayMs = 100,
      maxDelayMs = 5000,
      backoffMultiplier = 2,
    } = options;

    let lastError: Error | undefined;
    let delayMs = initialDelayMs;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = normalizeError(error);

        if (attempt < maxAttempts) {
          await new Promise((resolve) => setTimeout(resolve, delayMs));
          delayMs = Math.min(delayMs * backoffMultiplier, maxDelayMs);
        }
      }
    }

    throw lastError || new Error("Failed after retries");
  },

  /**
   * Execute with timeout.
   */
  async withTimeout<T>(
    promise: Promise<T>,
    timeoutMs: number = 5000
  ): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
      ),
    ]);
  },

  /**
   * Fallback value if operation fails.
   */
  async withFallback<T>(
    promise: Promise<T>,
    fallback: T | (() => Promise<T>)
  ): Promise<T> {
    try {
      return await promise;
    } catch (error) {
      console.warn("Operation failed, using fallback:", error);
      if (typeof fallback === "function") {
        return await (fallback as () => Promise<T>)();
      }
      return fallback;
    }
  },
};
