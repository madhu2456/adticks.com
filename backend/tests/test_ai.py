"""Tests for the AI API endpoints (/api/prompts/*, /api/scan/*, /api/results/*, /api/mentions/*)."""
import uuid
from unittest.mock import MagicMock, patch



# ---------------------------------------------------------------------------
# POST /api/prompts/generate
# ---------------------------------------------------------------------------

async def test_generate_prompts_returns_202(client, test_project, auth_headers):
    """POST /api/prompts/generate returns 202 and queued status."""
    mock_task = MagicMock()
    mock_task.id = "prompt-task-001"
    with patch("app.tasks.ai_tasks.generate_prompts_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/prompts/generate?project_id={test_project.id}",
            headers=auth_headers,
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"


async def test_generate_prompts_unauthenticated_returns_401(client, test_project):
    """POST /api/prompts/generate without auth returns 401."""
    response = await client.post(
        f"/api/prompts/generate?project_id={test_project.id}",
    )
    assert response.status_code == 401


async def test_generate_prompts_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """POST /api/prompts/generate with wrong owner returns 404."""
    response = await client.post(
        f"/api/prompts/generate?project_id={test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_generate_prompts_nonexistent_project_returns_404(client, auth_headers):
    """POST /api/prompts/generate with unknown project_id returns 404."""
    response = await client.post(
        f"/api/prompts/generate?project_id={uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/scan/run
# ---------------------------------------------------------------------------

async def test_run_scan_returns_202(client, test_project, auth_headers):
    """POST /api/scan/run returns 202 and queued status."""
    mock_task = MagicMock()
    mock_task.id = "scan-task-002"
    with patch("app.workers.tasks.run_full_scan_task.delay", return_value=mock_task):
        response = await client.post(
            f"/api/scan/run?project_id={test_project.id}",
            headers=auth_headers,
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"


async def test_run_scan_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """POST /api/scan/run with wrong owner returns 404."""
    response = await client.post(
        f"/api/scan/run?project_id={test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_run_scan_nonexistent_project_returns_404(client, auth_headers):
    """POST /api/scan/run with unknown project_id returns 404."""
    response = await client.post(
        f"/api/scan/run?project_id={uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/results/{project_id}
# ---------------------------------------------------------------------------

async def test_get_results_empty_list(client, test_project, auth_headers):
    """GET /api/results returns 200 with empty list when no results exist."""
    response = await client.get(
        f"/api/results/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 50


async def test_get_results_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/results with wrong owner returns 404."""
    response = await client.get(
        f"/api/results/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_get_results_nonexistent_project_returns_404(client, auth_headers):
    """GET /api/results with unknown project_id returns 404."""
    response = await client.get(
        f"/api/results/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/mentions/{project_id}
# ---------------------------------------------------------------------------

async def test_get_mentions_empty_list(client, test_project, auth_headers):
    """GET /api/mentions returns 200 with empty list when no mentions exist."""
    response = await client.get(
        f"/api/mentions/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 50


async def test_get_mentions_wrong_owner_returns_404(
    client, test_project, second_auth_headers
):
    """GET /api/mentions with wrong owner returns 404."""
    response = await client.get(
        f"/api/mentions/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_get_mentions_unauthenticated_returns_401(client, test_project):
    """GET /api/mentions without auth returns 401."""
    response = await client.get(f"/api/mentions/{test_project.id}")
    assert response.status_code == 401
