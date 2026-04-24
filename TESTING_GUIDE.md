# AdTicks SEO Scanning Pipeline - Quick Start & Testing Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose running
- Redis available (via docker-compose)
- Celery workers running (via docker-compose)

### 1. Verify Installation

```bash
# Run verification script
cd backend
python verify_pipeline.py

# Expected output:
# 8/8 tests passed ✅
```

### 2. Start Containers

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Test SEO Scan

```bash
# In your frontend application:
1. Create/Select a project
2. Click "Run Scan"
3. Modal shows "Starting..."
4. You can now close the modal - scan continues in background
```

---

## Testing Scenarios

### Scenario 1: First Scan (Full Execution)
**Expected behavior:**
- Scan starts (status: "scanning")
- Real-time progress updates every 2 seconds
- Current stage displayed (e.g., "Keyword Generation")
- Progress bar shows actual percentage
- ETA displayed at bottom
- Completes in ~45 minutes
- Results cached for 24 hours

**Verify:**
```bash
# Check Redis has cached results
docker exec adticks-redis redis-cli
> KEYS scan:results:*
> GET scan:results:{project_id}
```

### Scenario 2: Cached Results (No Changes)
**Expected behavior:**
1. Run scan on same project
2. Modal shows "Results from Cache"
3. Auto-closes after 3 seconds
4. Results appear instantly
5. Timestamp shows "Cached XX minutes ago"

**Verify:**
```bash
# Check cache was used
# In browser network tab: request completes in <1s
# Response includes: from_cache: true
```

### Scenario 3: Forced Refresh
**Expected behavior:**
1. Change project settings (domain, competitors, etc.)
2. Run scan
3. Cache detected as invalid
4. Full scan executes fresh
5. New results cached

**Verify:**
```bash
# Use cache invalidation endpoint
curl -X POST http://localhost:8000/api/cache/invalidate/{project_id}

# Returns:
# {
#   "project_id": "...",
#   "status": "invalidated",
#   "message": "All cache cleared..."
# }
```

### Scenario 4: Real-Time Progress
**Expected behavior:**
1. Start scan
2. Open browser console
3. See WebSocket messages (or HTTP polling)
4. Progress updates in real-time:
   - Stage changes
   - Percentage increases
   - Message updates
   - ETA recalculates

**Verify:**
```bash
# Check WebSocket in browser dev tools:
# Chrome: DevTools → Network → WS → Filter WebSocket
# Should see: /api/ws/scan/progress/{task_id}
# Messages: type: "progress", stage, progress, message
```

### Scenario 5: Component Caching
**Expected behavior:**
1. First scan: All components cached
2. Get cache stats:
```bash
curl http://localhost:8000/api/cache/stats/{project_id}
```
3. Response shows all 4 components cached with TTLs
4. Invalidate specific component:
```bash
curl -X POST http://localhost:8000/api/cache/invalidate-component/{project_id}/rankings
```
5. Rankings recalculated on next scan, others reused

**API Response:**
```json
{
  "project_id": "uuid",
  "scan_cache": {"exists": true, "ttl_remaining": 86000},
  "components": {
    "keywords": {"exists": true, "ttl_seconds": 86400},
    "rankings": {"exists": false},
    "audit": {"exists": true, "ttl_seconds": 86400},
    "gaps": {"exists": true, "ttl_seconds": 86400}
  },
  "total_cached_components": 3
}
```

---

## Manual Testing Checklist

### Phase 1: Caching ✅
- [ ] First scan completes and results are cached
- [ ] Second scan on same project shows cached results instantly
- [ ] Cache displayed with timestamp
- [ ] Changing project settings invalidates cache
- [ ] Cache stats endpoint shows correct TTLs
- [ ] Cache hit flag appears in API response

### Phase 2: Progress ✅
- [ ] WebSocket connection established for progress
- [ ] Progress updates every 2-3 seconds
- [ ] Stage name displayed correctly
- [ ] Progress percentage increases gradually
- [ ] Message shows current task details
- [ ] ETA calculates and updates
- [ ] Fallback to HTTP polling if WebSocket fails
- [ ] Progress bar animation smooth

### Phase 3: Performance ✅
- [ ] Rank checking uses batch API (fewer requests)
- [ ] Parallel tasks execute simultaneously
- [ ] Component caching reduces 2nd scan time
- [ ] Can invalidate specific components
- [ ] Ranking-only rescan faster than full rescan

### Phase 4: Advanced ✅
- [ ] Manual invalidation via API works
- [ ] Differential updates detect changes
- [ ] Cache statistics endpoint responsive
- [ ] Component-level invalidation works
- [ ] Can force refresh without timeout

---

## Performance Benchmarks

### Measurement Points
Use these to verify performance improvements:

**Start time:** When scan button clicked
**First update:** When progress updates first time
**Completion:** When results returned

```bash
# Check logs
docker-compose logs -f backend | grep -E "(Starting|completed|Cached)"

# Monitor Redis
docker exec adticks-redis redis-cli --stat

# Monitor Celery
docker exec adticks-celery celery inspect active_queues
```

### Expected Times
| Scenario | Expected | Actual |
|----------|----------|--------|
| Cache hit | <1s | _____ |
| First scan | ~45min | _____ |
| Forced refresh | ~45min | _____ |
| Component refresh | 5-15min | _____ |
| Fallback (no cache) | ~45min | _____ |

---

## Troubleshooting Guide

### Issue: "Scan took too long" error
**Solution:**
```bash
# Check timeouts are set correctly
docker exec adticks-backend python -c "from app.core.celery_app import celery_app; print('Soft:', celery_app.conf.soft_time_limit, 'Hard:', celery_app.conf.time_limit)"

# Should show: Soft: 3300 (55 min) Hard: 3600 (60 min)
```

### Issue: Cache not saving
**Solution:**
```bash
# Check Redis connection
docker exec adticks-backend python -c "
import asyncio
from app.core.caching import get_redis_client
async def test():
    redis = await get_redis_client()
    print('Redis:', redis)
    if redis:
        print('Ping:', await redis.ping())
asyncio.run(test())
"
```

### Issue: Progress not updating
**Solution:**
```bash
# Check WebSocket endpoint responds
curl -i http://localhost:8000/api/ws/scan/progress/test-task-id

# Check Celery task is running
docker exec adticks-celery celery inspect active

# Verify progress module is imported
docker exec adticks-backend python -c "from app.api.progress import router; print('OK')"
```

### Issue: Cache invalidation not working
**Solution:**
```bash
# Check API endpoint exists
curl -X POST http://localhost:8000/api/cache/invalidate/test-project-id

# Check Redis keys were deleted
docker exec adticks-redis redis-cli KEYS "component:*:test-project-id"

# Should return empty list after invalidation
```

---

## API Testing with cURL

### Test Cache Stats
```bash
curl http://localhost:8000/api/cache/stats/{project_id} \
  -H "Authorization: Bearer {token}"
```

### Test Cache Invalidation
```bash
curl -X POST http://localhost:8000/api/cache/invalidate/{project_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Test Component Invalidation
```bash
curl -X POST http://localhost:8000/api/cache/invalidate-component/{project_id}/rankings \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Test Progress Endpoint
```bash
# HTTP fallback (always works)
curl http://localhost:8000/api/ws/scan/progress/{task_id} \
  -H "Authorization: Bearer {token}"
```

---

## Monitoring

### Redis Monitoring
```bash
# Monitor cache operations in real-time
docker exec -it adticks-redis redis-cli monitor

# Check cache size
docker exec adticks-redis redis-cli INFO memory

# List all cached keys
docker exec adticks-redis redis-cli KEYS "*"
```

### Celery Monitoring
```bash
# Check active tasks
docker exec adticks-celery celery inspect active

# Check task statistics
docker exec adticks-celery celery inspect stats

# Monitor task execution
docker compose logs -f celery
```

### Backend Logs
```bash
# Watch for scan execution
docker compose logs -f backend | grep -E "(cache|progress|scan)"

# Watch for errors
docker compose logs -f backend | grep -i error
```

---

## Expected Log Output

### Successful Scan Start
```
[INFO] Starting non-blocking full scan pipeline for project=uuid
[INFO] Progress tracking initialized for project=uuid task=task-uuid
[INFO] Generating keywords for project=uuid
```

### Cache Hit
```
[INFO] Using cached scan results for project=uuid
[INFO] Cached results returned in <100ms
```

### Cache Invalidation
```
[INFO] Manually invalidated all cache for project=uuid
[INFO] Invalidated keywords cache for project=uuid
```

---

## Next Steps

1. **Production Deployment:**
   - Run verification: `python verify_pipeline.py`
   - All 8 tests should pass
   - Deploy containers

2. **Monitoring Setup:**
   - Monitor cache hit rates
   - Track average scan times
   - Alert on timeout occurrences

3. **User Communication:**
   - Inform users cache is now active
   - Explain why scans are faster on 2nd run
   - Document how to force refresh if needed

4. **Future Optimization:**
   - Add cache statistics dashboard
   - Implement differential updates UI
   - Add manual refresh button to dashboard

---

## Support

For issues or questions:
1. Check troubleshooting guide above
2. Review logs: `docker compose logs backend`
3. Run verification: `python verify_pipeline.py`
4. Check Redis: `docker exec adticks-redis redis-cli`
5. Check Celery: `docker exec adticks-celery celery inspect`
