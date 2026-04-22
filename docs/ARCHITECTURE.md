# Architecture — AdTicks Visibility Intelligence Platform

This document describes the system architecture, service interactions, request lifecycle, async task pipeline, data storage strategy, and security model of AdTicks.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Service Responsibilities](#service-responsibilities)
- [HTTP Request Lifecycle](#http-request-lifecycle)
- [Async Task Pipeline](#async-task-pipeline)
- [Authentication & Authorization Flow](#authentication--authorization-flow)
- [Data Storage Strategy](#data-storage-strategy)
- [AI Visibility Scan Pipeline](#ai-visibility-scan-pipeline)
- [SEO Audit Pipeline](#seo-audit-pipeline)
- [Scoring System](#scoring-system)
- [Frontend Data Layer](#frontend-data-layer)
- [CORS & Security Boundaries](#cors--security-boundaries)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER BROWSER                                  │
│                     Next.js 14  (React 18, TypeScript)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Overview │  │ SEO Hub  │  │AI Visib. │  │   GSC    │  │  Ads     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └─────────────┴─────────────┴──────────────┴─────────────┘        │
│                            React Query (TanStack v5)                      │
│                         Axios HTTP Client (JWT Bearer)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS / HTTP
                    ┌────────────▼────────────┐
                    │      Nginx (prod)        │
                    │  Port 80 → 443 redirect  │
                    │  Port 443 (SSL/TLS)      │
                    │  /api/* → FastAPI        │
                    │  /*    → Next.js         │
                    └──────┬──────────┬────────┘
                           │          │
              ┌────────────▼──┐  ┌────▼───────────────┐
              │  FastAPI      │  │   Next.js Server    │
              │  Uvicorn      │  │   (port 3000)       │
              │  (port 8000)  │  │   SSR + API Routes  │
              └──────┬────────┘  └────────────────────┘
                     │
    ┌────────────────┼────────────────────┐
    │                │                    │
┌───▼──────┐  ┌──────▼──────┐  ┌─────────▼──────────┐
│PostgreSQL│  │    Redis    │  │  Celery Workers (4) │
│  (5432)  │  │   (6379)    │  │  + Beat Scheduler  │
│          │  │  ┌────────┐ │  │                    │
│  ORM:    │  │  │ Cache  │ │  │  SEO Tasks         │
│ SQLAlch. │  │  ├────────┤ │  │  AI Scan Tasks     │
│ asyncpg  │  │  │Broker  │ │  │  GSC Sync Tasks    │
│  Alembic │  │  └────────┘ │  │  Ads Sync Tasks    │
└──────────┘  └─────────────┘  │  Insight Gen Tasks │
                                └──────────┬─────────┘
                                           │
                               ┌───────────▼───────────┐
                               │  External Services     │
                               │  ┌──────────────────┐ │
                               │  │ OpenAI (GPT-4)   │ │
                               │  │ Anthropic(Claude)│ │
                               │  │ Google GSC API   │ │
                               │  │ Google Ads API   │ │
                               │  └──────────────────┘ │
                               │  ┌──────────────────┐ │
                               │  │ DO Spaces (S3)   │ │
                               │  │ JSON result store│ │
                               │  └──────────────────┘ │
                               └───────────────────────┘
```

---

## Service Responsibilities

### FastAPI Backend (port 8000)

The backend is a **thin orchestration layer** — it validates requests, checks auth, dispatches Celery tasks, and reads/writes the database. It does **not** perform any heavy I/O inline.

Responsibilities:
- JWT authentication and user session management
- Project CRUD operations
- Immediate data reads (scores, recommendations, rankings from DB)
- Task dispatch and status checks
- Google OAuth flows

What it does NOT do:
- Call LLM APIs directly from request handlers
- Run long-running scraping or analysis inline
- Block waiting for external APIs

### Celery Workers (4 concurrent processes)

Workers handle all asynchronous heavy lifting:
- LLM API calls (OpenAI, Anthropic)
- Google Search Console data sync
- Google Ads data sync
- SEO analysis and rank checking
- Score computation and insight generation
- Storage uploads to DigitalOcean Spaces

### Celery Beat Scheduler

Runs periodic tasks:
- Daily full-scan for each active project
- Weekly content gap refresh
- Nightly score snapshot

### Next.js Frontend (port 3000)

A purely client-side data consumer:
- Server-side rendering for initial page load (SEO-friendly auth pages)
- Client-side React Query for all dashboard data
- Polls for task completion or invalidates queries on user actions

---

## HTTP Request Lifecycle

### Synchronous request (e.g., GET /api/projects)

```
Browser
  │
  ├─ React Query calls api.projects.list()
  │
  ├─ Axios adds Authorization: Bearer <JWT>
  │
  ▼
FastAPI route handler
  │
  ├─ get_current_user dependency:
  │     decode JWT → verify signature → fetch user from DB
  │
  ├─ DB query via async SQLAlchemy session
  │
  ▼
  └─ Return JSON response (< 50ms)
```

### Asynchronous request (e.g., POST /api/seo/audit)

```
Browser
  │
  ├─ POST /api/seo/audit  {project_id}
  │
  ▼
FastAPI route handler
  │
  ├─ Auth check (get_current_user)
  ├─ Ownership check (project belongs to user)
  ├─ celery_app.send_task("run_seo_audit_task", [project_id])
  │
  ▼ Returns immediately:
  {
    "status": "queued",
    "task_id": "abc-123-def"
  }

  (Celery worker picks up task asynchronously)
  │
  ├─ Worker calls seo_service.run_full_seo_audit()
  ├─ Results uploaded to DO Spaces
  ├─ DB records updated
  │
  ▼
Browser polls GET /api/scores/{project_id} or
React Query invalidates on next focus/interval
```

---

## Async Task Pipeline

```
User clicks "Run Scan"
        │
        ▼
POST /api/scan/run  {project_id}
        │
        ▼
run_full_scan_task(project_id)   ← Celery master task
        │
        ├──── Parallel group ─────────────────────────────┐
        │  generate_keywords_task(project_id)              │
        │  run_rank_tracking_task(project_id)              │
        │  run_seo_audit_task(project_id)                  │
        │  find_content_gaps_task(project_id)              │
        │  generate_prompts_task(project_id)               │
        │  sync_gsc_data_task(project_id)                  │
        │  sync_ads_data_task(project_id)                  │
        └─────────────────────────────────────────────────┘
        │
        │  (all parallel tasks complete)
        │
        ▼
run_llm_scan_task(project_id)    ← Execute prompts against LLMs
        │
        ▼
compute_scores_task(project_id)  ← Calculate visibility scores
        │
        ▼
generate_insights_task(project_id) ← AI-powered recommendations
        │
        ▼
Score record written to DB
Recommendations written to DB
Frontend React Query refetches
```

### Task retry policy

All tasks use:
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def my_task(self, project_id: str):
    try:
        # async work in new event loop
    except Exception as exc:
        raise self.retry(exc=exc)
```

Failed tasks are visible in Celery Flower at http://localhost:5555.

---

## Authentication & Authorization Flow

### Registration

```
POST /api/auth/register
  { email, password, full_name }
        │
        ▼
  Validate with Pydantic UserCreate schema
        │
        ▼
  Check email uniqueness (DB query)
        │
        ▼
  Hash password: bcrypt via passlib CryptContext
        │
        ▼
  Insert User record (trial_ends_at = now + 14 days)
        │
        ▼
  Return UserResponse (no token — user must log in)
```

### Login

```
POST /api/auth/login
  { email, password }
        │
        ▼
  Fetch user by email
        │
        ▼
  Verify password: passlib.verify(plain, hashed)
        │
        ▼
  Create JWT: python-jose HS256
    payload: { sub: user.id, exp: now + 30min }
        │
        ▼
  Return { access_token, token_type: "bearer" }
```

### Authenticated Request

```
Frontend
  ├─ Stores access_token in localStorage (key: adticks_access_token)
  ├─ Axios request interceptor: adds Authorization: Bearer <token>
  │
  ▼
FastAPI dependency: get_current_user()
  ├─ Extract Bearer token from Authorization header
  ├─ jose.jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
  ├─ Extract sub (user ID) from payload
  ├─ Query DB for user, verify is_active=True
  └─ Inject user into route handler

If 401 → Axios response interceptor:
  ├─ Clear localStorage tokens
  └─ Redirect to /login
```

### Project Ownership Guard

Every project endpoint verifies:
```python
project = await db.get(Project, project_id)
if project.user_id != current_user.id:
    raise HTTPException(403, "Forbidden")
```

---

## Data Storage Strategy

AdTicks uses a **two-tier storage pattern**: PostgreSQL for structured relational data and DigitalOcean Spaces for large JSON blobs.

### PostgreSQL — what goes in the DB

| Table | What's stored |
|-------|--------------|
| `users` | Auth credentials, trial status |
| `projects` | Brand/domain configuration |
| `keywords` | Tracked keywords with metadata |
| `rankings` | Position history (time-series) |
| `gsc_data` | Daily GSC query metrics |
| `ads_data` | Daily ad campaign metrics |
| `prompts` | LLM prompt text + category |
| `responses` | Reference to Spaces path + model used |
| `mentions` | Extracted brand mention positions |
| `clusters` | Keyword topic clusters |
| `scores` | Computed visibility scores (time-series) |
| `recommendations` | AI-generated insights |

### DigitalOcean Spaces — what goes in object storage

Large, schema-less JSON results that don't need to be queried relationally:

```
projects/{project_id}/
  ├── seo/
  │   ├── keywords_latest.json      # Full keyword discovery result
  │   ├── rank_audit_latest.json    # Full rank check result
  │   ├── on_page_latest.json       # On-page audit JSON
  │   ├── technical_latest.json     # Technical checks JSON
  │   └── content_gaps_latest.json  # Content gaps JSON
  ├── ai/
  │   ├── scan_latest.json          # Full AI scan result
  │   └── responses/
  │       └── {response_id}.json    # Individual LLM response text
  ├── gsc/
  │   └── queries_latest.json       # GSC query dump
  └── ads/
      └── performance_latest.json   # Ads performance dump
```

This approach keeps the DB fast and lean while preserving full fidelity of raw results.

---

## AI Visibility Scan Pipeline

```
generate_prompts_task
        │
        ▼
prompt_generator.py
  Input: brand_name, domain, industry, competitors[]
  Generates prompts in 4 categories:
    brand_awareness:   "What is {brand}?"
    comparison:        "Compare {brand} vs {competitor}"
    problem_solving:   "Best tool for {use_case in industry}?"
    feature_specific:  "Does {brand} support {feature}?"
  Output: 12–48 prompts saved to DB (prompts table)
        │
        ▼
run_llm_scan_task
        │
        ├── llm_executor.py (async, concurrent)
        │     ├── OpenAI   GPT-4: asyncio.gather with rate limiting
        │     ├── Anthropic Claude: async client
        │     ├── Gemini (mock in dev): stubbed response
        │     └── Perplexity (mock in dev): stubbed response
        │
        │     Each response → raw JSON saved to Spaces
        │     Response record created in DB (path reference)
        │
        ▼
mention_extractor.py
  For each response:
    ├── Regex exact match: {brand} → high confidence
    ├── Fuzzy match: Levenshtein distance ≤ 2 → medium confidence
    ├── Extract position in response (ordinal, 1-indexed)
    └── Save Mention records to DB
        │
        ▼
scorer.py
  visibility_score = (prompts_with_mention / total_prompts) × 100
  sov_score        = (brand_mentions / total_mentions_across_brands) × 100
  impact_score     = weighted avg (mention_confidence × position_weight)
                     position_weight = 1 / position (earlier = higher)
        │
        ▼
Score record saved to DB
Scores exposed via GET /api/scores/{project_id}
```

---

## SEO Audit Pipeline

```
run_full_seo_audit_task(project_id)
        │
        ├── keyword_service.generate_keywords(brand, industry)
        │     Returns 20-50 keywords with intent + volume (mock/AI-generated)
        │
        ├── keyword_service.cluster_keywords(keywords)
        │     Groups by semantic similarity → Cluster records
        │
        ├── rank_tracker.bulk_rank_check(keywords, domain)
        │     Returns position 1-100 per keyword (mock SERP data)
        │     Ranking records created in DB
        │
        ├── on_page_analyzer.analyze_url(domain)
        │     Checks: H1 presence, meta description, image alt text,
        │             page speed (simulated), mobile friendliness,
        │             structured data, canonical tags
        │     Returns scored checklist
        │
        ├── technical_seo.run_checks(domain)
        │     Checks: HTTPS, www redirect, robots.txt, XML sitemap,
        │             Core Web Vitals (simulated), crawl errors,
        │             broken links, HREFLANG
        │     Returns pass/fail/warning per check
        │
        └── content_gap_analyzer.find_gaps(domain, competitors)
              Compares competitor keyword rankings vs brand rankings
              Returns: topic, competitor_coverage, search_volume,
                       difficulty, opportunity_score

All results → JSON uploaded to Spaces
Scores computed → _compute_overall_health():
  overall = 0.3 × technical_score + 0.4 × on_page_score + 0.3 × ranking_score
```

---

## Scoring System

The Unified Visibility Score is a composite of four channel scores:

```
Visibility Score (0–100)
  │
  ├── SEO Score (0–100)
  │     = (avg rank improvement + on-page score + technical score) / 3
  │
  ├── AI Score (0–100)
  │     = visibility_score from AI service
  │       (% of prompts where brand is mentioned)
  │
  ├── GSC Score (0–100)
  │     = normalized: (clicks × 0.4 + impressions × 0.3 + CTR × 0.3)
  │
  └── Ads Score (0–100)
        = normalized: (ROAS × 0.4 + CVR × 0.3 + CTR × 0.3)

Overall = weighted average:
  overall = SEO × 0.30 + AI × 0.25 + GSC × 0.25 + Ads × 0.20
```

Score labels:
- **80–100** → Excellent
- **60–79**  → Good
- **40–59**  → Fair
- **0–39**   → Needs Work

---

## Frontend Data Layer

```
Component
  │
  ├── useProjects() / useSEO() / useAIVisibility() / etc.
  │     React Query hooks (hooks/ directory)
  │
  ├── Query config:
  │     queryKey: ["seo", "keywords", projectId]
  │     queryFn: () => api.seo.getKeywords(projectId)
  │     staleTime: 5 × 60 × 1000  (5 minutes)
  │     initialData: MOCK_DATA     (shown immediately on first load)
  │
  ├── api.ts:
  │     Axios instance, baseURL = NEXT_PUBLIC_API_URL
  │     Request interceptor → adds Authorization: Bearer <token>
  │     Response interceptor → handles 401, clears tokens, redirects
  │
  ├── On mutation (e.g., triggering a scan):
  │     useMutation → calls api.scan.run(projectId)
  │     onSuccess: queryClient.invalidateQueries(["scores", projectId])
  │
  └── Mock data fallback:
        If api call fails → catch returns MOCK_DATA
        Ensures dashboard is always populated (demo mode)
```

---

## CORS & Security Boundaries

### CORS Policy

```python
# Development
allow_origins=["*"]

# Production
allow_origins=[
  "https://app.adticks.io",
  "https://www.adticks.io",
]
allow_methods=["GET","POST","PUT","DELETE","OPTIONS"]
allow_headers=["Authorization","Content-Type"]
allow_credentials=True
```

### Security headers (Nginx, production)

```nginx
add_header X-Content-Type-Options  "nosniff";
add_header X-Frame-Options         "DENY";
add_header X-XSS-Protection        "1; mode=block";
add_header Referrer-Policy         "strict-origin-when-cross-origin";
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains";
```

### Rate limiting (planned)

Future: `slowapi` middleware on FastAPI routes:
- `/api/auth/login` → 10 requests / minute / IP
- `/api/scan/run` → 5 requests / hour / user

---

*For database schema details, see [`DATABASE.md`](DATABASE.md). For API endpoint reference, see [`API_REFERENCE.md`](API_REFERENCE.md).*
