"""
Google Ads service for AdTicks.
Provides realistic mock campaign and performance data with real structure.
"""

import logging
import random
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

CAMPAIGN_TYPES = ["Search", "Display", "Shopping", "Video", "Performance Max"]
CAMPAIGN_STATUSES = ["ENABLED", "PAUSED", "REMOVED"]
BID_STRATEGIES = ["TARGET_CPA", "TARGET_ROAS", "MAXIMIZE_CONVERSIONS", "MANUAL_CPC", "ENHANCED_CPC"]
AD_GROUP_THEMES = [
    "Brand Keywords", "Competitor Keywords", "Generic Industry", "Product Features",
    "Pricing Pages", "Free Trial", "Demo Request", "Integration Keywords"
]


def _generate_campaign(brand_name: str, industry: str, index: int) -> Dict[str, Any]:
    """Generate a realistic mock campaign dict."""
    campaign_type = random.choice(CAMPAIGN_TYPES[:3])
    budget = round(random.uniform(500, 8000), 2)
    status = random.choices(
        ["ENABLED", "PAUSED"],
        weights=[0.75, 0.25],
    )[0]

    names = {
        "Search": [f"[Search] {brand_name} - Brand", f"[Search] {industry} - Generic", "[Search] Competitor Conquest"],
        "Display": [f"[Display] {brand_name} - Remarketing", f"[Display] {industry} - Awareness"],
        "Shopping": [f"[Shopping] {brand_name} - All Products", f"[Shopping] {industry} - Best Sellers"],
    }
    campaign_names = names.get(campaign_type, [f"Campaign {index + 1}"])

    return {
        "id": str(uuid.uuid4()),
        "name": random.choice(campaign_names),
        "type": campaign_type,
        "status": status,
        "daily_budget_usd": budget,
        "monthly_budget_usd": round(budget * 30, 2),
        "bid_strategy": random.choice(BID_STRATEGIES),
        "target_cpa": round(random.uniform(15, 120), 2) if "CPA" in random.choice(BID_STRATEGIES) else None,
        "target_roas": round(random.uniform(2.0, 8.0), 2),
        "ad_groups": [
            {
                "id": str(uuid.uuid4()),
                "name": theme,
                "status": "ENABLED",
                "keyword_count": random.randint(5, 30),
                "avg_cpc_usd": round(random.uniform(0.5, 15.0), 2),
            }
            for theme in random.sample(AD_GROUP_THEMES, k=random.randint(2, 4))
        ],
        "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))).isoformat(),
    }


def _generate_performance_day(
    date: datetime,
    budget: float,
    campaign_id: str,
) -> Dict[str, Any]:
    """Generate realistic single-day performance metrics for a campaign."""
    impressions = int(random.gauss(5000, 1200))
    impressions = max(200, impressions)
    ctr = random.uniform(0.02, 0.08)
    clicks = int(impressions * ctr)
    cpc = round(random.uniform(0.8, 12.0), 2)
    spend = round(min(clicks * cpc, budget), 2)
    conv_rate = random.uniform(0.02, 0.12)
    conversions = round(clicks * conv_rate, 1)
    conv_value = round(conversions * random.uniform(50, 800), 2)
    roas = round(conv_value / spend, 2) if spend > 0 else 0

    return {
        "date": date.date().isoformat(),
        "campaign_id": campaign_id,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": round(ctr, 4),
        "ctr_pct": round(ctr * 100, 2),
        "avg_cpc_usd": cpc,
        "spend_usd": spend,
        "conversions": conversions,
        "conversion_rate": round(conv_rate, 4),
        "conversion_value_usd": conv_value,
        "roas": roas,
        "quality_score_avg": round(random.uniform(4.0, 9.5), 1),
    }


async def get_campaigns(project_id: str, brand_name: str = "Brand", industry: str = "Technology") -> List[Dict[str, Any]]:
    """
    Get Google Ads campaigns for a project (realistic mock).

    Args:
        project_id: Project identifier
        brand_name: Brand name for campaign naming
        industry: Industry for context

    Returns:
        List of campaign dicts
    """
    logger.info(f"[{project_id}] Fetching Ads campaigns")
    n_campaigns = random.randint(3, 7)
    campaigns = [_generate_campaign(brand_name, industry, i) for i in range(n_campaigns)]
    logger.info(f"[{project_id}] Returning {len(campaigns)} campaigns")
    return campaigns


async def get_performance(
    project_id: str,
    days: int = 30,
    brand_name: str = "Brand",
    industry: str = "Technology",
) -> Dict[str, Any]:
    """
    Get aggregated Google Ads performance metrics (realistic mock).

    Args:
        project_id: Project identifier
        days: Number of days for the reporting window
        brand_name: Brand name
        industry: Industry category

    Returns:
        Performance dict with daily breakdown and aggregated metrics
    """
    logger.info(f"[{project_id}] Fetching Ads performance for {days} days")
    campaigns = await get_campaigns(project_id, brand_name, industry)

    end_date = datetime.now(timezone.utc)
    daily_data: List[Dict[str, Any]] = []

    for campaign in campaigns:
        if campaign["status"] != "ENABLED":
            continue
        budget = campaign["daily_budget_usd"]
        for d in range(days):
            date = end_date - timedelta(days=d)
            daily_data.append(_generate_performance_day(date, budget, campaign["id"]))

    # Aggregate totals
    total_impressions = sum(d["impressions"] for d in daily_data)
    total_clicks = sum(d["clicks"] for d in daily_data)
    total_spend = round(sum(d["spend_usd"] for d in daily_data), 2)
    total_conversions = round(sum(d["conversions"] for d in daily_data), 1)
    total_conv_value = round(sum(d["conversion_value_usd"] for d in daily_data), 2)

    avg_ctr = round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0
    avg_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0
    overall_roas = round(total_conv_value / total_spend, 2) if total_spend > 0 else 0
    conv_rate = round(total_conversions / total_clicks, 4) if total_clicks > 0 else 0

    # Month-over-month comparison (simulate prior period)
    prev_spend = round(total_spend * random.uniform(0.8, 1.2), 2)
    prev_conversions = round(total_conversions * random.uniform(0.75, 1.25), 1)
    spend_change_pct = round((total_spend - prev_spend) / prev_spend * 100, 1) if prev_spend > 0 else 0
    conv_change_pct = round((total_conversions - prev_conversions) / prev_conversions * 100, 1) if prev_conversions > 0 else 0

    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "campaigns": campaigns,
        "daily_data": daily_data,
        "summary": {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_spend_usd": total_spend,
            "total_conversions": total_conversions,
            "total_conversion_value_usd": total_conv_value,
            "avg_ctr": avg_ctr,
            "avg_ctr_pct": round(avg_ctr * 100, 2),
            "avg_cpc_usd": avg_cpc,
            "overall_roas": overall_roas,
            "conversion_rate": conv_rate,
            "conversion_rate_pct": round(conv_rate * 100, 2),
            "cost_per_conversion_usd": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
        },
        "period_comparison": {
            "prev_spend_usd": prev_spend,
            "spend_change_pct": spend_change_pct,
            "prev_conversions": prev_conversions,
            "conv_change_pct": conv_change_pct,
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def sync_ads_data(
    project_id: str,
    brand_name: str = "Brand",
    industry: str = "Technology",
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Sync Google Ads data for a project and store to DB.

    Args:
        project_id: Project identifier
        brand_name: Brand name
        industry: Industry category
        db_session: Optional async DB session

    Returns:
        Sync result dict with performance summary
    """
    logger.info(f"[{project_id}] Syncing Ads data")
    performance = await get_performance(project_id, days=30, brand_name=brand_name, industry=industry)

    if db_session:
        logger.info(f"[{project_id}] Would store Ads performance to DB")

    return {
        "project_id": project_id,
        "status": "success",
        "campaigns_synced": len(performance["campaigns"]),
        "daily_records": len(performance["daily_data"]),
        "summary": performance["summary"],
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
