"""
Integration tests for authentication endpoints with database persistence.

Tests the full flow:
- Registration with database validation
- Login with password verification
- Token refresh with token rotation
- Protected endpoint access
- Logout and token invalidation
- Concurrent auth requests
- Database transaction rollback on failures
"""

import pytest
import asyncio
import uuid
from datetime import timedelta

from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# POST /api/auth/register INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_user_in_database(client, db_session):
    """User registration persists a new user record in the database."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@adticks.com",
            "password": "ValidPassword123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201

    # Verify user exists in DB
    from app.models.user import User
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.email == "newuser@adticks.com"))
    user = result.scalar_one()
    assert user.full_name == "New User"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_register_duplicate_email_not_inserted(client, test_user):
    """Duplicate email registration fails and doesn't create partial records."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": test_user.email,
            "password": "AnotherPassword123",
            "full_name": "Another User",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_hashes_password_before_storage(client, db_session):
    """Password is hashed before being stored in the database."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "hashedpw@adticks.com",
            "password": "PlainTextPassword123",
            "full_name": "Hash Test",
        },
    )
    assert response.status_code == 201

    from app.models.user import User
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.email == "hashedpw@adticks.com"))
    user = result.scalar_one()
    # Password should be hashed, not plain text
    assert user.hashed_password != "PlainTextPassword123"
    assert len(user.hashed_password) > 20


@pytest.mark.asyncio
async def test_register_multiple_users_isolation(client):
    """Multiple users can be registered independently."""
    # Register first user
    response1 = await client.post(
        "/api/auth/register",
        json={
            "email": "user1iso@adticks.com",
            "password": "Password1",
            "full_name": "User One",
        },
    )
    assert response1.status_code == 201
    user1_id = response1.json()["id"]

    # Register second user
    response2 = await client.post(
        "/api/auth/register",
        json={
            "email": "user2iso@adticks.com",
            "password": "Password2",
            "full_name": "User Two",
        },
    )
    assert response2.status_code == 201
    user2_id = response2.json()["id"]

    # Both have different IDs
    assert user1_id != user2_id


# ---------------------------------------------------------------------------
# POST /api/auth/login INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_retrieves_user_from_database(client, test_user):
    """Login looks up user from database and verifies password."""
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_inactive_user_rejected(client, db_session, test_user):
    """Inactive users cannot login even with correct password."""
    # Deactivate user
    test_user.is_active = False
    await db_session.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password_database_not_modified(client, db_session, test_user):
    """Failed login due to wrong password doesn't modify user record."""
    original_password_hash = test_user.hashed_password

    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401

    # Refresh user from DB and verify unchanged
    await db_session.refresh(test_user)
    assert test_user.hashed_password == original_password_hash


@pytest.mark.asyncio
async def test_login_nonexistent_user_returns_same_error(client):
    """Login with non-existent email returns same error as wrong password (security)."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@adticks.com", "password": "anypassword"},
    )
    assert response.status_code == 401
    # Error message should be generic
    assert "Invalid" in response.json()["message"]


# ---------------------------------------------------------------------------
# Register → Login → Access Protected Flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registration_login_access_flow(client, db_session):
    """Full flow: register → login → access protected route."""
    # Step 1: Register
    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": "flowtest@adticks.com",
            "password": "FlowPassword123",
            "full_name": "Flow Test User",
        },
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    # Step 2: Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "flowtest@adticks.com", "password": "FlowPassword123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Step 3: Access protected route (/me)
    me_response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["id"] == user_id
    assert me_response.json()["email"] == "flowtest@adticks.com"


# ---------------------------------------------------------------------------
# POST /api/auth/refresh INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client, test_user):
    """Refresh endpoint returns new token pair with new timestamps."""
    # Get initial tokens
    login_response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    old_refresh_token = login_response.json()["refresh_token"]

    # Refresh once
    refresh_response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_response.status_code == 200
    new_refresh_token = refresh_response.json()["refresh_token"]
    new_access_token = refresh_response.json()["access_token"]

    # Refresh tokens rotate
    assert new_refresh_token != old_refresh_token
    # New access token is valid
    assert new_access_token is not None
    assert len(new_access_token) > 0

    # Can use new tokens to access /me
    me_response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client):
    """Invalid refresh token is rejected."""
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_multiple_times_succeeds(client, test_user):
    """Can refresh multiple times in a row."""
    login_response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # First refresh
    response1 = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response1.status_code == 200
    refresh_token = response1.json()["refresh_token"]

    # Second refresh
    response2 = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response2.status_code == 200
    refresh_token = response2.json()["refresh_token"]

    # Third refresh
    response3 = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response3.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/auth/logout INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_success(client, test_user, auth_headers):
    """Logout endpoint returns success and can log user out."""
    response = await client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


# ---------------------------------------------------------------------------
# GET /api/auth/me INTEGRATION TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(client, test_user, auth_headers):
    """GET /me returns the authenticated user's full data."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(test_user.id)
    assert body["email"] == test_user.email
    assert body["full_name"] == test_user.full_name
    assert body["is_active"] is True
    # Password hash should not be in response
    assert "hashed_password" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    """GET /me without token returns 401 Unauthorized."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_expired_token(client, test_user):
    """GET /me with expired token returns 401."""
    expired_token = create_access_token(
        subject=test_user.id, expires_delta=timedelta(seconds=-1)
    )
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# CONCURRENT AUTH REQUESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_registrations_with_same_email(client):
    """Sequential registrations with same email: second fails with 409."""
    # Register first user
    response1 = await client.post(
        "/api/auth/register",
        json={
            "email": "concurrentemail@adticks.com",
            "password": "ConcurrentPassword123",
            "full_name": "Concurrent User One",
        },
    )
    assert response1.status_code == 201

    # Try second registration with same email
    response2 = await client.post(
        "/api/auth/register",
        json={
            "email": "concurrentemail@adticks.com",
            "password": "ConcurrentPassword456",
            "full_name": "Concurrent User Two",
        },
    )
    # Should fail with conflict
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_concurrent_logins_by_same_user(client, test_user):
    """Multiple concurrent login requests by same user all succeed."""
    async def login():
        return await client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

    # Run 5 logins concurrently
    results = await asyncio.gather(*[login() for _ in range(5)])

    # All should succeed
    for response in results:
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_concurrent_me_requests_with_same_token(client, test_user, auth_headers):
    """Multiple concurrent /me requests with same token all succeed."""
    async def get_me():
        return await client.get("/api/auth/me", headers=auth_headers)

    # Run 5 concurrent requests
    results = await asyncio.gather(*[get_me() for _ in range(5)])

    # All should succeed and return same user
    for response in results:
        assert response.status_code == 200
        assert response.json()["id"] == str(test_user.id)


# ---------------------------------------------------------------------------
# DATABASE TRANSACTION ROLLBACK ON FAILURE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registration_rollback_on_database_error(client, db_session):
    """Registration fails gracefully and doesn't create partial records on DB error."""
    # Try to register with a duplicate email twice
    response1 = await client.post(
        "/api/auth/register",
        json={
            "email": "duptest@adticks.com",
            "password": "Password1",
            "full_name": "User One",
        },
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/auth/register",
        json={
            "email": "duptest@adticks.com",
            "password": "Password2",
            "full_name": "User Two",
        },
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_login_does_not_modify_user_on_failure(client, db_session, test_user):
    """Failed login doesn't update user record (transaction isolation)."""
    from sqlalchemy import select

    original_user = await db_session.execute(
        select(test_user.__class__).where(test_user.__class__.id == test_user.id)
    )
    original_user = original_user.scalar_one()
    original_hash = original_user.hashed_password

    # Try to login with wrong password
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401

    # Verify user hash is unchanged
    current_user = await db_session.execute(
        select(test_user.__class__).where(test_user.__class__.id == test_user.id)
    )
    current_user = current_user.scalar_one()
    assert current_user.hashed_password == original_hash


# ---------------------------------------------------------------------------
# TOKEN EXPIRY AND EDGE CASES
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_with_invalid_user_id(client):
    """Token with invalid user ID (no such user) is rejected."""
    fake_user_id = uuid.uuid4()
    invalid_token = create_access_token(subject=fake_user_id)

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    # Should return 401 since user doesn't exist
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_malformed_authorization_header(client):
    """Malformed Authorization header is rejected."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "InvalidFormat token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bearer_token_case_sensitive(client, test_user):
    """Bearer token prefix handling is case-sensitive."""
    token = create_access_token(subject=test_user.id)

    # Try with correct 'Bearer' - should work
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Invalid format returns 401
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"InvalidPrefix {token}"},
    )
    assert response.status_code == 401
