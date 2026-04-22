"""
Main SEO service coordinator for AdTicks.
Orchestrates keyword generation, rank tracking, on-page analysis,
technical SEO, and content gap analysis.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .keyword_service import generate_keywords, cluster_keywords
from .rank_tracker import bulk_rank_check
from .on_page_analyzer import analyze_url
from .technical_seo import check_technical
from .content_gap_analyzer import find_gaps

logger = logging.getLogger(__name__)


async def run_keyword_discovery(
    project_id: str,
    domain: str,
    industry: str,
    seed_keywords: List[str],
) -> Dict[str, Any]:
    """
    Run keyword discovery and clustering for a project.

    Args:
        project_id: Project identifier
        domain: Target domain
        industry: Industry category
        seed_keywords: Seed keywords to expand

    Returns:
        Dict with generated keywords and cluster assignments
    """
    logger.info(f"[{project_id}] Starting keyword discovery for {domain}")
    keywords = await generate_keywords(domain, industry, seed_keywords)
    clusters = cluster_keywords(keywords)

    return {
        "project_id": project_id,
        "domain": domain,
        "keywords": keywords,
        "clusters": {str(k): v for k, v in clusters.items()},
        "keyword_count": len(keywords),
        "cluster_count": len(clusters),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_rank_audit(
    project_id: str,
    domain: str,
    keywords: List[Dict[str, Any]],
    serpapi_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run rank tracking for all project keywords.

    Args:
        project_id: Project identifier
        domain: Target domain
        keywords: List of keyword dicts
        serpapi_key: Optional SerpAPI key

    Returns:
        Dict with ranking results and summary stats
    """
    logger.info(f"[{project_id}] Starting rank audit for {domain} with {len(keywords)} keywords")
    rankings = await bulk_rank_check(project_id, keywords, domain, serpapi_key)

    ranked = [r for r in rankings if r.get("position") is not None]
    top10 = [r for r in ranked if r.get("position", 101) <= 10]
    top30 = [r for r in ranked if r.get("position", 101) <= 30]

    return {
        "project_id": project_id,
        "domain": domain,
        "rankings": rankings,
        "summary": {
            "total_keywords": len(keywords),
            "ranking_count": len(ranked),
            "not_ranking": len(keywords) - len(ranked),
            "top_10_count": len(top10),
            "top_30_count": len(top30),
            "avg_position": round(sum(r["position"] for r in ranked) / len(ranked), 1) if ranked else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_on_page_audit(
    project_id: str,
    urls: List[str],
    target_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run on-page SEO analysis for a list of URLs.

    Args:
        project_id: Project identifier
        urls: List of URLs to analyze
        target_keywords: Optional keywords to check density

    Returns:
        Dict with per-URL analysis and summary
    """
    logger.info(f"[{project_id}] Starting on-page audit for {len(urls)} URLs")

    async def _analyze_one(url: str) -> Dict[str, Any]:
        try:
            return await analyze_url(url, target_keywords)
        except Exception as e:
            logger.error(f"Failed to analyze {url}: {e}")
            return {"url": url, "error": str(e), "score": 0, "issues": [str(e)]}

    results = await asyncio.gather(*[_analyze_one(u) for u in urls])

    avg_score = round(sum(r.get("score", 0) for r in results) / len(results), 1) if results else 0
    all_issues = []
    for r in results:
        all_issues.extend(r.get("issues", []))

    return {
        "project_id": project_id,
        "url_analyses": list(results),
        "summary": {
            "urls_analyzed": len(results),
            "avg_score": avg_score,
            "total_issues": len(all_issues),
            "top_issues": list(set(all_issues))[:10],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_full_seo_audit(
    project_id: str,
    domain: str,
    industry: str = "Technology",
    seed_keywords: Optional[List[str]] = None,
    competitor_domains: Optional[List[str]] = None,
    pages_to_audit: Optional[List[str]] = None,
    serpapi_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a full SEO audit: keyword discovery, rank tracking, technical SEO,
    on-page analysis, and content gap analysis.

    Args:
        project_id: Project identifier
        domain: Target domain
        industry: Industry category
        seed_keywords: Seed keywords (auto-generated if not provided)
        competitor_domains: Competitor domains for gap analysis
        pages_to_audit: Specific pages to analyze (defaults to homepage)
        serpapi_key: Optional SerpAPI key for rank checking

    Returns:
        Complete audit results dict
    """
    logger.info(f"[{project_id}] Starting full SEO audit for domain={domain}")
    start_time = datetime.now(timezone.utc)

    seeds = seed_keywords or [domain.split(".")[0], industry.lower(), "software", "platform"]
    pages = pages_to_audit or [f"https://{domain}"]
    competitors = competitor_domains or []

    # Run all checks concurrently where possible
    keyword_task = asyncio.create_task(
        run_keyword_discovery(project_id, domain, industry, seeds)
    )
    technical_task = asyncio.create_task(
        check_technical(domain)
    )

    keyword_result = await keyword_task
    technical_result = await technical_task

    # Rank audit needs keywords
    keywords = keyword_result.get("keywords", [])[:50]  # Limit for speed
    rank_task = asyncio.create_task(
        run_rank_audit(project_id, domain, keywords, serpapi_key)
    )

    # On-page + gap analysis concurrently
    onpage_task = asyncio.create_task(
        run_on_page_audit(project_id, pages[:5], [kw["keyword"] for kw in keywords[:10]])
    )
    gap_task = asyncio.create_task(
        find_gaps([kw["keyword"] for kw in keywords], competitors, industry)
    ) if competitors else None

    rank_result = await rank_task
    onpage_result = await onpage_task
    gap_result = await gap_task if gap_task else {"gaps": [], "count": 0}

    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    audit = {
        "project_id": project_id,
        "domain": domain,
        "industry": industry,
        "audit_started": start_time.isoformat(),
        "audit_completed": end_time.isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "keyword_discovery": keyword_result,
        "rank_tracking": rank_result,
        "technical_seo": technical_result,
        "on_page_analysis": onpage_result,
        "content_gaps": gap_result if isinstance(gap_result, list) else [],
        "overall_health": _compute_overall_health(technical_result, rank_result, onpage_result),
    }

    logger.info(f"[{project_id}] Full SEO audit complete in {duration_seconds:.1f}s")
    return audit


def _compute_overall_health(
    technical: Dict[str, Any],
    rankings: Dict[str, Any],
    onpage: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute an overall SEO health score from all sub-audits."""
    tech_score = technical.get("health_score", 0)
    onpage_score = onpage.get("summary", {}).get("avg_score", 0)

    ranking_summary = rankings.get("summary", {})
    total_kw = ranking_summary.get("total_keywords", 1)
    ranked_kw = ranking_summary.get("ranking_count", 0)
    ranking_score = round((ranked_kw / total_kw) * 100) if total_kw > 0 else 0

    overall = round((tech_score * 0.3 + onpage_score * 0.4 + ranking_score * 0.3))

    return {
        "overall_score": overall,
        "technical_score": tech_score,
        "on_page_score": onpage_score,
        "ranking_score": ranking_score,
        "grade": "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D" if overall >= 40 else "F",
    }
