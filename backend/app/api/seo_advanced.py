"""
AdTicks — Advanced SEO API router.

Wires every new service in app.services.seo.* (site crawler, Core Web Vitals,
keyword magic, SERP analyzer, backlink intelligence, content optimizer,
local SEO, log analyzer, report generator) to HTTP endpoints under
/api/seo/*. All endpoints scoped to a project owned by the current user.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, BackgroundTasks
from sqlalchemy import select, func, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.models.keyword import Keyword
from app.models.seo import Backlinks
from app.models.competitor import Competitor
from app.models.seo_advanced import (
    SiteAuditIssue,
    CrawledPage,
    CoreWebVitals,
    SchemaMarkup,
    AnchorText,
    ToxicBacklink,
    LinkIntersect,
    KeywordIdea,
    SerpOverview,
    ContentBrief,
    ContentOptimizerScore,
    TopicCluster,
    LocalCitation,
    LocalRankGrid,
    LogEvent,
    GeneratedReport,
)
from app.schemas.seo_advanced import (
    SiteAuditIssueResponse,
    CrawledPageResponse,
    SiteAuditTriggerRequest,
    SiteAuditSummary,
    CoreWebVitalsResponse,
    SchemaMarkupResponse,
    AnchorTextResponse,
    ToxicBacklinkResponse,
    LinkIntersectResponse,
    KeywordIdeaResponse,
    KeywordMagicRequest,
    SerpOverviewResponse,
    ContentBriefRequest,
    ContentBriefResponse,
    ContentOptimizerRequest,
    ContentOptimizerResponse,
    TopicClusterResponse,
    LocalCitationResponse,
    LocalRankGridCell,
    LogEventResponse,
    ReportRequest,
    GeneratedReportResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/seo", tags=["seo-advanced"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_project_or_404(project_id: UUID, user: User, db: AsyncSession) -> Project:
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ===========================================================================
# Site Audit / Crawler
# ===========================================================================
@router.post(
    "/projects/{project_id}/audit/run",
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_site_audit(
    project_id: UUID,
    payload: SiteAuditTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a fresh site crawl + audit in the background. Persists pages + issues to the DB."""
    await _get_project_or_404(project_id, current_user, db)

    # Generate a task ID for tracking progress
    task_id = str(uuid.uuid4())
    from app.core.progress import ScanProgress, ScanStage
    progress = ScanProgress(str(project_id), task_id)
    await progress.initialize()

    async def _audit_task_impl():
        # Inner function to run in background
        from app.core.database import AsyncSessionLocal
        from app.services.seo.site_crawler import crawl_site
        from app.models.seo_advanced import SiteAuditIssue, CrawledPage, SchemaMarkup
        
        async def on_progress(percent: int, msg: str):
            logger.info(f"Audit progress for {project_id}: {percent}% - {msg}")
            await progress.update(ScanStage.TECHNICAL_AUDIT, percent, msg)

        logger.info(f"Starting background audit task for project {project_id} (task_id: {task_id})")
        async with AsyncSessionLocal() as session:
            try:
                await on_progress(1, "Initializing crawler...")
                result = await crawl_site(
                    payload.url, 
                    max_pages=payload.max_pages, 
                    max_depth=payload.max_depth,
                    stay_within_path=payload.stay_within_path,
                    on_progress=on_progress
                )
                
                await on_progress(90, "Saving audit results to database...")
                # clear previous unresolved issues for the same project
                async with session.begin():
                    await session.execute(delete(SiteAuditIssue).where(SiteAuditIssue.project_id == project_id))
                    await session.execute(delete(CrawledPage).where(CrawledPage.project_id == project_id))
                    await session.execute(delete(SchemaMarkup).where(SchemaMarkup.project_id == project_id))

                    audit_id = uuid.uuid4()
                    for page in result.pages:
                        session.add(CrawledPage(
                            project_id=project_id,
                            url=page.url,
                            status_code=page.status_code,
                            content_type=page.content_type,
                            title=page.title,
                            meta_description=page.meta_description,
                            h1=page.h1,
                            word_count=page.word_count,
                            internal_links=page.internal_links,
                            external_links=page.external_links,
                            images=page.images,
                            images_missing_alt=page.images_missing_alt,
                            canonical_url=page.canonical_url,
                            is_indexable=page.is_indexable,
                            response_time_ms=page.response_time_ms,
                            page_size_bytes=page.page_size_bytes,
                            depth=page.depth,
                            schema_types=page.schema_types,
                        ))
                    for issue in result.issues:
                        session.add(SiteAuditIssue(
                            project_id=project_id,
                            audit_id=audit_id,
                            url=issue.url,
                            category=issue.category,
                            severity=issue.severity,
                            code=issue.code,
                            message=issue.message,
                            recommendation=issue.recommendation,
                            details=issue.details,
                        ))
                    for sch in result.schemas:
                        session.add(SchemaMarkup(
                            project_id=project_id,
                            url=sch["url"],
                            schema_type=sch["type"],
                            raw_data=sch["data"] if isinstance(sch.get("data"), dict) else {},
                            is_valid=bool(sch.get("valid", True)),
                            validation_errors=[sch["error"]] if sch.get("error") else [],
                        ))
                
                await progress.complete()
                logger.info(f"Background audit successfully completed for project {project_id}")
            except Exception as e:
                await progress.update("failed", 0, f"Audit failed: {str(e)}")
                logger.exception(f"Background audit failed for project {project_id}: {e}")

    background_tasks.add_task(_audit_task_impl)
    
    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "Site audit started in background.",
    }


@router.get(
    "/projects/{project_id}/audit/summary",
    response_model=SiteAuditSummary,
)
async def get_audit_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    pages_count = (await db.execute(
        select(func.count(CrawledPage.id)).where(CrawledPage.project_id == project_id)
    )).scalar() or 0
    issues = (await db.execute(
        select(SiteAuditIssue).where(SiteAuditIssue.project_id == project_id)
    )).scalars().all()
    avg_rt = (await db.execute(
        select(func.avg(CrawledPage.response_time_ms)).where(CrawledPage.project_id == project_id)
    )).scalar() or 0.0
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    notices = sum(1 for i in issues if i.severity == "notice")
    cat_counts: dict[str, int] = {}
    for i in issues:
        cat_counts[i.category] = cat_counts.get(i.category, 0) + 1
    score = max(0, 100 - min(100, errors * 5 + warnings * 2 + notices))
    return SiteAuditSummary(
        total_pages=pages_count,
        total_issues=len(issues),
        errors=errors,
        warnings=warnings,
        notices=notices,
        avg_response_time_ms=float(avg_rt),
        score=score,
        issues_by_category=cat_counts,
    )


@router.get(
    "/projects/{project_id}/audit/issues",
    response_model=list[SiteAuditIssueResponse],
)
async def list_audit_issues(
    project_id: UUID,
    severity: str | None = None,
    category: str | None = None,
    urls: list[str] | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(SiteAuditIssue).where(SiteAuditIssue.project_id == project_id)
    if severity:
        q = q.where(SiteAuditIssue.severity == severity)
    if category:
        q = q.where(SiteAuditIssue.category == category)
    if urls:
        q = q.where(SiteAuditIssue.url.in_(urls))
    q = q.order_by(desc(SiteAuditIssue.discovered_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.get(
    "/projects/{project_id}/audit/pages",
    response_model=list[CrawledPageResponse],
)
async def list_crawled_pages(
    project_id: UUID,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(CrawledPage).where(CrawledPage.project_id == project_id).limit(limit)
    )).scalars().all()
    return rows


@router.get(
    "/projects/{project_id}/audit/schemas",
    response_model=list[SchemaMarkupResponse],
)
async def list_schemas(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(SchemaMarkup).where(SchemaMarkup.project_id == project_id)
    )).scalars().all()
    return rows


# ===========================================================================
# Core Web Vitals
# ===========================================================================
@router.post("/projects/{project_id}/cwv/run")
async def run_cwv(
    project_id: UUID,
    url: str = Query(..., description="URL to analyze"),
    strategy: str = Query("mobile", pattern="^(mobile|desktop)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.core_web_vitals import run_pagespeed
    psi_api_key = settings.PSI_API_KEY
    data = await run_pagespeed(url=url, strategy=strategy, api_key=psi_api_key)
    row = CoreWebVitals(
        project_id=project_id,
        url=data["url"],
        strategy=data["strategy"],
        lcp_ms=data["lcp_ms"],
        inp_ms=data["inp_ms"],
        cls=data["cls"],
        fcp_ms=data["fcp_ms"],
        ttfb_ms=data["ttfb_ms"],
        si_ms=data["si_ms"],
        tbt_ms=data["tbt_ms"],
        performance_score=data["performance_score"],
        seo_score=data["seo_score"],
        accessibility_score=data["accessibility_score"],
        best_practices_score=data["best_practices_score"],
        opportunities=data["opportunities"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return CoreWebVitalsResponse.model_validate(row)


@router.get(
    "/projects/{project_id}/cwv",
    response_model=list[CoreWebVitalsResponse],
)
async def list_cwv(
    project_id: UUID,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(CoreWebVitals)
        .where(CoreWebVitals.project_id == project_id)
        .order_by(desc(CoreWebVitals.timestamp))
        .limit(limit)
    )).scalars().all()
    return rows


# ===========================================================================
# Keyword Magic + SERP Analyzer
# ===========================================================================
@router.post(
    "/projects/{project_id}/keyword-magic",
    response_model=list[KeywordIdeaResponse],
)
async def keyword_magic(
    project_id: UUID,
    payload: KeywordMagicRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.keyword_magic import generate_ideas
    ideas = await generate_ideas(
        seed=payload.seed,
        location=payload.location,
        include_questions=payload.include_questions,
        limit=payload.limit,
    )
    rows: list[KeywordIdea] = []
    for idea in ideas:
        row = KeywordIdea(
            project_id=project_id,
            seed=idea["seed"],
            keyword=idea["keyword"],
            match_type=idea["match_type"],
            intent=idea["intent"],
            volume=idea["volume"],
            difficulty=idea["difficulty"],
            cpc=idea["cpc"],
            competition=idea["competition"],
            serp_features=idea["serp_features"],
            parent_topic=idea["parent_topic"],
        )
        rows.append(row)
        db.add(row)
    await db.commit()
    return rows


@router.get(
    "/projects/{project_id}/keyword-magic",
    response_model=list[KeywordIdeaResponse],
)
async def list_ideas(
    project_id: UUID,
    seed: str | None = None,
    match_type: str | None = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(KeywordIdea).where(KeywordIdea.project_id == project_id)
    if seed:
        q = q.where(KeywordIdea.seed == seed)
    if match_type:
        q = q.where(KeywordIdea.match_type == match_type)
    q = q.order_by(desc(KeywordIdea.volume)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post(
    "/projects/{project_id}/serp/analyze",
    response_model=SerpOverviewResponse,
)
async def analyze_serp_endpoint(
    project_id: UUID,
    keyword: str = Query(..., min_length=1),
    location: str = "us",
    device: str = "desktop",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.serp_analyzer import analyze_serp
    data = await analyze_serp(keyword=keyword, location=location, device=device)
    row = SerpOverview(
        project_id=project_id,
        keyword_text=data["keyword_text"],
        location=data["location"],
        device=data["device"],
        results=data["results"],
        features_present=data["features_present"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


# ===========================================================================
# Backlink Intelligence
# ===========================================================================
@router.post("/projects/{project_id}/backlinks/anchors/refresh")
async def refresh_anchor_distribution(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recompute anchor text distribution from current Backlinks rows."""
    project = await _get_project_or_404(project_id, current_user, db)
    backlinks_rows = (await db.execute(
        select(Backlinks).where(Backlinks.project_id == project_id)
    )).scalars().all()
    backlinks_data = [
        {
            "referring_domain": b.referring_domain,
            "target_url": b.target_url,
            "anchor_text": b.anchor_text,
        }
        for b in backlinks_rows
    ]
    from app.services.seo.backlink_intelligence import aggregate_anchor_distribution
    brand_terms = [project.brand_name] if project.brand_name else []
    target_keywords_rows = (await db.execute(
        select(Keyword.keyword).where(Keyword.project_id == project_id)
    )).scalars().all()
    distribution = aggregate_anchor_distribution(
        backlinks_data, brand_terms, list(target_keywords_rows)
    )
    await db.execute(delete(AnchorText).where(AnchorText.project_id == project_id))
    for row in distribution:
        db.add(AnchorText(
            project_id=project_id,
            anchor=row["anchor"],
            classification=row["classification"],
            count=row["count"],
            referring_domains=row["referring_domains"],
        ))
    await db.commit()
    return {"status": "ok", "rows_written": len(distribution)}


@router.get(
    "/projects/{project_id}/backlinks/anchors",
    response_model=list[AnchorTextResponse],
)
async def list_anchors(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(AnchorText).where(AnchorText.project_id == project_id).order_by(desc(AnchorText.count))
    )).scalars().all()
    return rows


@router.post("/projects/{project_id}/backlinks/toxic/scan")
async def scan_toxic_backlinks(
    project_id: UUID,
    min_score: float = Query(40.0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    backlinks_rows = (await db.execute(
        select(Backlinks).where(Backlinks.project_id == project_id)
    )).scalars().all()
    backlinks_data = [
        {
            "referring_domain": b.referring_domain,
            "target_url": b.target_url,
            "anchor_text": b.anchor_text,
        }
        for b in backlinks_rows
    ]
    from app.services.seo.backlink_intelligence import filter_toxic
    toxic = filter_toxic(backlinks_data, min_score=min_score)
    await db.execute(delete(ToxicBacklink).where(ToxicBacklink.project_id == project_id))
    for t in toxic:
        db.add(ToxicBacklink(
            project_id=project_id,
            referring_domain=t["referring_domain"] or "",
            target_url=t["target_url"],
            spam_score=t["spam_score"],
            reasons=t["reasons"],
        ))
    await db.commit()
    return {"status": "ok", "toxic_count": len(toxic)}


@router.get(
    "/projects/{project_id}/backlinks/toxic",
    response_model=list[ToxicBacklinkResponse],
)
async def list_toxic(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(ToxicBacklink)
        .where(ToxicBacklink.project_id == project_id)
        .order_by(desc(ToxicBacklink.spam_score))
    )).scalars().all()
    return rows


@router.post("/projects/{project_id}/backlinks/toxic/{toxic_id}/disavow")
async def disavow_toxic(
    project_id: UUID,
    toxic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    row = await db.get(ToxicBacklink, toxic_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Toxic backlink not found")
    row.disavowed = True
    await db.commit()
    return {"status": "disavowed"}


@router.get("/projects/{project_id}/backlinks/disavow.txt")
async def export_disavow_file(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export Google-format disavow file for all flagged toxic links."""
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(ToxicBacklink).where(
            ToxicBacklink.project_id == project_id, ToxicBacklink.disavowed.is_(True)
        )
    )).scalars().all()
    lines = ["# AdTicks disavow export", f"# generated: {datetime.now(tz=timezone.utc).isoformat()}"]
    for r in rows:
        lines.append(f"domain:{r.referring_domain}")
    return {"content": "\n".join(lines), "format": "google_disavow"}


@router.post(
    "/projects/{project_id}/backlinks/intersect",
    response_model=list[LinkIntersectResponse],
)
async def link_intersect_endpoint(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute domains that link to >=2 competitors but not the project."""
    await _get_project_or_404(project_id, current_user, db)

    project_referring = set((await db.execute(
        select(Backlinks.referring_domain).where(Backlinks.project_id == project_id)
    )).scalars().all())

    competitors = (await db.execute(
        select(Competitor).where(Competitor.project_id == project_id)
    )).scalars().all()

    competitor_referring: dict[str, set[str]] = {}
    for c in competitors:
        # In a real impl this would be backed by the competitor's own backlink data
        # (or pulled from a paid provider). Here we use any rows tagged with competitor name.
        referring = set((await db.execute(
            select(Backlinks.referring_domain).where(
                Backlinks.target_url.ilike(f"%{c.domain}%")
            )
        )).scalars().all())
        if referring:
            competitor_referring[c.domain] = referring

    from app.services.seo.backlink_intelligence import link_intersect
    rows_data = link_intersect(project_referring, competitor_referring, min_competitors=2)
    await db.execute(delete(LinkIntersect).where(LinkIntersect.project_id == project_id))
    rows: list[LinkIntersect] = []
    for r in rows_data:
        row = LinkIntersect(
            project_id=project_id,
            referring_domain=r["referring_domain"],
            competitor_count=r["competitor_count"],
            competitors=r["competitors"],
            domain_authority=r["domain_authority"],
        )
        rows.append(row)
        db.add(row)
    await db.commit()
    return rows


# ===========================================================================
# Content Optimizer + Briefs + Topic Clusters
# ===========================================================================
@router.post(
    "/projects/{project_id}/content/brief",
    response_model=ContentBriefResponse,
)
async def create_content_brief(
    project_id: UUID,
    payload: ContentBriefRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.content_optimizer import generate_brief
    competitors = payload.competitors
    if not competitors:
        # Use top SERP results as competitor sources
        from app.services.seo.serp_analyzer import analyze_serp
        serp = await analyze_serp(payload.target_keyword)
        competitors = [r["url"] for r in serp.get("results", [])[:5]]
    data = await generate_brief(
        target_keyword=payload.target_keyword,
        competitor_urls=competitors,
        target_word_count=payload.target_word_count,
    )
    row = ContentBrief(
        project_id=project_id,
        target_keyword=data["target_keyword"],
        title_suggestions=data["title_suggestions"],
        h1=data["h1"],
        outline=data["outline"],
        semantic_terms=data["semantic_terms"],
        questions_to_answer=data["questions_to_answer"],
        target_word_count=data["target_word_count"],
        avg_competitor_words=data["avg_competitor_words"],
        competitors_analyzed=data["competitors_analyzed"],
        readability_target=data["readability_target"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/content/briefs",
    response_model=list[ContentBriefResponse],
)
async def list_briefs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(ContentBrief).where(ContentBrief.project_id == project_id)
        .order_by(desc(ContentBrief.timestamp))
    )).scalars().all()
    return rows


@router.post(
    "/projects/{project_id}/content/optimize",
    response_model=ContentOptimizerResponse,
)
async def optimize_content(
    project_id: UUID,
    payload: ContentOptimizerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    # try to load semantic terms from latest brief
    brief = (await db.execute(
        select(ContentBrief)
        .where(
            ContentBrief.project_id == project_id,
            ContentBrief.target_keyword == payload.target_keyword,
        )
        .order_by(desc(ContentBrief.timestamp))
        .limit(1)
    )).scalar_one_or_none()
    semantic_terms = brief.semantic_terms if brief else []
    target_wc = brief.target_word_count if brief else 1500

    from app.services.seo.content_optimizer import score_content
    data = score_content(
        target_keyword=payload.target_keyword,
        content=payload.content,
        semantic_terms=semantic_terms,
        target_word_count=target_wc,
    )
    row = ContentOptimizerScore(
        project_id=project_id,
        target_keyword=data["target_keyword"],
        url=payload.url,
        word_count=data["word_count"],
        readability_score=data["readability_score"],
        grade_level=data["grade_level"],
        keyword_density=data["keyword_density"],
        headings_score=data["headings_score"],
        semantic_coverage=data["semantic_coverage"],
        overall_score=data["overall_score"],
        suggestions=data["suggestions"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post(
    "/projects/{project_id}/content/clusters/build",
    response_model=TopicClusterResponse,
)
async def build_topic_cluster(
    project_id: UUID,
    pillar_topic: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    ideas = (await db.execute(
        select(KeywordIdea).where(KeywordIdea.project_id == project_id)
    )).scalars().all()
    idea_dicts = [
        {"keyword": i.keyword, "volume": i.volume, "difficulty": i.difficulty, "intent": i.intent}
        for i in ideas
    ]
    from app.services.seo.content_optimizer import build_topic_cluster as _build
    data = _build(pillar_topic, idea_dicts)
    row = TopicCluster(
        project_id=project_id,
        pillar_topic=data["pillar_topic"],
        supporting_topics=data["supporting_topics"],
        total_volume=data["total_volume"],
        coverage_score=data["coverage_score"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/content/clusters",
    response_model=list[TopicClusterResponse],
)
async def list_topic_clusters(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(TopicCluster)
        .where(TopicCluster.project_id == project_id)
        .order_by(desc(TopicCluster.timestamp))
    )).scalars().all()
    return rows


# ===========================================================================
# Local SEO
# ===========================================================================
@router.get(
    "/projects/{project_id}/local/citations",
    response_model=list[LocalCitationResponse],
)
async def list_citations(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(LocalCitation).where(LocalCitation.project_id == project_id)
    )).scalars().all()
    return rows


@router.get("/projects/{project_id}/local/consistency")
async def consistency_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(LocalCitation).where(LocalCitation.project_id == project_id)
    )).scalars().all()
    citations_data = [
        {
            "directory": r.directory,
            "consistency_score": r.consistency_score,
            "issues": r.issues,
        }
        for r in rows
    ]
    from app.services.seo.local_seo import aggregate_consistency
    return aggregate_consistency(citations_data)


@router.post(
    "/projects/{project_id}/local/grid/run",
    response_model=list[LocalRankGridCell],
)
async def run_local_grid(
    project_id: UUID,
    keyword: str = Query(..., min_length=1),
    center_lat: float = Query(...),
    center_lng: float = Query(...),
    radius_km: float = 5.0,
    grid_size: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a synthetic local rank grid. Plug a real local-pack source
    (BrightLocal, Local Falcon, GBP API) into the inner block when available."""
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.local_seo import generate_grid_points
    points = generate_grid_points(center_lat, center_lng, radius_km, grid_size)

    import random
    new_rows: list[LocalRankGrid] = []
    for lat, lng in points:
        # Replace this with real local-pack lookup once a provider is wired
        rank = random.choice([1, 2, 3, 4, 5, 7, 10, 14, None, None])
        row = LocalRankGrid(
            project_id=project_id,
            keyword=keyword,
            grid_lat=lat,
            grid_lng=lng,
            rank=rank,
            radius_km=radius_km,
        )
        new_rows.append(row)
        db.add(row)
    await db.commit()
    return new_rows


@router.get(
    "/projects/{project_id}/local/grid",
    response_model=list[LocalRankGridCell],
)
async def list_local_grid(
    project_id: UUID,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(LocalRankGrid).where(LocalRankGrid.project_id == project_id)
    if keyword:
        q = q.where(LocalRankGrid.keyword == keyword)
    q = q.order_by(desc(LocalRankGrid.timestamp)).limit(200)
    rows = (await db.execute(q)).scalars().all()
    return rows


# ===========================================================================
# Log file analyzer
# ===========================================================================
@router.post("/projects/{project_id}/logs/upload")
async def upload_log_file(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    content = (await file.read()).decode("utf-8", errors="ignore")
    from app.services.seo.log_analyzer import parse_lines
    result = parse_lines(content.splitlines())
    await db.execute(delete(LogEvent).where(LogEvent.project_id == project_id))
    for row in result.aggregated:
        db.add(LogEvent(
            project_id=project_id,
            bot=row["bot"],
            url=row["url"],
            status_code=row["status_code"],
            hits=row["hits"],
            last_crawled=row["last_crawled"] or datetime.now(timezone.utc),
        ))
    await db.commit()
    return {"status": "ok", "summary": result.summary, "rows": len(result.aggregated)}


@router.get(
    "/projects/{project_id}/logs",
    response_model=list[LogEventResponse],
)
async def list_log_events(
    project_id: UUID,
    bot: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(LogEvent).where(LogEvent.project_id == project_id)
    if bot:
        q = q.where(LogEvent.bot == bot)
    q = q.order_by(desc(LogEvent.hits)).limit(500)
    rows = (await db.execute(q)).scalars().all()
    return rows


# ===========================================================================
# Reports
# ===========================================================================
@router.post(
    "/projects/{project_id}/reports/generate",
    response_model=GeneratedReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    project_id: UUID,
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_project_or_404(project_id, current_user, db)

    # Build the summary by aggregating data
    pages_count = (await db.execute(
        select(func.count(CrawledPage.id)).where(CrawledPage.project_id == project_id)
    )).scalar() or 0
    issues = (await db.execute(
        select(SiteAuditIssue).where(SiteAuditIssue.project_id == project_id).limit(20)
    )).scalars().all()
    backlinks_count = (await db.execute(
        select(func.count(Backlinks.id)).where(Backlinks.project_id == project_id)
    )).scalar() or 0
    keywords_count = (await db.execute(
        select(func.count(Keyword.id)).where(Keyword.project_id == project_id)
    )).scalar() or 0
    cwv_avg = (await db.execute(
        select(func.avg(CoreWebVitals.performance_score)).where(CoreWebVitals.project_id == project_id)
    )).scalar()
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    notices = sum(1 for i in issues if i.severity == "notice")
    score = max(0, 100 - min(100, errors * 5 + warnings * 2 + notices))

    summary = {
        "site_score": score,
        "pages_crawled": pages_count,
        "total_issues": len(issues),
        "errors": errors,
        "warnings": warnings,
        "backlinks": backlinks_count,
        "referring_domains": backlinks_count,
        "keywords_tracked": keywords_count,
        "cwv_score": int(cwv_avg) if cwv_avg else None,
        "top_issues": [
            {"severity": i.severity, "message": i.message, "url": i.url} for i in issues[:10]
        ],
    }

    from app.services.seo.report_generator import build_pdf_report
    from app.core.config import settings
    out_dir = os.path.join(settings.STORAGE_ROOT, "reports", str(project_id))
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{int(datetime.now(tz=timezone.utc).timestamp())}_{payload.report_type}.pdf"
    path = os.path.join(out_dir, fname)

    try:
        actual_path = build_pdf_report(project.brand_name, summary, path, payload.branding)
    except Exception:
        logger.exception("report generation failed")
        actual_path = path.replace(".pdf", ".md")
        from app.services.seo.report_generator import build_markdown_report
        with open(actual_path, "w", encoding="utf-8") as f:
            f.write(build_markdown_report(project.brand_name, summary, payload.branding))

    rel = os.path.relpath(actual_path, settings.STORAGE_ROOT).replace(os.sep, "/")
    file_url = f"/api/storage/{rel}"

    row = GeneratedReport(
        project_id=project_id,
        user_id=current_user.id,
        report_type=payload.report_type,
        title=payload.title,
        file_url=file_url,
        branding=payload.branding,
        summary=summary,
        status="ready",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/reports",
    response_model=list[GeneratedReportResponse],
)
async def list_reports(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(GeneratedReport)
        .where(GeneratedReport.project_id == project_id)
        .order_by(desc(GeneratedReport.timestamp))
    )).scalars().all()
    return rows


# ===========================================================================
# Hub — overview metrics for the SEO landing dashboard
# ===========================================================================
@router.get("/projects/{project_id}/hub-overview")
async def hub_overview(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Single endpoint that powers the new SEO Hub dashboard cards."""
    await _get_project_or_404(project_id, current_user, db)
    pages_count = (await db.execute(
        select(func.count(CrawledPage.id)).where(CrawledPage.project_id == project_id)
    )).scalar() or 0
    issues = (await db.execute(
        select(SiteAuditIssue).where(SiteAuditIssue.project_id == project_id)
    )).scalars().all()
    keywords = (await db.execute(
        select(func.count(Keyword.id)).where(Keyword.project_id == project_id)
    )).scalar() or 0
    backlinks = (await db.execute(
        select(func.count(Backlinks.id)).where(Backlinks.project_id == project_id)
    )).scalar() or 0
    refdom = (await db.execute(
        select(func.count(func.distinct(Backlinks.referring_domain))).where(Backlinks.project_id == project_id)
    )).scalar() or 0
    toxic = (await db.execute(
        select(func.count(ToxicBacklink.id)).where(ToxicBacklink.project_id == project_id)
    )).scalar() or 0
    ideas = (await db.execute(
        select(func.count(KeywordIdea.id)).where(KeywordIdea.project_id == project_id)
    )).scalar() or 0
    cwv = (await db.execute(
        select(func.avg(CoreWebVitals.performance_score)).where(CoreWebVitals.project_id == project_id)
    )).scalar()
    citations = (await db.execute(
        select(func.count(LocalCitation.id)).where(LocalCitation.project_id == project_id)
    )).scalar() or 0
    briefs = (await db.execute(
        select(func.count(ContentBrief.id)).where(ContentBrief.project_id == project_id)
    )).scalar() or 0
    clusters = (await db.execute(
        select(func.count(TopicCluster.id)).where(TopicCluster.project_id == project_id)
    )).scalar() or 0

    from app.models.aeo import AEOVisibility
    mentions = (await db.execute(
        select(func.count(AEOVisibility.id)).where(AEOVisibility.project_id == project_id)
    )).scalar() or 0

    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    score = max(0, 100 - min(100, errors * 5 + warnings * 2 + sum(1 for i in issues if i.severity == "notice")))
    
    return {
        "site_score": score,
        "pages_crawled": pages_count,
        "errors": errors,
        "warnings": warnings,
        "total_issues": len(issues),
        "keywords_tracked": keywords,
        "keyword_ideas": ideas,
        "backlinks": backlinks,
        "referring_domains": refdom,
        "toxic_backlinks": toxic,
        "core_web_vitals_score": int(cwv) if cwv else None,
        "citations": citations,
        "content_briefs": briefs,
        "clusters": clusters,
        "mentions": mentions,
        "authority_score": 78,  # Mocked
        "share_of_voice": 12.5  # Mocked
    }
