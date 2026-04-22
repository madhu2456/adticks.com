"""
AdTicks — SEO Suite API endpoints.

Endpoints
---------
GET    /projects/{id}/keywords/history      — Rank history with pagination
GET    /keywords/{id}/serp-features         — SERP features
GET    /projects/{id}/competitors/keywords  — Competitor keywords with pagination
GET    /projects/{id}/backlinks             — Backlinks with pagination
"""

from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached, invalidate_cache
from app.models.project import Project
from app.models.keyword import Keyword
from app.models.user import User
from app.models.seo import RankHistory, SerpFeatures, CompetitorKeywords, Backlinks
from app.schemas.common import PaginatedResponse
from app.schemas.seo import (
    RankHistoryResponse,
    SerpFeaturesResponse,
    CompetitorKeywordsResponse,
    BacklinksResponse,
)

router = APIRouter(prefix="/seo", tags=["seo"])


# ============================================================================
# Helper functions
# ============================================================================
async def _get_project_or_404(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """Get project or raise 404."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


async def _get_keyword_or_404(
    keyword_id: UUID, db: AsyncSession
) -> Keyword:
    """Get keyword or raise 404."""
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )
    return keyword


# ============================================================================
# Rank History Endpoint
# ============================================================================
@router.get(
    "/projects/{project_id}/keywords/history",
    response_model=PaginatedResponse[RankHistoryResponse],
)
@cached(ttl=300)  # 5 minutes cache
async def get_rank_history(
    project_id: UUID,
    keyword_id: UUID | None = Query(None, description="Filter by keyword ID"),
    device: str = Query(None, description="Filter by device (desktop/mobile)"),
    days: int = Query(30, ge=1, le=365, description="Last N days of history"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get rank history for a project's keywords.

    Returns paginated historical ranking data with optional filtering by keyword, device, and date range.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **project_id**: UUID of the project

    **Query parameters:**
    - **keyword_id**: Optional - Filter by specific keyword
    - **device**: Optional - Filter by device (desktop/mobile)
    - **days**: Number of days to look back (1-365, default: 30)
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items per page (default: 50, max: 500)

    **Returns:**
    - Paginated response with rank history data

    **Responses:**
    - 200 OK: Rank history returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build base query
    cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=days)
    query = (
        select(RankHistory)
        .join(Keyword)
        .where(
            Keyword.project_id == project_id,
            RankHistory.timestamp >= cutoff_date,
        )
    )

    # Apply optional filters
    if keyword_id:
        query = query.where(RankHistory.keyword_id == keyword_id)
    if device:
        query = query.where(RankHistory.device == device)

    # Get total count - build count query separately
    count_query = (
        select(func.count(RankHistory.id))
        .join(Keyword)
        .where(
            Keyword.project_id == project_id,
            RankHistory.timestamp >= cutoff_date,
        )
    )
    if keyword_id:
        count_query = count_query.where(RankHistory.keyword_id == keyword_id)
    if device:
        count_query = count_query.where(RankHistory.device == device)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    results = await db.execute(
        query.order_by(desc(RankHistory.timestamp))
        .offset(skip)
        .limit(limit)
    )
    rank_history = results.scalars().all()

    return PaginatedResponse.create(
        data=rank_history,
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================================
# SERP Features Endpoint
# ============================================================================
@router.get(
    "/keywords/{keyword_id}/serp-features",
    response_model=SerpFeaturesResponse,
)
@cached(ttl=600)  # 10 minutes cache
async def get_serp_features(
    keyword_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get SERP features for a specific keyword.

    Returns feature information including featured snippets, rich snippets, ads, and knowledge panels.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **keyword_id**: UUID of the keyword

    **Returns:**
    - SERP features data

    **Responses:**
    - 200 OK: SERP features returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Keyword not found
    """
    # Verify keyword exists and user owns the project
    keyword = await _get_keyword_or_404(keyword_id, db)
    await _get_project_or_404(keyword.project_id, current_user, db)

    # Get or create SERP features
    result = await db.execute(
        select(SerpFeatures).where(SerpFeatures.keyword_id == keyword_id)
    )
    serp_features = result.scalar_one_or_none()

    if not serp_features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SERP features not found for this keyword",
        )

    return serp_features


# ============================================================================
# Competitor Keywords Endpoint
# ============================================================================
@router.get(
    "/projects/{project_id}/competitors/keywords",
    response_model=PaginatedResponse[CompetitorKeywordsResponse],
)
@cached(ttl=3600)  # 1 hour cache
async def get_competitor_keywords(
    project_id: UUID,
    competitor_domain: str | None = Query(None, description="Filter by competitor domain"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get competitor keywords for a project.

    Returns paginated list of keywords tracked by competitors.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **project_id**: UUID of the project

    **Query parameters:**
    - **competitor_domain**: Optional - Filter by specific competitor domain
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items per page (default: 50, max: 500)

    **Returns:**
    - Paginated response with competitor keyword data

    **Responses:**
    - 200 OK: Competitor keywords returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build query
    query = select(CompetitorKeywords).where(CompetitorKeywords.project_id == project_id)

    # Apply optional filter
    if competitor_domain:
        query = query.where(CompetitorKeywords.competitor_domain == competitor_domain)

    # Get total count - build count query separately
    count_query = select(func.count(CompetitorKeywords.id)).where(CompetitorKeywords.project_id == project_id)
    if competitor_domain:
        count_query = count_query.where(CompetitorKeywords.competitor_domain == competitor_domain)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    results = await db.execute(
        query.order_by(desc(CompetitorKeywords.timestamp))
        .offset(skip)
        .limit(limit)
    )
    competitor_keywords = results.scalars().all()

    return PaginatedResponse.create(
        data=competitor_keywords,
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================================
# Backlinks Endpoint
# ============================================================================
@router.get(
    "/projects/{project_id}/backlinks",
    response_model=PaginatedResponse[BacklinksResponse],
)
@cached(ttl=3600)  # 1 hour cache
async def get_backlinks(
    project_id: UUID,
    min_authority: float | None = Query(
        None, ge=0, le=100, description="Minimum authority score"
    ),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get backlinks for a project.

    Returns paginated list of backlinks with authority scores, optionally filtered by minimum authority.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **project_id**: UUID of the project

    **Query parameters:**
    - **min_authority**: Optional - Filter by minimum authority score (0-100)
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items per page (default: 50, max: 500)

    **Returns:**
    - Paginated response with backlink data

    **Responses:**
    - 200 OK: Backlinks returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build query
    query = select(Backlinks).where(Backlinks.project_id == project_id)

    # Apply optional filter
    if min_authority is not None:
        query = query.where(Backlinks.authority_score >= min_authority)

    # Get total count - build count query separately
    count_query = select(func.count(Backlinks.id)).where(Backlinks.project_id == project_id)
    if min_authority is not None:
        count_query = count_query.where(Backlinks.authority_score >= min_authority)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    results = await db.execute(
        query.order_by(desc(Backlinks.authority_score))
        .offset(skip)
        .limit(limit)
    )
    backlinks = results.scalars().all()

    return PaginatedResponse.create(
        data=backlinks,
        total=total,
        skip=skip,
        limit=limit,
    )
