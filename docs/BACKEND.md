# Backend Developer Guide — AdTicks

This guide covers the backend code structure, architectural patterns, adding new endpoints, services, Celery tasks, and database models.

---

## Table of Contents

- [Technology Stack](#technology-stack)
- [Directory Layout](#directory-layout)
- [Application Entry Point](#application-entry-point)
- [Configuration & Environment](#configuration--environment)
- [Database Layer](#database-layer)
- [Authentication & Dependencies](#authentication--dependencies)
- [API Route Handlers](#api-route-handlers)
- [Services Layer](#services-layer)
- [Pydantic Schemas](#pydantic-schemas)
- [Celery Tasks](#celery-tasks)
- [Storage Service](#storage-service)
- [Adding a New Feature — Step-by-Step](#adding-a-new-feature--step-by-step)
- [Testing](#testing)
- [Linting & Formatting](#linting--formatting)
- [Logging](#logging)
- [Performance Notes](#performance-notes)

---

## Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.111+ | Web framework, async HTTP |
| Uvicorn | 0.30+ | ASGI server |
| SQLAlchemy | 2.0+ | ORM with async support |
| asyncpg | 0.29+ | Async PostgreSQL driver |
| Alembic | 1.13+ | Database migrations |
| Pydantic | 2.7+ | Request/response validation |
| Celery | 5.4+ | Distributed task queue |
| Redis | (via aioredis) | Celery broker + result backend |
| passlib[bcrypt] | 1.7+ | Password hashing |
| python-jose[cryptography] | 3.3+ | JWT creation/verification |
| boto3 | 1.34+ | DigitalOcean Spaces (S3 API) |
| openai | 1.35+ | OpenAI API client |
| anthropic | 0.28+ | Anthropic Claude client |

---

## Directory Layout

```
backend/
├── main.py                        # App factory, router mounting, middleware
├── requirements.txt               # All Python dependencies
├── Dockerfile
├── alembic.ini                    # Alembic configuration
├── alembic/
│   ├── env.py                     # Migration environment (imports all models)
│   └── versions/                  # Generated migration files
└── app/
    ├── api/                       # HTTP route handlers (thin — no business logic)
    │   ├── auth.py                #   /api/auth/*
    │   ├── projects.py            #   /api/projects/*
    │   ├── scores.py              #   /api/scores/*
    │   ├── seo.py                 #   /api/seo/*
    │   ├── ai.py                  #   /api/ai/*, /api/prompts/*, /api/scan/*
    │   ├── gsc.py                 #   /api/gsc/*
    │   ├── ads.py                 #   /api/ads/*
    │   └── insights.py            #   /api/insights/*
    ├── core/
    │   ├── config.py              # Pydantic Settings, all env vars
    │   ├── database.py            # Engine, session factory, get_db dependency
    │   ├── security.py            # JWT + bcrypt utilities
    │   ├── storage.py             # DigitalOcean Spaces wrapper
    │   ├── celery_app.py          # Celery instance
    │   └── dependencies.py        # FastAPI dependency functions
    ├── models/                    # SQLAlchemy declarative models
    │   ├── base.py                # Base class (uuid PK, timestamps)
    │   ├── user.py
    │   ├── project.py
    │   ├── keyword.py
    │   ├── gsc.py
    │   ├── ads.py
    │   ├── prompt.py
    │   ├── cluster.py
    │   ├── score.py
    │   └── recommendation.py
    ├── schemas/                   # Pydantic request/response schemas
    │   ├── auth.py
    │   ├── project.py
    │   ├── seo.py
    │   ├── ai.py
    │   ├── gsc.py
    │   ├── ads.py
    │   └── insights.py
    ├── services/                  # Business logic (pure, async functions)
    │   ├── seo/
    │   │   ├── seo_service.py
    │   │   ├── keyword_service.py
    │   │   ├── rank_tracker.py
    │   │   ├── on_page_analyzer.py
    │   │   ├── technical_seo.py
    │   │   └── content_gap_analyzer.py
    │   ├── ai/
    │   │   ├── ai_service.py
    │   │   ├── prompt_generator.py
    │   │   ├── llm_executor.py
    │   │   ├── mention_extractor.py
    │   │   └── scorer.py
    │   ├── gsc/
    │   │   └── gsc_service.py
    │   └── analytics/
    │       └── analytics_service.py
    ├── tasks/                     # Celery task definitions
    │   ├── seo_tasks.py
    │   └── ai_tasks.py
    └── workers/
        └── tasks.py               # Master orchestration task
```

---

## Application Entry Point

`backend/main.py` creates the FastAPI app and mounts all routers:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, projects, scores, seo, ai, gsc, ads, insights

app = FastAPI(title="AdTicks API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router mounting
app.include_router(auth.router,     prefix="/api/auth",     tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(scores.router,   prefix="/api/scores",   tags=["scores"])
app.include_router(seo.router,      prefix="/api/seo",      tags=["seo"])
app.include_router(ai.router,       prefix="/api",          tags=["ai"])
app.include_router(gsc.router,      prefix="/api/gsc",      tags=["gsc"])
app.include_router(ads.router,      prefix="/api/ads",      tags=["ads"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
```

---

## Configuration & Environment

`app/core/config.py` uses **Pydantic Settings** to load and validate all environment variables at startup:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

If a required variable is missing, the app fails to start with a clear validation error.

**Accessing settings anywhere:**

```python
from app.core.config import settings
print(settings.OPENAI_API_KEY)
```

---

## Database Layer

### Engine & session factory (`app/core/database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### Dependency injection (`get_db`)

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

Use in route handlers:

```python
@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await db.get(Project, project_id)
    ...
```

### ORM query patterns

```python
from sqlalchemy import select

# Fetch by ID
project = await db.get(Project, project_id)

# Filtered query
result = await db.execute(
    select(Project).where(Project.user_id == user.id)
)
projects = result.scalars().all()

# Create
new_project = Project(user_id=user.id, brand_name="AdTicks", domain="adticks.io")
db.add(new_project)
await db.flush()   # Gets the DB-assigned id
await db.commit()

# Update
project.brand_name = "New Name"
await db.commit()

# Delete
await db.delete(project)
await db.commit()
```

---

## Authentication & Dependencies

### Creating a JWT token (`app/core/security.py`)

```python
def create_access_token(subject: str, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

### Verifying a JWT token

```python
def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload["sub"]  # user ID
```

### Password hashing

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### `get_current_user` dependency

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(token)
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Could not validate credentials")
    return user
```

---

## API Route Handlers

Route handlers are **thin controllers** — they validate input, check auth, call services or dispatch tasks, and return responses. No business logic lives in route handlers.

**Pattern: synchronous route**

```python
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(403, "Forbidden")
    return project
```

**Pattern: async task dispatch**

```python
@router.post("/audit", status_code=202)
async def trigger_audit(
    body: AuditRequest,
    current_user: User = Depends(get_current_user),
):
    task = run_seo_audit_task.delay(body.project_id)
    return {"status": "queued", "task_id": task.id}
```

---

## Services Layer

Services contain all business logic. They are:
- Pure async Python functions (or classes)
- Independent of HTTP — no `Request`/`Response` objects
- Testable in isolation

**Calling a service from a route:**

```python
from app.services.seo import seo_service

result = await seo_service.run_full_seo_audit(project_id, domain, industry)
```

**Service function signature pattern:**

```python
# app/services/seo/seo_service.py
async def run_full_seo_audit(
    project_id: str,
    domain: str,
    industry: str,
) -> dict:
    """Orchestrates all SEO checks and returns a combined result dict."""
    keywords = await keyword_service.generate_keywords(domain, industry)
    rankings  = await rank_tracker.bulk_rank_check(keywords, domain)
    on_page   = await on_page_analyzer.analyze_url(f"https://{domain}")
    technical = await technical_seo.run_checks(domain)
    gaps      = await content_gap_analyzer.find_gaps(domain, competitors=[])

    overall = _compute_overall_health(technical, on_page, rankings)
    return {
        "project_id": project_id,
        "overall_health": overall,
        "keywords": keywords,
        "rankings": rankings,
        "on_page": on_page,
        "technical": technical,
        "gaps": gaps,
    }
```

---

## Pydantic Schemas

Schemas define what goes in and out of the API. They live in `app/schemas/`.

**Example: project schemas**

```python
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectCreate(BaseModel):
    brand_name: str
    domain: str
    industry: Optional[str] = None

class ProjectUpdate(BaseModel):
    brand_name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    brand_name: str
    domain: str
    industry: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2 ORM mode
```

The `model_config = {"from_attributes": True}` setting enables `ProjectResponse.model_validate(orm_object)`.

---

## Celery Tasks

Tasks are defined in `app/tasks/` and `app/workers/tasks.py`.

**Task boilerplate:**

```python
from app.core.celery_app import celery_app
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def my_new_task(self, project_id: str, extra_param: str):
    """Describe what this task does."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_my_new_task_impl(project_id, extra_param))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("my_new_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)

async def _my_new_task_impl(project_id: str, extra_param: str) -> dict:
    """Async implementation."""
    # All actual work here
    return {"status": "complete"}
```

**Dispatching a task from a route:**

```python
task = my_new_task.delay(project_id, extra_param="value")
return {"status": "queued", "task_id": task.id}
```

**Checking task status (optional):**

```python
from celery.result import AsyncResult
result = AsyncResult(task_id)
print(result.status)  # PENDING / STARTED / SUCCESS / FAILURE
```

**Adding to the master scan:**

If your task should run as part of the full scan, add it to the parallel group in `app/workers/tasks.py`:

```python
group(
    generate_keywords_task.s(project_id),
    run_rank_tracking_task.s(project_id),
    my_new_task.s(project_id),   # ← add here
    ...
)
```

---

## Storage Service

`app/core/storage.py` wraps DigitalOcean Spaces (S3-compatible API via boto3).

```python
from app.core.storage import storage_service

# Upload a JSON object
path = f"projects/{project_id}/seo/keywords_latest.json"
url  = await storage_service.upload_json(path, data_dict)

# Download a JSON object
data = await storage_service.download_json(path)

# Delete a file
await storage_service.delete_file(path)
```

Path conventions:
```
projects/{project_id}/seo/keywords_latest.json
projects/{project_id}/seo/rank_audit_latest.json
projects/{project_id}/ai/scan_latest.json
projects/{project_id}/ai/responses/{response_id}.json
projects/{project_id}/gsc/queries_latest.json
projects/{project_id}/ads/performance_latest.json
```

---

## Adding a New Feature — Step-by-Step

Example: adding a "Backlinks" feature.

### 1. Add the database model

```python
# app/models/backlink.py
from app.models.base import Base
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Backlink(Base):
    __tablename__ = "backlinks"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    source_url = Column(String(2048), nullable=False)
    target_url = Column(String(2048), nullable=False)
    domain_rating = Column(Float, nullable=True)
    date       = Column(Date, nullable=False, index=True)
```

Import it in `alembic/env.py` and `app/models/__init__.py`.

### 2. Create a migration

```bash
make migration msg="add backlinks table"
make migrate
```

### 3. Add Pydantic schemas

```python
# app/schemas/backlinks.py
class BacklinkResponse(BaseModel):
    id: UUID
    project_id: UUID
    source_url: str
    target_url: str
    domain_rating: Optional[float]
    date: date
    model_config = {"from_attributes": True}
```

### 4. Create a service

```python
# app/services/backlinks/backlink_service.py
async def fetch_backlinks(project_id: str, domain: str) -> list[dict]:
    # Call your data source (e.g., Ahrefs API, mock data)
    return [{"source_url": "...", "target_url": "...", ...}]
```

### 5. Create a Celery task

```python
# app/tasks/backlink_tasks.py
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_backlinks_task(self, project_id: str):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_sync(project_id))
        loop.close()
    except Exception as exc:
        raise self.retry(exc=exc)
```

### 6. Create route handlers

```python
# app/api/backlinks.py
router = APIRouter()

@router.get("/{project_id}", response_model=list[BacklinkResponse])
async def get_backlinks(project_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Backlink).where(Backlink.project_id == project_id))
    return result.scalars().all()

@router.post("/sync/{project_id}", status_code=202)
async def sync_backlinks(project_id: str, user=Depends(get_current_user)):
    task = sync_backlinks_task.delay(project_id)
    return {"status": "queued", "task_id": task.id}
```

### 7. Mount the router in `main.py`

```python
from app.api import backlinks
app.include_router(backlinks.router, prefix="/api/backlinks", tags=["backlinks"])
```

### 8. Write tests

```python
# tests/test_backlinks.py
def test_get_backlinks_empty(client, auth_headers, project):
    resp = client.get(f"/api/backlinks/{project.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
```

---

## Testing

Tests live in `backend/tests/`.

```bash
# Run all tests
make test

# Run a specific test file
docker-compose exec backend pytest tests/test_auth.py -v

# Run with coverage
make test-cov
```

**Test structure:**

```
tests/
├── conftest.py          # Fixtures: test DB, test client, auth headers
├── test_auth.py         # Registration + login tests
├── test_projects.py     # Project CRUD tests
├── test_seo.py          # SEO endpoint tests
└── test_insights.py     # Insights tests
```

**Key fixtures (`conftest.py`):**

```python
@pytest.fixture
def client():
    """Sync TestClient wrapping the FastAPI app."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers(client):
    """Register + login, return Authorization headers."""
    client.post("/api/auth/register", json={...})
    resp = client.post("/api/auth/login", json={...})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## Linting & Formatting

```bash
# Check for issues
make lint

# Auto-fix formatting
make format
```

Both use **Ruff** (configured in `pyproject.toml` or `ruff.toml`). Ruff covers isort, flake8, pyupgrade, and more.

---

## Logging

Use Python's standard `logging` module:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("[%s] Starting SEO audit", project_id)
logger.warning("[%s] No keywords found", project_id)
logger.error("[%s] Service failed: %s", project_id, exc)
```

Log format includes timestamp, level, module, and message. In production, logs are shipped to DigitalOcean Monitoring or a log aggregator.

---

## Performance Notes

- **Never run async code directly in Celery tasks** — Celery workers don't have a running event loop. Always create a new `asyncio.new_event_loop()` in each task.
- **Use `await db.flush()`** after adding new objects if you need the DB-assigned ID before the transaction commits.
- **Avoid N+1 queries** — use `selectinload` or `joinedload` for relationships:

```python
from sqlalchemy.orm import selectinload
result = await db.execute(
    select(Project)
    .options(selectinload(Project.keywords))
    .where(Project.user_id == user.id)
)
```

- **Use `index=True`** on any column used in `.where()` clauses in hot paths.
- **Batch inserts** for large data sets (GSC sync can have thousands of rows):

```python
db.add_all([GSCData(**row) for row in data_rows])
await db.commit()
```
