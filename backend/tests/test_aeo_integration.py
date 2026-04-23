"""
Integration tests for AEO API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.keyword import Keyword


class TestAEO_APIEndpoints:
    """Test AEO API endpoints."""

    @pytest.mark.asyncio
    async def test_get_aeo_summary(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test getting AEO dashboard summary."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/summary",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_keywords" in data
        assert "ai_visibility_count" in data
        assert "featured_snippet_count" in data
        assert "recommendation_count" in data

    @pytest.mark.asyncio
    async def test_check_ai_visibility(
        self, client: AsyncClient, user_token: str, project: Project, keyword: Keyword
    ):
        """Test checking AI visibility."""
        response = await client.post(
            "/api/aeo/check-visibility",
            json={
                "keyword_id": str(keyword.id),
                "ai_models": ["chatgpt", "perplexity", "claude"]
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code in [202, 200]
        data = response.json()
        assert "status" in data
        assert "keyword_id" in data

    @pytest.mark.asyncio
    async def test_get_chatgpt_visibility(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving ChatGPT visibility data."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/chatgpt",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_perplexity_visibility(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving Perplexity visibility data."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/perplexity",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_claude_visibility(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving Claude visibility data."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/claude",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_visibility_trends(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving visibility trends."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/trends",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_snippet_history(
        self, client: AsyncClient, user_token: str, keyword: Keyword
    ):
        """Test getting snippet history."""
        response = await client.get(
            f"/api/aeo/keywords/{keyword.id}/snippets",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_paa_queries(
        self, client: AsyncClient, user_token: str, keyword: Keyword
    ):
        """Test getting PAA queries."""
        response = await client.get(
            f"/api/aeo/keywords/{keyword.id}/paa",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_check_snippet_opportunity(
        self, client: AsyncClient, user_token: str, keyword: Keyword
    ):
        """Test checking snippet opportunity."""
        response = await client.post(
            "/api/aeo/snippets/check-opportunity",
            json={"keyword_id": str(keyword.id)},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert "difficulty" in data
        assert "potential_traffic_gain" in data

    @pytest.mark.asyncio
    async def test_get_snippet_summary(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test getting snippet summary."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/snippets/summary",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_keywords" in data
        assert "with_snippet" in data
        assert "without_snippet" in data
        assert "snippet_percentage" in data

    @pytest.mark.asyncio
    async def test_generate_recommendations(
        self, client: AsyncClient, user_token: str, keyword: Keyword
    ):
        """Test generating content recommendations."""
        response = await client.post(
            "/api/aeo/content/generate-recommendations",
            json={"keyword_id": str(keyword.id)},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "recommendation_type" in data[0]
            assert "recommendation_text" in data[0]

    @pytest.mark.asyncio
    async def test_get_recommendations(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving recommendations."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/recommendations",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_mark_recommendation_action(
        self, client: AsyncClient, user_token: str, project: Project, keyword: Keyword
    ):
        """Test marking recommendation action."""
        # First generate recommendations
        gen_response = await client.post(
            "/api/aeo/content/generate-recommendations",
            json={"keyword_id": str(keyword.id)},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert gen_response.status_code == 200
        recommendations = gen_response.json()

        if len(recommendations) > 0:
            rec_id = recommendations[0]["id"]

            # Mark as implemented
            response = await client.put(
                f"/api/aeo/recommendations/{rec_id}",
                json={"user_action": "implemented"},
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_action"] == "implemented"

    @pytest.mark.asyncio
    async def test_generate_faq_from_paa(
        self, client: AsyncClient, user_token: str, project: Project, keyword: Keyword
    ):
        """Test generating FAQ from PAA."""
        # Create a PAA query first
        await client.post(
            f"/api/aeo/keywords/{keyword.id}/paa",
            json={
                "paa_query": "How to optimize?",
                "answer_source_url": "https://example.com",
                "answer_snippet": "Answer text",
                "position": 1
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # This would need to be added to the actual implementation
        # For now, test the endpoint exists
        response = await client.get(
            f"/api/aeo/projects/{project.id}/faqs",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_faqs(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test retrieving FAQs."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/faqs",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_generate_content_outline(
        self, client: AsyncClient, user_token: str, keyword: Keyword
    ):
        """Test generating content outline."""
        response = await client.post(
            "/api/aeo/content/generate-outline",
            json={
                "keyword_id": str(keyword.id),
                "content_type": "blog",
                "target_length": "medium"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "outline" in data
        assert "estimated_word_count" in data
        assert isinstance(data["outline"], list)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient, project: Project):
        """Test that unauthorized requests are rejected."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/summary"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_forbidden_access_different_user(
        self, client: AsyncClient, user_token: str, project: Project, other_user_token: str
    ):
        """Test that users can't access other user's projects."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/visibility/summary",
            headers={"Authorization": f"Bearer {other_user_token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_project_id(self, client: AsyncClient, user_token: str):
        """Test accessing non-existent project."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/aeo/projects/{fake_id}/visibility/summary",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_visibility_trends_with_filters(
        self, client: AsyncClient, user_token: str, project: Project, keyword: Keyword
    ):
        """Test visibility trends with filters."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/trends",
            params={
                "keyword_id": str(keyword.id),
                "ai_model": "chatgpt",
                "limit": 10
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_recommendations_with_type_filter(
        self, client: AsyncClient, user_token: str, project: Project
    ):
        """Test filtering recommendations by type."""
        response = await client.get(
            f"/api/aeo/projects/{project.id}/recommendations",
            params={"rec_type": "optimize"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

