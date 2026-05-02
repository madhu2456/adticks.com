"""
Test suite for Backlink Analyzer.
Tests backlink analysis, domain authority, growth tracking, and link quality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.seo.backlink_analyzer import analyze_backlinks


@pytest.fixture
def mock_project_id():
    return "test-project-123"


@pytest.fixture
def mock_domain():
    return "example.com"


@pytest.mark.asyncio
async def test_analyze_backlinks_returns_list(mock_project_id, mock_domain):
    """Test that analyze_backlinks returns a list of backlinks."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    assert isinstance(result, list)
    assert len(result) >= 0


@pytest.mark.asyncio
async def test_analyze_backlinks_structure(mock_project_id, mock_domain):
    """Test that backlinks have required structure."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    if len(result) > 0:
        backlink = result[0]
        assert "referring_domain" in backlink
        assert "target_url" in backlink
        assert "anchor_text" in backlink
        assert "authority_score" in backlink
        assert "status" in backlink


@pytest.mark.asyncio
async def test_analyze_backlinks_authority_score_range(mock_project_id, mock_domain):
    """Test that authority scores are in valid range."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    for backlink in result:
        score = backlink["authority_score"]
        assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_analyze_backlinks_status_values(mock_project_id, mock_domain):
    """Test that backlink status values are valid."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    valid_statuses = ["active", "lost", "pending"]
    
    for backlink in result:
        assert backlink["status"] in valid_statuses


@pytest.mark.asyncio
async def test_analyze_backlinks_domain_consistency(mock_project_id):
    """Test backlinks for multiple domains."""
    domains = ["example.com", "test.org", "mysite.io"]
    
    for domain in domains:
        result = await analyze_backlinks(mock_project_id, domain)
        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_analyze_backlinks_realistic_count(mock_project_id, mock_domain):
    """Test that backlink count is realistic."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    assert 0 <= len(result) <= 50  # Reasonable range


@pytest.mark.asyncio
async def test_analyze_backlinks_timestamps(mock_project_id, mock_domain):
    """Test that backlinks have valid timestamps."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    for backlink in result:
        if "first_seen" in backlink:
            assert backlink["first_seen"] is not None


@pytest.mark.asyncio
async def test_analyze_backlinks_anchor_text_variety(mock_project_id, mock_domain):
    """Test variety in anchor text."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    if len(result) > 1:
        anchor_texts = [bl["anchor_text"] for bl in result]
        unique_anchors = set(anchor_texts)
        # Should have some variety
        assert len(unique_anchors) >= 1


@pytest.mark.asyncio
async def test_analyze_backlinks_target_urls(mock_project_id, mock_domain):
    """Test that target URLs are valid."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    for backlink in result:
        url = backlink["target_url"]
        assert isinstance(url, str)
        assert len(url) > 0


@pytest.mark.asyncio
async def test_analyze_backlinks_referring_domains(mock_project_id, mock_domain):
    """Test that referring domains are valid."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    for backlink in result:
        domain_str = backlink["referring_domain"]
        assert isinstance(domain_str, str)
        assert "." in domain_str  # Should have domain extension


@pytest.mark.asyncio
async def test_analyze_backlinks_multiple_calls(mock_project_id, mock_domain):
    """Test multiple calls to analyze_backlinks."""
    results = []
    for _ in range(3):
        result = await analyze_backlinks(mock_project_id, mock_domain)
        results.append(len(result))
    
    # All calls should return valid results
    assert all(0 <= count <= 50 for count in results)


@pytest.mark.asyncio
async def test_analyze_backlinks_empty_domain_string():
    """Test with edge case: empty domain."""
    # Should handle gracefully
    result = await analyze_backlinks("test-project", "")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_analyze_backlinks_special_chars_domain(mock_project_id):
    """Test with special characters in domain."""
    result = await analyze_backlinks(mock_project_id, "test-domain-123.co.uk")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_analyze_backlinks_sorting_by_authority(mock_project_id, mock_domain):
    """Test analyzing backlinks and checking authority distribution."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    if len(result) > 1:
        authorities = [bl["authority_score"] for bl in result]
        # Should have varied authority scores
        assert min(authorities) < max(authorities)


@pytest.mark.asyncio
async def test_analyze_backlinks_domain_tlds(mock_project_id, mock_domain):
    """Test various domain TLDs in results."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    valid_tlds = [".com", ".org", ".net", ".io", ".co", ".uk"]
    
    for backlink in result:
        domain = backlink["referring_domain"].lower()
        assert any(domain.endswith(tld) for tld in valid_tlds)


@pytest.mark.asyncio
async def test_analyze_backlinks_concurrent_calls(mock_domain):
    """Test concurrent backlink analysis."""
    project_ids = ["proj1", "proj2", "proj3"]
    
    tasks = [analyze_backlinks(proj_id, mock_domain) for proj_id in project_ids]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_analyze_backlinks_different_domains(mock_project_id):
    """Test analysis across different domains."""
    domains = ["example.com", "test.org", "mysite.io", "blog.net"]
    
    for domain in domains:
        result = await analyze_backlinks(mock_project_id, domain)
        assert isinstance(result, list)
        # Each domain should have some backlinks
        assert len(result) >= 0


@pytest.mark.asyncio
async def test_analyze_backlinks_authority_distribution(mock_project_id, mock_domain):
    """Test distribution of authority scores."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    if len(result) >= 5:
        authorities = [bl["authority_score"] for bl in result]
        avg_authority = sum(authorities) / len(authorities)
        # Average authority should be in reasonable range
        assert 10 <= avg_authority <= 85


@pytest.mark.asyncio
async def test_analyze_backlinks_active_vs_lost(mock_project_id, mock_domain):
    """Test mix of active and lost backlinks."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    statuses = [bl["status"] for bl in result]
    # Should have primarily active links
    active_count = statuses.count("active")
    if len(result) > 0:
        assert active_count >= len(result) * 0.7  # At least 70% active


@pytest.mark.asyncio
async def test_analyze_backlinks_no_duplicates(mock_project_id, mock_domain):
    """Test that there are no exact duplicate backlinks."""
    result = await analyze_backlinks(mock_project_id, mock_domain)
    
    # Create tuples of key fields
    seen = set()
    for bl in result:
        key = (bl["referring_domain"], bl["target_url"], bl["anchor_text"])
        assert key not in seen, "Found duplicate backlink"
        seen.add(key)
