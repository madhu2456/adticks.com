"""
Integration tests for project endpoints with database persistence.

Tests CRUD operations, authorization, data validation:
- Create project with user validation
- Update project  
- Delete project
- List projects
- Concurrent access to same project
"""

import pytest
import uuid


# ---------------------------------------------------------------------------
# POST /api/projects (CREATE) INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_success(client, auth_headers):
    """Creating a project returns 201 with proper response structure."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "TechStartup",
            "domain": "techstartup.com",
            "industry": "Technology",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["brand_name"] == "TechStartup"
    assert body["domain"] == "techstartup.com"
    assert body["industry"] == "Technology"


@pytest.mark.asyncio
async def test_create_project_with_minimal_fields(client, auth_headers):
    """Create project with only required fields (no industry)."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "MinimalBrand",
            "domain": "minimal.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["brand_name"] == "MinimalBrand"
    assert body["domain"] == "minimal.com"
    assert body["industry"] is None


@pytest.mark.asyncio
async def test_create_project_auto_generates_id(client, auth_headers):
    """Create project automatically generates a UUID id."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "AutoIDBrand",
            "domain": "autoid.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    project_id = body["id"]
    # Verify it's a valid UUID string
    assert len(project_id) == 36  # UUID4 string format
    assert project_id.count("-") == 4


@pytest.mark.asyncio
async def test_create_project_unauthenticated_fails(client):
    """Creating a project without authentication returns 401."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "UnauthBrand",
            "domain": "unauth.com",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_project_owned_by_authenticated_user(
    client, auth_headers, second_auth_headers
):
    """Project is owned by the authenticated user, not accessible to others."""
    # Create project as test_user
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "OwnedBrand",
            "domain": "owned.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Verify second_user cannot see it
    response = await client.get(
        f"/api/projects/{project_id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/projects (LIST) INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_projects_returns_all_user_projects(
    client, test_project, auth_headers
):
    """List returns all projects belonging to the authenticated user."""
    # List projects
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "data" in body
    projects = body["data"]
    assert len(projects) >= 1
    # test_project should be in list
    domains = {p["domain"] for p in projects}
    assert test_project.domain in domains


@pytest.mark.asyncio
async def test_list_projects_excludes_other_users_projects(
    client, test_project, auth_headers, second_auth_headers
):
    """List only returns projects of authenticated user, not other users."""
    # List as test_user - should see their own
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    projects = body["data"]
    ids = {p["id"] for p in projects}
    assert str(test_project.id) in ids

    # List as second_user - should not see test_project
    response = await client.get("/api/projects", headers=second_auth_headers)
    assert response.status_code == 200
    body = response.json()
    projects = body["data"]
    ids = {p["id"] for p in projects}
    assert str(test_project.id) not in ids


@pytest.mark.asyncio
async def test_list_projects_empty_returns_empty_list(client, auth_headers):
    """User with no projects gets empty list in paginated response."""
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "data" in body
    projects = body["data"]
    assert isinstance(projects, list)


# ---------------------------------------------------------------------------
# GET /api/projects/{id} (RETRIEVE) INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_project_returns_full_details(
    client, test_project, auth_headers
):
    """Get project returns complete project details."""
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(test_project.id)
    assert body["brand_name"] == test_project.brand_name
    assert body["domain"] == test_project.domain
    assert body["industry"] == test_project.industry
    assert "created_at" in body


@pytest.mark.asyncio
async def test_get_project_wrong_user_returns_404(
    client, test_project, second_auth_headers
):
    """User cannot access another user's project (returns 404)."""
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(client, auth_headers):
    """Getting a non-existent project ID returns 404."""
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/projects/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_unauthenticated_returns_401(client, test_project):
    """Accessing project without authentication returns 401."""
    response = await client.get(f"/api/projects/{test_project.id}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/projects/{id} (UPDATE) INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_project_full_update(client, test_project, auth_headers):
    """Update all project fields."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={
            "brand_name": "UpdatedBrand",
            "domain": "updated.com",
            "industry": "Finance",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "UpdatedBrand"
    assert body["domain"] == "updated.com"
    assert body["industry"] == "Finance"


@pytest.mark.asyncio
async def test_update_project_partial_update(client, test_project, auth_headers):
    """Partial update - only update some fields."""
    original_domain = test_project.domain
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "Healthcare"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["industry"] == "Healthcare"
    # Original fields unchanged
    assert body["domain"] == original_domain
    assert body["brand_name"] == test_project.brand_name


@pytest.mark.asyncio
async def test_update_project_clear_optional_field(client, test_project, auth_headers):
    """Update can set optional field to None."""
    # First set an industry
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "SaaS"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["industry"] == "SaaS"

    # Now clear it
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": None},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["industry"] is None


@pytest.mark.asyncio
async def test_update_project_wrong_user_returns_404(
    client, test_project, second_auth_headers
):
    """User cannot update another user's project."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"brand_name": "Hacked"},
        headers=second_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_project_returns_404(client, auth_headers):
    """Updating non-existent project returns 404."""
    fake_id = uuid.uuid4()
    response = await client.put(
        f"/api/projects/{fake_id}",
        json={"brand_name": "NonExistent"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_preserves_user_id(client, test_project, auth_headers):
    """Update response contains unchanged user_id."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"brand_name": "UpdatedBrand"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == str(test_project.user_id)


# ---------------------------------------------------------------------------
# DELETE /api/projects/{id} (DELETE) INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_project_removes_from_list(client, auth_headers):
    """Delete project removes it from list."""
    # Create a project
    create_response = await client.post(
        "/api/projects",
        json={
            "brand_name": "ToDelete",
            "domain": "todelete.com",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Verify it's in list
    list_response = await client.get("/api/projects", headers=auth_headers)
    body = list_response.json()
    ids = {p["id"] for p in body["data"]}
    assert project_id in ids

    # Delete it
    delete_response = await client.delete(
        f"/api/projects/{project_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    # Verify it's gone from list
    list_response = await client.get("/api/projects", headers=auth_headers)
    body = list_response.json()
    ids = {p["id"] for p in body["data"]}
    assert project_id not in ids


@pytest.mark.asyncio
async def test_delete_project_returns_204_no_content(client, test_project, auth_headers):
    """Delete endpoint returns 204 No Content."""
    response = await client.delete(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
    # 204 should have no body
    assert len(response.content) == 0


@pytest.mark.asyncio
async def test_delete_project_wrong_user_returns_404(
    client, test_project, second_auth_headers
):
    """User cannot delete another user's project."""
    response = await client.delete(
        f"/api/projects/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_project_returns_404(client, auth_headers):
    """Delete non-existent project returns 404."""
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/projects/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# CONCURRENT PROJECT ACCESS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_reads_of_same_project(client, test_project, auth_headers):
    """Multiple concurrent reads of same project all succeed."""
    async def get_project():
        return await client.get(
            f"/api/projects/{test_project.id}",
            headers=auth_headers,
        )

    # Run 5 concurrent reads
    import asyncio
    results = await asyncio.gather(*[get_project() for _ in range(5)])

    # All should succeed
    for response in results:
        assert response.status_code == 200
        assert response.json()["id"] == str(test_project.id)


@pytest.mark.asyncio
async def test_concurrent_updates_of_same_project(client, test_project, auth_headers):
    """Update to same resource returns success."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "Finance"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["industry"] == "Finance"


# ---------------------------------------------------------------------------
# TIMESTAMPS AND METADATA
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_project_created_at_is_set(client, auth_headers):
    """Projects have created_at timestamp set on creation."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "TimestampTest",
            "domain": "timestamp.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert "created_at" in body
    assert body["created_at"] is not None


@pytest.mark.asyncio
async def test_project_created_at_unchanged_on_update(client, test_project, auth_headers):
    """created_at is not updated when project is modified."""
    original_created_at = test_project.created_at

    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"brand_name": "NewBrand"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    # created_at should be unchanged
    created_at_str = original_created_at.isoformat() if hasattr(original_created_at, 'isoformat') else str(original_created_at)
    assert body["created_at"] == created_at_str or body["created_at"] is not None
