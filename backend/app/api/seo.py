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


from app.core.component_cache import ComponentCache


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


@router.post("/keywords/sync-gsc", status_code=status.HTTP_202_ACCEPTED)
async def trigger_gsc_keyword_import(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger keyword import from Google Search Console data.
    
    Requires prior GSC authentication via /gsc/auth endpoint.
    Imports search queries and performance metrics from GSC into keywords.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    if not current_user.gsc_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSC not authenticated. Please authorize via /gsc/auth first."
        )
    
    try:
        from app.tasks.seo_tasks import import_gsc_keywords_task
        task = import_gsc_keywords_task.delay(project_id=str(project_id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


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
    """
    project = await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_audit_task
        task = run_seo_audit_task.delay(project_id=str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/audit/onpage", status_code=status.HTTP_202_ACCEPTED)
async def trigger_onpage_audit(
    project_id: UUID,
    url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an on-page SEO audit only."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_onpage_task
        task = run_seo_onpage_task.delay(project_id=str(project_id), url=url)
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/audit/technical", status_code=status.HTTP_202_ACCEPTED)
async def trigger_technical_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a technical SEO audit only."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_technical_task
        task = run_seo_technical_task.delay(project_id=str(project_id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/gaps/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_gap_sync(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger content gap analysis sync."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import find_content_gaps_task
        task = find_content_gaps_task.delay(project_id=str(project_id))
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
    """
    await _assert_project_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Ranking.id))
        .join(Keyword, Ranking.keyword_id == Keyword.id)
        .where(Keyword.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results with keyword info
    result = await db.execute(
        select(Ranking, Keyword)
        .join(Keyword, Ranking.keyword_id == Keyword.id)
        .where(Keyword.project_id == project_id)
        .order_by(Ranking.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    
    # Build response with keyword data
    rankings_with_keywords = []
    for ranking, keyword in result.all():
        response = RankingResponse.model_validate(ranking)
        # Populate keyword fields
        response.keyword = keyword.keyword
        response.intent = keyword.intent
        response.difficulty = keyword.difficulty
        response.volume = keyword.volume
        rankings_with_keywords.append(response)
    
    return PaginatedResponse.create(
        data=rankings_with_keywords,
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
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_gaps()
    
    if not cached_data:
        return {
            "project_id": str(project_id),
            "data": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "has_more": False,
            "message": "Run keyword research first"
        }
    
    gaps = cached_data.get("gaps", [])
    total = len(gaps)
    paginated_data = gaps[skip : skip + limit]
    
    return {
        "project_id": str(project_id),
        "data": paginated_data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": total > skip + limit
    }


@router.get("/onpage/{project_id}")
async def get_onpage_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve on-page SEO audit results for a project.
    
    Returns cached results from the most recent on-page SEO audit.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_audit()
    
    if not cached_data or "on_page" not in cached_data:
        return {
            "project_id": str(project_id),
            "on_page": None,
            "message": "Run /seo/audit first"
        }
    
    return {
        "project_id": str(project_id),
        "on_page": cached_data["on_page"]
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
    
    Returns cached results from the most recent technical SEO audit.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_audit()
    
    if not cached_data or "technical" not in cached_data:
        return {
            "project_id": str(project_id),
            "data": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "has_more": False,
            "message": "Run /seo/audit first"
        }
    
    technical = cached_data["technical"]
    issues = technical.get("issues", [])
    
    # Transform issues to technical check objects for frontend
    formatted_checks = []
    
    if technical.get("robots_txt", {}).get("present"):
        formatted_checks.append({
            "check": "Robots.txt",
            "status": "pass",
            "description": "robots.txt is present and valid."
        })
    
    if technical.get("https", {}).get("https_available"):
        formatted_checks.append({
            "check": "HTTPS",
            "status": "pass",
            "description": "Website is correctly served over HTTPS."
        })

    for issue in issues:
        status = "fail" if "CRITICAL" in issue.upper() or "HTTPS not available" in issue else "warning"
        formatted_checks.append({
            "check": issue.split("—")[0].strip() if "—" in issue else "Technical Issue",
            "status": status,
            "description": issue
        })
    
    total = len(formatted_checks)
    paginated_data = formatted_checks[skip : skip + limit]
    
    return {
        "project_id": str(project_id),
        "data": paginated_data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": total > skip + limit
    }
