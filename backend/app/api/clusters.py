"""AdTicks topic clusters API router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.transactions import with_transaction
from app.models.cluster import Cluster
from app.models.keyword import Keyword
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.cluster import ClusterCreate, ClusterResponse, ClusterUpdate

router = APIRouter(prefix="/projects/{project_id}/clusters", tags=["clusters"])

async def _assert_project_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.post("", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
@with_transaction()
async def create_cluster(
    project_id: UUID,
    payload: ClusterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_owner(project_id, current_user, db)
    
    cluster = Cluster(
        project_id=project_id,
        topic_name=payload.topic_name,
        keywords=payload.keywords,
    )
    db.add(cluster)
    await db.flush()
    
    # Update keyword associations if provided
    if payload.keywords:
        for kw_text in payload.keywords:
            result = await db.execute(
                select(Keyword).where(
                    Keyword.project_id == project_id, 
                    Keyword.keyword == kw_text
                )
            )
            kw = result.scalar_one_or_none()
            if kw:
                kw.cluster_id = cluster.id
    
    return cluster

@router.get("", response_model=PaginatedResponse[ClusterResponse])
async def list_clusters(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    await _assert_project_owner(project_id, current_user, db)
    
    count_result = await db.execute(
        select(func.count(Cluster.id)).where(Cluster.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(Cluster)
        .where(Cluster.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    clusters = result.scalars().all()
    
    return PaginatedResponse.create(
        data=clusters,
        total=total,
        skip=skip,
        limit=limit,
    )

@router.get("/{cluster_id}", response_model=ClusterResponse)
async def get_cluster(
    project_id: UUID,
    cluster_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(Cluster).where(Cluster.id == cluster_id, Cluster.project_id == project_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return cluster

@router.put("/{cluster_id}", response_model=ClusterResponse)
@with_transaction()
async def update_cluster(
    project_id: UUID,
    cluster_id: UUID,
    payload: ClusterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(Cluster).where(Cluster.id == cluster_id, Cluster.project_id == project_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle keywords update separately to sync associations
    new_keywords = update_data.pop("keywords", None)
    
    for field, value in update_data.items():
        setattr(cluster, field, value)
    
    if new_keywords is not None:
        cluster.keywords = new_keywords
        # Reset old associations
        await db.execute(
            select(Keyword).where(Keyword.cluster_id == cluster.id).execution_options(synchronize_session="fetch")
        )
        # This is a bit complex in async, better to do a direct update
        from sqlalchemy import update
        await db.execute(
            update(Keyword).where(Keyword.cluster_id == cluster.id).values(cluster_id=None)
        )
        # Set new associations
        for kw_text in new_keywords:
            await db.execute(
                update(Keyword)
                .where(Keyword.project_id == project_id, Keyword.keyword == kw_text)
                .values(cluster_id=cluster.id)
            )
    
    return cluster

@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
@with_transaction()
async def delete_cluster(
    project_id: UUID,
    cluster_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(Cluster).where(Cluster.id == cluster_id, Cluster.project_id == project_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    
    await db.delete(cluster)
