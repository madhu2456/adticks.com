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
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached
from app.models.project import Project
from app.models.keyword import Keyword
from app.models.user import User
from app.models.seo import RankHistory, SerpFeatures, CompetitorKeywords, Backlinks, SiteAuditHistory
from app.schemas.common import PaginatedResponse
from app.schemas.seo import (
    RankHistoryResponse,
    SerpFeaturesResponse,
    CompetitorKeywordsResponse,
    BacklinksResponse,
    BacklinkStatsResponse,
    SiteAuditHistoryResponse,
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
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build base query
    cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=days)
    # Using Ranking table as RankHistory is currently not being populated by tasks
    from app.models.keyword import Ranking
    query = (
        select(Ranking)
        .join(Keyword)
        .where(
            Keyword.project_id == project_id,
            Ranking.timestamp >= cutoff_date,
        )
    )

    # Apply optional filters
    if keyword_id:
        query = query.where(Ranking.keyword_id == keyword_id)
    # Note: Ranking table doesn't have device field, so we ignore it if using Ranking table

    # Get total count
    count_query = (
        select(func.count(Ranking.id))
        .join(Keyword)
        .where(
            Keyword.project_id == project_id,
            Ranking.timestamp >= cutoff_date,
        )
    )
    if keyword_id:
        count_query = count_query.where(Ranking.keyword_id == keyword_id)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    results = await db.execute(
        query.order_by(desc(Ranking.timestamp))
        .offset(skip)
        .limit(limit)
    )
    rankings = results.scalars().all()
    
    # Map Ranking to RankHistoryResponse (position -> rank)
    history_data = [
        RankHistoryResponse(
            id=r.id,
            keyword_id=r.keyword_id,
            rank=r.position,
            timestamp=r.timestamp,
            device="desktop" # Default
        )
        for r in rankings
    ]

    return PaginatedResponse.create(
        data=history_data,
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
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build query
    query = select(CompetitorKeywords).where(CompetitorKeywords.project_id == project_id)

    # Apply optional filter
    if competitor_domain:
        query = query.where(CompetitorKeywords.competitor_domain == competitor_domain)

    # Get total count
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
    """
    # Verify project ownership
    await _get_project_or_404(project_id, current_user, db)

    # Build query
    query = select(Backlinks).where(Backlinks.project_id == project_id)

    # Apply optional filter
    if min_authority is not None:
        query = query.where(Backlinks.authority_score >= min_authority)

    # Get total count
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


@router.get(
    "/projects/{project_id}/backlinks/stats",
    response_model=BacklinkStatsResponse,
)
@cached(ttl=3600)
async def get_backlinks_stats(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summarized backlink statistics for a project."""
    await _get_project_or_404(project_id, current_user, db)

    # Basic counts
    count_result = await db.execute(
        select(func.count(Backlinks.id)).where(Backlinks.project_id == project_id)
    )
    total_links = count_result.scalar() or 0

    domain_count_result = await db.execute(
        select(func.count(func.distinct(Backlinks.referring_domain)))
        .where(Backlinks.project_id == project_id)
    )
    total_domains = domain_count_result.scalar() or 0

    # New/Lost in last 30 days
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)
    
    new_result = await db.execute(
        select(func.count(func.distinct(Backlinks.referring_domain)))
        .where(Backlinks.project_id == project_id, Backlinks.first_seen >= thirty_days_ago)
    )
    new_domains = new_result.scalar() or 0

    lost_result = await db.execute(
        select(func.count(Backlinks.id))
        .where(Backlinks.project_id == project_id, Backlinks.status == "lost", Backlinks.last_seen >= thirty_days_ago)
    )
    lost_domains = lost_result.scalar() or 0

    # Authority distribution
    auth_dist = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    res = await db.execute(
        select(Backlinks.authority_score).where(Backlinks.project_id == project_id)
    )
    scores = res.scalars().all()
    for s in scores:
        if s <= 20: auth_dist["0-20"] += 1
        elif s <= 40: auth_dist["21-40"] += 1
        elif s <= 60: auth_dist["41-60"] += 1
        elif s <= 80: auth_dist["61-80"] += 1
        else: auth_dist["81-100"] += 1

    avg_auth = sum(scores) / len(scores) if scores else 0.0

    # Top anchor texts
    anchor_result = await db.execute(
        select(Backlinks.anchor_text, func.count(Backlinks.id))
        .where(Backlinks.project_id == project_id)
        .group_by(Backlinks.anchor_text)
        .order_by(desc(func.count(Backlinks.id)))
        .limit(5)
    )
    top_anchors = [{"text": r[0], "count": r[1]} for r in anchor_result.all() if r[0]]

    return {
        "total_backlinks": total_links,
        "total_referring_domains": total_domains,
        "new_domains_30d": new_domains,
        "lost_domains_30d": lost_domains,
        "avg_authority": avg_auth,
        "authority_distribution": auth_dist,
        "top_anchor_texts": top_anchors
    }


@router.get(
    "/projects/{project_id}/backlinks/intersect",
    response_model=list[dict[str, Any]],
)
@cached(ttl=3600)
async def get_backlinks_intersect(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find domains that link to competitors but not the current project.
    """
    await _get_project_or_404(project_id, current_user, db)
    
    # Get project's referring domains
    project_domains_res = await db.execute(
        select(func.distinct(Backlinks.referring_domain)).where(Backlinks.project_id == project_id)
    )
    project_domains = set(project_domains_res.scalars().all())

    # Get competitors
    from app.models.competitor import Competitor
    comp_res = await db.execute(
        select(Competitor.domain).where(Competitor.project_id == project_id)
    )
    competitor_domains = comp_res.scalars().all()

    if not competitor_domains:
        return []

    # Find domains that link to any of these competitor domains in our database
    # but do NOT link to the current project
    from app.models.project import Project
    
    # Subquery to find projects that match our competitor domains
    competitor_projects_sub = (
        select(Project.id, Project.domain)
        .where(Project.domain.in_(competitor_domains))
    )
    comp_proj_res = await db.execute(competitor_projects_sub)
    comp_id_map = {row.id: row.domain for row in comp_proj_res.all()}
    
    if not comp_id_map:
        return []

    # Find backlinks belonging to those competitor projects
    intersect_query = (
        select(Backlinks.referring_domain, Backlinks.authority_score, Backlinks.project_id)
        .where(
            Backlinks.project_id.in_(list(comp_id_map.keys())),
            ~Backlinks.referring_domain.in_(list(project_domains))
        )
        .distinct(Backlinks.referring_domain)
    )
    
    intersect_res = await db.execute(intersect_query)
    
    intersections = [
        {
            "referring_domain": r[0],
            "authority_score": r[1],
            "links_to_competitor": comp_id_map.get(r[2])
        }
        for r in intersect_res.all()
    ]
    
    return sorted(intersections, key=lambda x: x["authority_score"], reverse=True)


@router.get(
    "/projects/{project_id}/audit/history",
    response_model=list[SiteAuditHistoryResponse],
)
@cached(ttl=300)
async def get_audit_history(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get historical site audit scores for a project."""
    await _get_project_or_404(project_id, current_user, db)
    
    result = await db.execute(
        select(SiteAuditHistory)
        .where(SiteAuditHistory.project_id == project_id)
        .order_by(desc(SiteAuditHistory.timestamp))
        .limit(20)
    )
    return result.scalars().all()
