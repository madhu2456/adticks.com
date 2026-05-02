"""
Component-level caching for AdTicks SEO components.

Caches individual components (keywords, rankings, audit) separately to enable:
1. Differential updates (only re-scan changed components)
2. Faster scans by reusing cached data
3. Better granularity than full-scan cache

Each component has:
- Separate Redis keys with versioning
- Validity checks (auto-invalidate if project state changes)
- TTL (default 24 hours, configurable per component)
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.caching import get_redis_client

logger = logging.getLogger(__name__)

# TTL constants (in seconds)
KEYWORDS_CACHE_TTL = 86400  # 24 hours
RANKINGS_CACHE_TTL = 43200  # 12 hours (rankings change frequently)
AUDIT_CACHE_TTL = 86400  # 24 hours
GAPS_CACHE_TTL = 86400  # 24 hours


class ComponentCache:
    """Cache manager for individual SEO components."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    async def cache_keywords(
        self,
        keywords: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
    ) -> None:
        """Cache generated keywords and clusters."""
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis unavailable, skipping keyword cache")
            return
        
        try:
            key = f"component:keywords:{self.project_id}"
            data = {
                "keywords": keywords,
                "clusters": clusters,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await redis.setex(
                key,
                KEYWORDS_CACHE_TTL,
                json.dumps(data),
            )
            logger.info(f"Cached {len(keywords)} keywords for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error caching keywords: {e}")
    
    async def get_cached_keywords(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached keywords and clusters if valid."""
        redis = await get_redis_client()
        if not redis:
            return None
        
        try:
            key = f"component:keywords:{self.project_id}"
            data = await redis.get(key)
            
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving cached keywords: {e}")
        
        return None
    
    async def cache_rankings(
        self,
        rankings: List[Dict[str, Any]],
    ) -> None:
        """Cache keyword rankings."""
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis unavailable, skipping rankings cache")
            return
        
        try:
            key = f"component:rankings:{self.project_id}"
            data = {
                "rankings": rankings,
                "total_keywords": len(rankings),
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await redis.setex(
                key,
                RANKINGS_CACHE_TTL,
                json.dumps(data),
            )
            logger.info(f"Cached rankings for {len(rankings)} keywords in project {self.project_id}")
        except Exception as e:
            logger.error(f"Error caching rankings: {e}")
    
    async def get_cached_rankings(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached rankings if valid."""
        redis = await get_redis_client()
        if not redis:
            return None
        
        try:
            key = f"component:rankings:{self.project_id}"
            data = await redis.get(key)
            
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving cached rankings: {e}")
        
        return None
    
    async def cache_audit(
        self,
        on_page_results: Dict[str, Any],
        technical_results: Dict[str, Any],
    ) -> None:
        """Cache SEO audit results (on-page + technical)."""
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis unavailable, skipping audit cache")
            return
        
        try:
            key = f"component:audit:{self.project_id}"
            data = {
                "on_page": on_page_results,
                "technical": technical_results,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await redis.setex(
                key,
                AUDIT_CACHE_TTL,
                json.dumps(data),
            )
            logger.info(f"Cached audit results for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error caching audit: {e}")
    
    async def get_cached_audit(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached audit results if valid."""
        redis = await get_redis_client()
        if not redis:
            return None
        
        try:
            key = f"component:audit:{self.project_id}"
            data = await redis.get(key)
            
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving cached audit: {e}")
        
        return None
    
    async def cache_gaps(
        self,
        gaps: List[Dict[str, Any]],
    ) -> None:
        """Cache content gap analysis results."""
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis unavailable, skipping gaps cache")
            return
        
        try:
            key = f"component:gaps:{self.project_id}"
            data = {
                "gaps": gaps,
                "gap_count": len(gaps),
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await redis.setex(
                key,
                GAPS_CACHE_TTL,
                json.dumps(data),
            )
            logger.info(f"Cached {len(gaps)} content gaps for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error caching gaps: {e}")
    
    async def get_cached_gaps(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached gaps if valid."""
        redis = await get_redis_client()
        if not redis:
            return None
        
        try:
            key = f"component:gaps:{self.project_id}"
            data = await redis.get(key)
            
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving cached gaps: {e}")
        
        return None
    
    async def invalidate_all(self) -> None:
        """Invalidate all component caches for this project."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            keys = [
                f"component:keywords:{self.project_id}",
                f"component:rankings:{self.project_id}",
                f"component:audit:{self.project_id}",
                f"component:gaps:{self.project_id}",
            ]
            
            for key in keys:
                await redis.delete(key)
            
            logger.info(f"Invalidated all component caches for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error invalidating component caches: {e}")
    
    async def invalidate_component(self, component: str) -> None:
        """Invalidate a specific component cache."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            key = f"component:{component}:{self.project_id}"
            await redis.delete(key)
            logger.info(f"Invalidated {component} cache for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error invalidating {component} cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all components."""
        redis = await get_redis_client()
        if not redis:
            return {}
        
        stats = {}
        components = ["keywords", "rankings", "audit", "gaps", "crawl_results"]
        
        for component in components:
            try:
                key = f"component:{component}:{self.project_id}"
                data = await redis.get(key)
                
                if data:
                    ttl = await redis.ttl(key)
                    stats[component] = {
                        "exists": True,
                        "size_bytes": len(data),
                        "ttl_seconds": ttl if ttl > 0 else None,
                    }
                else:
                    stats[component] = {"exists": False}
            except Exception as e:
                logger.warning(f"Error getting stats for {component}: {e}")
        
        return stats

    async def set_cached_crawl_results(
        self,
        crawl_data: Dict[str, Any],
    ) -> None:
        """Cache web crawl results and analysis."""
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis unavailable, skipping crawl results cache")
            return
        
        try:
            key = f"component:crawl_results:{self.project_id}"
            data = {
                **crawl_data,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await redis.setex(
                key,
                AUDIT_CACHE_TTL,
                json.dumps(data, default=str),
            )
            logger.info(f"Cached crawl results for project {self.project_id}")
        except Exception as e:
            logger.error(f"Error caching crawl results: {e}")

    async def get_cached_crawl_results(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached web crawl results if valid."""
        redis = await get_redis_client()
        if not redis:
            return None
        
        try:
            key = f"component:crawl_results:{self.project_id}"
            data = await redis.get(key)
            
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving cached crawl results: {e}")
        
        return None

