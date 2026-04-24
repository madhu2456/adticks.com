"""
AdTicks — Main orchestration tasks.
Master tasks that chain sub-tasks for full project scans.
"""
import asyncio
import logging
import uuid
from uuid import UUID
from datetime import datetime, timezone

from celery import group
from sqlalchemy import select, delete, func

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.storage import StorageService
from app.core.progress import ScanProgress, ScanStage
from app.core.differential_updates import DifferentialUpdateDetector
from app.models.project import Project
from app.models.competitor import Competitor
from app.models.prompt import Prompt
from app.models.score import Score
from app.models.gsc import GSCData
from app.models.ads import AdsData
from app.models.keyword import Keyword
from app.models.recommendation import Recommendation
from app.core.scan_cache import (
    has_scan_cache,
    get_cached_scan_results,
    should_invalidate_cache,
    save_scan_results,
    get_cache_status,
)
from app.services.insights.insight_engine import InsightEngine
from app.services.insights.recommendation_generator import generate_recommendations
from app.tasks.seo_tasks import (
    generate_keywords_task,
    run_rank_tracking_task,
    run_seo_audit_task,
    find_content_gaps_task,
    sync_gsc_data_task,
    sync_ads_data_task,
)
from app.tasks.ai_tasks import (
    generate_prompts_task,
    run_llm_scan_task,
    compute_scores_task,
)

logger = logging.getLogger(__name__)
storage = StorageService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_project(session, project_id: str):
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def _load_competitors(session, project_id: str):
    result = await session.execute(
        select(Competitor).where(Competitor.project_id == project_id)
    )
    return result.scalars().all()


from celery import chain, chord

# ---------------------------------------------------------------------------
# run_full_scan_task — master orchestration
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=2, default_retry_delay=120, time_limit=3600, soft_time_limit=3300)
def run_full_scan_task(self, project_id: str, force_refresh: bool = False) -> dict:
    """
    Master task: orchestrate the full AdTicks pipeline for a project using non-blocking chains.
    
    Task timeout: 60 minutes (soft 55 minutes)
    
    Workflow:
      1. Check if valid cached results exist (unless force_refresh=True)
      2. If cache miss or invalid: Keyword Generation (Initial)
      3. Group of Parallel tasks (SEO audit, rank tracking, gaps, prompts, GSC, Ads)
      4. LLM Scan (depends on prompts)
      5. Score Computation
      6. Insight Generation
      7. Cache results in Redis (24 hour TTL)
    
    Args:
        project_id: Project UUID string
        force_refresh: If True, bypass cache and re-run full scan
    """
    # Initialize progress tracking
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    progress = ScanProgress(project_id, self.request.id)
    loop.run_until_complete(progress.initialize())
    loop.close()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        project_info = loop.run_until_complete(_get_project_info(project_id))
        loop.close()
    except Exception as exc:
        logger.exception("run_full_scan_task: could not load project %s: %s", project_id, exc)
        raise self.retry(exc=exc)

    if not project_info:
        logger.warning("run_full_scan_task: project %s not found", project_id)
        return {"project_id": project_id, "status": "project_not_found"}

    # Check if we can use cached results
    if not force_refresh:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Check if cache exists and is still valid
            cache_exists = loop.run_until_complete(has_scan_cache(project_id))
            cache_invalid = loop.run_until_complete(should_invalidate_cache(project_id))
            
            loop.close()
            
            if cache_exists and not cache_invalid:
                logger.info(f"Using cached scan results for project {project_id}")
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(progress.update(ScanStage.COMPLETED, 100, "Using cached results"))
                    cached_results = loop.run_until_complete(get_cached_scan_results(project_id))
                    loop.close()
                    
                    if cached_results:
                        return {
                            "project_id": project_id,
                            "status": "cached",
                            "from_cache": True,
                            "message": "Results from cache (24 hour TTL)",
                        }
                except Exception as e:
                    logger.warning(f"Error retrieving cached results: {e}")
            elif cache_invalid:
                logger.info(f"Scan cache invalidated for project {project_id} (project state changed)")
        except Exception as e:
            logger.warning(f"Error checking scan cache: {e}")
            # Continue with fresh scan

    domain = project_info["domain"]
    brand_name = project_info["brand_name"]
    industry = project_info["industry"] or "Technology"
    competitor_domains = project_info["competitors"]
    seed_keywords = [brand_name, industry.lower()] + competitor_domains[:3]

    logger.info(
        "Starting non-blocking full scan pipeline for project=%s (force_refresh=%s)",
        project_id,
        force_refresh,
    )

    # We build a chain: 
    # generate_keywords -> group(parallel_tasks) -> run_llm_scan_task -> compute_scores_task -> generate_insights_task -> cache_results
    
    workflow = chain(
        generate_keywords_task.s(
            project_id=project_id,
            domain=domain,
            industry=industry,
            seed_keywords=seed_keywords,
        ),
        group(
            run_rank_tracking_task.s(project_id=project_id),
            run_seo_audit_task.s(project_id=project_id),
            find_content_gaps_task.s(project_id=project_id),
            generate_prompts_task.s(
                project_id=project_id,
                brand_name=brand_name,
                domain=domain,
                industry=industry,
                competitors=competitor_domains,
            ),
            sync_gsc_data_task.s(project_id=project_id),
            sync_ads_data_task.s(project_id=project_id),
        ),
        run_llm_scan_task.s(project_id=project_id, prompt_limit=100),
        compute_scores_task.s(project_id=project_id),
        generate_insights_task.s(project_id=project_id),
        cache_scan_results_task.s(project_id=project_id),
    )

    # Launch the chain
    workflow.apply_async()

    return {
        "project_id": project_id,
        "status": "started",
        "from_cache": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }



async def _get_project_info(project_id: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return None
        competitors = await _load_competitors(session, project_id)
        return {
            "domain": project.domain,
            "brand_name": project.brand_name,
            "industry": project.industry,
            "competitors": [c.domain for c in competitors],
        }


# ---------------------------------------------------------------------------
# generate_insights_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_insights_task(self, project_id: str) -> dict:
    """
    Generate cross-channel insights and recommendations from all collected data.

    Loads rankings, mentions, scores, GSC data, and Ads data from DB,
    runs InsightEngine, generates recommendations, persists to DB and Spaces.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_generate_insights_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("generate_insights_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _generate_insights_impl(project_id: str) -> dict:
    logger.info("Generating insights for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return {"project_id": project_id, "status": "project_not_found"}

        brand_name = project.brand_name
        industry = project.industry or "Technology"

        # Load latest score
        score_result = await session.execute(
            select(Score)
            .where(Score.project_id == project_id)
            .order_by(Score.timestamp.desc())
            .limit(1)
        )
        latest_score = score_result.scalar_one_or_none()
        score_dict = {}
        if latest_score:
            score_dict = {
                "visibility_score": latest_score.visibility_score or 0.0,
                "impact_score": latest_score.impact_score or 0.0,
                "sov_score": latest_score.sov_score or 0.0,
            }

        # Load recent GSC data (up to 50 rows)
        gsc_result = await session.execute(
            select(GSCData)
            .where(GSCData.project_id == project_id)
            .order_by(GSCData.date.desc())
            .limit(50)
        )
        gsc_rows = gsc_result.scalars().all()
        gsc_data_for_engine = {
            "queries": [
                {
                    "query": row.query,
                    "clicks": row.clicks,
                    "impressions": row.impressions,
                    "ctr": row.ctr,
                    "position": row.position,
                }
                for row in gsc_rows
            ]
        }

        # Load recent Ads data
        ads_result = await session.execute(
            select(AdsData)
            .where(AdsData.project_id == project_id)
            .order_by(AdsData.date.desc())
            .limit(50)
        )
        ads_rows = ads_result.scalars().all()
        ads_data_for_engine = {
            "daily_data": [
                {
                    "date": row.date.isoformat() if row.date else None,
                    "campaign": row.campaign,
                    "clicks": row.clicks,
                    "cpc": row.cpc,
                    "conversions": row.conversions,
                    "spend": row.spend,
                }
                for row in ads_rows
            ],
            "summary": {
                "total_spend_usd": sum((r.spend or 0) for r in ads_rows),
                "total_clicks": sum((r.clicks or 0) for r in ads_rows),
                "total_conversions": sum((r.conversions or 0) for r in ads_rows),
                "avg_cpc_usd": (
                    sum((r.cpc or 0) for r in ads_rows) / len(ads_rows)
                    if ads_rows else 0
                ),
            },
        }

        # Load mentions for AI data context
        prompts_result = await session.execute(
            select(Prompt).where(Prompt.project_id == project_id)
        )
        prompts = prompts_result.scalars().all()
        total_prompts = len(prompts) or 1

        # Build minimal ai_data dict for InsightEngine
        ai_data_for_engine = {
            "score": score_dict,
            "prompt_count": total_prompts,
            "visibility_pct": round((score_dict.get("visibility_score", 0.0)) * 100, 1),
            "brand_name": brand_name,
        }

        # Build minimal seo_data dict
        seo_data_for_engine = {}

    # Instantiate InsightEngine and generate insights
    engine = InsightEngine(brand_name=brand_name, industry=industry)
    insights = engine.generate_insights(
        project_id=project_id,
        seo_data=seo_data_for_engine,
        ai_data=ai_data_for_engine,
        gsc_data=gsc_data_for_engine,
        ads_data=ads_data_for_engine,
    )
    logger.info("InsightEngine produced %d insights", len(insights))

    # Generate recommendations from insights
    recommendations = generate_recommendations(
        insights=insights,
        scores=score_dict,
        brand_name=brand_name,
    )
    logger.info("Recommendation generator produced %d recommendations", len(recommendations))

    # Persist recommendations to DB (clear old ones first)
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Recommendation).where(Recommendation.project_id == project_id)
        )
        for rec in recommendations:
            rec_row = Recommendation(
                id=uuid.uuid4(),
                project_id=UUID(project_id),
                text=rec.get("text", ""),
                priority=int(rec.get("priority", 3)),
                category=rec.get("category"),
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            session.add(rec_row)
        await session.commit()
        logger.info(
            "Inserted %d Recommendation rows for project %s",
            len(recommendations), project_id,
        )

    # Store insights JSON to Spaces
    payload = {
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "insight_count": len(insights),
        "recommendation_count": len(recommendations),
        "scores": score_dict,
        "insights": insights,
        "recommendations": recommendations,
    }
    try:
        storage.upload_json(
            StorageService.exports_path(project_id, "insights_latest.json"),
            payload,
        )
        logger.info("Uploaded insights_latest.json to Spaces for project %s", project_id)
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    return {
        "project_id": project_id,
        "insights_generated": len(insights),
        "recommendations": len(recommendations),
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# cache_scan_results_task — cache the final scan results
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def cache_scan_results_task(self, project_id: str, scan_results: dict | None = None) -> dict:
    """
    Cache the final scan results to Redis (24 hour TTL).
    
    This task runs at the end of the workflow chain to persist
    results for quick retrieval on subsequent scans (if nothing changed).
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cache_scan_results_impl(project_id, scan_results))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("cache_scan_results_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _cache_scan_results_impl(project_id: str, scan_results: dict | None = None) -> dict:
    """
    Cache scan results to Redis.
    
    Builds a minimal but useful result object containing latest data from DB.
    """
    logger.info("Caching scan results for project %s", project_id)
    
    try:
        # Build a results dict with latest data
        async with AsyncSessionLocal() as session:
            # Get latest score
            score_result = await session.execute(
                select(Score)
                .where(Score.project_id == project_id)
                .order_by(Score.timestamp.desc())
                .limit(1)
            )
            latest_score = score_result.scalar_one_or_none()
            
            # Get latest keywords count
            kw_result = await session.execute(
                select(func.count(Keyword.id))
                .where(Keyword.project_id == project_id)
            )
            keyword_count = kw_result.scalar() or 0
            
            # Build cache object
            cache_data = {
                "project_id": project_id,
                "scan_completed_at": datetime.now(timezone.utc).isoformat(),
                "scores": {
                    "visibility_score": latest_score.visibility_score if latest_score else 0.0,
                    "impact_score": latest_score.impact_score if latest_score else 0.0,
                    "sov_score": latest_score.sov_score if latest_score else 0.0,
                } if latest_score else {},
                "keyword_count": keyword_count,
                "status": "complete",
            }
        
        # Save to Redis cache
        success = await save_scan_results(project_id, cache_data)
        
        if success:
            logger.info("Successfully cached scan results for project %s (24h TTL)", project_id)
            return {
                "project_id": project_id,
                "status": "cached",
                "message": "Scan results cached to Redis (24 hour TTL)",
            }
        else:
            logger.warning("Failed to cache scan results for project %s", project_id)
            return {
                "project_id": project_id,
                "status": "cache_failed",
                "message": "Could not save to cache (Redis unavailable?)",
            }
    except Exception as exc:
        logger.error("Error caching scan results: %s", exc)
        raise


# ---------------------------------------------------------------------------
# schedule_daily_scans_task — Celery Beat entry point
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def schedule_daily_scans_task(self) -> dict:
    """
    Celery Beat task: enqueue run_full_scan_task for every active project.
    Runs daily at 2 AM UTC (configured in celery_app.py beat_schedule).
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_schedule_daily_scans_impl())
        loop.close()
        return result
    except Exception as exc:
        logger.exception("schedule_daily_scans_task failed: %s", exc)
        raise self.retry(exc=exc)


async def _schedule_daily_scans_impl() -> dict:
    logger.info("Scheduling daily scans for all active projects")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Project))
        projects = result.scalars().all()

    scheduled = 0
    for project in projects:
        try:
            run_full_scan_task.delay(project_id=str(project.id))
            scheduled += 1
            logger.info("Scheduled full scan for project %s (%s)", project.id, project.brand_name)
        except Exception as exc:
            logger.warning("Could not schedule scan for project %s: %s", project.id, exc)

    logger.info("Daily scans scheduled: %d projects", scheduled)
    return {
        "projects_scheduled": scheduled,
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
    }
