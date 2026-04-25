# API Reference — AdTicks

Base URL: `https://adticks.com/api` (development)

All endpoints that modify or read user data require a **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## Table of Contents

- [Authentication](#authentication)
- [Projects](#projects)
- [Scores](#scores)
- [SEO](#seo)
- [AEO (Answer Engine Optimization)](#aeo-answer-engine-optimization)
- [Google Search Console (GSC)](#google-search-console-gsc)
- [Google Ads](#google-ads)
- [Insights](#insights)
- [Error Responses](#error-responses)
- [Pagination](#pagination)

---

## Authentication

### POST `/auth/register`

Create a new user account.

**Request body**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Jane Doe"
}
```

**Response `201 Created`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "trial_ends_at": "2026-05-05T12:00:00Z",
  "created_at": "2026-04-21T12:00:00Z"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| `400` | Email already registered |
| `422` | Validation error (missing fields, invalid email format) |

**Example**

```bash
curl -X POST https://adticks.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"Pass123!","full_name":"Jane Doe"}'
```

---

### POST `/auth/login`

Authenticate and receive a JWT access token.

**Request body**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response `200 OK`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| `401` | Invalid email or password |
| `400` | Account deactivated |

**Example**

```bash
curl -X POST https://adticks.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"Pass123!"}' \
  | jq '.access_token'
```

---

### GET `/auth/me`

Return the currently authenticated user.

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "jane@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "trial_ends_at": "2026-05-05T12:00:00Z",
  "created_at": "2026-04-21T12:00:00Z"
}
```

**Example**

```bash
curl https://adticks.com/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET `/auth/health`

Health check endpoint (unauthenticated).

**Response `200 OK`**

```json
{
  "status": "ok",
  "environment": "development"
}
```

---

## Projects

### POST `/projects`

Create a new project (brand + domain to track).

**Auth required:** Yes

**Request body**

```json
{
  "brand_name": "AdTicks",
  "domain": "adticks.io",
  "industry": "SaaS"
}
```

**Response `201 Created`**

```json
{
  "id": "7f3a1b2c-...",
  "user_id": "550e8400-...",
  "brand_name": "AdTicks",
  "domain": "adticks.io",
  "industry": "SaaS",
  "created_at": "2026-04-21T12:00:00Z"
}
```

---

### GET `/projects`

List all projects for the current user.

**Auth required:** Yes

**Response `200 OK`**

```json
[
  {
    "id": "7f3a1b2c-...",
    "brand_name": "AdTicks",
    "domain": "adticks.io",
    "industry": "SaaS",
    "created_at": "2026-04-21T12:00:00Z"
  }
]
```

---

### GET `/projects/{project_id}`

Get a single project by ID.

**Auth required:** Yes

**Errors**

| Status | Reason |
|--------|--------|
| `404` | Project not found |
| `403` | Project belongs to another user |

---

### PUT `/projects/{project_id}`

Update project metadata.

**Auth required:** Yes

**Request body** (all fields optional)

```json
{
  "brand_name": "AdTicks Pro",
  "domain": "adtickspro.io",
  "industry": "MarTech"
}
```

**Response `200 OK`** — updated project object

---

### DELETE `/projects/{project_id}`

Delete a project and all its data (cascade).

**Auth required:** Yes

**Response `204 No Content`**

---

## Scores

### GET `/scores/{project_id}`

Get the latest visibility score for a project.

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "id": "abc-123-...",
  "project_id": "7f3a1b2c-...",
  "visibility_score": 72.4,
  "impact_score": 68.1,
  "sov_score": 41.5,
  "timestamp": "2026-04-21T10:30:00Z"
}
```

**Errors**

| Status | Reason |
|--------|--------|
| `404` | No scores recorded yet — run a scan first |

---

### GET `/scores/{project_id}/history`

Score history for trending graphs.

**Auth required:** Yes

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 30 | Number of historical records to return |

**Response `200 OK`**

```json
[
  {
    "id": "abc-...",
    "project_id": "7f3a1b2c-...",
    "visibility_score": 72.4,
    "impact_score": 68.1,
    "sov_score": 41.5,
    "timestamp": "2026-04-21T10:30:00Z"
  },
  {
    "visibility_score": 67.0,
    "timestamp": "2026-04-20T10:30:00Z"
  }
]
```

---

## SEO

### POST `/seo/keywords`

Trigger async keyword discovery for a project.

**Auth required:** Yes

**Request body**

```json
{
  "project_id": "7f3a1b2c-...",
  "seed_keywords": ["visibility platform", "brand tracking"]
}
```

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

### GET `/seo/rankings/{project_id}`

Get current keyword rankings for a project.

**Auth required:** Yes

**Response `200 OK`**

```json
[
  {
    "id": "rank-uuid-...",
    "keyword_id": "kw-uuid-...",
    "keyword": "brand visibility platform",
    "position": 4,
    "url": "https://adticks.io/features",
    "timestamp": "2026-04-21T08:00:00Z"
  }
]
```

---

### GET `/seo/gaps/{project_id}`

Get content gap opportunities (topics competitors rank for that you don't).

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "project_id": "7f3a1b2c-...",
  "gaps": [
    {
      "topic": "AI brand monitoring",
      "competitor": "competitor.com",
      "competitor_position": 3,
      "your_position": null,
      "search_volume": 2200,
      "difficulty": 42,
      "opportunity_score": 8.4
    }
  ],
  "message": "Found 12 content gap opportunities"
}
```

---

### GET `/seo/technical/{project_id}`

Get technical SEO audit results.

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "project_id": "7f3a1b2c-...",
  "findings": [
    {
      "check": "HTTPS enabled",
      "status": "pass",
      "impact": "high",
      "recommendation": null
    },
    {
      "check": "XML Sitemap present",
      "status": "warning",
      "impact": "medium",
      "recommendation": "Submit sitemap at /sitemap.xml to Google Search Console"
    }
  ],
  "score": 84,
  "message": "Technical SEO audit complete"
}
```

---

### POST `/seo/audit`

Trigger a full asynchronous SEO audit (keywords + rankings + on-page + technical + gaps).

**Auth required:** Yes

**Request body**

```json
{
  "project_id": "7f3a1b2c-..."
}
```

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

## AEO (Answer Engine Optimization)

### POST `/prompts/generate`

Generate AI visibility prompts for a project.

**Auth required:** Yes

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | `all` | `brand_awareness`, `comparison`, `problem_solving`, `feature_specific`, or `all` |

**Request body**

```json
{
  "project_id": "7f3a1b2c-..."
}
```

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

### POST `/scan/run`

Execute all generated prompts against multiple LLMs and compute AI visibility score.

**Auth required:** Yes

**Request body**

```json
{
  "project_id": "7f3a1b2c-..."
}
```

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

### GET `/results/{project_id}`

Get LLM response records for the most recent AI scan.

**Auth required:** Yes

**Response `200 OK`**

```json
[
  {
    "id": "resp-uuid-...",
    "prompt_id": "prompt-uuid-...",
    "prompt_text": "What are the best AI visibility platforms?",
    "model": "gpt-4",
    "storage_path": "projects/7f3.../ai/responses/resp-uuid.json",
    "timestamp": "2026-04-21T09:00:00Z"
  }
]
```

---

### GET `/mentions/{project_id}`

Get brand mentions extracted from LLM responses.

**Auth required:** Yes

**Response `200 OK`**

```json
[
  {
    "id": "mention-uuid-...",
    "response_id": "resp-uuid-...",
    "brand": "AdTicks",
    "position": 2,
    "confidence": 0.97
  }
]
```

---

## Google Search Console (GSC)

### GET `/gsc/auth`

Get the Google OAuth authorization URL to connect GSC.

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&scope=..."
}
```

**Usage:** Redirect the user's browser to `auth_url`. After authorization, Google redirects back to the configured `GOOGLE_REDIRECT_URI`.

---

### GET `/gsc/callback`

OAuth callback handler. Called by Google after user authorizes.

**Auth required:** No (called by Google redirect)

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Authorization code from Google |
| `state` | string | State parameter for CSRF protection |

**Response `200 OK`**

```json
{
  "status": "connected",
  "user_id": "550e8400-..."
}
```

---

### GET `/gsc/queries/{project_id}`

Get Google Search Console query data for the last 28 days.

**Auth required:** Yes

**Response `200 OK`**

```json
[
  {
    "id": "gsc-uuid-...",
    "project_id": "7f3a1b2c-...",
    "query": "brand visibility tool",
    "clicks": 142,
    "impressions": 3800,
    "ctr": 0.0374,
    "position": 4.2,
    "page": "https://adticks.io/features",
    "date": "2026-04-21"
  }
]
```

---

### POST `/gsc/sync/{project_id}`

Trigger async sync of GSC data for a project.

**Auth required:** Yes

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

## Google Ads

### GET `/ads/performance/{project_id}`

Get ad campaign performance data.

**Auth required:** Yes

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 30 | Reporting window in days |

**Response `200 OK`**

```json
{
  "project_id": "7f3a1b2c-...",
  "reporting_period_days": 30,
  "campaigns": [
    {
      "id": "camp-uuid-...",
      "name": "[Search] AdTicks - Brand",
      "type": "Search",
      "status": "ENABLED",
      "daily_budget_usd": 150.00,
      "bid_strategy": "TARGET_CPA",
      "target_roas": 4.2,
      "ad_groups": [
        {
          "id": "ag-uuid-...",
          "name": "Brand Keywords",
          "status": "ENABLED",
          "keyword_count": 12,
          "avg_cpc_usd": 2.40
        }
      ]
    }
  ],
  "summary": {
    "total_impressions": 52400,
    "total_clicks": 3180,
    "total_spend_usd": 4320.00,
    "total_conversions": 186,
    "avg_ctr": 0.0607,
    "avg_cpc_usd": 1.36,
    "overall_roas": 5.8,
    "conversion_rate": 0.0585,
    "cost_per_conversion_usd": 23.23
  },
  "period_comparison": {
    "prev_spend_usd": 4100.00,
    "spend_change_pct": 5.4,
    "prev_conversions": 172,
    "conv_change_pct": 8.1
  }
}
```

---

### POST `/ads/sync/{project_id}`

Trigger async sync of Google Ads data.

**Auth required:** Yes

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

## Insights

### GET `/insights/{project_id}`

Get all AI-generated recommendations for a project.

**Auth required:** Yes

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `priority` | integer | Filter by priority: `1`, `2`, or `3` |
| `category` | string | Filter by: `seo`, `ai`, `gsc`, `ads`, `cross-channel` |
| `unread_only` | boolean | Return only unread recommendations |

**Response `200 OK`**

```json
[
  {
    "id": "rec-uuid-...",
    "project_id": "7f3a1b2c-...",
    "text": "Your brand appears in only 23% of AI responses when users ask about visibility platforms. Create dedicated 'AdTicks vs competitor' comparison pages to improve AI citation rates.",
    "priority": 1,
    "category": "ai",
    "is_read": false,
    "created_at": "2026-04-21T10:00:00Z"
  }
]
```

---

### GET `/insights/{project_id}/summary`

Get a summary of insights and latest scores (useful for dashboard overview).

**Auth required:** Yes

**Response `200 OK`**

```json
{
  "project_id": "7f3a1b2c-...",
  "latest_scores": {
    "visibility_score": 72.4,
    "impact_score": 68.1,
    "sov_score": 41.5,
    "timestamp": "2026-04-21T10:30:00Z"
  },
  "unread_recommendations": 5,
  "top_priorities": {
    "p1": 2,
    "p2": 3,
    "p3": 8
  }
}
```

---

### POST `/insights/{project_id}/refresh`

Regenerate insights using the latest data.

**Auth required:** Yes

**Response `202 Accepted`**

```json
{
  "status": "queued",
  "task_id": "celery-task-uuid"
}
```

---

## Error Responses

All errors follow a consistent JSON structure:

```json
{
  "detail": "Human-readable error message"
}
```

### Common HTTP status codes

| Status | Meaning |
|--------|---------|
| `200` | OK — Request succeeded |
| `201` | Created — Resource created |
| `202` | Accepted — Async task queued |
| `204` | No Content — Deletion succeeded |
| `400` | Bad Request — Invalid input or business logic error |
| `401` | Unauthorized — Missing or invalid JWT |
| `403` | Forbidden — JWT valid but resource access denied |
| `404` | Not Found — Resource does not exist |
| `422` | Unprocessable Entity — Pydantic validation failed |
| `429` | Too Many Requests — Rate limit exceeded |
| `500` | Internal Server Error — Unexpected server error |

### Validation error example (`422`)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Auth error example (`401`)

```json
{
  "detail": "Could not validate credentials"
}
```

---

## Pagination

Currently, list endpoints do **not** use pagination — they return all records for the project. This is suitable for the current data volumes.

Future endpoints will support:

```
GET /seo/rankings/{project_id}?page=1&page_size=50
```

With response headers:

```
X-Total-Count: 250
X-Page: 1
X-Page-Size: 50
```

---

## Interactive Documentation

When the backend is running, explore all endpoints interactively:

- **Swagger UI** — https://adticks.com/docs
  - Full request/response schemas
  - Try-it-out functionality
  - Authentication via the "Authorize" button

- **ReDoc** — https://adticks.com/redoc
  - Clean, readable reference format

- **OpenAPI JSON** — https://adticks.com/openapi.json
  - Import into Postman, Insomnia, or other API clients
