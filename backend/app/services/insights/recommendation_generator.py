"""
Recommendation generator for AdTicks.
Converts insights into prioritized, actionable recommendations.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Map insight types to recommendation templates
INSIGHT_TO_RECOMMENDATION: Dict[str, Dict[str, Any]] = {
    "high_impressions_low_ctr": {
        "category": "seo",
        "base_priority": 2,
        "action_template": (
            "Rewrite the meta description for your page ranking for '{query}'. "
            "Include the primary keyword, a clear value proposition, and a call-to-action. "
            "Aim for 150-160 characters. Test 2-3 variants using Search Console."
        ),
        "effort": "low",
        "impact": "high",
        "timeframe": "1-2 weeks",
    },
    "ranking_not_in_ai": {
        "category": "ai_visibility",
        "base_priority": 1,
        "action_template": (
            "Restructure your '{keyword}' content for AEO (Answer Engine Optimization): "
            "Add a dedicated FAQ section, use question-based H2/H3 headings, "
            "implement FAQ schema markup, and ensure your brand is clearly named "
            "in your authoritative content. Target 800+ words per topic page."
        ),
        "effort": "medium",
        "impact": "high",
        "timeframe": "2-4 weeks",
    },
    "competitor_dominates_ai": {
        "category": "ai_visibility",
        "base_priority": 1,
        "action_template": (
            "Create a comprehensive comparison page: '{brand} vs {competitor}: Complete Guide'. "
            "Include feature comparison table, pricing comparison, use-case fit, "
            "customer reviews, and migration guide. Target 2000+ words. "
            "Promote via email, social, and outreach to get backlinks."
        ),
        "effort": "high",
        "impact": "very_high",
        "timeframe": "3-6 weeks",
    },
    "traffic_drop_cpc_rise": {
        "category": "cross_channel",
        "base_priority": 2,
        "action_template": (
            "Audit your top organic traffic pages for ranking drops using GSC. "
            "Identify which queries lost impressions and refresh that content. "
            "Simultaneously, reduce paid spend on branded keywords where you should rank organically. "
            "Set target: recover organic traffic to reduce CPC dependency within 60 days."
        ),
        "effort": "high",
        "impact": "high",
        "timeframe": "4-8 weeks",
    },
    "high_intent_not_ranking": {
        "category": "seo",
        "base_priority": 1,
        "action_template": (
            "Create dedicated landing pages for your top {count} high-intent keywords. "
            "Each page should: target a specific transactional/commercial keyword, "
            "include pricing info, social proof, clear CTA, and FAQ section. "
            "Build 3-5 backlinks per page via outreach or guest posts."
        ),
        "effort": "high",
        "impact": "very_high",
        "timeframe": "4-8 weeks",
    },
    "ai_visibility_gap": {
        "category": "ai_visibility",
        "base_priority": 1,
        "action_template": (
            "Launch an AEO content program: publish 10 authoritative Q&A articles "
            "targeting your top prompt categories. Use structured data (FAQ, HowTo, Article schemas). "
            "Get featured in industry roundups and 'best tools' lists. "
            "Ensure your Wikipedia, Crunchbase, and LinkedIn presence is up to date. "
            "Submit your site to AI training data sources where possible."
        ),
        "effort": "high",
        "impact": "very_high",
        "timeframe": "6-12 weeks",
    },
    "content_gap": {
        "category": "content",
        "base_priority": 2,
        "action_template": (
            "Develop a content calendar to address {count} identified topic gaps. "
            "Prioritize by estimated traffic × conversion potential. "
            "Start with: {top_topics}. "
            "Each piece should be 1500+ words, include original data/research where possible, "
            "and target long-tail variations of the main topic."
        ),
        "effort": "high",
        "impact": "high",
        "timeframe": "8-16 weeks",
    },
    "backlink_opportunity": {
        "category": "seo",
        "base_priority": 3,
        "action_template": (
            "Fix {issues_count} technical SEO issues first (see technical audit). "
            "Then build domain authority: identify top 20 industry publications, "
            "pitch guest posts with data-driven articles, "
            "create linkable assets (tools, templates, original research), "
            "and set up a HARO (Help a Reporter Out) profile for media mentions."
        ),
        "effort": "high",
        "impact": "medium",
        "timeframe": "3-6 months",
    },
    "trial_usage_nudge": {
        "category": "product",
        "base_priority": 4,
        "action_template": (
            "Upgrade your AdTicks plan to unlock: unlimited AI scans, "
            "advanced competitor tracking, white-label reports, API access, "
            "and priority support. Schedule a demo to see the full platform."
        ),
        "effort": "none",
        "impact": "platform_value",
        "timeframe": "immediate",
    },
}


def _build_recommendation_text(template: str, supporting_data: Dict[str, Any], brand_name: str = "") -> str:
    """
    Fill a recommendation template with data from the supporting insight.

    Args:
        template: Template string with {placeholders}
        supporting_data: Data dict from the insight
        brand_name: Brand name for substitution

    Returns:
        Formatted recommendation text
    """
    count = supporting_data.get("unranked_high_intent_count", supporting_data.get("gap_count", ""))
    query = supporting_data.get("query", "")
    keyword = supporting_data.get("keyword", "")
    competitor = supporting_data.get("competitor", "Competitor")
    issues_count = supporting_data.get("issues_count", "")
    top_topics = ", ".join(supporting_data.get("top_topics", [])[:3])

    return (template
            .replace("{count}", str(count))
            .replace("{query}", query)
            .replace("{keyword}", keyword)
            .replace("{competitor}", competitor)
            .replace("{brand}", brand_name)
            .replace("{issues_count}", str(issues_count))
            .replace("{top_topics}", top_topics))


def generate_recommendations(
    insights: List[Dict[str, Any]],
    scores: Optional[Dict[str, Any]] = None,
    brand_name: str = "",
) -> List[Dict[str, Any]]:
    """
    Convert insights into prioritized, actionable recommendations.

    Args:
        insights: List of insight dicts from InsightEngine.generate_insights()
        scores: Optional Score dict for additional context
        brand_name: Brand name for recommendation text

    Returns:
        List of Recommendation dicts sorted by priority (1=highest),
        each with: id, project_id, text, priority, category, effort, impact, timeframe, insight_id
    """
    logger.info(f"Generating recommendations from {len(insights)} insights")
    recommendations: List[Dict[str, Any]] = []

    for insight in insights:
        insight_type = insight.get("insight_type", "")
        template_config = INSIGHT_TO_RECOMMENDATION.get(insight_type)

        if not template_config:
            # Generic fallback recommendation
            recommendations.append({
                "id": str(uuid.uuid4()),
                "text": f"Action required: {insight.get('text', '')}",
                "priority": insight.get("priority", 3),
                "category": insight.get("category", "general"),
                "effort": "medium",
                "impact": "medium",
                "timeframe": "2-4 weeks",
                "insight_id": insight.get("id"),
                "insight_type": insight_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            continue

        supporting_data = insight.get("supporting_data", {})
        text = _build_recommendation_text(
            template_config["action_template"],
            supporting_data,
            brand_name,
        )

        # Adjust priority based on score signals
        priority = template_config["base_priority"]
        if scores:
            visibility = scores.get("visibility_score", 0.5)
            if insight_type == "ai_visibility_gap" and visibility < 0.15:
                priority = 1  # Escalate to highest
            elif insight_type == "high_intent_not_ranking" and scores.get("impact_score", 0.5) < 0.20:
                priority = 1

        recommendations.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "priority": priority,
            "category": template_config["category"],
            "effort": template_config["effort"],
            "impact": template_config["impact"],
            "timeframe": template_config["timeframe"],
            "insight_id": insight.get("id"),
            "insight_type": insight_type,
            "supporting_data": supporting_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Sort by priority (ascending = most important first), then by impact
    impact_order = {"very_high": 0, "high": 1, "medium": 2, "low": 3, "platform_value": 4, "none": 5}
    recommendations.sort(key=lambda r: (
        r.get("priority", 5),
        impact_order.get(r.get("impact", "medium"), 2),
    ))

    # Add sequential numbering
    for i, rec in enumerate(recommendations):
        rec["rank"] = i + 1

    logger.info(f"Generated {len(recommendations)} recommendations")
    return recommendations
