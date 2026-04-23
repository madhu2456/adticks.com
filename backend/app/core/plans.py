"""
AdTicks — Plan configurations and limits.
"""

from typing import Dict, Any

PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "ai_scans": 50,
        "keywords": 500,
        "competitors": 3,
        "team_members": 1,
        "gsc_integration": True,
        "ads_integration": False,
        "custom_reports": False,
        "api_access": False,
        "priority_support": False,
        "api_rate_limit": "100/hr",
    },
    "pro": {
        "ai_scans": 1000000,  # Unlimited (represented by a large number)
        "keywords": 1000000,   # Unlimited
        "competitors": 10,
        "team_members": 10,
        "gsc_integration": True,
        "ads_integration": True,
        "custom_reports": True,
        "api_access": True,
        "priority_support": True,
        "api_rate_limit": "1,000/hr",
    },
    "enterprise": {
        "ai_scans": 10000000,
        "keywords": 10000000,
        "competitors": 100,
        "team_members": 100,
        "gsc_integration": True,
        "ads_integration": True,
        "custom_reports": True,
        "api_access": True,
        "priority_support": True,
        "api_rate_limit": "10,000/hr",
    },
}

def get_plan_limits(plan: str) -> Dict[str, Any]:
    """Get limits for a specific plan."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
