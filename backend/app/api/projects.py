"""
AdTicks — Projects router.

Endpoints
---------
POST   /projects        — create a project
GET    /projects        — list user's projects
GET    /projects/{id}   — get a single project
PUT    /projects/{id}   — update a project
DELETE /projects/{id}   — delete a project
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.transactions import with_transaction
from app.core.caching import invalidate_cache
from app.core.storage import storage
from app.models.project import Project
from app.models.competitor import Competitor
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_or_404(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    result = await db.execute(
        select(Project)
        .options(joinedload(Project.competitors))
        .where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.unique().scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@with_transaction()
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project for the authenticated user.
    
    Initialize a new visibility tracking project with basic metadata.
    """
    project = Project(
        user_id=current_user.id,
        brand_name=payload.brand_name,
        domain=payload.domain,
        industry=payload.industry,
    )
    db.add(project)
    await db.flush()

    # Add competitors if provided
    if payload.competitors:
        for domain in payload.competitors:
            comp = Competitor(project_id=project.id, domain=domain)
            db.add(comp)
        await db.flush()
    
    # Trigger initial keyword research if seeds are provided
    if payload.seed_keywords:
        try:
            from app.tasks.seo_tasks import generate_keywords_task
            generate_keywords_task.delay(
                project_id=str(project.id),
                domain=project.domain,
                industry=project.industry or "",
                seed_keywords=payload.seed_keywords,
            )
        except Exception:
            pass

    # Reload with competitors for the response
    return await _get_project_or_404(project.id, current_user, db)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    List all projects belonging to the authenticated user.
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results with competitors
    result = await db.execute(
        select(Project)
        .options(joinedload(Project.competitors))
        .where(Project.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    projects = result.unique().scalars().all()
    
    return PaginatedResponse.create(
        data=projects,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single project by ID.
    
    Fetches detailed information about a specific project owned by the authenticated user.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project to retrieve (required)
    
    **Returns:**
    - Project object with id, brand_name, domain, industry, and timestamps
    
    **Responses:**
    - 200 OK: Project retrieved successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    return await _get_project_or_404(project_id, current_user, db)


@router.put("/{project_id}", response_model=ProjectResponse)
@with_transaction()
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a project's metadata and competitors.
    
    Updates selected fields of an existing project and its competitors.
    """
    project = await _get_project_or_404(project_id, current_user, db)
    
    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle competitors separately
    competitors_to_set = update_data.pop("competitors", None)
    
    # Update project fields
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Sync competitors if provided in payload
    if competitors_to_set is not None:
        # Delete existing competitors
        await db.execute(
            delete(Competitor).where(Competitor.project_id == project.id)
        )
        # Add new competitors
        for domain in competitors_to_set:
            if domain.strip():
                comp = Competitor(project_id=project.id, domain=domain.strip())
                db.add(comp)
    
    await db.flush()
    
    # Invalidate project cache
    await invalidate_cache(f"cache:list_projects:*{current_user.id}*")
    
    # Reload to ensure competitors are included in response
    return await _get_project_or_404(project_id, current_user, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@with_transaction()
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a project and all its related data.
    
    Permanently removes a project and cascades the deletion to all associated data 
    including keywords, rankings, scan results, and insights.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project to delete (required)
    
    **Returns:**
    - No content (204 response)
    
    **Responses:**
    - 204 No Content: Project deleted successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    """
    project = await _get_project_or_404(project_id, current_user, db)
    
    # 1. Delete physical files associated with the project
    try:
        storage.delete_project_files(str(project_id))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to delete files for project {project_id}: {e}")

    # 2. Delete project from DB (Cascades handled by SQLAlchemy and DB constraints)
    await db.delete(project)
    await db.flush()
    
    # 3. Invalidate project cache
    await invalidate_cache(f"cache:list_projects:*{current_user.id}*")
    await invalidate_cache(f"cache:get_rankings:{project_id}:*")
    await invalidate_cache(f"cache:get_sov_stats:{project_id}*")
