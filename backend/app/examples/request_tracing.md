# Request ID Propagation in AdTicks

## Overview

Request ID propagation enables end-to-end tracing of requests across all services in AdTicks:
- **HTTP Endpoints**: Request IDs are automatically captured and included in responses
- **Celery Tasks**: Request IDs flow from HTTP requests into background tasks
- **External API Calls**: Request IDs are automatically injected into calls to external services
- **Structured Logs**: All logs automatically include the request ID for correlation

## Architecture

The request ID propagation system uses Python's `contextvars` (context variables) to maintain request context across async boundaries, task queues, and external service calls.

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP Request                                 │
│              (with or without X-Request-ID header)              │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  add_request_id middleware  │
                    │  Sets request_id_context    │
                    └──────────────┬──────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
   ┌─────────────┐         ┌─────────────┐         ┌──────────────┐
   │   Endpoint  │         │Celery Task  │         │ External API │
   │   Handler   │         │  (delayed)  │         │    Call      │
   │             │         │             │         │              │
   │ Logs include│◄───────►│ Logs include│◄───────►│ Has X-Request│
   │ request_id  │         │ request_id  │         │ -ID header   │
   └─────────────┘         └─────────────┘         └──────────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Response with X-Request-ID │
                    │         Header              │
                    └─────────────────────────────┘
```

## Core Components

### 1. Logging Module (`backend/app/core/logging.py`)

#### Functions:

**`get_request_id() -> str | None`**
- Retrieves the current request ID from context
- Returns `None` if no request ID is set
- Safe to call anywhere in the application

```python
from app.core.logging import get_request_id

request_id = get_request_id()
print(f"Current request: {request_id}")
```

**`set_request_id(request_id: str | None = None) -> str`**
- Sets the request ID in the context
- Generates a UUID if no ID is provided
- Called automatically by the HTTP middleware

```python
from app.core.logging import set_request_id

# Manual request ID setting (rarely needed)
request_id = set_request_id("manual-id-123")
```

**`set_request_id_for_task(request_id: str | None) -> None`**
- Sets request ID for Celery task execution
- Called automatically by Celery signal handlers
- Use this in task signal handlers

```python
from app.core.logging import set_request_id_for_task

# In Celery signal handler
@signals.task_prerun.connect
def on_task_prerun(sender=None, **kwargs):
    request_id = task.request.headers.get("x_request_id")
    set_request_id_for_task(request_id)
```

**`with_request_id(request_id: str | None) -> Generator`**
- Context manager to temporarily set a request ID
- Automatically restores the previous ID when exiting
- Useful for executing code in a specific request context

```python
from app.core.logging import with_request_id, get_logger

logger = get_logger(__name__)

with with_request_id("req-123"):
    logger.info("message")  # Will have request_id="req-123"
    # Do work here
```

### 2. Celery Integration (`backend/app/core/celery_app.py`)

#### Signal Handlers:

**`before_task_publish_handler`**
- Triggered before a task is published to the queue
- Captures the current request ID
- Stores it in the task's headers for later retrieval

**`task_prerun_handler`**
- Triggered before a task starts execution
- Restores the request ID from task headers into the task's execution context
- Ensures all logs in the task have the request ID

#### Helper Function:

**`apply_async_with_request_id(task, *args, **kwargs)`**
- Applies a task with automatic request ID propagation
- Alternative to `task.delay()` for explicit control

```python
from app.core.celery_app import apply_async_with_request_id
from app.tasks.seo_tasks import generate_keywords_task

# Request ID is automatically captured and propagated
apply_async_with_request_id(
    generate_keywords_task,
    project_id="proj-123",
    domain="example.com"
)
```

### 3. HTTP Client Wrapper (`backend/app/core/http_client.py`)

#### `RequestIDAsyncClient`
- Subclass of `httpx.AsyncClient`
- Automatically injects `X-Request-ID` header into all requests
- Used for all external API calls

#### `create_request_id_client(**kwargs) -> RequestIDAsyncClient`
- Factory function to create a request ID client
- Arguments are passed to `httpx.AsyncClient`

```python
from app.core.http_client import create_request_id_client

async with create_request_id_client(timeout=30.0) as client:
    response = await client.get("https://api.ahrefs.com/data")
    # X-Request-ID header is automatically included
```

## Usage Patterns

### Pattern 1: Standard Endpoint → Task → External API

```python
# endpoint
@router.post("/analyze")
async def analyze(project_id: str, current_user: User = Depends(get_current_user)):
    # Request ID is automatically set by middleware
    from app.tasks.analysis import analyze_project_task
    
    # Request ID is automatically propagated to the task
    task = analyze_project_task.delay(project_id=project_id)
    return {"task_id": task.id}

# In task
@celery_app.task
def analyze_project_task(project_id: str):
    logger = get_logger(__name__)
    # Log automatically includes request_id
    logger.info(f"Analyzing project {project_id}")
    
    # Make external API call
    async with create_request_id_client() as client:
        response = await client.get(
            "https://api.example.com/analyze",
            params={"project": project_id}
        )
        # X-Request-ID header is automatically included in the request
```

### Pattern 2: Task Chain with Request ID

```python
from app.core.celery_app import apply_async_with_request_id

@celery_app.task
def parent_task(project_id: str):
    logger = get_logger(__name__)
    logger.info("Starting parent task")
    
    # Request ID is automatically propagated to child task
    apply_async_with_request_id(
        child_task,
        project_id=project_id
    )

@celery_app.task
def child_task(project_id: str):
    logger = get_logger(__name__)
    # Log includes same request_id as parent task
    logger.info("Running child task")
```

### Pattern 3: External API Calls in Endpoints

```python
from app.core.http_client import create_request_id_client
from app.core.logging import get_logger

@router.get("/data/{project_id}")
async def get_external_data(project_id: str):
    logger = get_logger(__name__)
    
    async with create_request_id_client(timeout=30.0) as client:
        response = await client.get(
            "https://api.external.com/data",
            params={"id": project_id}
        )
        # X-Request-ID header is automatically included
        logger.info("Fetched external data")
    
    return response.json()
```

### Pattern 4: Manual Request ID Management

```python
from app.core.logging import with_request_id, get_logger

logger = get_logger(__name__)

# Execute some code in a specific request context
with with_request_id("custom-request-123"):
    logger.info("This log has request_id='custom-request-123'")
    
    # Even external API calls will include this request ID
    async with create_request_id_client() as client:
        await client.get("https://api.example.com/endpoint")
        # X-Request-ID: custom-request-123 is sent in the header
```

## Structured Logging

The logging system automatically includes request IDs in all structured logs. The JSON output includes:

```json
{
  "timestamp": "2024-01-15 10:30:45,123",
  "level": "INFO",
  "logger": "app.api.projects",
  "message": "Project analysis started",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "proj-123",
  "status": "queued"
}
```

Request IDs appear in logs from:
- **HTTP endpoints**: Captured by middleware
- **Celery tasks**: Restored from task headers
- **External API calls**: Logged by RequestIDAsyncClient
- **Database operations**: Visible in structured logs
- **Error handling**: Included in exception logs

## Testing Request ID Propagation

Use the `with_request_id()` context manager in tests:

```python
import pytest
from app.core.logging import with_request_id, get_request_id, get_logger

def test_request_id_in_task():
    from app.tasks.analysis import analyze_task
    
    logger = get_logger(__name__)
    test_request_id = "test-req-123"
    
    with with_request_id(test_request_id):
        assert get_request_id() == test_request_id
        
        # Task will have this request ID
        result = analyze_task.apply(args=["proj-123"])
```

## Debugging with Request IDs

To trace a request through the system:

1. **Find the request ID in the HTTP response header**:
   ```
   X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
   ```

2. **Search logs for that ID**:
   ```bash
   grep "550e8400-e29b-41d4-a716-446655440000" logs.json
   ```

3. **View the complete request flow**:
   - HTTP endpoint entry/exit
   - Task start/completion
   - External API calls
   - Database operations
   - Any errors that occurred

4. **Monitor external service logs**:
   - Search their logs for the same `X-Request-ID` to see what happened on their side

## Best Practices

1. **Always use `create_request_id_client()` for external API calls**
   - Never use plain `httpx.AsyncClient` for external APIs
   - Ensures request ID propagation

2. **Use `apply_async_with_request_id()` for task chains**
   - Preserves request context across task boundaries
   - Better than `task.delay()` when explicit propagation is needed

3. **Let the middleware handle request IDs in endpoints**
   - Don't manually set request IDs in HTTP handlers
   - The middleware does this automatically

4. **Use `with_request_id()` for testing**
   - Makes it easy to test code that depends on request IDs
   - Automatically restores the previous ID

5. **Log at appropriate levels**
   - INFO for normal operations
   - DEBUG for detailed request tracing
   - ERROR for failures

## Troubleshooting

**Problem**: Request IDs missing from task logs
- **Solution**: Ensure the HTTP endpoint calls `.delay()` or `.apply_async()` on the task
- The `before_task_publish_handler` signal captures the request ID

**Problem**: Request IDs not appearing in external API logs
- **Solution**: Always use `create_request_id_client()` instead of plain `httpx.AsyncClient`

**Problem**: Different request IDs in endpoint vs task logs
- **Solution**: Check that the task was actually called (not in a try/except that silently fails)
- Verify the Celery app is actually processing tasks

**Problem**: `get_request_id()` returns None
- **Solution**: You're outside an HTTP request or task context
- Use `with_request_id()` context manager to set one manually

## Configuration

No additional configuration is needed. Request ID propagation is built into:
- HTTP middleware in `main.py`
- Celery signal handlers in `celery_app.py`
- All logging operations via `JSONFormatter`

The system uses standard `contextvars` which works correctly with:
- Async/await
- Celery tasks
- Task chains
- Nested function calls
