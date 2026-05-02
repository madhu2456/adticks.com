"""
AdTicks — Core Web Vitals + Lighthouse via Google's PageSpeed Insights API.

Free Google endpoint (5 req/sec without API key, 25k/day with key):
    https://www.googleapis.com/pagespeedonline/v5/runPagespeed

Returns:
    Performance / SEO / Accessibility / Best-Practices scores
    Lab metrics: FCP, LCP, TBT, CLS, SI, TTI
    Field metrics from CrUX: LCP, INP, CLS (when origin has data)
    Top 5 opportunities with potential time savings
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

def _audit_value(audits: dict, key: str) -> int | None:
    """Extract numeric value from audit."""
    audit = audits.get(key, {})
    num = audit.get("numericValue")
    return int(num) if num is not None else None


async def run_pagespeed(url: str, strategy: str = "mobile", categories: list[str] | None = None, api_key: str | None = None) -> dict[str, Any]:
    """
    Run PageSpeed Insights analysis on a URL.
    
    Requires PSI_API_KEY environment variable (from Google Cloud Console).
    Without it, limited to 5 req/sec (free tier quota).
    """
    if api_key is None:
        api_key = settings.PSI_API_KEY
    
    params = [("url", url), ("strategy", strategy)]
    if categories:
        for c in categories:
            params.append(("category", c))
    if api_key:
        params.append(("key", api_key))

    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.get(PSI_ENDPOINT, params=params)
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning("PSI rate limited (429) for %s. Retrying in %.1f seconds (attempt %d/%d)", url, delay, attempt + 1, max_retries)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.warning("PSI returned 429 for %s after %d retries", url, max_retries)
                        return _empty_result(url, strategy)
                elif resp.status_code != 200:
                    logger.warning("PSI returned %s for %s", resp.status_code, url)
                    return _empty_result(url, strategy)
                data = resp.json()
                break
            except Exception as e:
                logger.exception("PSI failed for %s: %s", url, e)
                return _empty_result(url, strategy)

    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    cats = lh.get("categories", {})

    # Field data (CrUX) takes priority over lab data when present
    loading = data.get("loadingExperience", {}).get("metrics", {})
    field_lcp = loading.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile")
    field_inp = (
        loading.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile")
        or loading.get("FIRST_INPUT_DELAY_MS", {}).get("percentile")
    )
    field_cls_raw = loading.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile")
    field_cls = (field_cls_raw / 100) if field_cls_raw is not None else None

    # opportunities
    opportunities = []
    for key, audit in audits.items():
        if audit.get("details", {}).get("type") == "opportunity":
            ms = audit.get("details", {}).get("overallSavingsMs")
            if ms and ms > 0:
                opportunities.append({
                    "id": key,
                    "title": audit.get("title"),
                    "description": audit.get("description"),
                    "savings_ms": int(ms),
                    "score": audit.get("score"),
                })
    opportunities.sort(key=lambda o: -(o["savings_ms"] or 0))
    opportunities = opportunities[:5]

    return {
        "url": url,
        "strategy": strategy,
        "lcp_ms": field_lcp if field_lcp is not None else _audit_value(audits, "largest-contentful-paint"),
        "inp_ms": field_inp,
        "cls": field_cls if field_cls is not None else _audit_value(audits, "cumulative-layout-shift"),
        "fcp_ms": _audit_value(audits, "first-contentful-paint"),
        "ttfb_ms": _audit_value(audits, "server-response-time"),
        "si_ms": _audit_value(audits, "speed-index"),
        "tbt_ms": _audit_value(audits, "total-blocking-time"),
        "performance_score": _score_to_int(cats.get("performance", {}).get("score")),
        "seo_score": _score_to_int(cats.get("seo", {}).get("score")),
        "accessibility_score": _score_to_int(cats.get("accessibility", {}).get("score")),
        "best_practices_score": _score_to_int(cats.get("best-practices", {}).get("score")),
        "opportunities": opportunities,
    }


def _empty_result(url: str, strategy: str) -> dict[str, Any]:
    return {
        "url": url,
        "strategy": strategy,
        "lcp_ms": None,
        "inp_ms": None,
        "cls": None,
        "fcp_ms": None,
        "ttfb_ms": None,
        "si_ms": None,
        "tbt_ms": None,
        "performance_score": None,
        "seo_score": None,
        "accessibility_score": None,
        "best_practices_score": None,
        "opportunities": [],
    }


def _score_to_int(score: float | None) -> int | None:
    if score is None:
        return None
    return int(round(score * 100))


async def run_both_strategies(url: str, api_key: str | None = None) -> dict[str, dict[str, Any]]:
    """Convenience: run both mobile + desktop."""
    import asyncio
    mobile, desktop = await asyncio.gather(
        run_pagespeed(url, "mobile", api_key),
        run_pagespeed(url, "desktop", api_key),
        return_exceptions=False,
    )
    return {"mobile": mobile, "desktop": desktop}
