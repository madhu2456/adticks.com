"""
Google Search Console service for AdTicks.
Provides OAuth flow structure and realistic mock GSC data.
"""

import logging
import random
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# OAuth configuration (fill with real values via environment)
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_REDIRECT_URI = "https://app.adticks.io/auth/gsc/callback"
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

# Realistic branded/non-branded query mix
QUERY_TEMPLATES = [
    # Branded
    ("{brand}", True, (150, 800), (5000, 20000), (0.03, 0.08), (1.0, 3.5)),
    ("{brand} pricing", True, (80, 300), (2000, 8000), (0.04, 0.09), (1.5, 4.0)),
    ("{brand} reviews", True, (60, 250), (1500, 6000), (0.04, 0.08), (2.0, 5.0)),
    ("{brand} login", True, (200, 1000), (3000, 12000), (0.07, 0.15), (1.0, 2.0)),
    ("{brand} tutorial", True, (30, 150), (800, 3000), (0.04, 0.08), (3.0, 6.0)),
    ("{brand} vs {comp}", True, (20, 100), (500, 2000), (0.03, 0.07), (4.0, 8.0)),
    # Non-branded
    ("best {industry} software", False, (50, 300), (3000, 15000), (0.01, 0.04), (5.0, 15.0)),
    ("{industry} tools comparison", False, (30, 200), (2000, 10000), (0.01, 0.035), (6.0, 18.0)),
    ("how to {action} {industry}", False, (40, 250), (2500, 12000), (0.015, 0.045), (4.0, 12.0)),
    ("{industry} automation", False, (20, 150), (1500, 8000), (0.01, 0.03), (7.0, 20.0)),
    ("free {industry} platform", False, (60, 400), (4000, 18000), (0.015, 0.04), (5.0, 16.0)),
    ("top {industry} companies", False, (15, 100), (1000, 5000), (0.01, 0.025), (8.0, 22.0)),
    ("{industry} for small business", False, (25, 180), (1800, 9000), (0.014, 0.038), (6.0, 19.0)),
    ("enterprise {industry} solution", False, (10, 80), (600, 3000), (0.012, 0.03), (9.0, 25.0)),
    ("{industry} roi calculator", False, (8, 60), (400, 2000), (0.02, 0.05), (3.0, 10.0)),
    ("improve {industry} performance", False, (15, 120), (1000, 5500), (0.012, 0.03), (5.0, 15.0)),
]


def _render_template(template: str, brand: str, industry: str, competitors: List[str]) -> str:
    """Render a query template with real values."""
    comp = random.choice(competitors) if competitors else "competitor"
    action = random.choice(["improve", "optimize", "scale", "automate", "measure"])
    return (template
            .replace("{brand}", brand)
            .replace("{comp}", comp)
            .replace("{industry}", industry.lower())
            .replace("{action}", action))


def get_auth_url(state: Optional[str] = None) -> str:
    """
    Generate the Google OAuth2 authorization URL for GSC access.

    Args:
        state: Optional CSRF state token

    Returns:
        Full OAuth2 authorization URL string
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GSC_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state

    url = f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"
    logger.info("Generated GSC OAuth URL")
    return url


async def exchange_code(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Exchange an OAuth authorization code for tokens (mocked).

    In production: POST to GOOGLE_TOKEN_URL with code + client credentials.

    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Override redirect URI

    Returns:
        Token dict with access_token, refresh_token, expires_in, token_type
    """
    logger.info(f"Exchanging OAuth code: {code[:10]}...")

    # Mocked token response (real implementation would POST to GOOGLE_TOKEN_URL)
    mock_token = {
        "access_token": f"ya29.mock_access_token_{uuid.uuid4().hex[:20]}",
        "refresh_token": f"1//mock_refresh_{uuid.uuid4().hex[:20]}",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": GSC_SCOPE,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("OAuth code exchange complete (mocked)")
    return mock_token


async def fetch_queries(
    project_id: str,
    brand_name: str = "Brand",
    industry: str = "Technology",
    competitors: Optional[List[str]] = None,
    days: int = 30,
) -> List[Dict[str, Any]]:
    """
    Fetch GSC search query performance data (realistic mock).

    Returns 20-50 queries with clicks, impressions, CTR, and position.

    Args:
        project_id: Project identifier
        brand_name: Brand name for templating queries
        industry: Industry for non-branded query generation
        competitors: Competitor names for comparison queries
        days: Number of days to simulate data for

    Returns:
        List of GSC query performance dicts
    """
    logger.info(f"[{project_id}] Fetching GSC queries for past {days} days")
    competitors = competitors or ["Competitor A", "Competitor B"]
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    queries: List[Dict[str, Any]] = []

    # Select 25-40 templates randomly
    n_queries = random.randint(25, 40)
    templates_sample = random.choices(QUERY_TEMPLATES, k=n_queries)

    for tmpl, is_branded, clicks_range, imp_range, ctr_range, pos_range in templates_sample:
        query_text = _render_template(tmpl, brand_name, industry, competitors)
        clicks = random.randint(*clicks_range)
        impressions = random.randint(*imp_range)
        # Ensure CTR is consistent with clicks/impressions
        ctr = clicks / impressions
        position = round(random.uniform(*pos_range), 1)

        queries.append({
            "query": query_text,
            "clicks": clicks,
            "impressions": impressions,
            "ctr": round(ctr, 4),
            "ctr_pct": round(ctr * 100, 2),
            "position": position,
            "is_branded": is_branded,
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
            },
        })

    # Sort by clicks descending
    queries.sort(key=lambda x: x["clicks"], reverse=True)
    logger.info(f"[{project_id}] Fetched {len(queries)} GSC queries")
    return queries


async def sync_gsc_data(
    project_id: str,
    brand_name: str = "Brand",
    industry: str = "Technology",
    competitors: Optional[List[str]] = None,
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Sync GSC data for a project (fetches and prepares for DB storage).

    Args:
        project_id: Project identifier
        brand_name: Brand name
        industry: Industry category
        competitors: Competitor names
        db_session: Optional async DB session for storage

    Returns:
        Sync result dict with query count and summary stats
    """
    logger.info(f"[{project_id}] Syncing GSC data")
    queries = await fetch_queries(project_id, brand_name, industry, competitors)

    branded = [q for q in queries if q["is_branded"]]
    non_branded = [q for q in queries if not q["is_branded"]]

    total_clicks = sum(q["clicks"] for q in queries)
    total_impressions = sum(q["impressions"] for q in queries)
    avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0
    avg_position = round(sum(q["position"] for q in queries) / len(queries), 1) if queries else 0

    # In production: would bulk-insert to Ranking model via db_session
    if db_session:
        logger.info(f"[{project_id}] Would store {len(queries)} GSC records to DB")

    return {
        "project_id": project_id,
        "queries": queries,
        "query_count": len(queries),
        "branded_count": len(branded),
        "non_branded_count": len(non_branded),
        "summary": {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr_pct": avg_ctr,
            "avg_position": avg_position,
            "top_query": queries[0]["query"] if queries else None,
            "top_query_clicks": queries[0]["clicks"] if queries else 0,
        },
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
