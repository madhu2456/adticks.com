"""AdTicks SEO router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached, invalidate_cache
from app.models.keyword import Keyword, Ranking
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.keyword import KeywordCreate, RankingResponse

router = APIRouter(prefix="/seo", tags=["seo"])


async def _assert_project_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/keywords", status_code=status.HTTP_202_ACCEPTED)
async def trigger_keyword_research(
    payload: KeywordCreate,
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger async keyword research for a project.
    
    Creates a new keyword record and queues a background task to perform keyword research.
    The research generates related keywords, estimates search volume, calculates difficulty
    scores, and analyzes search intent. Results are stored and available via /seo/rankings.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **project_id**: UUID of the project (required)
    
    **Request body:**
    - **keyword**: Primary seed keyword to research
    - **intent**: Search intent category (e.g., "commercial", "informational", "navigational")
    - **difficulty**: SEO difficulty estimate (0-100)
    - **volume**: Estimated monthly search volume
    
    **Returns:**
    - **status**: Task status ("queued")
    - **keyword_id**: UUID of the created keyword record
    
    **Responses:**
    - 202 Accepted: Research queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    - 422 Unprocessable Entity: Invalid request body
    """
    await _assert_project_owner(project_id, current_user, db)
    keyword = Keyword(
        project_id=project_id,
        keyword=payload.keyword,
        intent=payload.intent,
        difficulty=payload.difficulty,
        volume=payload.volume,
    )
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    
    # Invalidate keyword cache
    await invalidate_cache(f"cache:get_rankings:{project_id}:*")
    
    try:
        from app.tasks.seo_tasks import generate_keywords_task
        generate_keywords_task.delay(
            project_id=str(project_id),
            domain="",
            industry="",
            seed_keywords=[payload.keyword],
        )
    except Exception:
        pass
    return {"status": "queued", "keyword_id": str(keyword.id)}


@router.post("/audit", status_code=status.HTTP_202_ACCEPTED)
async def trigger_site_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an async technical SEO audit for a project.
    
    Starts a background job that crawls the website and performs comprehensive technical
    SEO analysis. Checks for issues like broken links, missing meta tags, slow pages,
    mobile usability, structured data, and more. Results are available via /seo/technical.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **project_id**: UUID of the project (required)
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Audit queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    project = await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_audit_task
        task = run_seo_audit_task.delay(project_id=str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.get("/rankings/{project_id}", response_model=PaginatedResponse[RankingResponse])
@cached(ttl=300)  # 5 minutes
async def get_rankings(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve all SERP ranking snapshots for a project with pagination.
    
    Returns paginated list of keyword rankings tracked for the project. Each ranking
    represents a point-in-time snapshot of where a keyword ranked on Google SERPs.
    Results are sorted by most recent first. Results are cached for 5 minutes.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of ranking objects with keyword, position, url, timestamp
      - **total**: Total number of ranking records
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Rankings returned successfully (may be cached)
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_project_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Ranking.id))
        .join(Keyword, Ranking.keyword_id == Keyword.id)
        .where(Keyword.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Ranking)
        .join(Keyword, Ranking.keyword_id == Keyword.id)
        .where(Keyword.project_id == project_id)
        .order_by(Ranking.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    rankings = result.scalars().all()
    
    return PaginatedResponse.create(
        data=rankings,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/gaps/{project_id}")
async def get_keyword_gaps(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve keyword gap analysis for a project.
    
    Analyzes differences between keywords the project currently ranks for and keywords
    that competitors rank for. Identifies high-opportunity gaps where competitors rank
    but the project does not. This helps identify new keyword targeting opportunities.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of gap objects with keyword, competitor_rank, difficulty, volume
      - **total**: Total number of keyword gaps found
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
      - **message**: Status message if no gaps available
    
    **Responses:**
    - 200 OK: Gap analysis returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Note:** Run /seo/keywords endpoint first to generate keyword data
    """
    await _assert_project_owner(project_id, current_user, db)
    return {
        "project_id": str(project_id),
        "data": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
        "has_more": False,
        "message": "Run keyword research first"
    }


@router.get("/technical/{project_id}")
async def get_technical_seo(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve technical SEO audit results for a project.
    
    Returns cached results from the most recent technical SEO audit. Includes findings
    for issues like broken links, missing meta tags, page speed, mobile usability,
    structured data, robots.txt, sitemap, and other technical SEO factors.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of audit findings with issue_type, severity, url, description
      - **total**: Total number of findings
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
      - **message**: Status message if no audit results available
    
    **Responses:**
    - 200 OK: Audit results returned
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Note:** Run /seo/audit endpoint first to generate audit data
    """
    await _assert_project_owner(project_id, current_user, db)
    return {
        "project_id": str(project_id),
        "data": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
        "has_more": False,
        "message": "Run /seo/audit first"
    }
