# Database Schema — AdTicks

AdTicks uses **PostgreSQL** (async via `asyncpg` + `SQLAlchemy`) with **Alembic** for migrations.

---

## Table of Contents

- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Tables Reference](#tables-reference)
  - [users](#users)
  - [projects](#projects)
  - [competitors](#competitors)
  - [keywords](#keywords)
  - [rankings](#rankings)
  - [clusters](#clusters)
  - [gsc_data](#gsc_data)
  - [ads_data](#ads_data)
  - [prompts](#prompts)
  - [responses](#responses)
  - [mentions](#mentions)
  - [scores](#scores)
  - [recommendations](#recommendations)
- [Indexes](#indexes)
- [Naming Conventions](#naming-conventions)
- [Working with Migrations](#working-with-migrations)

---

## Entity Relationship Diagram

```
┌──────────────────┐
│      users       │
│──────────────────│
│ id  UUID  PK     │
│ email            │
│ hashed_password  │
│ full_name        │
│ is_active        │
│ trial_ends_at    │
│ created_at       │
└────────┬─────────┘
         │ 1
         │
         │ N
┌────────▼─────────────────────────────────────────────────┐
│                        projects                           │
│──────────────────────────────────────────────────────────│
│ id          UUID   PK                                     │
│ user_id     UUID   FK → users.id  (cascade delete)       │
│ brand_name  TEXT                                          │
│ domain      TEXT                                          │
│ industry    TEXT   nullable                               │
│ created_at  TIMESTAMPTZ                                   │
└──┬────┬────┬────┬────┬────┬────┬────┬────────────────────┘
   │    │    │    │    │    │    │    │
   │    │    │    │    │    │    │    │ 1:N
   │    │    │    │    │    │    │    └──► competitors
   │    │    │    │    │    │    │           id, project_id, domain
   │    │    │    │    │    │    │
   │    │    │    │    │    │    │ 1:N
   │    │    │    │    │    │    └──────► keywords
   │    │    │    │    │    │                id, project_id, keyword,
   │    │    │    │    │    │                intent, difficulty, volume
   │    │    │    │    │    │                    │ 1:N
   │    │    │    │    │    │                    └──► rankings
   │    │    │    │    │    │                            id, keyword_id,
   │    │    │    │    │    │                            position, url, timestamp
   │    │    │    │    │    │
   │    │    │    │    │    │ 1:N
   │    │    │    │    │    └──────────► clusters
   │    │    │    │    │                    id, project_id, topic_name,
   │    │    │    │    │                    keywords (JSON)
   │    │    │    │    │
   │    │    │    │    │ 1:N
   │    │    │    │    └───────────────► gsc_data
   │    │    │    │                        id, project_id, query,
   │    │    │    │                        clicks, impressions, ctr,
   │    │    │    │                        position, page, date
   │    │    │    │
   │    │    │    │ 1:N
   │    │    │    └────────────────────► ads_data
   │    │    │                            id, project_id, campaign,
   │    │    │                            clicks, cpc, conversions,
   │    │    │                            spend, date
   │    │    │
   │    │    │ 1:N
   │    │    └─────────────────────────► prompts
   │    │                                  id, project_id, text,
   │    │                                  category, created_at
   │    │                                      │ 1:N
   │    │                                      └──► responses
   │    │                                             id, prompt_id,
   │    │                                             storage_path, model,
   │    │                                             timestamp
   │    │                                                 │ 1:N
   │    │                                                 └──► mentions
   │    │                                                        id, response_id,
   │    │                                                        brand, position,
   │    │                                                        confidence
   │    │
   │    │ 1:N
   │    └──────────────────────────────► scores
   │                                       id, project_id,
   │                                       visibility_score,
   │                                       impact_score, sov_score,
   │                                       timestamp
   │
   │ 1:N
   └───────────────────────────────────► recommendations
                                           id, project_id, text,
                                           priority, category,
                                           is_read, created_at
```

---

## Tables Reference

### `users`

Stores authenticated user accounts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `uuid4()` | Unique user identifier |
| `email` | `VARCHAR(320)` | NOT NULL, UNIQUE | Login email address |
| `hashed_password` | `VARCHAR(1024)` | NOT NULL | bcrypt hash (passlib) |
| `full_name` | `VARCHAR(255)` | nullable | Display name |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Soft disable flag |
| `trial_ends_at` | `TIMESTAMPTZ` | nullable | Trial expiry (14 days from registration) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Account creation time |

**Indexes:** `email` (unique B-tree)

---

### `projects`

One user → many projects. Each project represents a brand/domain being tracked.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Project identifier |
| `user_id` | `UUID` | NOT NULL, FK → `users.id` | Owner (cascade delete) |
| `brand_name` | `VARCHAR(255)` | NOT NULL | Brand display name (e.g. "AdTicks") |
| `domain` | `VARCHAR(255)` | NOT NULL | Root domain (e.g. "adticks.io") |
| `industry` | `VARCHAR(255)` | nullable | Industry category (e.g. "SaaS") |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Creation timestamp |

**Indexes:** `user_id` (B-tree)

**Cascade:** Deleting a user cascade-deletes all their projects and all project data.

---

### `competitors`

Competitor domains to compare against in SEO gap analysis and AI share-of-voice.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Competitor record ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `domain` | `VARCHAR(255)` | NOT NULL | Competitor domain (e.g. "competitor.com") |

---

### `keywords`

Tracked keywords associated with a project.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Keyword record ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `keyword` | `VARCHAR(512)` | NOT NULL | The keyword text |
| `intent` | `VARCHAR(64)` | nullable | Search intent: `informational`, `navigational`, `transactional`, `commercial` |
| `difficulty` | `FLOAT` | nullable | Keyword difficulty 0–100 |
| `volume` | `INTEGER` | nullable | Monthly search volume |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | When keyword was added |

---

### `rankings`

SERP position history for each keyword. Time-series table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Ranking record ID |
| `keyword_id` | `UUID` | NOT NULL, FK → `keywords.id` | Parent keyword |
| `position` | `INTEGER` | NOT NULL | SERP position (1 = top result) |
| `url` | `VARCHAR(2048)` | nullable | Ranking URL for this keyword |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL, default `now()` | When this rank was recorded |

**Indexes:** `keyword_id` (B-tree), `timestamp` (B-tree, for range queries)

---

### `clusters`

Semantic keyword topic clusters generated by the AI keyword service.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Cluster ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `topic_name` | `VARCHAR(512)` | NOT NULL | Cluster topic label (e.g. "Pricing Pages") |
| `keywords` | `JSON` | NOT NULL | Array of keyword strings in this cluster |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Creation timestamp |

---

### `gsc_data`

Google Search Console query performance data. Synced periodically via Celery task.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | GSC data record ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `query` | `VARCHAR(1024)` | NOT NULL | Search query string |
| `clicks` | `INTEGER` | NOT NULL | Clicks on this query/date |
| `impressions` | `INTEGER` | NOT NULL | Impressions on this query/date |
| `ctr` | `FLOAT` | NOT NULL | Click-through rate (0.0–1.0) |
| `position` | `FLOAT` | NOT NULL | Average SERP position |
| `page` | `VARCHAR(2048)` | nullable | Landing page URL |
| `date` | `DATE` | NOT NULL | Data date |

**Indexes:** `project_id` (B-tree), `date` (B-tree), composite `(project_id, date)`

---

### `ads_data`

Google Ads campaign performance data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Ads data record ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `campaign` | `VARCHAR(512)` | NOT NULL | Campaign name |
| `clicks` | `INTEGER` | NOT NULL | Clicks on this campaign/date |
| `cpc` | `FLOAT` | NOT NULL | Cost-per-click (USD) |
| `conversions` | `INTEGER` | NOT NULL | Conversion count |
| `spend` | `FLOAT` | NOT NULL | Total spend (USD) |
| `date` | `DATE` | NOT NULL | Data date |

**Indexes:** `project_id` (B-tree), `date` (B-tree)

---

### `prompts`

LLM prompts generated for AI visibility scanning.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Prompt ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `text` | `TEXT` | NOT NULL | Full prompt text |
| `category` | `VARCHAR(128)` | NOT NULL | `brand_awareness`, `comparison`, `problem_solving`, `feature_specific` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Generation timestamp |

---

### `responses`

LLM response records (actual text stored in DigitalOcean Spaces; this table stores the reference).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Response ID |
| `prompt_id` | `UUID` | NOT NULL, FK → `prompts.id` | Parent prompt |
| `storage_path` | `VARCHAR(1024)` | NOT NULL | DO Spaces path: `projects/{id}/ai/responses/{response_id}.json` |
| `model` | `VARCHAR(128)` | NOT NULL | LLM model: `gpt-4`, `claude-3-opus`, `gemini-pro`, `perplexity` |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL, default `now()` | When response was captured |

---

### `mentions`

Brand mentions extracted from LLM responses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Mention ID |
| `response_id` | `UUID` | NOT NULL, FK → `responses.id` | Parent response |
| `brand` | `VARCHAR(255)` | NOT NULL | Mentioned brand name |
| `position` | `INTEGER` | NOT NULL | Ordinal position in response (1 = first mention) |
| `confidence` | `FLOAT` | NOT NULL | Match confidence (0.0–1.0) |

---

### `scores`

Computed visibility scores snapshot. New row created on each scan. Enables historical trending.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Score record ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `visibility_score` | `FLOAT` | NOT NULL | Overall brand visibility (0–100) |
| `impact_score` | `FLOAT` | NOT NULL | Weighted mention impact (0–100) |
| `sov_score` | `FLOAT` | NOT NULL | Share of voice vs competitors (0–100) |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL, default `now()` | When score was computed |

**Indexes:** `project_id` (B-tree), `timestamp` (B-tree DESC for latest-first queries)

---

### `recommendations`

AI-generated, prioritised recommendations for the user.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Recommendation ID |
| `project_id` | `UUID` | NOT NULL, FK → `projects.id` | Parent project |
| `text` | `TEXT` | NOT NULL | Full recommendation text |
| `priority` | `INTEGER` | NOT NULL | `1` = P1 critical, `2` = P2 important, `3` = P3 nice-to-have |
| `category` | `VARCHAR(128)` | NOT NULL | `seo`, `ai`, `gsc`, `ads`, `cross-channel` |
| `is_read` | `BOOLEAN` | NOT NULL, default `false` | Whether user has seen it |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Generation timestamp |

**Indexes:** `project_id` (B-tree), `(project_id, is_read)` for unread count queries

---

## Indexes

| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| `users` | `email` | UNIQUE B-tree | Login lookup |
| `projects` | `user_id` | B-tree | List user's projects |
| `rankings` | `keyword_id` | B-tree | Ranking history per keyword |
| `rankings` | `timestamp` | B-tree | Date range queries |
| `gsc_data` | `project_id` | B-tree | GSC data per project |
| `gsc_data` | `date` | B-tree | GSC data by date |
| `gsc_data` | `(project_id, date)` | Composite | Combined filter |
| `ads_data` | `project_id` | B-tree | Ads data per project |
| `ads_data` | `date` | B-tree | Ads data by date |
| `scores` | `project_id` | B-tree | Score history per project |
| `scores` | `timestamp DESC` | B-tree | Latest score lookup |
| `recommendations` | `project_id` | B-tree | Recs per project |
| `recommendations` | `(project_id, is_read)` | Composite | Unread count |

---

## Naming Conventions

- **Table names**: plural snake_case (`users`, `gsc_data`, `ads_data`)
- **Column names**: snake_case (`brand_name`, `created_at`, `is_active`)
- **Primary keys**: always `id UUID` with `uuid4()` default
- **Foreign keys**: named `{referenced_table_singular}_id` (e.g. `user_id`, `project_id`)
- **Timestamps**: `created_at` for immutable creation time, `timestamp` for time-series records
- **Soft flags**: `is_{state}` Boolean columns (e.g. `is_active`, `is_read`)
- **JSON columns**: only for schema-less arrays (e.g. `keywords JSON` in clusters)

---

## Working with Migrations

### Check current state

```bash
docker-compose exec backend alembic current
```

### Apply all pending migrations

```bash
make migrate
# Equivalent: docker-compose exec backend alembic upgrade head
```

### Create a new migration (auto-generated from model changes)

```bash
make migration msg="add trial_plan column to users"
# Equivalent: docker-compose exec backend alembic revision --autogenerate -m "..."
```

Always review the generated file in `backend/alembic/versions/` before applying — autogenerate can miss some changes (e.g. renamed columns, custom constraints).

### Rollback one step

```bash
make downgrade
# Equivalent: docker-compose exec backend alembic downgrade -1
```

### View full migration history

```bash
docker-compose exec backend alembic history --verbose
```

### Adding a new model

1. Create the ORM model in `backend/app/models/my_model.py`
2. Import it in `backend/app/models/__init__.py`
3. Import it in `backend/alembic/env.py` so autogenerate can detect it
4. Run `make migration msg="add my_model table"`
5. Review the generated migration file
6. Apply with `make migrate`
