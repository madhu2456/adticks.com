"""Integration test demonstrating complete AI scan workflow with response persistence."""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.prompt import Prompt, Response, Mention
from app.models.project import Project


@pytest.mark.asyncio
async def test_complete_ai_scan_workflow(db, test_user):
    """
    Test the complete workflow: project creation → prompts → responses with text → mentions.
    
    This simulates the actual AI scan workflow:
    1. Create project
    2. Generate prompts
    3. Execute LLM and persist responses with response_text
    4. Extract mentions from responses
    5. Verify all data is queryable through the API
    """
    # Step 1: Create project
    project = Project(
        user_id=test_user.id,
        brand_name="TechCorp",
        domain="techcorp.ai",
        industry="Artificial Intelligence",
    )
    db.add(project)
    await db.flush()

    # Step 2: Create prompts (simulating generate_prompts_task)
    prompts_data = [
        {"text": "What is TechCorp?", "category": "brand_awareness"},
        {"text": "TechCorp vs OpenAI: comparison", "category": "comparison"},
        {"text": "Best AI tools for enterprises", "category": "problem_solving"},
    ]

    prompts = []
    for p_data in prompts_data:
        prompt = Prompt(
            project_id=project.id,
            text=p_data["text"],
            category=p_data["category"],
        )
        db.add(prompt)
        prompts.append(prompt)
    await db.flush()

    # Step 3: Simulate LLM execution and response persistence
    # (simulating what _run_llm_scan_impl does)
    responses_data = [
        {
            "prompt_idx": 0,
            "model": "gpt-4o",
            "response_text": (
                "TechCorp is a leading provider of enterprise AI solutions. "
                "They offer comprehensive tools for data analysis and machine learning. "
                "TechCorp is known for their excellent customer support and integration capabilities."
            ),
        },
        {
            "prompt_idx": 1,
            "model": "claude",
            "response_text": (
                "TechCorp and OpenAI both provide advanced AI capabilities. "
                "TechCorp specializes in enterprise solutions while OpenAI focuses on consumer accessibility. "
                "Both are recommended depending on your use case."
            ),
        },
        {
            "prompt_idx": 2,
            "model": "gpt-4o",
            "response_text": (
                "Several AI tools are excellent for enterprises: TechCorp for structured analytics, "
                "OpenAI for language models, and Google Cloud AI for image processing. "
                "TechCorp is particularly recommended for companies prioritizing data privacy."
            ),
        },
    ]

    responses = []
    for r_data in responses_data:
        resp = Response(
            id=uuid.uuid4(),
            prompt_id=prompts[r_data["prompt_idx"]].id,
            response_text=r_data["response_text"],  # KEY: Store actual LLM output
            storage_path=f"responses/gpt/{prompts[r_data['prompt_idx']].id}.json",
            model=r_data["model"],
            timestamp=datetime.now(timezone.utc),
        )
        db.add(resp)
        responses.append(resp)
    await db.flush()

    # Step 4: Extract and persist mentions from responses
    # (simulating what mention extraction does)
    mention_data = [
        # From first response
        {
            "response_idx": 0,
            "brand": "TechCorp",
            "position": 1,
            "confidence": 0.95,
        },
        {
            "response_idx": 0,
            "brand": "TechCorp",
            "position": 2,
            "confidence": 0.92,
        },
        # From second response
        {
            "response_idx": 1,
            "brand": "TechCorp",
            "position": 1,
            "confidence": 0.88,
        },
        {
            "response_idx": 1,
            "brand": "OpenAI",
            "position": 1,
            "confidence": 0.90,
        },
        # From third response
        {
            "response_idx": 2,
            "brand": "TechCorp",
            "position": 1,
            "confidence": 0.93,
        },
        {
            "response_idx": 2,
            "brand": "OpenAI",
            "position": 1,
            "confidence": 0.85,
        },
    ]

    mentions = []
    for m_data in mention_data:
        mention = Mention(
            id=uuid.uuid4(),
            response_id=responses[m_data["response_idx"]].id,
            brand=m_data["brand"],
            position=m_data["position"],
            confidence=m_data["confidence"],
        )
        db.add(mention)
        mentions.append(mention)
    await db.commit()

    # Step 5: Verify all data is queryable (simulating API responses)
    # Get all responses for the project with their mentions
    result = await db.execute(
        select(Response)
        .join(Prompt)
        .where(Prompt.project_id == project.id)
        .options(selectinload(Response.mentions))
        .order_by(Response.timestamp)
    )
    fetched_responses = result.scalars().unique().all()

    # Assertions
    assert len(fetched_responses) == 3, "Should have 3 responses"
    assert all(r.response_text for r in fetched_responses), "All responses should have text"
    assert all(r.model for r in fetched_responses), "All responses should have model"

    # Verify response content is accessible (KEY FIX)
    assert "TechCorp" in fetched_responses[0].response_text
    assert "OpenAI" in fetched_responses[1].response_text
    assert "data privacy" in fetched_responses[2].response_text

    # Verify mentions are linked
    all_mentions = []
    for resp in fetched_responses:
        all_mentions.extend(resp.mentions)
    
    assert len(all_mentions) == 6, "Should have 6 total mentions"
    
    techcorp_mentions = [m for m in all_mentions if m.brand == "TechCorp"]
    openai_mentions = [m for m in all_mentions if m.brand == "OpenAI"]
    
    assert len(techcorp_mentions) == 4, "Should have 4 TechCorp mentions"
    assert len(openai_mentions) == 2, "Should have 2 OpenAI mentions"
    
    avg_techcorp_confidence = sum(m.confidence for m in techcorp_mentions) / len(techcorp_mentions)
    assert avg_techcorp_confidence > 0.9, "TechCorp should have high confidence scores"

    # Simulate API response for /api/results/{project_id}
    from app.schemas.prompt import ResponseResponse
    
    response_schemas = [ResponseResponse.model_validate(r) for r in fetched_responses]
    assert len(response_schemas) == 3
    
    # Verify API response includes the response_text (KEY FIX)
    for schema in response_schemas:
        assert schema.response_text, "API should expose response_text"
        assert len(schema.response_text) > 50, "Response text should be substantial"
        assert schema.model in ["gpt-4o", "claude"]
