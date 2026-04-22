"""
Insight Engine for AdTicks — the core intelligence layer.
Analyzes cross-channel data (SEO, AI visibility, GSC, Ads) to generate
actionable insights with priority scores and supporting data.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

INDUSTRY_AI_VISIBILITY_BENCHMARKS = {
    "Technology": 0.32,
    "SaaS": 0.28,
    "E-commerce": 0.25,
    "Healthcare": 0.18,
    "Finance": 0.20,
    "Marketing": 0.35,
    "default": 0.25,
}


def _make_insight(
    text: str,
    category: str,
    priority: int,
    supporting_data: Dict[str, Any],
    insight_type: str,
) -> Dict[str, Any]:
    """
    Create a standardized insight dict.

    Args:
        text: Human-readable insight description
        category: Insight category (seo, ai_visibility, ads, analytics, etc.)
        priority: Priority 1-5 (1=highest)
        supporting_data: Dict of metrics that support this insight
        insight_type: Machine-readable type identifier

    Returns:
        Insight dict
    """
    return {
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category,
        "priority": priority,
        "insight_type": insight_type,
        "supporting_data": supporting_data,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


class InsightEngine:
    """
    Core insight generation engine for AdTicks.
    Analyzes SEO, AI visibility, GSC, and Ads data to surface actionable intelligence.
    """

    def __init__(self, brand_name: str = "", industry: str = "Technology"):
        self.brand_name = brand_name
        self.industry = industry
        self.benchmark_visibility = INDUSTRY_AI_VISIBILITY_BENCHMARKS.get(
            industry, INDUSTRY_AI_VISIBILITY_BENCHMARKS["default"]
        )

    def _insight_high_impressions_low_ctr(
        self,
        gsc_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 1: High impressions, low CTR — optimize meta description.
        Fires for queries where impressions > 1000 and CTR < 2%.
        """
        insights = []
        queries = gsc_data.get("queries", [])

        for query in queries:
            impressions = query.get("impressions", 0)
            ctr = query.get("ctr", 0)
            ctr_pct = query.get("ctr_pct", ctr * 100)
            position = query.get("position", 99)

            if impressions >= 1000 and ctr < 0.02 and position <= 20:
                text = (
                    f"You're getting {impressions:,} impressions for '{query['query']}' "
                    f"but only {ctr_pct:.1f}% CTR. Optimizing your meta description "
                    f"could unlock significant traffic."
                )
                insights.append(_make_insight(
                    text=text,
                    category="seo",
                    priority=2,
                    supporting_data={
                        "query": query["query"],
                        "impressions": impressions,
                        "ctr_pct": ctr_pct,
                        "position": position,
                        "potential_clicks_at_5pct_ctr": int(impressions * 0.05),
                    },
                    insight_type="high_impressions_low_ctr",
                ))
        return insights[:3]  # Cap at 3 per rule

    def _insight_ranking_but_missing_in_ai(
        self,
        seo_data: Dict[str, Any],
        ai_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 2: Ranking on Google but not mentioned in AI responses.
        Fires when keyword is in top 30 but brand visibility for that category is 0.
        """
        insights = []
        rankings = seo_data.get("rank_tracking", {}).get("rankings", [])
        prompt_results = ai_data.get("prompt_results", [])

        # Find categories where brand isn't mentioned
        zero_visibility_categories = set()
        for pr in prompt_results:
            if not pr.get("mentioned") and pr.get("prompt", {}).get("category"):
                zero_visibility_categories.add(pr["prompt"]["category"])

        for ranking in rankings:
            position = ranking.get("position")
            keyword = ranking.get("keyword", "")
            if position and position <= 30 and zero_visibility_categories:
                text = (
                    f"You rank #{position} on Google for '{keyword}' but aren't mentioned "
                    f"in AI responses for related prompts. Optimize your content for AEO "
                    f"(Answer Engine Optimization) to capture AI visibility."
                )
                insights.append(_make_insight(
                    text=text,
                    category="ai_visibility",
                    priority=1,
                    supporting_data={
                        "keyword": keyword,
                        "google_position": position,
                        "ai_visibility": 0,
                        "opportunity": "Add authoritative, question-answer formatted content",
                        "zero_visibility_categories": list(zero_visibility_categories)[:3],
                    },
                    insight_type="ranking_not_in_ai",
                ))
        return insights[:3]

    def _insight_competitor_dominates_ai(
        self,
        ai_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 3: Competitor dominates AI comparison prompts.
        Fires when a competitor appears in >40% of comparison prompts vs brand's <20%.
        """
        insights = []
        prompt_results = ai_data.get("prompt_results", [])

        comparison_results = [
            pr for pr in prompt_results
            if pr.get("prompt", {}).get("category") == "comparison"
        ]
        if not comparison_results:
            return []

        total_comparison = len(comparison_results)

        # Count competitor vs brand appearances in comparison prompts
        competitor_counts: Dict[str, int] = {}
        brand_count = 0

        for pr in comparison_results:
            all_mentions = pr.get("all_mentions", [])
            for m in all_mentions:
                brand = m.get("brand", "")
                if m.get("is_target_brand"):
                    brand_count += 1
                else:
                    competitor_counts[brand] = competitor_counts.get(brand, 0) + 1

        brand_pct = round(brand_count / total_comparison * 100, 1) if total_comparison > 0 else 0

        for comp, count in competitor_counts.items():
            comp_pct = round(count / total_comparison * 100, 1)
            if comp_pct >= 40 and brand_pct < 25:
                text = (
                    f"'{comp}' appears in {comp_pct}% of comparison prompts while you appear "
                    f"in only {brand_pct}%. Create direct comparison content like "
                    f"'{self.brand_name} vs {comp}: A Complete Guide' to recapture this traffic."
                )
                insights.append(_make_insight(
                    text=text,
                    category="ai_visibility",
                    priority=1,
                    supporting_data={
                        "competitor": comp,
                        "competitor_pct": comp_pct,
                        "brand_pct": brand_pct,
                        "total_comparison_prompts": total_comparison,
                        "action": f"Create '{self.brand_name} vs {comp}' comparison page",
                    },
                    insight_type="competitor_dominates_ai",
                ))
        return insights[:2]

    def _insight_traffic_drop_vs_cpc_rise(
        self,
        analytics_data: Dict[str, Any],
        ads_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 4: Traffic drop correlated with CPC increase.
        Fires when sessions drop >10% while CPC increases >15%.
        """
        insights = []
        sessions_change = analytics_data.get("period_comparison", {}).get("sessions_change_pct", 0)
        spend_change = ads_data.get("period_comparison", {}).get("spend_change_pct", 0)
        avg_cpc = ads_data.get("summary", {}).get("avg_cpc_usd", 0)

        if sessions_change < -10 and spend_change > 10:
            text = (
                f"Sessions dropped {abs(sessions_change):.1f}% this month while ad spend "
                f"increased {spend_change:.1f}% (avg CPC: ${avg_cpc:.2f}). "
                f"Organic visibility loss may be pushing costs higher. "
                f"Invest in organic content to reduce paid dependency."
            )
            insights.append(_make_insight(
                text=text,
                category="cross_channel",
                priority=2,
                supporting_data={
                    "sessions_change_pct": sessions_change,
                    "spend_change_pct": spend_change,
                    "avg_cpc_usd": avg_cpc,
                    "correlation": "organic_loss_drives_paid_cost",
                },
                insight_type="traffic_drop_cpc_rise",
            ))
        return insights

    def _insight_high_intent_not_ranking(
        self,
        seo_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 5: High-intent keywords not ranking.
        Fires when transactional/commercial keywords have no position.
        """
        insights = []
        keywords = seo_data.get("keyword_discovery", {}).get("keywords", [])
        rankings = {r.get("keyword", ""): r.get("position") for r in seo_data.get("rank_tracking", {}).get("rankings", [])}

        high_intent_not_ranking = [
            kw for kw in keywords
            if kw.get("intent") in ("transactional", "commercial")
            and (rankings.get(kw.get("keyword", "")) is None)
        ]

        if len(high_intent_not_ranking) >= 5:
            top_kws = [kw["keyword"] for kw in high_intent_not_ranking[:3]]
            text = (
                f"You're not ranking for {len(high_intent_not_ranking)} high-intent keywords "
                f"in your industry (e.g., {', '.join(top_kws)}). "
                f"These represent your highest conversion opportunities — "
                f"create dedicated landing pages targeting each."
            )
            insights.append(_make_insight(
                text=text,
                category="seo",
                priority=1,
                supporting_data={
                    "unranked_high_intent_count": len(high_intent_not_ranking),
                    "top_opportunities": high_intent_not_ranking[:5],
                    "estimated_monthly_traffic": sum(kw.get("volume", 0) for kw in high_intent_not_ranking[:10]),
                },
                insight_type="high_intent_not_ranking",
            ))
        return insights

    def _insight_ai_visibility_gap(
        self,
        ai_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 6: Brand's AI visibility significantly below industry benchmark.
        Fires when visibility < 70% of industry average.
        """
        insights = []
        score = ai_data.get("score", {})
        visibility = score.get("visibility_score", 0)
        visibility_pct = round(visibility * 100, 1)
        benchmark_pct = round(self.benchmark_visibility * 100, 1)

        if visibility < self.benchmark_visibility * 0.70:
            text = (
                f"Your brand appears in only {visibility_pct}% of AI responses vs "
                f"{benchmark_pct}% industry average for {self.industry}. "
                f"AI optimization is critical for {self.brand_name} — "
                f"structure your content with clear Q&A format, add FAQ schemas, "
                f"and build authoritative backlinks."
            )
            insights.append(_make_insight(
                text=text,
                category="ai_visibility",
                priority=1,
                supporting_data={
                    "brand_visibility_pct": visibility_pct,
                    "industry_benchmark_pct": benchmark_pct,
                    "gap_pct": round(benchmark_pct - visibility_pct, 1),
                    "industry": self.industry,
                    "prompts_analyzed": score.get("prompts_analyzed", 0),
                },
                insight_type="ai_visibility_gap",
            ))
        return insights

    def _insight_content_gap(
        self,
        seo_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 7: Competitor content gaps identified.
        Fires when content gaps have high estimated traffic.
        """
        insights = []
        gaps = seo_data.get("content_gaps", [])

        if not gaps:
            return []

        high_value_gaps = sorted(gaps, key=lambda g: g.get("estimated_monthly_traffic", 0), reverse=True)[:5]
        if high_value_gaps:
            total_traffic = sum(g.get("estimated_monthly_traffic", 0) for g in high_value_gaps)
            topics = [g["topic"] for g in high_value_gaps[:3]]
            text = (
                f"Competitors rank for topics you don't cover: {', '.join(topics)}. "
                f"Creating content on these could capture ~{total_traffic:,} additional monthly visits."
            )
            insights.append(_make_insight(
                text=text,
                category="content",
                priority=2,
                supporting_data={
                    "gap_count": len(gaps),
                    "top_gaps": high_value_gaps[:5],
                    "total_estimated_traffic": total_traffic,
                    "top_topics": topics,
                },
                insight_type="content_gap",
            ))
        return insights

    def _insight_backlink_opportunity(
        self,
        seo_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Rule 8: Domain authority / backlink opportunity.
        Always fires as a structural SEO recommendation.
        """
        technical = seo_data.get("technical_seo", {})
        health_score = technical.get("health_score", 50)

        if health_score < 70:
            text = (
                f"Your technical SEO health score is {health_score}/100, below the recommended threshold. "
                f"Your domain authority is likely lower than competitors. "
                f"Focus on acquiring links from industry publications, "
                f"guest posts, and fixing the {technical.get('issues_count', 0)} technical issues identified."
            )
            return [_make_insight(
                text=text,
                category="seo",
                priority=3,
                supporting_data={
                    "technical_health_score": health_score,
                    "issues_count": technical.get("issues_count", 0),
                    "top_issues": technical.get("issues", [])[:3],
                },
                insight_type="backlink_opportunity",
            )]
        return []

    def _insight_trial_usage_nudge(
        self,
        ai_data: Dict[str, Any],
        max_free_scans: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Rule 9: Trial usage nudge when user is nearing scan limit.
        Fires when scan count is 60-90% of free limit.
        """
        score = ai_data.get("score", {})
        scan_count = score.get("scan_count", 0)
        if scan_count is None:
            return []

        usage_pct = scan_count / max_free_scans
        if 0.60 <= usage_pct <= 0.95:
            text = (
                f"You've used {scan_count} of your {max_free_scans} free AI scans. "
                f"Upgrade to run unlimited scans, track more keywords, "
                f"and access advanced competitor intelligence."
            )
            return [_make_insight(
                text=text,
                category="product",
                priority=4,
                supporting_data={
                    "scans_used": scan_count,
                    "scans_limit": max_free_scans,
                    "usage_pct": round(usage_pct * 100, 1),
                    "scans_remaining": max_free_scans - scan_count,
                },
                insight_type="trial_usage_nudge",
            )]
        return []

    def generate_insights(
        self,
        project_id: str,
        seo_data: Optional[Dict[str, Any]] = None,
        ai_data: Optional[Dict[str, Any]] = None,
        gsc_data: Optional[Dict[str, Any]] = None,
        ads_data: Optional[Dict[str, Any]] = None,
        analytics_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate all insights from cross-channel data.

        Args:
            project_id: Project identifier
            seo_data: Full SEO audit result dict
            ai_data: AI visibility scan result dict
            gsc_data: GSC sync result dict
            ads_data: Ads performance result dict
            analytics_data: Analytics overview dict

        Returns:
            List of Insight dicts sorted by priority (1=highest)
        """
        logger.info(f"[{project_id}] Generating insights for brand={self.brand_name}")
        insights: List[Dict[str, Any]] = []

        seo_data = seo_data or {}
        ai_data = ai_data or {}
        gsc_data = gsc_data or {}
        ads_data = ads_data or {}
        analytics_data = analytics_data or {}

        # Rule 1: High impressions, low CTR (needs GSC)
        if gsc_data:
            try:
                insights.extend(self._insight_high_impressions_low_ctr(gsc_data))
            except Exception as e:
                logger.error(f"Rule 1 failed: {e}")

        # Rule 2: Ranking but missing in AI (needs SEO + AI)
        if seo_data and ai_data:
            try:
                insights.extend(self._insight_ranking_but_missing_in_ai(seo_data, ai_data))
            except Exception as e:
                logger.error(f"Rule 2 failed: {e}")

        # Rule 3: Competitor dominates AI (needs AI)
        if ai_data:
            try:
                insights.extend(self._insight_competitor_dominates_ai(ai_data))
            except Exception as e:
                logger.error(f"Rule 3 failed: {e}")

        # Rule 4: Traffic drop + CPC rise (needs analytics + ads)
        if analytics_data and ads_data:
            try:
                insights.extend(self._insight_traffic_drop_vs_cpc_rise(analytics_data, ads_data))
            except Exception as e:
                logger.error(f"Rule 4 failed: {e}")

        # Rule 5: High intent keywords not ranking (needs SEO)
        if seo_data:
            try:
                insights.extend(self._insight_high_intent_not_ranking(seo_data))
            except Exception as e:
                logger.error(f"Rule 5 failed: {e}")

        # Rule 6: AI visibility gap (needs AI)
        if ai_data:
            try:
                insights.extend(self._insight_ai_visibility_gap(ai_data))
            except Exception as e:
                logger.error(f"Rule 6 failed: {e}")

        # Rule 7: Content gap (needs SEO with gap data)
        if seo_data:
            try:
                insights.extend(self._insight_content_gap(seo_data))
            except Exception as e:
                logger.error(f"Rule 7 failed: {e}")

        # Rule 8: Backlink opportunity (needs SEO)
        if seo_data:
            try:
                insights.extend(self._insight_backlink_opportunity(seo_data))
            except Exception as e:
                logger.error(f"Rule 8 failed: {e}")

        # Rule 9: Trial usage nudge (needs AI with scan count)
        if ai_data:
            try:
                insights.extend(self._insight_trial_usage_nudge(ai_data))
            except Exception as e:
                logger.error(f"Rule 9 failed: {e}")

        # Sort by priority (1=most urgent)
        insights.sort(key=lambda x: (x.get("priority", 5), x.get("generated_at", "")))

        # Add sequential numbering
        for i, insight in enumerate(insights):
            insight["rank"] = i + 1

        logger.info(f"[{project_id}] Generated {len(insights)} insights")
        return insights
