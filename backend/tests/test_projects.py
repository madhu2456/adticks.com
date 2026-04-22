"""Tests for /api/projects/* CRUD endpoints.

Verifies create, list, get, update, and delete operations, including
authorization checks that prevent users from accessing each other's projects.
"""
import uuid

import pytest


# ---------------------------------------------------------------------------
# POST /api/projects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_project_success(client, auth_headers):
    """Authenticated user can create a project and gets 201 back."""
    response = await client.post(
        "/api/projects",
        json={"brand_name": "TestBrand", "domain": "testbrand.com", "industry": "SaaS"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["brand_name"] == "TestBrand"
    assert body["domain"] == "testbrand.com"
    assert body["industry"] == "SaaS"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_project_unauthenticated(client):
    """Creating a project without a token returns 401."""
    response = await client.post(
        "/api/projects",
        json={"brand_name": "Anon", "domain": "anon.com"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/projects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_own_projects(client, test_user, test_project, auth_headers):
    """Listing projects returns only the authenticated user's projects."""
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "data" in body
    project_ids = [p["id"] for p in body["data"]]
    assert str(test_project.id) in project_ids


@pytest.mark.asyncio
async def test_list_projects_excludes_other_users(
    client, db_session, test_project, second_user, second_auth_headers
):
    """A user cannot see projects belonging to another user."""
    response = await client.get("/api/projects", headers=second_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "data" in body
    ids = [p["id"] for p in body["data"]]
    assert str(test_project.id) not in ids


# ---------------------------------------------------------------------------
# GET /api/projects/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_own_project(client, test_project, auth_headers):
    """Owner can fetch their project by ID."""
    response = await client.get(
        f"/api/projects/{test_project.id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(test_project.id)


@pytest.mark.asyncio
async def test_get_project_wrong_user(
    client, test_project, second_auth_headers
):
    """Another user gets 404 when trying to access someone else's project."""
    response = await client.get(
        f"/api/projects/{test_project.id}", headers=second_auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_nonexistent(client, auth_headers):
    """Fetching a non-existent project ID returns 404."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/projects/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/projects/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_project(client, test_project, auth_headers):
    """Owner can update all fields of a project."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"brand_name": "UpdatedBrand", "domain": "updated.com", "industry": "E-commerce"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "UpdatedBrand"
    assert body["domain"] == "updated.com"
    assert body["industry"] == "E-commerce"


@pytest.mark.asyncio
async def test_update_project_partial(client, test_project, auth_headers):
    """Owner can do a partial update (only some fields)."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "Finance"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["industry"] == "Finance"
    # Other fields unchanged
    assert body["brand_name"] == test_project.brand_name


# ---------------------------------------------------------------------------
# DELETE /api/projects/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_project(client, test_user, db_session, auth_headers):
    """Owner can delete their own project; response is 204 No Content."""
    import uuid
    from app.models.project import Project

    project = Project(
        id=uuid.uuid4(),
        user_id=test_user.id,
        brand_name="ToDelete",
        domain="todelete.com",
    )
    db_session.add(project)
    await db_session.commit()

    response = await client.delete(
        f"/api/projects/{project.id}", headers=auth_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_users_project(
    client, test_project, second_auth_headers
):
    """A user cannot delete another user's project; expects 404."""
    response = await client.delete(
        f"/api/projects/{test_project.id}", headers=second_auth_headers
    )
    assert response.status_code == 404
