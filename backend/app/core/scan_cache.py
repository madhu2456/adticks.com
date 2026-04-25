"""
AdTicks — Scan Results Caching Strategy.

Implements intelligent caching for SEO scan results with automatic invalidation
when project details change. Results are cached in Redis with configurable TTL.

Cache Structure:
- scan:results:{project_id} → Complete scan results (TTL: 24 hours)
- scan:metadata:{project_id} → Scan metadata (timestamp, status)
- scan:invalidation:{project_id} → Hash of project state (for change detection)
"""

import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.caching import get_redis_client, clear_cache
from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.competitor import Competitor

logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
SCAN_RESULTS_TTL = 24 * 60 * 60  # 24 hours
SCAN_METADATA_TTL = 24 * 60 * 60  # 24 hours


def _get_scan_cache_key(project_id: str) -> str:
    """Get cache key for scan results."""
    return f"scan:results:{project_id}"


def _get_scan_metadata_key(project_id: str) -> str:
    """Get cache key for scan metadata."""
    return f"scan:metadata:{project_id}"


def _get_invalidation_key(project_id: str) -> str:
    """Get cache key for project state hash (used to detect changes)."""
    return f"scan:invalidation:{project_id}"


async def _get_project_state_hash(session: AsyncSession, project_id: str) -> str:
    """
    Generate a hash of the project's current state.
    
    Used to detect if anything has changed since last scan.
    If hash changes, cache is automatically invalidated.
    """
    try:
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return ""
        
        competitors_result = await session.execute(
            select(Competitor).where(Competitor.project_id == project_id)
        )
        competitors = competitors_result.scalars().all()
        
        # Build state from project details
        state_parts = [
            str(project.domain or ""),
            str(project.brand_name or ""),
            str(project.industry or ""),
            ",".join(sorted([c.domain for c in competitors])),
        ]
        state_string = "|".join(state_parts)
        
        # Generate hash
        state_hash = hashlib.md5(state_string.encode()).hexdigest()
        logger.debug(f"Project state hash for {project_id}: {state_hash}")
        return state_hash
    except Exception as e:
        logger.error(f"Error generating project state hash: {e}")
        return ""


async def has_scan_cache(project_id: str) -> bool:
    """Check if valid scan results exist in cache."""
    redis = await get_redis_client()
    if not redis:
        return False
    
    try:
        cache_key = _get_scan_cache_key(project_id)
        exists = await redis.exists(cache_key)
        return bool(exists)
    except Exception as e:
        logger.warning(f"Error checking scan cache: {e}")
        return False


async def get_cached_scan_results(project_id: str) -> Optional[dict]:
    """
    Retrieve cached scan results if available.
    
    Returns:
        Dict with scan results or None if not cached/expired
    """
    redis = await get_redis_client()
    if not redis:
        return None
    
    try:
        cache_key = _get_scan_cache_key(project_id)
        cached_value = await redis.get(cache_key)
        
        if cached_value:
            logger.info(f"Cache hit for scan results: {project_id}")
            # Also get metadata to include timestamp
            metadata = await get_scan_metadata(project_id)
            result = json.loads(cached_value)
            if metadata:
                result["_cache_metadata"] = metadata
            return result
        
        logger.debug(f"Cache miss for scan results: {project_id}")
        return None
    except Exception as e:
        logger.warning(f"Error retrieving cached scan results: {e}")
        return None


async def save_scan_results(project_id: str, results: dict) -> bool:
    """
    Save scan results to cache.
    
    Args:
        project_id: Project UUID
        results: Complete scan results dict
    
    Returns:
        True if successfully cached, False otherwise
    """
    redis = await get_redis_client()
    if not redis:
        logger.warning("Redis unavailable for scan caching")
        return False
    
    try:
        cache_key = _get_scan_cache_key(project_id)
        
        # Save results
        cached_data = json.dumps(results, default=str)
        await redis.setex(cache_key, SCAN_RESULTS_TTL, cached_data)
        
        # Save metadata (timestamp, status)
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "cached_at": now,
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=SCAN_RESULTS_TTL)).isoformat(),
            "status": "complete",
        }
        metadata_key = _get_scan_metadata_key(project_id)
        await redis.setex(metadata_key, SCAN_METADATA_TTL, json.dumps(metadata))
        
        # Save project state hash for change detection
        async with AsyncSessionLocal() as session:
            state_hash = await _get_project_state_hash(session, project_id)
            if state_hash:
                hash_key = _get_invalidation_key(project_id)
                await redis.set(hash_key, state_hash)
        
        logger.info(f"Cached scan results for project {project_id}, TTL: {SCAN_RESULTS_TTL}s")
        return True
    except Exception as e:
        logger.error(f"Error saving scan results to cache: {e}")
        return False


async def get_scan_metadata(project_id: str) -> Optional[dict]:
    """Get metadata about cached scan (timestamp, status, etc.)."""
    redis = await get_redis_client()
    if not redis:
        return None
    
    try:
        metadata_key = _get_scan_metadata_key(project_id)
        cached_value = await redis.get(metadata_key)
        
        if cached_value:
            return json.loads(cached_value)
        return None
    except Exception as e:
        logger.warning(f"Error retrieving scan metadata: {e}")
        return None


async def invalidate_scan_cache(project_id: str, reason: str = "unknown") -> bool:
    """
    Invalidate scan cache for a project.
    
    Called when:
    - Project domain changes
    - Competitors list changes
    - User manually requests refresh
    
    Args:
        project_id: Project UUID
        reason: Reason for invalidation (for logging)
    
    Returns:
        True if successfully invalidated
    """
    redis = await get_redis_client()
    if not redis:
        return False
    
    try:
        keys_to_delete = [
            _get_scan_cache_key(project_id),
            _get_scan_metadata_key(project_id),
            _get_invalidation_key(project_id),
        ]
        
        for key in keys_to_delete:
            await clear_cache(key)
        
        logger.info(f"Invalidated scan cache for project {project_id}, reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating scan cache: {e}")
        return False


async def should_invalidate_cache(project_id: str) -> bool:
    """
    Check if scan cache should be invalidated due to project state change.
    
    Returns:
        True if project state has changed (cache should be cleared)
    """
    redis = await get_redis_client()
    if not redis:
        return True  # When Redis unavailable, assume cache is stale
    
    try:
        # Get current project state hash
        async with AsyncSessionLocal() as session:
            current_hash = await _get_project_state_hash(session, project_id)
        
        if not current_hash:
            return True  # Can't determine, assume invalid
        
        # Get cached project state hash
        hash_key = _get_invalidation_key(project_id)
        cached_hash = await redis.get(hash_key)
        
        if not cached_hash:
            logger.debug(f"No cached state hash for {project_id}")
            return True  # No cached state means cache is invalid
        
        # Compare hashes
        changed = current_hash != cached_hash
        if changed:
            logger.info(f"Project state changed for {project_id}, cache should be invalidated")
            logger.debug(f"Current hash: {current_hash}, Cached hash: {cached_hash}")
        
        return changed
    except Exception as e:
        logger.error(f"Error checking cache invalidation: {e}")
        return True  # On error, assume cache is stale


async def get_cache_status(project_id: str) -> dict[str, Any]:
    """
    Get detailed status of scan cache for a project.
    
    Returns:
        Dict with cache status, timestamp, TTL remaining, etc.
    """
    redis = await get_redis_client()
    
    cache_key = _get_scan_cache_key(project_id)
    metadata_key = _get_scan_metadata_key(project_id)
    
    has_cache = False
    ttl_remaining = 0
    metadata = None
    changed = False
    
    if redis:
        try:
            # Check if cache exists
            has_cache = bool(await redis.exists(cache_key))
            
            # Get TTL
            if has_cache:
                ttl_remaining = await redis.ttl(cache_key)
            
            # Get metadata
            metadata_str = await redis.get(metadata_key)
            if metadata_str:
                metadata = json.loads(metadata_str)
            
            # Check if state has changed
            changed = await should_invalidate_cache(project_id)
        except Exception as e:
            logger.warning(f"Error getting cache status: {e}")
    
    return {
        "has_cache": has_cache,
        "ttl_remaining": ttl_remaining if ttl_remaining > 0 else 0,
        "metadata": metadata,
        "state_changed": changed,
        "cache_key": cache_key,
    }
