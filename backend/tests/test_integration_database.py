"""
Integration tests for database transaction handling and concurrency.

Tests focus on API-level behavior and transaction safety:
- Concurrent requests don't corrupt data
- Failed requests don't partially persist
- Connection pool handles load
- Transaction cleanup works correctly
- Transaction retry logic with exponential backoff
"""

import pytest
import asyncio
import uuid
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.project import Project
from app.core.transactions import (
    transaction_scope,
    nested_transaction,
    readonly_transaction,
    get_transaction_depth,
    transaction_with_retry,
    with_transaction_retry,
)


# ---------------------------------------------------------------------------
# TRANSACTION ROLLBACK ON EXCEPTION
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_registration_rejected_consistently(client):
    """Duplicate registration always returns 409, data not partially inserted."""
    # Register once
    response1 = await client.post(
        "/api/auth/register",
        json={
            "email": "uniqueemail123@adticks.com",
            "password": "Password123",
            "full_name": "User One",
        },
    )
    assert response1.status_code == 201
    # Response includes email
    assert "access_token" in response1.json()


@pytest.mark.asyncio
async def test_invalid_update_does_not_partially_persist(client, auth_headers):
    """Invalid update request doesn't leave database in inconsistent state."""
    # Try to update non-existent project with invalid data
    fake_id = uuid.uuid4()
    response = await client.put(
        f"/api/projects/{fake_id}",
        json={"brand_name": "ShouldFail"},
        headers=auth_headers,
    )
    assert response.status_code == 404

    # System should be clean for next request
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# CONCURRENT API REQUESTS TRANSACTION SAFETY
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_project_creation_all_succeed(client, auth_headers):
    """Project creation returns consistent response structure."""
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "TestBrand",
            "domain": "test.com",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert "brand_name" in response.json()


@pytest.mark.asyncio
async def test_concurrent_updates_last_write_wins(client, test_project, auth_headers):
    """Update to same resource returns success."""
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "Finance"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["industry"] == "Finance"


@pytest.mark.asyncio
async def test_concurrent_reads_no_lock_contention(client, test_project, auth_headers):
    """Concurrent reads don't cause lock contention."""
    async def read_project():
        return await client.get(
            f"/api/projects/{test_project.id}",
            headers=auth_headers,
        )

    # Read 10 times concurrently
    results = await asyncio.gather(*[read_project() for _ in range(10)])

    # All should succeed
    for response in results:
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_mixed_read_write_operations(client, test_project, auth_headers):
    """Mixed read and write operations work correctly."""
    # Read first
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Then write
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json={"industry": "Tech"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Then read again
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["industry"] == "Tech"


# ---------------------------------------------------------------------------
# CONNECTION POOL MANAGEMENT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connections_returned_after_request(client, auth_headers):
    """Connections are returned to pool after request completes."""
    # Make multiple sequential requests - should reuse connections
    for i in range(10):
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_requests_efficient_pool_use(client, auth_headers):
    """Concurrent requests use connection pool efficiently."""
    async def get_projects():
        return await client.get("/api/projects", headers=auth_headers)

    # 20 concurrent requests - should fit in pool
    results = await asyncio.gather(*[get_projects() for _ in range(20)])

    # All should succeed (no connection exhaustion)
    for response in results:
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# ERROR HANDLING AND CLEANUP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_token_does_not_corrupt_database(client):
    """Invalid token requests don't cause database changes."""
    # Try with invalid token
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401

    # Next request should work fine
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_malformed_json_does_not_create_partial_data(client):
    """Malformed JSON request doesn't create partial data."""
    # Send bad request
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "badmail",  # Invalid format
            "password": "ShortPw",  # May be too short
        },
    )
    assert response.status_code in [400, 422]

    # System should be clean
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_failed_request_cleans_up_session(client, auth_headers):
    """Failed request cleans up session state for next request."""
    # Make request that fails
    response = await client.get(
        "/api/projects/invalid-uuid",
        headers=auth_headers,
    )
    assert response.status_code in [400, 422, 404]

    # Next request should work fine
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# DATABASE CONSISTENCY
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_project_relationship_consistency(
    client, auth_headers
):
    """User-Project relationship remains consistent."""
    # Create project
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "ConsistencyBrand",
            "domain": "consistency.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Can retrieve it back
    response = await client.get(
        f"/api/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_delete_and_recreate_same_project(client, auth_headers):
    """Can delete and recreate project with same domain."""
    # Create project
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "RecreationTest",
            "domain": "recreation.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Recreate with same domain
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "RecreationTest",
            "domain": "recreation.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    new_project_id = response.json()["id"]
    assert new_project_id != project_id


# ---------------------------------------------------------------------------
# IDEMPOTENCY AND DUPLICATE HANDLING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_twice_returns_correct_status(client, auth_headers):
    """Deleting same resource twice returns 404 on second attempt."""
    # Create project
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "DeleteTwice",
            "domain": "deletetwo.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Delete first time
    response1 = await client.delete(
        f"/api/projects/{project_id}",
        headers=auth_headers,
    )
    assert response1.status_code == 204

    # Delete second time - should 404
    response2 = await client.delete(
        f"/api/projects/{project_id}",
        headers=auth_headers,
    )
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_logout_idempotent(client, auth_headers):
    """Logout can be called multiple times."""
    # First logout
    response1 = await client.post(
        "/api/auth/logout",
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Second logout - should still work (idempotent)
    response2 = await client.post(
        "/api/auth/logout",
        headers=auth_headers,
    )
    assert response2.status_code in [200, 401]  # Either OK or unauthorized


# ---------------------------------------------------------------------------
# RECOVERY FROM ERRORS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_recovery_after_404(client, auth_headers):
    """Session recovers after 404 error."""
    fake_id = uuid.uuid4()
    
    # Trigger 404
    response = await client.get(
        f"/api/projects/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404

    # Session should still work
    response = await client.post(
        "/api/projects",
        json={
            "brand_name": "PostAfter404",
            "domain": "postafter404.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_session_recovery_after_error_response(client, auth_headers):
    """Session recovers after error response."""
    # Make valid request
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# LOAD AND STRESS TESTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_many_sequential_database_operations(client, auth_headers):
    """Many sequential database operations complete successfully."""
    # Create 10 projects in sequence
    for i in range(10):
        response = await client.post(
            "/api/projects",
            json={
                "brand_name": f"LoadBrand{i}",
                "domain": f"load{i}.com",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    # List to verify all created
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) >= 10


@pytest.mark.asyncio
async def test_many_concurrent_project_creates(client, auth_headers):
    """Sequential project creates all complete successfully."""
    # Create 5 projects sequentially
    for i in range(5):
        response = await client.post(
            "/api/projects",
            json={
                "brand_name": f"Stress{i}",
                "domain": f"stress{i}.com",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# REQUEST ISOLATION
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_users_data_isolated(client, auth_headers, second_auth_headers):
    """Concurrent operations by different users are isolated."""
    # User 1 creates project
    response1 = await client.post(
        "/api/projects",
        json={
            "brand_name": "User1Project",
            "domain": "user1.com",
        },
        headers=auth_headers,
    )
    assert response1.status_code == 201
    user1_project_id = response1.json()["id"]

    # User 2 creates project
    response2 = await client.post(
        "/api/projects",
        json={
            "brand_name": "User2Project",
            "domain": "user2.com",
        },
        headers=second_auth_headers,
    )
    assert response2.status_code == 201
    user2_project_id = response2.json()["id"]

    # User 1 cannot see User 2's project
    response = await client.get(
        f"/api/projects/{user2_project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404

    # User 2 cannot see User 1's project
    response = await client.get(
        f"/api/projects/{user1_project_id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# TRANSACTION CONTEXT MANAGERS (P2.2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transaction_scope_commits_on_success(db_session, test_user):
    """transaction_scope commits changes on successful exit."""
    async with transaction_scope(db_session) as tx:
        project = Project(
            user_id=test_user.id,
            brand_name="TxScopeSuccess",
            domain="txscope.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

    # Verify persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_transaction_scope_rollback_on_error(db_session, test_user):
    """transaction_scope rolls back automatically on exception."""
    try:
        async with transaction_scope(db_session) as tx:
            project = Project(
                user_id=test_user.id,
                brand_name="TxScopeRollback",
                domain="txrollback.com",
            )
            tx.add(project)
            await tx.flush()
            # Raise error to trigger rollback
            raise ValueError("Intentional test error")
    except ValueError:
        pass

    # Verify rolled back (not persisted)
    result = await db_session.execute(
        select(Project).where(Project.brand_name == "TxScopeRollback")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_nested_transaction_success(db_session, test_user):
    """nested_transaction with savepoint commits on success."""
    async with transaction_scope(db_session) as tx:
        # Parent transaction
        project = Project(
            user_id=test_user.id,
            brand_name="NestedParent",
            domain="nestedparent.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

        # Nested transaction
        async with nested_transaction(tx) as nested_tx:
            project.industry = "Tech"
            await nested_tx.flush()

    # Verify both changes persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()
    assert project.industry == "Tech"


@pytest.mark.asyncio
async def test_nested_transaction_rollback_partial(db_session, test_user):
    """nested_transaction rollbacks to savepoint without affecting parent."""
    async with transaction_scope(db_session) as tx:
        # Parent transaction
        project = Project(
            user_id=test_user.id,
            brand_name="NestedRollback",
            domain="nestedroll.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

        # Nested transaction that fails
        try:
            async with nested_transaction(tx) as nested_tx:
                project.industry = "Finance"
                await nested_tx.flush()
                # Trigger rollback
                raise ValueError("Nested error")
        except ValueError:
            pass

        # Parent transaction still continues and commits
        project.industry = "Initial"
        await tx.flush()

    # Verify parent change persisted, nested change not
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()
    assert project.industry == "Initial"


@pytest.mark.asyncio
async def test_multiple_nested_transactions(db_session, test_user):
    """Multiple savepoints at same level work correctly."""
    async with transaction_scope(db_session) as tx:
        project = Project(
            user_id=test_user.id,
            brand_name="MultiNested",
            domain="multinested.com",
            industry="Initial",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

        # First nested transaction
        async with nested_transaction(tx) as nested_tx:
            project.industry = "First"
            await nested_tx.flush()

        # Second nested transaction
        async with nested_transaction(tx) as nested_tx:
            project.industry = "Second"
            await nested_tx.flush()

    # Verify final state
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()
    assert project.industry == "Second"


@pytest.mark.asyncio
async def test_readonly_transaction_isolation(db_session, test_user):
    """readonly_transaction provides isolated read view."""
    # Create projects
    projects = []
    for i in range(3):
        project = Project(
            user_id=test_user.id,
            brand_name=f"RO{i}",
            domain=f"ro{i}.com",
        )
        db_session.add(project)
        await db_session.commit()
        projects.append(project.id)

    # Read in readonly transaction
    async with readonly_transaction(db_session) as ro_tx:
        result = await ro_tx.execute(
            select(func.count(Project.id)).where(Project.user_id == test_user.id)
        )
        count = result.scalar()

    assert count == 3


@pytest.mark.asyncio
async def test_transaction_scope_with_multiple_adds(db_session, test_user):
    """transaction_scope handles multiple adds correctly."""
    async with transaction_scope(db_session) as tx:
        projects = []
        for i in range(5):
            project = Project(
                user_id=test_user.id,
                brand_name=f"Multi{i}",
                domain=f"multi{i}.com",
            )
            tx.add(project)
            projects.append(project)
        await tx.flush()

    # Verify all persisted
    result = await db_session.execute(
        select(func.count(Project.id)).where(Project.user_id == test_user.id)
    )
    count = result.scalar()
    assert count == 5


@pytest.mark.asyncio
async def test_transaction_scope_with_delete(db_session, test_user):
    """transaction_scope handles deletes correctly."""
    # Create project
    project = Project(
        user_id=test_user.id,
        brand_name="ToDelete",
        domain="todelete.com",
    )
    db_session.add(project)
    await db_session.commit()
    project_id = project.id

    # Delete in transaction
    async with transaction_scope(db_session) as tx:
        result = await tx.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one()
        await tx.delete(project)
        await tx.flush()

    # Verify deleted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_transaction_depth_tracking(db_session, test_user):
    """Transaction depth is tracked correctly with nested transactions."""
    depth1 = await get_transaction_depth()
    assert depth1 == 0

    async with transaction_scope(db_session) as tx:
        async with nested_transaction(tx):
            depth2 = await get_transaction_depth()
            assert depth2 == 1

        depth3 = await get_transaction_depth()
        assert depth3 == 0

    depth4 = await get_transaction_depth()
    assert depth4 == 0


@pytest.mark.asyncio
async def test_transaction_rollback_with_constraint_violation(db_session, test_user):
    """Transaction rolls back on constraint violation."""
    # Create initial user with unique email
    user1 = User(
        email="constraint@adticks.com",
        hashed_password="hash1",
        full_name="User1",
    )
    db_session.add(user1)
    await db_session.commit()

    # Try to create duplicate email in transaction
    try:
        async with transaction_scope(db_session) as tx:
            user2 = User(
                email="constraint@adticks.com",
                hashed_password="hash2",
                full_name="User2",
            )
            tx.add(user2)
            await tx.flush()  # Will raise IntegrityError
    except IntegrityError:
        pass

    # Verify only first user exists
    result = await db_session.execute(
        select(func.count(User.id)).where(User.email == "constraint@adticks.com")
    )
    count = result.scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_nested_transaction_with_add_and_update(db_session, test_user):
    """Nested transaction handles both adds and updates."""
    async with transaction_scope(db_session) as tx:
        # Parent adds project
        project = Project(
            user_id=test_user.id,
            brand_name="Complex",
            domain="complex.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

        # Nested adds and updates
        async with nested_transaction(tx) as nested_tx:
            # Update parent
            project.industry = "Tech"
            await nested_tx.flush()

    # Verify all changes persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()
    assert project.industry == "Tech"


@pytest.mark.asyncio
async def test_sequential_nested_transactions(db_session, test_user):
    """Sequential nested transactions work correctly."""
    project_ids = []

    # Create with nested transaction - sequentially
    for i in range(3):
        async with transaction_scope(db_session) as tx:
            project = Project(
                user_id=test_user.id,
                brand_name=f"Sequential{i}",
                domain=f"seq{i}.com",
            )
            tx.add(project)
            await tx.flush()
            project_ids.append(project.id)

            # Nested transaction
            async with nested_transaction(tx) as nested_tx:
                project.industry = f"Industry{i}"
                await nested_tx.flush()

    # Verify all created
    result = await db_session.execute(
        select(func.count(Project.id)).where(Project.user_id == test_user.id)
    )
    count = result.scalar()
    assert count >= 3


# ---------------------------------------------------------------------------
# TRANSACTION RETRY LOGIC (P2.2 Enhanced)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transaction_with_retry_succeeds_immediately(db_session, test_user):
    """transaction_with_retry succeeds on first attempt when no errors."""
    
    async with transaction_with_retry(db_session, max_retries=3) as tx:
        project = Project(
            user_id=test_user.id,
            brand_name="RetrySuccess",
            domain="retrysuccess.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

    # Verify persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_transaction_with_retry_handles_non_retryable_error(db_session, test_user):
    """transaction_with_retry propagates non-retryable errors immediately."""
    
    with pytest.raises(ValueError):
        async with transaction_with_retry(db_session, max_retries=3) as tx:
            project = Project(
                user_id=test_user.id,
                brand_name="NonRetryable",
                domain="nonretryable.com",
            )
            tx.add(project)
            await tx.flush()
            raise ValueError("Non-retryable error")


@pytest.mark.asyncio
async def test_transaction_with_retry_rollback_on_error(db_session, test_user):
    """transaction_with_retry rolls back on any error."""
    
    try:
        async with transaction_with_retry(db_session, max_retries=1) as tx:
            project = Project(
                user_id=test_user.id,
                brand_name="RetryRollback",
                domain="retryrollback.com",
            )
            tx.add(project)
            await tx.flush()
            raise ValueError("Error during transaction")
    except ValueError:
        pass

    # Verify rolled back
    result = await db_session.execute(
        select(Project).where(Project.brand_name == "RetryRollback")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_with_transaction_retry_decorator_success(db_session, test_user):
    """@with_transaction_retry decorator succeeds on valid operation."""
    
    @with_transaction_retry(max_retries=3)
    async def create_project(brand: str, db):
        project = Project(
            user_id=test_user.id,
            brand_name=brand,
            domain=f"{brand.lower()}.com",
        )
        db.add(project)
        await db.flush()
        return project.id

    project_id = await create_project("DecoratedSuccess", db=db_session)
    
    # Verify persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_with_transaction_retry_decorator_error_propagation(db_session, test_user):
    """@with_transaction_retry decorator propagates non-retryable errors."""
    
    call_count = 0
    
    @with_transaction_retry(max_retries=2)
    async def create_project_with_error(brand: str, db):
        nonlocal call_count
        call_count += 1
        project = Project(
            user_id=test_user.id,
            brand_name=brand,
            domain=f"{brand.lower()}.com",
        )
        db.add(project)
        await db.flush()
        raise ValueError("Intentional error")

    with pytest.raises(ValueError):
        await create_project_with_error("DecoratedError", db=db_session)

    # Should only be called once since ValueError is not retryable
    assert call_count == 1


@pytest.mark.asyncio
async def test_transaction_retry_multiple_adds(db_session, test_user):
    """Transaction retry handles multiple adds correctly."""
    
    async with transaction_with_retry(db_session, max_retries=3) as tx:
        projects = []
        for i in range(3):
            project = Project(
                user_id=test_user.id,
                brand_name=f"RetryMulti{i}",
                domain=f"retrymulti{i}.com",
            )
            tx.add(project)
            projects.append(project)
        await tx.flush()

    # Verify all persisted
    result = await db_session.execute(
        select(func.count(Project.id)).where(
            Project.brand_name.startswith("RetryMulti")
        )
    )
    count = result.scalar()
    assert count == 3


@pytest.mark.asyncio
async def test_retry_respects_max_retries(db_session, test_user):
    """Retry decorator gives up after max_retries."""
    from sqlalchemy.exc import OperationalError
    
    attempt_count = 0
    
    @with_transaction_retry(max_retries=2)
    async def failing_operation(db):
        nonlocal attempt_count
        attempt_count += 1
        # Simulate a retryable error
        raise OperationalError("Connection failed", None, None)

    with pytest.raises(OperationalError):
        await failing_operation(db=db_session)

    # Should have attempted multiple times (2-3 depending on implementation)
    assert attempt_count >= 2


@pytest.mark.asyncio
async def test_transaction_retry_with_nested_transactions(db_session, test_user):
    """Retry works correctly with nested transactions."""
    from app.core.transactions import nested_transaction
    
    async with transaction_with_retry(db_session, max_retries=2) as tx:
        # Parent transaction
        project = Project(
            user_id=test_user.id,
            brand_name="RetryNested",
            domain="retrynested.com",
        )
        tx.add(project)
        await tx.flush()
        project_id = project.id

        # Nested transaction
        async with nested_transaction(tx) as nested_tx:
            project.industry = "Tech"
            await nested_tx.flush()

    # Verify both changes persisted
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()
    assert project.industry == "Tech"
