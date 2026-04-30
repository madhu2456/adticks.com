"""
AdTicks — Featured Snippet + PAA tracker + SERP volatility detector.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Featured Snippet detection
# ---------------------------------------------------------------------------
def detect_featured_snippet(serp_data: dict[str, Any], project_domain: str) -> dict[str, Any]:
    """Inspect a SERP payload (from serp_analyzer.analyze_serp) and report
    whether a featured snippet exists, who owns it, and whether it's us."""
    features = serp_data.get("features_present", [])
    has_snippet = "featured_snippet" in features
    if not has_snippet:
        return {"has_snippet": False, "we_own": False, "current_owner_url": None,
                "snippet_text": None, "snippet_type": None}
    # In SerpAPI mode the answer_box would carry the text; in DDG fallback
    # we infer a top-1 ownership.
    results = serp_data.get("results", [])
    if not results:
        return {"has_snippet": True, "we_own": False, "current_owner_url": None,
                "snippet_text": None, "snippet_type": "paragraph"}
    top = results[0]
    owner_url = top.get("url", "")
    domain = urlparse(owner_url).netloc.lower().replace("www.", "")
    pd = project_domain.lower().replace("www.", "")
    return {
        "has_snippet": True,
        "we_own": pd in domain,
        "current_owner_url": owner_url,
        "snippet_text": top.get("snippet"),
        "snippet_type": "paragraph",
    }


def extract_paa_questions(serp_data: dict[str, Any], seed_keyword: str) -> list[dict[str, Any]]:
    """Extract People Also Ask question rows from a SERP payload."""
    questions: list[dict[str, Any]] = []
    if "people_also_ask" not in serp_data.get("features_present", []):
        return questions
    raw_qs = serp_data.get("paa_questions") or []
    for q in raw_qs:
        if isinstance(q, str):
            questions.append({"seed_keyword": seed_keyword, "question": q,
                              "answer_url": None, "answer_snippet": None})
        elif isinstance(q, dict):
            questions.append({
                "seed_keyword": seed_keyword,
                "question": q.get("question") or q.get("title") or "",
                "answer_url": q.get("link"),
                "answer_snippet": q.get("snippet"),
            })
    return questions


# ---------------------------------------------------------------------------
# SERP Volatility — significant rank movement events
# ---------------------------------------------------------------------------
def detect_volatility_events(
    rank_diffs: list[dict[str, Any]],
    drop_threshold: int = 5,
    rise_threshold: int = 5,
    significant_top_position: int = 20,
) -> list[dict[str, Any]]:
    """Given a list of {keyword, previous_position, current_position} dicts,
    surface notable position changes worth alerting on."""
    events: list[dict[str, Any]] = []
    for r in rank_diffs:
        prev = r.get("previous_position")
        curr = r.get("current_position")
        if prev is None and curr is None:
            continue
        # entered top results
        if prev is None and curr is not None and curr <= significant_top_position:
            events.append({
                "keyword": r["keyword"], "previous_position": None,
                "current_position": curr, "delta": -curr, "direction": "up",
            })
            continue
        # dropped out
        if curr is None and prev is not None and prev <= significant_top_position:
            events.append({
                "keyword": r["keyword"], "previous_position": prev,
                "current_position": None, "delta": 100, "direction": "down",
            })
            continue
        if prev is None or curr is None:
            continue
        delta = curr - prev
        if abs(delta) < min(drop_threshold, rise_threshold):
            continue
        # only alert when at least one side is in the meaningful range
        if min(prev, curr) > significant_top_position:
            continue
        events.append({
            "keyword": r["keyword"],
            "previous_position": prev,
            "current_position": curr,
            "delta": delta,
            "direction": "up" if delta < 0 else "down",
        })
    events.sort(key=lambda e: -abs(e["delta"]))
    return events


# ---------------------------------------------------------------------------
# Outreach helpers
# ---------------------------------------------------------------------------
PROSPECT_STATUS_FLOW = ["new", "contacted", "replied", "won", "lost"]


def is_valid_prospect_status(status: str) -> bool:
    return status in PROSPECT_STATUS_FLOW


def progress_status(current: str) -> str | None:
    """Return the next logical status after `current` in the outreach flow."""
    try:
        idx = PROSPECT_STATUS_FLOW.index(current)
    except ValueError:
        return None
    if idx + 1 >= len(PROSPECT_STATUS_FLOW):
        return None
    return PROSPECT_STATUS_FLOW[idx + 1]


def campaign_summary(prospects: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate metrics for an outreach campaign."""
    counts = {s: 0 for s in PROSPECT_STATUS_FLOW}
    for p in prospects:
        s = p.get("status", "new")
        counts[s] = counts.get(s, 0) + 1
    total = len(prospects)
    contacted = counts["contacted"] + counts["replied"] + counts["won"] + counts["lost"]
    reply_rate = (counts["replied"] + counts["won"] + counts["lost"]) / contacted if contacted else 0
    win_rate = counts["won"] / contacted if contacted else 0
    return {
        "total_prospects": total,
        "by_status": counts,
        "contacted": contacted,
        "reply_rate": round(reply_rate, 3),
        "win_rate": round(win_rate, 3),
    }
