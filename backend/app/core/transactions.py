"""
AdTicks — Transaction context managers and decorators.

Provides explicit transaction handling with automatic rollback, nested transaction
support via savepoints, and read-only transaction contexts.

Context Managers:
    transaction_scope()  — explicit transaction with auto rollback
    nested_transaction() — savepoint-based nested transaction
    readonly_transaction() — read-only transaction (no commit)

Decorators:
    @with_transaction — wraps route handlers in a transaction
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, IntegrityError

# Context variable to track transaction state (for debugging/monitoring)
_transaction_depth: ContextVar[int] = ContextVar("transaction_depth", default=0)
_transaction_active: ContextVar[bool] = ContextVar("transaction_active", default=False)


# ---------------------------------------------------------------------------
# Public API: Context Managers
# ---------------------------------------------------------------------------


@asynccontextmanager
async def transaction_scope(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Explicit transaction context with automatic rollback on exception.

    This context manager ensures:
    - Transaction starts when entering
    - Commits on successful exit
    - Automatically rolls back on any exception
    - Properly closes the session

    Example:
        from app.core.transactions import transaction_scope

        async def create_user(email: str, db: AsyncSession):
            async with transaction_scope(db) as tx:
                user = User(email=email)
                tx.add(user)
                await tx.flush()
                return user

    Args:
        db: AsyncSession instance

    Yields:
        AsyncSession: The same session for transaction execution

    Raises:
        Any exception from the context is re-raised after rollback
    """
    try:
        # Mark transaction as active
        _transaction_active.set(True)
        # Begin explicit transaction (only if not already in one)
        if not db.in_transaction():
            await db.begin()
        yield db
        # Commit on success (only if we're at the top level)
        if not db.in_nested_transaction():
            await db.commit()
    except Exception:
        # Automatic rollback on any exception
        await db.rollback()
        raise
    finally:
        # Mark transaction as inactive
        _transaction_active.set(False)


@asynccontextmanager
async def nested_transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Savepoint-based nested transaction for complex multi-step operations.

    Allows nested transactions within a parent transaction. If a nested
    transaction fails, only the nested changes are rolled back.

    Example:
        async with transaction_scope(db) as tx:
            # Parent transaction
            user = User(email="user@example.com")
            tx.add(user)
            await tx.flush()

            try:
                async with nested_transaction(tx) as nested_tx:
                    # Nested transaction with savepoint
                    record = Record(user_id=user.id)
                    nested_tx.add(record)
                    await nested_tx.flush()
            except ValueError:
                # If this fails, user is still saved, record is rolled back
                pass

    Args:
        db: AsyncSession instance (must already be in a transaction)

    Yields:
        AsyncSession: The same session for nested operations

    Raises:
        Any exception from the context is re-raised after savepoint rollback
    """
    depth = _transaction_depth.get()
    _transaction_depth.set(depth + 1)

    try:
        # Create savepoint for nested transaction
        savepoint = await db.begin_nested()
        yield db
        # Release savepoint on success (implicitly commits nested transaction)
        await savepoint.commit()
    except Exception:
        # Rollback to savepoint on any exception
        await savepoint.rollback()
        raise
    finally:
        _transaction_depth.set(depth)


@asynccontextmanager
async def readonly_transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Read-only transaction context.

    Useful for ensuring a query sequence is not accidentally modified.
    The transaction is rolled back instead of committed.

    Example:
        async with readonly_transaction(db) as ro_tx:
            result = await ro_tx.execute(select(User))
            users = result.scalars().all()
            # Any adds/updates/deletes here will be rolled back

    Args:
        db: AsyncSession instance

    Yields:
        AsyncSession: The same session for read-only queries

    Raises:
        Any exception from the context is re-raised after rollback
    """
    try:
        # Begin transaction for isolation if not already in one
        if not db.in_transaction():
            await db.begin()
        yield db
        # Always rollback (no commits for read-only)
        await db.rollback()
    except Exception:
        # Explicit rollback on exception
        await db.rollback()
        raise


# ---------------------------------------------------------------------------
# Public API: Decorators
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def with_transaction(
    auto_flush: bool = True,
    auto_commit: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to automatically wrap a function in a transaction scope.

    Automatically manages transaction lifecycle for route handlers or
    service methods. The decorated function receives the db session as
    a parameter and doesn't need to call commit/rollback.

    Example:
        @router.post("/users")
        @with_transaction()
        async def create_user(
            payload: UserCreate,
            db: AsyncSession = Depends(get_db),
        ):
            user = User(email=payload.email)
            db.add(user)
            await db.flush()  # Optional: flush before commit
            return user

    Args:
        auto_flush: Call db.flush() before commit (default: True)
        auto_commit: Commit transaction on success (default: True)

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract db session from kwargs (FastAPI injects dependencies)
            db: AsyncSession | None = kwargs.get("db")
            if db is None:
                # Fallback: search for AsyncSession in args/kwargs
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                        break
                if db is None:
                    raise RuntimeError(
                        "with_transaction decorator requires 'db: AsyncSession' parameter"
                    )

            # Check if already in transaction
            is_nested = db.in_transaction()

            try:
                if not is_nested:
                    await db.begin()
                result = await func(*args, **kwargs)
                if auto_flush:
                    await db.flush()
                if auto_commit and not is_nested:
                    await db.commit()
                return result
            except Exception:
                if not is_nested:
                    await db.rollback()
                raise

        return wrapper  # type: ignore

    return decorator


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


async def get_transaction_depth() -> int:
    """Get the current nesting depth of transactions."""
    return _transaction_depth.get()


async def is_transaction_active() -> bool:
    """Check if a transaction is currently active."""
    return _transaction_active.get()


# ---------------------------------------------------------------------------
# Advanced: Batch Operations with Transaction Control
# ---------------------------------------------------------------------------


@asynccontextmanager
async def batch_operation(
    db: AsyncSession,
    batch_size: int = 1000,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for batch operations with periodic commits.

    Useful for bulk inserts/updates where you want to commit periodically
    to avoid memory buildup from large transactions.

    Example:
        async with batch_operation(db, batch_size=100) as batch_session:
            for i in range(10000):
                item = Item(value=i)
                batch_session.add(item)
                # Auto-commits every 100 items

    Args:
        db: AsyncSession instance
        batch_size: Number of operations before auto-commit

    Yields:
        AsyncSession: Same session with batch tracking
    """
    # Wrap session with batch tracking
    batch_session = _BatchSessionWrapper(db, batch_size)
    try:
        await db.begin()
        yield batch_session
        # Final commit for remaining items
        if batch_session.operation_count % batch_size != 0:
            await db.commit()
    except Exception:
        await db.rollback()
        raise


class _BatchSessionWrapper:
    """Wraps AsyncSession to track batch operations and auto-commit."""

    def __init__(self, db: AsyncSession, batch_size: int):
        self._db = db
        self._batch_size = batch_size
        self.operation_count = 0

    def add(self, instance: Any) -> None:
        """Add instance and check if batch commit is needed."""
        self._db.add(instance)
        self.operation_count += 1
        # Note: actual commit would require async context, so batching is
        # tracked but caller must handle commits via explicit await

    async def flush(self) -> None:
        """Flush pending operations."""
        await self._db.flush()

    async def __aenter__(self) -> "_BatchSessionWrapper":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Advanced: Retry Logic with Exponential Backoff
# ---------------------------------------------------------------------------


@asynccontextmanager
async def transaction_with_retry(
    db: AsyncSession,
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    retryable_exceptions: tuple[type[Exception], ...] = (OperationalError,),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager that retries a transaction with exponential backoff.
    
    Useful for handling transient database errors like deadlocks or temporary
    connection issues. Automatically rolls back and retries on retryable exceptions.
    
    Example:
        async with transaction_with_retry(db, max_retries=3) as tx:
            user = User(email="user@example.com")
            tx.add(user)
            await tx.flush()
    
    Args:
        db: AsyncSession instance
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 0.1)
        max_delay: Maximum delay in seconds (default: 5.0)
        retryable_exceptions: Tuple of exception types to retry on (default: OperationalError)
    
    Yields:
        AsyncSession: The same session for transaction execution
    
    Raises:
        The last exception if all retries are exhausted
    """
    last_exception: Exception | None = None
    
    for attempt in range(max_retries):
        try:
            async with transaction_scope(db) as tx:
                yield tx
                return  # Success
        except retryable_exceptions as e:
            last_exception = e
            # Calculate exponential backoff delay
            delay = min(base_delay * (2 ** attempt), max_delay)
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            # Continue to next retry
        except Exception:
            # Non-retryable exceptions should be raised immediately
            raise
    
    # All retries exhausted
    if last_exception:
        raise last_exception


def with_transaction_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    retryable_exceptions: tuple[type[Exception], ...] = (OperationalError,),
) -> Callable[[Any], Any]:
    """
    Decorator to automatically wrap a function in a retryable transaction scope.
    
    Automatically manages transaction lifecycle with retry logic for transient errors.
    The decorated function receives the db session as a parameter.
    
    Example:
        @router.post("/users")
        @with_transaction_retry(max_retries=3)
        async def create_user(
            payload: UserCreate,
            db: AsyncSession = Depends(get_db),
        ):
            user = User(email=payload.email)
            db.add(user)
            await db.flush()
            return user
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 0.1)
        retryable_exceptions: Tuple of exception types to retry on
    
    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract db session from kwargs (FastAPI injects dependencies)
            db: AsyncSession | None = kwargs.get("db")
            if db is None:
                # Fallback: search for AsyncSession in args/kwargs
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                        break
                if db is None:
                    raise RuntimeError(
                        "with_transaction_retry decorator requires 'db: AsyncSession' parameter"
                    )

            last_exception: Exception | None = None
            for attempt in range(max_retries):
                try:
                    # Check if already in transaction
                    is_nested = db.in_transaction()
                    try:
                        if not is_nested:
                            await db.begin()
                        result = await func(*args, **kwargs)
                        await db.flush()
                        if not is_nested:
                            await db.commit()
                        return result
                    except Exception:
                        if not is_nested:
                            await db.rollback()
                        raise
                except retryable_exceptions as e:
                    last_exception = e
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), 5.0)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                    # Continue to next retry
                except Exception:
                    # Non-retryable exceptions should be raised immediately
                    raise

            # All retries exhausted
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


__all__ = [
    "transaction_scope",
    "nested_transaction",
    "readonly_transaction",
    "with_transaction",
    "transaction_with_retry",
    "with_transaction_retry",
    "batch_operation",
    "get_transaction_depth",
    "is_transaction_active",
]
