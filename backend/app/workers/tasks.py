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
from sqlalchemy import select, delete

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.storage import StorageService
from app.models.project import Project
from app.models.competitor import Competitor
from app.models.prompt import Prompt
from app.models.score import Score
from app.models.gsc import GSCData
from app.models.ads import AdsData
from app.models.recommendation import Recommendation
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


# ---------------------------------------------------------------------------
# run_full_scan_task — master orchestration
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_full_scan_task(self, project_id: str) -> dict:
    """
    Master task: orchestrate the full AdTicks pipeline for a project.

    Pipeline:
      1. generate_keywords_task
      2. run_rank_tracking_task (after keywords)  [parallel]
      3. run_seo_audit_task                       [parallel]
      4. find_content_gaps_task                   [parallel]
      5. generate_prompts_task                    [parallel]
      6. sync_gsc_data_task                       [parallel]
      7. sync_ads_data_task                       [parallel]
      8. run_llm_scan_task (after prompts)
      9. compute_scores_task (after LLM scan)
     10. generate_insights_task (final)
    """
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

    domain = project_info["domain"]
    brand_name = project_info["brand_name"]
    industry = project_info["industry"] or "Technology"
    competitor_domains = project_info["competitors"]
    seed_keywords = [brand_name, industry.lower()] + competitor_domains[:3]

    logger.info(
        "Starting full scan pipeline for project=%s brand=%s domain=%s",
        project_id, brand_name, domain,
    )

    # Step 1: Generate keywords (must complete before rank tracking)
    kw_result = generate_keywords_task.delay(
        project_id=project_id,
        domain=domain,
        industry=industry,
        seed_keywords=seed_keywords,
    )
    try:
        kw_result.get(timeout=300)
        logger.info("Keywords generated for project %s", project_id)
    except Exception as exc:
        logger.warning("Keyword generation had an issue (continuing): %s", exc)

    # Step 2-7: Parallel tasks (SEO audit, rank tracking, gaps, prompts, GSC, Ads)
    parallel_tasks = [
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
    ]

    parallel_group = group(parallel_tasks)
    parallel_result = parallel_group.apply_async()
    try:
        parallel_result.get(timeout=600, propagate=False)
        logger.info("Parallel tasks complete for project %s", project_id)
    except Exception as exc:
        logger.warning("Some parallel tasks had issues (continuing): %s", exc)

    # Step 8: Run LLM scan (after prompts were generated)
    llm_result = run_llm_scan_task.delay(project_id=project_id, prompt_limit=100)
    try:
        llm_result.get(timeout=600)
        logger.info("LLM scan complete for project %s", project_id)
    except Exception as exc:
        logger.warning("LLM scan had an issue (continuing): %s", exc)

    # Step 9: Compute scores
    scores_result = compute_scores_task.delay(project_id=project_id)
    try:
        scores_result.get(timeout=120)
        logger.info("Scores computed for project %s", project_id)
    except Exception as exc:
        logger.warning("Score computation had an issue (continuing): %s", exc)

    # Step 10: Generate insights
    insights_result = generate_insights_task.delay(project_id=project_id)
    try:
        insights_result.get(timeout=120)
        logger.info("Insights generated for project %s", project_id)
    except Exception as exc:
        logger.warning("Insight generation had an issue (continuing): %s", exc)

    logger.info("Full scan pipeline complete for project %s", project_id)
    return {
        "project_id": project_id,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
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
