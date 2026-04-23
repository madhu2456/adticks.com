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
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.transactions import with_transaction
from app.core.caching import invalidate_cache
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_or_404(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
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
    
    **Authentication:** Required (Bearer token)
    
    **Request body:**
    - **brand_name**: Project brand name
    - **domain**: Primary domain to track
    - **industry**: Industry category
    
    **Returns:**
    - Created project object with id, timestamps, and metadata
    
    **Responses:**
    - 201 Created: Project successfully created
    - 400 Bad Request: Invalid input data
    - 401 Unauthorized: Missing or invalid authentication
    """
    project = Project(
        user_id=current_user.id,
        brand_name=payload.brand_name,
        domain=payload.domain,
        industry=payload.industry,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    List all projects belonging to the authenticated user.
    
    Returns paginated list of projects the user owns.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of project objects
      - **total**: Total number of projects
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Projects list returned
    - 401 Unauthorized: Missing or invalid authentication
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()
    
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
    Update a project's metadata.
    
    Updates selected fields of an existing project. All request body fields are optional.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project to update (required)
    
    **Request body:** (all optional)
    - **brand_name**: Updated project brand name
    - **domain**: Updated primary domain to track
    - **industry**: Updated industry category
    
    **Returns:**
    - Updated project object with id, brand_name, domain, industry, and timestamps
    
    **Responses:**
    - 200 OK: Project updated successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    - 422 Unprocessable Entity: Invalid input data
    """
    project = await _get_project_or_404(project_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    await db.flush()
    
    # Invalidate project cache
    await invalidate_cache(f"cache:list_projects:*{current_user.id}*")
    
    return project


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
    await db.delete(project)
    await db.flush()
    
    # Invalidate project cache
    await invalidate_cache(f"cache:list_projects:*{current_user.id}*")
