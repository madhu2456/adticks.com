"""Tests for /api/auth/* endpoints.

Covers registration, login, and the /me (current-user) endpoints including
edge cases such as duplicate email, wrong password, missing credentials,
and expired / invalid JWT tokens.
"""
from datetime import timedelta

import pytest

from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client):
    """A new user can register and receives a 201 with user data."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@adticks.com",
            "password": "StrongPassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@adticks.com"
    assert body["full_name"] == "New User"
    assert body["is_active"] is True
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    """Registering with an already-used email returns 409 Conflict."""
    response = await client.post(
        "/api/auth/register",
        json={"email": test_user.email, "password": "AnotherPassword123"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """Invalid email format results in 422 Unprocessable Entity."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "validpassword"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client):
    """Missing password field results in 422 Unprocessable Entity."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "nopw@adticks.com"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Valid credentials return 200 with access + refresh tokens."""
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20
    assert len(body["refresh_token"]) > 20


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    """Wrong password returns 401 Unauthorized."""
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    """Login attempt with an email that does not exist returns 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_success(client, test_user):
    """A valid refresh token rotates and returns a fresh token pair."""
    login_response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """Invalid refresh token is rejected with 401."""
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not-a-valid-token"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_success(client, test_user, auth_headers):
    """Logout endpoint returns success response."""
    response = await client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_authenticated(client, test_user, auth_headers):
    """Authenticated request to /me returns current user data."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == test_user.email
    assert body["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_me_no_token(client):
    """Request to /me without a token returns 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    """A completely invalid (garbage) token returns 401."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer this.is.garbage"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_expired_token(client, test_user):
    """An expired JWT returns 401 Unauthorized."""
    expired_token = create_access_token(
        subject=test_user.id, expires_delta=timedelta(seconds=-1)
    )
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
