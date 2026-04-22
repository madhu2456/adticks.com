"""
Analytics service for AdTicks.
Provides realistic mock web analytics data: sessions, users, funnel, and engagement metrics.
"""

import logging
import random
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

TRAFFIC_SOURCES = [
    ("Organic Search", 0.38),
    ("Direct", 0.22),
    ("Paid Search", 0.18),
    ("Referral", 0.10),
    ("Social", 0.07),
    ("Email", 0.05),
]

TOP_PAGES = [
    ("/", "Home"),
    ("/pricing", "Pricing"),
    ("/features", "Features"),
    ("/blog", "Blog"),
    ("/about", "About"),
    ("/contact", "Contact"),
    ("/demo", "Request Demo"),
    ("/login", "Login"),
    ("/signup", "Sign Up"),
    ("/docs", "Documentation"),
]

DEVICES = [("desktop", 0.58), ("mobile", 0.34), ("tablet", 0.08)]
COUNTRIES = [("United States", 0.45), ("United Kingdom", 0.12), ("Canada", 0.08),
             ("Australia", 0.06), ("Germany", 0.05), ("France", 0.04), ("Other", 0.20)]


def _weighted_choice(options: List[tuple]) -> str:
    """Pick a weighted random choice from (value, weight) tuples."""
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


async def get_overview(
    project_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get analytics overview metrics for a project (realistic mock).

    Args:
        project_id: Project identifier
        days: Reporting period in days

    Returns:
        Dict with sessions, users, bounce_rate, avg_session_duration,
        pages_per_session, traffic sources, top pages, device breakdown, country breakdown
    """
    logger.info(f"[{project_id}] Fetching analytics overview for {days} days")

    # Base metrics with realistic variation
    sessions = int(random.gauss(12000, 3000))
    sessions = max(500, sessions)
    users = int(sessions * random.uniform(0.70, 0.85))
    new_users = int(users * random.uniform(0.55, 0.72))
    pageviews = int(sessions * random.uniform(2.5, 4.5))
    bounce_rate = round(random.uniform(0.38, 0.62), 3)
    avg_session_duration_sec = int(random.gauss(185, 45))
    avg_session_duration_sec = max(60, avg_session_duration_sec)
    pages_per_session = round(pageviews / sessions, 2) if sessions > 0 else 0
    goal_completions = int(sessions * random.uniform(0.02, 0.08))
    conversion_rate = round(goal_completions / sessions, 4) if sessions > 0 else 0

    # Period comparison
    prev_sessions = int(sessions * random.uniform(0.82, 1.18))
    sessions_change_pct = round((sessions - prev_sessions) / prev_sessions * 100, 1) if prev_sessions > 0 else 0

    # Traffic sources breakdown
    traffic_sources = []
    for source, share in TRAFFIC_SOURCES:
        src_sessions = int(sessions * share * random.uniform(0.9, 1.1))
        traffic_sources.append({
            "source": source,
            "sessions": src_sessions,
            "share_pct": round(share * 100, 1),
            "bounce_rate": round(random.uniform(0.30, 0.70), 3),
            "avg_duration_sec": int(random.gauss(avg_session_duration_sec, 40)),
        })

    # Top pages
    top_pages = []
    remaining_pv = pageviews
    for i, (path, name) in enumerate(TOP_PAGES[:8]):
        weight = max(0.05, 0.30 - i * 0.03)
        pv = int(remaining_pv * weight * random.uniform(0.85, 1.15))
        top_pages.append({
            "path": path,
            "name": name,
            "pageviews": pv,
            "unique_pageviews": int(pv * random.uniform(0.65, 0.85)),
            "avg_time_on_page_sec": int(random.gauss(90, 30)),
            "bounce_rate": round(random.uniform(0.30, 0.70), 3),
            "exit_rate": round(random.uniform(0.20, 0.55), 3),
        })

    # Device breakdown
    device_breakdown = [
        {"device": d, "sessions": int(sessions * w), "share_pct": round(w * 100, 1)}
        for d, w in DEVICES
    ]

    # Country breakdown
    country_breakdown = [
        {"country": c, "sessions": int(sessions * w), "share_pct": round(w * 100, 1)}
        for c, w in COUNTRIES
    ]

    # Daily trend (simplified)
    end_date = datetime.now(timezone.utc)
    daily_trend = []
    for d in range(days):
        date = end_date - timedelta(days=days - d - 1)
        day_sessions = int(sessions / days * random.uniform(0.7, 1.3))
        daily_trend.append({
            "date": date.date().isoformat(),
            "sessions": day_sessions,
            "users": int(day_sessions * random.uniform(0.70, 0.85)),
        })

    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "summary": {
            "sessions": sessions,
            "users": users,
            "new_users": new_users,
            "returning_users": users - new_users,
            "pageviews": pageviews,
            "bounce_rate": bounce_rate,
            "bounce_rate_pct": round(bounce_rate * 100, 1),
            "avg_session_duration_sec": avg_session_duration_sec,
            "avg_session_duration_formatted": f"{avg_session_duration_sec // 60}m {avg_session_duration_sec % 60}s",
            "pages_per_session": pages_per_session,
            "goal_completions": goal_completions,
            "conversion_rate": conversion_rate,
            "conversion_rate_pct": round(conversion_rate * 100, 2),
        },
        "period_comparison": {
            "prev_sessions": prev_sessions,
            "sessions_change_pct": sessions_change_pct,
            "trend": "up" if sessions_change_pct > 0 else "down" if sessions_change_pct < 0 else "flat",
        },
        "traffic_sources": traffic_sources,
        "top_pages": top_pages,
        "device_breakdown": device_breakdown,
        "country_breakdown": country_breakdown,
        "daily_trend": daily_trend,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_funnel(
    project_id: str,
    funnel_name: str = "Awareness to Conversion",
) -> Dict[str, Any]:
    """
    Get funnel analysis data showing awareness → consideration → conversion.

    Args:
        project_id: Project identifier
        funnel_name: Funnel name for labeling

    Returns:
        Dict with funnel stages, drop-off rates, and conversion metrics
    """
    logger.info(f"[{project_id}] Fetching funnel data")

    # Top-of-funnel baseline
    awareness_users = int(random.gauss(15000, 4000))
    awareness_users = max(1000, awareness_users)

    # Each stage has realistic drop-off
    consideration_rate = random.uniform(0.25, 0.45)
    intent_rate = random.uniform(0.35, 0.55)
    decision_rate = random.uniform(0.30, 0.55)
    conversion_rate = random.uniform(0.15, 0.35)

    consideration_users = int(awareness_users * consideration_rate)
    intent_users = int(consideration_users * intent_rate)
    decision_users = int(intent_users * decision_rate)
    converted_users = int(decision_users * conversion_rate)

    # Stage details
    stages = [
        {
            "stage": "Awareness",
            "description": "Users who discovered the brand (organic, paid, social)",
            "users": awareness_users,
            "drop_off_pct": 0.0,
            "conversion_from_start_pct": 100.0,
            "avg_touchpoints": 1.0,
            "top_channels": ["Organic Search", "Paid Search", "Social Media"],
        },
        {
            "stage": "Consideration",
            "description": "Users who visited key pages (features, pricing, blog)",
            "users": consideration_users,
            "drop_off_pct": round((1 - consideration_rate) * 100, 1),
            "conversion_from_start_pct": round(consideration_users / awareness_users * 100, 1),
            "avg_touchpoints": round(random.uniform(2.5, 4.0), 1),
            "top_pages": ["/features", "/pricing", "/blog"],
        },
        {
            "stage": "Intent",
            "description": "Users who showed purchase intent (pricing, demo, sign-up visits)",
            "users": intent_users,
            "drop_off_pct": round((1 - intent_rate) * 100, 1),
            "conversion_from_start_pct": round(intent_users / awareness_users * 100, 1),
            "avg_touchpoints": round(random.uniform(4.0, 7.0), 1),
            "top_pages": ["/pricing", "/demo", "/signup"],
        },
        {
            "stage": "Decision",
            "description": "Users who started trial or contacted sales",
            "users": decision_users,
            "drop_off_pct": round((1 - decision_rate) * 100, 1),
            "conversion_from_start_pct": round(decision_users / awareness_users * 100, 1),
            "avg_touchpoints": round(random.uniform(6.0, 10.0), 1),
            "top_actions": ["Free Trial", "Demo Request", "Contact Sales"],
        },
        {
            "stage": "Conversion",
            "description": "Users who became paying customers",
            "users": converted_users,
            "drop_off_pct": round((1 - conversion_rate) * 100, 1),
            "conversion_from_start_pct": round(converted_users / awareness_users * 100, 2),
            "avg_touchpoints": round(random.uniform(8.0, 15.0), 1),
            "avg_days_to_convert": round(random.uniform(7, 45), 1),
        },
    ]

    overall_conversion_rate = round(converted_users / awareness_users * 100, 2) if awareness_users > 0 else 0

    # Optimization opportunities
    opportunities = []
    if (1 - consideration_rate) > 0.65:
        opportunities.append("High awareness-to-consideration drop-off: improve landing page relevance and messaging clarity")
    if (1 - intent_rate) > 0.65:
        opportunities.append("High consideration-to-intent drop-off: add social proof, case studies, and clearer CTAs on feature pages")
    if (1 - conversion_rate) > 0.75:
        opportunities.append("High decision-to-conversion drop-off: reduce friction in sign-up flow, offer live chat support")

    return {
        "project_id": project_id,
        "funnel_name": funnel_name,
        "stages": stages,
        "overall_conversion_rate_pct": overall_conversion_rate,
        "total_awareness": awareness_users,
        "total_converted": converted_users,
        "optimization_opportunities": opportunities,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
