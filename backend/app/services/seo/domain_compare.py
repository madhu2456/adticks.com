"""
AdTicks — Domain comparison + bulk URL analyzer.

`compare_domains` collects a snapshot of headline metrics for the project
domain and one or more competitors. Every metric source is pluggable so
paid providers (Ahrefs/SEMrush/Moz) can be swapped in.

`run_bulk_analysis` runs lightweight on-page audits or Core Web Vitals
checks across a list of URLs and returns a flat result list.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from .serp_analyzer import _da_estimate
from .core_web_vitals import run_pagespeed
from .site_crawler import SiteCrawler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain comparison
# ---------------------------------------------------------------------------
@dataclass
class DomainSnapshot:
    domain: str
    domain_authority: float
    homepage_status: int | None = None
    homepage_response_ms: int | None = None
    indexable: bool | None = None
    estimated_traffic: int | None = None
    estimated_keywords: int | None = None
    backlink_estimate: int | None = None


async def _probe_homepage(client: httpx.AsyncClient, domain: str) -> DomainSnapshot:
    snap = DomainSnapshot(domain=domain, domain_authority=_da_estimate(domain))
    url = domain if domain.startswith("http") else f"https://{domain}"
    try:
        import time
        t0 = time.perf_counter()
        resp = await client.get(url, follow_redirects=True, timeout=10)
        snap.homepage_status = resp.status_code
        snap.homepage_response_ms = int((time.perf_counter() - t0) * 1000)
        snap.indexable = "noindex" not in resp.text.lower()
    except Exception as e:
        logger.debug("domain probe failed for %s: %s", domain, e)
    return snap


async def compare_domains(primary: str, competitors: list[str]) -> dict[str, Any]:
    """Collect a side-by-side snapshot for primary + competitors."""
    headers = {"User-Agent": "AdTicksBot/1.0 DomainCompare"}
    all_domains = [primary] + [c for c in competitors if c]
    async with httpx.AsyncClient(headers=headers) as client:
        snaps = await asyncio.gather(*(_probe_homepage(client, d) for d in all_domains))
    metrics: dict[str, Any] = {}
    for s in snaps:
        metrics[s.domain] = {
            "domain_authority": s.domain_authority,
            "homepage_status": s.homepage_status,
            "homepage_response_ms": s.homepage_response_ms,
            "indexable": s.indexable,
            "estimated_traffic": s.estimated_traffic,
            "estimated_keywords": s.estimated_keywords,
            "backlink_estimate": s.backlink_estimate,
        }
    return {
        "primary_domain": primary,
        "competitor_domains": competitors,
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# Bulk URL analyzer
# ---------------------------------------------------------------------------
async def _quick_onpage(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    from bs4 import BeautifulSoup
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            return {"url": url, "status": "failed", "error": f"HTTP {r.status_code}"}
        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title and soup.title.string else None
        meta = soup.find("meta", attrs={"name": "description"})
        h1 = soup.find("h1")
        return {
            "url": url,
            "status": "done",
            "result": {
                "status_code": r.status_code,
                "title": title,
                "title_length": len(title) if title else 0,
                "meta_description": meta["content"] if meta and meta.get("content") else None,
                "meta_description_length": len(meta["content"]) if meta and meta.get("content") else 0,
                "h1": h1.get_text(strip=True) if h1 else None,
                "h1_count": len(soup.find_all("h1")),
                "word_count": len(r.text.split()),
                "image_count": len(soup.find_all("img")),
                "image_missing_alt": sum(1 for i in soup.find_all("img") if not i.get("alt")),
                "internal_link_count": len(soup.find_all("a", href=True)),
            },
        }
    except Exception as e:
        return {"url": url, "status": "failed", "error": str(e)}


async def run_bulk_analysis(
    urls: list[str],
    job_type: str = "onpage",
    concurrency: int = 5,
    psi_api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Run an analysis across many URLs. Returns a flat list of result rows."""
    sem = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": "AdTicksBot/1.0 BulkAnalyzer"}

    if job_type == "onpage":
        async with httpx.AsyncClient(headers=headers) as client:
            async def runner(u):
                async with sem:
                    return await _quick_onpage(client, u)
            return await asyncio.gather(*(runner(u) for u in urls))

    if job_type == "cwv":
        async def cwv_runner(u):
            async with sem:
                try:
                    out = await run_pagespeed(u, strategy="mobile", api_key=psi_api_key)
                    return {"url": u, "status": "done", "result": out}
                except Exception as e:
                    return {"url": u, "status": "failed", "error": str(e)}
        return await asyncio.gather(*(cwv_runner(u) for u in urls))

    raise ValueError(f"Unknown job_type: {job_type}")
