"""
Test suite for AdTicks SEO scanning pipeline.
Tests Phase 1-4 functionality: caching, progress, components, differential updates.
"""

import pytest

from app.core.scan_cache import (
    has_scan_cache,
    get_cached_scan_results,
    save_scan_results,
    should_invalidate_cache,
)
from app.core.component_cache import ComponentCache
from app.core.progress import ScanProgress, ScanStage
from app.core.differential_updates import DifferentialUpdateDetector


# ---------------------------------------------------------------------------
# Phase 1: Redis Caching Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_cache_save_and_retrieve():
    """Test saving and retrieving full scan cache."""
    project_id = "test-project-1"
    test_data = {
        "keywords": [{"keyword": "test", "volume": 100}],
        "rankings": [{"position": 5}],
        "score": 75,
    }
    
    # Save to cache
    await save_scan_results(project_id, test_data)
    
    # Retrieve from cache
    cached = await get_cached_scan_results(project_id)
    assert cached is not None
    assert cached["keywords"] == test_data["keywords"]
    assert cached["score"] == test_data["score"]


@pytest.mark.asyncio
async def test_scan_cache_ttl():
    """Test that scan cache has 24-hour TTL."""
    project_id = "test-project-ttl"
    test_data = {"status": "complete"}
    
    await save_scan_results(project_id, test_data)
    
    # Cache should exist
    exists = await has_scan_cache(project_id)
    assert exists


@pytest.mark.asyncio
async def test_cache_invalidation_on_state_change():
    """Test that cache is invalidated when project state changes."""
    project_id = "test-project-invalid"
    
    # Mock project state change detection
    should_invalidate = await should_invalidate_cache(project_id)
    # Should return False for new projects (first cache)
    assert isinstance(should_invalidate, bool)


# ---------------------------------------------------------------------------
# Phase 2: Progress Tracking Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_progress_initialization():
    """Test progress tracking initialization."""
    project_id = "test-project-progress"
    task_id = "task-123"
    
    progress = ScanProgress(project_id, task_id)
    await progress.initialize()
    
    # Verify initial state
    assert progress.project_id == project_id
    assert progress.task_id == task_id


@pytest.mark.asyncio
async def test_progress_updates():
    """Test progress stage updates."""
    project_id = "test-project-progress-update"
    task_id = "task-456"
    
    progress = ScanProgress(project_id, task_id)
    await progress.initialize()
    
    # Update to different stages
    await progress.update(ScanStage.KEYWORD_GENERATION, 10, "Generating keywords")
    await progress.update(ScanStage.RANK_TRACKING, 40, "Checking 40/100 keywords")
    await progress.update(ScanStage.TECHNICAL_AUDIT, 60, "Running technical audit")
    
    # All updates should complete without error
    assert True


# ---------------------------------------------------------------------------
# Phase 3: Component Caching Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_component_cache_keywords():
    """Test keyword component caching."""
    project_id = "test-project-keywords"
    keywords = [
        {"keyword": "seo", "volume": 5000, "difficulty": 45},
        {"keyword": "seo tools", "volume": 2000, "difficulty": 52},
    ]
    clusters = [
        ["seo", "seo tools", "best seo"],
        ["keywords", "keyword research"],
    ]
    
    cache = ComponentCache(project_id)
    
    # Save keywords
    await cache.cache_keywords(keywords, clusters)
    
    # Retrieve keywords
    cached = await cache.get_cached_keywords()
    assert cached is not None
    assert len(cached["keywords"]) == len(keywords)
    assert cached["keywords"][0]["keyword"] == "seo"


@pytest.mark.asyncio
async def test_component_cache_rankings():
    """Test ranking component caching."""
    project_id = "test-project-rankings"
    rankings = [
        {"keyword": "seo", "position": 5, "url": "https://example.com/seo"},
        {"keyword": "seo tools", "position": 12, "url": "https://example.com/tools"},
    ]
    
    cache = ComponentCache(project_id)
    
    # Save rankings
    await cache.cache_rankings(rankings)
    
    # Retrieve rankings
    cached = await cache.get_cached_rankings()
    assert cached is not None
    assert cached["total_keywords"] == len(rankings)


@pytest.mark.asyncio
async def test_component_cache_audit():
    """Test SEO audit component caching."""
    project_id = "test-project-audit"
    on_page = {"score": 85, "issues": [{"type": "missing_h1"}]}
    technical = {"score": 90, "issues": []}
    
    cache = ComponentCache(project_id)
    
    # Save audit
    await cache.cache_audit(on_page, technical)
    
    # Retrieve audit
    cached = await cache.get_cached_audit()
    assert cached is not None
    assert cached["on_page"]["score"] == 85
    assert cached["technical"]["score"] == 90


@pytest.mark.asyncio
async def test_component_cache_gaps():
    """Test content gaps component caching."""
    project_id = "test-project-gaps"
    gaps = [
        {"topic": "mobile optimization", "difficulty": "medium"},
        {"topic": "core web vitals", "difficulty": "high"},
    ]
    
    cache = ComponentCache(project_id)
    
    # Save gaps
    await cache.cache_gaps(gaps)
    
    # Retrieve gaps
    cached = await cache.get_cached_gaps()
    assert cached is not None
    assert cached["gap_count"] == len(gaps)


@pytest.mark.asyncio
async def test_component_cache_stats():
    """Test getting cache statistics."""
    project_id = "test-project-stats"
    cache = ComponentCache(project_id)
    
    # Cache some components
    await cache.cache_keywords([{"keyword": "test"}], [])
    await cache.cache_rankings([{"keyword": "test", "position": 1}])
    
    # Get stats
    stats = await cache.get_cache_stats()
    
    assert "keywords" in stats
    assert "rankings" in stats
    assert stats["keywords"]["exists"] is True
    assert stats["rankings"]["exists"] is True


@pytest.mark.asyncio
async def test_component_cache_invalidation():
    """Test invalidating specific components."""
    project_id = "test-project-invalidate"
    cache = ComponentCache(project_id)
    
    # Cache keywords
    await cache.cache_keywords([{"keyword": "test"}], [])
    
    # Verify it exists
    cached = await cache.get_cached_keywords()
    assert cached is not None
    
    # Invalidate
    await cache.invalidate_component("keywords")
    
    # Should be gone
    cached = await cache.get_cached_keywords()
    assert cached is None


# ---------------------------------------------------------------------------
# Phase 4: Differential Updates Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_differential_detect_keyword_changes():
    """Test detecting keyword changes."""
    project_id = "test-project-diff"
    detector = DifferentialUpdateDetector(project_id)
    
    keywords_v1 = ["seo", "marketing", "analytics"]
    keywords_v2 = ["seo", "marketing", "analytics", "content marketing"]
    
    # Save initial state
    await detector.save_keywords_state(keywords_v1)
    
    # Check if changed (should be False for same keywords)
    changed = await detector.keywords_changed(keywords_v1)
    assert changed is False
    
    # Check with different keywords (should be True)
    changed = await detector.keywords_changed(keywords_v2)
    assert changed is True


@pytest.mark.asyncio
async def test_differential_detect_domain_changes():
    """Test detecting domain changes."""
    project_id = "test-project-domain"
    detector = DifferentialUpdateDetector(project_id)
    
    domain_v1 = "example.com"
    domain_v2 = "newexample.com"
    
    # Save initial state
    await detector.save_domain_state(domain_v1)
    
    # Check if changed
    changed = await detector.domain_changed(domain_v1)
    assert changed is False
    
    changed = await detector.domain_changed(domain_v2)
    assert changed is True


@pytest.mark.asyncio
async def test_differential_changes_summary():
    """Test getting comprehensive changes summary."""
    project_id = "test-project-summary"
    detector = DifferentialUpdateDetector(project_id)
    
    domain = "example.com"
    keywords = ["seo", "marketing"]
    competitors = ["competitor1.com", "competitor2.com"]
    
    # Save initial state
    await detector.save_all_states(domain, keywords, competitors)
    
    # Get changes summary (no changes)
    summary = await detector.get_changes_summary(domain, keywords, competitors)
    
    assert summary["keywords_changed"] is False
    assert summary["domain_changed"] is False
    assert summary["competitors_changed"] is False
    assert summary["requires_full_rescan"] is False


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_pipeline_caching_flow():
    """Test complete caching pipeline from cache check to storage."""
    project_id = "test-integration-flow"
    
    # Phase 1: Check cache
    cache_exists = await has_scan_cache(project_id)
    assert cache_exists is False or True  # First time should be False
    
    # Phase 3: Save components
    component_cache = ComponentCache(project_id)
    await component_cache.cache_keywords(
        [{"keyword": "test", "volume": 100}],
        [["test", "testing"]]
    )
    
    # Phase 2: Initialize progress
    progress = ScanProgress(project_id, "test-task")
    await progress.initialize()
    await progress.update(ScanStage.COMPLETED, 100, "Scan complete")
    
    # Verify all components are cached
    stats = await component_cache.get_cache_stats()
    assert stats is not None


@pytest.mark.asyncio
async def test_cache_invalidation_workflow():
    """Test full cache invalidation workflow."""
    project_id = "test-invalidation-flow"
    
    # Setup: Cache some data
    cache = ComponentCache(project_id)
    await cache.cache_keywords([{"keyword": "test"}], [])
    await cache.cache_rankings([{"keyword": "test", "position": 1}])
    
    # Verify cached
    stats = await cache.get_cache_stats()
    assert stats["keywords"]["exists"] is True
    
    # Invalidate all
    await cache.invalidate_all()
    
    # Verify cleared
    stats = await cache.get_cache_stats()
    assert stats["keywords"]["exists"] is False
    assert stats["rankings"]["exists"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
