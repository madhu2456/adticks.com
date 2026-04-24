"use client";

import React, { ReactNode } from "react";
import { CircleAlert, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, componentStack: string) => void;
  level?: "page" | "section" | "component";
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  componentStack: string | null;
  errorCount: number;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      componentStack: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState((prevState) => ({
      componentStack: errorInfo.componentStack || null,
      errorCount: prevState.errorCount + 1,
    }));

    // Log error with context
    this.logError(error, errorInfo.componentStack || "");

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo.componentStack || "");
    }
  }

  private logError = (error: Error, componentStack: string | null) => {
    const errorContext = {
      message: error.message,
      stack: error.stack,
      componentStack,
      level: this.props.level || "component",
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
      url: typeof window !== "undefined" ? window.location.href : "unknown",
    };

    // Log to console in development
    if (process.env.NODE_ENV === "development") {
      console.error("Error caught by ErrorBoundary:", errorContext);
    }

    // Send to error tracking service (Sentry, etc.)
    // This will be implemented in Phase 4
    if (typeof window !== "undefined" && (window as any).logErrorToService) {
      (window as any).logErrorToService(errorContext);
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      componentStack: null,
    });
  };

  private handleRetry = () => {
    this.handleReset();
  };

  private handleGoHome = () => {
    this.handleReset();
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  private handleReportError = async () => {
    if (!this.state.error) return;

    const errorData = {
      message: this.state.error.message,
      stack: this.state.error.stack,
      componentStack: this.state.componentStack,
      level: this.props.level || "component",
      timestamp: new Date().toISOString(),
    };

    try {
      // Will be replaced with actual API call
      console.log("Error report would be sent:", errorData);
      if (typeof window !== "undefined" && (window as any).__showAlert) {
        (window as any).__showAlert({
          title: "Thank You",
          message: "Thank you for reporting this error. Our team has been notified.",
          type: "success",
          confirmText: "OK",
        });
      }
    } catch (error) {
      console.error("Failed to report error:", error);
    }
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback ? (
        this.props.fallback(this.state.error!, this.handleReset)
      ) : (
        <DefaultErrorFallback
          error={this.state.error}
          componentStack={this.state.componentStack}
          level={this.props.level || "component"}
          onRetry={this.handleRetry}
          onGoHome={this.handleGoHome}
          onReportError={this.handleReportError}
        />
      );
    }

    return this.props.children;
  }
}

interface DefaultErrorFallbackProps {
  error: Error | null;
  componentStack: string | null;
  level: "page" | "section" | "component";
  onRetry: () => void;
  onGoHome: () => void;
  onReportError: () => void;
}

function DefaultErrorFallback({
  error,
  componentStack,
  level,
  onRetry,
  onGoHome,
  onReportError,
}: DefaultErrorFallbackProps) {
  const isProd = process.env.NODE_ENV === "production";
  const containerClass = level === "page" ? "min-h-screen" : "p-6 rounded-lg border";
  const bgColor = level === "page" ? "bg-background" : "bg-destructive/5 border-destructive/20";

  return (
    <div className={`${containerClass} ${bgColor} flex items-center justify-center`}>
      <div className="max-w-md w-full">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="p-3 bg-destructive/10 rounded-full">
            <CircleAlert className="h-6 w-6 text-destructive" />
          </div>

          <div>
            <h2 className="text-lg font-semibold text-text-primary mb-1">
              {level === "page" ? "Something went wrong" : "Error loading content"}
            </h2>
            <p className="text-sm text-text-secondary">
              {error?.message || "An unexpected error occurred. Please try again."}
            </p>
          </div>

          {!isProd && componentStack && (
            <details className="w-full text-left">
              <summary className="cursor-pointer text-xs text-text-tertiary hover:text-text-secondary font-mono py-2">
                Details (Development Only)
              </summary>
              <pre className="mt-2 p-3 bg-background rounded text-xs text-text-secondary overflow-auto max-h-40 border border-border">
                {componentStack}
              </pre>
            </details>
          )}

          <div className="flex gap-2 w-full pt-4">
            <Button variant="default" size="sm" onClick={onRetry} className="flex-1">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
            {level === "page" && (
              <Button variant="outline" size="sm" onClick={onGoHome} className="flex-1">
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </Button>
            )}
          </div>

          <Button variant="ghost" size="sm" onClick={onReportError} className="w-full text-xs">
            Report Error
          </Button>
        </div>
      </div>
    </div>
  );
}
