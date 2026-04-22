"""
Brand mention extractor for AdTicks AI visibility analysis.
Uses regex + NLP heuristics to find and score brand mentions in LLM responses.
"""

import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Confidence boost patterns indicating a strong, contextual mention
STRONG_MENTION_PATTERNS = [
    r"I recommend",
    r"you should (use|try|consider|check out)",
    r"is (the )?best",
    r"is (highly )?recommended",
    r"is (a )?(top|leading|popular|trusted|reputable)",
    r"is known for",
    r"stands out",
    r"outperforms",
    r"is (often |frequently )?praised",
    r"is #1",
    r"is rated",
    r"users love",
    r"worth considering",
    r"great (option|choice|tool|platform)",
]

WEAK_MENTION_PATTERNS = [
    r"(also|additionally|furthermore|moreover|however)",
    r"some (users|people|businesses) (use|choose|prefer)",
    r"another (option|alternative|tool)",
    r"you (may|might|could) (also )?consider",
    r"as well as",
    r"along with",
]

NEGATIVE_PATTERNS = [
    r"avoid",
    r"not recommend",
    r"stay away",
    r"poor (quality|support|performance)",
    r"disappointing",
    r"overpriced",
    r"has (many |several )?issues",
]


def _normalize_brand(brand: str) -> str:
    """Normalize brand name for matching."""
    return brand.strip().lower()


def _build_brand_pattern(brand: str) -> re.Pattern:
    """Build a case-insensitive regex pattern for a brand name."""
    escaped = re.escape(brand.strip())
    # Allow for possessive, plural forms
    return re.compile(
        r'\b' + escaped + r'(?:\'s|s)?\b',
        re.IGNORECASE
    )


def _get_context_around(text: str, match_start: int, match_end: int, window: int = 100) -> str:
    """Extract a context window around a match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    return text[start:end]


def _determine_position(match_start: int, text_length: int) -> str:
    """
    Determine where in the response a mention appears.

    Args:
        match_start: Character index of the mention start
        text_length: Total length of the response text

    Returns:
        'first', 'middle', or 'last'
    """
    third = text_length / 3
    if match_start < third:
        return "first"
    elif match_start < 2 * third:
        return "middle"
    return "last"


def _compute_confidence(
    brand: str,
    context: str,
    is_target: bool,
    match_count_in_response: int,
    position: str,
) -> float:
    """
    Compute a confidence score (0.0-1.0) for a brand mention.

    Args:
        brand: The brand name found
        context: Text surrounding the mention
        is_target: Whether this is the target brand (vs competitor)
        match_count_in_response: How many times this brand appears in total
        position: 'first', 'middle', or 'last'

    Returns:
        Confidence float 0.0-1.0
    """
    base = 0.5
    ctx_lower = context.lower()

    # Strong contextual signals
    for pattern in STRONG_MENTION_PATTERNS:
        if re.search(pattern, ctx_lower, re.IGNORECASE):
            base += 0.2
            break

    # Weak contextual signals
    for pattern in WEAK_MENTION_PATTERNS:
        if re.search(pattern, ctx_lower, re.IGNORECASE):
            base -= 0.1
            break

    # Negative signals
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, ctx_lower, re.IGNORECASE):
            base -= 0.25
            break

    # Position bonus: first mention is most impactful
    position_bonus = {"first": 0.15, "middle": 0.05, "last": 0.0}
    base += position_bonus.get(position, 0)

    # Multiple mentions = higher confidence it's a real recommendation
    if match_count_in_response > 1:
        base += min(match_count_in_response * 0.05, 0.15)

    return max(0.0, min(1.0, round(base, 3)))


def extract_mentions(
    response_text: str,
    target_brand: str,
    competitor_brands: Optional[List[str]] = None,
    response_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract and score brand mentions from an LLM response.

    Args:
        response_text: The full text response from the LLM
        target_brand: The primary brand to track
        competitor_brands: Optional list of competitor brand names
        response_id: Optional response ID for linking

    Returns:
        List of Mention dicts with: id, response_id, brand, position,
        confidence, is_target, context, sentiment, match_index
    """
    if not response_text:
        return []

    competitor_brands = competitor_brands or []
    all_brands = [(target_brand, True)] + [(c, False) for c in competitor_brands]
    mentions: List[Dict[str, Any]] = []
    text_length = len(response_text)

    for brand, is_target in all_brands:
        if not brand.strip():
            continue

        pattern = _build_brand_pattern(brand)
        matches = list(pattern.finditer(response_text))
        match_count = len(matches)

        for i, match in enumerate(matches):
            context = _get_context_around(response_text, match.start(), match.end())
            position = _determine_position(match.start(), text_length)
            confidence = _compute_confidence(
                brand, context, is_target, match_count, position
            )

            # Basic sentiment from context
            ctx_lower = context.lower()
            sentiment = "neutral"
            if any(re.search(p, ctx_lower) for p in STRONG_MENTION_PATTERNS):
                sentiment = "positive"
            if any(re.search(p, ctx_lower) for p in NEGATIVE_PATTERNS):
                sentiment = "negative"

            mentions.append({
                "id": str(uuid.uuid4()),
                "response_id": response_id,
                "brand": brand,
                "is_target_brand": is_target,
                "position": position,
                "match_index": i + 1,
                "total_brand_matches": match_count,
                "confidence": confidence,
                "context": context,
                "sentiment": sentiment,
                "char_offset": match.start(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    logger.debug(
        f"Extracted {len(mentions)} mentions from response ({text_length} chars): "
        f"target={sum(1 for m in mentions if m['is_target_brand'])}, "
        f"competitors={sum(1 for m in mentions if not m['is_target_brand'])}"
    )
    return mentions


def aggregate_mention_stats(
    mentions: List[Dict[str, Any]],
    target_brand: str,
) -> Dict[str, Any]:
    """
    Aggregate mention statistics across multiple responses.

    Args:
        mentions: All mention dicts collected from responses
        target_brand: The target brand name

    Returns:
        Aggregated stats dict
    """
    if not mentions:
        return {
            "total_mentions": 0,
            "target_mentions": 0,
            "competitor_mentions": 0,
            "avg_confidence": 0.0,
            "position_distribution": {},
            "sentiment_distribution": {},
            "competitor_breakdown": {},
        }

    target_m = [m for m in mentions if m.get("is_target_brand")]
    competitor_m = [m for m in mentions if not m.get("is_target_brand")]

    position_dist: Dict[str, int] = {}
    sentiment_dist: Dict[str, int] = {}
    competitor_breakdown: Dict[str, int] = {}

    for m in mentions:
        pos = m.get("position", "unknown")
        position_dist[pos] = position_dist.get(pos, 0) + 1
        sent = m.get("sentiment", "neutral")
        sentiment_dist[sent] = sentiment_dist.get(sent, 0) + 1

    for m in competitor_m:
        brand = m.get("brand", "unknown")
        competitor_breakdown[brand] = competitor_breakdown.get(brand, 0) + 1

    avg_conf = round(sum(m.get("confidence", 0) for m in target_m) / len(target_m), 3) if target_m else 0.0

    return {
        "total_mentions": len(mentions),
        "target_mentions": len(target_m),
        "competitor_mentions": len(competitor_m),
        "avg_confidence": avg_conf,
        "position_distribution": position_dist,
        "sentiment_distribution": sentiment_dist,
        "competitor_breakdown": competitor_breakdown,
    }
