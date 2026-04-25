#!/usr/bin/env python
"""
Manual verification script for AdTicks SEO scanning pipeline.
Tests all phases without complex async/Redis setup.
"""

import json
import sys
from pathlib import Path

# Ensure we can import from backend
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all Phase 4 modules import correctly."""
    print("✓ Testing imports...")
    
    try:
        from app.core.scan_cache import (
            has_scan_cache,
            get_cached_scan_results,
            save_scan_results,
            should_invalidate_cache,
            get_cache_status,
        )
        print("  ✓ Phase 1: scan_cache imports OK")
    except ImportError as e:
        print(f"  ✗ Phase 1 import failed: {e}")
        return False
    
    try:
        from app.core.component_cache import ComponentCache
        print("  ✓ Phase 3: component_cache imports OK")
    except ImportError as e:
        print(f"  ✗ Phase 3 import failed: {e}")
        return False
    
    try:
        from app.core.progress import ScanProgress, ScanStage
        print("  ✓ Phase 2: progress imports OK")
    except ImportError as e:
        print(f"  ✗ Phase 2 import failed: {e}")
        return False
    
    try:
        from app.core.differential_updates import DifferentialUpdateDetector
        print("  ✓ Phase 4: differential_updates imports OK")
    except ImportError as e:
        print(f"  ✗ Phase 4 import failed: {e}")
        return False
    
    try:
        from app.api.cache import router
        print("  ✓ Phase 4: cache API endpoints OK")
    except ImportError as e:
        print(f"  ✗ Phase 4 API import failed: {e}")
        return False
    
    return True


def test_scan_cache_structure():
    """Test scan_cache module structure."""
    print("\n✓ Testing Phase 1: Redis Caching Structure...")
    
    from app.core.scan_cache import (
        SCAN_RESULTS_TTL,
        SCAN_METADATA_TTL,
    )
    
    # Check TTL constants
    assert SCAN_RESULTS_TTL == 86400, f"Expected 86400s (24h), got {SCAN_RESULTS_TTL}"
    print(f"  ✓ Scan results TTL: {SCAN_RESULTS_TTL}s (24 hours)")
    
    assert SCAN_METADATA_TTL == 86400, f"Expected 86400s (24h), got {SCAN_METADATA_TTL}"
    print(f"  ✓ Scan metadata TTL: {SCAN_METADATA_TTL}s (24 hours)")
    
    return True


def test_component_cache_structure():
    """Test component_cache module structure."""
    print("\n✓ Testing Phase 3: Component Caching Structure...")
    
    from app.core.component_cache import (
        ComponentCache,
        KEYWORDS_CACHE_TTL,
        RANKINGS_CACHE_TTL,
        AUDIT_CACHE_TTL,
        GAPS_CACHE_TTL,
    )
    
    # Check TTL values
    assert KEYWORDS_CACHE_TTL == 86400, f"Keywords TTL should be 24h"
    print(f"  ✓ Keywords TTL: {KEYWORDS_CACHE_TTL}s (24 hours)")
    
    assert RANKINGS_CACHE_TTL == 43200, f"Rankings TTL should be 12h"
    print(f"  ✓ Rankings TTL: {RANKINGS_CACHE_TTL}s (12 hours)")
    
    assert AUDIT_CACHE_TTL == 86400, f"Audit TTL should be 24h"
    print(f"  ✓ Audit TTL: {AUDIT_CACHE_TTL}s (24 hours)")
    
    assert GAPS_CACHE_TTL == 86400, f"Gaps TTL should be 24h"
    print(f"  ✓ Gaps TTL: {GAPS_CACHE_TTL}s (24 hours)")
    
    # Check methods
    cache = ComponentCache("test-project")
    assert hasattr(cache, 'cache_keywords'), "Missing cache_keywords method"
    assert hasattr(cache, 'get_cached_keywords'), "Missing get_cached_keywords method"
    assert hasattr(cache, 'cache_rankings'), "Missing cache_rankings method"
    assert hasattr(cache, 'cache_audit'), "Missing cache_audit method"
    assert hasattr(cache, 'cache_gaps'), "Missing cache_gaps method"
    assert hasattr(cache, 'invalidate_all'), "Missing invalidate_all method"
    assert hasattr(cache, 'invalidate_component'), "Missing invalidate_component method"
    assert hasattr(cache, 'get_cache_stats'), "Missing get_cache_stats method"
    print("  ✓ All component cache methods present")
    
    return True


def test_progress_structure():
    """Test progress module structure."""
    print("\n✓ Testing Phase 2: Progress Tracking Structure...")
    
    from app.core.progress import ScanProgress, ScanStage
    
    # Check ScanStage enum
    stages = [
        'INITIALIZING', 'KEYWORD_GENERATION', 'RANK_TRACKING',
        'TECHNICAL_AUDIT', 'ON_PAGE_ANALYSIS', 'AI_SCAN',
        'GAP_ANALYSIS', 'SCORE_COMPUTATION', 'INSIGHTS_GENERATION',
        'CACHING', 'COMPLETED'
    ]
    
    for stage in stages:
        assert hasattr(ScanStage, stage), f"Missing stage: {stage}"
    print(f"  ✓ All {len(stages)} scan stages defined")
    
    # Check methods
    progress = ScanProgress("test-project", "test-task")
    assert hasattr(progress, 'initialize'), "Missing initialize method"
    assert hasattr(progress, 'update'), "Missing update method"
    assert hasattr(progress, 'complete'), "Missing complete method"
    print("  ✓ All progress tracking methods present")
    
    return True


def test_differential_updates_structure():
    """Test differential_updates module structure."""
    print("\n✓ Testing Phase 4: Differential Updates Structure...")
    
    from app.core.differential_updates import DifferentialUpdateDetector
    
    detector = DifferentialUpdateDetector("test-project")
    
    # Check methods
    methods = [
        'save_keywords_state', 'keywords_changed',
        'save_domain_state', 'domain_changed',
        'save_competitors_state', 'competitors_changed',
        'get_changes_summary', 'save_all_states', 'clear_states'
    ]
    
    for method in methods:
        assert hasattr(detector, method), f"Missing method: {method}"
    print(f"  ✓ All {len(methods)} differential update methods present")
    
    return True


def test_api_endpoints():
    """Test cache API endpoints structure."""
    print("\n✓ Testing Phase 4: Cache API Endpoints...")
    
    from app.api.cache import router
    
    # Check routes
    routes = [route.path for route in router.routes]
    
    assert any("/stats/" in path for path in routes), "Missing /cache/stats endpoint"
    assert any("/invalidate/" in path for path in routes), "Missing /cache/invalidate endpoint"
    assert any("/invalidate-component" in path for path in routes), "Missing /cache/invalidate-component endpoint"
    
    print(f"  ✓ Cache API has {len(routes)} endpoints")
    for route in router.routes:
        print(f"    - {route.methods} {route.path}")
    
    return True


def test_seo_tasks_integration():
    """Test that SEO tasks import component caching."""
    print("\n✓ Testing Phase 3: SEO Tasks Integration...")
    
    try:
        from app.tasks.seo_tasks import ComponentCache
        print("  ✓ ComponentCache imported in seo_tasks.py")
        
        # Verify tasks are modified
        from app.tasks import seo_tasks
        import inspect
        
        # Check if tasks have component cache references
        source = inspect.getsource(seo_tasks)
        
        assert "ComponentCache" in source, "ComponentCache not used in seo_tasks"
        assert "cache_keywords" in source, "cache_keywords not called"
        assert "cache_rankings" in source, "cache_rankings not called"
        assert "cache_audit" in source, "cache_audit not called"
        assert "cache_gaps" in source, "cache_gaps not called"
        
        print("  ✓ All SEO tasks integrated with component caching")
        
        return True
    except AssertionError as e:
        print(f"  ✗ Integration check failed: {e}")
        return False


def test_main_router_registration():
    """Test that all routers are registered in main.py."""
    print("\n✓ Testing Router Registration in main.py...")
    
    try:
        backend_dir = Path(__file__).parent
        main_py = backend_dir / 'main.py'
        with open(main_py, 'r') as f:
            content = f.read()
        
        # Check imports
        assert 'from app.api import auth, projects, seo' in content, "Missing API imports"
        assert 'progress' in content, "Missing progress router import"
        assert 'cache' in content, "Missing cache router import"
        
        # Check router registration
        assert 'app.include_router(progress.router' in content, "Progress router not registered"
        assert 'app.include_router(cache.router' in content, "Cache router not registered"
        
        print("  ✓ Progress router registered")
        print("  ✓ Cache router registered")
        
        return True
    except (AssertionError, FileNotFoundError) as e:
        print(f"  ✗ Router registration check failed: {e}")
        return False


def main():
    """Run all manual verification tests."""
    print("=" * 70)
    print("AdTicks SEO Pipeline - Manual Verification Suite")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Phase 1: Scan Cache", test_scan_cache_structure),
        ("Phase 3: Component Cache", test_component_cache_structure),
        ("Phase 2: Progress Tracking", test_progress_structure),
        ("Phase 4: Differential Updates", test_differential_updates_structure),
        ("Phase 4: Cache API", test_api_endpoints),
        ("Phase 3: SEO Tasks Integration", test_seo_tasks_integration),
        ("Router Registration", test_main_router_registration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed! Pipeline is ready for testing.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
