import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.project import Project
from app.models.keyword import Keyword
from app.models.competitor import Competitor
from app.models.aeo import AEOVisibility

@pytest.mark.asyncio
async def test_get_usage_empty(client: AsyncClient, user_token: str):
    """Test get usage when no data exists."""
    response = await client.get(
        "/api/auth/usage",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ai_scans_used"] == 0
    assert data["keywords_used"] == 0
    assert data["competitors_used"] == 0
    assert "days_remaining" in data

@pytest.mark.asyncio
async def test_get_usage_with_data(
    client: AsyncClient, 
    db: AsyncSession, 
    user_token: str, 
    project: Project
):
    """Test get usage with existing data."""
    # Add a keyword
    kw = Keyword(project_id=project.id, keyword="test", intent="informational", volume=100)
    db.add(kw)
    await db.flush()
    
    # Add a competitor
    comp = Competitor(project_id=project.id, domain="competitor.com")
    db.add(comp)
    
    # Add an AI visibility record
    vis = AEOVisibility(
        project_id=project.id, 
        keyword_id=kw.id, 
        ai_model="chatgpt", 
        is_mentioned=True,
        mention_context="AdTicks is great"
    )
    db.add(vis)
    
    await db.commit()
    
    response = await client.get(
        "/api/auth/usage",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ai_scans_used"] == 1
    assert data["keywords_used"] == 1
    assert data["competitors_used"] == 1
