"""
AdTicks — Celery application factory.

The Celery app uses Redis as both the message broker and result backend.
Configured with retry logic, error handling, monitoring support, and request ID propagation.

Import `celery_app` wherever you need to define or call tasks.
"""

from celery import Celery, signals
from celery.schedules import crontab

from app.core.config import settings
from app.core.logging import get_request_id, set_request_id_for_task

celery_app = Celery(
    "adticks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.seo_tasks",
        "app.tasks.ai_tasks",
        "app.workers.tasks",
    ],
)

# ---------------------------------------------------------------------------
# Task Configuration
# ---------------------------------------------------------------------------
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task Tracking & Results
    task_track_started=True,
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker Configuration
    worker_prefetch_multiplier=1,  # Don't pre-fetch tasks
    task_acks_late=True,  # Acknowledge only after task completes
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    
    # Task Timeouts
    task_soft_time_limit=30 * 60,  # 30 minutes soft timeout (raise exception)
    task_time_limit=45 * 60,  # 45 minutes hard timeout (kill task)
    
    # Retry Configuration
    task_max_retries=3,  # Maximum retry attempts
    task_default_retry_delay=60,  # Retry after 60 seconds
    
    # Error Handling
    task_ignore_result=False,
    task_store_eager_result=True,
)

# ---------------------------------------------------------------------------
# Beat Schedule (Celery Beat Scheduler)
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    "daily-scans": {
        "task": "app.workers.tasks.schedule_daily_scans_task",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
}


# ---------------------------------------------------------------------------
# Request ID Propagation to Tasks
# ---------------------------------------------------------------------------
@signals.before_task_publish.connect
def before_task_publish_handler(sender=None, body=None, **kwargs):
    """Capture request ID before task is published to queue.
    
    Stores the current request ID in task headers so it can be
    retrieved and restored in the task context.
    """
    request_id = get_request_id()
    if request_id:
        headers = kwargs.get("headers") or {}
        headers["x_request_id"] = request_id
        kwargs["headers"] = headers


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Restore request ID in task execution context.
    
    Called before task execution to set up the request ID
    from task headers.
    """
    request_id = task.request.headers.get("x_request_id")
    if request_id:
        set_request_id_for_task(request_id)


# ---------------------------------------------------------------------------
# Request ID Propagation for Task.apply_async Calls
# ---------------------------------------------------------------------------
def apply_async_with_request_id(task, *args, **kwargs):
    """Helper to apply a Celery task with automatic request ID propagation.
    
    Use this instead of task.apply_async() or task.delay() to ensure
    the current request ID is passed to the task.
    
    Example:
        apply_async_with_request_id(my_task, arg1, arg2, kwarg1=value)
    """
    request_id = get_request_id()
    headers = kwargs.get("headers") or {}
    if request_id:
        headers["x_request_id"] = request_id
    kwargs["headers"] = headers
    return task.apply_async(*args, **kwargs)

