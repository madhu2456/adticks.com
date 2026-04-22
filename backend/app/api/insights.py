"""AdTicks insights router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.models.score import Score
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.recommendation import RecommendationResponse

router = APIRouter(prefix="/insights", tags=["insights"])


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}", response_model=PaginatedResponse[RecommendationResponse])
async def get_insights(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve all recommendations and insights for a project with pagination.
    
    Returns paginated list of actionable insights and recommendations generated for the
    project. Each recommendation includes category, priority level, and detailed description.
    Results are sorted by priority (ascending) then by most recent first.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of recommendation objects with text, category, priority, created_at, is_read
      - **total**: Total number of recommendations
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Insights returned successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Recommendation.id)).where(Recommendation.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.project_id == project_id)
        .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    recommendations = result.scalars().all()
    
    return PaginatedResponse.create(
        data=recommendations,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{project_id}/summary")
async def get_insights_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a high-level summary of insights and latest scores for a project.
    
    Returns a summary dashboard view combining the latest visibility scores and top
    unread recommendations. Useful for quick overview of project status and key areas
    that need attention.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Returns:**
    - Summary object with:
      - **project_id**: UUID of the project
      - **latest_scores**: Object with visibility_score, impact_score, sov_score, timestamp
      - **unread_recommendations**: Count of unread recommendations
      - **top_priorities**: Array of top 5 unread recommendations by priority
    
    **Responses:**
    - 200 OK: Summary returned successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)

    score_result = await db.execute(
        select(Score)
        .where(Score.project_id == project_id)
        .order_by(Score.timestamp.desc())
        .limit(1)
    )
    latest_score = score_result.scalar_one_or_none()

    rec_result = await db.execute(
        select(Recommendation)
        .where(Recommendation.project_id == project_id, Recommendation.is_read.is_(False))
    )
    unread = rec_result.scalars().all()

    return {
        "project_id": str(project_id),
        "latest_scores": {
            "visibility_score": latest_score.visibility_score if latest_score else None,
            "impact_score": latest_score.impact_score if latest_score else None,
            "sov_score": latest_score.sov_score if latest_score else None,
            "timestamp": latest_score.timestamp.isoformat() if latest_score else None,
        },
        "unread_recommendations": len(unread),
        "top_priorities": [
            {"text": r.text, "priority": r.priority, "category": r.category}
            for r in sorted(unread, key=lambda x: x.priority)[:5]
        ],
    }


@router.post("/{project_id}/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_insights(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a background refresh of all insights for a project."""
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.workers.tasks import generate_insights_task
        task = generate_insights_task.delay(str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}
