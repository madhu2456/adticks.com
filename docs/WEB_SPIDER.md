# Privacy-Safe Web Spider for Bot Crawl Analysis

## Overview

The Web Spider provides a **privacy-safe alternative to uploading raw access logs** for analyzing bot crawl patterns. Instead of requiring users to share sensitive server logs (which contain IPs, referers, timestamps, and user agents), the spider crawls the website directly and performs the same analysis.

## Why Spider Instead of Log Upload?

### Security & Privacy Benefits
- **No sensitive data exposure** — No IP addresses, full referers, or user details stored
- **User-controlled scope** — Users choose what gets crawled
- **GDPR/CCPA compliant** — No log file storage or retention
- **Domain-only input** — Just provide `https://example.com`, nothing else needed

### Equivalent Functionality
- ✅ Bot crawl pattern analysis (Googlebot, Bingbot, Yandexbot, etc.)
- ✅ Response time tracking and performance analysis
- ✅ Status code distribution (200s, 400s, 500s)
- ✅ Crawl waste detection (% of 4xx/5xx responses)
- ✅ Orphan page detection (crawled but not in sitemap)
- ✅ Redirect chain tracking
- ✅ Rate limiting and robots.txt compliance

## API Endpoints

### 1. Start Website Crawl

**POST** `/api/seo/analyze-website`

Queues a background crawl job.

**Query Parameters:**
- `project_id` (required): Project UUID
- `website_url` (required): Domain to crawl (e.g., `https://example.com`)
- `bot_name` (optional, default: `googlebot`): Bot to simulate
  - `googlebot`, `bingbot`, `yandexbot`, `duckduckbot`, `baiduspider`, `applebot`, `facebookbot`, `ahrefsbot`, `semrushbot`
- `max_urls` (optional, default: 500): Max URLs to crawl (10-5000)
- `max_depth` (optional, default: 3): Max crawl depth (1-10)

**Response:**
```json
{
  "status": "queued",
  "task_id": "abc-123-def",
  "project_id": "project-uuid",
  "website_url": "https://example.com",
  "bot": "googlebot",
  "message": "Website crawl queued. Results will be available shortly."
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/seo/analyze-website?project_id=abc&website_url=https://example.com&bot_name=googlebot&max_urls=500&max_depth=3" \
  -H "Authorization: Bearer TOKEN"
```

### 2. Get Crawl Results

**GET** `/api/seo/crawl-results/{project_id}`

Retrieves cached analysis results from the latest crawl.

**Query Parameters:**
- `skip` (optional, default: 0): Pagination offset
- `limit` (optional, default: 100): Number of results (max 500)

**Response:**
```json
{
  "project_id": "project-uuid",
  "summary": {
    "total_urls_crawled": 125,
    "unique_urls": 125,
    "bots": { "spider": 125 },
    "status_distribution": {
      "200": 120,
      "404": 3,
      "500": 2
    },
    "crawl_waste_pct": 4.0,
    "top_status_codes": { "200": 120, "404": 3, "500": 2 },
    "avg_response_time_ms": 245.6,
    "crawl_errors": 0
  },
  "aggregated": [
    {
      "bot": "spider",
      "url": "https://example.com/page1",
      "status_code": 200,
      "hits": 1,
      "response_time_ms": 234.5,
      "last_crawled": "2026-05-02T21:08:57.815000+00:00",
      "error": null,
      "redirect_to": null
    }
    // ... more results
  ],
  "orphans": {
    "crawled_not_in_sitemap": [
      "https://example.com/hidden-page"
    ],
    "in_sitemap_not_crawled": []
  },
  "total": 125,
  "skip": 0,
  "limit": 100,
  "has_more": true
}
```

## How It Works

### 1. Crawl Initiation
- User provides domain URL and optional bot name
- System queues background task
- Returns task ID immediately (202 Accepted)

### 2. Crawl Process
- **Fetches robots.txt** and caches rules
- **Starts from domain root** with configurable max depth
- **Respects robots.txt** — skips disallowed paths
- **Rate limits requests** — default 2 req/sec to avoid overload
- **Extracts links** from HTML pages (same-domain only)
- **Tracks redirects** (301, 302, 303, 307, 308)
- **Records response times** for performance analysis
- **Stops at max URLs** (default 500, configurable up to 5000)

### 3. Analysis
- **Aggregates crawl data** by URL and status code
- **Calculates statistics:**
  - Total URLs crawled
  - Unique URLs discovered
  - Status code distribution
  - Crawl waste % (4xx/5xx as % of total)
  - Average response time
- **Detects orphans:**
  - Fetches and parses sitemap.xml
  - Compares crawled URLs vs. sitemap URLs
  - Lists pages crawled but not in sitemap (and vice versa)

### 4. Result Caching
- Results cached in Redis for 24 hours
- Available via GET `/api/seo/crawl-results/{project_id}`
- Supports pagination (100 results per page)

## Bot User-Agents

The spider simulates these bots with realistic User-Agent headers:

| Bot | User-Agent |
|-----|-----------|
| **googlebot** | Mozilla/5.0 (compatible; Googlebot/2.1; ...) |
| **bingbot** | Mozilla/5.0 (Windows NT 10.0...) AppleWebKit/537.36 (compatible; Bingbot/2.0; ...) |
| **yandexbot** | Mozilla/5.0 (compatible; YandexBot/3.0; ...) |
| **duckduckbot** | DuckDuckBot/1.1 |
| **baiduspider** | Mozilla/5.0 (compatible; Baiduspider/2.0; ...) |
| **applebot** | Mozilla/5.0 (Macintosh...) AppleWebKit/537.36 (compatible; Applebot/0.1) |
| **facebookbot** | facebookexternalhit/1.1 |
| **ahrefsbot** | Mozilla/5.0 (compatible; AhrefsBot/7.0; ...) |
| **semrushbot** | Mozilla/5.0 (compatible; SemrushBot/7~bl; ...) |

## robots.txt Support

The spider fully respects `robots.txt` directives:

```
User-agent: *
Disallow: /private/
Disallow: /admin/
Crawl-delay: 2

User-agent: googlebot
Disallow: /no-google/
```

The spider will:
- Skip `/private/*` and `/admin/*` paths for all bots
- Skip `/no-google/*` only when simulating Googlebot
- Respect crawl delays if specified

## Rate Limiting

To prevent overload on target server:
- **Default: 2 requests/second**
- **Concurrent requests: None** (sequential crawling)
- **Request timeout: 60 seconds per URL**
- **Total session timeout: 5 minutes max**

This ensures crawls are gentle and won't trigger DDoS protection.

## Response Time Analysis

Response times are recorded in milliseconds and help identify:
- **Slow pages** — Response time > 500ms suggests performance issues
- **Server issues** — Timeouts or connection errors
- **CDN effectiveness** — Static vs. dynamic content comparison

Example:
```json
{
  "url": "https://example.com/large-page",
  "response_time_ms": 1245.6,  // Slow!
  "status_code": 200
}
```

## Orphan Page Detection

Orphans are pages that:
1. **Crawled but not in sitemap** — Spider found them, but `sitemap.xml` doesn't list them
   - Suggests internal linking issues or forgotten pages
2. **In sitemap but not crawled** — `sitemap.xml` lists them, but spider couldn't reach them
   - Suggests broken links, access restrictions, or redirect loops

## Example Workflow

```bash
# 1. Start crawl
curl -X POST "http://localhost:8000/api/seo/analyze-website?project_id=proj-123&website_url=https://example.com" \
  -H "Authorization: Bearer TOKEN"

# Response: { "status": "queued", "task_id": "task-456" }

# 2. Wait a moment for crawl to complete (usually 10-60 seconds depending on site size)

# 3. Fetch results
curl "http://localhost:8000/api/seo/crawl-results/proj-123" \
  -H "Authorization: Bearer TOKEN"

# Response: { "summary": {...}, "aggregated": [...], "orphans": {...} }

# 4. Analyze results for SEO issues:
#    - High crawl_waste_pct? → Fix broken pages or 404s
#    - Orphaned pages? → Add to sitemap or remove from internal links
#    - Slow response times? → Optimize server performance
```

## Error Handling

### Connection Errors
- Timeouts, DNS failures, SSL errors
- Recorded in `error` field of crawl result
- Doesn't stop crawl — continues with remaining URLs

### Invalid URLs
- Malformed URLs are skipped
- Non-200 HTML responses aren't parsed for links

### Sitemap Parsing
- Missing sitemap.xml → Orphan detection skipped gracefully
- Malformed XML → Logged as warning, continues

## Performance Considerations

### Crawl Speed
- **Small site (< 100 URLs):** 30-60 seconds
- **Medium site (100-500 URLs):** 1-3 minutes
- **Large site (500-5000 URLs):** 3-15 minutes

### Memory Usage
- Minimal — only keeps in-flight request data in memory
- Results cached in Redis (not memory)

### API Response
- Immediate 202 response — background processing
- Results available within 5 minutes for most sites

## Differences from Log Analyzer

| Feature | Log Analyzer | Web Spider |
|---------|-------------|-----------|
| Data source | Server access logs | Live website crawl |
| Security | Requires log upload (risky) | Domain-only input |
| Historical data | Yes (months/years) | No (current state only) |
| Accuracy | 100% of actual traffic | Simulation of bot behavior |
| Setup | Configure remote log URL | Just provide domain |
| Privacy | Exposes IPs, referers | No sensitive data |

## Integration with Existing Log Analyzer

Both can coexist:
- Use **Log Analyzer** if you have historical access logs
- Use **Web Spider** for privacy-safe current state analysis
- Combine results for comprehensive bot crawl insights

The spider reuses the same `log_analyzer.py` logic for result formatting, ensuring consistency.

## API Error Responses

| Status | Error | Resolution |
|--------|-------|-----------|
| 404 | Project not found | Verify project_id is correct and you own it |
| 400 | Invalid website_url | Provide full URL like `https://example.com` |
| 400 | Invalid bot_name | Use one of the supported bot names |
| 500 | Failed to queue crawl task | Retry or contact support |
| 202 | Success (not an error) | Results will be ready soon |

## Testing

Run unit tests:
```bash
pytest tests/unit/test_web_spider.py -v
```

Tests include:
- ✅ robots.txt parsing (allow/disallow)
- ✅ URL normalization and deduplication
- ✅ Link extraction from HTML
- ✅ Redirect detection
- ✅ Sitemap parsing (XML and index format)
- ✅ Statistics calculation
- ✅ Orphan detection
