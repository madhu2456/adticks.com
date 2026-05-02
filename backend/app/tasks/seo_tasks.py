"""SEO Celery tasks — full implementation."""
import hashlib
import logging
import uuid
from uuid import UUID
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete

from app.core.celery_app import celery_app
from app.core.celery_utils import run_async
from app.core.database import AsyncSessionLocal, engine
from app.core.storage import StorageService
from app.core.progress import ScanProgress, ScanStage
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
from app.services.seo.backlink_analyzer import sync_backlinks as backlinks_sync
from app.services.seo.competitor_research import sync_competitor_keywords as competitor_keywords_sync
from app.services.gsc.gsc_service import sync_gsc_data as gsc_sync
from app.services.ads.ads_service import sync_ads_data as ads_sync
from app.core.component_cache import ComponentCache
from app.core.logging import get_logger

logger = get_logger(__name__)
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
    parent_task_id: str | None = None,
) -> dict:
    """Generate keywords + clusters for a project, persist to DB and Spaces."""
    async def _run():
        try:
            return await _generate_keywords_impl(
                project_id, domain, industry, seed_keywords or [], 
                parent_task_id or self.request.id
            )
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("generate_keywords_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _generate_keywords_impl(
    project_id: str,
    domain: str,
    industry: str,
    seed_keywords: list,
    task_id: str,
) -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # Don't initialize again if it's a parent task
    if task_id == project_id: # or some other logic
        await progress.initialize()
    
    logger.info(
        "Generating keywords for project=%s domain=%s industry=%s seeds=%s",
        project_id, domain, industry, seed_keywords,
    )
    await progress.update(ScanStage.KEYWORD_GENERATION, 5, "⏳ Initializing keyword generation...")

    async with AsyncSessionLocal() as session:
        # Load project for brand context
        project = await _load_project(session, project_id)
        if project:
            domain = project.domain or domain
            industry = project.industry or industry
            logger.info("Using project context: domain=%s industry=%s", domain, industry)

        await progress.update(ScanStage.KEYWORD_GENERATION, 15, f"🤖 Generating keywords for {industry}...")
        # Call service
        keywords_raw = await generate_keywords(domain, industry, seed_keywords)
        logger.info("Service returned %d keywords", len(keywords_raw))
        await progress.update(ScanStage.KEYWORD_GENERATION, 35, f"✅ Generated {len(keywords_raw)} keywords • Processing...")

        # Upsert keywords into DB
        kw_objects = []
        new_count = 0
        duplicate_count = 0
        for idx, kw_data in enumerate(keywords_raw):
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
                new_count += 1
            else:
                duplicate_count += 1
            
            # Show progress every 10 keywords
            if (idx + 1) % 10 == 0:
                progress_pct = 35 + int((idx + 1) / len(keywords_raw) * 20)
                await progress.update(ScanStage.KEYWORD_GENERATION, progress_pct, f"📥 Processed {idx+1}/{len(keywords_raw)} • {new_count} new, {duplicate_count} duplicates")

        await session.flush()
        keywords_count = len(keywords_raw)

        # Cluster keywords
        await progress.update(ScanStage.KEYWORD_GENERATION, 60, f"Clustering {keywords_count} keywords...")
        clusters_raw = cluster_keywords(keywords_raw)
        logger.info("Clustered into %d groups", len(clusters_raw))

        # Clear old clusters and store new ones
        await session.execute(
            delete(Cluster).where(Cluster.project_id == project_id)
        )
        
        # We need to map keyword text to their objects to set cluster_id
        # Reloading all keywords for this project to be sure
        kw_result = await session.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        db_keywords = {kw.keyword: kw for kw in kw_result.scalars().all()}

        for cluster_idx, cluster_kws in clusters_raw.items():
            if not cluster_kws:
                continue
            
            # Use the most common word in the cluster as the topic name
            # Or use AI to generate a better topic name if available
            # For now, taking the first keyword's first word or the whole keyword if short
            representative_kw = cluster_kws[0].get("keyword", "")
            topic_name = representative_kw.split()[0].title() if " " in representative_kw else representative_kw.title()
            
            new_cluster = Cluster(
                id=uuid.uuid4(),
                project_id=UUID(project_id),
                topic_name=topic_name,
                keywords=[kw.get("keyword") for kw in cluster_kws],
            )
            session.add(new_cluster)
            await session.flush() # Get the new_cluster.id

            # Update Keyword records with the new cluster_id
            for kw_data in cluster_kws:
                kw_text = kw_data.get("keyword")
                if kw_text in db_keywords:
                    db_keywords[kw_text].cluster_id = new_cluster.id

        await session.commit()
        
        # Cache keywords and clusters
        await progress.update(ScanStage.KEYWORD_GENERATION, 80, "Caching keywords...")
        try:
            component_cache = ComponentCache(project_id)
            await component_cache.cache_keywords(keywords_raw, list(clusters_raw.values()))
        except Exception as e:
            logger.warning(f"Error caching keywords: {e}")

        # Store to Spaces
        await progress.update(ScanStage.KEYWORD_GENERATION, 90, "Uploading to storage...")
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

        await progress.complete()
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
def run_rank_tracking_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Check SERP rankings for all project keywords and persist results."""
    async def _run():
        try:
            return await _run_rank_tracking_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("run_rank_tracking_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _run_rank_tracking_impl(project_id: str, task_id: str) -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # logger.debug(f"Rank tracking using task_id {task_id}")
    
    logger.info("Running rank tracking for project=%s", project_id)
    await progress.update(ScanStage.RANK_TRACKING, 5, "⏳ Loading project and keywords...")

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            logger.warning("Project %s not found", project_id)
            return {"project_id": project_id, "keywords_checked": 0, "status": "project_not_found"}

        domain = project.domain
        logger.info("Using domain: %s", domain)

        kw_result = await session.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        keywords = kw_result.scalars().all()
        logger.info("Loaded %d keywords for ranking check", len(keywords))
        await progress.update(ScanStage.RANK_TRACKING, 10, f"📊 Loaded {len(keywords)} keywords • Domain: {domain}")

        if not keywords:
            await progress.complete()
            return {"project_id": project_id, "keywords_checked": 0, "status": "no_keywords"}

        # Build list for bulk_rank_check
        kw_dicts = [{"id": str(kw.id), "keyword": kw.keyword} for kw in keywords]

        await progress.update(ScanStage.RANK_TRACKING, 15, f"🔍 Checking SERP positions for {len(keywords)} keywords...")
        logger.info("Starting bulk rank check with %d keywords", len(keywords))
        ranking_results = await bulk_rank_check(
            project_id=project_id,
            keywords=kw_dicts,
            domain=domain,
            concurrency=5,  # Reduced from 10 for better stability
        )
        logger.info("Completed ranking check: %d results", len(ranking_results))

        await progress.update(ScanStage.RANK_TRACKING, 75, f"💾 Persisting {len(ranking_results)} ranking records...")
        # Persist Ranking rows
        for idx, res in enumerate(ranking_results):
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
            # Show progress during batch inserts
            if (idx + 1) % 25 == 0:
                progress_pct = 75 + int((idx + 1) / len(ranking_results) * 15)
                await progress.update(ScanStage.RANK_TRACKING, progress_pct, f"💾 Saved {idx + 1}/{len(ranking_results)} records...")

        await session.commit()
        logger.info("Persisted all ranking records")
        
        # Invalidate API caches
        from app.core.caching import invalidate_cache
        try:
            await invalidate_cache(f"cache:get_rankings:{project_id}:*")
            await invalidate_cache(f"cache:get_sov_stats:{project_id}*")
            await invalidate_cache(f"cache:get_rank_history:{project_id}:*")
            logger.info("Invalidated API caches for project %s", project_id)
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)
        
        # Cache rankings in ComponentCache
        await progress.update(ScanStage.RANK_TRACKING, 92, "⚡ Caching rankings in Redis...")
        try:
            component_cache = ComponentCache(project_id)
            await component_cache.cache_rankings(ranking_results)
            logger.info("Cached rankings successfully")
        except Exception as e:
            logger.warning(f"Error caching rankings: {e}")

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

        await progress.complete()
        return {
            "project_id": project_id,
            "keywords_checked": len(ranking_results),
            "status": "completed",
        }


# ---------------------------------------------------------------------------
# run_seo_audit_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, time_limit=1800, soft_time_limit=1500)
def run_seo_audit_task(self, project_id: str, url: str | None = None, parent_task_id: str | None = None) -> dict:
    """Run full SEO audit (on-page + technical)."""
    async def _run():
        try:
            return await _run_seo_audit_impl(project_id, url, audit_type="full", task_id=parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("run_seo_audit_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_seo_onpage_task(self, project_id: str, url: str, parent_task_id: str | None = None) -> dict:
    """Run on-page SEO audit only."""
    async def _run():
        try:
            return await _run_seo_audit_impl(project_id, url, audit_type="on_page", task_id=parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("run_seo_onpage_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_seo_technical_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Run technical SEO audit only."""
    async def _run():
        try:
            return await _run_seo_audit_impl(project_id, None, audit_type="technical", task_id=parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("run_seo_technical_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _run_seo_audit_impl(project_id: str, url: str | None, audit_type: str = "full", task_id: str = "") -> dict:
    try:
        return await _run_seo_audit_impl_inner(project_id, url, audit_type, task_id)
    except Exception as e:
        import traceback
        logger.error(f"DETAILED SEO AUDIT FAILURE for project {project_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def _run_seo_audit_impl_inner(project_id: str, url: str | None, audit_type: str = "full", task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # await progress.initialize() # Don't initialize if part of chain
    
    audit_stage = ScanStage.ON_PAGE_ANALYSIS if audit_type in ["on_page", "full"] else ScanStage.TECHNICAL_AUDIT
    await progress.update(audit_stage, 5, f"⏳ Initializing {audit_type} audit...")
    
    logger.info("Running SEO audit type=%s for project=%s url=%s", audit_type, project_id, url)

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        domain = project.domain if project else (url or "")

    target_url = url or f"https://{domain}"
    url_hash = hashlib.md5(target_url.encode()).hexdigest()[:12]
    logger.info("Audit target: %s", target_url)

    on_page = {}
    technical = {}

    def _ensure_dict(val: Any) -> Dict[str, Any]:
        if isinstance(val, dict):
            return val
        return {}

    # Load existing cached audit to merge if doing partial audit
    await progress.update(audit_stage, 15, "📂 Loading previous audit results...")
    try:
        component_cache = ComponentCache(project_id)
        cached_audit = await component_cache.get_cached_audit()
        if cached_audit and isinstance(cached_audit, dict):
            on_page = _ensure_dict(cached_audit.get("on_page", {}))
            technical = _ensure_dict(cached_audit.get("technical", {}))
            logger.info("Loaded cached audit data")
    except Exception as e:
        logger.warning(f"Error loading cached audit for merge: {e}")

    # Run requested checks
    if audit_type in ("full", "on_page"):
        await progress.update(ScanStage.ON_PAGE_ANALYSIS, 35, f"🔍 Analyzing page elements • URL: {target_url[:50]}...")
        logger.info("Starting on-page analysis for %s", target_url)
        raw_on_page = await analyze_url(target_url)
        on_page = _ensure_dict(raw_on_page)
        logger.info(f"On-page analysis complete (type: {type(on_page)}): {len(on_page.get('issues', []))} issues found")
    
    if audit_type in ("full", "technical"):
        await progress.update(ScanStage.TECHNICAL_AUDIT, 60, f"⚙️ Running technical checks • Domain: {domain}")
        logger.info("Starting technical audit for %s", domain)
        raw_tech = await check_technical(domain)
        technical = _ensure_dict(raw_tech)
        logger.info(f"Technical audit complete (type: {type(technical)}): {len(technical.get('issues', []))} issues found")

    if audit_type == "full":
        await progress.update(ScanStage.BACKLINK_ANALYSIS, 75, f"🔗 Analyzing backlink profile...")
        try:
            await backlinks_sync(project_id, domain)
            logger.info("Backlink sync complete")
        except Exception as e:
            logger.warning(f"Backlink sync failed: {e}")

    await progress.update(audit_stage, 82, "📊 Compiling audit report...")
    audit = {
        "project_id": project_id,
        "domain": domain,
        "url": target_url,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "on_page": on_page,
        "technical": technical,
        "overall_score": (
            (on_page.get("overall_score", 0) + technical.get("health_score", 0)) // 2
        ),
        "total_issues": (
            on_page.get("issues_count", len(on_page.get("issues", [])))
            + technical.get("issues_count", 0)
        ),
    }
    
    # Cache audit results
    await progress.update(audit_stage, 90, "Caching audit results...")
    try:
        component_cache = ComponentCache(project_id)
        await component_cache.cache_audit(on_page, technical)
        
        # Invalidate API caches
        from app.core.caching import invalidate_cache
        await invalidate_cache(f"cache:get_onpage_audit:{project_id}*")
        await invalidate_cache(f"cache:get_technical_seo:{project_id}*")
        logger.info("Invalidated audit API caches for project %s", project_id)
    except Exception as e:
        logger.warning(f"Error caching audit or invalidating: {e}")

    try:
        storage.upload_json(
            StorageService.seo_path(project_id, f"audits/{url_hash}.json"),
            audit,
        )
        logger.info("Uploaded audit to Spaces for project %s url_hash %s", project_id, url_hash)
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    # Persist to SiteAuditHistory table
    from app.models.seo import SiteAuditHistory
    async with AsyncSessionLocal() as db:
        history = SiteAuditHistory(
            id=uuid.uuid4(),
            project_id=UUID(project_id),
            url=target_url,
            score=audit["overall_score"],
            total_errors=sum(1 for i in on_page.get("issues", []) if isinstance(i, dict) and i.get("severity") == "error") + 
                         sum(1 for i in technical.get("all_issues", []) if isinstance(i, str) and "CRITICAL" in i.upper()),
            total_warnings=sum(1 for i in on_page.get("issues", []) if isinstance(i, dict) and i.get("severity") == "warning") +
                           sum(1 for i in on_page.get("issues", []) if isinstance(i, str) and "CRITICAL" not in i.upper()) +
                           sum(1 for i in technical.get("all_issues", []) if isinstance(i, str) and "CRITICAL" not in i.upper()),
            pages_crawled=1, # Initial basic crawler
            crawl_depth=1,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)
        await db.commit()

    await progress.complete()
    return {
        "project_id": project_id,
        "url": target_url,
        "overall_score": audit["overall_score"],
        "total_issues": audit["total_issues"],
        "on_page_score": on_page.get("overall_score", 0),
        "technical_score": technical.get("health_score", 0),
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# find_content_gaps_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def find_content_gaps_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Identify content gaps vs competitors and persist results to Spaces."""
    try:
        return run_async(_find_content_gaps_impl(project_id, parent_task_id or self.request.id))
    except Exception as exc:
        logger.exception("find_content_gaps_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _find_content_gaps_impl(project_id: str, task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # await progress.initialize()
    
    logger.info("Finding content gaps for project=%s", project_id)
    await progress.update(ScanStage.GAP_ANALYSIS, 10, "Loading keywords and competitors...")

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            logger.warning("Project %s not found", project_id)
            await progress.complete()
            return {"project_id": project_id, "gaps_found": 0, "status": "project_not_found"}

        kw_result = await session.execute(
            select(Keyword).where(Keyword.project_id == project_id)
        )
        keywords = kw_result.scalars().all()

        competitors = await _load_competitors(session, project_id)

    await progress.update(ScanStage.GAP_ANALYSIS, 30, f"Analyzing {len(keywords)} keywords...")
    project_kw_texts = [kw.keyword for kw in keywords]
    competitor_domains = [c.domain for c in competitors]

    gaps = await find_gaps(
        project_keywords=project_kw_texts,
        competitor_domains=competitor_domains,
        industry=project.industry,
        brand_name=project.brand_name,
    )
    logger.info("Found %d content gaps", len(gaps))
    
    # Cache gaps
    try:
        component_cache = ComponentCache(project_id)
        await component_cache.cache_gaps(gaps)
    except Exception as e:
        logger.warning(f"Error caching gaps: {e}")

    # --- ADDED: Sync competitor keywords as well ---
    if competitor_domains:
        await progress.update(ScanStage.GAP_ANALYSIS, 80, f"🔍 Researching competitor keywords...")
        try:
            await competitor_keywords_sync(project_id, competitor_domains, project.industry or "Technology")
            
            # Invalidate cache
            from app.core.caching import invalidate_cache
            await invalidate_cache(f"cache:get_competitor_keywords:{project_id}*")
            logger.info("Sync'd competitor keywords during gap analysis")
        except Exception as e:
            logger.warning(f"Failed to sync competitor keywords: {e}")

    payload = {
        "project_id": project_id,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "project_keyword_count": len(project_kw_texts),
        "competitor_count": len(competitor_domains),
        "gaps": gaps,
    }
    
    await progress.update(ScanStage.GAP_ANALYSIS, 90, "Uploading results to storage...")
    try:
        storage.upload_json(
            StorageService.seo_path(project_id, "content_gaps.json"),
            payload,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    await progress.complete()
    return {
        "project_id": project_id,
        "gaps_found": len(gaps),
        "top_gap": gaps[0].get("topic") if gaps else None,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# sync_backlinks_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_backlinks_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Sync backlinks for a project and persist to DB."""
    async def _run():
        try:
            return await _sync_backlinks_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("sync_backlinks_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _sync_backlinks_impl(project_id: str, task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    
    logger.info("Syncing backlinks for project=%s", project_id)
    await progress.update(ScanStage.BACKLINK_ANALYSIS, 10, "⏳ Loading project data...")

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            await progress.complete()
            return {"project_id": project_id, "links_synced": 0, "status": "project_not_found"}
        domain = project.domain

    await progress.update(ScanStage.BACKLINK_ANALYSIS, 30, f"🔍 Analyzing backlinks for {domain}...")
    
    # Call service
    links_count = await backlinks_sync(project_id, domain)
    
    # Invalidate API caches
    from app.core.caching import invalidate_cache
    try:
        await invalidate_cache(f"cache:get_backlinks:{project_id}*")
        await invalidate_cache(f"cache:get_backlinks_stats:{project_id}*")
        logger.info("Invalidated backlink API caches for project %s", project_id)
    except Exception as e:
        logger.warning(f"Error invalidating backlink caches: {e}")

    await progress.complete()
    return {
        "project_id": project_id,
        "links_synced": links_count,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# import_gsc_keywords_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def import_gsc_keywords_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Import search queries from GSC data as keywords for tracking."""
    async def _run():
        try:
            return await _import_gsc_keywords_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("import_gsc_keywords_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _import_gsc_keywords_impl(project_id: str, task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # await progress.initialize()
    
    logger.info("Importing GSC queries as keywords for project=%s", project_id)
    await progress.update(ScanStage.KEYWORD_GENERATION, 10, "📂 Loading GSC data...")

    async with AsyncSessionLocal() as session:
        # Get all unique queries from GSCData for this project
        result = await session.execute(
            select(GSCData.query)
            .where(GSCData.project_id == project_id)
            .distinct()
        )
        gsc_queries = [r[0] for r in result.all() if r[0]]
        logger.info("Found %d unique GSC queries", len(gsc_queries))
        
        if not gsc_queries:
            logger.warning("No GSC data found for project %s", project_id)
            await progress.complete()
            return {
                "project_id": project_id,
                "keywords_imported": 0,
                "status": "no_gsc_data",
                "message": "No GSC data found. Run GSC sync first."
            }

        await progress.update(ScanStage.KEYWORD_GENERATION, 25, f"🔄 Checking {len(gsc_queries)} GSC queries for duplicates...")
        # Get existing keywords to avoid duplicates
        result = await session.execute(
            select(Keyword.keyword)
            .where(Keyword.project_id == project_id)
        )
        existing_kws = {r[0].lower() for r in result.all()}
        logger.info("Found %d existing keywords in database", len(existing_kws))
        
        new_kws_count = 0
        for i, query in enumerate(gsc_queries):
            if query.lower() not in existing_kws:
                new_kw = Keyword(
                    id=uuid.uuid4(),
                    project_id=UUID(project_id),
                    keyword=query,
                    intent="informational", # Default intent
                    difficulty=20.0,        # Lower default for found keywords
                    volume=0,               # GSC doesn't give global volume
                )
                session.add(new_kw)
                new_kws_count += 1
                # To prevent memory issues with thousands of keywords
                if new_kws_count % 100 == 0:
                    await session.flush()
                    progress_pct = min(80, 30 + int((i / len(gsc_queries)) * 50))
                    await progress.update(ScanStage.KEYWORD_GENERATION, progress_pct, f"Processed {i+1}/{len(gsc_queries)} queries...")

        await progress.update(ScanStage.KEYWORD_GENERATION, 90, "Committing new keywords...")
        await session.commit()
        logger.info("Imported %d new keywords from GSC for project %s", new_kws_count, project_id)

    await progress.complete()
    return {
        "project_id": project_id,
        "keywords_imported": new_kws_count,
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# sync_gsc_data_task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_gsc_data_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Pull GSC data, upsert into DB, and archive raw data to Spaces."""
    async def _run():
        try:
            return await _sync_gsc_data_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("sync_gsc_data_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _sync_gsc_data_impl(project_id: str, task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # await progress.initialize()
    
    logger.info("Syncing GSC data for project=%s", project_id)
    await progress.update("gsc_sync", 10, "Loading project data...")

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            await progress.complete()
            return {"project_id": project_id, "rows_synced": 0, "status": "project_not_found"}

        competitors = await _load_competitors(session, project_id)
        competitor_names = [c.domain for c in competitors]

    await progress.update("gsc_sync", 30, "Fetching GSC queries...")
    sync_result = await gsc_sync(
        project_id=project_id,
        brand_name=project.brand_name,
        industry=project.industry or "Technology",
        competitors=competitor_names,
    )

    queries = sync_result.get("queries", [])
    logger.info("GSC returned %d query rows", len(queries))

    await progress.update("gsc_sync", 60, f"Uploading {len(queries)} query records...")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        storage.upload_json(
            StorageService.gsc_path(project_id, f"raw/{date_str}.json"),
            sync_result,
        )
    except Exception as exc:
        logger.warning("Spaces upload failed (non-fatal): %s", exc)

    await progress.update("gsc_sync", 75, "Persisting to database...")
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

    await progress.complete()
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
def sync_ads_data_task(self, project_id: str, parent_task_id: str | None = None) -> dict:
    """Pull Ads performance data, upsert into DB, and archive to Spaces."""
    async def _run():
        try:
            return await _sync_ads_data_impl(project_id, parent_task_id or self.request.id)
        finally:
            await engine.dispose()
    try:
        return run_async(_run())
    except Exception as exc:
        logger.exception("sync_ads_data_task failed for project %s: %s", project_id, exc)
        raise self.retry(exc=exc)


async def _sync_ads_data_impl(project_id: str, task_id: str = "") -> dict:
    # Initialize progress tracking
    progress = ScanProgress(project_id, task_id)
    # await progress.initialize()
    
    logger.info("Syncing Ads data for project=%s", project_id)
    await progress.update("ads_sync", 10, "Loading project data...")

    async with AsyncSessionLocal() as session:
        project = await _load_project(session, project_id)
        if not project:
            await progress.complete()
            return {"project_id": project_id, "rows_synced": 0, "status": "project_not_found"}

        brand_name = project.brand_name
        industry = project.industry or "Technology"

    sync_result = await ads_sync(
        project_id=project_id,
        brand_name=brand_name,
        industry=industry,
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
        brand_name=brand_name,
        industry=industry,
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
