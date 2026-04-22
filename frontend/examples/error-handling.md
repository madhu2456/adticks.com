# Error Handling Guide

AdTicks provides a comprehensive error boundary system for graceful error handling across the frontend application. This guide covers error boundary components, recovery strategies, and best practices.

## Quick Start

### Page-Level Error Boundary

Wrap entire pages to catch all render errors and provide recovery options:

```tsx
import { PageErrorBoundary } from "@/components/PageErrorBoundary";

export default function DashboardPage() {
  return (
    <PageErrorBoundary>
      <DashboardContent />
    </PageErrorBoundary>
  );
}
```

### Section-Level Error Boundary

Isolate errors to specific sections without breaking the entire page:

```tsx
import { SectionErrorBoundary } from "@/components/SectionErrorBoundary";

export default function Dashboard() {
  return (
    <div>
      <Header />
      <SectionErrorBoundary title="Analytics">
        <AnalyticsSection />
      </SectionErrorBoundary>
      <SectionErrorBoundary title="Charts">
        <ChartsSection />
      </SectionErrorBoundary>
    </div>
  );
}
```

### Async Error Boundary

Handle errors from async operations and Promise-based components:

```tsx
import { AsyncErrorBoundary } from "@/components/AsyncErrorBoundary";

export default function UserProfile() {
  return (
    <AsyncErrorBoundary suspenseFallback={<LoadingSkeleton />}>
      <UserData />
    </AsyncErrorBoundary>
  );
}
```

## Components

### ErrorBoundary

Base error boundary component that captures React render errors.

**Props:**
- `children` - Components to wrap
- `fallback?` - Custom error UI component
- `onError?` - Custom error handler callback
- `level?` - Error severity level: `"page"`, `"section"`, or `"component"`

**Features:**
- Captures render errors
- Displays error UI with recovery options
- Logs errors with context (timestamp, URL, component stack)
- Shows stack traces in development mode
- Retry button to recover from errors

**Example:**

```tsx
<ErrorBoundary
  level="page"
  onError={(error, stack) => {
    console.log("Error caught:", error);
    // Send to error tracking service
  }}
>
  <MyComponent />
</ErrorBoundary>
```

### PageErrorBoundary

Specialized boundary for page-level errors. Shows full-page error UI with "Go Home" navigation.

```tsx
<PageErrorBoundary>
  <PageContent />
</PageErrorBoundary>
```

### SectionErrorBoundary

Isolates errors to specific sections. Shows compact error UI that doesn't break the entire page.

```tsx
<SectionErrorBoundary title="Sales Data">
  <SalesChart />
</SectionErrorBoundary>
```

### AsyncErrorBoundary

Combines error boundary with Suspense for async operations.

```tsx
<AsyncErrorBoundary
  suspenseFallback={<div>Loading...</div>}
  onError={(error) => logError(error)}
>
  <AsyncComponent />
</AsyncErrorBoundary>
```

## Hooks and Utilities

### useErrorHandler

Throw errors from async operations to be caught by error boundaries.

```tsx
import { useErrorHandler } from "@/hooks/useErrorHandler";

function MyComponent() {
  const throwError = useErrorHandler();

  const handleFetch = async () => {
    try {
      const data = await fetchData();
      setData(data);
    } catch (error) {
      throwError(error); // Caught by ErrorBoundary
    }
  };

  return <button onClick={handleFetch}>Load Data</button>;
}
```

### createContextError

Create errors with additional context for debugging:

```tsx
import { createContextError } from "@/hooks/useErrorHandler";

throw createContextError("Failed to fetch user", {
  userId: user.id,
  endpoint: "/api/users",
  timestamp: new Date(),
});
```

### withAsyncErrorHandler

Wrapper function for automatic error handling in async operations:

```tsx
import { withAsyncErrorHandler } from "@/hooks/useErrorHandler";

const fetchData = withAsyncErrorHandler(async () => {
  const response = await api.get("/data");
  return response.data;
});
```

### ErrorRecovery Utilities

Utility functions for advanced error recovery strategies:

```tsx
import { ErrorRecovery } from "@/hooks/useErrorHandler";

// Retry with exponential backoff
const data = await ErrorRecovery.retry(
  () => fetchData(),
  {
    maxAttempts: 3,
    initialDelayMs: 100,
    backoffMultiplier: 2,
  }
);

// Execute with timeout
const result = await ErrorRecovery.withTimeout(
  slowOperation(),
  5000 // 5 second timeout
);

// Use fallback value on error
const data = await ErrorRecovery.withFallback(
  fetchData(),
  { /* default data */ }
);
```

## Common Patterns

### API Error Handling

```tsx
function UserList() {
  const [users, setUsers] = useState([]);
  const throwError = useErrorHandler();

  const loadUsers = async () => {
    try {
      const response = await fetch("/api/users");
      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.status}`);
      }
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      throwError(error);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  return (
    <div>
      {users.map((user) => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  );
}

export default function Page() {
  return (
    <PageErrorBoundary>
      <UserList />
    </PageErrorBoundary>
  );
}
```

### Form Validation Errors

```tsx
function LoginForm() {
  const throwError = useErrorHandler();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Validation
      const errors = validateForm(formData);
      if (Object.keys(errors).length > 0) {
        throw new Error(`Validation failed: ${Object.values(errors).join(", ")}`);
      }

      // Submit
      const response = await submitLogin(formData);
      handleLoginSuccess(response);
    } catch (error) {
      throwError(error);
    }
  };

  return <form onSubmit={handleSubmit}>...</form>;
}
```

### Nested Error Boundaries

```tsx
function Dashboard() {
  return (
    <PageErrorBoundary>
      <div className="grid">
        <SectionErrorBoundary title="Analytics">
          <AnalyticsSection />
        </SectionErrorBoundary>

        <SectionErrorBoundary title="Charts">
          <ChartsSection />
        </SectionErrorBoundary>

        <SectionErrorBoundary title="Metrics">
          <MetricsSection />
        </SectionErrorBoundary>
      </div>
    </PageErrorBoundary>
  );
}
```

### Custom Error UI

```tsx
function CustomErrorFallback(error: Error, reset: () => void) {
  return (
    <div className="custom-error">
      <h2>Oops! Something went wrong</h2>
      <p>{error.message}</p>
      <div className="actions">
        <button onClick={reset}>Try Again</button>
        <button onClick={() => (window.location.href = "/")}>Home</button>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <PageErrorBoundary fallback={CustomErrorFallback}>
      <PageContent />
    </PageErrorBoundary>
  );
}
```

## Error Types

### Render Errors

Errors that occur during component rendering:

```tsx
function Component() {
  // This error is caught by ErrorBoundary
  return <div>{undefined.toUpperCase()}</div>;
}
```

### Async Errors

Errors from promises and async operations:

```tsx
function Component() {
  const throwError = useErrorHandler();

  useEffect(() => {
    fetchData()
      .then(setData)
      .catch(throwError); // Caught by ErrorBoundary
  }, []);
}
```

### Event Handler Errors

Error handlers in event listeners need manual error boundary integration:

```tsx
function Component() {
  const throwError = useErrorHandler();

  const handleClick = () => {
    try {
      // This error won't be caught by ErrorBoundary
      throw new Error("Oops");
    } catch (error) {
      throwError(error); // Now it will be caught
    }
  };

  return <button onClick={handleClick}>Click</button>;
}
```

## Error Logging

All errors are logged with comprehensive context:

```
{
  message: "Failed to fetch data",
  stack: "Error: Failed to fetch data\n    at fetchData (...)",
  componentStack: "in UserList (created by Dashboard)\n    in Dashboard",
  level: "page",
  timestamp: "2024-01-15T10:30:45.123Z",
  userAgent: "Mozilla/5.0...",
  url: "http://localhost:3000/dashboard"
}
```

Future phases will integrate with Sentry for centralized error tracking and monitoring.

## Best Practices

1. **Use appropriate boundaries**: Wrap pages with `PageErrorBoundary` and sections with `SectionErrorBoundary`.

2. **Provide context**: Use `createContextError` to attach relevant information to errors.

3. **Handle async errors**: Always use `useErrorHandler` or `withAsyncErrorHandler` for promises and async operations.

4. **Custom error UI**: Override the fallback UI for critical sections to match your design.

5. **Test error scenarios**: Write tests for error boundaries to ensure graceful error handling.

6. **Log strategically**: Enable error logging in development and integrate with error tracking in production.

7. **Recovery options**: Provide meaningful recovery actions (retry, go home, report).

## Testing Error Boundaries

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorBoundary } from "@/components/ErrorBoundary";

function ErrorComponent() {
  throw new Error("Test error");
}

it("catches render errors", () => {
  render(
    <ErrorBoundary>
      <ErrorComponent />
    </ErrorBoundary>
  );
  expect(screen.getByText("Test error")).toBeInTheDocument();
});

it("recovers from errors when retry is clicked", () => {
  const { rerender } = render(
    <ErrorBoundary>
      <ErrorComponent />
    </ErrorBoundary>
  );

  fireEvent.click(screen.getByRole("button", { name: /retry/i }));

  rerender(
    <ErrorBoundary>
      <div>Recovered</div>
    </ErrorBoundary>
  );

  expect(screen.getByText("Recovered")).toBeInTheDocument();
});
```

## Troubleshooting

### Error Boundary Not Catching Errors

Error boundaries do NOT catch:
- Event handlers (use try-catch or `useErrorHandler`)
- Async code (use `useErrorHandler` or `AsyncErrorBoundary`)
- Server-side rendering errors
- Errors in the error boundary itself

Solution: Use `useErrorHandler` for these scenarios.

### Blank Screen on Error

Ensure you have a top-level `PageErrorBoundary` in your root layout:

```tsx
// app/layout.tsx
<PageErrorBoundary>
  <Navbar />
  {children}
  <Footer />
</PageErrorBoundary>
```

### Component Stack Not Showing

Component stack is available in React 17+ and will be included in the error logs when `getDerivedStateFromError` is used.

## Migration Guide

### Phase 1: Add Error Boundaries to Layouts

```tsx
// app/(dashboard)/layout.tsx
<PageErrorBoundary>
  <DashboardLayout>{children}</DashboardLayout>
</PageErrorBoundary>
```

### Phase 2: Wrap Critical Sections

```tsx
<SectionErrorBoundary title="Analytics">
  <AnalyticsComponent />
</SectionErrorBoundary>
```

### Phase 3: Use useErrorHandler for Async

```tsx
const throwError = useErrorHandler();
// Use in catch blocks
```

### Phase 4: Integrate Error Tracking

Connect to Sentry or similar service for production monitoring.
