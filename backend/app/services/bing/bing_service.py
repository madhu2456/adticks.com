"""
Bing Webmaster Tools service for AdTicks.
Direct API OAuth2 flow and Bing Webmaster Tools API integration.
No Python SDK available, so we use httpx for all API calls.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth endpoints
BING_AUTH_BASE = "https://login.live.com/oauth20_authorize.srf"
BING_TOKEN_URL = "https://login.live.com/oauth20_token.srf"
BING_API_BASE = "https://api.webmaster.bing.com"

# Bing scopes
BING_SCOPE = "bingwebmaster.api"


def get_auth_url(state: Optional[str] = None) -> str:
    """
    Generate the Bing OAuth2 authorization URL for Webmaster Tools access.

    Args:
        state: Optional CSRF state token

    Returns:
        Full OAuth2 authorization URL string
    """
    params = {
        "client_id": settings.BING_CLIENT_ID,
        "redirect_uri": settings.BING_REDIRECT_URI,
        "response_type": "code",
        "scope": BING_SCOPE,
    }
    if state:
        params["state"] = state

    url = f"{BING_AUTH_BASE}?{urlencode(params)}"
    logger.info("Generated Bing OAuth URL")
    return url


async def exchange_code(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Exchange an OAuth authorization code for Bing tokens.

    Posts to Bing's token endpoint to get access_token and refresh_token.

    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Override redirect URI (default from settings)

    Returns:
        Token dict with access_token, refresh_token, expires_in, token_type
        
    Raises:
        ValueError: If token exchange fails
    """
    redirect_uri = redirect_uri or settings.BING_REDIRECT_URI
    
    if not settings.BING_CLIENT_ID or not settings.BING_CLIENT_SECRET:
        logger.error("Bing OAuth credentials not configured in .env")
        raise ValueError("Bing OAuth credentials missing")
    
    logger.info(f"Exchanging OAuth code for Bing tokens. Redirect URI: {redirect_uri}")
    
    payload = {
        "code": code,
        "client_id": settings.BING_CLIENT_ID,
        "client_secret": settings.BING_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(BING_TOKEN_URL, data=payload)
            response.raise_for_status()
            
        token_data = response.json()
        token_data["issued_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("Bing OAuth code exchange successful - got real tokens")
        return token_data
        
    except httpx.HTTPError as e:
        logger.error(f"Bing OAuth token exchange failed: {e}")
        raise ValueError(f"Failed to exchange OAuth code: {e}")


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an expired Bing access token using refresh token.

    Args:
        refresh_token: The refresh token from previous authorization

    Returns:
        New token dict with access_token and expires_in
        
    Raises:
        ValueError: If token refresh fails
    """
    if not settings.BING_CLIENT_ID or not settings.BING_CLIENT_SECRET:
        raise ValueError("Bing OAuth credentials missing")
    
    logger.info("Refreshing Bing access token...")
    
    payload = {
        "client_id": settings.BING_CLIENT_ID,
        "client_secret": settings.BING_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(BING_TOKEN_URL, data=payload)
            response.raise_for_status()
        
        token_data = response.json()
        token_data["issued_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("Bing access token refreshed successfully")
        return token_data
        
    except httpx.HTTPError as e:
        logger.error(f"Bing token refresh failed: {e}")
        raise ValueError(f"Failed to refresh access token: {e}")


async def get_sites(access_token: str) -> List[Dict[str, Any]]:
    """
    Fetch Bing Webmaster Tools sites available to the user.

    Args:
        access_token: Bing OAuth access token

    Returns:
        List of site dicts with url, siteId, and verification status
        
    Raises:
        ValueError: If API call fails
    """
    logger.info("Fetching Bing Webmaster Tools sites...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BING_API_BASE}/webmasters/api.svc/sites",
                headers=headers
            )
            response.raise_for_status()
        
        data = response.json()
        sites = data.get("d", {}).get("Sites", [])
        
        logger.info(f"Found {len(sites)} Bing sites")
        return sites
        
    except httpx.HTTPError as e:
        logger.error(f"Bing API error fetching sites: {e}")
        raise ValueError(f"Failed to fetch Bing sites: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching Bing sites: {e}")
        raise ValueError(f"Unexpected error: {e}")


async def fetch_search_queries(
    access_token: str,
    site_url: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    """
    Fetch Bing search query performance data for a site.

    Args:
        access_token: Bing OAuth access token
        site_url: Site URL (e.g., 'https://example.com')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of query performance dicts with clicks, impressions, position, ctr
        
    Raises:
        ValueError: If API call fails
    """
    logger.info(f"Fetching Bing search queries for {site_url} from {start_date} to {end_date}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    # URL encode the site URL for API query
    site_param = site_url.rstrip('/')
    
    params = {
        "siteUrl": site_param,
        "startDate": start_date,
        "endDate": end_date,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BING_API_BASE}/webmasters/api.svc/queryStats",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
        
        data = response.json()
        queries = data.get("d", {}).get("QueryStats", [])
        
        logger.info(f"Got {len(queries)} Bing query records")
        
        # Transform Bing API response to our format
        results = []
        for query in queries:
            query_dict = {
                "query": query.get("Query", "unknown"),
                "clicks": int(query.get("Clicks", 0)),
                "impressions": int(query.get("Impressions", 0)),
                "ctr": round(float(query.get("Ctr", 0)), 4),
                "position": round(float(query.get("AvgPosition", 0)), 1),
                "date": datetime.now(timezone.utc).date().isoformat(),
            }
            results.append(query_dict)
        
        logger.info(f"Transformed {len(results)} Bing query records")
        return results
        
    except httpx.HTTPError as e:
        logger.error(f"Bing API error: {e}")
        raise ValueError(f"Failed to fetch Bing search queries: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching Bing search queries: {e}")
        raise ValueError(f"Unexpected error: {e}")


async def fetch_crawl_issues(
    access_token: str,
    site_url: str,
) -> List[Dict[str, Any]]:
    """
    Fetch Bing crawl and indexing issues for a site.

    Args:
        access_token: Bing OAuth access token
        site_url: Site URL (e.g., 'https://example.com')

    Returns:
        List of issue dicts with type, url, status, severity
        
    Raises:
        ValueError: If API call fails
    """
    logger.info(f"Fetching Bing crawl issues for {site_url}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    site_param = site_url.rstrip('/')
    
    params = {
        "siteUrl": site_param,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BING_API_BASE}/webmasters/api.svc/crawlissues",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
        
        data = response.json()
        issues = data.get("d", {}).get("CrawlIssues", [])
        
        logger.info(f"Got {len(issues)} Bing crawl issues")
        return issues
        
    except httpx.HTTPError as e:
        logger.error(f"Bing API error fetching crawl issues: {e}")
        raise ValueError(f"Failed to fetch Bing crawl issues: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching Bing crawl issues: {e}")
        raise ValueError(f"Unexpected error: {e}")


async def sync_bing_data(
    access_token: str,
    site_url: str,
    start_date: str,
    end_date: str,
    project_id: Optional[str] = None,
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Sync real Bing Webmaster Tools data for a project.

    Fetches search queries and issues, stores to database with deduplication.

    Args:
        access_token: Bing OAuth access token
        site_url: Site URL (e.g., 'https://example.com')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        project_id: UUID of project for database persistence
        db_session: Optional async DB session for storing results

    Returns:
        Sync result dict with query count and summary stats
        
    Raises:
        ValueError: If API call fails
    """
    logger.info(f"Syncing Bing data for {site_url} from {start_date} to {end_date}")
    
    # Fetch real data from Bing API
    queries = await fetch_search_queries(
        access_token=access_token,
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
    )
    
    issues = await fetch_crawl_issues(
        access_token=access_token,
        site_url=site_url,
    )
    
    total_clicks = sum(q["clicks"] for q in queries)
    total_impressions = sum(q["impressions"] for q in queries)
    avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0
    avg_position = round(sum(q["position"] for q in queries) / len(queries), 1) if queries else 0
    
    logger.info(f"Synced {len(queries)} Bing search records and {len(issues)} issues")
    
    # Bulk insert to database with deduplication and transaction handling
    if db_session and project_id:
        logger.info(f"Storing {len(queries)} Bing records to database for project {project_id}")
        try:
            from sqlalchemy import and_, delete
            from app.models.bing import BingData, BingIssue
            
            # Convert project_id string to UUID
            import uuid as uuid_module
            project_uuid = uuid_module.UUID(project_id) if isinstance(project_id, str) else project_id
            
            # Delete existing records for this date range to avoid duplicates
            await db_session.execute(
                delete(BingData).where(
                    and_(
                        BingData.project_id == project_uuid,
                        BingData.date == datetime.now(timezone.utc).date().isoformat()
                    )
                )
            )
            
            # Bulk insert search query records
            records_to_insert = []
            seen_queries = set()
            
            for query_data in queries:
                query_key = (query_data["query"], query_data.get("date"))
                
                if query_key in seen_queries:
                    logger.debug(f"Skipping duplicate Bing query: {query_data['query']}")
                    continue
                
                seen_queries.add(query_key)
                
                bing_record = BingData(
                    id=uuid.uuid4(),
                    project_id=project_uuid,
                    query=query_data.get("query"),
                    clicks=query_data.get("clicks", 0),
                    impressions=query_data.get("impressions", 0),
                    ctr=query_data.get("ctr", 0.0),
                    position=query_data.get("position", 0.0),
                    date=query_data.get("date"),
                )
                records_to_insert.append(bing_record)
            
            for record in records_to_insert:
                db_session.add(record)
            
            # Bulk insert issue records
            issue_records = []
            for issue in issues:
                issue_record = BingIssue(
                    id=uuid.uuid4(),
                    project_id=project_uuid,
                    issue_type=issue.get("IssueType", "unknown"),
                    url=issue.get("Url", "unknown"),
                    status=issue.get("IssueStatus", "open"),
                    severity=issue.get("IssueLevel", "medium"),
                    detected_date=datetime.now(timezone.utc).date(),
                )
                issue_records.append(issue_record)
            
            for record in issue_records:
                db_session.add(record)
            
            # Commit transaction
            await db_session.commit()
            logger.info(f"Successfully stored {len(records_to_insert)} Bing records and {len(issue_records)} issues to database")
            
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to store Bing data to database: {e}")
            raise ValueError(f"Database persistence failed: {e}")
    
    return {
        "site_url": site_url,
        "queries": queries,
        "query_count": len(queries),
        "issues": issues,
        "issue_count": len(issues),
        "summary": {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr_pct": avg_ctr,
            "avg_position": avg_position,
            "top_query": queries[0]["query"] if queries else None,
            "top_query_clicks": queries[0]["clicks"] if queries else 0,
            "open_issues": len([i for i in issues if i.get("IssueStatus") == "open"]),
        },
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
