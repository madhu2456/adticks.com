"""
AdTicks — SEO Meta Tags & Audit endpoints.
"""

from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached, invalidate_cache
from app.models.project import Project
from app.models.user import User
from app.models.seo_audit import (
    MetaTagAudit,
    StructuredDataAudit,
    PageSpeedMetrics,
    CrawlabilityAudit,
    InternalLinkMap,
    SEOHealthScore,
)
from app.schemas.seo_audit import (
    MetaTagAuditResponse,
    StructuredDataAuditResponse,
    PageSpeedMetricsResponse,
    CrawlabilityAuditResponse,
    InternalLinkMapResponse,
    SEOHealthScoreResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/seo", tags=["seo"])


async def _assert_project_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/audit/meta-tags", status_code=status.HTTP_202_ACCEPTED)
async def trigger_meta_tag_audit(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to audit"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger meta tag audit for specified URLs.
    
    Audits title, description, canonical URL, Open Graph tags, and Twitter cards.
    Returns immediately with task ID; results available via /seo/audit/meta-tags/{project_id}.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    # Queue background task for audit
    try:
        from app.tasks.seo_tasks import audit_meta_tags_task
        task = audit_meta_tags_task.delay(
            project_id=str(project_id),
            urls=urls[:50],  # Limit to 50 URLs per request
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "urls_count": len(urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue audit task: {str(e)}"
        )


@router.get("/audit/meta-tags/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_meta_tag_audits(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    url: str | None = Query(None, description="Filter by URL"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get meta tag audit results for a project.
    
    Returns paginated list of meta tag audits with optimization scores.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(MetaTagAudit).where(MetaTagAudit.project_id == project_id)
    
    if url:
        query = query.where(MetaTagAudit.url.ilike(f"%{url}%"))
    
    # Get total count
    total = await db.execute(select(func.count(MetaTagAudit.id)).where(MetaTagAudit.project_id == project_id))
    total_count = total.scalar() or 0
    
    # Get paginated results
    query = query.order_by(desc(MetaTagAudit.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return {
        "items": [MetaTagAuditResponse.from_orm(a) for a in audits],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.post("/audit/structured-data", status_code=status.HTTP_202_ACCEPTED)
async def trigger_structured_data_audit(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to audit"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger structured data (JSON-LD) audit for specified URLs.
    
    Checks for Organization, Article, BreadcrumbList, Product, FAQ, LocalBusiness, Event, Review schemas.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import audit_structured_data_task
        task = audit_structured_data_task.delay(
            project_id=str(project_id),
            urls=urls[:50],
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "urls_count": len(urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue audit task: {str(e)}"
        )


@router.get("/audit/structured-data/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_structured_data_audits(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    url: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get structured data audit results."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(StructuredDataAudit).where(StructuredDataAudit.project_id == project_id)
    
    if url:
        query = query.where(StructuredDataAudit.url.ilike(f"%{url}%"))
    
    total = await db.execute(select(func.count(StructuredDataAudit.id)).where(StructuredDataAudit.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(StructuredDataAudit.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return {
        "items": [StructuredDataAuditResponse.from_orm(a) for a in audits],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.post("/metrics/page-speed", status_code=status.HTTP_202_ACCEPTED)
async def trigger_page_speed_audit(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to audit"),
    device: str = Query("desktop", pattern="^(desktop|mobile)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger page speed metrics (Core Web Vitals) audit.
    
    Captures LCP, FID, CLS, TTFB, FCP and Lighthouse scores.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import audit_page_speed_task
        task = audit_page_speed_task.delay(
            project_id=str(project_id),
            urls=urls[:50],
            device=device,
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "urls_count": len(urls),
            "device": device,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue task: {str(e)}"
        )


@router.get("/metrics/page-speed/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_page_speed_metrics(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    device: str = Query(None, pattern="^(desktop|mobile)$"),
    url: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Core Web Vitals and page speed metrics."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(PageSpeedMetrics).where(PageSpeedMetrics.project_id == project_id)
    
    if device:
        query = query.where(PageSpeedMetrics.device == device)
    if url:
        query = query.where(PageSpeedMetrics.url.ilike(f"%{url}%"))
    
    total = await db.execute(select(func.count(PageSpeedMetrics.id)).where(PageSpeedMetrics.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(PageSpeedMetrics.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "items": [PageSpeedMetricsResponse.from_orm(m) for m in metrics],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.post("/audit/crawlability", status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawlability_audit(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to audit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger crawlability audit for URLs.
    
    Checks redirects, robots.txt, noindex/nofollow, canonical tags, links, and images.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import audit_crawlability_task
        task = audit_crawlability_task.delay(
            project_id=str(project_id),
            urls=urls[:50],
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "urls_count": len(urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue task: {str(e)}"
        )


@router.get("/audit/crawlability/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_crawlability_audits(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    url: str | None = Query(None),
    has_issues: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get crawlability audit results."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(CrawlabilityAudit).where(CrawlabilityAudit.project_id == project_id)
    
    if url:
        query = query.where(CrawlabilityAudit.url.ilike(f"%{url}%"))
    if has_issues is not None:
        if has_issues:
            query = query.where(CrawlabilityAudit.score < 80)
        else:
            query = query.where(CrawlabilityAudit.score >= 80)
    
    total = await db.execute(select(func.count(CrawlabilityAudit.id)).where(CrawlabilityAudit.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(CrawlabilityAudit.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return {
        "items": [CrawlabilityAuditResponse.from_orm(a) for a in audits],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.get("/internal-links/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_internal_link_map(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source_url: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get internal link map for a project."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(InternalLinkMap).where(InternalLinkMap.project_id == project_id)
    
    if source_url:
        query = query.where(InternalLinkMap.source_url.ilike(f"%{source_url}%"))
    
    total = await db.execute(select(func.count(InternalLinkMap.id)).where(InternalLinkMap.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(InternalLinkMap.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    links = result.scalars().all()
    
    return {
        "items": [InternalLinkMapResponse.from_orm(l) for l in links],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.get("/health-score/{project_id}", response_model=SEOHealthScoreResponse)
@cached(ttl=1800)
async def get_seo_health_score(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall SEO health score for a project."""
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(SEOHealthScore).where(SEOHealthScore.project_id == project_id)
    )
    score = result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SEO health score calculated yet. Run audits first."
        )
    
    return SEOHealthScoreResponse.from_orm(score)


@router.post("/health-score/{project_id}/recalculate", status_code=status.HTTP_202_ACCEPTED)
async def recalculate_seo_health_score(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recalculate SEO health score based on latest audit data.
    
    Aggregates results from meta tag, structured data, crawlability, and performance audits.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import calculate_seo_health_score_task
        task = calculate_seo_health_score_task.delay(project_id=str(project_id))
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "SEO health score recalculation started",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue task: {str(e)}"
        )
