"""AdTicks scores router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached, invalidate_cache
from app.models.project import Project
from app.models.score import Score
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.score import ScoreResponse

router = APIRouter(prefix="/scores", tags=["scores"])


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}", response_model=ScoreResponse)
@cached(ttl=1800)  # 30 minutes
async def get_latest_score(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the most recent visibility score for a project.
    
    Returns the latest composite visibility score and related metrics for the project.
    Includes visibility score, impact score, share of voice (SOV), and calculation timestamp.
    Results are cached for 30 minutes to optimize performance.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Returns:**
    - Score object with:
      - **visibility_score**: Overall visibility score (0-100)
      - **impact_score**: Impact assessment (0-100)
      - **sov_score**: Share of voice score (0-100)
      - **timestamp**: When the score was calculated
    
    **Responses:**
    - 200 OK: Latest score returned (may be cached)
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found, not owned by user, or no scores calculated yet
    
    **Note:** Run /ai/scan/run or similar endpoints first to generate score data
    """
    await _assert_owner(project_id, current_user, db)
    result = await db.execute(
        select(Score)
        .where(Score.project_id == project_id)
        .order_by(Score.timestamp.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scores found. Run a visibility scan first.",
        )
    return score


@router.get("/{project_id}/history", response_model=PaginatedResponse[ScoreResponse])
@cached(ttl=1800)  # 30 minutes
async def get_score_history(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve historical visibility scores for a project with pagination.
    
    Returns paginated list of all visibility score snapshots for the project, sorted by
    most recent first. Useful for tracking score trends over time and analyzing improvements
    or declines in visibility metrics. Results are cached for 30 minutes.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of score objects with visibility_score, impact_score, sov_score, timestamp
      - **total**: Total number of score records
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Score history returned (may be cached)
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Score.id)).where(Score.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Score)
        .where(Score.project_id == project_id)
        .order_by(Score.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    scores = result.scalars().all()
    
    return PaginatedResponse.create(
        data=scores,
        total=total,
        skip=skip,
        limit=limit,
    )
