"""
Tests for SEO Suite API endpoints.

Covers:
- RankHistory endpoints with pagination
- SerpFeatures endpoints
- CompetitorKeywords endpoints with pagination
- Backlinks endpoints with pagination
- Caching behavior
- Error handling and authorization
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.keyword import Keyword
from app.models.seo import RankHistory, SerpFeatures, CompetitorKeywords, Backlinks
from app.core.security import hash_password
from app.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="seo@adticks.com",
        hashed_password=hash_password("testpass123"),
        full_name="SEO User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid.uuid4(),
        user_id=test_user.id,
        brand_name="SEO Test Brand",
        domain="seotest.com",
        industry="Technology",
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest.fixture
async def test_keyword(db_session: AsyncSession, test_project: Project) -> Keyword:
    """Create a test keyword."""
    keyword = Keyword(
        id=uuid.uuid4(),
        project_id=test_project.id,
        keyword="best seo tools",
        intent="commercial",
        difficulty=45.5,
        volume=2400,
    )
    db_session.add(keyword)
    await db_session.commit()
    return keyword


@pytest.fixture
async def test_token(test_user: User) -> str:
    """Generate test JWT token."""
    from app.core.security import create_access_token
    return create_access_token(subject=test_user.id)


# ============================================================================
# RankHistory Tests
# ============================================================================
class TestRankHistory:
    """Tests for rank history endpoints."""

    async def test_get_rank_history_empty(
        self, client: AsyncClient, test_project: Project, test_token: str
    ):
        """Test getting rank history when none exist."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 50
        assert data["has_more"] is False

    async def test_get_rank_history_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test getting rank history with existing data."""
        # Create rank history entries
        for i in range(5):
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=test_keyword.id,
                rank=10 + i,
                search_volume=2400,
                cpc=5.5,
                device="desktop",
                location="US",
                timestamp=datetime.now(tz=timezone.utc) - timedelta(days=i),
            )
            db_session.add(rank_history)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["total"] == 5
        assert data["has_more"] is False

    async def test_get_rank_history_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test pagination on rank history."""
        # Create 150 rank history entries
        for i in range(150):
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=test_keyword.id,
                rank=10 + (i % 100),
                search_volume=2400,
                cpc=5.5,
                device="desktop" if i % 2 == 0 else "mobile",
                location="US",
                timestamp=datetime.now(tz=timezone.utc) - timedelta(hours=i),
            )
            db_session.add(rank_history)
        await db_session.commit()

        # First page
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history?limit=50",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 50
        assert data["total"] == 150
        assert data["has_more"] is True

        # Second page
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history?skip=50&limit=50",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 50
        assert data["skip"] == 50
        assert data["has_more"] is True

    async def test_get_rank_history_filter_by_device(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test filtering rank history by device."""
        # Create entries for both devices
        for i in range(10):
            device = "desktop" if i % 2 == 0 else "mobile"
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=test_keyword.id,
                rank=10 + i,
                search_volume=2400,
                cpc=5.5,
                device=device,
                location="US",
            )
            db_session.add(rank_history)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history?device=desktop",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert all(item["device"] == "desktop" for item in data["data"])

    async def test_get_rank_history_filter_by_keyword(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test filtering rank history by keyword."""
        # Create another keyword
        keyword2 = Keyword(
            id=uuid.uuid4(),
            project_id=test_project.id,
            keyword="seo tools 2024",
            intent="informational",
            difficulty=35.0,
            volume=1200,
        )
        db_session.add(keyword2)
        await db_session.commit()

        # Create entries for both keywords
        for i in range(5):
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=test_keyword.id,
                rank=10 + i,
                search_volume=2400,
                cpc=5.5,
                device="desktop",
                location="US",
            )
            db_session.add(rank_history)

        for i in range(3):
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=keyword2.id,
                rank=15 + i,
                search_volume=1200,
                cpc=3.5,
                device="desktop",
                location="US",
            )
            db_session.add(rank_history)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history?keyword_id={test_keyword.id}",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert all(item["keyword_id"] == str(test_keyword.id) for item in data["data"])

    async def test_get_rank_history_days_filter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test filtering rank history by days."""
        now = datetime.now(tz=timezone.utc)
        # Create entries spanning 60 days
        for i in range(60):
            rank_history = RankHistory(
                id=uuid.uuid4(),
                keyword_id=test_keyword.id,
                rank=10 + (i % 50),
                search_volume=2400,
                cpc=5.5,
                device="desktop",
                location="US",
                timestamp=now - timedelta(days=i),
            )
            db_session.add(rank_history)
        await db_session.commit()

        # Request last 30 days
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history?days=30",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 30

    async def test_rank_history_unauthorized(
        self, client: AsyncClient, test_project: Project
    ):
        """Test unauthorized access to rank history."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/keywords/history"
        )
        assert response.status_code == 401

    async def test_rank_history_project_not_found(
        self, client: AsyncClient, test_token: str
    ):
        """Test rank history for non-existent project."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/seo/projects/{fake_id}/keywords/history",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 404


# ============================================================================
# SerpFeatures Tests
# ============================================================================
class TestSerpFeatures:
    """Tests for SERP features endpoints."""

    async def test_get_serp_features_not_found(
        self, client: AsyncClient, test_keyword: Keyword, test_token: str
    ):
        """Test getting SERP features when none exist."""
        response = await client.get(
            f"/api/seo/keywords/{test_keyword.id}/serp-features",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 404

    async def test_get_serp_features(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_keyword: Keyword,
        test_token: str,
    ):
        """Test getting SERP features."""
        serp_features = SerpFeatures(
            id=uuid.uuid4(),
            keyword_id=test_keyword.id,
            featured_snippet=True,
            rich_snippets=True,
            ads=True,
            knowledge_panel=False,
        )
        db_session.add(serp_features)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/keywords/{test_keyword.id}/serp-features",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["featured_snippet"] is True
        assert data["rich_snippets"] is True
        assert data["ads"] is True
        assert data["knowledge_panel"] is False

    async def test_serp_features_unauthorized(self, client: AsyncClient, test_keyword: Keyword):
        """Test unauthorized access to SERP features."""
        response = await client.get(
            f"/api/seo/keywords/{test_keyword.id}/serp-features"
        )
        assert response.status_code == 401

    async def test_serp_features_keyword_not_found(self, client: AsyncClient, test_token: str):
        """Test SERP features for non-existent keyword."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/seo/keywords/{fake_id}/serp-features",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 404


# ============================================================================
# CompetitorKeywords Tests
# ============================================================================
class TestCompetitorKeywords:
    """Tests for competitor keywords endpoints."""

    async def test_get_competitor_keywords_empty(
        self, client: AsyncClient, test_project: Project, test_token: str
    ):
        """Test getting competitor keywords when none exist."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/competitors/keywords",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    async def test_get_competitor_keywords_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test getting competitor keywords with data."""
        # Create competitor keywords
        for i in range(3):
            comp_keywords = CompetitorKeywords(
                id=uuid.uuid4(),
                project_id=test_project.id,
                competitor_domain=f"competitor{i}.com",
                keywords=["keyword1", "keyword2", "keyword3"],
                count=3,
            )
            db_session.add(comp_keywords)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/competitors/keywords",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["total"] == 3

    async def test_get_competitor_keywords_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test pagination on competitor keywords."""
        # Create 100 competitor keyword entries
        for i in range(100):
            comp_keywords = CompetitorKeywords(
                id=uuid.uuid4(),
                project_id=test_project.id,
                competitor_domain=f"competitor{i}.com",
                keywords=[f"keyword{j}" for j in range(5)],
                count=5,
            )
            db_session.add(comp_keywords)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/competitors/keywords?limit=25",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 25
        assert data["total"] == 100
        assert data["has_more"] is True

    async def test_get_competitor_keywords_filter_by_domain(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test filtering competitor keywords by domain."""
        # Create keywords for different competitors
        for i in range(3):
            comp_keywords = CompetitorKeywords(
                id=uuid.uuid4(),
                project_id=test_project.id,
                competitor_domain="specific.com" if i == 0 else f"other{i}.com",
                keywords=["keyword1", "keyword2"],
                count=2,
            )
            db_session.add(comp_keywords)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/competitors/keywords?competitor_domain=specific.com",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["competitor_domain"] == "specific.com"

    async def test_competitor_keywords_unauthorized(
        self, client: AsyncClient, test_project: Project
    ):
        """Test unauthorized access to competitor keywords."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/competitors/keywords"
        )
        assert response.status_code == 401


# ============================================================================
# Backlinks Tests
# ============================================================================
class TestBacklinks:
    """Tests for backlinks endpoints."""

    async def test_get_backlinks_empty(
        self, client: AsyncClient, test_project: Project, test_token: str
    ):
        """Test getting backlinks when none exist."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    async def test_get_backlinks_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test getting backlinks with data."""
        # Create backlinks
        for i in range(5):
            backlink = Backlinks(
                id=uuid.uuid4(),
                project_id=test_project.id,
                referring_domain=f"domain{i}.com",
                authority_score=50.0 + i * 5,
            )
            db_session.add(backlink)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["total"] == 5

    async def test_get_backlinks_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test pagination on backlinks."""
        # Create 75 backlinks
        for i in range(75):
            backlink = Backlinks(
                id=uuid.uuid4(),
                project_id=test_project.id,
                referring_domain=f"domain{i}.com",
                authority_score=25.0 + (i % 50),
            )
            db_session.add(backlink)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks?limit=30",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 30
        assert data["total"] == 75
        assert data["has_more"] is True

    async def test_get_backlinks_sorted_by_authority(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test backlinks are sorted by authority score."""
        # Create backlinks with different scores
        scores = [25.0, 75.0, 50.0, 90.0, 35.0]
        for i, score in enumerate(scores):
            backlink = Backlinks(
                id=uuid.uuid4(),
                project_id=test_project.id,
                referring_domain=f"domain{i}.com",
                authority_score=score,
            )
            db_session.add(backlink)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        returned_scores = [item["authority_score"] for item in data["data"]]
        assert returned_scores == [90.0, 75.0, 50.0, 35.0, 25.0]

    async def test_get_backlinks_filter_by_authority(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project: Project,
        test_token: str,
    ):
        """Test filtering backlinks by minimum authority."""
        # Create backlinks with varying scores
        for i in range(10):
            backlink = Backlinks(
                id=uuid.uuid4(),
                project_id=test_project.id,
                referring_domain=f"domain{i}.com",
                authority_score=10.0 + i * 10,  # 10, 20, 30, ..., 100
            )
            db_session.add(backlink)
        await db_session.commit()

        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks?min_authority=60",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert all(item["authority_score"] >= 60.0 for item in data["data"])

    async def test_backlinks_unauthorized(
        self, client: AsyncClient, test_project: Project
    ):
        """Test unauthorized access to backlinks."""
        response = await client.get(
            f"/api/seo/projects/{test_project.id}/backlinks"
        )
        assert response.status_code == 401
