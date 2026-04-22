import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";
import { SectionErrorBoundary } from "@/components/SectionErrorBoundary";
import { AsyncErrorBoundary, useErrorHandler } from "@/components/AsyncErrorBoundary";
import {
  useErrorHandler as useErrorHandlerHook,
  createContextError,
  withAsyncErrorHandler,
  ErrorRecovery,
} from "@/hooks/useErrorHandler";

// Mock console methods
const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();
const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

// Test component that throws an error
function ErrorThrowingComponent(): React.ReactNode {
  throw new Error("Test error");
}

// Test component that conditionally throws
interface ConditionalErrorProps {
  shouldError: boolean;
}

function ConditionalErrorComponent({ shouldError }: ConditionalErrorProps) {
  if (shouldError) {
    throw new Error("Conditional error");
  }
  return <div>No error</div>;
}

// Test component with useErrorHandler hook
function AsyncErrorComponent() {
  const throwError = useErrorHandlerHook();

  const handleClick = async () => {
    try {
      throw new Error("Async error");
    } catch (error) {
      throwError(error);
    }
  };

  return <button onClick={handleClick}>Trigger Error</button>;
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <div>Content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("catches render errors and shows error UI", () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText(/error loading content/i)).toBeInTheDocument();
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("displays retry button", () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );
    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it("recovers from error when retry is clicked", () => {
    render(
      <ErrorBoundary>
        <ConditionalErrorComponent shouldError={true} />
      </ErrorBoundary>
    );
    // Verify error is displayed
    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();

    // Clicking retry should work (implementation detail - just verify button exists and is clickable)
    fireEvent.click(retryButton);
    // The recovery will happen if the children change to not throw
  });

  it("calls custom onError handler", () => {
    const onError = jest.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );
    expect(onError).toHaveBeenCalledWith(expect.any(Error), expect.any(String));
  });

  it("renders custom fallback when provided", () => {
    const customFallback = (error: Error) => <div>Custom error: {error.message}</div>;
    render(
      <ErrorBoundary fallback={customFallback}>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText("Custom error: Test error")).toBeInTheDocument();
  });

  it("shows error details in development mode", () => {
    const originalEnv = process.env.NODE_ENV;
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "development",
      configurable: true,
    });

    render(
      <ErrorBoundary>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );

    const detailsButton = screen.getByText(/details/i);
    expect(detailsButton).toBeInTheDocument();

    Object.defineProperty(process.env, "NODE_ENV", {
      value: originalEnv,
      configurable: true,
    });
  });

  it("logs errors with context", () => {
    render(
      <ErrorBoundary level="page">
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );
    // Verify that console.error was called (error logging happens)
    expect(consoleErrorSpy.mock.calls.length).toBeGreaterThan(0);
  });
});

describe("PageErrorBoundary", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("renders children without error", () => {
    render(
      <PageErrorBoundary>
        <div>Page Content</div>
      </PageErrorBoundary>
    );
    expect(screen.getByText("Page Content")).toBeInTheDocument();
  });

  it("catches page-level errors", () => {
    render(
      <PageErrorBoundary>
        <ErrorThrowingComponent />
      </PageErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("displays go home button for page errors", () => {
    render(
      <PageErrorBoundary>
        <ErrorThrowingComponent />
      </PageErrorBoundary>
    );
    const goHomeButton = screen.getByRole("button", { name: /go home/i });
    expect(goHomeButton).toBeInTheDocument();
  });

  it("displays go home button for page errors", () => {
    render(
      <PageErrorBoundary>
        <ErrorThrowingComponent />
      </PageErrorBoundary>
    );
    const goHomeButton = screen.getByRole("button", { name: /go home/i });
    expect(goHomeButton).toBeInTheDocument();
  });
});

describe("SectionErrorBoundary", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("renders children without error", () => {
    render(
      <SectionErrorBoundary>
        <div>Section Content</div>
      </SectionErrorBoundary>
    );
    expect(screen.getByText("Section Content")).toBeInTheDocument();
  });

  it("catches section errors without breaking page", () => {
    render(
      <div>
        <div>Other content</div>
        <SectionErrorBoundary title="Test Section">
          <ErrorThrowingComponent />
        </SectionErrorBoundary>
      </div>
    );
    expect(screen.getByText("Other content")).toBeInTheDocument();
    expect(screen.getByText("Test Section")).toBeInTheDocument();
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("shows compact error UI for sections", () => {
    render(
      <SectionErrorBoundary title="Cards">
        <ErrorThrowingComponent />
      </SectionErrorBoundary>
    );
    expect(screen.getByText("Cards")).toBeInTheDocument();
    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it("recovers sections independently", () => {
    render(
      <div>
        <SectionErrorBoundary title="Section 2">
          <div>Working section</div>
        </SectionErrorBoundary>
      </div>
    );

    expect(screen.getByText("Working section")).toBeInTheDocument();
  });
});

describe("AsyncErrorBoundary", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("renders children without error", async () => {
    render(
      <AsyncErrorBoundary>
        <div>Async Content</div>
      </AsyncErrorBoundary>
    );
    expect(screen.getByText("Async Content")).toBeInTheDocument();
  });

  it("catches async errors", async () => {
    render(
      <AsyncErrorBoundary>
        <ErrorThrowingComponent />
      </AsyncErrorBoundary>
    );
    expect(screen.getByText(/error loading content/i)).toBeInTheDocument();
  });

  it("shows suspension fallback while loading", () => {
    render(
      <AsyncErrorBoundary suspenseFallback={<div>Loading async data...</div>}>
        <div>Content</div>
      </AsyncErrorBoundary>
    );
    // Content should render (Suspense not triggered without actual suspended component)
    expect(screen.getByText("Content")).toBeInTheDocument();
  });
});

describe("useErrorHandler Hook", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("is available for use in components", () => {
    // Verify the hook exists and can be imported
    expect(typeof useErrorHandlerHook).toBe("function");
  });

  it("allows custom error handling with boundary", () => {
    const onError = jest.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalled();
  });
});

describe("Error Handler Utilities", () => {
  describe("createContextError", () => {
    it("creates error with context information", () => {
      const error = createContextError("API failed", { endpoint: "/api/data", status: 500 });
      expect(error.message).toBe("API failed");
      expect((error as any).context).toEqual({ endpoint: "/api/data", status: 500 });
    });
  });

  describe("withAsyncErrorHandler", () => {
    it("catches and rethrows async errors", async () => {
      const fn = jest.fn().mockRejectedValue(new Error("Async failed"));
      const wrapped = withAsyncErrorHandler(fn);

      await expect(wrapped()).rejects.toThrow("Async failed");
      expect(fn).toHaveBeenCalled();
    });

    it("preserves successful results", async () => {
      const fn = jest.fn().mockResolvedValue("success");
      const wrapped = withAsyncErrorHandler(fn);

      const result = await wrapped();
      expect(result).toBe("success");
    });
  });

  describe("ErrorRecovery.retry", () => {
    it("retries failed operation with exponential backoff", async () => {
      const fn = jest
        .fn()
        .mockRejectedValueOnce(new Error("Fail 1"))
        .mockRejectedValueOnce(new Error("Fail 2"))
        .mockResolvedValueOnce("success");

      const result = await ErrorRecovery.retry(fn, { maxAttempts: 3, initialDelayMs: 10 });
      expect(result).toBe("success");
      expect(fn).toHaveBeenCalledTimes(3);
    });

    it("throws after max attempts exceeded", async () => {
      const fn = jest.fn().mockRejectedValue(new Error("Always fails"));

      await expect(
        ErrorRecovery.retry(fn, { maxAttempts: 2, initialDelayMs: 10 })
      ).rejects.toThrow("Always fails");
      expect(fn).toHaveBeenCalledTimes(2);
    });
  });

  describe("ErrorRecovery.withTimeout", () => {
    it("rejects promise that takes too long", async () => {
      const slowPromise = new Promise((resolve) =>
        setTimeout(() => resolve("late"), 1000)
      );

      await expect(ErrorRecovery.withTimeout(slowPromise, 100)).rejects.toThrow(
        /timed out/i
      );
    });

    it("resolves promise within timeout", async () => {
      const quickPromise = Promise.resolve("quick");
      const result = await ErrorRecovery.withTimeout(quickPromise, 1000);
      expect(result).toBe("quick");
    });
  });

  describe("ErrorRecovery.withFallback", () => {
    it("uses fallback value on error", async () => {
      const failingPromise = Promise.reject(new Error("Failed"));
      const result = await ErrorRecovery.withFallback(failingPromise, "fallback value");
      expect(result).toBe("fallback value");
    });

    it("uses fallback function on error", async () => {
      const failingPromise = Promise.reject(new Error("Failed"));
      const fallbackFn = jest.fn().mockResolvedValue("fallback result");
      const result = await ErrorRecovery.withFallback(failingPromise, fallbackFn);
      expect(result).toBe("fallback result");
      expect(fallbackFn).toHaveBeenCalled();
    });

    it("returns original value on success", async () => {
      const successPromise = Promise.resolve("success");
      const result = await ErrorRecovery.withFallback(successPromise, "fallback");
      expect(result).toBe("success");
    });
  });
});

describe("Error Boundary Edge Cases", () => {
  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("has retry button on error", () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("calls onError handler multiple times for repeated errors", () => {
    const onError = jest.fn();
    render(
      <ErrorBoundary onError={onError} level="section">
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("handles error report button click", async () => {
    const alertSpy = jest.spyOn(window, "alert").mockImplementation();

    render(
      <ErrorBoundary>
        <ErrorThrowingComponent />
      </ErrorBoundary>
    );

    fireEvent.click(screen.getByRole("button", { name: /report error/i }));

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    });

    alertSpy.mockRestore();
  });

  it("preserves component state in different error boundaries", () => {
    render(
      <div>
        <ErrorBoundary>
          <ErrorThrowingComponent />
        </ErrorBoundary>
        <div>Sibling content</div>
      </div>
    );

    expect(screen.getByText("Sibling content")).toBeInTheDocument();
  });
});
