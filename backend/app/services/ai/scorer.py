"""
AI visibility scorer for AdTicks.
Computes visibility, share-of-voice, and impact scores from prompt results.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Intent weights for impact score calculation
INTENT_WEIGHTS = {
    "transactional": 1.5,
    "commercial": 1.3,
    "comparison": 1.2,
    "informational": 1.0,
    "navigational": 0.8,
    "brand_awareness": 1.0,
    "recommendations": 1.3,
    "trust_signals": 1.1,
    "problem_solving": 1.2,
}

# Industry average AI visibility benchmarks
INDUSTRY_BENCHMARKS = {
    "Technology": 0.32,
    "SaaS": 0.28,
    "E-commerce": 0.25,
    "Healthcare": 0.18,
    "Finance": 0.20,
    "Marketing": 0.35,
    "default": 0.25,
}


def _get_intent_weight(category: str, intent: Optional[str] = None) -> float:
    """
    Get the intent weight for a prompt category.

    Args:
        category: Prompt category string
        intent: Optional keyword intent string

    Returns:
        Float weight multiplier
    """
    # Prefer explicit intent if provided
    if intent and intent.lower() in INTENT_WEIGHTS:
        return INTENT_WEIGHTS[intent.lower()]
    cat = (category or "informational").lower()
    return INTENT_WEIGHTS.get(cat, 1.0)


def _estimate_traffic_proxy(prompt: Dict[str, Any]) -> float:
    """
    Estimate a traffic proxy score for a prompt based on its category and metadata.
    Higher = more valuable prompt to be mentioned in.

    Args:
        prompt: Prompt dict with category and optional volume fields

    Returns:
        Float 0.1 - 1.0 traffic proxy
    """
    category = (prompt.get("category") or "informational").lower()
    volume = prompt.get("volume", 500)

    # Normalize volume to 0-1 scale (cap at 10000)
    volume_score = min(volume / 10000, 1.0) if volume else 0.1

    category_proxy = {
        "comparison": 0.9,
        "recommendations": 0.85,
        "transactional": 0.95,
        "commercial": 0.8,
        "trust_signals": 0.75,
        "problem_solving": 0.7,
        "brand_awareness": 0.6,
        "informational": 0.5,
    }
    base_proxy = category_proxy.get(category, 0.5)

    # Blend category proxy with volume score
    return round(base_proxy * 0.7 + volume_score * 0.3, 3)


def compute_visibility_score(
    project_id: str,
    prompt_results: List[Dict[str, Any]],
    target_brand: str,
    industry: str = "Technology",
    scan_count: Optional[int] = None,
    max_free_scans: int = 50,
) -> Dict[str, Any]:
    """
    Compute AI visibility, share-of-voice (SoV), and impact scores.

    Args:
        project_id: Project identifier
        prompt_results: List of dicts, each containing:
            - prompt: dict with 'id', 'text', 'category'
            - mentions: list of mention dicts
            - all_mentions: list of all brand mentions (target + competitor) in the response
        target_brand: Brand name to compute scores for
        industry: Industry for benchmark comparison
        scan_count: Current number of AI scans used (for nudge insight)
        max_free_scans: Maximum free scan limit

    Returns:
        Score dict with: project_id, visibility_score, impact_score, sov_score,
        mention_rate, benchmark_comparison, timestamp, and per-category breakdown
    """
    logger.info(f"Computing visibility scores for project={project_id} brand={target_brand} prompts={len(prompt_results)}")

    if not prompt_results:
        logger.warning("No prompt results to score")
        return {
            "project_id": project_id,
            "visibility_score": 0.0,
            "impact_score": 0.0,
            "sov_score": 0.0,
            "mention_rate": 0.0,
            "scan_count": scan_count,
            "max_free_scans": max_free_scans,
            "scans_remaining": max(0, max_free_scans - (scan_count or 0)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    total_prompts = len(prompt_results)
    brand_lower = target_brand.lower()

    # Per-prompt analysis
    prompts_with_mention = 0
    total_target_mentions = 0
    total_all_mentions = 0
    weighted_impact_sum = 0.0
    category_stats: Dict[str, Dict[str, Any]] = {}

    for result in prompt_results:
        prompt = result.get("prompt", {})
        mentions = result.get("mentions", [])
        all_mentions = result.get("all_mentions", mentions)  # All brand mentions including competitors

        category = prompt.get("category", "informational")
        intent_weight = _get_intent_weight(category, prompt.get("intent"))
        traffic_proxy = _estimate_traffic_proxy(prompt)

        # Count target brand mentions in this response
        target_mentions_here = [
            m for m in mentions
            if m.get("is_target_brand", False) or brand_lower in m.get("brand", "").lower()
        ]
        all_mentions_here = all_mentions

        has_target_mention = len(target_mentions_here) > 0

        if has_target_mention:
            prompts_with_mention += 1
            total_target_mentions += len(target_mentions_here)

            # Average confidence of target mentions
            avg_conf = sum(m.get("confidence", 0.5) for m in target_mentions_here) / len(target_mentions_here)

            # Impact contribution: visibility_binary × intent_weight × traffic_proxy × confidence
            impact_contribution = 1.0 * intent_weight * traffic_proxy * avg_conf
            weighted_impact_sum += impact_contribution

        total_all_mentions += len(all_mentions_here)

        # Per-category tracking
        if category not in category_stats:
            category_stats[category] = {
                "total_prompts": 0,
                "prompts_with_mention": 0,
                "visibility_rate": 0.0,
            }
        category_stats[category]["total_prompts"] += 1
        if has_target_mention:
            category_stats[category]["prompts_with_mention"] += 1

    # Core metrics
    visibility_score = prompts_with_mention / total_prompts  # 0-1
    sov_score = total_target_mentions / total_all_mentions if total_all_mentions > 0 else 0.0
    # Impact normalized by max possible (all prompts weighted)
    max_possible_impact = sum(
        _get_intent_weight(r.get("prompt", {}).get("category", "informational")) *
        _estimate_traffic_proxy(r.get("prompt", {}))
        for r in prompt_results
    )
    impact_score = (weighted_impact_sum / max_possible_impact) if max_possible_impact > 0 else 0.0

    # Category breakdown
    for cat, stats in category_stats.items():
        t = stats["total_prompts"]
        m = stats["prompts_with_mention"]
        stats["visibility_rate"] = round(m / t, 3) if t > 0 else 0.0

    # Benchmark comparison
    benchmark = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["default"])
    vs_benchmark = round(visibility_score - benchmark, 3)
    benchmark_status = "above" if vs_benchmark > 0 else "below" if vs_benchmark < 0 else "at"

    score = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "visibility_score": round(visibility_score, 4),
        "impact_score": round(impact_score, 4),
        "sov_score": round(sov_score, 4),
        "mention_rate": round(visibility_score * 100, 2),  # As percentage
        "prompts_analyzed": total_prompts,
        "prompts_with_mention": prompts_with_mention,
        "total_target_mentions": total_target_mentions,
        "total_all_mentions": total_all_mentions,
        "industry_benchmark": benchmark,
        "vs_benchmark": vs_benchmark,
        "benchmark_status": benchmark_status,
        "category_breakdown": category_stats,
        "scan_count": scan_count,
        "max_free_scans": max_free_scans,
        "scans_remaining": max(0, max_free_scans - (scan_count or 0)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Scores computed: visibility={visibility_score:.3f} "
        f"sov={sov_score:.3f} impact={impact_score:.3f} "
        f"vs_benchmark={vs_benchmark:+.3f}"
    )
    return score
