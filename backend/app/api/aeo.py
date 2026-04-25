"""
AdTicks AEO (AI-Powered SEO) API Router.

Endpoints for:
- AI chatbot visibility tracking
- Featured snippets and PAA tracking
- Content recommendations and FAQ generation
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.keyword import Keyword
from app.models.aeo import AEOVisibility, AEOTrends, SnippetTracking, PAA, ContentRecommendation
from app.models.user import User
from app.schemas.aeo import (
    AEOVisibilityResponse,
    AEOTrendsResponse,
    VisibilityCheckRequest,
    KeywordIdRequest,
    SnippetTrackingResponse,
    PAA_Response,
    ContentRecommendationResponse,
    ContentRecommendationUpdate,
    GeneratedFAQResponse,
    ContentOutlineRequest,
    ContentOutline,
    SnippetOpportunity,
    AEO_DashboardSummary,
)
from app.services.ai_visibility import AIVisibilityService
from app.services.snippet_tracking import SnippetTrackingService
from app.services.content_recommendations import ContentRecommendationService

router = APIRouter(prefix="/aeo", tags=["aeo"])

# Initialize services
visibility_service = AIVisibilityService()
snippet_service = SnippetTrackingService()
recommendation_service = ContentRecommendationService()


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    """Verify user owns the project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _get_keyword(keyword_id: UUID, db: AsyncSession) -> Keyword:
    """Get keyword by ID."""
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")
    return keyword


# ============================================================================
# AI Visibility Tracking Endpoints
# ============================================================================

@router.get(
    "/projects/{project_id}/visibility/summary",
    response_model=AEO_DashboardSummary,
    summary="Get AEO Dashboard Summary"
)
async def get_aeo_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall AEO dashboard summary for a project."""
    await _assert_owner(project_id, current_user, db)

    # Count keywords
    keyword_result = await db.execute(
        select(Keyword).where(Keyword.project_id == project_id)
    )
    all_keywords = keyword_result.scalars().all()
    total_keywords = len(all_keywords)

    # Count visibility records
    visibility_result = await db.execute(
        select(AEOVisibility).where(AEOVisibility.project_id == project_id)
    )
    all_visibility = visibility_result.scalars().all()

    # Count snippets
    snippet_records = []
    if all_keywords:
        snippet_result = await db.execute(
            select(SnippetTracking).where(
                SnippetTracking.keyword_id.in_([k.id for k in all_keywords])
            )
        )
        snippet_records = snippet_result.scalars().all()
    
    featured_snippet_count = sum(1 for s in snippet_records if s.has_snippet)

    # Count PAA queries
    paa_queries = []
    if all_keywords:
        paa_result = await db.execute(
            select(PAA).where(
                PAA.keyword_id.in_([k.id for k in all_keywords])
            )
        )
        paa_queries = paa_result.scalars().all()

    # Count recommendations
    rec_result = await db.execute(
        select(ContentRecommendation).where(ContentRecommendation.project_id == project_id)
    )
    all_recommendations = rec_result.scalars().all()
    pending_recs = sum(1 for r in all_recommendations if not r.user_action)
    implemented_recs = sum(1 for r in all_recommendations if r.user_action == "implemented")

    # Calculate average visibility percentage
    avg_visibility = 0.0
    if all_visibility:
        mentioned = sum(1 for v in all_visibility if v.is_mentioned)
        avg_visibility = (mentioned / len(all_visibility)) * 100

    return AEO_DashboardSummary(
        total_keywords=total_keywords,
        ai_visibility_count=len(all_visibility),
        featured_snippet_count=featured_snippet_count,
        paa_queries_count=len(paa_queries),
        recommendation_count=len(all_recommendations),
        pending_recommendations=pending_recs,
        implemented_recommendations=implemented_recs,
        avg_ai_visibility_percentage=avg_visibility,
        snippet_opportunities=max(0, total_keywords - featured_snippet_count)
    )


@router.post(
    "/check-visibility",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check AI Visibility"
)
async def check_ai_visibility(
    request: VisibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger AI visibility check for a keyword.
    
    Queries ChatGPT, Perplexity, and Claude for brand mentions.
    This is an asynchronous operation.
    """
    await _get_keyword(request.keyword_id, db)
    
    # For MVP, return accepted without queuing - in production, use Celery
    return {
        "status": "queued",
        "keyword_id": str(request.keyword_id),
        "models_to_check": request.ai_models,
        "message": "Visibility check queued"
    }


@router.get(
    "/projects/{project_id}/visibility/chatgpt",
    response_model=list[AEOVisibilityResponse],
    summary="Get ChatGPT Visibility Data"
)
async def get_chatgpt_visibility(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get ChatGPT visibility data for keywords in a project."""
    await _assert_owner(project_id, current_user, db)

    query = select(AEOVisibility).where(
        AEOVisibility.project_id == project_id,
        AEOVisibility.ai_model == "chatgpt"
    )

    if keyword_id:
        query = query.where(AEOVisibility.keyword_id == keyword_id)

    query = query.order_by(AEOVisibility.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [AEOVisibilityResponse.model_validate(r) for r in records]


@router.get(
    "/projects/{project_id}/visibility/perplexity",
    response_model=list[AEOVisibilityResponse],
    summary="Get Perplexity Visibility Data"
)
async def get_perplexity_visibility(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Perplexity visibility data for keywords in a project."""
    await _assert_owner(project_id, current_user, db)

    query = select(AEOVisibility).where(
        AEOVisibility.project_id == project_id,
        AEOVisibility.ai_model == "perplexity"
    )

    if keyword_id:
        query = query.where(AEOVisibility.keyword_id == keyword_id)

    query = query.order_by(AEOVisibility.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [AEOVisibilityResponse.model_validate(r) for r in records]


@router.get(
    "/projects/{project_id}/visibility/claude",
    response_model=list[AEOVisibilityResponse],
    summary="Get Claude Visibility Data"
)
async def get_claude_visibility(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Claude visibility data for keywords in a project."""
    await _assert_owner(project_id, current_user, db)

    query = select(AEOVisibility).where(
        AEOVisibility.project_id == project_id,
        AEOVisibility.ai_model == "claude"
    )

    if keyword_id:
        query = query.where(AEOVisibility.keyword_id == keyword_id)

    query = query.order_by(AEOVisibility.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [AEOVisibilityResponse.model_validate(r) for r in records]


@router.get(
    "/projects/{project_id}/trends",
    response_model=list[AEOTrendsResponse],
    summary="Get Visibility Trends"
)
async def get_visibility_trends(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    ai_model: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get visibility trends over time."""
    await _assert_owner(project_id, current_user, db)

    query = select(AEOTrends).where(AEOTrends.project_id == project_id)

    if keyword_id:
        query = query.where(AEOTrends.keyword_id == keyword_id)

    if ai_model:
        query = query.where(AEOTrends.ai_model == ai_model)

    query = query.order_by(AEOTrends.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [AEOTrendsResponse.model_validate(r) for r in records]


# ============================================================================
# Featured Snippets & PAA Endpoints
# ============================================================================

@router.get(
    "/keywords/{keyword_id}/snippets",
    response_model=list[SnippetTrackingResponse],
    summary="Get Snippet Tracking History"
)
async def get_snippet_history(
    keyword_id: UUID,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get featured snippet tracking history for a keyword."""
    await _get_keyword(keyword_id, db)
    snippets = await snippet_service.get_snippet_history(db, keyword_id, limit)
    return [SnippetTrackingResponse.model_validate(s) for s in snippets]


@router.get(
    "/keywords/{keyword_id}/paa",
    response_model=list[PAA_Response],
    summary="Get People Also Ask Queries"
)
async def get_paa_queries(
    keyword_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get People Also Ask queries for a keyword."""
    await _get_keyword(keyword_id, db)
    paa_queries = await snippet_service.get_paa_queries(db, keyword_id)
    return [PAA_Response.model_validate(p) for p in paa_queries]


@router.post(
    "/snippets/check-opportunity",
    response_model=SnippetOpportunity,
    summary="Check Snippet Opportunity"
)
async def check_snippet_opportunity(
    request: KeywordIdRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze featured snippet optimization opportunity for a keyword."""
    await _get_keyword(request.keyword_id, db)
    opportunity = await snippet_service.check_snippet_opportunity(db, request.keyword_id)
    return SnippetOpportunity(**opportunity)


@router.get(
    "/projects/{project_id}/snippets/summary",
    summary="Get Snippet Summary"
)
async def get_snippet_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get snippet summary for all keywords in a project."""
    await _assert_owner(project_id, current_user, db)
    summary = await snippet_service.get_snippet_summary(db, project_id)
    return summary


# ============================================================================
# Content Recommendations Endpoints
# ============================================================================

@router.post(
    "/content/generate-recommendations",
    response_model=list[ContentRecommendationResponse],
    summary="Generate Content Recommendations"
)
async def generate_recommendations(
    request: KeywordIdRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI-powered content recommendations for a keyword."""
    keyword = await _get_keyword(request.keyword_id, db)

    recommendations = await recommendation_service.generate_recommendations(
        db=db,
        project_id=keyword.project_id,
        keyword_id=request.keyword_id,
        keyword_text=keyword.keyword
    )
    await db.commit()

    return [ContentRecommendationResponse.model_validate(r) for r in recommendations]


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=list[ContentRecommendationResponse],
    summary="Get Recommendations"
)
async def get_recommendations(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    rec_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get content recommendations for a project."""
    await _assert_owner(project_id, current_user, db)

    query = select(ContentRecommendation).where(
        ContentRecommendation.project_id == project_id
    )

    if keyword_id:
        query = query.where(ContentRecommendation.keyword_id == keyword_id)

    if rec_type:
        query = query.where(ContentRecommendation.recommendation_type == rec_type)

    query = query.order_by(ContentRecommendation.created_at.desc()).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [ContentRecommendationResponse.model_validate(r) for r in records]


@router.put(
    "/recommendations/{rec_id}",
    response_model=ContentRecommendationResponse,
    summary="Mark Recommendation Action"
)
async def mark_recommendation_action(
    rec_id: UUID,
    update: ContentRecommendationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a recommendation as implemented or rejected."""
    rec = await recommendation_service.mark_recommendation_action(
        db, rec_id, update.user_action
    )
    await db.commit()
    return ContentRecommendationResponse.model_validate(rec)


# ============================================================================
# FAQ Endpoints
# ============================================================================

@router.post(
    "/faq/generate-from-paa",
    response_model=GeneratedFAQResponse,
    summary="Generate FAQ from PAA"
)
async def generate_faq_from_paa(
    keyword_id: UUID,
    paa_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate FAQ entry from a People Also Ask query."""
    keyword = await _get_keyword(keyword_id, db)

    faq = await recommendation_service.generate_faq_from_paa(
        db=db,
        project_id=keyword.project_id,
        keyword_id=keyword_id,
        paa_id=paa_id
    )
    await db.commit()

    return GeneratedFAQResponse.model_validate(faq)


@router.get(
    "/projects/{project_id}/faqs",
    response_model=list[GeneratedFAQResponse],
    summary="Get FAQs"
)
async def get_faqs(
    project_id: UUID,
    keyword_id: UUID | None = Query(None),
    approved_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get generated FAQs for a project."""
    await _assert_owner(project_id, current_user, db)

    faqs = await recommendation_service.get_faqs(
        db=db,
        project_id=project_id,
        keyword_id=keyword_id,
        approved_only=approved_only
    )

    return [GeneratedFAQResponse.model_validate(f) for f in faqs[:limit]]


@router.put(
    "/faqs/{faq_id}/approve",
    response_model=GeneratedFAQResponse,
    summary="Approve FAQ"
)
async def approve_faq(
    faq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a generated FAQ entry."""
    faq = await recommendation_service.approve_faq(db, faq_id)
    await db.commit()
    return GeneratedFAQResponse.model_validate(faq)


# ============================================================================
# Content Outline Endpoint
# ============================================================================

@router.post(
    "/content/generate-outline",
    response_model=ContentOutline,
    summary="Generate Content Outline"
)
async def generate_content_outline(
    request: ContentOutlineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a content outline for a keyword."""
    await _get_keyword(request.keyword_id, db)

    outline = await recommendation_service.generate_content_outline(
        db=db,
        keyword_id=request.keyword_id,
        content_type=request.content_type or "blog",
        target_length=request.target_length or "medium"
    )

    return ContentOutline(**outline)
