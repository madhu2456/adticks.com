"""
Adapter to convert spider crawl results to log analyzer format.

Reuses the existing LogParseResult and log analyzer logic with spider data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.seo.log_analyzer import LogParseResult, detect_orphans
from app.services.seo.web_spider import CrawlResult, SpiderStats


@dataclass
class SpiderAnalysisResult:
    """Result of analyzing spider crawl data."""
    aggregated: list[dict[str, Any]]
    summary: dict[str, Any]
    orphans: dict[str, list[str]]


def analyze_spider_results(
    crawl_results: list[CrawlResult],
    spider_stats: SpiderStats,
    sitemap_urls: set[str] | None = None,
) -> SpiderAnalysisResult:
    """
    Convert spider crawl results to analysis report.

    Mimics LogParseResult structure but uses spider data.
    Includes orphan detection if sitemap URLs provided.
    """
    # Aggregate crawl data similar to log analyzer
    aggregated: list[dict[str, Any]] = []
    crawled_urls: set[str] = set()

    for result in crawl_results:
        crawled_urls.add(result.url)
        aggregated.append({
            "bot": result.bot_name,
            "url": result.url,
            "status_code": result.status_code,
            "hits": 1,  # Each spider crawl is one "hit"
            "response_time_ms": result.response_time_ms,
            "last_crawled": result.crawl_timestamp,
            "error": result.error,
            "redirect_to": result.redirect_to,
        })

    # Sort by status code (errors first) and response time
    aggregated.sort(
        key=lambda x: (x["status_code"] >= 400, -x["response_time_ms"]),
        reverse=True,
    )

    # Build summary
    summary = {
        "total_urls_crawled": spider_stats.total_urls_crawled,
        "unique_urls": spider_stats.unique_urls,
        "bots": {"spider": spider_stats.total_urls_crawled},
        "status_distribution": {str(s): c for s, c in spider_stats.status_distribution.items()},
        "crawl_waste_pct": spider_stats.crawl_waste_pct,
        "top_status_codes": spider_stats.top_status_codes,
        "avg_response_time_ms": round(spider_stats.avg_response_time_ms, 2),
        "crawl_errors": spider_stats.crawl_errors,
    }

    # Detect orphans if sitemap provided
    orphans = {"crawled_not_in_sitemap": [], "in_sitemap_not_crawled": []}
    if sitemap_urls:
        orphans = detect_orphans(crawled_urls, sitemap_urls)

    return SpiderAnalysisResult(
        aggregated=aggregated,
        summary=summary,
        orphans=orphans,
    )
