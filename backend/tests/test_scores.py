"""Tests for the scores API endpoints (/api/scores/*)."""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.score import Score


# ---------------------------------------------------------------------------
# GET /api/scores/{project_id}  — latest score
# ---------------------------------------------------------------------------

async def test_get_latest_score_no_score_returns_404(client, test_project, auth_headers):
    """GET /api/scores/{id} returns 404 when no scores exist yet."""
    response = await client.get(
        f"/api/scores/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "scan" in response.json()["detail"].lower()


async def test_get_latest_score_returns_most_recent(
    client, test_project, auth_headers, db_session
):
    """GET /api/scores/{id} returns the most recent Score row."""
    older = Score(
        id=uuid.uuid4(),
        project_id=test_project.id,
        visibility_score=0.10,
        impact_score=0.05,
        sov_score=0.08,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    newer = Score(
        id=uuid.uuid4(),
        project_id=test_project.id,
        visibility_score=0.55,
        impact_score=0.40,
        sov_score=0.30,
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )
    db_session.add(older)
    db_session.add(newer)
    await db_session.commit()

    response = await client.get(
        f"/api/scores/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["visibility_score"] == pytest.approx(0.55)
    assert data["impact_score"] == pytest.approx(0.40)
    assert data["sov_score"] == pytest.approx(0.30)


async def test_get_latest_score_unauthenticated_returns_401(client, test_project):
    """GET /api/scores/{id} without auth returns 401."""
    response = await client.get(f"/api/scores/{test_project.id}")
    assert response.status_code == 401


async def test_get_latest_score_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/scores/{id} with wrong owner returns 404."""
    response = await client.get(
        f"/api/scores/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_get_latest_score_nonexistent_project_returns_404(client, auth_headers):
    """GET /api/scores/{id} with unknown project_id returns 404."""
    response = await client.get(
        f"/api/scores/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/scores/{project_id}/history
# ---------------------------------------------------------------------------

async def test_get_score_history_empty(client, test_project, auth_headers):
    """GET /api/scores/{id}/history returns 200 with empty list when no scores exist."""
    response = await client.get(
        f"/api/scores/{test_project.id}/history",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 50


async def test_get_score_history_returns_all_scores_sorted(
    client, test_project, auth_headers, db_session
):
    """GET /api/scores/{id}/history returns multiple scores sorted newest first."""
    s1 = Score(
        id=uuid.uuid4(),
        project_id=test_project.id,
        visibility_score=0.20,
        impact_score=0.15,
        sov_score=0.10,
        timestamp=datetime(2024, 3, 1, tzinfo=timezone.utc),
    )
    s2 = Score(
        id=uuid.uuid4(),
        project_id=test_project.id,
        visibility_score=0.35,
        impact_score=0.28,
        sov_score=0.18,
        timestamp=datetime(2024, 5, 1, tzinfo=timezone.utc),
    )
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    response = await client.get(
        f"/api/scores/{test_project.id}/history",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    # Newest first
    assert data["data"][0]["visibility_score"] == pytest.approx(0.35)
    assert data["data"][1]["visibility_score"] == pytest.approx(0.20)


async def test_get_score_history_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/scores/{id}/history with wrong owner returns 404."""
    response = await client.get(
        f"/api/scores/{test_project.id}/history",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_get_score_history_nonexistent_project_returns_404(client, auth_headers):
    """GET /api/scores/{id}/history with unknown project_id returns 404."""
    response = await client.get(
        f"/api/scores/{uuid.uuid4()}/history",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_get_score_history_respects_limit(
    client, test_project, auth_headers, db_session
):
    """GET /api/scores/{id}/history?limit=1 returns only one score."""
    for i in range(3):
        db_session.add(Score(
            id=uuid.uuid4(),
            project_id=test_project.id,
            visibility_score=float(i) / 10,
            impact_score=0.1,
            sov_score=0.1,
            timestamp=datetime(2024, i + 1, 1, tzinfo=timezone.utc),
        ))
    await db_session.commit()

    response = await client.get(
        f"/api/scores/{test_project.id}/history?limit=1",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["total"] == 3
    assert data["limit"] == 1
