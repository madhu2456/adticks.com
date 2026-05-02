"""
Google Ads service for AdTicks.
Feature not yet implemented - stub returns empty data with logging.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def get_campaigns(project_id: str, brand_name: str = "Brand", industry: str = "Technology") -> List[Dict[str, Any]]:
    """
    Get Google Ads campaigns for a project.

    Args:
        project_id: Project identifier
        brand_name: Brand name for campaign naming
        industry: Industry for context

    Returns:
        Empty list - Google Ads API not yet implemented
    """
    logger.info(f"[{project_id}] Google Ads API not yet implemented", extra={"feature": "get_campaigns"})
    return []


async def get_performance(
    project_id: str,
    days: int = 30,
    brand_name: str = "Brand",
    industry: str = "Technology",
) -> Dict[str, Any]:
    """
    Get aggregated Google Ads performance metrics.

    Args:
        project_id: Project identifier
        days: Number of days for the reporting window
        brand_name: Brand name
        industry: Industry category

    Returns:
        Empty dict - Google Ads API not yet implemented
    """
    logger.info(f"[{project_id}] Google Ads API not yet implemented", extra={"feature": "get_performance"})
    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "campaigns": [],
        "daily_data": [],
        "summary": {},
        "period_comparison": {},
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
        Sync result dict indicating feature not yet implemented
    """
    logger.info(f"[{project_id}] Google Ads API not yet implemented", extra={"feature": "sync_ads_data"})

    return {
        "project_id": project_id,
        "status": "not_implemented",
        "campaigns_synced": 0,
        "daily_records": 0,
        "summary": {},
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
