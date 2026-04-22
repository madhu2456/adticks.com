"""Tests for the /health endpoint."""
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    """GET /health should return HTTP 200 with status=ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "environment" in body
