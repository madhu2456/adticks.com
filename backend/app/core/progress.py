"""
AdTicks — Scan Progress Tracking System.

Provides real-time progress updates for long-running scan tasks.
Tracks current stage, percentage completion, and estimated time remaining.

Usage:
    progress = ScanProgress("project_id")
    progress.update("rank_tracking", 25, "Checked 25/100 keywords")
    progress.get_status()  # Returns current state
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class ScanStage(str, Enum):
    """Stages of a full scan pipeline."""
    INITIALIZING = "initializing"
    KEYWORD_GENERATION = "keyword_generation"
    RANK_TRACKING = "rank_tracking"
    TECHNICAL_AUDIT = "technical_audit"
    ON_PAGE_ANALYSIS = "on_page_analysis"
    AI_SCAN = "ai_scan"
    GAP_ANALYSIS = "gap_analysis"
    SCORE_COMPUTATION = "score_computation"
    INSIGHTS_GENERATION = "insights_generation"
    CACHING = "caching"
    COMPLETED = "completed"


class ScanProgress:
    """
    Tracks progress of a scan in Redis for real-time updates.
    
    Stores progress state with:
    - Current stage
    - Completion percentage (0-100)
    - Current task message
    - Start time (for ETA calculation)
    - Estimated completion time
    """
    
    def __init__(self, project_id: str, task_id: str):
        """
        Initialize progress tracker.
        
        Args:
            project_id: Project UUID
            task_id: Celery task ID
        """
        self.project_id = project_id
        self.task_id = task_id
        self.redis_key = f"progress:{task_id}"
        self.start_time = datetime.now(timezone.utc)
    
    async def initialize(self) -> None:
        """Initialize progress tracking in Redis."""
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            initial_state = {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "stage": ScanStage.INITIALIZING.value,
                "progress": 0,
                "message": "Initializing scan...",
                "started_at": self.start_time.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "estimated_completion_at": None,
            }
            
            import json
            await redis_client.setex(
                self.redis_key,
                3600,  # 1 hour TTL
                json.dumps(initial_state, default=str)
            )
            logger.debug(f"Initialized progress tracking for task {self.task_id}")
        except Exception as e:
            logger.warning(f"Error initializing progress: {e}")
    
    async def update(
        self,
        stage: ScanStage | str,
        progress: int,
        message: str = ""
    ) -> None:
        """
        Update scan progress.
        
        Args:
            stage: Current stage (ScanStage enum or string)
            progress: Completion percentage (0-100)
            message: Current task message
        """
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            stage_str = stage.value if isinstance(stage, ScanStage) else stage
            progress = min(100, max(0, progress))  # Clamp 0-100
            
            now = datetime.now(timezone.utc)
            elapsed = (now - self.start_time).total_seconds()
            
            # Calculate ETA based on progress rate
            estimated_total = None
            if progress > 0:
                estimated_seconds = (elapsed / progress) * 100
                estimated_total = (self.start_time + timedelta(seconds=estimated_seconds)).isoformat()
            
            state = {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "stage": stage_str,
                "progress": progress,
                "message": message,
                "started_at": self.start_time.isoformat(),
                "updated_at": now.isoformat(),
                "estimated_completion_at": estimated_total,
                "elapsed_seconds": round(elapsed),
            }
            
            import json
            await redis_client.setex(
                self.redis_key,
                3600,  # 1 hour TTL
                json.dumps(state, default=str)
            )
            
            logger.debug(f"Progress: {stage_str} {progress}% - {message}")
        except Exception as e:
            logger.warning(f"Error updating progress: {e}")
    
    async def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current progress status."""
        redis_client = await self._get_redis()
        if not redis_client:
            return None
        
        try:
            status_str = await redis_client.get(self.redis_key)
            if status_str:
                import json
                return json.loads(status_str)
            return None
        except Exception as e:
            logger.warning(f"Error getting progress status: {e}")
            return None
    
    async def complete(self) -> None:
        """Mark scan as completed."""
        await self.update(ScanStage.COMPLETED, 100, "Scan completed successfully")
    
    async def cleanup(self) -> None:
        """Remove progress tracking from Redis."""
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            await redis_client.delete(self.redis_key)
        except Exception as e:
            logger.warning(f"Error cleaning up progress: {e}")
    
    @staticmethod
    async def _get_redis() -> Optional[redis.Redis]:
        """Get Redis client."""
        try:
            client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            return None
    
    @staticmethod
    async def get_progress_for_task(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve progress for a specific task (for WebSocket clients).
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Progress dict or None if not found
        """
        redis_client = await ScanProgress._get_redis()
        if not redis_client:
            return None
        
        try:
            redis_key = f"progress:{task_id}"
            status_str = await redis_client.get(redis_key)
            if status_str:
                import json
                return json.loads(status_str)
            return None
        except Exception as e:
            logger.warning(f"Error retrieving task progress: {e}")
            return None


# Stage durations (estimates for progress calculation)
STAGE_WEIGHTS = {
    ScanStage.INITIALIZING: 1,
    ScanStage.KEYWORD_GENERATION: 5,
    ScanStage.RANK_TRACKING: 40,  # Usually longest
    ScanStage.TECHNICAL_AUDIT: 5,
    ScanStage.ON_PAGE_ANALYSIS: 10,
    ScanStage.AI_SCAN: 20,
    ScanStage.GAP_ANALYSIS: 5,
    ScanStage.SCORE_COMPUTATION: 5,
    ScanStage.INSIGHTS_GENERATION: 5,
    ScanStage.CACHING: 2,
    ScanStage.COMPLETED: 2,
}

TOTAL_WEIGHT = sum(STAGE_WEIGHTS.values())


def calculate_progress_for_stage(stage: ScanStage | str) -> int:
    """Calculate cumulative progress percentage for a stage."""
    stage_obj = stage if isinstance(stage, ScanStage) else ScanStage(stage)
    
    cumulative = 0
    for s in ScanStage:
        if s == stage_obj:
            return min(100, round((cumulative / TOTAL_WEIGHT) * 100))
        cumulative += STAGE_WEIGHTS[s]
    
    return 100
