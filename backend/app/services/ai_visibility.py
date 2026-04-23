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
        if not self.chatgpt_api_key:
            logger.warning("ChatGPT API key not configured")
            return False, None, None, 0.0

        try:
            # Simulate ChatGPT API call (for MVP, would use actual API)
            # Real implementation would call OpenAI API
            
            # This is a mock implementation - real version would call OpenAI
            is_mentioned = self._mock_api_call(keyword, brand_name)
            confidence = 0.85 if is_mentioned else 0.90

            if is_mentioned:
                mention_text = f"Mentioned {brand_name} in context of {keyword}"
                position = 1  # Would extract actual position from response
                logger.info("chatgpt_mention_found", extra={"keyword": keyword, "brand": brand_name})
            else:
                mention_text = None
                position = None

            return is_mentioned, mention_text, position, confidence

        except Exception as e:
            logger.error("chatgpt_visibility_check_failed", extra={"error": str(e)})
            return False, None, None, 0.0

    async def check_perplexity_visibility(
        self,
        keyword: str,
        brand_name: str,
        domain: str
    ) -> tuple[bool, Optional[str], Optional[int], float]:
        """Check if domain is mentioned in Perplexity response."""
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not configured")
            return False, None, None, 0.0

        try:
            # Mock implementation
            is_mentioned = self._mock_api_call(keyword, brand_name, model="perplexity")
            confidence = 0.82 if is_mentioned else 0.88

            if is_mentioned:
                mention_text = f"Mentioned {brand_name} in Perplexity search results"
                position = 2
            else:
                mention_text = None
                position = None

            return is_mentioned, mention_text, position, confidence

        except Exception as e:
            logger.error("perplexity_visibility_check_failed", extra={"error": str(e)})
            return False, None, None, 0.0

    async def check_claude_visibility(
        self,
        keyword: str,
        brand_name: str,
        domain: str
    ) -> tuple[bool, Optional[str], Optional[int], float]:
        """Check if domain is mentioned in Claude response."""
        if not self.claude_api_key:
            logger.warning("Claude API key not configured")
            return False, None, None, 0.0

        try:
            # Mock implementation
            is_mentioned = self._mock_api_call(keyword, brand_name, model="claude")
            confidence = 0.88 if is_mentioned else 0.92

            if is_mentioned:
                mention_text = f"Mentioned {brand_name} in response about {keyword}"
                position = 1
            else:
                mention_text = None
                position = None

            return is_mentioned, mention_text, position, confidence

        except Exception as e:
            logger.error("claude_visibility_check_failed", extra={"error": str(e)})
            return False, None, None, 0.0

    def _mock_api_call(
        self,
        keyword: str,
        brand_name: str,
        model: str = "chatgpt"
    ) -> bool:
        """Mock API call for MVP - returns random mention based on keyword characteristics."""
        # In production, this would call the actual API
        # For MVP, we'll simulate based on keyword properties
        popular_keywords = ["seo", "digital marketing", "content", "analytics", "optimization"]
        has_popular_keyword = any(word in keyword.lower() for word in popular_keywords)
        return has_popular_keyword and len(brand_name) > 0

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
