import asyncio
import logging

logger = logging.getLogger(__name__)

# Maintain a single persistent event loop per worker process
_worker_loop = None

def get_or_create_loop():
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop

def run_async(coro):
    """
    Run an async coroutine using the worker's persistent event loop.
    This prevents SQLAlchemy 'attached to a different loop' connection errors.
    """
    loop = get_or_create_loop()
    return loop.run_until_complete(coro)
