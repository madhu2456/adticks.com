"""
Tests for AEO (AI-Powered SEO) Module.

Tests for:
- AI visibility tracking
- Featured snippets and PAA tracking
- Content recommendations and FAQ generation
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.keyword import Keyword
from app.models.user import User
from app.models.aeo import (
    ContentRecommendation,
)
from app.services.ai_visibility import AIVisibilityService
from app.services.snippet_tracking import SnippetTrackingService
from app.services.content_recommendations import ContentRecommendationService


class TestAEOVisibilityService:
    """Test AI Visibility Service."""

    @pytest.mark.asyncio
    async def test_store_visibility_check(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test storing visibility check result."""
        service = AIVisibilityService()

        visibility = await service.store_visibility_check(
            db=db,
            project_id=project.id,
            keyword_id=keyword.id,
            ai_model="chatgpt",
            is_mentioned=True,
            mention_context="Brand was mentioned in response",
            position=1,
            confidence_score=0.95
        )

        assert visibility.project_id == project.id
        assert visibility.keyword_id == keyword.id
        assert visibility.ai_model == "chatgpt"
        assert visibility.is_mentioned is True
        assert visibility.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_get_latest_visibility(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test retrieving latest visibility record."""
        service = AIVisibilityService()

        # Store multiple records
        await service.store_visibility_check(
            db, project.id, keyword.id, "chatgpt", False, None, None, 0.85
        )
        await db.commit()

        visibility2 = await service.store_visibility_check(
            db, project.id, keyword.id, "chatgpt", True, "Mentioned", 2, 0.92
        )
        await db.commit()

        # Get latest
        latest = await service.get_latest_visibility(
            db, project.id, keyword.id, "chatgpt"
        )

        assert latest.id == visibility2.id
        assert latest.is_mentioned is True

    @pytest.mark.asyncio
    async def test_get_visibility_summary(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test getting visibility summary across models."""
        service = AIVisibilityService()

        # Add records for different models
        await service.store_visibility_check(
            db, project.id, keyword.id, "chatgpt", True, "Mentioned", 1, 0.95
        )
        await service.store_visibility_check(
            db, project.id, keyword.id, "perplexity", False, None, None, 0.88
        )
        await service.store_visibility_check(
            db, project.id, keyword.id, "claude", True, "Mentioned", 2, 0.90
        )
        await db.commit()

        summary = await service.get_visibility_summary(db, project.id, keyword.id)

        assert summary["overall_mentioned"] is True
        assert len(summary["mentioned_models"]) == 2
        assert "chatgpt" in summary["mentioned_models"]
        assert "claude" in summary["mentioned_models"]

    @pytest.mark.asyncio
    async def test_calculate_trends(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test trend calculation."""
        service = AIVisibilityService()

        # Add multiple records
        for i in range(10):
            await service.store_visibility_check(
                db, project.id, keyword.id, "chatgpt",
                is_mentioned=(i % 2 == 0),
                mention_context="Test" if i % 2 == 0 else None,
                position=1 if i % 2 == 0 else None,
                confidence_score=0.9
            )
        await db.commit()

        trend = await service.calculate_trends(
            db, project.id, keyword.id, "chatgpt"
        )

        assert trend.ai_model == "chatgpt"
        assert trend.mention_count == 5
        assert trend.visibility_percentage > 0

    @pytest.mark.asyncio
    async def test_check_chatgpt_visibility(self):
        """Test ChatGPT visibility check (mock)."""
        service = AIVisibilityService()

        is_mentioned, context, position, confidence = await service.check_chatgpt_visibility(
            "seo", "AdTicks", "adticks.com"
        )

        assert isinstance(is_mentioned, bool)
        assert confidence >= 0.0 and confidence <= 1.0

    @pytest.mark.asyncio
    async def test_check_perplexity_visibility(self):
        """Test Perplexity visibility check (mock)."""
        service = AIVisibilityService()

        is_mentioned, context, position, confidence = await service.check_perplexity_visibility(
            "digital marketing", "AdTicks", "adticks.com"
        )

        assert isinstance(is_mentioned, bool)
        assert confidence >= 0.0 and confidence <= 1.0

    @pytest.mark.asyncio
    async def test_check_claude_visibility(self):
        """Test Claude visibility check (mock)."""
        service = AIVisibilityService()

        is_mentioned, context, position, confidence = await service.check_claude_visibility(
            "content optimization", "AdTicks", "adticks.com"
        )

        assert isinstance(is_mentioned, bool)
        assert confidence >= 0.0 and confidence <= 1.0


class TestSnippetTrackingService:
    """Test Snippet Tracking Service."""

    @pytest.mark.asyncio
    async def test_create_snippet_tracking(self, db: AsyncSession, keyword: Keyword):
        """Test creating snippet tracking record."""
        service = SnippetTrackingService()

        snippet = await service.create_or_update_snippet(
            db=db,
            keyword_id=keyword.id,
            has_snippet=True,
            snippet_type="featured",
            snippet_text="Sample snippet text",
            snippet_source_url="https://example.com",
            position_before_snippet=3
        )

        assert snippet.keyword_id == keyword.id
        assert snippet.has_snippet is True
        assert snippet.snippet_type == "featured"

    @pytest.mark.asyncio
    async def test_get_current_snippet(self, db: AsyncSession, keyword: Keyword):
        """Test getting current snippet."""
        service = SnippetTrackingService()

        # Create two records
        await service.create_or_update_snippet(
            db, keyword.id, True, "featured", "Text 1", None, 3
        )
        await db.commit()

        snippet2 = await service.create_or_update_snippet(
            db, keyword.id, False, None, None, None, None
        )
        await db.commit()

        current = await service.get_current_snippet(db, keyword.id)

        assert current.id == snippet2.id

    @pytest.mark.asyncio
    async def test_snippet_lost_tracking(self, db: AsyncSession, keyword: Keyword):
        """Test tracking when snippet is lost."""
        service = SnippetTrackingService()

        # Create snippet
        snippet1 = await service.create_or_update_snippet(
            db, keyword.id, True, "featured", "Text", None, 2
        )
        await db.commit()

        # Snippet is lost
        await service.create_or_update_snippet(
            db, keyword.id, False, None, None, None, None
        )
        await db.commit()

        # Get first snippet again
        db.refresh(snippet1)
        assert snippet1.lost_date is not None

    @pytest.mark.asyncio
    async def test_add_paa_query(self, db: AsyncSession, keyword: Keyword):
        """Test adding PAA query."""
        service = SnippetTrackingService()

        paa = await service.add_paa_query(
            db=db,
            keyword_id=keyword.id,
            paa_query="How to do X?",
            answer_source_url="https://example.com",
            answer_snippet="Answer snippet",
            position=1
        )

        assert paa.keyword_id == keyword.id
        assert paa.paa_query == "How to do X?"
        assert paa.position == 1

    @pytest.mark.asyncio
    async def test_paa_deduplication(self, db: AsyncSession, keyword: Keyword):
        """Test that duplicate PAA queries are not added."""
        service = SnippetTrackingService()

        query_text = "Same question?"

        paa1 = await service.add_paa_query(db, keyword.id, query_text, None, None, None)
        await db.commit()

        paa2 = await service.add_paa_query(db, keyword.id, query_text, None, None, None)
        await db.commit()

        # Should return the same record
        assert paa1.id == paa2.id

    @pytest.mark.asyncio
    async def test_get_paa_queries(self, db: AsyncSession, keyword: Keyword):
        """Test retrieving PAA queries."""
        service = SnippetTrackingService()

        # Add multiple queries
        await service.add_paa_query(db, keyword.id, "Question 1?", None, None, None)
        await service.add_paa_query(db, keyword.id, "Question 2?", None, None, None)
        await db.commit()

        queries = await service.get_paa_queries(db, keyword.id)

        assert len(queries) == 2

    @pytest.mark.asyncio
    async def test_check_snippet_opportunity(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test snippet opportunity check."""
        service = SnippetTrackingService()

        opportunity = await service.check_snippet_opportunity(db, keyword.id)

        assert "recommendation" in opportunity
        assert "difficulty" in opportunity
        assert opportunity["difficulty"] in ["easy", "medium", "hard"]

    @pytest.mark.asyncio
    async def test_get_snippet_summary(self, db: AsyncSession, project: Project):
        """Test getting snippet summary for project."""
        service = SnippetTrackingService()

        # Create some keywords and snippets
        kw1 = Keyword(project_id=project.id, keyword="test1")
        kw2 = Keyword(project_id=project.id, keyword="test2")
        kw3 = Keyword(project_id=project.id, keyword="test3")
        db.add_all([kw1, kw2, kw3])
        await db.flush()

        await service.create_or_update_snippet(db, kw1.id, True, "featured", None, None, 2)
        await service.create_or_update_snippet(db, kw2.id, False, None, None, None, None)
        await db.commit()

        summary = await service.get_snippet_summary(db, project.id)

        assert summary["total_keywords"] == 3
        assert summary["with_snippet"] == 1
        assert summary["without_snippet"] >= 1


class TestContentRecommendationService:
    """Test Content Recommendation Service."""

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test generating recommendations."""
        service = ContentRecommendationService()

        recommendations = await service.generate_recommendations(
            db=db,
            project_id=project.id,
            keyword_id=keyword.id,
            keyword_text=keyword.keyword
        )

        assert len(recommendations) > 0
        assert all(isinstance(r, ContentRecommendation) for r in recommendations)
        assert all(r.recommendation_type in ["optimize", "faq", "expand", "rewrite"] for r in recommendations)

    @pytest.mark.asyncio
    async def test_get_recommendations(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test retrieving recommendations."""
        service = ContentRecommendationService()

        # Generate some
        await service.generate_recommendations(
            db, project.id, keyword.id, keyword.keyword
        )
        await db.commit()

        recommendations = await service.get_recommendations(db, project.id)

        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_mark_recommendation_action(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test marking recommendation action."""
        service = ContentRecommendationService()

        recommendations = await service.generate_recommendations(
            db, project.id, keyword.id, keyword.keyword
        )
        await db.commit()

        rec_id = recommendations[0].id

        updated = await service.mark_recommendation_action(
            db, rec_id, "implemented"
        )

        assert updated.user_action == "implemented"

    @pytest.mark.asyncio
    async def test_generate_faq_from_paa(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test generating FAQ from PAA."""
        service = SnippetTrackingService()
        rec_service = ContentRecommendationService()

        # Create PAA
        paa = await service.add_paa_query(
            db, keyword.id, "Test question?", None, None, None
        )
        await db.commit()

        # Generate FAQ
        faq = await rec_service.generate_faq_from_paa(
            db, project.id, keyword.id, paa.id
        )

        assert faq.keyword_id == keyword.id
        assert faq.paa_id == paa.id
        assert faq.question == "Test question?"

    @pytest.mark.asyncio
    async def test_generate_content_outline(self, db: AsyncSession, keyword: Keyword):
        """Test content outline generation."""
        service = ContentRecommendationService()

        outline = await service.generate_content_outline(
            db, keyword.id, "blog", "medium"
        )

        assert "outline" in outline
        assert "estimated_word_count" in outline
        assert len(outline["outline"]) > 0

    @pytest.mark.asyncio
    async def test_get_faqs(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test retrieving FAQs."""
        service = SnippetTrackingService()
        rec_service = ContentRecommendationService()

        # Create FAQs
        paa = await service.add_paa_query(db, keyword.id, "Q1?", None, None, None)
        await db.commit()

        await rec_service.generate_faq_from_paa(
            db, project.id, keyword.id, paa.id
        )
        await db.commit()

        faqs = await rec_service.get_faqs(db, project.id)

        assert len(faqs) > 0

    @pytest.mark.asyncio
    async def test_approve_faq(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test approving FAQ."""
        service = SnippetTrackingService()
        rec_service = ContentRecommendationService()

        # Create FAQ
        paa = await service.add_paa_query(db, keyword.id, "Q?", None, None, None)
        await db.commit()

        faq = await rec_service.generate_faq_from_paa(
            db, project.id, keyword.id, paa.id
        )
        await db.commit()

        approved_faq = await rec_service.approve_faq(db, faq.id)

        assert approved_faq.approved is True

    @pytest.mark.asyncio
    async def test_get_recommendations_summary(self, db: AsyncSession, project: Project, keyword: Keyword):
        """Test getting recommendations summary."""
        service = ContentRecommendationService()

        # Generate some recommendations
        await service.generate_recommendations(
            db, project.id, keyword.id, keyword.keyword
        )
        await db.commit()

        summary = await service.get_recommendations_summary(db, project.id)

        assert "total_recommendations" in summary
        assert "pending_recommendations" in summary
        assert summary["total_recommendations"] > 0


# Fixtures
@pytest.fixture
def db() -> AsyncSession:
    """Database session fixture."""
    pytest.skip("Use conftest fixtures")


@pytest.fixture
def project(db: AsyncSession, user: User) -> Project:
    """Create test project."""
    pytest.skip("Use conftest fixtures")


@pytest.fixture
def keyword(db: AsyncSession, project: Project) -> Keyword:
    """Create test keyword."""
    pytest.skip("Use conftest fixtures")


@pytest.fixture
def user(db: AsyncSession) -> User:
    """Create test user."""
    pytest.skip("Use conftest fixtures")
