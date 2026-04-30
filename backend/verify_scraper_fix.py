
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Mock dependencies
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force PLAYWRIGHT_AVAILABLE to False to test basic fallback
with patch('playwright.async_api.async_playwright', side_effect=ImportError):
    from app.services.seo.rank_tracker import _check_via_scrape

async def test_scraper_fallback():
    logging.basicConfig(level=logging.INFO)
    
    # Mock response for Google Search (200)
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '<html><a href="/url?q=https://test.com&sa=U">Result</a></html>'
    
    # Setup httpx mock
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_200
        
        print("Testing scraper fallback logic...")
        result = await _check_via_scrape("test keyword", "test.com")
        
        print(f"Position: {result}")
        assert result == 1
        print("✅ Success: Scraper correctly fell back to basic HTTP and parsed result!")

if __name__ == "__main__":
    asyncio.run(test_scraper_fallback())
