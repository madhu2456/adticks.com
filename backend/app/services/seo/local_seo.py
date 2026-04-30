"""
AdTicks — Local SEO suite.

Capabilities:
    - NAP (Name, Address, Phone) consistency checking across citations
    - Citation tracking with directory list
    - Local rank grid (SoLV/SoLO style heatmap snapshots)
    - Review-summary aggregator hook (uses existing GEO models when available)
"""
from __future__ import annotations

import logging
import re
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Top citation directories to track
DIRECTORIES = [
    "Google Business Profile", "Bing Places", "Apple Maps", "Yelp", "Facebook",
    "TripAdvisor", "Yellow Pages", "Foursquare", "Better Business Bureau",
    "Angi", "Houzz", "Manta", "MapQuest", "Superpages", "Citysearch",
    "Local.com", "Hotfrog", "MerchantCircle", "ChamberofCommerce.com", "Kudzu",
]


@dataclass
class CanonicalNAP:
    name: str
    address: str
    phone: str
    website: str | None = None


def _normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def _normalize_address(address: str) -> str:
    a = (address or "").lower()
    a = re.sub(r"\b(street|st\.?|road|rd\.?|avenue|ave\.?|boulevard|blvd\.?|drive|dr\.?|suite|ste\.?)\b", "", a)
    a = re.sub(r"[^\w\s]", " ", a)
    return re.sub(r"\s+", " ", a).strip()


def _normalize_name(name: str) -> str:
    n = (name or "").lower()
    n = re.sub(r"\b(llc|inc|corp|co|ltd|incorporated)\b", "", n)
    n = re.sub(r"[^\w\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def check_consistency(citation: dict[str, Any], canonical: CanonicalNAP) -> tuple[int, list[str]]:
    """Compare a single citation's fields to canonical NAP. Return (score, issues)."""
    issues: list[str] = []
    name_match = _normalize_name(citation.get("business_name", "")) == _normalize_name(canonical.name)
    if not name_match:
        issues.append("Business name differs from canonical NAP")
    addr_match = _normalize_address(citation.get("address", "")) == _normalize_address(canonical.address)
    if not addr_match:
        issues.append("Address differs from canonical NAP")
    phone_match = _normalize_phone(citation.get("phone", "")) == _normalize_phone(canonical.phone)
    if not phone_match:
        issues.append("Phone differs from canonical NAP")
    if canonical.website and citation.get("website"):
        site_match = re.sub(r"https?://(www\.)?", "", canonical.website.lower()) == re.sub(
            r"https?://(www\.)?", "", citation["website"].lower()
        )
        if not site_match:
            issues.append("Website differs from canonical NAP")
    score = 100 - len(issues) * 25
    return max(0, score), issues


def aggregate_consistency(citations: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute project-level NAP consistency metrics."""
    if not citations:
        return {"score": 0, "directories_listed": 0, "directories_total": len(DIRECTORIES), "issues_count": 0}
    avg = sum(c.get("consistency_score", 100) for c in citations) / len(citations)
    issues = sum(len(c.get("issues") or []) for c in citations)
    listed = len({c.get("directory") for c in citations})
    return {
        "score": int(round(avg)),
        "directories_listed": listed,
        "directories_total": len(DIRECTORIES),
        "directories_missing": [d for d in DIRECTORIES if d not in {c.get("directory") for c in citations}],
        "issues_count": issues,
    }


def generate_grid_points(
    center_lat: float,
    center_lng: float,
    radius_km: float = 5.0,
    grid_size: int = 5,
) -> list[tuple[float, float]]:
    """Generate a grid_size x grid_size list of (lat, lng) points around center."""
    # ~111 km per degree latitude
    deg_per_km_lat = 1 / 111.0
    import math
    deg_per_km_lng = 1 / (111.0 * max(0.1, math.cos(math.radians(center_lat))))
    half = (grid_size - 1) / 2
    points: list[tuple[float, float]] = []
    for i in range(grid_size):
        for j in range(grid_size):
            d_lat = (i - half) * (radius_km / half) * deg_per_km_lat if half else 0
            d_lng = (j - half) * (radius_km / half) * deg_per_km_lng if half else 0
            points.append((center_lat + d_lat, center_lng + d_lng))
    return points


def grid_visibility_score(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute Share of Local Voice (SoLV) style metrics from a grid run."""
    if not cells:
        return {"avg_rank": None, "top3_pct": 0, "top10_pct": 0, "not_ranked_pct": 100}
    ranked = [c for c in cells if c.get("rank") is not None]
    top3 = sum(1 for c in ranked if c["rank"] <= 3)
    top10 = sum(1 for c in ranked if c["rank"] <= 10)
    not_ranked = len(cells) - len(ranked)
    return {
        "avg_rank": (sum(c["rank"] for c in ranked) / len(ranked)) if ranked else None,
        "top3_pct": round(top3 / len(cells) * 100, 1),
        "top10_pct": round(top10 / len(cells) * 100, 1),
        "not_ranked_pct": round(not_ranked / len(cells) * 100, 1),
    }
