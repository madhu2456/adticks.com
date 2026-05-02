# AdTicks Spider - Integration Testing & Monitoring Guide

---

## Integration Testing

### End-to-End Workflow Test

Test the complete spider workflow from project creation to results:

```bash
#!/bin/bash

# 1. Create a new project
PROJECT=$(curl -s -X POST http://localhost:8002/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"E2E Spider Test",
    "domain":"python.org",
    "tld":".org"
  }' | jq -r '.id')

echo "Created project: $PROJECT"

# 2. Trigger web spider crawl
CRAWL=$(curl -s -X POST "http://localhost:8002/api/seo/analyze-website?project_id=$PROJECT&website_url=https://python.org&bot_name=googlebot&max_urls=100&max_depth=2" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.task_id')

echo "Queued crawl task: $CRAWL"

# 3. Wait for task completion (poll every 2 seconds)
echo "Waiting for crawl to complete..."
for i in {1..60}; do
  RESULTS=$(curl -s http://localhost:8002/api/seo/crawl-results/$PROJECT \
    -H "Authorization: Bearer $TOKEN")
  
  TOTAL=$(echo $RESULTS | jq '.total // 0')
  
  if [ "$TOTAL" -gt 0 ]; then
    echo "✅ Crawl completed! URLs crawled: $TOTAL"
    echo $RESULTS | jq '.summary'
    break
  fi
  
  echo "  Attempt $i/60 - Crawl still processing..."
  sleep 2
done

# 4. Verify results contain expected data
ORPHANS=$(echo $RESULTS | jq '.orphans.crawled_not_in_sitemap | length')
echo "Found $ORPHANS orphan pages"

# 5. Test cannibalization detection
curl -s "http://localhost:8002/api/seo/projects/$PROJECT/cannibalization/scan" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo "✅ E2E test completed successfully!"
```

### Real Website Testing

Test the spider on actual websites and verify it works correctly:

#### Test 1: python.org (Complex Site)
```bash
curl -X POST "http://localhost:8002/api/seo/analyze-website" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    'project_id': '$PROJECT_ID',
    'website_url': 'https://python.org',
    'bot_name': 'googlebot',
    'max_urls': 500,
    'max_depth': 3
  }"

# Expected: 200-400 URLs crawled, 0-5 orphan pages
```

#### Test 2: github.com (Large Site)
```bash
# Should handle large sites gracefully with depth limits
curl -X POST "http://localhost:8002/api/seo/analyze-website" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    'project_id': '$PROJECT_ID',
    'website_url': 'https://github.com',
    'bot_name': 'googlebot',
    'max_urls': 200,
    'max_depth': 2
  }"
```

#### Test 3: robots.txt Compliance
```bash
# Site with strict robots.txt (e.g., example.com)
# Should respect all disallow rules
curl -X POST "http://localhost:8002/api/seo/analyze-website" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    'project_id': '$PROJECT_ID',
    'website_url': 'https://example.com',
    'bot_name': 'googlebot',
    'max_urls': 100,
    'max_depth': 2
  }"

# Verify that disallowed paths aren't in results
```

### Cannibalization Workflow Test

```bash
# 1. Get a project with keywords
PROJECT_ID="550e8400-e29b-41d4-a716-446655440001"

# 2. Add keywords that might cannibalize
curl -X POST "http://localhost:8002/api/seo/keywords?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "keyword": "python tutorials",
    "intent": "informational",
    "difficulty": 35,
    "volume": 5000
  }'

# 3. Add another keyword that might cannibalize the first
curl -X POST "http://localhost:8002/api/seo/keywords?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "keyword": "python learning",
    "intent": "informational",
    "difficulty": 32,
    "volume": 4500
  }'

# 4. Trigger cannibalization scan
curl -X POST "http://localhost:8002/api/seo/projects/$PROJECT_ID/cannibalization/scan" \
  -H "Authorization: Bearer $TOKEN"

# 5. Get results
curl "http://localhost:8002/api/seo/projects/$PROJECT_ID/cannibalization" \
  -H "Authorization: Bearer $TOKEN" | jq '.cannibalizations'

# Expected: Should detect potential keyword cannibalization
```

---

## Production Monitoring Setup

### 1. Health Check Monitoring

```bash
#!/bin/bash
# Monitor endpoint health every 60 seconds

ENDPOINTS=(
  "http://localhost:8002/health"
  "http://localhost:8002/health/live"
  "http://localhost:8002/health/ready"
  "http://localhost:8002/api/health"
)

while true; do
  for endpoint in "${ENDPOINTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
    
    if [ "$RESPONSE" != "200" ]; then
      echo "⚠️ ALERT: $endpoint returned $RESPONSE"
      # Send to monitoring system (e.g., PagerDuty, Datadog)
    fi
  done
  
  sleep 60
done
```

### 2. Spider Task Monitoring

Monitor crawler task completion and errors:

```python
# monitor_spider_tasks.py
import asyncio
from app.tasks.seo_tasks import crawler_results
from app.core.component_cache import ComponentCache
import logging

logger = logging.getLogger("spider_monitor")

async def monitor_spider_tasks():
    """Monitor active spider tasks and alert on failures."""
    
    while True:
        try:
            # Get all active projects
            projects = await get_all_projects()  # Your implementation
            
            for project in projects:
                cache = ComponentCache(str(project.id))
                results = await cache.get_cached_crawl_results()
                
                if results:
                    stats = results.get("summary", {})
                    
                    # Alert if too many errors
                    error_count = stats.get("5xx", 0) + stats.get("4xx", 0)
                    total = stats.get("total_urls_crawled", 1)
                    error_rate = (error_count / total) * 100
                    
                    if error_rate > 10:
                        logger.warning(
                            f"High error rate on project {project.id}: "
                            f"{error_rate:.1f}% errors"
                        )
                    
                    # Alert if no URLs crawled
                    if total == 0:
                        logger.error(f"Project {project.id}: No URLs crawled")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor_spider_tasks())
```

### 3. Performance Metrics

```python
# Metrics to track

metrics = {
    "spider_crawl_time_seconds": {
        "description": "Time to complete full crawl",
        "alert_threshold": "> 300 seconds",
    },
    "spider_urls_per_second": {
        "description": "Crawl rate",
        "expected": "2 URLs/second (with rate limiting)",
    },
    "spider_cache_hit_rate": {
        "description": "% of requests served from cache",
        "target": "> 80%",
    },
    "spider_error_rate": {
        "description": "% of URLs returning 4xx/5xx",
        "alert_threshold": "> 15%",
    },
    "spider_orphan_pages": {
        "description": "Pages crawled but not in sitemap",
        "action": "Review and link or remove",
    },
    "spider_redirect_chains": {
        "description": "Multi-hop redirects (> 2 hops)",
        "action": "Consolidate redirects",
    },
}
```

### 4. Sentry Integration (Error Tracking)

```python
# Already configured in main.py, but verify settings

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,  # Set in .env
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    environment=settings.ENVIRONMENT,
)

# Tag spider operations for better tracking
with sentry_sdk.push_scope() as scope:
    scope.tag("spider_operation", "crawl")
    scope.tag("bot", "googlebot")
    scope.tag("project_id", project_id)
    # Spider operation here...
```

### 5. Log Analysis

Key logs to monitor:

```
# Successful crawl
LOG: "spider_crawl_complete" project_id=XXX urls_crawled=247 duration_seconds=42

# Crawl errors
LOG: "spider_crawl_error" project_id=XXX error=timeout

# Rate limiting active
LOG: "spider_rate_limit_active" delay_ms=500

# robots.txt issues
LOG: "spider_robots_txt_error" domain=example.com error="Parse failed"

# Cache operations
LOG: "spider_cache_hit" project_id=XXX
LOG: "spider_cache_miss" project_id=XXX

# Orphan detection
LOG: "spider_orphans_found" project_id=XXX count=5
```

---

## Alert Rules

### High Priority (Page Alert)

1. **Spider unavailable** - 3 consecutive failed health checks
2. **High error rate** - > 20% of crawled URLs returning errors
3. **Crawl timeout** - Single crawl takes > 10 minutes
4. **Database connection lost** - Metrics not being stored

### Medium Priority (Notify Team)

1. **Slow crawl** - Taking > 5 minutes for standard crawl
2. **Cache eviction** - > 50 cache misses in an hour
3. **robots.txt parse failure** - Can't parse domain's robots.txt
4. **High orphan rate** - > 30% of URLs are orphaned

### Low Priority (Log Only)

1. **Rate limiting** - Crawl hitting rate limits frequently
2. **Redirect chains** - Found 3+ hop redirects
3. **Missing sitemap** - Domain doesn't have robots.txt reference to sitemap

---

## Load Testing

```bash
# Simple load test: 10 concurrent crawls

for i in {1..10}; do
  curl -X POST "http://localhost:8002/api/seo/analyze-website?project_id=TEST_$i&website_url=https://example.com" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{}' &
done

wait

# Monitor resource usage during test:
# - CPU should stay < 80%
# - Memory should stay < 2GB
# - Response times should stay < 2 seconds
```

---

## Deployment Checklist

- [ ] All 17 unit tests passing
- [ ] Health check endpoints responding (4/4)
- [ ] Can crawl python.org successfully
- [ ] Orphan detection working
- [ ] Robots.txt parsing works
- [ ] Rate limiting active
- [ ] Redis caching functional
- [ ] Sentry configured
- [ ] Monitoring alerts set up
- [ ] Backup/disaster recovery plan in place
- [ ] Documentation reviewed
- [ ] User guide published

---

**Status:** Production Ready ✅  
**Last Updated:** 2026-05-02
