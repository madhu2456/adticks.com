"""
AdTicks — Content analysis, redirects, and broken links endpoints.
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
from app.models.seo_content import (
    ContentAnalysis,
    ImageAudit,
    DuplicateContent,
    SEORecommendation,
    URLRedirect,
    BrokenLink,
)
from app.schemas.seo_content import (
    ContentAnalysisResponse,
    ImageAuditResponse,
    DuplicateContentResponse,
    SEORecommendationResponse,
    URLRedirectResponse,
    BrokenLinkResponse,
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


# ============================================================================
# Content Analysis Endpoints
# ============================================================================

@router.post("/analyze/content", status_code=status.HTTP_202_ACCEPTED)
async def trigger_content_analysis(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger content analysis for URLs.
    
    Analyzes word count, readability (Flesch-Kincaid), keyword density,
    heading structure, and generates recommendations.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import analyze_content_task
        task = analyze_content_task.delay(
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


@router.get("/analyze/content/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_content_analysis(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    url: str | None = Query(None),
    min_score: int = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get content analysis results."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(ContentAnalysis).where(ContentAnalysis.project_id == project_id)
    
    if url:
        query = query.where(ContentAnalysis.url.ilike(f"%{url}%"))
    if min_score:
        query = query.where(ContentAnalysis.score >= min_score)
    
    total = await db.execute(select(func.count(ContentAnalysis.id)).where(ContentAnalysis.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(ContentAnalysis.score), desc(ContentAnalysis.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return {
        "items": [ContentAnalysisResponse.from_orm(a) for a in analyses],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.get("/analyze/content/{project_id}/{content_id}", response_model=ContentAnalysisResponse)
async def get_content_analysis_details(
    project_id: UUID,
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed content analysis for a URL."""
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(ContentAnalysis).where(
            ContentAnalysis.id == content_id,
            ContentAnalysis.project_id == project_id,
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    
    return ContentAnalysisResponse.from_orm(analysis)


# ============================================================================
# Image Audit Endpoints
# ============================================================================

@router.post("/audit/images", status_code=status.HTTP_202_ACCEPTED)
async def trigger_image_audit(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to audit for images"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger image optimization audit.
    
    Checks alt text, file size, dimensions, format, and provides optimization suggestions.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import audit_images_task
        task = audit_images_task.delay(
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


@router.get("/audit/images/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_image_audits(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    url: str | None = Query(None),
    has_issues: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get image audit results."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(ImageAudit).where(ImageAudit.project_id == project_id)
    
    if url:
        query = query.where(ImageAudit.url.ilike(f"%{url}%"))
    if has_issues is not None:
        query = query.where(ImageAudit.is_optimized == (not has_issues))
    
    total = await db.execute(select(func.count(ImageAudit.id)).where(ImageAudit.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(ImageAudit.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return {
        "items": [ImageAuditResponse.from_orm(a) for a in audits],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# Duplicate Content Endpoints
# ============================================================================

@router.post("/analyze/duplicates", status_code=status.HTTP_202_ACCEPTED)
async def trigger_duplicate_content_detection(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to check for duplicates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger duplicate content detection.
    
    Finds exact duplicates, near duplicates, and canonical issues.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import detect_duplicate_content_task
        task = detect_duplicate_content_task.delay(
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


@router.get("/analyze/duplicates/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_duplicate_content(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_similarity: int = Query(80, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get duplicate content detection results."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(DuplicateContent).where(
        DuplicateContent.project_id == project_id,
        DuplicateContent.similarity_percentage >= min_similarity,
    )
    
    total = await db.execute(
        select(func.count(DuplicateContent.id)).where(
            DuplicateContent.project_id == project_id,
            DuplicateContent.similarity_percentage >= min_similarity,
        )
    )
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(DuplicateContent.similarity_percentage), desc(DuplicateContent.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    duplicates = result.scalars().all()
    
    return {
        "items": [DuplicateContentResponse.from_orm(d) for d in duplicates],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# SEO Recommendations Endpoints
# ============================================================================

@router.get("/recommendations/{project_id}", response_model=PaginatedResponse)
@cached(ttl=1800)
async def get_seo_recommendations(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    priority: str | None = Query(None, pattern="^(critical|high|medium|low)$"),
    recommendation_type: str | None = Query(None),
    status_filter: str | None = Query(None, pattern="^(pending|in_progress|done)$"),
    quick_wins_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get SEO recommendations for a project.
    
    AI-powered suggestions with priority, impact, and implementation steps.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(SEORecommendation).where(SEORecommendation.project_id == project_id)
    
    if priority:
        query = query.where(SEORecommendation.priority == priority)
    if recommendation_type:
        query = query.where(SEORecommendation.recommendation_type == recommendation_type)
    if status_filter:
        query = query.where(SEORecommendation.status == status_filter)
    if quick_wins_only:
        query = query.where(SEORecommendation.quick_win == True)
    
    total = await db.execute(select(func.count(SEORecommendation.id)).where(SEORecommendation.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(
        SEORecommendation.quick_win.desc(),
        SEORecommendation.priority.desc(),
        desc(SEORecommendation.timestamp)
    ).offset(skip).limit(limit)
    result = await db.execute(query)
    recommendations = result.scalars().all()
    
    return {
        "items": [SEORecommendationResponse.from_orm(r) for r in recommendations],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.patch("/recommendations/{project_id}/{recommendation_id}/status")
async def update_recommendation_status(
    project_id: UUID,
    recommendation_id: UUID,
    status: str = Query(pattern="^(pending|in_progress|done)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update SEO recommendation status."""
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(SEORecommendation).where(
            SEORecommendation.id == recommendation_id,
            SEORecommendation.project_id == project_id,
        )
    )
    rec = result.scalar_one_or_none()
    
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    
    rec.status = status
    await db.commit()
    await db.refresh(rec)
    
    # Invalidate cache
    await invalidate_cache(f"cache:get_seo_recommendations:{project_id}")
    
    return SEORecommendationResponse.from_orm(rec)


# ============================================================================
# URL Redirect Endpoints
# ============================================================================

@router.post("/redirects", status_code=status.HTTP_201_CREATED)
async def create_redirect(
    project_id: UUID,
    source_url: str,
    target_url: str,
    status_code: int = 301,
    redirect_reason: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a URL redirect."""
    await _assert_project_owner(project_id, current_user, db)
    
    redirect = URLRedirect(
        project_id=project_id,
        source_url=source_url,
        target_url=target_url,
        status_code=status_code,
        redirect_reason=redirect_reason,
    )
    db.add(redirect)
    await db.commit()
    await db.refresh(redirect)
    
    await invalidate_cache(f"cache:get_redirects:{project_id}:*")
    
    return URLRedirectResponse.from_orm(redirect)


@router.get("/redirects/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_redirects(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source_url: str | None = Query(None),
    has_chain: bool = Query(None),
    is_broken: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get URL redirects for a project."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(URLRedirect).where(URLRedirect.project_id == project_id)
    
    if source_url:
        query = query.where(URLRedirect.source_url.ilike(f"%{source_url}%"))
    if has_chain is not None:
        query = query.where(URLRedirect.is_chain == has_chain)
    if is_broken is not None:
        query = query.where(URLRedirect.is_broken == is_broken)
    
    total = await db.execute(select(func.count(URLRedirect.id)).where(URLRedirect.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(URLRedirect.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    redirects = result.scalars().all()
    
    return {
        "items": [URLRedirectResponse.from_orm(r) for r in redirects],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


# ============================================================================
# Broken Links Endpoints
# ============================================================================

@router.post("/broken-links/detect", status_code=status.HTTP_202_ACCEPTED)
async def trigger_broken_links_detection(
    project_id: UUID,
    urls: list[str] = Query(description="URLs to check for broken links"),
    check_external: bool = Query(True, description="Also check external links"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger broken link detection for URLs.
    
    Scans pages for broken internal and external links.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import detect_broken_links_task
        task = detect_broken_links_task.delay(
            project_id=str(project_id),
            urls=urls[:50],
            check_external=check_external,
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


@router.get("/broken-links/{project_id}", response_model=PaginatedResponse)
@cached(ttl=3600)
async def get_broken_links(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source_url: str | None = Query(None),
    link_type: str | None = Query(None, pattern="^(internal|external)$"),
    status_filter: str | None = Query(None, pattern="^(active|fixed)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get broken links for a project."""
    await _assert_project_owner(project_id, current_user, db)
    
    query = select(BrokenLink).where(BrokenLink.project_id == project_id)
    
    if source_url:
        query = query.where(BrokenLink.source_url.ilike(f"%{source_url}%"))
    if link_type:
        query = query.where(BrokenLink.link_type == link_type)
    if status_filter:
        query = query.where(BrokenLink.status == status_filter)
    
    total = await db.execute(select(func.count(BrokenLink.id)).where(BrokenLink.project_id == project_id))
    total_count = total.scalar() or 0
    
    query = query.order_by(desc(BrokenLink.first_detected)).offset(skip).limit(limit)
    result = await db.execute(query)
    links = result.scalars().all()
    
    return {
        "items": [BrokenLinkResponse.from_orm(l) for l in links],
        "total": total_count,
        "skip": skip,
        "limit": limit,
    }


@router.patch("/broken-links/{project_id}/{link_id}/mark-fixed")
async def mark_broken_link_fixed(
    project_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a broken link as fixed."""
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(BrokenLink).where(
            BrokenLink.id == link_id,
            BrokenLink.project_id == project_id,
        )
    )
    link = result.scalar_one_or_none()
    
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    
    link.status = "fixed"
    link.last_checked = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(link)
    
    await invalidate_cache(f"cache:get_broken_links:{project_id}:*")
    
    return BrokenLinkResponse.from_orm(link)
