# AdTicks — Visibility Intelligence Platform

> **Track your brand's presence across SEO, AI-generated content, Google Search Console, and Google Ads — unified into a single intelligence hub.**

AdTicks is a full-stack SaaS platform that combines a FastAPI backend, Next.js 14 frontend, Celery async task queue, and AI-powered insights engine to give brands real-time visibility intelligence.

---

## Table of Contents

- [What AdTicks Does](#what-adticks-does)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Service URLs](#service-urls)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Running Services](#running-services)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Makefile Reference](#makefile-reference)
- [Detailed Documentation](#detailed-documentation)

---

## What AdTicks Does

AdTicks monitors four channels of brand visibility and surfaces AI-generated recommendations:

| Channel | What it tracks |
|---------|----------------|
| **SEO Hub** | Keyword rankings, on-page scores, content gaps, technical health checks |
| **AI Visibility** | Brand mentions in ChatGPT, Gemini, Claude, and Perplexity responses |
| **Search Console** | Impressions, clicks, CTR, and position data from Google Search Console |
| **Google Ads** | Campaign performance, spend, ROAS, CPC, and conversion data |
| **Insights Engine** | Cross-channel AI recommendations prioritised P1 → P3 |

The **Unified Visibility Score** (0–100) combines all four channels into a single metric updated on every scan.

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Docker | 24+ | Runs all services |
| Docker Compose | 2.20+ | Orchestrates multi-container setup |
| Node.js | 20+ | Local frontend development only |
| Python | 3.11+ | Local backend development only |
| Git | Any | Version control & deployment tagging |
| Make | Any | Convenience command runner |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/adticks.git
cd adticks

# 2. Run the automated setup script
./scripts/setup.sh
```

The `setup.sh` script handles:
1. Copying `.env.example` → `.env` and `frontend/.env.local.example` → `frontend/.env.local`
2. Starting PostgreSQL and Redis
3. Running all Alembic database migrations
4. Starting the full service stack

**First user registration** is done through the UI at `http://localhost:3002/register` or via the API:

```bash
curl -X POST http://localhost:8002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"SecurePass123!","full_name":"Your Name"}'
```

---

## Service URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend** | http://localhost:3002 | Next.js dashboard |
| **Backend API** | http://localhost:8002 | FastAPI server |
| **Swagger UI** | http://localhost:8002/docs | Interactive API explorer |
| **ReDoc** | http://localhost:8002/redoc | Clean API reference |
| **OpenAPI JSON** | http://localhost:8002/openapi.json | Machine-readable schema |
| **Celery Flower** | http://localhost:5555 | Task queue monitor |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Browser / Client                            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ HTTPS
                    ┌──────────▼────────────┐
                    │   Nginx (prod only)    │  ← SSL termination, gzip
                    │      port 80/443       │
                    └───┬───────────────┬───┘
                        │ /api/*        │ /*
               ┌────────▼────────┐  ┌───▼────────────┐
               │  FastAPI (8002) │  │  Next.js (3002) │
               │  + Uvicorn      │  │  App Router     │
               └────────┬────────┘  └────────────────┘
                        │
         ┌──────────────┼──────────────────┐
         │              │                  │
┌────────▼──────┐ ┌─────▼──────┐ ┌────────▼────────────┐
│  PostgreSQL   │ │   Redis    │ │   Celery Worker     │
│    (5432)     │ │  (6379)    │ │   + Beat Scheduler  │
│  Primary DB   │ │  Cache +   │ │   4 concurrent      │
│  SQLAlchemy   │ │  Broker    │ │   workers           │
└───────────────┘ └────────────┘ └────────┬────────────┘
                                          │
                               ┌──────────▼──────────┐
                               │  DigitalOcean Spaces │
                               │  (S3-compatible)     │
                               │  JSON result store   │
                               └─────────────────────┘

External APIs called by Celery workers:
  ├── OpenAI (GPT-4)         — AI prompt execution
  ├── Anthropic (Claude)     — AI prompt execution
  ├── Google Search Console  — Impression/click data
  └── Google Ads API         — Campaign performance
```

**Key design decisions:**
- All heavy I/O (LLM calls, third-party syncs) happens in **Celery tasks**, never in HTTP request handlers
- API routes return `{status: "queued", task_id}` immediately for async operations
- Results are stored in **DigitalOcean Spaces** to keep the database lean
- React Query on the frontend polls or invalidates after task completion

---

## Project Structure

```
adticks/
├── backend/
│   ├── main.py                     # FastAPI app entry, router mounting, CORS
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Python 3.11-slim image
│   ├── alembic/                    # Database migration scripts
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── api/                    # HTTP route handlers (thin controllers)
│       │   ├── auth.py             #   POST /register, /login, GET /me
│       │   ├── projects.py         #   CRUD /projects
│       │   ├── scores.py           #   GET /scores/{project_id}
│       │   ├── seo.py              #   Keywords, rankings, audit endpoints
│       │   ├── ai.py               #   AI prompt & scan endpoints
│       │   ├── gsc.py              #   Google Search Console endpoints
│       │   ├── ads.py              #   Google Ads endpoints
│       │   └── insights.py         #   Recommendations endpoints
│       ├── core/                   # Cross-cutting concerns
│       │   ├── config.py           #   Pydantic Settings (env vars)
│       │   ├── database.py         #   Async SQLAlchemy engine + session
│       │   ├── security.py         #   JWT creation/verification, bcrypt
│       │   ├── storage.py          #   DigitalOcean Spaces/S3 wrapper
│       │   ├── celery_app.py       #   Celery instance + config
│       │   └── dependencies.py     #   FastAPI dependency injection helpers
│       ├── models/                 # SQLAlchemy ORM models (database tables)
│       │   ├── user.py             #   users table
│       │   ├── project.py          #   projects table
│       │   ├── keyword.py          #   keywords + rankings tables
│       │   ├── gsc.py              #   gsc_data table
│       │   ├── ads.py              #   ads_data table
│       │   ├── prompt.py           #   prompts + responses + mentions tables
│       │   ├── cluster.py          #   clusters table
│       │   ├── score.py            #   scores table
│       │   └── recommendation.py   #   recommendations table
│       ├── schemas/                # Pydantic request/response schemas
│       │   ├── auth.py
│       │   ├── project.py
│       │   ├── seo.py
│       │   ├── ai.py
│       │   ├── gsc.py
│       │   ├── ads.py
│       │   └── insights.py
│       ├── services/               # Business logic (pure functions, no HTTP)
│       │   ├── seo/
│       │   │   ├── seo_service.py          # Orchestrator
│       │   │   ├── keyword_service.py      # Keyword discovery & clustering
│       │   │   ├── rank_tracker.py         # SERP rank checking
│       │   │   ├── on_page_analyzer.py     # Page audit
│       │   │   ├── technical_seo.py        # Technical checks
│       │   │   └── content_gap_analyzer.py # Content gap analysis
│       │   ├── ai/
│       │   │   ├── ai_service.py           # AI scan orchestrator
│       │   │   ├── prompt_generator.py     # Context-aware prompt generation
│       │   │   ├── llm_executor.py         # Multi-LLM execution
│       │   │   ├── mention_extractor.py    # Brand mention extraction
│       │   │   └── scorer.py              # Visibility score computation
│       │   ├── gsc/
│       │   │   └── gsc_service.py          # GSC OAuth + data fetch
│       │   └── analytics/
│       │       └── analytics_service.py    # Overview + funnel metrics
│       ├── tasks/                  # Celery task definitions
│       │   ├── seo_tasks.py        #   SEO-related async tasks
│       │   └── ai_tasks.py         #   AI scan async tasks
│       └── workers/
│           └── tasks.py            #   Master orchestration task (full scan)
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── jest.config.ts
│   ├── Dockerfile                  # Multi-stage Node 20 → Alpine
│   ├── app/
│   │   ├── layout.tsx              # Root layout (QueryProvider, dark mode)
│   │   ├── globals.css             # Tailwind directives + design tokens
│   │   ├── (auth)/
│   │   │   ├── layout.tsx
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx
│   │       ├── page.tsx            # Overview dashboard
│   │       ├── seo/page.tsx
│   │       ├── ai-visibility/page.tsx
│   │       ├── gsc/page.tsx
│   │       ├── ads/page.tsx
│   │       ├── insights/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── layout/                 # Sidebar, Header, DashboardLayout
│   │   ├── ui/                     # Design-system primitives (Button, Card, etc.)
│   │   ├── dashboard/              # Overview widgets
│   │   ├── seo/                    # SEO-specific components
│   │   ├── ai/                     # AI Visibility components
│   │   ├── gsc/                    # GSC components
│   │   ├── ads/                    # Ads components
│   │   ├── charts/                 # Recharts wrappers
│   │   └── providers/              # QueryProvider
│   ├── hooks/                      # React Query data hooks
│   ├── lib/
│   │   ├── types.ts                # TypeScript interfaces
│   │   ├── api.ts                  # Axios client + endpoint map
│   │   ├── auth.ts                 # JWT localStorage management
│   │   ├── utils.ts                # Formatting helpers
│   │   └── mockData.ts             # Offline / demo fallback data
│   └── __tests__/                  # Jest test suite
│
├── nginx/
│   └── nginx.conf                  # Reverse proxy (prod)
├── scripts/
│   ├── setup.sh                    # First-time dev environment setup
│   └── deploy.sh                   # Production deployment script
├── docker-compose.yml              # Development stack
├── docker-compose.prod.yml         # Production stack
├── Makefile                        # Developer convenience commands
├── .env.example                    # Backend env template
└── docs/                           # Detailed documentation (see below)
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── BACKEND.md
    ├── FRONTEND.md
    ├── DATABASE.md
    ├── DEPLOYMENT.md
    └── CONTRIBUTING.md
```

---

## Environment Variables

### Backend — `.env`

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | Async SQLAlchemy connection string | `postgresql+asyncpg://adticks:pass@postgres:5432/adticks` |
| `POSTGRES_USER` | ✅ | Postgres username (used by Docker) | `adticks` |
| `POSTGRES_PASSWORD` | ✅ | Postgres password | `changeme` |
| `POSTGRES_DB` | ✅ | Database name | `adticks` |
| `REDIS_URL` | ✅ | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | ✅ | JWT signing key — **must be 64+ random chars in prod** | `openssl rand -hex 32` |
| `ALGORITHM` | ✅ | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ | JWT access token lifetime | `30` |
| `DO_SPACES_KEY` | ✅ | DigitalOcean Spaces access key | — |
| `DO_SPACES_SECRET` | ✅ | DigitalOcean Spaces secret | — |
| `DO_SPACES_ENDPOINT` | ✅ | Spaces endpoint URL | `https://nyc3.digitaloceanspaces.com` |
| `DO_SPACES_BUCKET` | ✅ | Bucket name | `adticks-data` |
| `DO_SPACES_REGION` | ✅ | Spaces region | `nyc3` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM calls | `sk-...` |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic (Claude) API key | `sk-ant-...` |
| `GOOGLE_CLIENT_ID` | ⚠️ | Google OAuth client ID (GSC & Ads) | — |
| `GOOGLE_CLIENT_SECRET` | ⚠️ | Google OAuth client secret | — |
| `GOOGLE_REDIRECT_URI` | ⚠️ | OAuth callback URL | `http://localhost:8002/api/gsc/callback` |
| `ENVIRONMENT` | ✅ | Runtime environment | `development` or `production` |

> ⚠️ = Required only if Google integrations (GSC / Ads) are enabled.

### Frontend — `frontend/.env.local`

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API base URL (no trailing slash) | `http://localhost:8002/api` |
| `NEXTAUTH_SECRET` | ✅ | NextAuth.js signing secret | `openssl rand -hex 32` |
| `NEXTAUTH_URL` | ✅ | Canonical frontend URL | `http://localhost:3002` |

---

## Running Services

```bash
# Start the full stack
docker-compose up -d

# Start only infrastructure (DB + Redis)
docker-compose up -d postgres redis

# Start a specific service
docker-compose up -d backend

# View live logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Restart a service after code change
docker-compose restart backend

# Stop everything (preserves volumes)
docker-compose down

# Stop and wipe all data (destructive!)
docker-compose down -v
```

---

## Database Migrations

Alembic handles all schema changes. **Never edit the database schema manually.**

```bash
# Apply all pending migrations
make migrate

# Generate a new migration from model changes
make migration msg="add campaigns table"

# Roll back the last applied migration
make downgrade

# Show migration history
docker-compose exec backend alembic history

# Show current migration state
docker-compose exec backend alembic current
```

---

## Testing

```bash
# Backend — pytest
make test

# Backend — with HTML coverage report
make test-cov
# Opens: backend/htmlcov/index.html

# Frontend — Jest
cd frontend && npm test

# Frontend — watch mode
cd frontend && npm run test:watch

# Frontend — coverage
cd frontend && npm run test:coverage
```

---

## API Documentation

Interactive API docs are auto-generated by FastAPI:

- **Swagger UI** — http://localhost:8002/docs (full interactive testing)
- **ReDoc** — http://localhost:8002/redoc (clean, readable reference)
- **OpenAPI JSON** — http://localhost:8002/openapi.json

See [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) for the complete annotated endpoint reference including request/response schemas and example `curl` commands.

---

## Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full guide. Quick summary:

```bash
# Set your DigitalOcean droplet IP and access token
export DEPLOY_HOST=your.droplet.ip
export DO_ACCESS_TOKEN=your_do_token

# Run the deployment script
./scripts/deploy.sh
```

The script builds images, tags with git SHA, pushes to DigitalOcean Container Registry, SSHs to the droplet, runs migrations, and performs a rolling restart.

---

## Makefile Reference

```bash
make up                        # Start all Docker services
make down                      # Stop all Docker services
make logs                      # Tail all service logs
make migrate                   # Apply pending Alembic migrations
make migration msg="describe"  # Create a new Alembic migration
make downgrade                 # Roll back one migration
make test                      # Run pytest (backend)
make test-cov                  # Run pytest with coverage report
make lint                      # Run Ruff linter
make format                    # Auto-format with Ruff
make status                    # Show running container status
```

---

## Detailed Documentation

| Document | Contents |
|----------|----------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, service interactions, async task pipeline, data flow |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Full schema reference, ER diagram, all tables and relationships |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Every endpoint — method, path, auth, request body, response, errors |
| [`docs/BACKEND.md`](docs/BACKEND.md) | Backend code structure, patterns, adding endpoints/services/models |
| [`docs/FRONTEND.md`](docs/FRONTEND.md) | Frontend structure, pages, components, hooks, design system |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Docker, CI/CD, DigitalOcean, SSL, environment management, rollback |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Git workflow, coding standards, PR process, testing requirements |

---

*AdTicks is built with ❤️ using FastAPI, Next.js, PostgreSQL, Redis, Celery, and OpenAI.*
