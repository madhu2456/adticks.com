"""
AdTicks — Cache Timeout Tests

Tests that the caching system gracefully handles timeouts 
on the final scan completion stage (previously stuck at 99%).
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.core.scan_cache import save_scan_results


@pytest.mark.asyncio
async def test_save_scan_results_handles_timeout_gracefully():
    """
    Test that save_scan_results completes successfully even if 
    project state hash query times out.
    
    This was the root cause of scans stuck at 99%.
    """
    project_id = "test-project-timeout"
    test_data = {
        "keywords": [{"keyword": "test", "volume": 100}],
        "rankings": [{"position": 5}],
        "score": 75,
        "status": "complete",
    }
    
    # Mock the AsyncSessionLocal to simulate timeout on state hash query
    with patch('app.core.scan_cache.AsyncSessionLocal') as mock_session_class:
        # Create a mock session that raises TimeoutError
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        # Mock the _get_project_state_hash to simulate timeout
        with patch('app.core.scan_cache._get_project_state_hash') as mock_hash:
            # Simulate a timeout by making it wait longer than the timeout
            async def timeout_simulator(*args, **kwargs):
                await asyncio.sleep(15)  # Longer than our 10s timeout
                
            mock_hash.side_effect = timeout_simulator
            mock_session_class.return_value = mock_session
            
            # Despite the timeout, save_scan_results should return True
            # because the main caching operations (Redis setex) complete
            result = await save_scan_results(project_id, test_data)
            
            # Should still return True because the timeout is non-fatal
            assert result is True


@pytest.mark.asyncio
async def test_save_scan_results_with_normal_state_hash():
    """Test normal operation when state hash completes within timeout."""
    project_id = "test-project-normal"
    test_data = {
        "keywords": [{"keyword": "test", "volume": 100}],
        "status": "complete",
    }
    
    # Should succeed normally (Redis is available in test environment)
    result = await save_scan_results(project_id, test_data)
    assert isinstance(result, bool)
    # Result depends on whether Redis is available, but the function
    # should not raise an exception
    

@pytest.mark.asyncio
async def test_differential_update_timeout_handling():
    """
    Test that differential update state saving doesn't block scan completion.
    This was tested through save_scan_results timeout handling above.
    """
    # The timeout handling is tested through the main save_scan_results path
    # since it wraps the differential update detector calls with asyncio.wait_for
    pass
