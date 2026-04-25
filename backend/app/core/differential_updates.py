"""
Differential update detection for AdTicks SEO scans.

Compares current project state with previous scan to detect what changed,
enabling partial re-scans instead of full scans.

Detectable Changes:
- Keywords: New/removed keywords, domain changes
- Rankings: Keywords only (data always refreshed)
- Audit: Domain/URL changes
- Gaps: Domain/competitor changes
"""

import hashlib
import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.caching import get_redis_client

logger = logging.getLogger(__name__)


class DifferentialUpdateDetector:
    """Detects changes in project state to enable partial updates."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    async def _get_state_hash(self, state_dict: Dict[str, Any]) -> str:
        """Generate MD5 hash of project state."""
        state_json = json.dumps(state_dict, sort_keys=True, default=str)
        return hashlib.md5(state_json.encode()).hexdigest()
    
    async def save_keywords_state(self, keywords: list) -> None:
        """Save current keywords state hash."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            state_hash = await self._get_state_hash({"keywords": keywords})
            key = f"diff:keywords_state:{self.project_id}"
            await redis.setex(key, 86400 * 30, state_hash)  # 30 days
            logger.debug(f"Saved keywords state hash for project {self.project_id}: {state_hash[:8]}")
        except Exception as e:
            logger.warning(f"Error saving keywords state: {e}")
    
    async def keywords_changed(self, current_keywords: list) -> bool:
        """Detect if keywords have changed since last scan."""
        redis = await get_redis_client()
        if not redis:
            return True  # Assume changed if Redis unavailable
        
        try:
            key = f"diff:keywords_state:{self.project_id}"
            previous_hash = await redis.get(key)
            
            if not previous_hash:
                logger.info(f"No previous keywords state found for project {self.project_id}")
                return True
            
            current_hash = await self._get_state_hash({"keywords": current_keywords})
            
            changed = current_hash != previous_hash
            if changed:
                logger.info(f"Keywords changed for project {self.project_id}")
            
            return changed
        except Exception as e:
            logger.warning(f"Error detecting keyword changes: {e}")
            return True
    
    async def save_domain_state(self, domain: str) -> None:
        """Save current domain."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            key = f"diff:domain_state:{self.project_id}"
            await redis.setex(key, 86400 * 30, domain, )  # 30 days
            logger.debug(f"Saved domain state for project {self.project_id}: {domain}")
        except Exception as e:
            logger.warning(f"Error saving domain state: {e}")
    
    async def domain_changed(self, current_domain: str) -> bool:
        """Detect if domain has changed."""
        redis = await get_redis_client()
        if not redis:
            return False  # Assume no change if Redis unavailable
        
        try:
            key = f"diff:domain_state:{self.project_id}"
            previous_domain = await redis.get(key)
            
            if not previous_domain:
                logger.info(f"No previous domain state found for project {self.project_id}")
                return False
            
            changed = previous_domain != current_domain
            if changed:
                logger.warning(
                    f"Domain changed for project {self.project_id}: "
                    f"{previous_domain} -> {current_domain}"
                )
            
            return changed
        except Exception as e:
            logger.warning(f"Error detecting domain changes: {e}")
            return False
    
    async def save_competitors_state(self, competitor_domains: list) -> None:
        """Save current competitor domains."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            state_hash = await self._get_state_hash({"competitors": sorted(competitor_domains)})
            key = f"diff:competitors_state:{self.project_id}"
            await redis.setex(key, 86400 * 30, state_hash)  # 30 days
            logger.debug(f"Saved competitors state for project {self.project_id}: {state_hash[:8]}")
        except Exception as e:
            logger.warning(f"Error saving competitors state: {e}")
    
    async def competitors_changed(self, current_competitors: list) -> bool:
        """Detect if competitors have changed."""
        redis = await get_redis_client()
        if not redis:
            return False
        
        try:
            key = f"diff:competitors_state:{self.project_id}"
            previous_hash = await redis.get(key)
            
            if not previous_hash:
                logger.info(f"No previous competitors state found for project {self.project_id}")
                return False
            
            current_hash = await self._get_state_hash({"competitors": sorted(current_competitors)})
            
            changed = current_hash != previous_hash
            if changed:
                logger.info(f"Competitors changed for project {self.project_id}")
            
            return changed
        except Exception as e:
            logger.warning(f"Error detecting competitor changes: {e}")
            return False
    
    async def get_changes_summary(
        self,
        domain: str,
        current_keywords: list,
        competitor_domains: list,
    ) -> Dict[str, Any]:
        """
        Get a summary of all detected changes.
        
        Returns:
            Dict with flags indicating which components changed
        """
        domain_changed = await self.domain_changed(domain)
        keywords_changed = await self.keywords_changed(current_keywords)
        competitors_changed = await self.competitors_changed(competitor_domains)
        
        # If domain/competitors changed, everything must be rescanned
        audit_needs_refresh = domain_changed
        gaps_need_refresh = domain_changed or competitors_changed
        rankings_need_refresh = keywords_changed  # Always refresh rankings
        
        return {
            "keywords_changed": keywords_changed,
            "domain_changed": domain_changed,
            "competitors_changed": competitors_changed,
            "audit_needs_refresh": audit_needs_refresh,
            "gaps_need_refresh": gaps_need_refresh,
            "rankings_need_refresh": rankings_need_refresh,
            "requires_full_rescan": domain_changed or keywords_changed,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def save_all_states(
        self,
        domain: str,
        keywords: list,
        competitor_domains: list,
    ) -> None:
        """Save all state hashes for future differential updates."""
        try:
            await self.save_domain_state(domain)
            await self.save_keywords_state(keywords)
            await self.save_competitors_state(competitor_domains)
            logger.info(f"Saved all differential update states for project {self.project_id}")
        except Exception as e:
            logger.warning(f"Error saving differential update states: {e}")
    
    async def clear_states(self) -> None:
        """Clear all saved state hashes (for manual reset)."""
        redis = await get_redis_client()
        if not redis:
            return
        
        try:
            keys = [
                f"diff:keywords_state:{self.project_id}",
                f"diff:domain_state:{self.project_id}",
                f"diff:competitors_state:{self.project_id}",
            ]
            for key in keys:
                await redis.delete(key)
            logger.info(f"Cleared all differential update states for project {self.project_id}")
        except Exception as e:
            logger.warning(f"Error clearing differential update states: {e}")
