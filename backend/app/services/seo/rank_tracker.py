"""
Rank tracking service for AdTicks SEO module.
Checks keyword rankings via SerpAPI or Google scraping with user-agent rotation.
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
    from playwright.async_api import async_playwright
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


def _get_random_ua() -> str:
    """Return a random user-agent string."""
    return random.choice(USER_AGENTS)


def _mock_position(keyword: str, domain: str) -> Optional[int]:
    """
    Deterministic mock ranking for when no API key is available.
    Returns a position 1-100 or None (not ranking).
    """
    seed = hash(f"{keyword}:{domain}") % 1000
    if seed < 150:
        return None  # Not ranking
    if seed < 250:
        return random.randint(1, 10)
    if seed < 450:
        return random.randint(11, 30)
    if seed < 700:
        return random.randint(31, 70)
    return random.randint(71, 100)


async def _check_via_serpapi(keyword: str, domain: str, api_key: str) -> Optional[int]:
    """
    Query SerpAPI for a keyword and return the domain's position (1-100) or None.

    Args:
        keyword: Search keyword to look up
        domain: Domain to find in results
        api_key: SerpAPI key

    Returns:
        Integer position 1-100 or None if not found in top 100
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
    except httpx.HTTPStatusError as e:
        logger.warning(f"SerpAPI HTTP error for '{keyword}': {e}")
    except Exception as e:
        logger.warning(f"SerpAPI error for '{keyword}': {e}")
    return None


async def _check_via_scrape(keyword: str, domain: str) -> Optional[int]:
    """
    Scrape Google search results for a keyword using Playwright (fallback).
    Uses a headless browser to better mimic real user activity.

    Args:
        keyword: Search keyword
        domain: Domain to locate

    Returns:
        Integer position or None
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available, falling back to basic scrape")
        return await _check_via_scrape_basic(keyword, domain)

    url = f"https://www.google.com/search?q={keyword}&num=100&hl=en&gl=us"
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            # Randomized viewport
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            
            context = await browser.new_context(
                user_agent=_get_random_ua(),
                viewport={'width': width, 'height': height},
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = await context.new_page()

            # --- Stealth Script: Hide WebDriver ---
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Additional stealth headers
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
                "DNT": "1",
            })
            
            # Navigate to Google with a small delay
            logger.info(f"Playwright: Navigating to Google for '{keyword}'")
            # Using a more natural navigation
            await page.goto("https://www.google.com", wait_until="networkidle")
            
            # Wait a bit then search instead of direct URL
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            search_url = f"https://www.google.com/search?q={keyword}&num=100&hl=en&gl=us"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            
            # Check for CAPTCHA or 'sorry' page
            if "sorry/index" in page.url:
                logger.warning(f"Google detected automated traffic for '{keyword}'")
                await browser.close()
                return None

            # Extract links from organic results
            # Typical Google organic result link selector: div.g a[data-ved] or just h3 + a
            # We'll use a more generic approach to find all organic links
            links = await page.evaluate('''() => {
                const results = [];
                const anchors = document.querySelectorAll('div.g a');
                for (const a of anchors) {
                    const href = a.href;
                    if (href && href.startsWith('http') && !href.includes('google.com')) {
                        results.push(href);
                    }
                }
                return results;
            }''')
            
            await browser.close()

            position = 1
            seen = set()
            for link in links:
                # Clean URL (remove tracking params if any)
                clean_link = link.split('#')[0].split('?')[0].rstrip('/')
                if clean_link in seen:
                    continue
                seen.add(clean_link)
                
                if domain.lower().rstrip("/") in clean_link.lower():
                    logger.info(f"Found '{domain}' at position {position} for '{keyword}' via Playwright")
                    return position
                position += 1
                if position > 100:
                    break
                    
    except Exception as e:
        logger.error(f"Playwright scraping failed for '{keyword}': {e}")
        # Final fallback to basic scrape if playwright fails
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

    Args:
        keyword: The keyword to check
        domain: The domain to find
        serpapi_key: Optional SerpAPI key; falls back to scraping then mock

    Returns:
        Dict with: keyword, domain, position (int or None), url (str or None), timestamp, source
    """
    logger.info(f"Checking ranking for keyword='{keyword}' domain='{domain}'")
    position: Optional[int] = None
    source = "mock"

    if serpapi_key:
        position = await _check_via_serpapi(keyword, domain, serpapi_key)
        source = "serpapi"
    else:
        try:
            # Add significant jitter to avoid rate limiting
            # 3-7 seconds is more human-like than the previous 1.5-3.5s
            await asyncio.sleep(random.uniform(3.0, 7.0))
            position = await _check_via_scrape(keyword, domain)
            source = "scrape"
        except Exception as e:
            logger.warning(f"Scraping unavailable: {e}")

    # Final fallback to mock
    if position is None and source in ("scrape",):
        position = _mock_position(keyword, domain)
        source = "mock"
    elif source == "mock":
        position = _mock_position(keyword, domain)

    result = {
        "keyword": keyword,
        "domain": domain,
        "position": position,
        "url": f"https://{domain}" if position else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }
    logger.info(f"Ranking result: {result}")
    return result


async def _batch_check_via_serpapi(
    keywords: List[str],
    domain: str,
    api_key: str,
    timeout: float = 30.0,
) -> Dict[str, Optional[int]]:
    """
    Batch check multiple keywords via SerpAPI.
    Makes individual requests but with optimized concurrency control.
    
    Args:
        keywords: List of keywords to check
        domain: Target domain
        api_key: SerpAPI key
        timeout: Request timeout
    
    Returns:
        Dict mapping keyword -> position (or None if not ranked)
    """
    results = {}
    semaphore = asyncio.Semaphore(5)  # SerpAPI rate limiting: 5 concurrent
    
    async def _check_one(keyword: str) -> tuple[str, Optional[int]]:
        async with semaphore:
            try:
                position = await _check_via_serpapi(keyword, domain, api_key)
                return keyword, position
            except Exception as e:
                logger.warning(f"Batch check error for '{keyword}': {e}")
                return keyword, None
    
    tasks = [_check_one(kw) for kw in keywords]
    batch_results = await asyncio.gather(*tasks, return_exceptions=False)
    
    for keyword, position in batch_results:
        results[keyword] = position
    
    return results


async def bulk_rank_check(
    project_id: str,
    keywords: List[Dict[str, Any]],
    domain: str,
    serpapi_key: Optional[str] = None,
    concurrency: int = 5,
) -> List[Dict[str, Any]]:
    """
    Batch rank checking for a list of keywords with improved performance.

    Args:
        project_id: The project ID for logging/storage reference
        keywords: List of keyword dicts (must contain 'keyword' field)
        domain: Target domain
        serpapi_key: Optional SerpAPI key
        concurrency: Max concurrent requests (default 5 for better stability)

    Returns:
        List of ranking result dicts (same shape as check_rankings output)
    """
    # Reduce concurrency if scraping to avoid Google blocks
    if not serpapi_key:
        concurrency = 1
        logger.info(f"Scraping mode: Limiting concurrency to {concurrency} (conservative) to avoid 429s")

    logger.info(f"Bulk rank check: project_id={project_id} keywords={len(keywords)} domain={domain} concurrency={concurrency}")
    results = []
    semaphore = asyncio.Semaphore(concurrency)

    async def _check_one_with_retry(kw_dict: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        async with semaphore:
            kw_text = kw_dict.get("keyword", "")
            for attempt in range(max_retries):
                try:
                    result = await check_rankings(kw_text, domain, serpapi_key)
                    result["keyword_id"] = kw_dict.get("id")
                    result["project_id"] = project_id
                    return result
                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"Timeout checking '{kw_text}', retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed to check '{kw_text}' after {max_retries} attempts")
                        return {
                            "keyword": kw_text,
                            "domain": domain,
                            "position": None,
                            "url": None,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "source": "error",
                            "keyword_id": kw_dict.get("id"),
                            "project_id": project_id,
                        }
                except Exception as e:
                    logger.warning(f"Error checking '{kw_text}': {e}")
                    return {
                        "keyword": kw_text,
                        "domain": domain,
                        "position": None,
                        "url": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "error",
                        "keyword_id": kw_dict.get("id"),
                        "project_id": project_id,
                    }

    tasks = [_check_one_with_retry(kw) for kw in keywords]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    logger.info(f"Bulk rank check complete: {len(results)} results processed")
    return results
