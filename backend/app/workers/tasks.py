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
from app.core.celery_utils import run_async
from app.core.database import AsyncSessionLocal, engine
from app.core.storage import StorageService
from app.core.progress import ScanProgress, ScanStage
from app.core.component_cache import ComponentCache
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
)
from app.services.insights.insight_engine import InsightEngine
from app.services.insights.recommendation_generator import generate_recommendations
from app.services.seo.competitor_research import identify_competitors
from app.tasks.seo_tasks import (
    generate_keywords_task,
    run_rank_tracking_task,
    run_seo_audit_task,
    find_content_gaps_task,
    sync_backlinks_task,
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


from celery import chain

# ---------------------------------------------------------------------------
# run_full_scan_task — master orchestration
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=2, default_retry_delay=120, time_limit=3600, soft_time_limit=3300)
def run_full_scan_task(self, project_id: str, force_refresh: bool = False) -> dict:
    """
    Master task: orchestrate the full AdTicks pipeline for a project using non-blocking chains.
    """
    async def _run_init():
        try:
            # Initialize progress tracking
            progress = ScanProgress(project_id, self.request.id)
            await progress.initialize()
            
            project_info = await _get_project_info(project_id)
            
            if not project_info:
                logger.warning("run_full_scan_task: project %s not found", project_id)
                return None, None

            # Check if we can use cached results
            if not force_refresh:
                try:
                    # Check if cache exists and is still valid
                    cache_exists = await has_scan_cache(project_id)
                    cache_invalid = await should_invalidate_cache(project_id)
                    
                    if cache_exists and not cache_invalid:
                        logger.info(f"Using cached scan results for project {project_id}")
                        try:
                            await progress.update(ScanStage.COMPLETED, 100, "Using cached results")
                            cached_results = await get_cached_scan_results(project_id)
                            
                            if cached_results:
                                return {
                                    "project_id": project_id,
                                    "status": "cached",
                                    "from_cache": True,
                                    "message": "Results from cache (24 hour TTL)",
                                }, None
                        except Exception as e:
                            logger.warning(f"Error retrieving cached results: {e}")
                    elif cache_invalid:
                        logger.info(f"Scan cache invalidated for project {project_id} (project state changed)")
                except Exception as e:
                    logger.warning(f"Error checking scan cache: {e}")
            
            return None, project_info
        finally:
            await engine.dispose()

    try:
        cached_res, project_info = run_async(_run_init())
        if cached_res:
            return cached_res
        if not project_info:
            return {"project_id": project_id, "status": "project_not_found"}
    except Exception as exc:
        logger.exception("run_full_scan_task initialization failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)

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
    master_task_id = self.request.id

    
    # 4. Filter AI tasks if disabled
    ai_enabled = project_info.get("ai_scans_enabled", True)
    
    # 5. Differential Update Detection
    async def _get_changes():
        detector = DifferentialUpdateDetector(project_id)
        return await detector.get_changes_summary(
            domain=domain,
            keywords=project_info["keywords"],
            competitors=project_info["competitors"]
        )
    
    changes = run_async(_get_changes())
    logger.info(f"[{project_id}] Differential analysis: {changes}")

    # Define parallel group based on changes
    parallel_tasks = []
    
    # Rankings should probably run every time unless we want to be very aggressive, 
    # but let's say we always run them for fresh data.
    parallel_tasks.append(run_rank_tracking_task.si(project_id=project_id, parent_task_id=master_task_id))
    
    # Audit: skip if domain hasn't changed and not forced
    if changes["domain_changed"] or force_refresh:
        parallel_tasks.append(run_seo_audit_task.si(project_id=project_id, parent_task_id=master_task_id))
    else:
        logger.info(f"[{project_id}] Skipping SEO audit (domain unchanged)")

    # Content Gaps: skip if domain and competitors haven't changed
    if changes["domain_changed"] or changes["competitors_changed"] or force_refresh:
        parallel_tasks.append(find_content_gaps_task.si(project_id=project_id, parent_task_id=master_task_id))
    else:
        logger.info(f"[{project_id}] Skipping content gap analysis (domain and competitors unchanged)")

    # GSC and Ads: always sync for fresh daily data
    parallel_tasks.append(sync_gsc_data_task.si(project_id=project_id, parent_task_id=master_task_id))
    parallel_tasks.append(sync_ads_data_task.si(project_id=project_id, parent_task_id=master_task_id))
    parallel_tasks.append(sync_backlinks_task.si(project_id=project_id, parent_task_id=master_task_id))
    
    if ai_enabled:
        # Prompt generation: only if keywords or competitors changed
        if changes["keywords_changed"] or changes["competitors_changed"] or force_refresh:
            parallel_tasks.append(
                generate_prompts_task.si(
                    project_id=project_id,
                    brand_name=brand_name,
                    domain=domain,
                    industry=industry,
                    competitors=competitor_domains,
                    parent_task_id=master_task_id,
                )
            )
        else:
            logger.info(f"[{project_id}] Skipping prompt generation (keywords and competitors unchanged)")
    else:
        logger.info(f"[{project_id}] AI scans disabled for this project. Skipping prompt generation.")

    # 6. Build the chain
    chain_steps = []
    
    # Keyword discovery: only if domain or industry changed
    if changes["domain_changed"] or force_refresh:
        chain_steps.append(
            generate_keywords_task.s(
                project_id=project_id,
                domain=domain,
                industry=industry,
                seed_keywords=seed_keywords,
                parent_task_id=master_task_id,
            )
        )
    else:
        logger.info(f"[{project_id}] Skipping keyword discovery (domain unchanged)")
    
    if parallel_tasks:
        chain_steps.append(group(parallel_tasks))
    
    if ai_enabled:
        # LLM scan: run if prompts were regenerated or if specifically requested
        # For simplicity, if AI is enabled and we are running a scan, we run the LLM scan
        chain_steps.append(run_llm_scan_task.si(project_id=project_id, prompt_limit=100, parent_task_id=master_task_id))
    
    chain_steps.extend([
        compute_scores_task.si(project_id=project_id, parent_task_id=master_task_id),
        generate_insights_task.si(project_id=project_id, parent_task_id=master_task_id),
        cache_scan_results_task.si(project_id=project_id, parent_task_id=master_task_id),
    ])
    
    workflow = chain(*chain_steps)

    # Launch the chain
    # By returning self.replace, we make the master task's ID represent the entire chain
    return self.replace(workflow)


@celery_app.task(bind=True)
def on_scan_error(self, request, exc, traceback, project_id: str, master_task_id: str):
    """
    Error handler for the full scan chain.
    Ensures progress is marked as failed so the UI doesn't get stuck.
    """
    async def _run():
        try:
            progress = ScanProgress(project_id, master_task_id)
            await progress.fail(str(exc))
            logger.error(f"Scan failed for project {project_id} (task {master_task_id}): {exc}")
        finally:
            await engine.dispose()
    
    run_async(_run())



async def _get_project_info(project_id: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return None
        competitors = await _load_competitors(session, project_id)
        comp_domains = [c.domain for c in competitors]
        
        # If no competitors are defined, automatically identify and persist them
        if not comp_domains:
            comp_domains = await identify_competitors(project.domain, project.industry or "Technology")
            if comp_domains:
                for domain in comp_domains:
                    new_comp = Competitor(
                        id=uuid.uuid4(),
                        project_id=UUID(project_id),
                        domain=domain
                    )
                    session.add(new_comp)
                await session.commit()
                logger.info(f"Auto-identified and persisted {len(comp_domains)} competitors for project {project_id}: {comp_domains}")
        
        # Also load keyword texts for differential update detection
        kw_result = await session.execute(
            select(Keyword.keyword).where(Keyword.project_id == project_id)
        )
        keywords = [r[0] for r in kw_result.all()]
        
        return {
            "domain": project.domain,
            "brand_name": project.brand_name,
            "industry": project.industry,
            "competitors": comp_domains,
            "keywords": keywords,
            "ai_scans_enabled": project.ai_scans_enabled,
        }


# ---------------------------------------------------------------------------
# generate_insights_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_insights_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """
    Generate cross-channel insights and recommendations from all collected data.
    """
    async def _run():
        try:
            return await _generate_insights_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("generate_insights_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _generate_insights_impl(project_id: str, task_id: str = "") -> dict:
    progress = ScanProgress(project_id, task_id)
    await progress.update(ScanStage.INSIGHT_GENERATION, 5, "⏳ Initializing insight engine...")
    
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
def cache_scan_results_task(self, project_id: str, scan_results: dict | None = None, parent_task_id: str | None = None) -> dict:
    """
    Cache the final scan results to Redis (24 hour TTL).
    """
    async def _run():
        try:
            return await _cache_scan_results_impl(project_id, scan_results, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("cache_scan_results_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _cache_scan_results_impl(project_id: str, scan_results: dict | None = None, task_id: str = "") -> dict:
    """
    Cache scan results to Redis.
    """
    progress = ScanProgress(project_id, task_id)
    await progress.update(ScanStage.COMPLETED, 95, "⚡ Finalizing and caching results...")
    
    logger.info("Caching scan results for project %s", project_id)
    
    try:
        # Build a results dict with latest data with timeout to prevent hanging
        try:
            async with AsyncSessionLocal() as session:
                # Load project for domain info
                project = await asyncio.wait_for(
                    _load_project(session, project_id),
                    timeout=10
                )
                if not project:
                    return {"project_id": project_id, "status": "project_not_found"}
                
                # Get latest score with timeout
                score_result = await asyncio.wait_for(
                    session.execute(
                        select(Score)
                        .where(Score.project_id == project_id)
                        .order_by(Score.timestamp.desc())
                        .limit(1)
                    ),
                    timeout=10
                )
                latest_score = score_result.scalar_one_or_none()
                
                # Get latest keywords with timeout (only fetch first 100 to avoid memory issues)
                kw_result = await asyncio.wait_for(
                    session.execute(
                        select(Keyword.keyword).where(Keyword.project_id == project_id).limit(100)
                    ),
                    timeout=15
                )
                keyword_list = [r[0] for r in kw_result.all()]
                keyword_count = len(keyword_list)
                
                # Get competitors with timeout
                competitors = await asyncio.wait_for(
                    _load_competitors(session, project_id),
                    timeout=10
                )
                competitor_domains = [c.domain for c in competitors]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout loading scan data for {project_id} (continuing with partial data)")
            # Use empty/default values to continue
            latest_score = None
            keyword_list = []
            keyword_count = 0
            competitor_domains = []
            project = None
        
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
        
        # Save state for differential updates (only if project was loaded)
        if project:
            try:
                detector = DifferentialUpdateDetector(project_id)
                await asyncio.wait_for(
                    detector.save_all_states(
                        domain=project.domain,
                        keywords=keyword_list,
                        competitors=competitor_domains
                    ),
                    timeout=5  # 5 second timeout for this operation
                )
                logger.info(f"Saved differential update state for project {project_id}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout saving differential update state for {project_id} (non-fatal)")
            except Exception as e:
                logger.warning(f"Failed to save differential update state: {e}")
        
        # Save to Redis cache
        success = await save_scan_results(project_id, cache_data)
        
        if success:
            logger.info("Successfully cached scan results for project %s (24h TTL)", project_id)
            await progress.complete()
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
    """
    async def _run():
        try:
            return await _schedule_daily_scans_impl()
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
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
