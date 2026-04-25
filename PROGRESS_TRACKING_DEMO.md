# Real-Time Task Progress Streaming Demo

## Overview
All long-running background tasks now stream detailed, real-time progress updates to the frontend via WebSocket. Users can see exactly what's happening at each stage.

## What You'll See During Scans

### 1. Keyword Generation Task 🎯
```
⏳ Initializing keyword generation...
   (5% complete)
   
🤖 Generating keywords for Technology...
   (15% complete)
   
✅ Generated 87 keywords • Processing...
   (35% complete)
   
📥 Processed 10/87 • 7 new, 3 duplicates
📥 Processed 20/87 • 14 new, 6 duplicates
📥 Processed 30/87 • 21 new, 9 duplicates
   (45% complete)
   
🔗 Clustering 87 keywords into semantic groups...
   (60% complete)
   
⚡ Caching keywords in Redis...
   (80% complete)
   
💾 Uploading to storage...
   (90% complete)
   
✨ Complete
```

**Logs Behind the Scenes:**
```
2026-04-25 12:54:54 INFO Generating keywords for project=4c72067b domain=example.com industry=Technology seeds=['ai']
2026-04-25 12:54:56 INFO Service returned 87 keywords
2026-04-25 12:55:02 INFO Clustered into 12 groups
2026-04-25 12:55:03 INFO Uploaded keywords.json to Spaces for project 4c72067b
```

---

### 2. Rank Tracking Task 📊
```
⏳ Loading project and keywords...
   (5% complete)
   
📊 Loaded 45 keywords • Domain: example.com
   (10% complete)
   
🔍 Checking SERP positions for 45 keywords...
   (15% complete)
   [Actual ranking checks happening against search engines]
   
💾 Saved 25/45 records...
💾 Saved 45/45 records...
   (85% complete)
   
⚡ Caching rankings in Redis...
   (92% complete)
   
📤 Uploading results to storage...
   (97% complete)
   
✨ Complete
```

**Logs Behind the Scenes:**
```
2026-04-25 12:55:04 INFO Running rank tracking for project=4c72067b
2026-04-25 12:55:04 INFO Using domain: example.com
2026-04-25 12:55:04 INFO Loaded 45 keywords for ranking check
2026-04-25 12:55:12 INFO Starting bulk rank check with 45 keywords
2026-04-25 12:55:45 INFO Completed ranking check: 45 results
2026-04-25 12:55:45 INFO Persisted all ranking records
2026-04-25 12:55:46 INFO Cached rankings successfully
```

---

### 3. SEO Audit Task 🔍
```
⏳ Initializing full audit...
   (5% complete)
   
📂 Loading previous audit results...
   (15% complete)
   
🔍 Analyzing page elements • URL: https://example.com/...
   (40% complete)
   [Crawling page, checking HTML, analyzing on-page elements]
   
⚙️ Running technical checks • Domain: example.com
   (60% complete)
   [Checking HTTPS, robots.txt, sitemap, performance, security headers]
   
📊 Compiling audit report...
   (82% complete)
   
⚡ Caching audit results...
   (92% complete)
   
💾 Uploading audit to storage...
   (97% complete)
   
✨ Complete: 42 issues found (8 on-page, 34 technical)
```

**Logs Behind the Scenes:**
```
2026-04-25 12:56:00 INFO Running SEO audit type=full for project=4c72067b url=https://example.com
2026-04-25 12:56:00 INFO Audit target: https://example.com
2026-04-25 12:56:02 INFO Starting on-page analysis for https://example.com
2026-04-25 12:56:04 INFO On-page analysis complete: 8 issues found
2026-04-25 12:56:05 INFO Starting technical audit for example.com
2026-04-25 12:56:12 INFO Technical audit complete: 34 issues found
```

---

### 4. GSC Keyword Import Task 📥
```
📂 Loading GSC data...
   (10% complete)
   
🔄 Checking 156 GSC queries for duplicates...
   (25% complete)
   
📥 Processed 10/156 • 8 new keywords added
📥 Processed 20/156 • 16 new keywords added
📥 Processed 50/156 • 42 new keywords added
📥 Processed 100/156 • 85 new keywords added
   (70% complete)
   
💾 Committing new keywords...
   (90% complete)
   
✨ Complete: Imported 127 new keywords from GSC
```

**Logs Behind the Scenes:**
```
2026-04-25 12:57:00 INFO Importing GSC queries as keywords for project=4c72067b
2026-04-25 12:57:00 INFO Found 156 unique GSC queries
2026-04-25 12:57:01 INFO Found 45 existing keywords in database
2026-04-25 12:57:05 INFO Imported 127 new keywords from GSC for project 4c72067b
```

---

## Technical Details

### Progress Tracking Architecture
- **Source**: Each Celery task initializes `ScanProgress(project_id, task_id)`
- **Storage**: Real-time progress stored in Redis with 1-hour TTL
- **Transport**: WebSocket endpoint streams updates every 2 seconds
- **Display**: Frontend shows stage, percentage, and human-readable message

### Task ID Flow
1. Task is queued by API endpoint
2. Celery receives task, extracts `self.request.id` (unique task UUID)
3. Task passes ID to implementation function
4. Implementation creates `ScanProgress` instance with task ID
5. All progress updates stored at key `progress:{task_id}`
6. Frontend WebSocket subscribes to `{task_id}` and receives live updates

### Stages Tracked
- `initializing` - Task starting
- `keyword_generation` - Generating/importing keywords
- `rank_tracking` - Checking SERP rankings
- `on_page_analysis` - Analyzing page elements
- `technical_audit` - Running technical checks
- `gap_analysis` - Finding content gaps
- `gsc_sync` - Syncing GSC data
- `completed` - Task finished successfully

### Progress Percentage Calibration
Each stage has weighted percentages based on typical execution time:
- Faster stages (5-10% of total)
- Main work (40-80% of total)
- Persistence & caching (80-95% of total)
- Completion (100%)

This ensures the progress bar moves consistently and doesn't appear stuck.

---

## Testing Progress Streaming

### Option 1: Via API
```bash
# Start a scan
curl -X POST http://localhost:8002/api/seo/keywords \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "4c72067b-be2a-4f53-8325-a389a19012aa", "keyword": "digital marketing"}'

# Get task_id from response
# Query progress via REST
curl http://localhost:8002/api/ws/scan/progress/{task_id}
```

### Option 2: Via WebSocket (Frontend)
```javascript
// In browser console
const taskId = "..." // from API response
const ws = new WebSocket(
  `ws://localhost:8002/api/ws/scan/progress/${taskId}?auth_token=${authToken}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.progress}% - ${data.message}`);
};
```

### Option 3: Watch Celery Worker Logs
```bash
# Terminal 1: Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Queue task via API
# Watch Terminal 1 for real-time task execution logs
```

---

## What's Improved

### Before ❌
- All scans showed "Initializing..." at 0%
- Users had no idea if tasks were running or stuck
- No feedback for 30+ minutes on some scans
- Difficult to debug task failures

### After ✅
- Real-time status updates every 2 seconds
- 10-15 different status messages per task
- Clear stage indication with emojis
- Batch progress (e.g., "Processed 100/156")
- Count tracking (e.g., "8 new, 3 duplicates")
- Detailed backend logs for debugging
- Users can see exactly what's happening

---

## Example Frontend Display

```
Running (4 scans)

  ✓ keywords_gsc                        Running
    📥 Processed 150/156 • 127 new, 29 duplicates
    94% • 3m 24s elapsed

  ✓ SEO Scan (Full Audit)               Running
    📊 Compiling audit report...
    82% • 2m 15s elapsed

  ✓ Rank Tracking                       Running
    💾 Saved 45/45 records...
    85% • 4m 30s elapsed

  ✓ Technical SEO Check                 Running
    ⚙️ Running technical checks • Domain: example.com
    60% • 1m 42s elapsed

[Stop button] [View logs]
```

---

## Debugging with Logs

Each task logs:
1. **Start**: What's being processed
2. **Checkpoints**: Major milestones and counts
3. **Issues**: Non-fatal warnings with recovery info
4. **Completion**: Final summary statistics

```bash
# View logs with timestamps and context
docker compose logs backend --follow | grep -E "task|progress|project=4c72067b"
```

This gives a complete audit trail of what happened during each scan.
