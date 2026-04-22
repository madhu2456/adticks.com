"""Tests for the insights API endpoints (/api/insights/*)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models.recommendation import Recommendation
from app.models.score import Score


# ---------------------------------------------------------------------------
# GET /api/insights/{project_id}
# ---------------------------------------------------------------------------

async def test_get_insights_empty_list(client, test_project, auth_headers):
    """GET /api/insights returns 200 with empty data when no recommendations exist."""
    response = await client.get(
        f"/api/insights/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["total"] == 0


async def test_get_insights_unauthenticated_returns_401(client, test_project):
    """GET /api/insights without auth returns 401."""
    response = await client.get(f"/api/insights/{test_project.id}")
    assert response.status_code == 401


async def test_get_insights_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/insights with wrong owner returns 404."""
    response = await client.get(
        f"/api/insights/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_get_insights_with_recommendations_returns_sorted(
    client, test_project, auth_headers, db_session
):
    """GET /api/insights returns recommendations sorted by priority ascending."""
    low_priority = Recommendation(
        id=uuid.uuid4(),
        project_id=test_project.id,
        text="Low priority recommendation",
        priority=4,
        category="seo",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    high_priority = Recommendation(
        id=uuid.uuid4(),
        project_id=test_project.id,
        text="High priority recommendation",
        priority=1,
        category="ai_visibility",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(low_priority)
    db_session.add(high_priority)
    await db_session.commit()

    response = await client.get(
        f"/api/insights/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 2
    # sorted by priority asc — priority 1 first
    assert data[0]["priority"] == 1
    assert data[1]["priority"] == 4


# ---------------------------------------------------------------------------
# GET /api/insights/{project_id}/summary
# ---------------------------------------------------------------------------

async def test_get_insights_summary_null_scores(client, test_project, auth_headers):
    """GET /api/insights/{id}/summary returns 200 with null scores when no Score exists."""
    response = await client.get(
        f"/api/insights/{test_project.id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    assert data["latest_scores"]["visibility_score"] is None
    assert data["latest_scores"]["impact_score"] is None
    assert data["latest_scores"]["sov_score"] is None
    assert data["latest_scores"]["timestamp"] is None
    assert data["unread_recommendations"] == 0


async def test_get_insights_summary_with_score(
    client, test_project, auth_headers, db_session
):
    """GET /api/insights/{id}/summary returns real scores when a Score exists."""
    score = Score(
        id=uuid.uuid4(),
        project_id=test_project.id,
        visibility_score=0.45,
        impact_score=0.38,
        sov_score=0.22,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(score)
    await db_session.commit()

    response = await client.get(
        f"/api/insights/{test_project.id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["latest_scores"]["visibility_score"] == pytest.approx(0.45)
    assert data["latest_scores"]["impact_score"] == pytest.approx(0.38)
    assert data["latest_scores"]["sov_score"] == pytest.approx(0.22)
    assert data["latest_scores"]["timestamp"] is not None


async def test_get_insights_summary_with_unread_recommendations(
    client, test_project, auth_headers, db_session
):
    """GET /api/insights/{id}/summary counts unread recommendations correctly."""
    rec1 = Recommendation(
        id=uuid.uuid4(),
        project_id=test_project.id,
        text="First unread rec",
        priority=2,
        category="seo",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    rec2 = Recommendation(
        id=uuid.uuid4(),
        project_id=test_project.id,
        text="Second unread rec",
        priority=3,
        category="content",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    rec3 = Recommendation(
        id=uuid.uuid4(),
        project_id=test_project.id,
        text="Already read rec",
        priority=1,
        category="ai_visibility",
        is_read=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([rec1, rec2, rec3])
    await db_session.commit()

    response = await client.get(
        f"/api/insights/{test_project.id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unread_recommendations"] == 2
    assert len(data["top_priorities"]) == 2


async def test_get_insights_summary_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/insights/{id}/summary with wrong owner returns 404."""
    response = await client.get(
        f"/api/insights/{test_project.id}/summary",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/insights/{project_id}/refresh
# ---------------------------------------------------------------------------

async def test_refresh_insights_returns_202(client, test_project, auth_headers):
    """POST /api/insights/{id}/refresh returns 202 and queued status."""
    mock_task = MagicMock()
    mock_task.id = "insights-task-123"
    with patch("app.workers.tasks.generate_insights_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/insights/{test_project.id}/refresh",
            headers=auth_headers,
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"


async def test_refresh_insights_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """POST /api/insights/{id}/refresh with wrong owner returns 404."""
    response = await client.post(
        f"/api/insights/{test_project.id}/refresh",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_refresh_insights_nonexistent_project_returns_404(client, auth_headers):
    """POST /api/insights/{id}/refresh with unknown project returns 404."""
    response = await client.post(
        f"/api/insights/{uuid.uuid4()}/refresh",
        headers=auth_headers,
    )
    assert response.status_code == 404
