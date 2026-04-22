"""
AdTicks — Async SQLAlchemy database setup.

Provides:
- async engine backed by asyncpg with connection pooling
- AsyncSessionLocal session factory
- Base declarative class for all models
- get_db FastAPI dependency with transaction management
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine with Connection Pooling
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    # Connection pooling
    pool_size=20,  # Keep 20 connections in the pool
    max_overflow=10,  # Allow up to 10 additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connection is alive before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_use_lifo=True,  # LIFO strategy for connection reuse (faster)
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Explicit flush required
    autocommit=False,  # Explicit commit required
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency with transaction management
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session and handle transaction lifecycle.
    
    - Rolls back on exception
    - Commits on success
    - Properly closes connection
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit successful transactions
            await session.commit()
        except Exception:
            # Rollback on any exception
            await session.rollback()
            raise
        finally:
            # Always close the session
            await session.close()

