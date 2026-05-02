"""
Cache management API endpoints for AdTicks.

Provides endpoints for:
- Viewing cache statistics
- Manual cache invalidation
- Cache status monitoring
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.scan_cache import get_cache_status, invalidate_scan_cache
from app.core.component_cache import ComponentCache
from app.models.project import Project
from app.core.security import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cache", tags=["cache"])

@router.post("/purge-all", name="Purge system-wide cache")
async def purge_all_cache(current_user=Depends(get_current_user)):
    """
    DANGER ZONE: Purge EVERYTHING from Redis.
    Clears all cached results, task progress data, and session data across all projects.
    
    Requires superuser privileges.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can perform a system-wide purge."
        )
    
    try:
        from app.core.celery_app import celery_app
        from app.core.progress import ScanProgress
        
        # 1. Revoke all active and reserved tasks in Celery
        # broadcast() sends the command to all workers
        celery_app.control.purge() # Clears the queue
        celery_app.control.discard_all() # Discards all tasks
        
        # Revoke all tasks (broadcast to all workers)
        # We use terminate=True to kill currently running tasks
        celery_app.control.revoke(
            task_id="*", # Dummy ID for broad revoke if supported, or we just purge/discard
            terminate=True,
            signal='SIGKILL'
        )
        
        # 2. Flush Redis (clears progress data, cache, and the broker queue)
        redis_client = await ScanProgress._get_redis()
        if redis_client:
            await redis_client.flushall()
            logger.warning(f"SYSTEM RESET: User {current_user.email} purged all Redis data and stopped all tasks.")
            return {"status": "success", "message": "All background tasks stopped and cache purged successfully."}
        else:
            raise Exception("Could not connect to Redis")
    except Exception as e:
        logger.error(f"Error during system purge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-db", name="Clear database records")
async def clear_database_records(
    project_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    DANGER ZONE: Clear all data records for a project from the database.
    This removes keywords, rankings, scores, prompts, responses, and all scan-related data.
    This action CANNOT be undone.
    
    Only project owner can perform this action.
    """
    # Verify project exists and user owns it
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can clear project data."
        )
    
    try:
        from sqlalchemy import delete
        import app.models as models
        
        # We want to clear all data associated with this project.
        # We iterate through all models that have a 'project_id' field.
        # Database-level CASCADE will handle child records (like Rankings for Keywords).
        
        deleted_count = 0
        cleared_tables = []
        
        for model_name in models.__all__:
            # Skip User and Project models
            if model_name in ["User", "Project"]:
                continue
                
            model = getattr(models, model_name)
            
            # Check if this model has a project_id field
            if hasattr(model, "project_id"):
                stmt = delete(model).where(model.project_id == project_id)
                result = await session.execute(stmt)
                count = result.rowcount
                deleted_count += count
                if count > 0:
                    cleared_tables.append(model_name)
                    logger.info(f"Cleared {count} records from {model_name} for project {project_id}")
        
        await session.commit()
        
        # Also invalidate project cache in Redis to ensure fresh data
        try:
            await invalidate_scan_cache(project_id)
            logger.info(f"Invalidated cache for project {project_id} after database clear")
        except Exception as cache_err:
            logger.warning(f"Failed to invalidate cache after DB clear: {cache_err}")
        
        logger.warning(f"DATABASE CLEARED: User {current_user.email} cleared all records for project {project_id} ({deleted_count} records deleted from {len(cleared_tables)} tables)")
        
        return {
            "status": "success",
            "message": f"Successfully cleared {deleted_count} records from project database.",
            "records_cleared": deleted_count,
            "tables_cleared": cleared_tables
        }
    except Exception as e:
        await session.rollback()
        logger.error(f"Error clearing database records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")



@router.get("/stats/{project_id}", name="Get cache stats")
async def get_cache_stats(project_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    """
    Get cache statistics for a project (hits, misses, size, TTL).
    
    Args:
        project_id: Project UUID
        session: Database session
    
    Returns:
        Cache statistics including component breakdown
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        component_cache = ComponentCache(str(project_id))
        component_stats = await component_cache.get_cache_stats()
        
        # Get scan-level cache status
        scan_status = await get_cache_status(str(project_id))
        
        return {
            "project_id": project_id,
            "scan_cache": scan_status,
            "components": component_stats,
            "total_cached_components": sum(1 for c in component_stats.values() if c.get("exists")),
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@router.post("/invalidate/{project_id}", name="Invalidate project cache")
async def invalidate_cache(project_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    """
    Manually invalidate all cache for a project (forces full rescan).
    
    This is useful when:
    - Project settings changed (domain, competitors, etc.)
    - User wants fresh data
    - Cache becomes stale
    
    Args:
        project_id: Project UUID
        session: Database session
    
    Returns:
        Invalidation confirmation
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Invalidate scan-level cache
        await invalidate_scan_cache(str(project_id))
        
        # Invalidate all component caches
        component_cache = ComponentCache(str(project_id))
        await component_cache.invalidate_all()
        
        logger.info(f"Manually invalidated all cache for project {project_id}")
        
        return {
            "project_id": project_id,
            "status": "invalidated",
            "message": "All cache cleared. Next scan will be a fresh full scan.",
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.post("/invalidate-component/{project_id}/{component}", name="Invalidate specific component")
async def invalidate_component(
    project_id: uuid.UUID,
    component: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Invalidate a specific component cache (keywords, rankings, audit, or gaps).
    
    Useful for targeted updates without full rescan.
    
    Args:
        project_id: Project UUID
        component: Component name (keywords, rankings, audit, or gaps)
        session: Database session
    
    Returns:
        Component invalidation confirmation
    """
    valid_components = ["keywords", "rankings", "audit", "gaps"]
    if component not in valid_components:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid component. Must be one of: {', '.join(valid_components)}"
        )
    
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        component_cache = ComponentCache(str(project_id))
        await component_cache.invalidate_component(component)
        
        logger.info(f"Manually invalidated {component} cache for project {project_id}")
        
        return {
            "project_id": project_id,
            "component": component,
            "status": "invalidated",
            "message": f"{component} cache cleared. Next scan will re-generate {component}.",
        }
    except Exception as e:
        logger.error(f"Error invalidating component cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate component cache")
