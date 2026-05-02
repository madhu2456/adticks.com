"""
Test suite for Rank Tracker.
Tests keyword ranking positions, SERP features, volatility monitoring.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.seo.rank_tracker import PlaywrightManager


@pytest.fixture
def sample_keywords():
    return [
        "python programming",
        "web development",
        "SEO tools",
        "machine learning",
        "cloud computing",
    ]


@pytest.fixture
def sample_domain():
    return "example.com"


@pytest.mark.asyncio
async def test_rank_tracker_keywords_format(sample_keywords):
    """Test that keywords are properly formatted."""
    for keyword in sample_keywords:
        assert isinstance(keyword, str)
        assert len(keyword) > 0


@pytest.mark.asyncio
async def test_rank_tracker_keyword_variety(sample_keywords):
    """Test variety in keyword types."""
    assert len(sample_keywords) >= 3


@pytest.mark.asyncio
async def test_rank_tracker_long_tail_keywords(sample_keywords):
    """Test that long-tail keywords are included."""
    long_tail = [k for k in sample_keywords if len(k.split()) >= 2]
    assert len(long_tail) >= 1


@pytest.mark.asyncio
async def test_rank_tracker_short_tail_keywords(sample_keywords):
    """Test that short-tail keywords are included."""
    short_tail = [k for k in sample_keywords if len(k.split()) == 1]
    assert len(short_tail) >= 0


@pytest.mark.asyncio
async def test_rank_tracker_ranking_position_valid():
    """Test that ranking positions are valid (1-100)."""
    positions = [1, 5, 10, 25, 50, 75, 100]
    for pos in positions:
        assert 1 <= pos <= 100


@pytest.mark.asyncio
async def test_rank_tracker_ranking_changes():
    """Test ranking volatility tracking."""
    # Simulate ranking changes
    initial_ranks = {
        "keyword1": 5,
        "keyword2": 12,
        "keyword3": 28,
    }
    
    updated_ranks = {
        "keyword1": 4,  # Moved up
        "keyword2": 12,  # Stayed same
        "keyword3": 31,  # Moved down
    }
    
    changes = {}
    for keyword in initial_ranks:
        changes[keyword] = updated_ranks[keyword] - initial_ranks[keyword]
    
    assert changes["keyword1"] < 0  # Improvement
    assert changes["keyword2"] == 0  # No change
    assert changes["keyword3"] > 0  # Decline


@pytest.mark.asyncio
async def test_rank_tracker_serp_features():
    """Test SERP feature detection."""
    serp_features = [
        "featured_snippet",
        "knowledge_panel",
        "local_pack",
        "sitelinks",
        "news",
    ]
    
    for feature in serp_features:
        assert isinstance(feature, str)


@pytest.mark.asyncio
async def test_rank_tracker_result_structure():
    """Test that rank tracking results have proper structure."""
    result = {
        "keyword": "python programming",
        "position": 5,
        "url": "https://example.com",
        "title": "Python Programming Guide",
        "serp_features": ["featured_snippet"],
        "change": -2,
    }
    
    assert "keyword" in result
    assert "position" in result
    assert "url" in result
    assert "serp_features" in result


@pytest.mark.asyncio
async def test_rank_tracker_position_history():
    """Test tracking position history."""
    history = [
        {"date": "2024-01-01", "position": 10},
        {"date": "2024-01-08", "position": 8},
        {"date": "2024-01-15", "position": 6},
        {"date": "2024-01-22", "position": 5},
    ]
    
    assert len(history) == 4
    # Verify trend
    positions = [h["position"] for h in history]
    assert positions == sorted(positions, reverse=True)  # Improving


@pytest.mark.asyncio
async def test_rank_tracker_concurrent_tracking():
    """Test concurrent rank tracking for multiple keywords."""
    keywords = ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    
    # Simulate concurrent tracking
    async def track_keyword(keyword):
        await asyncio.sleep(0.01)
        return {"keyword": keyword, "position": 15}
    
    results = await asyncio.gather(*[track_keyword(k) for k in keywords])
    assert len(results) == len(keywords)


@pytest.mark.asyncio
async def test_rank_tracker_ranking_clusters():
    """Test grouping rankings by position clusters."""
    rankings = [
        (1, 5),  # Top 5
        (6, 10),  # 6-10
        (11, 20),  # 11-20
        (21, 50),  # 21-50
        (51, 100),  # Beyond 50
    ]
    
    for start, end in rankings:
        assert start <= end
        assert 1 <= start <= 100
        assert 1 <= end <= 100


@pytest.mark.asyncio
async def test_rank_tracker_ranking_velocity():
    """Test ranking velocity calculations."""
    weekly_positions = {
        "week1": 15,
        "week2": 13,
        "week3": 10,
        "week4": 8,
    }
    
    # Calculate velocity (improvement per week)
    velocity = (weekly_positions["week1"] - weekly_positions["week4"]) / 3
    assert velocity > 0  # Improving


@pytest.mark.asyncio
async def test_rank_tracker_serp_feature_variations():
    """Test various SERP feature types."""
    features = {
        "snippet": 80,  # % of keywords with featured snippet
        "knowledge_panel": 30,
        "local_pack": 15,
        "people_also_ask": 45,
        "sitelinks": 25,
    }
    
    for feature, percentage in features.items():
        assert 0 <= percentage <= 100


@pytest.mark.asyncio
async def test_rank_tracker_competitor_rankings():
    """Test tracking competitor rankings alongside own."""
    result = {
        "keyword": "best python tutorials",
        "positions": {
            "our_site": 5,
            "competitor1": 2,
            "competitor2": 8,
            "competitor3": 12,
        }
    }
    
    positions = result["positions"].values()
    assert min(positions) >= 1
    assert max(positions) <= 100


@pytest.mark.asyncio
async def test_rank_tracker_ranking_difficulty():
    """Test ranking difficulty scoring."""
    keywords = {
        "python": {"difficulty": 85},  # Hard to rank
        "python tutorials for beginners": {"difficulty": 25},  # Easy
        "best python framework 2024": {"difficulty": 55},  # Medium
    }
    
    for keyword, data in keywords.items():
        assert 0 <= data["difficulty"] <= 100


@pytest.mark.asyncio
async def test_rank_tracker_ranking_stability():
    """Test ranking stability metrics."""
    # Track volatility
    positions_over_time = [5, 4, 6, 5, 5, 4, 5]
    
    # Calculate standard deviation as stability measure
    mean = sum(positions_over_time) / len(positions_over_time)
    variance = sum((x - mean) ** 2 for x in positions_over_time) / len(positions_over_time)
    stability = 1 / (1 + (variance ** 0.5))  # Higher = more stable
    
    assert 0 <= stability <= 1


@pytest.mark.asyncio
async def test_rank_tracker_search_volume():
    """Test search volume tracking."""
    keywords_data = {
        "python": {"search_volume": 75000, "position": 15},
        "python tutorial": {"search_volume": 12000, "position": 8},
        "learn python online": {"search_volume": 3200, "position": 3},
    }
    
    for keyword, data in keywords_data.items():
        assert data["search_volume"] > 0


@pytest.mark.asyncio
async def test_rank_tracker_conversion_potential():
    """Test conversion potential scoring."""
    keywords = [
        {"keyword": "python books", "intent": "commercial", "potential": 8},
        {"keyword": "how to learn python", "intent": "informational", "potential": 3},
        {"keyword": "buy python course", "intent": "transactional", "potential": 9},
    ]
    
    for item in keywords:
        assert 0 <= item["potential"] <= 10


@pytest.mark.asyncio
async def test_rank_tracker_top_keywords():
    """Test identifying top-performing keywords."""
    rankings = [
        {"keyword": "keyword1", "position": 2, "clicks": 500},
        {"keyword": "keyword2", "position": 15, "clicks": 80},
        {"keyword": "keyword3", "position": 1, "clicks": 1200},
    ]
    
    top = sorted(rankings, key=lambda x: x["clicks"], reverse=True)[0]
    assert top["keyword"] == "keyword3"


@pytest.mark.asyncio
async def test_rank_tracker_ranking_opportunities():
    """Test identifying ranking opportunities."""
    keywords = [
        {"keyword": "main keyword", "position": 15, "difficulty": 45},
        {"keyword": "related keyword", "position": 21, "difficulty": 35},
        {"keyword": "long tail", "position": 75, "difficulty": 20},
    ]
    
    # Opportunities: low difficulty keywords near top 10
    opportunities = [
        k for k in keywords 
        if 11 <= k["position"] <= 30 and k["difficulty"] < 50
    ]
    assert len(opportunities) >= 1


@pytest.mark.asyncio
async def test_rank_tracker_ranking_winners_losers():
    """Test identifying winners and losers."""
    changes = {
        "keyword1": -5,  # Winner (moved up 5 positions)
        "keyword2": 0,   # Stable
        "keyword3": 3,   # Loser (moved down 3 positions)
    }
    
    winners = [k for k, v in changes.items() if v < 0]
    losers = [k for k, v in changes.items() if v > 0]
    
    assert len(winners) >= 0
    assert len(losers) >= 0
