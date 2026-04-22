"""
Content Recommendations Service.

AI-powered content optimization and FAQ generation using Claude.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import json

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aeo import ContentRecommendation, GeneratedFAQ, PAA
from app.models.keyword import Keyword
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class ContentRecommendationService:
    """Service for generating AI-powered content recommendations."""

    def __init__(self):
        self.claude_api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

    async def generate_recommendations(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID,
        keyword_text: str,
        current_content: Optional[str] = None
    ) -> list[ContentRecommendation]:
        """
        Generate content recommendations for a keyword using Claude.
        
        For MVP, this is a mock implementation.
        """
        try:
            recommendations = []

            # Mock recommendations based on keyword characteristics
            mock_recommendations = [
                {
                    "type": "optimize",
                    "text": f"Optimize the meta title to include primary keyword '{keyword_text}' and improve click-through rate.",
                    "difficulty": "easy",
                    "impact": "high"
                },
                {
                    "type": "expand",
                    "text": f"Expand your content to cover related long-tail variations of '{keyword_text}'.",
                    "difficulty": "medium",
                    "impact": "medium"
                },
                {
                    "type": "faq",
                    "text": f"Add FAQ section addressing common questions about '{keyword_text}'.",
                    "difficulty": "easy",
                    "impact": "high"
                },
                {
                    "type": "rewrite",
                    "text": "Rewrite introduction to be more compelling and answer user intent immediately.",
                    "difficulty": "medium",
                    "impact": "medium"
                }
            ]

            for rec in mock_recommendations:
                recommendation = ContentRecommendation(
                    project_id=project_id,
                    keyword_id=keyword_id,
                    recommendation_type=rec["type"],
                    recommendation_text=rec["text"],
                    implementation_difficulty=rec["difficulty"],
                    estimated_impact=rec["impact"],
                    created_at=datetime.now(tz=timezone.utc)
                )
                db.add(recommendation)
                recommendations.append(recommendation)

            await db.flush()
            logger.info("recommendations_generated", extra={
                "keyword_id": str(keyword_id),
                "count": len(recommendations)
            })
            return recommendations

        except Exception as e:
            logger.error("recommendation_generation_failed", extra={"error": str(e)})
            raise

    async def get_recommendations(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: Optional[UUID] = None
    ) -> list[ContentRecommendation]:
        """Get recommendations for a project or specific keyword."""
        query = select(ContentRecommendation).where(
            ContentRecommendation.project_id == project_id
        )

        if keyword_id:
            query = query.where(ContentRecommendation.keyword_id == keyword_id)

        query = query.order_by(desc(ContentRecommendation.created_at))

        result = await db.execute(query)
        return result.scalars().all()

    async def mark_recommendation_action(
        self,
        db: AsyncSession,
        recommendation_id: UUID,
        action: str
    ) -> ContentRecommendation:
        """Mark recommendation as implemented or rejected."""
        try:
            result = await db.execute(
                select(ContentRecommendation).where(
                    ContentRecommendation.id == recommendation_id
                )
            )
            rec = result.scalar_one_or_none()

            if not rec:
                raise ValueError(f"Recommendation {recommendation_id} not found")

            rec.user_action = action
            await db.flush()

            logger.info("recommendation_action_marked", extra={
                "recommendation_id": str(recommendation_id),
                "action": action
            })
            return rec

        except Exception as e:
            logger.error("mark_recommendation_action_failed", extra={"error": str(e)})
            raise

    async def generate_faq_from_paa(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: UUID,
        paa_id: UUID
    ) -> GeneratedFAQ:
        """
        Generate FAQ entry from a People Also Ask query.
        """
        try:
            # Get the PAA query
            result = await db.execute(
                select(PAA).where(PAA.id == paa_id)
            )
            paa = result.scalar_one_or_none()

            if not paa:
                raise ValueError(f"PAA query {paa_id} not found")

            # Mock FAQ generation - in production would use Claude
            answer_text = f"Based on our expertise and research, {paa.paa_query.lower()} is an important question. [Detailed answer would be generated by Claude]"

            faq = GeneratedFAQ(
                project_id=project_id,
                keyword_id=keyword_id,
                paa_id=paa_id,
                question=paa.paa_query,
                answer=answer_text,
                approved=False,
                created_at=datetime.now(tz=timezone.utc)
            )

            db.add(faq)
            await db.flush()

            logger.info("faq_generated_from_paa", extra={
                "paa_id": str(paa_id),
                "keyword_id": str(keyword_id)
            })
            return faq

        except Exception as e:
            logger.error("faq_generation_failed", extra={"error": str(e)})
            raise

    async def generate_content_outline(
        self,
        db: AsyncSession,
        keyword_id: UUID,
        content_type: str = "blog",
        target_length: str = "medium"
    ) -> dict:
        """
        Generate content outline for a keyword.
        """
        try:
            # Get keyword
            result = await db.execute(
                select(Keyword).where(Keyword.id == keyword_id)
            )
            keyword = result.scalar_one_or_none()

            if not keyword:
                raise ValueError(f"Keyword {keyword_id} not found")

            # Mock outline generation
            outlines = {
                "blog": [
                    f"Introduction: What is {keyword.keyword}?",
                    "Key Benefits of " + keyword.keyword,
                    "How to Implement " + keyword.keyword,
                    "Common Mistakes to Avoid",
                    "Best Practices for " + keyword.keyword,
                    "Case Studies & Examples",
                    "Tools & Resources",
                    "Frequently Asked Questions",
                    "Conclusion: Getting Started"
                ],
                "guide": [
                    f"Understanding {keyword.keyword}",
                    "Prerequisites",
                    "Step-by-Step Guide",
                    "Advanced Techniques",
                    "Troubleshooting",
                    "Resources & References"
                ],
                "article": [
                    f"What You Need to Know About {keyword.keyword}",
                    "Current Trends in " + keyword.keyword,
                    "Expert Insights",
                    "Real-World Applications",
                    "Future Outlook"
                ]
            }

            outline = outlines.get(content_type, outlines["blog"])

            # Estimate word count
            word_counts = {
                "short": 1000,
                "medium": 2500,
                "long": 5000
            }
            estimated_words = word_counts.get(target_length, 2500)

            return {
                "keyword": keyword.keyword,
                "outline": outline,
                "estimated_word_count": estimated_words,
                "key_topics": [
                    keyword.keyword,
                    f"{keyword.keyword} benefits",
                    f"{keyword.keyword} implementation",
                    f"{keyword.keyword} best practices"
                ]
            }

        except Exception as e:
            logger.error("outline_generation_failed", extra={"error": str(e)})
            raise

    async def get_faqs(
        self,
        db: AsyncSession,
        project_id: UUID,
        keyword_id: Optional[UUID] = None,
        approved_only: bool = False
    ) -> list[GeneratedFAQ]:
        """Get generated FAQs."""
        query = select(GeneratedFAQ).where(
            GeneratedFAQ.project_id == project_id
        )

        if keyword_id:
            query = query.where(GeneratedFAQ.keyword_id == keyword_id)

        if approved_only:
            query = query.where(GeneratedFAQ.approved == True)

        query = query.order_by(desc(GeneratedFAQ.created_at))

        result = await db.execute(query)
        return result.scalars().all()

    async def approve_faq(
        self,
        db: AsyncSession,
        faq_id: UUID
    ) -> GeneratedFAQ:
        """Approve an FAQ entry."""
        try:
            result = await db.execute(
                select(GeneratedFAQ).where(GeneratedFAQ.id == faq_id)
            )
            faq = result.scalar_one_or_none()

            if not faq:
                raise ValueError(f"FAQ {faq_id} not found")

            faq.approved = True
            await db.flush()

            logger.info("faq_approved", extra={"faq_id": str(faq_id)})
            return faq

        except Exception as e:
            logger.error("faq_approve_failed", extra={"error": str(e)})
            raise

    async def get_recommendations_summary(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> dict:
        """Get summary of recommendations for a project."""
        result = await db.execute(
            select(ContentRecommendation)
            .where(ContentRecommendation.project_id == project_id)
        )
        all_recs = result.scalars().all()

        pending = sum(1 for r in all_recs if not r.user_action)
        implemented = sum(1 for r in all_recs if r.user_action == "implemented")
        rejected = sum(1 for r in all_recs if r.user_action == "rejected")

        # Get FAQs
        faq_result = await db.execute(
            select(GeneratedFAQ)
            .where(GeneratedFAQ.project_id == project_id)
        )
        all_faqs = faq_result.scalars().all()
        approved_faqs = sum(1 for f in all_faqs if f.approved)

        return {
            "total_recommendations": len(all_recs),
            "pending_recommendations": pending,
            "implemented_recommendations": implemented,
            "rejected_recommendations": rejected,
            "total_faqs": len(all_faqs),
            "approved_faqs": approved_faqs,
            "by_type": {
                "optimize": sum(1 for r in all_recs if r.recommendation_type == "optimize"),
                "expand": sum(1 for r in all_recs if r.recommendation_type == "expand"),
                "faq": sum(1 for r in all_recs if r.recommendation_type == "faq"),
                "rewrite": sum(1 for r in all_recs if r.recommendation_type == "rewrite")
            }
        }
