"""
Analytics service for AdTicks.
Feature not yet implemented - stub returns empty data with logging.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def get_overview(
    project_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get analytics overview metrics for a project.
    
    Feature not yet implemented.
    Returns: Empty dict with stub data
    """
    logger.info(f"[{project_id}] Analytics API not yet implemented", extra={"feature": "get_overview"})
    
    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "sessions": 0,
        "users": 0,
        "bounce_rate": 0.0,
        "avg_session_duration_sec": 0,
        "pages_per_session": 0.0,
        "goal_completions": 0,
        "conversion_rate": 0.0,
        "traffic_sources": [],
        "top_pages": [],
        "device_breakdown": [],
        "country_breakdown": [],
        "daily_trend": [],
        "sessions_change_pct": 0.0,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_traffic_sources(
    project_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get traffic source breakdown.
    
    Feature not yet implemented.
    Returns: Empty dict
    """
    logger.info(f"[{project_id}] Analytics API not yet implemented", extra={"feature": "get_traffic_sources"})
    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "sources": [],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_pages(
    project_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get top pages analytics.
    
    Feature not yet implemented.
    Returns: Empty dict
    """
    logger.info(f"[{project_id}] Analytics API not yet implemented", extra={"feature": "get_pages"})
    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "pages": [],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_goals(
    project_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get goal conversion analytics.
    
    Feature not yet implemented.
    Returns: Empty dict
    """
    logger.info(f"[{project_id}] Analytics API not yet implemented", extra={"feature": "get_goals"})
    return {
        "project_id": project_id,
        "reporting_period_days": days,
        "goals": [],
        "total_conversions": 0,
        "conversion_rate": 0.0,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def sync_analytics(
    project_id: str,
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Sync analytics data for a project.
    
    Feature not yet implemented.
    Returns: Sync result dict indicating feature not yet implemented
    """
    logger.info(f"[{project_id}] Analytics API not yet implemented", extra={"feature": "sync_analytics"})
    
    return {
        "project_id": project_id,
        "status": "not_implemented",
        "records_synced": 0,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
