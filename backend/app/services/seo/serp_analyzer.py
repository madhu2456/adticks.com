"""
AdTicks — SERP Analyzer (DuckDuckGo Optimized).

Captures the top 10 organic results plus SERP feature presence for a keyword.
Optimized for high-performance scraping of DuckDuckGo's HTML interface
to provide a 100% free "one-stop" search intelligence experience.
"""
from __future__ import annotations

import logging
import re
import random
import asyncio
from typing import Any
from urllib.parse import urlparse, unquote

import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

logger = logging.getLogger(__name__)

# Primary DDG endpoints
DDG_HTML = "https://html.duckduckgo.com/html/"
DDG_LITE = "https://duckduckgo.com/lite/"


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


async def _via_duckduckgo(keyword: str) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Robust scraping of DuckDuckGo's HTML search engine.
    Returns a list of results and detected SERP features.
    """
    # Rotating user agents for better resilience
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/",
        "Origin": "https://duckduckgo.com",
    }
    
    results: list[dict[str, Any]] = []
    features: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            # We use the HTML version as it's the easiest to parse without JavaScript
            resp = await client.post(DDG_HTML, data={"q": keyword})
            
            # If HTML is blocked, try LITE version
            if resp.status_code != 200:
                logger.warning(f"DDG HTML returned {resp.status_code}, trying LITE...")
                resp = await client.get(DDG_LITE, params={"q": keyword})
            
            if resp.status_code != 200:
                logger.error(f"DuckDuckGo search failed for '{keyword}' with status {resp.status_code}")
                return [], []
            
            soup = BeautifulSoup(resp.text, "html.parser")

        # Parse organic results
        # DDG HTML uses .result selector
        items = soup.select(".result") or soup.select("tr") # Lite uses tr
        
        for i, item in enumerate(items[:10]):
            a = item.select_one(".result__a") or item.select_one(".result-link")
            snippet_el = item.select_one(".result__snippet") or item.select_one(".result-snippet")
            
            if not a:
                continue
                
            url = a.get("href", "")
            
            # DDG HTML wraps internal redirect URLs in /l/?uddg=...
            if "/l/?uddg=" in url:
                m = re.search(r"uddg=([^&]+)", url)
                if m:
                    url = unquote(m.group(1))
            
            # Clean up double slashes if any
            if url.startswith("//"):
                url = "https:" + url
                
            title = a.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            
            # Filter out internal DDG links
            if "duckduckgo.com" in url or not url.startswith("http"):
                continue

            results.append({
                "position": len(results) + 1,
                "url": url,
                "title": title,
                "snippet": snippet,
                "domain": _domain(url),
                "domain_authority": _da_estimate(_domain(url)),
            })

        # Detect SERP features
        if soup.select_one(".zci__answer") or soup.select_one(".zero-click"):
            features.append("featured_snippet")
        if soup.select_one(".module--images") or "Images" in resp.text:
            features.append("images")
        if soup.select_one(".module--videos") or "Videos" in resp.text:
            features.append("video")
        if "Related searches" in resp.text:
            features.append("people_also_ask")

    except Exception as e:
        logger.exception(f"Error scraping DuckDuckGo for '{keyword}': {e}")
    
    return results, features


_KNOWN_AUTHORITY = {
    "wikipedia.org": 95, "youtube.com": 100, "amazon.com": 96, "reddit.com": 91,
    "github.com": 92, "linkedin.com": 98, "medium.com": 90, "stackoverflow.com": 92,
    "nytimes.com": 95, "bbc.com": 95, "forbes.com": 94, "nih.gov": 93, "harvard.edu": 94,
    "google.com": 100, "ahrefs.com": 90, "moz.com": 91, "semrush.com": 91,
}


def _da_estimate(domain: str) -> float:
    """Calculates a heuristic-based Domain Authority estimate."""
    if not domain:
        return 0.0
    if domain in _KNOWN_AUTHORITY:
        return float(_KNOWN_AUTHORITY[domain])
    
    # tld weighting
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    base = {"gov": 70, "edu": 65, "org": 40, "com": 25, "io": 20, "co": 20}.get(tld, 10)
    
    # Length / hyphen heuristic (shorter, no-hyphen domains tend to have more authority)
    bonus = min(20, 30 - len(domain))
    if "-" in domain:
        bonus -= 5
        
    return float(max(1, min(100, base + bonus)))


async def analyze_serp(
    keyword: str,
    location: str = "us",
    device: str = "desktop",
    **kwargs,
) -> dict[str, Any]:
    """
    Primary entry point for SERP analysis. 
    Now strictly uses DuckDuckGo to provide a cost-free experience.
    """
    logger.info(f"Analyzing SERP for '{keyword}' via DuckDuckGo")
    
    results, features = await _via_duckduckgo(keyword)

    # If results are empty, provide a small delay and retry once to handle transient network issues
    if not results:
        await asyncio.sleep(1.0)
        results, features = await _via_duckduckgo(keyword)

    return {
        "keyword_text": keyword,
        "location": location,
        "device": device,
        "results": results,
        "features_present": features,
    }
