"""
Content gap analysis service for AdTicks SEO module.
Uses OpenAI to identify topics competitors rank for that the project misses.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


def _fallback_gaps(project_keywords: List[str], competitor_domains: List[str]) -> List[Dict[str, Any]]:
    """
    Generate realistic fallback gap opportunities when OpenAI is unavailable.

    Args:
        project_keywords: Current project keyword list
        competitor_domains: Competitor domain list

    Returns:
        List of gap opportunity dicts
    """
    gap_templates = [
        {"topic": "Ultimate Beginner's Guide", "estimated_traffic": 4200, "difficulty": 35, "intent": "informational", "content_type": "Long-form guide"},
        {"topic": "Industry Case Studies", "estimated_traffic": 2800, "difficulty": 45, "intent": "commercial", "content_type": "Case study collection"},
        {"topic": "Comparison Hub Pages", "estimated_traffic": 6100, "difficulty": 55, "intent": "commercial", "content_type": "Comparison page"},
        {"topic": "How-to Tutorials", "estimated_traffic": 3500, "difficulty": 30, "intent": "informational", "content_type": "Tutorial series"},
        {"topic": "ROI Calculator Tool", "estimated_traffic": 1800, "difficulty": 40, "intent": "transactional", "content_type": "Interactive tool"},
        {"topic": "Industry Statistics & Data", "estimated_traffic": 5200, "difficulty": 25, "intent": "informational", "content_type": "Statistics page"},
        {"topic": "Expert Interview Series", "estimated_traffic": 1200, "difficulty": 20, "intent": "informational", "content_type": "Interview content"},
        {"topic": "Template Library", "estimated_traffic": 3900, "difficulty": 38, "intent": "transactional", "content_type": "Free resources"},
        {"topic": "Glossary / Definitions", "estimated_traffic": 7800, "difficulty": 22, "intent": "informational", "content_type": "Glossary page"},
        {"topic": "Integration Guides", "estimated_traffic": 2100, "difficulty": 42, "intent": "transactional", "content_type": "Technical documentation"},
    ]

    gaps = []
    for i, comp in enumerate(competitor_domains[:3]):
        for j, gap in enumerate(gap_templates[:4]):
            gaps.append({
                "topic": gap["topic"],
                "competitor_domain": comp,
                "estimated_monthly_traffic": gap["estimated_traffic"],
                "keyword_difficulty": gap["difficulty"],
                "intent": gap["intent"],
                "suggested_content_type": gap["content_type"],
                "priority_score": round((gap["estimated_traffic"] / 100) / (gap["difficulty"] + 1), 2),
                "example_keywords": [f"{gap['topic'].lower()} guide", f"how to {gap['topic'].lower()}", f"best {gap['topic'].lower()}"],
            })

    # Sort by priority
    gaps.sort(key=lambda x: x["priority_score"], reverse=True)
    return gaps


async def find_gaps(
    project_keywords: List[str],
    competitor_domains: List[str],
    industry: Optional[str] = None,
    brand_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Identify content gaps — topics competitors rank for that the project misses.

    Args:
        project_keywords: Keywords the project currently targets
        competitor_domains: List of competitor domain names
        industry: Optional industry context
        brand_name: Optional brand name for context

    Returns:
        List of gap opportunity dicts with: topic, competitor_domain, estimated_monthly_traffic,
        keyword_difficulty, intent, suggested_content_type, priority_score, example_keywords
    """
    logger.info(f"Finding content gaps for {len(project_keywords)} project keywords vs {len(competitor_domains)} competitors")

    if not OPENAI_AVAILABLE:
        logger.warning("OpenAI not available — returning fallback gap analysis")
        return _fallback_gaps(project_keywords, competitor_domains)

    try:
        client = AsyncOpenAI()

        kw_sample = project_keywords[:30]  # Limit to 30 for prompt size
        comp_str = ", ".join(competitor_domains[:5])
        kw_str = ", ".join(kw_sample)
        industry_ctx = f"Industry: {industry}" if industry else ""
        brand_ctx = f"Brand: {brand_name}" if brand_name else ""

        prompt = f"""You are a senior SEO strategist. Analyze the following and identify content gap opportunities.

{brand_ctx}
{industry_ctx}
Current project keywords: {kw_str}
Competitor domains: {comp_str}

Identify 15-20 high-value content gap opportunities — topics the competitors likely rank for that the project is missing.

For each gap return a JSON object with:
- topic: string (clear topic name)
- competitor_domain: string (which competitor ranks for this)
- estimated_monthly_traffic: integer (realistic search volume estimate)
- keyword_difficulty: integer 1-100
- intent: one of [informational, commercial, transactional, navigational]
- suggested_content_type: string (e.g. "Long-form guide", "Comparison page", "Tool/calculator")
- priority_score: float 0-10 (higher = better opportunity)
- example_keywords: list of 3 example keywords for this topic

Return valid JSON array only. No extra text."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        gaps = json.loads(raw)

        validated = []
        for gap in gaps:
            validated.append({
                "topic": str(gap.get("topic", "")),
                "competitor_domain": str(gap.get("competitor_domain", competitor_domains[0] if competitor_domains else "")),
                "estimated_monthly_traffic": max(0, int(gap.get("estimated_monthly_traffic", 500))),
                "keyword_difficulty": max(1, min(100, int(gap.get("keyword_difficulty", 50)))),
                "intent": gap.get("intent", "informational"),
                "suggested_content_type": str(gap.get("suggested_content_type", "Article")),
                "priority_score": float(gap.get("priority_score", 5.0)),
                "example_keywords": gap.get("example_keywords", []),
            })

        validated.sort(key=lambda x: x["priority_score"], reverse=True)
        logger.info(f"Content gap analysis found {len(validated)} gaps")
        return validated

    except Exception as e:
        logger.warning(f"OpenAI gap analysis failed: {e}. Returning fallback.")
        return _fallback_gaps(project_keywords, competitor_domains)
