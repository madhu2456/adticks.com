"""
AdTicks — Keyword cannibalization detector.

Identifies cases where two or more pages on the same domain rank for the
same query — a common SEO anti-pattern that splits link equity / CTR.

Inputs come from the project's GSC data or the crawl rank rows. The
function returns a list of cannibalization rows ready to persist into
KeywordCannibalization.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def _severity(rank_count: int, top_position: int | None) -> str:
    if rank_count >= 3 and (top_position or 99) <= 20:
        return "high"
    if rank_count >= 2 and (top_position or 99) <= 30:
        return "medium"
    return "low"


def detect_cannibalization(
    rows: Iterable[dict[str, Any]],
    min_pages: int = 2,
) -> list[dict[str, Any]]:
    """Detect cannibalized keywords from a flat list of rank rows.

    `rows` is iterable of dicts with at minimum {keyword, url, position}.
    Optional fields {clicks, impressions} are passed through.
    """
    by_kw: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        kw = (r.get("keyword") or "").strip().lower()
        url = (r.get("url") or "").strip()
        if not kw or not url:
            continue
        by_kw[kw].append(r)

    out: list[dict[str, Any]] = []
    for kw, group in by_kw.items():
        # de-dupe by url, keep best position per url
        url_map: dict[str, dict[str, Any]] = {}
        for r in group:
            existing = url_map.get(r["url"])
            if not existing or (r.get("position") or 999) < (existing.get("position") or 999):
                url_map[r["url"]] = r
        unique = list(url_map.values())
        if len(unique) < min_pages:
            continue

        unique.sort(key=lambda r: r.get("position") or 999)
        top_position = unique[0].get("position")
        sev = _severity(len(unique), top_position)
        recommendation = _recommend(unique)
        out.append({
            "keyword": kw,
            "urls": [
                {
                    "url": r["url"],
                    "position": r.get("position"),
                    "clicks": r.get("clicks", 0),
                    "impressions": r.get("impressions", 0),
                }
                for r in unique[:10]
            ],
            "severity": sev,
            "recommendation": recommendation,
        })
    out.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}[r["severity"]], -len(r["urls"])))
    return out


def _recommend(unique: list[dict[str, Any]]) -> str:
    """Generate a textual recommendation based on the conflict shape."""
    if len(unique) == 2:
        winner = unique[0]
        loser = unique[1]
        return (
            f"Consolidate by 301-redirecting {loser['url']} to {winner['url']}, "
            f"or by adding a canonical from the lower-performing URL."
        )
    return (
        f"You have {len(unique)} pages competing for this query. "
        f"Pick the strongest URL ({unique[0]['url']}) as the canonical target, "
        f"then merge or redirect the rest."
    )
