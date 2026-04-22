"""Shared pytest fixtures for AdTicks tests.

Uses an in-memory SQLite database (via aiosqlite) so tests run fully offline
without a real PostgreSQL instance.  PostgreSQL-dialect UUID columns are
remapped to String at the engine level via SQLAlchemy's type affinity for
SQLite.
"""
import uuid
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.project import Project
from app.models.user import User
from main import app

# ---------------------------------------------------------------------------
# Test DB URL — in-memory SQLite with aiosqlite
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Engine — created once per session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create an async SQLite engine and build the schema once."""
    _engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with _engine.begin() as conn:
        # SQLite does not understand postgresql.UUID — use native_uuid=False
        # so UUID columns are stored as VARCHAR.
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


# ---------------------------------------------------------------------------
# DB session — fresh per test (rollback after each)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async DB session and clear persisted rows per test."""
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
        yield session
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()


# ---------------------------------------------------------------------------
# HTTP client — overrides get_db with the test session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an AsyncClient backed by FastAPI with the test DB wired in."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and persist a standard test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@adticks.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Return Authorization headers containing a valid JWT for test_user."""
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create and persist a project owned by test_user."""
    project = Project(
        id=uuid.uuid4(),
        user_id=test_user.id,
        brand_name="Optivio",
        domain="optivio.com",
        industry="SaaS",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    """Create a second user that should not be able to access test_user's data."""
    user = User(
        id=uuid.uuid4(),
        email="other@adticks.com",
        hashed_password=hash_password("otherpassword123"),
        full_name="Other User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_auth_headers(second_user: User) -> dict:
    """Return Authorization headers for second_user."""
    token = create_access_token(subject=second_user.id)
    return {"Authorization": f"Bearer {token}"}


# AEO Module Fixtures
@pytest_asyncio.fixture
async def keyword(db_session: AsyncSession, test_project: Project):
    """Create a test keyword."""
    from app.models.keyword import Keyword
    
    keyword = Keyword(
        id=uuid.uuid4(),
        project_id=test_project.id,
        keyword="test keyword",
        intent="informational",
        difficulty=45.0,
        volume=1200,
    )
    db_session.add(keyword)
    await db_session.commit()
    await db_session.refresh(keyword)
    return keyword


@pytest_asyncio.fixture
async def db(db_session: AsyncSession):
    """Alias for db_session."""
    return db_session


@pytest_asyncio.fixture
async def project(test_project: Project):
    """Alias for test_project."""
    return test_project


@pytest_asyncio.fixture
async def user(test_user: User):
    """Alias for test_user."""
    return test_user


@pytest_asyncio.fixture
async def user_token(auth_headers: dict) -> str:
    """Extract token from auth headers."""
    return auth_headers["Authorization"].replace("Bearer ", "")


@pytest_asyncio.fixture
async def other_user_token(second_auth_headers: dict) -> str:
    """Extract token from second user's auth headers."""
    return second_auth_headers["Authorization"].replace("Bearer ", "")


# GEO Module Fixtures
@pytest_asyncio.fixture
async def test_location(db_session: AsyncSession, test_project: Project):
    """Create a test location."""
    from app.models.geo import Location

    location = Location(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="Test Location",
        address="123 Main Street",
        city="New York",
        state="NY",
        country="USA",
        postal_code="10001",
        phone="+1-555-0123",
        latitude=40.7128,
        longitude=-74.0060,
    )
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    return location
