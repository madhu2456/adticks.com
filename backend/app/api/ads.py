"""AdTicks Ads performance router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ads import AdsData
from app.models.project import Project
from app.models.user import User
from app.schemas.ads import AdsDataResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/ads", tags=["ads"])


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/performance/{project_id}", response_model=PaginatedResponse[AdsDataResponse])
async def get_ads_performance(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve stored ad campaign performance data for a project with pagination.
    
    Returns paginated list of ads performance metrics synced from connected ad platforms.
    Includes data like impressions, clicks, conversions, cost, CTR, and conversion rate.
    Results are sorted by most recent date first.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of ads performance objects with date, impressions, clicks, conversions, cost
      - **total**: Total number of performance records
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Performance data returned successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(AdsData.id)).where(AdsData.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(AdsData)
        .where(AdsData.project_id == project_id)
        .order_by(AdsData.date.desc())
        .offset(skip)
        .limit(limit)
    )
    ads_data = result.scalars().all()
    
    return PaginatedResponse.create(
        data=ads_data,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/sync/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def sync_ads(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an async ads data sync for a project.
    
    Initiates a background job that pulls latest advertising campaign data from connected
    ad platforms (Google Ads, Facebook Ads, etc.) and stores the performance metrics.
    Results are available via /ads/performance endpoint after sync completes.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Sync queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import sync_ads_data
        task = sync_ads_data.delay(str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}
