"""
AdTicks — Backlink Intelligence Suite.

Capabilities:
    - Anchor text classification + distribution
    - Toxic / spammy backlink detection (heuristic + score)
    - Lost / new backlink tracking
    - Link intersect (domains linking to competitors but not us)
    - Broken backlink builder (linker has 404 → opportunity)
    - Referring domain authority estimate

Provider strategy: a pluggable adapter contract is exposed so paid providers
(Ahrefs, Majestic, Moz Link Explorer) can drop in. The default adapter uses
the existing project Backlinks rows + competitor data already collected.
"""
from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Any
from urllib.parse import urlparse

import httpx

from .serp_analyzer import _da_estimate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Anchor text classification
# ---------------------------------------------------------------------------
def classify_anchor(anchor: str, brand_terms: list[str], target_keywords: list[str]) -> str:
    """Classify an anchor text into one of:
    branded | exact | partial | generic | naked_url | image
    """
    if not anchor:
        return "image"
    a = anchor.lower().strip()
    if re.match(r"^https?://", a) or re.match(r"^www\.", a):
        return "naked_url"
    for brand in brand_terms:
        if brand and brand.lower() in a:
            return "branded"
    for kw in target_keywords:
        if kw and a == kw.lower():
            return "exact"
    for kw in target_keywords:
        if kw and any(w in a for w in kw.lower().split()):
            return "partial"
    generic = {"click here", "read more", "learn more", "this", "here", "link", "website", "site", "visit"}
    if a in generic:
        return "generic"
    return "generic"


def aggregate_anchor_distribution(
    backlinks: list[dict[str, Any]],
    brand_terms: list[str],
    target_keywords: list[str],
) -> list[dict[str, Any]]:
    """Aggregate raw backlink rows into anchor distribution entries."""
    counts: Counter[tuple[str, str]] = Counter()
    domains: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in backlinks:
        anchor = (row.get("anchor_text") or "").strip()
        cls = classify_anchor(anchor, brand_terms, target_keywords)
        ref = row.get("referring_domain") or ""
        key = (anchor[:512] if anchor else f"[{cls}]", cls)
        counts[key] += 1
        if ref:
            domains[key].add(ref)

    rows: list[dict[str, Any]] = []
    for (anchor, cls), count in counts.most_common():
        rows.append({
            "anchor": anchor,
            "classification": cls,
            "count": count,
            "referring_domains": len(domains[(anchor, cls)]),
        })
    return rows


# ---------------------------------------------------------------------------
# Toxic backlink detection
# ---------------------------------------------------------------------------
SPAM_TLDS = {"xyz", "top", "click", "loan", "win", "racing", "stream", "review", "tk", "ml", "ga", "cf", "gq"}
SPAM_KEYWORDS = ["casino", "viagra", "porn", "escort", "loan", "pharm", "betting", "replica", "warez"]


def assess_toxicity(domain: str, anchor: str | None, target_url: str | None) -> tuple[float, list[str]]:
    """Return (spam_score 0-100, reasons)."""
    reasons: list[str] = []
    score = 0.0

    d = domain.lower().strip()
    parsed = urlparse(d if d.startswith("http") else f"http://{d}")
    netloc = parsed.netloc or d

    tld = netloc.rsplit(".", 1)[-1] if "." in netloc else ""
    if tld in SPAM_TLDS:
        score += 35
        reasons.append(f"Domain uses a high-risk TLD (.{tld})")

    sub_count = netloc.count(".")
    if sub_count >= 3:
        score += 10
        reasons.append("Many subdomains")

    if "-" in netloc and netloc.count("-") >= 3:
        score += 12
        reasons.append("Excessive hyphens in domain")

    if any(w in netloc for w in SPAM_KEYWORDS) or (anchor and any(w in anchor.lower() for w in SPAM_KEYWORDS)):
        score += 30
        reasons.append("Domain or anchor contains spam-pattern keyword")

    if len(netloc) > 35:
        score += 8
        reasons.append("Unusually long domain name")

    da = _da_estimate(netloc)
    if da < 15:
        score += 15
        reasons.append("Very low estimated authority")

    return min(100.0, score), reasons


def filter_toxic(
    backlinks: list[dict[str, Any]], min_score: float = 40.0
) -> list[dict[str, Any]]:
    out = []
    for b in backlinks:
        score, reasons = assess_toxicity(
            b.get("referring_domain") or "",
            b.get("anchor_text"),
            b.get("target_url"),
        )
        if score >= min_score:
            out.append({
                "referring_domain": b.get("referring_domain"),
                "target_url": b.get("target_url"),
                "spam_score": round(score, 1),
                "reasons": reasons,
                "disavowed": False,
            })
    return out


# ---------------------------------------------------------------------------
# Link intersect
# ---------------------------------------------------------------------------
def link_intersect(
    project_referring: set[str],
    competitor_referring: dict[str, set[str]],
    min_competitors: int = 2,
) -> list[dict[str, Any]]:
    """Domains linking to >=N competitors but NOT to the project."""
    out: list[dict[str, Any]] = []
    all_competitor_domains: dict[str, list[str]] = defaultdict(list)
    for competitor, domains in competitor_referring.items():
        for d in domains:
            all_competitor_domains[d].append(competitor)
    for domain, competitors in all_competitor_domains.items():
        if domain in project_referring:
            continue
        if len(competitors) < min_competitors:
            continue
        out.append({
            "referring_domain": domain,
            "competitor_count": len(competitors),
            "competitors": competitors,
            "domain_authority": _da_estimate(domain),
        })
    out.sort(key=lambda r: (-r["competitor_count"], -r["domain_authority"]))
    return out


# ---------------------------------------------------------------------------
# Lost / new tracking
# ---------------------------------------------------------------------------
def diff_backlink_sets(
    previous: set[str], current: set[str]
) -> tuple[list[str], list[str]]:
    """Return (new, lost) referring domain lists."""
    new = sorted(current - previous)
    lost = sorted(previous - current)
    return new, lost


# ---------------------------------------------------------------------------
# Broken backlink builder — find linkers whose target is a 404
# ---------------------------------------------------------------------------
async def find_broken_backlinks(
    backlinks: list[dict[str, Any]],
    sample_size: int = 50,
) -> list[dict[str, Any]]:
    """Probe target URLs from the project's backlink set; surface 404 targets
    as outreach opportunities (the linker should redirect or update the link)."""
    sample = [b for b in backlinks if b.get("target_url")][:sample_size]
    out: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        for b in sample:
            try:
                resp = await client.head(b["target_url"])
                if resp.status_code == 404:
                    out.append({
                        "referring_domain": b.get("referring_domain"),
                        "target_url": b["target_url"],
                        "status": 404,
                        "anchor_text": b.get("anchor_text"),
                        "opportunity": "Linker is sending visitors to a dead URL — request a redirect or replacement link",
                    })
            except Exception:
                continue
    return out
