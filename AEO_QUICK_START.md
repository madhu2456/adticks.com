# AEO Module - Quick Start Guide

## Installation & Setup

### 1. Backend Setup
No additional installation required. Models are auto-created on startup.

```bash
cd backend
python main.py
# Tables will be created automatically
```

### 2. Frontend Setup
Components are ready to use:

```bash
cd frontend
npm install  # If needed
npm run dev
```

## Using the AEO Module

### 1. Accessing the AEO Dashboard

```typescript
// In your routing/navigation
import { AEODashboard } from '@/components/aeo';

// Route handler or page
export default function ProjectPage() {
  return <AEODashboard />;
}
```

### 2. API Examples

#### Check AI Visibility

```bash
curl -X POST http://localhost:8002/api/aeo/check-visibility \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword_id": "uuid-here",
    "ai_models": ["chatgpt", "perplexity", "claude"]
  }'

# Response (202 Accepted)
{
  "status": "queued",
  "keyword_id": "uuid-here",
  "models_to_check": ["chatgpt", "perplexity", "claude"],
  "message": "Visibility check queued"
}
```

#### Get Visibility Data

```bash
curl http://localhost:8002/api/aeo/projects/{project_id}/visibility/summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response
{
  "total_keywords": 25,
  "ai_visibility_count": 150,
  "featured_snippet_count": 8,
  "paa_queries_count": 45,
  "recommendation_count": 35,
  "pending_recommendations": 12,
  "implemented_recommendations": 18,
  "avg_ai_visibility_percentage": 62.5,
  "snippet_opportunities": 17
}
```

#### Get Snippet Data

```bash
curl http://localhost:8002/api/aeo/keywords/{keyword_id}/snippets \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response
[
  {
    "id": "uuid",
    "keyword_id": "uuid",
    "has_snippet": true,
    "snippet_type": "featured",
    "snippet_text": "...",
    "snippet_source_url": "https://...",
    "position_before_snippet": 3,
    "date_captured": "2024-01-15T10:30:00Z",
    "lost_date": null
  }
]
```

#### Generate Recommendations

```bash
curl -X POST http://localhost:8002/api/aeo/content/generate-recommendations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword_id": "uuid-here"
  }'

# Response
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "keyword_id": "uuid",
    "recommendation_type": "optimize",
    "recommendation_text": "Optimize the meta title...",
    "implementation_difficulty": "easy",
    "estimated_impact": "high",
    "created_at": "2024-01-15T10:30:00Z",
    "user_action": null
  },
  ...
]
```

#### Get Content Outline

```bash
curl -X POST http://localhost:8002/api/aeo/content/generate-outline \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword_id": "uuid-here",
    "content_type": "blog",
    "target_length": "medium"
  }'

# Response
{
  "keyword": "keyword text",
  "outline": [
    "Introduction: What is...",
    "Key Benefits of...",
    "How to Implement...",
    ...
  ],
  "estimated_word_count": 2500,
  "key_topics": ["keyword", "keyword benefits", ...]
}
```

### 3. Using Services Directly (Python)

```python
from app.services.ai_visibility import AIVisibilityService
from app.services.snippet_tracking import SnippetTrackingService
from app.services.content_recommendations import ContentRecommendationService

# Initialize services
visibility_service = AIVisibilityService()
snippet_service = SnippetTrackingService()
rec_service = ContentRecommendationService()

# Check visibility
is_mentioned, context, position, confidence = await visibility_service.check_chatgpt_visibility(
    keyword="your keyword",
    brand_name="Your Brand",
    domain="yourdomain.com"
)

# Store result
visibility = await visibility_service.store_visibility_check(
    db=db_session,
    project_id=project_id,
    keyword_id=keyword_id,
    ai_model="chatgpt",
    is_mentioned=is_mentioned,
    mention_context=context,
    position=position,
    confidence_score=confidence
)

# Add PAA query
paa = await snippet_service.add_paa_query(
    db=db_session,
    keyword_id=keyword_id,
    paa_query="How to optimize?",
    answer_source_url="https://example.com",
    answer_snippet="Answer here",
    position=1
)

# Generate FAQ from PAA
faq = await rec_service.generate_faq_from_paa(
    db=db_session,
    project_id=project_id,
    keyword_id=keyword_id,
    paa_id=paa.id
)

# Generate recommendations
recommendations = await rec_service.generate_recommendations(
    db=db_session,
    project_id=project_id,
    keyword_id=keyword_id,
    keyword_text="your keyword"
)
```

### 4. React Component Usage

```typescript
import { AEODashboard } from '@/components/aeo';

// In your page/component
export default function SEOPage() {
  return (
    <div>
      <h1>SEO Dashboard</h1>
      <AEODashboard />
    </div>
  );
}
```

### 5. Individual Component Usage

```typescript
import {
  AIVisibilityTracker,
  SnippetTracker,
  ContentRecommendations,
  FAQGenerator
} from '@/components/aeo';

export default function CustomDashboard({ projectId }: { projectId: string }) {
  return (
    <div>
      <AIVisibilityTracker projectId={projectId} />
      <SnippetTracker projectId={projectId} />
      <ContentRecommendations projectId={projectId} />
      <FAQGenerator projectId={projectId} />
    </div>
  );
}
```

## Common Tasks

### Task 1: Set Up Daily Visibility Checks

```python
# backend/app/tasks/aeo_tasks.py is ready to integrate with Celery

# Add to your Celery beat schedule (celery.py)
from celery.schedules import crontab
from app.tasks.aeo_tasks import daily_visibility_check

app.conf.beat_schedule = {
    'daily-aeo-visibility-check': {
        'task': 'app.tasks.aeo_tasks.daily_visibility_check',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': (project_id, brand_name, domain)
    }
}
```

### Task 2: Get Project AEO Summary

```python
# Python
from sqlalchemy import select
from app.models.aeo import AEOVisibility, ContentRecommendation

async def get_aeo_summary(db: AsyncSession, project_id: UUID):
    visibility = await db.execute(
        select(AEOVisibility).where(AEOVisibility.project_id == project_id)
    )
    recommendations = await db.execute(
        select(ContentRecommendation).where(
            ContentRecommendation.project_id == project_id
        )
    )
    return {
        'visibility_checks': len(visibility.scalars().all()),
        'recommendations': len(recommendations.scalars().all())
    }
```

### Task 3: Export Recommendations

```typescript
// React/TypeScript
async function exportRecommendations(projectId: string) {
  const response = await fetch(
    `/api/aeo/projects/${projectId}/recommendations`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  const data = await response.json();
  
  // Convert to CSV
  const csv = data.map(r => `${r.recommendation_type},${r.recommendation_text}`).join('\n');
  
  // Download
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'recommendations.csv';
  a.click();
}
```

## Configuration

### Environment Variables

```bash
# .env (optional for production)
OPENAI_API_KEY=sk-...  # For real ChatGPT integration
PERPLEXITY_API_KEY=pplx-...  # For real Perplexity
ANTHROPIC_API_KEY=sk-ant-...  # For real Claude
```

### Database

Default SQLite (development):
```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

Production (PostgreSQL):
```python
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/adticks"
```

## Troubleshooting

### Issue: Visibility data is empty
**Solution**: Run a visibility check first via POST /api/aeo/check-visibility

### Issue: Snippet tracker not updating
**Solution**: Create a snippet tracking record via POST /api/aeo/snippets/check-opportunity

### Issue: Frontend components not loading
**Solution**: Ensure:
1. Token is stored in localStorage
2. API server is running
3. Routes are properly configured

### Issue: Tests failing
**Solution**:
```bash
cd backend
pytest tests/test_aeo_module.py -v
pytest tests/test_aeo_integration.py -v
```

## Performance Tips

1. **Pagination**: Always use limit parameter for large datasets
   ```bash
   /api/aeo/projects/{id}/trends?limit=50
   ```

2. **Filtering**: Use filters to reduce data
   ```bash
   /api/aeo/projects/{id}/recommendations?rec_type=optimize
   ```

3. **Caching**: Trends change less frequently
   - Cache trends for 1-7 days
   - Visibility checks for 1 day

4. **Background Tasks**: Schedule checks during off-peak hours
   - Daily: 2-3 AM UTC
   - Weekly: Monday 6 AM UTC

## Next Steps

1. **Configure Real APIs**
   - Add OPENAI_API_KEY, PERPLEXITY_API_KEY, ANTHROPIC_API_KEY
   - Replace mock implementations

2. **Set Up Background Tasks**
   - Install Celery: `pip install celery redis`
   - Configure beat scheduler
   - Start workers

3. **Add Monitoring**
   - Configure Sentry for error tracking
   - Set up dashboards for metrics

4. **Performance Optimization**
   - Add Redis caching layer
   - Implement query optimization
   - Add database connection pooling

## Support & Documentation

- See **AEO_MODULE_DOCUMENTATION.md** for complete technical docs
- See **AEO_MODULE_DELIVERY.md** for implementation details
- See **AEO_IMPLEMENTATION_CHECKLIST.md** for verification

## Success! 🎉

You now have a fully functional AEO module ready to power AI-driven SEO optimization!
