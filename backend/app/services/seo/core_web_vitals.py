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

def _audit_value(audits: dict, key: str) -> float | None:
    """Extract numeric value from audit."""
    audit = audits.get(key, {})
    num = audit.get("numericValue")
    return float(num) if num is not None else None


async def run_pagespeed(url: str, strategy: str = "mobile", categories: list[str] | None = None, api_key: str | None = None) -> dict[str, Any]:
    """
    Run PageSpeed Insights analysis on a URL.
    
    Requires PSI_API_KEY environment variable (from Google Cloud Console).
    Without it, limited to 5 req/sec (free tier quota).
    """
    # Ensure URL has a scheme (Google API requires it)
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    if api_key is None:
        api_key = settings.PSI_API_KEY
    
    params = [("url", url), ("strategy", strategy)]
    if categories:
        for c in categories:
            params.append(("category", c))
    if api_key:
        params.append(("key", api_key))
    else:
        logger.warning("Running PSI without API key. This may lead to 429 rate limits.")

    max_retries = 5
    base_delay = 2.0
    
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.get(PSI_ENDPOINT, params=params)
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        import random
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                        logger.warning("PSI rate limited (429) for %s. Retrying in %.1f seconds (attempt %d/%d)", url, delay, attempt + 1, max_retries)
                        if not api_key:
                            logger.info("Tip: Set PSI_API_KEY in your .env file to get higher rate limits.")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.warning("PSI returned 429 for %s after %d retries. Try setting PSI_API_KEY.", url, max_retries)
                        return _empty_result(url, strategy)
                elif resp.status_code != 200:
                    error_detail = "No detail"
                    try:
                        error_json = resp.json()
                        error_detail = error_json.get("error", {}).get("message", str(error_json))
                    except:
                        error_detail = resp.text[:200]
                    logger.warning("PSI returned %s for %s: %s", resp.status_code, url, error_detail)
                    return _empty_result(url, strategy)
                data = resp.json()
                break
            except Exception as e:
                logger.exception("PSI failed for %s: %s", url, e)
                return _empty_result(url, strategy)

    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    cats = lh.get("categories", {})
    
    # Log available audit keys for debugging (using warning to ensure it shows in logs)
    if not audits:
        logger.warning("PSI response for %s missing audits. Keys in data: %s", url, list(data.keys()))
    else:
        # Check for a few expected keys to see if they exist
        expected = ["largest-contentful-paint", "first-contentful-paint", "cumulative-layout-shift", "server-response-time"]
        found = [k for k in expected if k in audits]
        logger.warning("PSI audits for %s: found %d/%d expected keys. Sample keys: %s", 
                       url, len(found), len(expected), list(audits.keys())[:10])

    def _get_metric(keys: list[str]) -> float | None:
        for k in keys:
            val = _audit_value(audits, k)
            if val is not None:
                return val
        return None

    # Field data (CrUX) takes priority over lab data when present
    loading = data.get("loadingExperience", {}).get("metrics", {})
    field_lcp = loading.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile")
    field_inp = (
        loading.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile")
        or loading.get("FIRST_INPUT_DELAY_MS", {}).get("percentile")
    )
    field_cls_raw = loading.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile")
    field_cls = (field_cls_raw / 100) if field_cls_raw is not None else None
    field_fcp = loading.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile")

    # metrics with fallbacks
    lcp = field_lcp if field_lcp is not None else _get_metric(["largest-contentful-paint", "largestContentfulPaint"])
    fcp = field_fcp if field_fcp is not None else _get_metric(["first-contentful-paint", "firstContentfulPaint"])
    cls = field_cls if field_cls is not None else _get_metric(["cumulative-layout-shift", "cumulativeLayoutShift"])
    ttfb = _get_metric(["server-response-time", "serverResponseTime", "network-server-latency"])
    si = _get_metric(["speed-index", "speedIndex"])
    tbt = _get_metric(["total-blocking-time", "totalBlockingTime"])

    # opportunities and diagnostics
    opportunities = []
    for key, audit in audits.items():
        # Capture both 'opportunity' and 'diagnostic' types for richer detail
        audit_type = audit.get("details", {}).get("type")
        if audit_type in ("opportunity", "diagnostic"):
            ms = audit.get("details", {}).get("overallSavingsMs")
            
            # For diagnostics, we might not have 'overallSavingsMs', so we use score
            # or just include them if they represent an issue (score < 1)
            score = audit.get("score")
            
            # Only include if there's actual potential savings or it's a failing diagnostic
            if (ms and ms > 0) or (score is not None and score < 0.9):
                opportunities.append({
                    "id": key,
                    "title": audit.get("title"),
                    "description": audit.get("description"), # Detailed explanation with links
                    "savings_ms": int(ms) if ms else 0,
                    "score": score,
                    "display_value": audit.get("displayValue"),
                })
    
    # Sort by impact: prioritize high savings, then low scores
    opportunities.sort(key=lambda o: (-(o["savings_ms"] or 0), o["score"] if o["score"] is not None else 1))
    opportunities = opportunities[:8] # Return top 8 for more depth

    return {
        "url": url,
        "strategy": strategy,
        "lcp_ms": lcp,
        "inp_ms": field_inp,
        "cls": cls,
        "fcp_ms": fcp,
        "ttfb_ms": ttfb,
        "si_ms": si,
        "tbt_ms": tbt,
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
