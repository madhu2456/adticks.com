"""
AdTicks — SERP Analyzer.

Captures the top 10 organic results plus SERP feature presence for a keyword.
By default uses DuckDuckGo's HTML SERP (no API key, no quota) and falls back
to SerpAPI when SERPAPI_KEY is configured. Results are normalized into
the SerpOverview schema.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DDG_HTML = "https://html.duckduckgo.com/html/"


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


async def _via_serpapi(keyword: str, location: str, device: str, api_key: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        params = {
            "engine": "google",
            "q": keyword,
            "gl": location,
            "device": device,
            "api_key": api_key,
        }
        resp = await client.get("https://serpapi.com/search", params=params)
        if resp.status_code != 200:
            return {}
        return resp.json()


def _features_from_serpapi(data: dict[str, Any]) -> list[str]:
    features: list[str] = []
    if "answer_box" in data:
        features.append("featured_snippet")
    if "related_questions" in data:
        features.append("people_also_ask")
    if "knowledge_graph" in data:
        features.append("knowledge_panel")
    if "ads" in data or "shopping_results" in data:
        features.append("ads")
    if "local_results" in data:
        features.append("local_pack")
    if "videos" in data:
        features.append("video")
    if "images_results" in data:
        features.append("images")
    return features


async def _via_duckduckgo(keyword: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Free fallback when no SerpAPI key. Returns (results, features)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 AdTicksSERP/1.0",
    }
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        resp = await client.post(DDG_HTML, data={"q": keyword})
        if resp.status_code != 200:
            return [], []
        soup = BeautifulSoup(resp.text, "html.parser")

    results: list[dict[str, Any]] = []
    for i, item in enumerate(soup.select(".result")[:10]):
        a = item.select_one(".result__a")
        snippet_el = item.select_one(".result__snippet")
        if not a:
            continue
        url = a.get("href", "")
        # DDG wraps URLs in /l/?uddg=...
        m = re.search(r"uddg=([^&]+)", url)
        if m:
            from urllib.parse import unquote
            url = unquote(m.group(1))
        title = a.get_text(strip=True)
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        results.append({
            "position": i + 1,
            "url": url,
            "title": title,
            "snippet": snippet,
            "domain": _domain(url),
            "domain_authority": _da_estimate(_domain(url)),
        })

    features: list[str] = []
    if soup.select_one(".zci__answer"):
        features.append("featured_snippet")
    if soup.select_one(".module--images"):
        features.append("images")
    if soup.select_one(".module--videos"):
        features.append("video")
    return results, features


_KNOWN_AUTHORITY = {
    "wikipedia.org": 95, "youtube.com": 100, "amazon.com": 96, "reddit.com": 91,
    "github.com": 92, "linkedin.com": 98, "medium.com": 90, "stackoverflow.com": 92,
    "nytimes.com": 95, "bbc.com": 95, "forbes.com": 94, "nih.gov": 93, "harvard.edu": 94,
    "google.com": 100, "ahrefs.com": 90, "moz.com": 91, "semrush.com": 91,
}


def _da_estimate(domain: str) -> float:
    """Cheap DA estimate by TLD + known list."""
    if not domain:
        return 0.0
    if domain in _KNOWN_AUTHORITY:
        return float(_KNOWN_AUTHORITY[domain])
    # tld weighting
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    base = {"gov": 70, "edu": 65, "org": 40, "com": 25, "io": 20, "co": 20}.get(tld, 10)
    # Length / hyphen heuristic
    return float(base + min(20, 30 - len(domain)))


async def analyze_serp(
    keyword: str,
    location: str = "us",
    device: str = "desktop",
    serpapi_key: str | None = None,
) -> dict[str, Any]:
    """Return SERP overview for the given keyword."""
    serpapi_key = serpapi_key or os.environ.get("SERPAPI_KEY", "")
    results: list[dict[str, Any]] = []
    features: list[str] = []

    if serpapi_key:
        try:
            data = await _via_serpapi(keyword, location, device, serpapi_key)
            for item in data.get("organic_results", [])[:10]:
                url = item.get("link", "")
                results.append({
                    "position": item.get("position"),
                    "url": url,
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "domain": _domain(url),
                    "domain_authority": _da_estimate(_domain(url)),
                })
            features = _features_from_serpapi(data)
        except Exception as e:
            logger.warning("SerpAPI failed (%s); falling back to DDG", e)

    if not results:
        results, features = await _via_duckduckgo(keyword)

    return {
        "keyword_text": keyword,
        "location": location,
        "device": device,
        "results": results,
        "features_present": features,
    }
