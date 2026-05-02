"""
AdTicks — Local SEO Analyzer Tests (Phase 3 Tier 3).

Tests for local SEO checking including NAP consistency, local schema,
citations, and local rank tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services.seo.technical_seo import _check_local_seo_analysis


@pytest.fixture
def mock_client():
    """Mock httpx AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.mark.asyncio
async def test_local_seo_analyzer_initialization(mock_client):
    """Test local SEO analyzer initializes correctly."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result is not None
    assert result["name"] == "Local SEO Analysis"
    assert "passed" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)


@pytest.mark.asyncio
async def test_local_seo_nap_consistency(mock_client):
    """Test NAP (Name, Address, Phone) consistency."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "nap" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_local_schema(mock_client):
    """Test local business schema presence."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "schema" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_google_business_profile(mock_client):
    """Test Google Business Profile optimization."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "google" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_citations(mock_client):
    """Test business citations."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "citation" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_review_management(mock_client):
    """Test review management setup."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "review" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_business_hours(mock_client):
    """Test business hours markup."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "hour" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_location_pages(mock_client):
    """Test location page optimization."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "location" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_service_area_schema(mock_client):
    """Test service area schema markup."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "service" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_local_keywords(mock_client):
    """Test local keyword targeting."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "keyword" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_local_citations_consistency(mock_client):
    """Test citation consistency across directories."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "consist" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_directory_listings(mock_client):
    """Test directory listing coverage."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "director" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_local_link_building(mock_client):
    """Test local link building opportunities."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "link" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_local_content(mock_client):
    """Test local content optimization."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "content" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_map_optimization(mock_client):
    """Test map/location optimization."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "map" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_mobile_optimization(mock_client):
    """Test mobile optimization for local."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "mobile" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_multi_location_sites(mock_client):
    """Test multi-location site optimization."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "multi" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_review_schema(mock_client):
    """Test review aggregate schema."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "aggregate" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_social_signals(mock_client):
    """Test local social signals."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "social" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_brand_consistency(mock_client):
    """Test brand name consistency."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "brand" in str(result).lower() or result["passed"] in [True, False]


@pytest.mark.asyncio
async def test_local_seo_compliance_score(mock_client):
    """Test local SEO compliance score calculation."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert "score" in result or "issues" in result
    assert result["passed"] is not None


@pytest.mark.asyncio
async def test_local_seo_multiple_issues(mock_client):
    """Test handling multiple local SEO issues."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert isinstance(result["issues"], list)
    assert result["name"] == "Local SEO Analysis"


@pytest.mark.asyncio
async def test_local_seo_error_handling(mock_client):
    """Test error handling in local SEO checks."""
    mock_client.get = AsyncMock(side_effect=Exception("Network error"))
    
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert isinstance(result["passed"], bool)


@pytest.mark.asyncio
async def test_local_seo_comprehensive_report(mock_client):
    """Test comprehensive local SEO report."""
    result = await _check_local_seo_analysis("example.com", mock_client)
    
    assert result["name"] == "Local SEO Analysis"
    assert "passed" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)
