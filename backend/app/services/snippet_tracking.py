"""
Snippet Tracking Service.

Track featured snippets and People Also Ask queries from Google SERPs.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aeo import SnippetTracking, PAA
from app.models.keyword import Keyword
from app.core.logging import get_logger

logger = get_logger(__name__)


class SnippetTrackingService:
    """Service for tracking featured snippets and PAA queries."""

    async def create_or_update_snippet(
        self,
        db: AsyncSession,
        keyword_id: UUID,
        has_snippet: bool,
        snippet_type: Optional[str] = None,
        snippet_text: Optional[str] = None,
        snippet_source_url: Optional[str] = None,
        position_before_snippet: Optional[int] = None
    ) -> SnippetTracking:
        """Create or update snippet tracking record."""
        try:
            # Check if keyword already has a snippet record
            result = await db.execute(
                select(SnippetTracking)
                .where(SnippetTracking.keyword_id == keyword_id)
                .order_by(desc(SnippetTracking.date_captured))
                .limit(1)
            )
            last_record = result.scalar_one_or_none()

            # If snippet was lost, mark the previous record
            if last_record and last_record.has_snippet and not has_snippet:
                last_record.lost_date = datetime.now(tz=timezone.utc)
                logger.info("snippet_lost", extra={"keyword_id": str(keyword_id)})

            # Create new record
            snippet = SnippetTracking(
                keyword_id=keyword_id,
                has_snippet=has_snippet,
                snippet_type=snippet_type,
                snippet_text=snippet_text,
                snippet_source_url=snippet_source_url,
                position_before_snippet=position_before_snippet,
                date_captured=datetime.now(tz=timezone.utc)
            )

            db.add(snippet)
            await db.flush()
            return snippet

        except Exception as e:
            logger.error("snippet_tracking_failed", extra={"error": str(e)})
            raise

    async def get_current_snippet(
        self,
        db: AsyncSession,
        keyword_id: UUID
    ) -> Optional[SnippetTracking]:
        """Get the most recent snippet tracking record."""
        result = await db.execute(
            select(SnippetTracking)
            .where(SnippetTracking.keyword_id == keyword_id)
            .order_by(desc(SnippetTracking.date_captured))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_snippet_history(
        self,
        db: AsyncSession,
        keyword_id: UUID,
        limit: int = 30
    ) -> list[SnippetTracking]:
        """Get snippet tracking history for a keyword."""
        result = await db.execute(
            select(SnippetTracking)
            .where(SnippetTracking.keyword_id == keyword_id)
            .order_by(desc(SnippetTracking.date_captured))
            .limit(limit)
        )
        return result.scalars().all()

    async def add_paa_query(
        self,
        db: AsyncSession,
        keyword_id: UUID,
        paa_query: str,
        answer_source_url: Optional[str] = None,
        answer_snippet: Optional[str] = None,
        position: Optional[int] = None
    ) -> PAA:
        """Add a People Also Ask query."""
        try:
            # Check if this exact query already exists for this keyword
            result = await db.execute(
                select(PAA)
                .where(
                    PAA.keyword_id == keyword_id,
                    PAA.paa_query == paa_query
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug("paa_query_already_exists", extra={
                    "keyword_id": str(keyword_id),
                    "query": paa_query
                })
                return existing

            paa = PAA(
                keyword_id=keyword_id,
                paa_query=paa_query,
                answer_source_url=answer_source_url,
                answer_snippet=answer_snippet,
                position=position,
                date_found=datetime.now(tz=timezone.utc)
            )

            db.add(paa)
            await db.flush()
            logger.info("paa_query_added", extra={
                "keyword_id": str(keyword_id),
                "query": paa_query
            })
            return paa

        except Exception as e:
            logger.error("paa_add_failed", extra={"error": str(e)})
            raise

    async def get_paa_queries(
        self,
        db: AsyncSession,
        keyword_id: UUID
    ) -> list[PAA]:
        """Get all PAA queries for a keyword."""
        result = await db.execute(
            select(PAA)
            .where(PAA.keyword_id == keyword_id)
            .order_by(desc(PAA.date_found))
        )
        return result.scalars().all()

    async def check_snippet_opportunity(
        self,
        db: AsyncSession,
        keyword_id: UUID
    ) -> dict:
        """
        Analyze opportunity for featured snippet for a keyword.

        Returns opportunity assessment.
        """
        try:
            # Get current snippet status
            snippet = await self.get_current_snippet(db, keyword_id)
            
            # Get current ranking
            from app.models.keyword import Ranking
            from sqlalchemy import desc

            result = await db.execute(
                select(Ranking)
                .where(Ranking.keyword_id == keyword_id)
                .order_by(desc(Ranking.timestamp))
                .limit(1)
            )
            ranking = result.scalar_one_or_none()

            current_position = ranking.position if ranking else None
            has_snippet = bool(snippet and snippet.has_snippet)

            # Get keyword details
            keyword_result = await db.execute(
                select(Keyword).where(Keyword.id == keyword_id)
            )
            keyword_obj = keyword_result.scalar_one_or_none()

            # Simple heuristic: if not in top 5, lower opportunity
            if current_position is None:
                difficulty = "hard"
                recommendation = "No current ranking found. Improve ranking first."
            elif current_position <= 3:
                if has_snippet:
                    difficulty = "medium"
                    recommendation = "You have the snippet. Optimize it further."
                else:
                    difficulty = "easy"
                    recommendation = "High ranking but no snippet. Optimize for snippet."
            elif current_position <= 10:
                if has_snippet:
                    difficulty = "medium"
                    recommendation = "Good position. Improve ranking to maintain snippet."
                else:
                    difficulty = "medium"
                    recommendation = "Improve ranking to increase snippet likelihood."
            else:
                difficulty = "hard"
                recommendation = "Low ranking. Improve SEO basics first."

            return {
                "keyword_id": keyword_id,
                "keyword": keyword_obj.keyword if keyword_obj else "Unknown",
                "current_position": current_position,
                "has_featured_snippet": has_snippet,
                "recommendation": recommendation,
                "difficulty": difficulty,
                "potential_traffic_gain": "high" if current_position and current_position <= 5 else "medium"
            }

        except Exception as e:
            logger.error("snippet_opportunity_check_failed", extra={"error": str(e)})
            raise

    async def get_snippet_summary(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> dict:
        """
        Get snippet summary for all keywords in a project.
        """
        from app.models.keyword import Keyword
        from sqlalchemy import func

        try:
            # Get all keywords for project
            kw_result = await db.execute(
                select(Keyword.id).where(Keyword.project_id == project_id)
            )
            keyword_ids = [r[0] for r in kw_result.all()]
            
            if not keyword_ids:
                return {
                    "total_keywords": 0,
                    "with_snippet": 0,
                    "without_snippet": 0,
                    "lost_snippet": 0,
                    "snippet_percentage": 0
                }

            # Get the most recent snippet record for each keyword
            # Using a subquery to find the latest date_captured per keyword
            latest_snippets_sub = (
                select(
                    SnippetTracking.keyword_id,
                    func.max(SnippetTracking.date_captured).label("max_date")
                )
                .where(SnippetTracking.keyword_id.in_(keyword_ids))
                .group_by(SnippetTracking.keyword_id)
                .subquery()
            )

            latest_snippets_query = (
                select(SnippetTracking)
                .join(
                    latest_snippets_sub,
                    (SnippetTracking.keyword_id == latest_snippets_sub.c.keyword_id) &
                    (SnippetTracking.date_captured == latest_snippets_sub.c.max_date)
                )
            )
            
            snippet_result = await db.execute(latest_snippets_query)
            latest_snippets = snippet_result.scalars().all()
            
            has_snippet = sum(1 for s in latest_snippets if s.has_snippet)
            lost_snippet = sum(1 for s in latest_snippets if not s.has_snippet and s.lost_date)
            
            total_keywords = len(keyword_ids)
            # Keywords that either have no snippet record or have a record saying they don't have one
            no_snippet = total_keywords - has_snippet

            return {
                "total_keywords": total_keywords,
                "with_snippet": has_snippet,
                "without_snippet": no_snippet,
                "lost_snippet": lost_snippet,
                "snippet_percentage": (has_snippet / total_keywords * 100) if total_keywords > 0 else 0
            }

        except Exception as e:
            logger.error("snippet_summary_failed", extra={"error": str(e)})
            raise
