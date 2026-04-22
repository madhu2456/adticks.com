"""Tests for the SEO API endpoints (/api/seo/*)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


from app.models.keyword import Keyword, Ranking


# ---------------------------------------------------------------------------
# POST /api/seo/keywords
# ---------------------------------------------------------------------------

async def test_trigger_keywords_returns_202(client, test_project, auth_headers):
    """POST /api/seo/keywords returns 202 and queued status."""
    mock_task = MagicMock()
    mock_task.id = "task-abc123"
    with patch("app.tasks.seo_tasks.generate_keywords_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/seo/keywords?project_id={test_project.id}",
            json={"keyword": "seo tool"},
            headers=auth_headers,
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert "keyword_id" in data


async def test_trigger_keywords_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """POST /api/seo/keywords with wrong owner returns 404."""
    response = await client.post(
        f"/api/seo/keywords?project_id={test_project.id}",
        json={"keyword": "seo tool"},
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_trigger_keywords_unauthenticated_returns_401(client, test_project):
    """POST /api/seo/keywords without auth returns 401."""
    response = await client.post(
        f"/api/seo/keywords?project_id={test_project.id}",
        json={"keyword": "seo tool"},
    )
    assert response.status_code == 401


async def test_trigger_keywords_nonexistent_project_returns_404(client, auth_headers):
    """POST /api/seo/keywords with unknown project_id returns 404."""
    response = await client.post(
        f"/api/seo/keywords?project_id={uuid.uuid4()}",
        json={"keyword": "seo tool"},
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/seo/audit
# ---------------------------------------------------------------------------

async def test_trigger_audit_returns_202(client, test_project, auth_headers):
    """POST /api/seo/audit returns 202 and queued status."""
    mock_task = MagicMock()
    mock_task.id = "audit-task-999"
    with patch("app.tasks.seo_tasks.run_seo_audit_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/seo/audit?project_id={test_project.id}",
            headers=auth_headers,
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"


async def test_trigger_audit_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """POST /api/seo/audit with wrong owner returns 404."""
    response = await client.post(
        f"/api/seo/audit?project_id={test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_trigger_audit_nonexistent_project_returns_404(client, auth_headers):
    """POST /api/seo/audit with unknown project returns 404."""
    response = await client.post(
        f"/api/seo/audit?project_id={uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/seo/rankings/{project_id}
# ---------------------------------------------------------------------------

async def test_get_rankings_empty(client, test_project, auth_headers):
    """GET /api/seo/rankings returns 200 with empty data when no rankings exist."""
    response = await client.get(
        f"/api/seo/rankings/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["total"] == 0


async def test_get_rankings_with_data(client, test_project, auth_headers, db_session):
    """GET /api/seo/rankings returns ranking rows from the DB."""
    keyword = Keyword(
        id=uuid.uuid4(),
        project_id=test_project.id,
        keyword="best seo tool",
    )
    db_session.add(keyword)
    await db_session.commit()

    ranking = Ranking(
        id=uuid.uuid4(),
        keyword_id=keyword.id,
        position=5,
        url="https://optivio.com/blog/seo",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(ranking)
    await db_session.commit()

    response = await client.get(
        f"/api/seo/rankings/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    data = body["data"]
    assert len(data) == 1
    assert data[0]["position"] == 5
    assert data[0]["url"] == "https://optivio.com/blog/seo"


async def test_get_rankings_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/seo/rankings with wrong owner returns 404."""
    response = await client.get(
        f"/api/seo/rankings/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/seo/gaps/{project_id}
# ---------------------------------------------------------------------------

async def test_get_gaps_returns_200(client, test_project, auth_headers):
    """GET /api/seo/gaps returns 200 with project_id and gaps key."""
    response = await client.get(
        f"/api/seo/gaps/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    # Paginated response with data key
    assert "data" in data or "gaps" in data


async def test_get_gaps_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/seo/gaps with wrong owner returns 404."""
    response = await client.get(
        f"/api/seo/gaps/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/seo/technical/{project_id}
# ---------------------------------------------------------------------------

async def test_get_technical_seo_returns_200(client, test_project, auth_headers):
    """GET /api/seo/technical returns 200 with project_id and findings key."""
    response = await client.get(
        f"/api/seo/technical/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    # Paginated response with data key
    assert "data" in data or "findings" in data


async def test_get_technical_seo_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/seo/technical with wrong owner returns 404."""
    response = await client.get(
        f"/api/seo/technical/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404
