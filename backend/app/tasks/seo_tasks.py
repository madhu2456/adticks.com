"""SEO Celery tasks — full implementation."""
import asyncio
import hashlib
import logging
import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, delete

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.storage import StorageService
from app.models.cluster import Cluster
from app.models.keyword import Keyword, Ranking
from app.models.project import Project
from app.models.competitor import Competitor
from app.models.gsc import GSCData
from app.models.ads import AdsData
from app.services.seo.keyword_service import generate_keywords, cluster_keywords
from app.services.seo.rank_tracker import bulk_rank_check
from app.services.seo.on_page_analyzer import analyze_url
from app.services.seo.technical_seo import check_technical
from app.services.seo.content_gap_analyzer import find_gaps
from app.services.gsc.gsc_service import sync_gsc_data as gsc_sync
from app.services.ads.ads_service import sync_ads_data as ads_sync

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
# generate_keywords_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, time_limit=1800, soft_time_limit=1500)
def generate_keywords_task(
    self,
    project_id: str,
    domain: str,
    industry: str,
    seed_keywords: list | None = None,
) -> dict:
    """Generate keywords + clusters for a project, persist to DB and Spaces.
    
    Task timeout: 30 minutes (soft 25 minutes)
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_keywords_impl(project_id, domain, industry, seed_keywords or [])
        )
        loop.close()
        return result
    except Exception as exc:
        logger.exception("generate_keywords_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _generate_keywords_impl(
    project_id: str,
    domain: str,
    industry: str,
    seed_keywords: list,
) -> dict:
    logger.info(
        "Generating keywords for project=%s domain=%s industry=%s seeds=%s",
        project_id, domain, industry, seed_keywords,
    )

    async with AsyncSessionLocal() as session:
        # Load project for brand context
        project = await _load_project(session, project_id)
        if project:
            domain = project.domain or domain
            industry = project.industry or industry

        # Call service
        keywords_raw = await generate_keywords(domain, industry, seed_keywords)
        logger.info("Service returned %d keywords", len(keywords_raw))

        # Upsert keywords into DB
        kw_objects = []
        for kw_data in keywords_raw:
            text = kw_data.get("keyword", "").strip()
            if not text:
                continue
            # Check for existing
            existing = await session.execute(
                select(Keyword).where(
                    Keyword.project_id == project_id,
                    Keyword.keyword == text,
                )
            )
            existing_kw = existing.scalar_one_or_none()
            if existing_kw is None:
                new_kw = Keyword(
                    id=uuid.uuid4(),
                    project_id=UUID(project_id),
                    keyword=text,
                    intent=kw_data.get("intent"),
                    difficulty=float(kw_data.get("difficulty", 50)),
                    volume=int(kw_data.get("volume", 0)),
                )
                session.add(new_kw)
                kw_objects.append(new_kw)

        await session.flush()
        keywords_count = len(keywords_raw)

        # Cluster keywords
        clusters_raw = cluster_keywords(keywords_raw)
        logger.info("Clustered into %d groups", len(clusters_raw))

        # Clear old clusters and store new ones
        await session.execute(
            delete(Cluster).where(Cluster.project_id == project_id)
        )
        for cluster_id, cluster_kws in clusters_raw.items():
            if not cluster_kws:
                continue
            # Use the most common word in the cluster as the topic name
            topic_name = cluster_kws[0].get("keyword", f"cluster_{cluster_id}").split()[0].title()
            new_cluster = Cluster(
                id=uuid.uuid4(),
                project_id=UUID(project_id),
                topic_name=topic_name,
                keywords=[kw.get("keyword") for kw in cluster_kws],
            )
            session.add(new_cluster)

        await session.commit()

        # Store to Spaces
        payload = {
            "project_id": project_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "keywords": keywords_raw,
            "clusters": {
                str(k): [kw.get("keyword") for kw in v]
                for k, v in clusters_raw.items()
            },
        }
        try:
            storage.upload_json(StorageService.seo_path(project_id, "keywords.json"), payload)
            logger.info("Uploaded keywords.json to Spaces for project %s", project_id)
        except Exception as exc:
            logger.warning("Spaces upload failed (non-fatal): %s", exc)

        return {
            "project_id": project_id,
            "keywords_generated": keywords_count,
            "keywords_upserted": len(kw_objects),
            "clusters": len(clusters_raw),
            "status": "completed",
        }


# ---------------------------------------------------------------------------
# run_rank_tracking_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, time_limit=2700, soft_time_limit=2400)
def run_rank_tracking_task(self, project_id: str) -> dict:
    """Check SERP rankings for all project keywords and persist results.
    
    Task timeout: 45 minutes (soft 40 minutes)
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run_rank_tracking_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("run_rank_tracking_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _run_rank_tracking_impl(project_id: str) -> dict:
    logger.info("Running rank tracking for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            logger.warning("Project %s not found", project_id)
            return {"project_id": project_id, "keywords_checked": 0, "status": "project_not_found"}

        domain = project.domain

        kw_result = await session.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        keywords = kw_result.scalars().all()
        logger.info("Loaded %d keywords for ranking check", len(keywords))

        if not keywords:
            return {"project_id": project_id, "keywords_checked": 0, "status": "no_keywords"}

        # Build list for bulk_rank_check
        kw_dicts = [{"id": str(kw.id), "keyword": kw.keyword} for kw in keywords]

        ranking_results = await bulk_rank_check(
            project_id=project_id,
            keywords=kw_dicts,
            domain=domain,
            concurrency=10,  # Increased from default 5 for better performance
        )

        # Persist Ranking rows
        for res in ranking_results:
            kw_id = res.get("keyword_id")
            if not kw_id:
                continue
            ranking = Ranking(
                id=uuid.uuid4(),
                keyword_id=kw_id,
                position=res.get("position"),
                url=res.get("url"),
                timestamp=datetime.now(timezone.utc),
            )
            session.add(ranking)

        await session.commit()

        # Store to Spaces
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        payload = {
            "project_id": project_id,
            "domain": domain,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "results": ranking_results,
        }
        try:
            storage.upload_json(
                StorageService.seo_path(project_id, f"rankings/{date_str}.json"),
                payload,
            )
        except Exception as exc:
            logger.warning("Spaces upload failed (non-fatal): %s", exc)

        return {
            "project_id": project_id,
            "keywords_checked": len(ranking_results),
            "status": "completed",
        }


# ---------------------------------------------------------------------------
# run_seo_audit_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, time_limit=1800, soft_time_limit=1500)
def run_seo_audit_task(self, project_id: str, url: str | None = None) -> dict:
    """Run on-page + technical SEO audit and persist results to Spaces.
    
    Task timeout: 30 minutes (soft 25 minutes)
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run_seo_audit_impl(project_id, url))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("run_seo_audit_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _run_seo_audit_impl(project_id: str, url: str | None) -> dict:
    logger.info("Running SEO audit for project=%s url=%s", project_id, url)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        domain = project.domain if project else (url or "")

    target_url = url or f"https://{domain}"
    url_hash = hashlib.md5(target_url.encode()).hexdigest()[:12]

    # Run on-page analysis
    on_page = await analyze_url(target_url)
    # Run technical SEO check
    technical = await check_technical(domain)

    audit = {
        "project_id": project_id,
        "domain": domain,
        "url": target_url,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "on_page": on_page,
        "technical": technical,
        "overall_score": (
            (on_page.get("score", 0) + technical.get("score", 0)) // 2
        ),
        "total_issues": (
            on_page.get("issues_count", len(on_page.get("issues", [])))
            + len(technical.get("issues", []))
        ),
    }

    try:
        storage.upload_json(
            StorageService.seo_path(project_id, f"audits/{url_hash}.json"),
            audit,
        )
        logger.info("Uploaded audit to Spaces for project %s url_hash %s", project_id, url_hash)
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    return {
        "project_id": project_id,
        "url": target_url,
        "overall_score": audit["overall_score"],
        "total_issues": audit["total_issues"],
        "on_page_score": on_page.get("score", 0),
        "technical_score": technical.get("score", 0),
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# find_content_gaps_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def find_content_gaps_task(self, project_id: str) -> dict:
    """Identify content gaps vs competitors and persist results to Spaces."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_find_content_gaps_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("find_content_gaps_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _find_content_gaps_impl(project_id: str) -> dict:
    logger.info("Finding content gaps for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            logger.warning("Project %s not found", project_id)
            return {"project_id": project_id, "gaps_found": 0, "status": "project_not_found"}

        kw_result = await session.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        keywords = kw_result.scalars().all()

        competitors = await _load_competitors(session, project_id)

    project_kw_texts = [kw.keyword for kw in keywords]
    competitor_domains = [c.domain for c in competitors]

    gaps = await find_gaps(
        project_keywords=project_kw_texts,
        competitor_domains=competitor_domains,
        industry=project.industry,
        brand_name=project.brand_name,
    )
    logger.info("Found %d content gaps", len(gaps))

    payload = {
        "project_id": project_id,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "project_keyword_count": len(project_kw_texts),
        "competitor_count": len(competitor_domains),
        "gaps": gaps,
    }
    try:
        storage.upload_json(
            StorageService.seo_path(project_id, "content_gaps.json"),
            payload,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    return {
        "project_id": project_id,
        "gaps_found": len(gaps),
        "top_gap": gaps[0].get("topic") if gaps else None,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# sync_gsc_data_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_gsc_data_task(self, project_id: str) -> dict:
    """Pull GSC data, upsert into DB, and archive raw data to Spaces."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_sync_gsc_data_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("sync_gsc_data_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _sync_gsc_data_impl(project_id: str) -> dict:
    logger.info("Syncing GSC data for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return {"project_id": project_id, "rows_synced": 0, "status": "project_not_found"}

        competitors = await _load_competitors(session, project_id)
        competitor_names = [c.domain for c in competitors]

    sync_result = await gsc_sync(
        project_id=project_id,
        brand_name=project.brand_name,
        industry=project.industry or "Technology",
        competitors=competitor_names,
    )

    queries = sync_result.get("queries", [])
    logger.info("GSC returned %d query rows", len(queries))

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        storage.upload_json(
            StorageService.gsc_path(project_id, f"raw/{date_str}.json"),
            sync_result,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    # Upsert into GSCData table
    async with AsyncSessionLocal() as session:
        today = datetime.now(timezone.utc).date()
        for row in queries:
            gsc_row = GSCData(
                id=uuid.uuid4(),
                project_id=UUID(project_id),
                query=row.get("query"),
                clicks=row.get("clicks"),
                impressions=row.get("impressions"),
                ctr=row.get("ctr"),
                position=row.get("position"),
                date=today,
            )
            session.add(gsc_row)
        await session.commit()
        logger.info("Inserted %d GSCData rows for project %s", len(queries), project_id)

    return {
        "project_id": project_id,
        "rows_synced": len(queries),
        "summary": sync_result.get("summary", {}),
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# sync_ads_data_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_ads_data_task(self, project_id: str) -> dict:
    """Pull Ads performance data, upsert into DB, and archive to Spaces."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_sync_ads_data_impl(project_id))
        loop.close()
        return result
    except Exception as exc:
        logger.exception("sync_ads_data_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _sync_ads_data_impl(project_id: str) -> dict:
    logger.info("Syncing Ads data for project=%s", project_id)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            return {"project_id": project_id, "rows_synced": 0, "status": "project_not_found"}

    sync_result = await ads_sync(
        project_id=project_id,
        brand_name=project.brand_name,
        industry=project.industry or "Technology",
    )

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        storage.upload_json(
            StorageService.ads_path(project_id, f"reports/{date_str}.json"),
            sync_result,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    # Upsert daily_data rows into AdsData table
    daily_rows = []
    # The full performance object is not returned from sync_ads_data — re-call get_performance
    from app.services.ads.ads_service import get_performance
    perf = await get_performance(
        project_id=project_id,
        brand_name=project.brand_name,
        industry=project.industry or "Technology",
        days=30,
    )

    async with AsyncSessionLocal() as session:
        today = datetime.now(timezone.utc).date()
        for row in perf.get("daily_data", []):
            from datetime import date as date_type
            row_date_str = row.get("date")
            try:
                row_date = date_type.fromisoformat(row_date_str) if row_date_str else today
            except (ValueError, TypeError):
                row_date = today
            ads_row = AdsData(
                id=uuid.uuid4(),
                project_id=UUID(project_id),
                campaign=row.get("campaign_id"),
                clicks=row.get("clicks"),
                cpc=row.get("avg_cpc_usd"),
                conversions=int(row.get("conversions", 0)),
                spend=row.get("spend_usd"),
                date=row_date,
            )
            session.add(ads_row)
            daily_rows.append(ads_row)
        await session.commit()
        logger.info("Inserted %d AdsData rows for project %s", len(daily_rows), project_id)

    return {
        "project_id": project_id,
        "rows_synced": len(daily_rows),
        "campaigns_synced": len(perf.get("campaigns", [])),
        "summary": perf.get("summary", {}),
        "status": "completed",
    }
