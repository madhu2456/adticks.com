"""
Example: Request ID propagation in AdTicks

This example demonstrates complete request ID propagation:
1. HTTP request captures or generates request ID
2. Request ID flows to Celery tasks
3. External API calls include X-Request-ID header
4. All logs include the request ID for tracing
"""

# ============================================================================
# Example 1: Endpoint with Celery task
# ============================================================================

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger, get_request_id
from app.core.security import get_current_user
from app.models.user import User
from app.tasks.seo_tasks import generate_keywords_task

router = APIRouter(prefix="/example", tags=["example"])
logger = get_logger(__name__)


@router.post("/analyze/{project_id}")
async def analyze_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Example endpoint that triggers a background analysis task.
    
    Request ID is:
    1. Captured from HTTP header or generated
    2. Automatically logged at the endpoint
    3. Propagated to the Celery task
    4. Available in all logs throughout the request lifecycle
    """
    request_id = get_request_id()
    logger.info(
        "analysis_requested",
        extra={
            "project_id": str(project_id),
            "request_id": request_id,
        }
    )
    
    # Trigger analysis task - request ID is automatically propagated
    task = generate_keywords_task.delay(project_id=str(project_id))
    
    return {
        "status": "queued",
        "task_id": task.id,
        "request_id": request_id,  # Include in response for tracing
    }


# ============================================================================
# Example 2: Celery task with external API calls
# ============================================================================

from app.core.celery_app import celery_app
from app.core.http_client import create_request_id_client


@celery_app.task(bind=True)
def fetch_seo_data_task(self, project_id: str):
    """
    Example Celery task that makes external API calls.
    
    The request ID:
    1. Is automatically restored from task headers
    2. Is available in all logger calls
    3. Is injected into all external API calls
    """
    logger = get_logger(__name__)
    request_id = get_request_id()
    
    logger.info(
        "seo_data_fetch_started",
        extra={
            "project_id": project_id,
            "task_id": self.request.id,
        }
    )
    
    # Make external API call with automatic request ID injection
    try:
        async def fetch_from_external_api():
            async with create_request_id_client() as client:
                # Request includes X-Request-ID header automatically
                response = await client.get(
                    "https://api.ahrefs.com/v3/backlinks",
                    params={"target": "example.com"},
                )
                logger.info(
                    "external_api_call_succeeded",
                    extra={"status_code": response.status_code},
                )
                return response.json()
        
        # Run async function from sync Celery task
        import asyncio
        data = asyncio.run(fetch_from_external_api())
        
        logger.info(
            "seo_data_fetch_completed",
            extra={
                "project_id": project_id,
                "records": len(data) if isinstance(data, list) else 1,
            }
        )
        return data
        
    except Exception as e:
        logger.error(
            "seo_data_fetch_failed",
            extra={
                "project_id": project_id,
                "error": str(e),
            }
        )
        raise


# ============================================================================
# Example 3: Task chain with request ID
# ============================================================================

from app.core.celery_app import apply_async_with_request_id


@celery_app.task
def analyze_content_task(project_id: str, content: str):
    """Analyze content and trigger child tasks."""
    logger = get_logger(__name__)
    logger.info("content_analysis_started", extra={"project_id": project_id})
    
    # Request ID is automatically available here
    request_id = get_request_id()
    logger.debug("current_request_id", extra={"request_id": request_id})
    
    # Trigger child task with explicit request ID propagation
    apply_async_with_request_id(
        generate_report_task,
        args=(project_id, content),
    )
    
    return {"status": "started"}


@celery_app.task
def generate_report_task(project_id: str, content: str):
    """Generate report (child task of analyze_content_task)."""
    logger = get_logger(__name__)
    request_id = get_request_id()
    
    # This log has the same request_id as the parent task
    logger.info(
        "report_generation_started",
        extra={
            "project_id": project_id,
            "content_length": len(content),
        }
    )
    
    return {"status": "completed", "request_id": request_id}


# ============================================================================
# Example 4: Manual request ID management for testing
# ============================================================================

from app.core.logging import with_request_id


async def test_scenario():
    """Example test showing manual request ID management."""
    from app.core.logging import get_request_id
    
    logger = get_logger(__name__)
    
    # Execute code in a specific request context
    with with_request_id("test-scenario-123"):
        assert get_request_id() == "test-scenario-123"
        
        # All logs here have request_id="test-scenario-123"
        logger.info("test event 1")
        
        # Nested context temporarily overrides
        with with_request_id("nested-456"):
            assert get_request_id() == "nested-456"
            logger.info("test event 2")  # Has request_id="nested-456"
        
        # Back to original
        assert get_request_id() == "test-scenario-123"
        logger.info("test event 3")  # Has request_id="test-scenario-123"


# ============================================================================
# Example 5: Debugging with request IDs
# ============================================================================

def debug_request_trace(request_id: str):
    """
    Example function to trace a request through all logs.
    
    In production:
    1. Get the request ID from response header or error message
    2. Search logs for that ID
    3. View complete request flow
    """
    import json
    
    # Example log entries with request_id:
    sample_logs = [
        {
            "timestamp": "2024-01-15 10:30:45,123",
            "level": "INFO",
            "logger": "app.api.projects",
            "message": "analysis_requested",
            "request_id": request_id,
            "project_id": "proj-123",
        },
        {
            "timestamp": "2024-01-15 10:30:46,234",
            "level": "INFO",
            "logger": "app.tasks.seo_tasks",
            "message": "seo_data_fetch_started",
            "request_id": request_id,
            "task_id": "task-456",
        },
        {
            "timestamp": "2024-01-15 10:30:47,345",
            "level": "DEBUG",
            "logger": "app.core.http_client",
            "message": "external_api_call",
            "request_id": request_id,
            "method": "GET",
            "url": "https://api.ahrefs.com/v3/backlinks",
        },
        {
            "timestamp": "2024-01-15 10:30:52,456",
            "level": "INFO",
            "logger": "app.tasks.seo_tasks",
            "message": "seo_data_fetch_completed",
            "request_id": request_id,
            "project_id": "proj-123",
            "records": 42,
        },
    ]
    
    print(f"\nTracing request: {request_id}")
    print("=" * 70)
    
    for log in sample_logs:
        print(json.dumps(log, indent=2))
        print("-" * 70)


# ============================================================================
# Example 6: Error handling with request ID
# ============================================================================


@celery_app.task(bind=True, max_retries=3)
def risky_operation_task(self, data: str):
    """Task that demonstrates error handling with request ID."""
    logger = get_logger(__name__)
    request_id = get_request_id()
    
    try:
        logger.info("operation_started")
        
        # Simulate some processing
        result = process_data(data)
        
        logger.info("operation_completed", extra={"result_length": len(result)})
        return result
        
    except ValueError as e:
        # Log error with request ID for debugging
        logger.error(
            "operation_validation_error",
            extra={
                "error": str(e),
                "input": data[:100],  # First 100 chars
            }
        )
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
        
    except Exception as e:
        # Unexpected error - log with full context
        logger.error(
            "operation_unexpected_error",
            extra={
                "error_type": type(e).__name__,
                "error": str(e),
                "request_id": request_id,  # Redundant but explicit
            }
        )
        raise


def process_data(data: str) -> str:
    """Process data and potentially raise errors."""
    if not data:
        raise ValueError("Data cannot be empty")
    return data.upper()


if __name__ == "__main__":
    # Example of debugging a request
    debug_request_trace("550e8400-e29b-41d4-a716-446655440000")
