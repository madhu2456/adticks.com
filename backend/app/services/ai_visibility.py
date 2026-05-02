"""
AI Visibility Tracking Service.

Queries AI models (ChatGPT, Perplexity, Claude) for brand mentions
and tracks visibility metrics over time.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
import httpx

from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aeo import AEOVisibility, AEOTrends
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class AIVisibilityService:
    """Service for tracking visibility in AI chatbot responses."""

    def __init__(self):
        self.chatgpt_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.perplexity_api_key = getattr(settings, 'PERPLEXITY_API_KEY', None)
        self.claude_api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.timeout = 30
        self.http_client = httpx.AsyncClient()

    async def check_chatgpt_visibility(
        self, 
        keyword: str, 
        brand_name: str,
        domain: str
    ) -> tuple[bool, Optional[str], Optional[int], float]:
        """
        Check if domain is mentioned in ChatGPT response for a keyword.

        Returns: (is_mentioned, mention_context, position, confidence)
        """
        logger.info("AI visibility checking not yet implemented", extra={"feature": "chatgpt_visibility"})
        return False, None, None, 0.0

    async def check_perplexity_visibility(
        self,
        keyword: str,
        brand_name: str,
        domain: str
    ) -> tuple[bool, Optional[str], Optional[int], float]:
        """Check if domain is mentioned in Perplexity response."""
        logger.info("AI visibility checking not yet implemented", extra={"feature": "perplexity_visibility"})
        return False, None, None, 0.0

    async def check_claude_visibility(
        self,
        keyword: str,
        brand_name: str,
        domain: str
    ) -> tuple[bool, Optional[str], Optional[int], float]:
        """Check if domain is mentioned in Claude response."""
        logger.info("AI visibility checking not yet implemented", extra={"feature": "claude_visibility"})
        return False, None, None, 0.0

    # Removed _mock_api_call() method - replaced with explicit logging

    async def store_visibility_check(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID,
        ai_model: str,
        is_mentioned: bool,
        mention_context: Optional[str],
        position: Optional[int],
        confidence_score: float
    ) -> AEOVisibility:
        """Store visibility check result in database."""
        try:
            visibility = AEOVisibility(
                project_id=project_id,
                keyword_id=keyword_id,
                ai_model=ai_model,
                is_mentioned=is_mentioned,
                mention_context=mention_context,
                position=position,
                confidence_score=confidence_score,
                timestamp=datetime.now(tz=timezone.utc)
            )
            db.add(visibility)
            await db.flush()
            return visibility

        except Exception as e:
            logger.error("store_visibility_failed", extra={"error": str(e)})
            raise

    async def get_latest_visibility(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID,
        ai_model: str
    ) -> Optional[AEOVisibility]:
        """Get the most recent visibility check for a keyword-model pair."""
        result = await db.execute(
            select(AEOVisibility)
            .where(
                AEOVisibility.project_id == project_id,
                AEOVisibility.keyword_id == keyword_id,
                AEOVisibility.ai_model == ai_model
            )
            .order_by(AEOVisibility.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_visibility_summary(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID
    ) -> dict:
        """Get visibility summary across all AI models."""
        result = await db.execute(
            select(AEOVisibility)
            .where(
                AEOVisibility.project_id == project_id,
                AEOVisibility.keyword_id == keyword_id
            )
            .order_by(AEOVisibility.timestamp.desc())
        )
        records = result.scalars().all()

        # Group by model, keep most recent
        by_model = {}
        for record in records:
            if record.ai_model not in by_model:
                by_model[record.ai_model] = record

        mentioned_models = [m for m, r in by_model.items() if r.is_mentioned]

        return {
            "by_model": by_model,
            "mentioned_models": mentioned_models,
            "overall_mentioned": len(mentioned_models) > 0,
            "visibility_count": len(by_model)
        }

    async def calculate_trends(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID,
        ai_model: str,
        window_days: int = 30
    ) -> AEOTrends:
        """Calculate visibility trends for a keyword."""
        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=window_days)

        result = await db.execute(
            select(
                func.count(AEOVisibility.id).label("total"),
                func.sum(
                    cast(AEOVisibility.is_mentioned, Integer)
                ).label("mentioned_count"),
                func.avg(cast(AEOVisibility.position, Integer)).label("avg_pos")
            )
            .where(
                AEOVisibility.project_id == project_id,
                AEOVisibility.keyword_id == keyword_id,
                AEOVisibility.ai_model == ai_model,
                AEOVisibility.timestamp >= cutoff_date
            )
        )
        stats = result.one()

        total = stats[0] or 0
        mentioned = stats[1] or 0
        avg_position = stats[2]

        visibility_pct = (mentioned / total * 100) if total > 0 else 0.0

        trend = AEOTrends(
            project_id=project_id,
            keyword_id=keyword_id,
            ai_model=ai_model,
            visibility_percentage=visibility_pct,
            mention_count=mentioned,
            avg_position=avg_position,
            timestamp=datetime.now(tz=timezone.utc)
        )

        db.add(trend)
        await db.flush()
        return trend

    async def close(self):
        """Clean up resources."""
        await self.http_client.aclose()
