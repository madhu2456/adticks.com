"""
AdTicks — Gap-fill SEO API router (cannibalization, internal links, domain
compare, bulk analyzer, sitemap/robots/schema generators, outreach,
featured-snippet + PAA + volatility tracking).
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.user import User
from app.models.seo_extra import (
    KeywordCannibalization, InternalLink, OrphanPage, DomainComparison,
    BulkAnalysisJob, BulkAnalysisItem, SitemapGeneration, RobotsValidation,
    SchemaTemplate, OutreachCampaign, OutreachProspect,
    FeaturedSnippetWatch, PAAQuestion, SerpVolatilityEvent,
)
from app.schemas.seo_extra import (
    CannibalizationResponse, CannibalizationRunRequest,
    InternalLinkResponse, OrphanPageResponse, InternalLinkAnalyzeRequest,
    DomainComparisonRequest, DomainComparisonResponse,
    BulkAnalysisRequest, BulkAnalysisItemResponse, BulkAnalysisJobResponse,
    SitemapGenerateRequest, SitemapGenerationResponse,
    RobotsValidationRequest, RobotsValidationResponse,
    SchemaGenerateRequest, SchemaTemplateResponse,
    OutreachCampaignCreate, OutreachCampaignResponse,
    OutreachProspectCreate, OutreachProspectUpdate, OutreachProspectResponse,
    FeaturedSnippetResponse, PAAQuestionResponse,
    SerpVolatilityEventResponse, SerpVolatilityScanRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seo", tags=["seo-extra"])


async def _get_project_or_404(project_id: UUID, user: User, db: AsyncSession) -> Project:
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ===========================================================================
# Cannibalization
# ===========================================================================
@router.post(
    "/projects/{project_id}/cannibalization/scan",
    response_model=list[CannibalizationResponse],
)
async def scan_cannibalization(
    project_id: UUID,
    payload: CannibalizationRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = payload.rows
    if not rows:
        # try to use GSC + ranking data already in the project
        from app.models.gsc import GSCData
        from app.models.keyword import Ranking, Keyword
        gsc_rows = (await db.execute(
            select(GSCData).where(GSCData.project_id == project_id)
        )).scalars().all()
        rows = [
            {"keyword": g.query, "url": g.page, "position": g.position,
             "clicks": g.clicks, "impressions": g.impressions}
            for g in gsc_rows
            if getattr(g, "query", None) and getattr(g, "page", None)
        ]

    from app.services.seo.cannibalization import detect_cannibalization
    findings = detect_cannibalization(rows or [], min_pages=payload.min_pages)

    await db.execute(delete(KeywordCannibalization).where(KeywordCannibalization.project_id == project_id))
    out: list[KeywordCannibalization] = []
    for f in findings:
        row = KeywordCannibalization(
            project_id=project_id,
            keyword=f["keyword"],
            urls=f["urls"],
            severity=f["severity"],
            recommendation=f["recommendation"],
        )
        out.append(row)
        db.add(row)
    await db.commit()
    return out


@router.get(
    "/projects/{project_id}/cannibalization",
    response_model=list[CannibalizationResponse],
)
async def list_cannibalization(
    project_id: UUID,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(KeywordCannibalization).where(KeywordCannibalization.project_id == project_id)
    if severity:
        q = q.where(KeywordCannibalization.severity == severity)
    q = q.order_by(desc(KeywordCannibalization.detected_at))
    rows = (await db.execute(q)).scalars().all()
    return rows


# ===========================================================================
# Internal links + orphans
# ===========================================================================
@router.post("/projects/{project_id}/internal-links/analyze")
async def analyze_internal_links(
    project_id: UUID,
    payload: InternalLinkAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.internal_links import build_graph_from_urls

    graph = await build_graph_from_urls(payload.urls)
    await db.execute(delete(InternalLink).where(InternalLink.project_id == project_id))
    await db.execute(delete(OrphanPage).where(OrphanPage.project_id == project_id))
    for e in graph.edges:
        db.add(InternalLink(
            project_id=project_id,
            source_url=e.source_url,
            target_url=e.target_url,
            anchor_text=e.anchor_text,
            is_nofollow=e.is_nofollow,
            link_position=e.link_position,
        ))
    for u in graph.orphans:
        db.add(OrphanPage(
            project_id=project_id, url=u, in_sitemap=False,
            page_authority=graph.page_authority.get(u, 0.0),
        ))
    await db.commit()
    return {
        "status": "ok",
        "edges": len(graph.edges),
        "nodes": len(graph.nodes),
        "orphans": len(graph.orphans),
        "dead_ends": len(graph.dead_ends),
    }


@router.get(
    "/projects/{project_id}/internal-links",
    response_model=list[InternalLinkResponse],
)
async def list_internal_links(
    project_id: UUID,
    target: str | None = None,
    limit: int = Query(200, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(InternalLink).where(InternalLink.project_id == project_id)
    if target:
        q = q.where(InternalLink.target_url == target)
    rows = (await db.execute(q.limit(limit))).scalars().all()
    return rows


@router.get(
    "/projects/{project_id}/orphan-pages",
    response_model=list[OrphanPageResponse],
)
async def list_orphan_pages(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(OrphanPage).where(OrphanPage.project_id == project_id)
    )).scalars().all()
    return rows


# ===========================================================================
# Domain comparison
# ===========================================================================
@router.post(
    "/projects/{project_id}/domain-compare",
    response_model=DomainComparisonResponse,
)
async def domain_compare(
    project_id: UUID,
    payload: DomainComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.domain_compare import compare_domains
    data = await compare_domains(payload.primary_domain, payload.competitor_domains)
    row = DomainComparison(
        project_id=project_id,
        primary_domain=data["primary_domain"],
        competitor_domains=data["competitor_domains"],
        metrics=data["metrics"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/domain-compare/history",
    response_model=list[DomainComparisonResponse],
)
async def domain_compare_history(
    project_id: UUID,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(DomainComparison)
        .where(DomainComparison.project_id == project_id)
        .order_by(desc(DomainComparison.timestamp))
        .limit(limit)
    )).scalars().all()
    return rows


# ===========================================================================
# Bulk URL analyzer
# ===========================================================================
@router.post(
    "/projects/{project_id}/bulk/run",
    response_model=BulkAnalysisJobResponse,
)
async def run_bulk(
    project_id: UUID,
    payload: BulkAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    job = BulkAnalysisJob(
        project_id=project_id,
        job_type=payload.job_type,
        status="running",
        total_urls=len(payload.urls),
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from app.services.seo.domain_compare import run_bulk_analysis
    try:
        results = await run_bulk_analysis(payload.urls, job_type=payload.job_type)
    except Exception as e:
        logger.exception("bulk analysis failed")
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    for r in results:
        db.add(BulkAnalysisItem(
            job_id=job.id,
            url=r.get("url", ""),
            status=r.get("status", "done"),
            result=r.get("result", {}),
            error=r.get("error"),
        ))
    job.completed_urls = sum(1 for r in results if r.get("status") == "done")
    job.status = "done"
    job.finished_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return job


@router.get(
    "/projects/{project_id}/bulk/{job_id}/items",
    response_model=list[BulkAnalysisItemResponse],
)
async def list_bulk_items(
    project_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(BulkAnalysisItem).where(BulkAnalysisItem.job_id == job_id)
    )).scalars().all()
    return rows


@router.get(
    "/projects/{project_id}/bulk",
    response_model=list[BulkAnalysisJobResponse],
)
async def list_bulk_jobs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(BulkAnalysisJob)
        .where(BulkAnalysisJob.project_id == project_id)
        .order_by(desc(BulkAnalysisJob.timestamp))
    )).scalars().all()
    return rows


# ===========================================================================
# Sitemap + Robots + Schema generators
# ===========================================================================
@router.post(
    "/projects/{project_id}/sitemap/generate",
    response_model=SitemapGenerationResponse,
)
async def sitemap_generate(
    project_id: UUID,
    payload: SitemapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.sitemap_robots import generate_sitemap_xml
    xml = generate_sitemap_xml(payload.urls, payload.default_changefreq, payload.default_priority)

    from app.core.config import settings
    out_dir = os.path.join(settings.STORAGE_ROOT, "sitemaps", str(project_id))
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{int(datetime.now(tz=timezone.utc).timestamp())}_sitemap.xml"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    rel = os.path.relpath(path, settings.STORAGE_ROOT).replace(os.sep, "/")

    row = SitemapGeneration(
        project_id=project_id,
        url_count=len(payload.urls),
        file_url=f"/api/storage/{rel}",
        xml_preview=xml[:5000],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post(
    "/projects/{project_id}/robots/validate",
    response_model=RobotsValidationResponse,
)
async def robots_validate(
    project_id: UUID,
    payload: RobotsValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    raw = payload.raw_content
    url = payload.url or ""
    if not raw and url:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, follow_redirects=True)
                if r.status_code == 200:
                    raw = r.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch robots.txt: {e}")
    if not raw:
        raise HTTPException(status_code=400, detail="Provide raw_content or a URL")

    from app.services.seo.sitemap_robots import validate_robots_txt
    result = validate_robots_txt(raw)
    row = RobotsValidation(
        project_id=project_id,
        url=url or "(pasted)",
        raw_content=raw,
        is_valid=result["is_valid"],
        issues=result["issues"],
        rules=result["rules"],
        sitemap_directives=result["sitemap_directives"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post(
    "/projects/{project_id}/schema/generate",
    response_model=SchemaTemplateResponse,
)
async def schema_generate(
    project_id: UUID,
    payload: SchemaGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.sitemap_robots import generate_json_ld, SUPPORTED_SCHEMA_TYPES
    if payload.schema_type not in SUPPORTED_SCHEMA_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported schema_type. Choose from: {sorted(SUPPORTED_SCHEMA_TYPES)}")
    json_ld = generate_json_ld(payload.schema_type, payload.inputs)
    row = SchemaTemplate(
        project_id=project_id,
        schema_type=payload.schema_type,
        name=payload.name,
        inputs=payload.inputs,
        json_ld=json_ld,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/schema/templates",
    response_model=list[SchemaTemplateResponse],
)
async def list_schema_templates(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(SchemaTemplate).where(SchemaTemplate.project_id == project_id)
        .order_by(desc(SchemaTemplate.timestamp))
    )).scalars().all()
    return rows


# ===========================================================================
# Outreach
# ===========================================================================
@router.post(
    "/projects/{project_id}/outreach/campaigns",
    response_model=OutreachCampaignResponse,
    status_code=201,
)
async def create_campaign(
    project_id: UUID,
    payload: OutreachCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    row = OutreachCampaign(project_id=project_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/outreach/campaigns",
    response_model=list[OutreachCampaignResponse],
)
async def list_campaigns(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(OutreachCampaign).where(OutreachCampaign.project_id == project_id)
        .order_by(desc(OutreachCampaign.timestamp))
    )).scalars().all()
    return rows


@router.post(
    "/projects/{project_id}/outreach/campaigns/{campaign_id}/prospects",
    response_model=OutreachProspectResponse,
    status_code=201,
)
async def create_prospect(
    project_id: UUID,
    campaign_id: UUID,
    payload: OutreachProspectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    campaign = await db.get(OutreachCampaign, campaign_id)
    if not campaign or campaign.project_id != project_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    row = OutreachProspect(campaign_id=campaign_id, **payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/outreach/campaigns/{campaign_id}/prospects",
    response_model=list[OutreachProspectResponse],
)
async def list_prospects(
    project_id: UUID,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(OutreachProspect).where(OutreachProspect.campaign_id == campaign_id)
        .order_by(desc(OutreachProspect.timestamp))
    )).scalars().all()
    return rows


@router.patch(
    "/projects/{project_id}/outreach/prospects/{prospect_id}",
    response_model=OutreachProspectResponse,
)
async def update_prospect(
    project_id: UUID,
    prospect_id: UUID,
    payload: OutreachProspectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    prospect = await db.get(OutreachProspect, prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    update = payload.model_dump(exclude_unset=True)
    if "status" in update:
        from app.services.seo.snippet_volatility import is_valid_prospect_status
        if not is_valid_prospect_status(update["status"]):
            raise HTTPException(status_code=400, detail="Invalid status")
        if update["status"] == "contacted" and not prospect.last_contacted_at:
            prospect.last_contacted_at = datetime.now(timezone.utc)
        if update["status"] == "won":
            campaign = await db.get(OutreachCampaign, prospect.campaign_id)
            if campaign:
                campaign.won_link_count += 1
    for k, v in update.items():
        setattr(prospect, k, v)
    await db.commit()
    await db.refresh(prospect)
    return prospect


@router.get("/projects/{project_id}/outreach/campaigns/{campaign_id}/summary")
async def campaign_summary_endpoint(
    project_id: UUID,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(OutreachProspect).where(OutreachProspect.campaign_id == campaign_id)
    )).scalars().all()
    from app.services.seo.snippet_volatility import campaign_summary
    return campaign_summary([
        {"status": r.status} for r in rows
    ])


# ===========================================================================
# Featured snippet + PAA + volatility
# ===========================================================================
@router.get(
    "/projects/{project_id}/snippets",
    response_model=list[FeaturedSnippetResponse],
)
async def list_snippet_watch(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    rows = (await db.execute(
        select(FeaturedSnippetWatch).where(FeaturedSnippetWatch.project_id == project_id)
    )).scalars().all()
    return rows


@router.post(
    "/projects/{project_id}/snippets/check",
    response_model=FeaturedSnippetResponse,
)
async def check_snippet(
    project_id: UUID,
    keyword: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.serp_analyzer import analyze_serp
    from app.services.seo.snippet_volatility import detect_featured_snippet
    serp = await analyze_serp(keyword=keyword)
    info = detect_featured_snippet(serp, project.domain or "")
    row = FeaturedSnippetWatch(
        project_id=project_id, keyword=keyword,
        we_own=info["we_own"],
        current_owner_url=info["current_owner_url"],
        snippet_text=info["snippet_text"],
        snippet_type=info["snippet_type"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/projects/{project_id}/paa",
    response_model=list[PAAQuestionResponse],
)
async def list_paa(
    project_id: UUID,
    seed: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(PAAQuestion).where(PAAQuestion.project_id == project_id)
    if seed:
        q = q.where(PAAQuestion.seed_keyword == seed)
    rows = (await db.execute(q.order_by(desc(PAAQuestion.timestamp)))).scalars().all()
    return rows


@router.post(
    "/projects/{project_id}/volatility/scan",
    response_model=list[SerpVolatilityEventResponse],
)
async def scan_volatility(
    project_id: UUID,
    payload: SerpVolatilityScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    from app.services.seo.snippet_volatility import detect_volatility_events
    events = detect_volatility_events(
        payload.rank_diffs,
        drop_threshold=payload.drop_threshold,
        rise_threshold=payload.rise_threshold,
    )
    out: list[SerpVolatilityEvent] = []
    for e in events:
        row = SerpVolatilityEvent(
            project_id=project_id,
            keyword=e["keyword"],
            previous_position=e["previous_position"],
            current_position=e["current_position"],
            delta=e["delta"],
            direction=e["direction"],
        )
        out.append(row)
        db.add(row)
    await db.commit()
    return out


@router.get(
    "/projects/{project_id}/volatility",
    response_model=list[SerpVolatilityEventResponse],
)
async def list_volatility(
    project_id: UUID,
    direction: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, current_user, db)
    q = select(SerpVolatilityEvent).where(SerpVolatilityEvent.project_id == project_id)
    if direction in ("up", "down"):
        q = q.where(SerpVolatilityEvent.direction == direction)
    rows = (await db.execute(q.order_by(desc(SerpVolatilityEvent.detected_at)))).scalars().all()
    return rows
