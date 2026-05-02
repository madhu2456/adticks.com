"""
Rank tracking service for AdTicks SEO module.
Checks keyword rankings via SerpAPI or Google scraping with user-agent rotation.
Optimized for low resource usage.
"""

import logging
import asyncio
import random
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from urllib.parse import unquote

import httpx
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

SERPAPI_BASE = "https://serpapi.com/search"


class PlaywrightManager:
    """Manages a shared Playwright browser instance to save resources."""
    _browser: Optional[Browser] = None
    _playwright = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_browser(cls) -> Browser:
        async with cls._lock:
            if cls._browser is None:
                logger.info("🚀 Launching optimized headless Chrome instance...")
                cls._playwright = await async_playwright().start()
                cls._browser = await cls._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--disable-gpu",
                        "--no-first-run",
                        "--no-zygote",
                        "--disable-extensions",
                        "--disable-default-apps",
                        "--mute-audio",
                    ]
                )
            return cls._browser

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None


async def _intercept_requests(route):
    """Block images, fonts, and stylesheets to save CPU/RAM."""
    if route.request.resource_type in ["image", "font", "stylesheet", "media", "other"]:
        await route.abort()
    else:
        await route.continue_()


def _get_random_ua() -> str:
    """Return a random user-agent string."""
    return random.choice(USER_AGENTS)


async def _check_via_serpapi(keyword: str, domain: str, api_key: str) -> Optional[int]:
    """
    Query SerpAPI for a keyword and return the domain's position (1-100) or None.
    """
    params = {
        "q": keyword,
        "api_key": api_key,
        "engine": "google",
        "num": 100,
        "gl": "us",
        "hl": "en",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(SERPAPI_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
            organic = data.get("organic_results", [])
            for result in organic:
                link = result.get("link", "")
                if domain.lower().rstrip("/") in link.lower():
                    return result.get("position", organic.index(result) + 1)
    except Exception as e:
        logger.warning(f"SerpAPI error for '{keyword}': {e}")
    return None


async def _check_via_scrape(keyword: str, domain: str) -> Optional[int]:
    """
    Scrape Google search results for a keyword using Playwright (fallback).
    Optimized for resource efficiency.
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available, falling back to basic scrape")
        return await _check_via_scrape_basic(keyword, domain)

    try:
        browser = await PlaywrightManager.get_browser()
        
        # Fresh context for each keyword to avoid cookie persistence/detection
        context = await browser.new_context(
            user_agent=_get_random_ua(),
            viewport={'width': 1280, 'height': 720},
            locale="en-US",
        )
        page = await context.new_page()

        # Optimize: Block heavy resources
        await page.route("**/*", _intercept_requests)

        # Stealth Script
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        try:
            search_url = f"https://www.google.com/search?q={keyword}&num=100&hl=en&gl=us"
            logger.info(f"Playwright: Scraping Google for '{keyword}'")
            
            # Navigate with aggressive timeout and wait for minimal state
            await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            
            if "sorry/index" in page.url:
                logger.warning(f"Google detected automated traffic for '{keyword}'")
                return None

            # Extract links efficiently
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('div.g a'))
                    .map(a => a.href)
                    .filter(href => href && href.startsWith('http') && !href.includes('google.com'));
            }''')
            
            position = 1
            seen = set()
            for link in links:
                clean_link = link.split('#')[0].split('?')[0].rstrip('/')
                if clean_link in seen:
                    continue
                seen.add(clean_link)
                
                if domain.lower().rstrip("/") in clean_link.lower():
                    logger.info(f"Found '{domain}' at position {position} for '{keyword}'")
                    return position
                position += 1
                if position > 100: break
                    
        finally:
            await page.close()
            await context.close()
                    
    except Exception as e:
        logger.error(f"Playwright scraping failed for '{keyword}': {e}")
        return await _check_via_scrape_basic(keyword, domain)

    return None


async def _check_via_scrape_basic(keyword: str, domain: str) -> Optional[int]:
    """Basic HTTP-based scrape fallback."""
    url = "https://www.google.com/search"
    params = {"q": keyword, "num": 100, "hl": "en", "gl": "us"}
    headers = {
        "User-Agent": _get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                logger.warning(f"Basic scrape hit 429 for '{keyword}'")
                return None
            resp.raise_for_status()
            html = resp.text

            pattern = re.compile(r'href="/url\?q=(https?://[^&"]+)', re.IGNORECASE)
            matches = pattern.findall(html)

            position = 1
            seen = set()
            for link in matches:
                link = unquote(link)
                if link in seen:
                    continue
                seen.add(link)
                if domain.lower().rstrip("/") in link.lower():
                    return position
                position += 1
                if position > 100:
                    break
    except Exception as e:
        logger.warning(f"Basic scraping failed for '{keyword}': {e}")
    return None


async def check_rankings(
    keyword: str,
    domain: str,
    serpapi_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check the ranking position of a domain for a given keyword.
    """
    logger.info(f"Checking ranking for keyword='{keyword}' domain='{domain}'")
    position: Optional[int] = None
    source = "mock"

    if serpapi_key:
        position = await _check_via_serpapi(keyword, domain, serpapi_key)
        source = "serpapi"
    else:
        try:
            # Human-like jitter
            await asyncio.sleep(random.uniform(4.0, 8.0))
            position = await _check_via_scrape(keyword, domain)
            source = "scrape"
        except Exception as e:
            logger.warning(f"Scraping unavailable: {e}")

    # Fallback to mock
    if position is None:
        position = _mock_position(keyword, domain)
        source = "mock"

    return {
        "keyword": keyword,
        "domain": domain,
        "position": position,
        "url": f"https://{domain}" if position else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }


async def bulk_rank_check(
    project_id: str,
    keywords: List[Dict[str, Any]],
    domain: str,
    serpapi_key: Optional[str] = None,
    concurrency: int = 5,
) -> List[Dict[str, Any]]:
    """
    Batch rank checking with resource management.
    """
    # Force low concurrency for scraping
    if not serpapi_key:
        concurrency = 1
        logger.info("Scraping mode: Using serial execution to save resources and avoid blocks.")

    results = []
    semaphore = asyncio.Semaphore(concurrency)

    async def _check_one(kw_dict: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            kw_text = kw_dict.get("keyword", "")
            try:
                res = await check_rankings(kw_text, domain, serpapi_key)
                res["keyword_id"] = kw_dict.get("id")
                res["project_id"] = project_id
                return res
            except Exception as e:
                logger.error(f"Error checking '{kw_text}': {e}")
                return {
                    "keyword": kw_text, "domain": domain, "position": None,
                    "url": None, "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "error", "keyword_id": kw_dict.get("id"), "project_id": project_id
                }

    tasks = [_check_one(kw) for kw in keywords]
    results = await asyncio.gather(*tasks)

    # Clean up browser after bulk operation
    if not serpapi_key and PLAYWRIGHT_AVAILABLE:
        await PlaywrightManager.close()

    return list(results)
