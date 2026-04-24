"""AdTicks AI router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.prompt import Mention, Prompt, Response
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.prompt import MentionResponse, ResponseResponse

router = APIRouter(tags=["ai"])


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/prompts/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_prompts(
    project_id: UUID,
    category: str = "brand_awareness",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger async AI prompt generation and scanning for a project.
    
    Starts a background task that generates AI prompts for the project based on brand info,
    then runs those prompts through an LLM to generate responses and detect brand mentions.
    This is an asynchronous operation that returns immediately.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **project_id**: UUID of the project to generate prompts for (required)
    - **category**: Category of prompts to generate (default: "brand_awareness")
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Task queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Example:** Generates prompts like "Who makes product X?" and runs AI to find mentions
    """
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.tasks.ai_tasks import generate_prompts_task
        task = generate_prompts_task.delay(
            project_id=str(project.id),
            brand_name=project.brand_name,
            domain=project.domain,
            industry=project.industry or "Technology",
        )
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/scan/run", status_code=status.HTTP_202_ACCEPTED)
async def run_scan(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a full comprehensive scan for a project across all channels.
    
    Initiates a background scan pipeline that includes:
    - SEO: keyword discovery, rank tracking, on-page audits, content gap analysis
    - AI Visibility: LLM-based brand mention detection across ChatGPT, Claude, Gemini
    - GSC: Google Search Console data import (impressions, clicks, CTR)
    - Ads: Google Ads performance data import (spend, conversions, ROAS)
    - Insights: Cross-channel AI recommendations (P1-P3 prioritized)
    
    This is an asynchronous operation that returns immediately.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **project_id**: UUID of the project to scan (required)
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Scan queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Example:** Performs comprehensive multi-channel brand visibility analysis
    """
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.workers.tasks import run_full_scan_task
        task = run_full_scan_task.delay(project_id=str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/insights/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_insights_ai(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a background refresh of all insights for a project (AI router).
    
    Queues a background job to regenerate insights, recommendations, and composite scores
    based on all collected data (AI scans, SEO data, ads performance, GSC queries).
    Results are persisted and available via /insights endpoints.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **project_id**: UUID of the project to refresh insights for (required)
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Refresh queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.workers.tasks import generate_insights_task
        task = generate_insights_task.delay(project_id=str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.get("/results/{project_id}", response_model=PaginatedResponse[ResponseResponse])
async def get_results(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve all AI response records for a project with pagination.
    
    Returns paginated list of AI-generated responses from prompt execution. Each response
    contains the LLM output for a specific prompt and its associated metadata.
    Results are sorted by most recent first.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of AI response objects with response_text, prompt_id, timestamp
      - **total**: Total number of responses
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Results returned successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Response.id))
        .join(Prompt, Response.prompt_id == Prompt.id)
        .where(Prompt.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Response)
        .join(Prompt, Response.prompt_id == Prompt.id)
        .where(Prompt.project_id == project_id)
        .order_by(Response.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    responses = result.scalars().all()
    
    return PaginatedResponse.create(
        data=responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/mentions/{project_id}", response_model=PaginatedResponse[MentionResponse])
async def get_mentions(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve all brand mentions detected across AI responses for a project with pagination.
    
    Returns paginated list of brand mentions found in AI-generated responses. A mention
    represents a detected reference to the brand, competitor, or related entity found
    by the LLM while analyzing search results. Results are sorted by mention ID.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of mention objects with mention_text, context, response_id, sentiment
      - **total**: Total number of mentions found
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Mentions returned successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Mention.id))
        .join(Response, Mention.response_id == Response.id)
        .join(Prompt, Response.prompt_id == Prompt.id)
        .where(Prompt.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Mention)
        .join(Response, Mention.response_id == Response.id)
        .join(Prompt, Response.prompt_id == Prompt.id)
        .where(Prompt.project_id == project_id)
        .order_by(Mention.id)
        .offset(skip)
        .limit(limit)
    )
    mentions = result.scalars().all()
    
    return PaginatedResponse.create(
        data=mentions,
        total=total,
        skip=skip,
        limit=limit,
    )
