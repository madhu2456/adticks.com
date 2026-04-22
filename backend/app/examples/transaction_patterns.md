# Transaction Patterns Guide

This guide demonstrates best practices for using AdTicks transaction context managers in FastAPI endpoints and service methods.

## Overview

The transaction module provides three main context managers and one decorator for handling database transactions:

- **`transaction_scope()`** - Standard transaction with automatic rollback
- **`nested_transaction()`** - Savepoint-based nested transactions
- **`readonly_transaction()`** - Read-only transaction (no commit)
- **`@with_transaction`** - Decorator for automatic transaction wrapping

## 1. Simple Transaction Usage

### Basic Create Operation

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.transactions import transaction_scope
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()

@router.post("/users")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with explicit transaction control."""
    async with transaction_scope(db) as tx:
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        tx.add(user)
        await tx.flush()
        return UserResponse.from_orm(user)
    # Transaction automatically commits on exit (no exception)
```

### With Validation and Rollback

```python
@router.post("/users")
async def create_user_with_validation(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """User creation with validation that triggers rollback."""
    async with transaction_scope(db) as tx:
        # Check if email exists
        result = await tx.execute(
            select(User).where(User.email == payload.email)
        )
        if result.scalar_one_or_none():
            # Raises exception → automatic rollback
            raise ConflictError("Email already registered")
        
        # If we reach here, email doesn't exist
        user = User(email=payload.email)
        tx.add(user)
        await tx.flush()
        return user
```

## 2. Nested Transactions with Savepoints

### Two-Step Creation with Fallback

```python
from app.core.transactions import transaction_scope, nested_transaction

@router.post("/projects")
async def create_project_with_config(
    payload: ProjectCreateWithConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create project and apply configuration. Rollback config only if it fails."""
    async with transaction_scope(db) as tx:
        # Main transaction: create project
        project = Project(
            user_id=current_user.id,
            brand_name=payload.brand_name,
            domain=payload.domain,
        )
        tx.add(project)
        await tx.flush()

        # Nested transaction: apply configuration
        try:
            async with nested_transaction(tx) as nested_tx:
                for config_key, config_value in payload.config.items():
                    setting = ProjectSetting(
                        project_id=project.id,
                        key=config_key,
                        value=config_value,
                    )
                    nested_tx.add(setting)
                await nested_tx.flush()
        except ValueError as e:
            # Config failed, but project is still created
            logger.warning(f"Config failed for project {project.id}: {e}")
            # Outer transaction still commits the project

        return project
```

### Bulk Operations with Savepoints

```python
@router.post("/projects/{id}/import-keywords")
async def import_keywords(
    project_id: UUID,
    payload: KeywordImportPayload,
    db: AsyncSession = Depends(get_db),
):
    """Import keywords with savepoints to skip failed items."""
    async with transaction_scope(db) as tx:
        project = await tx.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        successful = []
        failed = []

        for keyword_data in payload.keywords:
            try:
                async with nested_transaction(tx) as nested_tx:
                    keyword = Keyword(
                        project_id=project.id,
                        term=keyword_data.term,
                        monthly_volume=keyword_data.volume,
                    )
                    nested_tx.add(keyword)
                    await nested_tx.flush()
                successful.append(keyword_data.term)
            except IntegrityError:
                # Keyword already exists, skip it
                failed.append(keyword_data.term)
                continue

        return {
            "imported": len(successful),
            "failed": len(failed),
            "keywords": successful,
            "errors": failed,
        }
```

## 3. Using the @with_transaction Decorator

### Simple Decorator Usage

```python
from app.core.transactions import with_transaction

@router.post("/users")
@with_transaction()
async def create_user_decorated(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cleaner syntax using decorator for transaction management."""
    user = User(email=payload.email)
    db.add(user)
    await db.flush()
    return user
    # Decorator handles commit/rollback automatically
```

### Decorator with Multiple Operations

```python
@router.put("/projects/{id}")
@with_transaction(auto_flush=True, auto_commit=True)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project with automatic transaction control."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404)

    # Update fields
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    # auto_flush=True ensures changes are persisted before return
    return project
```

## 4. Read-Only Transactions

### Consistent Data Reads

```python
from app.core.transactions import readonly_transaction

@router.get("/analytics/summary")
async def get_analytics_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate analytics report with consistent read isolation."""
    async with readonly_transaction(db) as ro_tx:
        # All queries within this context are isolated
        scores_result = await ro_tx.execute(
            select(Score).where(Score.project_id == project_id)
        )
        scores = scores_result.scalars().all()

        insights_result = await ro_tx.execute(
            select(Insight).where(Insight.project_id == project_id)
        )
        insights = insights_result.scalars().all()

        # Calculate metrics (no persistence)
        metrics = compute_metrics(scores, insights)
        return metrics
    # Transaction rolled back automatically (no changes committed)
```

## 5. Error Handling and Rollback

### Catching Specific Exceptions

```python
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import ConflictError, ValidationError

@router.post("/users")
async def create_user_with_error_handling(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Handle errors with specific rollback behavior."""
    try:
        async with transaction_scope(db) as tx:
            # Validate email format
            if not is_valid_email(payload.email):
                raise ValidationError("Invalid email format")

            user = User(email=payload.email)
            tx.add(user)
            await tx.flush()

            # Send welcome email (might fail)
            try:
                await send_welcome_email(user.email)
            except Exception as e:
                logger.warning(f"Email send failed: {e}")
                # Continue without rolling back user creation

            return user

    except ValidationError as e:
        # Validation errors → automatic rollback
        logger.warning(f"Validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError as e:
        # Unique constraint violation → already rolled back
        logger.warning(f"Integrity error: {e}")
        raise ConflictError("Email already registered")

    except Exception as e:
        # Unexpected errors → automatic rollback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 6. Concurrent Transaction Safety

### Multiple Concurrent Operations

```python
@router.post("/projects/{id}/sync")
async def sync_project_data(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sync external data with isolation from other concurrent requests."""
    async with transaction_scope(db) as tx:
        # Lock the project row to prevent concurrent syncs
        project = await tx.execute(
            select(Project)
            .where(Project.id == project_id)
            .with_for_update()  # Row-level lock
        )
        project = project.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404)

        # Fetch external data (outside transaction if possible)
        external_data = await fetch_external_api()

        # Update project within transaction
        project.last_synced_at = datetime.now(timezone.utc)
        project.sync_status = "syncing"
        await tx.flush()

        # Import data with savepoints
        for data_item in external_data:
            try:
                async with nested_transaction(tx) as nested_tx:
                    item = DataItem(
                        project_id=project.id,
                        **data_item.model_dump(),
                    )
                    nested_tx.add(item)
                    await nested_tx.flush()
            except IntegrityError:
                # Skip duplicates
                continue

        project.sync_status = "synced"
        return project
```

## 7. Service Layer Pattern

### Service Methods with Transactions

```python
# services/project_service.py
from app.core.transactions import transaction_scope, nested_transaction

class ProjectService:
    """Service for project operations with transaction management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, user_id: UUID, payload: ProjectCreate) -> Project:
        """Create a new project with transaction handling."""
        async with transaction_scope(self.db) as tx:
            project = Project(
                user_id=user_id,
                brand_name=payload.brand_name,
                domain=payload.domain,
            )
            tx.add(project)
            await tx.flush()
            return project

    async def bulk_import_keywords(
        self, project_id: UUID, keywords: list[str]
    ) -> dict[str, int]:
        """Import keywords with transaction safety."""
        async with transaction_scope(self.db) as tx:
            successful = 0
            failed = 0

            for term in keywords:
                try:
                    async with nested_transaction(tx) as nested_tx:
                        keyword = Keyword(
                            project_id=project_id,
                            term=term,
                        )
                        nested_tx.add(keyword)
                        await nested_tx.flush()
                    successful += 1
                except IntegrityError:
                    failed += 1
                    continue

            return {"successful": successful, "failed": failed}
```

## 8. Testing Transactions

### Unit Test Example

```python
import pytest
from app.core.transactions import transaction_scope, nested_transaction

@pytest.mark.asyncio
async def test_transaction_rollback_on_error(db_session):
    """Verify transaction rolls back on exception."""
    with pytest.raises(ConflictError):
        async with transaction_scope(db_session) as tx:
            user = User(email="test@example.com")
            tx.add(user)
            await tx.flush()
            # Manually trigger error
            raise ConflictError("Test error")

    # Verify user was not persisted
    result = await db_session.execute(select(User))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_nested_transaction_partial_rollback(db_session):
    """Verify nested transaction rollbacks don't affect parent."""
    async with transaction_scope(db_session) as tx:
        user = User(email="parent@example.com")
        tx.add(user)
        await tx.flush()

        try:
            async with nested_transaction(tx) as nested_tx:
                # This should fail and rollback
                raise ValueError("Nested error")
        except ValueError:
            pass  # Expected

    # Parent commit should succeed
    result = await db_session.execute(select(User))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == "parent@example.com"
```

## 9. Best Practices

### ✅ DO:

- Use `transaction_scope()` for standard operations
- Use `nested_transaction()` when you want partial rollback capability
- Use `@with_transaction` for cleaner route handler code
- Handle specific exceptions (ValidationError, IntegrityError, etc.)
- Use `readonly_transaction()` for reporting/analytics queries
- Place long-running operations (external API calls) outside transactions
- Test transaction rollback behavior explicitly

### ❌ DON'T:

- Mix explicit transaction management with implicit `get_db()` in same function
- Leave transactions open during network calls
- Ignore transaction failures silently
- Manually call `commit()` inside `transaction_scope()`
- Use nested transactions without parent transaction
- Create transactions around read-only queries (use `readonly_transaction()` instead)

## 10. Migration Guide

### From Implicit to Explicit Transactions

#### Before (Implicit):
```python
@router.post("/users")
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(email=payload.email)
    db.add(user)
    await db.commit()  # Manual commit
    return user
```

#### After (Explicit):
```python
@router.post("/users")
@with_transaction()
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(email=payload.email)
    db.add(user)
    return user  # Decorator handles commit
```

Or using context manager:
```python
@router.post("/users")
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    async with transaction_scope(db) as tx:
        user = User(email=payload.email)
        tx.add(user)
        return user
```
