"""Tests for response_text persistence in AI scan workflow."""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.prompt import Prompt, Response, Mention
from app.models.project import Project


@pytest.mark.asyncio
async def test_response_stores_response_text(db, test_user):
    """Verify that Response model stores and retrieves response_text."""
    # Create a project
    project = Project(
        user_id=test_user.id,
        brand_name="TestBrand",
        domain="test.com",
        industry="Technology",
    )
    db.add(project)
    await db.flush()

    # Create a prompt
    prompt = Prompt(
        project_id=project.id,
        text="What is TestBrand?",
        category="brand_awareness",
        created_at=datetime.now(timezone.utc),
    )
    db.add(prompt)
    await db.flush()

    # Create a response with response_text
    response_text = "TestBrand is a leading software company known for innovation and customer support."
    response = Response(
        id=uuid.uuid4(),
        prompt_id=prompt.id,
        response_text=response_text,
        storage_path="responses/test/response.json",
        model="gpt-4o",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(response)
    await db.flush()

    # Create mentions
    mention = Mention(
        id=uuid.uuid4(),
        response_id=response.id,
        brand="TestBrand",
        position=1,
        confidence=0.95,
    )
    db.add(mention)
    await db.commit()

    # Retrieve and verify
    result = await db.execute(
        select(Response)
        .where(Response.id == response.id)
        .options(selectinload(Response.mentions))
    )
    retrieved_response = result.scalar_one()

    assert retrieved_response.response_text == response_text
    assert retrieved_response.model == "gpt-4o"
    assert retrieved_response.storage_path == "responses/test/response.json"
    assert len(retrieved_response.mentions) == 1
    assert retrieved_response.mentions[0].brand == "TestBrand"


@pytest.mark.asyncio
async def test_response_text_persists_with_empty_string(db, test_user):
    """Verify that Response model handles empty response_text."""
    project = Project(
        user_id=test_user.id,
        brand_name="TestBrand",
        domain="test.com",
        industry="Technology",
    )
    db.add(project)
    await db.flush()

    prompt = Prompt(
        project_id=project.id,
        text="Empty response test",
        category="brand_awareness",
    )
    db.add(prompt)
    await db.flush()

    # Create a response with empty text (fallback behavior)
    response = Response(
        id=uuid.uuid4(),
        prompt_id=prompt.id,
        response_text="",  # Empty but required field
        storage_path="responses/test/empty.json",
        model="claude",
    )
    db.add(response)
    await db.commit()

    result = await db.execute(
        select(Response).where(Response.id == response.id)
    )
    retrieved = result.scalar_one()

    assert retrieved.response_text == ""
    assert retrieved.model == "claude"


@pytest.mark.asyncio
async def test_response_schema_includes_response_text(db, test_user):
    """Verify ResponseResponse schema exposes response_text."""
    from app.schemas.prompt import ResponseResponse

    project = Project(
        user_id=test_user.id,
        brand_name="TestBrand",
        domain="test.com",
    )
    db.add(project)
    await db.flush()

    prompt = Prompt(project_id=project.id, text="Test", category="brand_awareness")
    db.add(prompt)
    await db.flush()

    response_text = "This is the actual LLM response."
    response = Response(
        id=uuid.uuid4(),
        prompt_id=prompt.id,
        response_text=response_text,
        storage_path="test/path.json",
        model="gpt-4o",
    )
    db.add(response)
    await db.commit()

    result = await db.execute(select(Response).where(Response.id == response.id))
    retrieved = result.scalar_one()

    # Verify schema can serialize the response with response_text
    schema = ResponseResponse.model_validate(retrieved)
    assert schema.response_text == response_text
    assert schema.model == "gpt-4o"
    assert str(schema.prompt_id) == str(prompt.id)
