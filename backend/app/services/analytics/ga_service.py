"""
Google Analytics 4 service for AdTicks.
Real OAuth2 flow and Google Analytics 4 Reporting API integration.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth base URLs
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GA_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"


def get_auth_url(state: Optional[str] = None) -> str:
    """
    Generate the Google OAuth2 authorization URL for GA4 access.

    Args:
        state: Optional CSRF state token

    Returns:
        Full OAuth2 authorization URL string
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GA_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state

    url = f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"
    logger.info("Generated GA4 OAuth URL")
    return url


async def exchange_code(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Exchange an OAuth authorization code for real Google tokens.

    Posts to Google's token endpoint to get access_token and refresh_token.

    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Override redirect URI (default from settings)

    Returns:
        Token dict with access_token, refresh_token, expires_in, token_type
        
    Raises:
        ValueError: If token exchange fails
    """
    redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured in .env")
        raise ValueError("Google OAuth credentials missing")
    
    logger.info(f"Exchanging OAuth code for GA4 tokens. Redirect URI: {redirect_uri}")
    
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            response.raise_for_status()
            
        token_data = response.json()
        token_data["issued_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("GA4 OAuth code exchange successful - got real tokens")
        return token_data
        
    except httpx.HTTPError as e:
        logger.error(f"GA4 OAuth token exchange failed: {e}")
        raise ValueError(f"Failed to exchange OAuth code: {e}")


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an expired Google access token using refresh token.

    Args:
        refresh_token: The refresh token from previous authorization

    Returns:
        New token dict with access_token and expires_in
        
    Raises:
        ValueError: If token refresh fails
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials missing")
    
    logger.info("Refreshing GA4 access token...")
    
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            response.raise_for_status()
        
        token_data = response.json()
        token_data["issued_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("GA4 access token refreshed successfully")
        return token_data
        
    except httpx.HTTPError as e:
        logger.error(f"GA4 token refresh failed: {e}")
        raise ValueError(f"Failed to refresh access token: {e}")


async def get_ga_properties(access_token: str) -> List[Dict[str, Any]]:
    """
    Fetch GA4 properties available to the user.

    Args:
        access_token: Google OAuth access token

    Returns:
        List of property dicts with id, displayName, parent (account)
        
    Raises:
        ValueError: If API call fails
    """
    logger.info("Fetching GA4 properties...")
    
    try:
        from google.oauth2.credentials import Credentials
        
        credentials = Credentials(access_token)
        service = build("analyticsadmin", "v1beta", credentials=credentials)
        
        # List accounts
        accounts_response = service.accounts().list().execute()
        accounts = accounts_response.get("accounts", [])
        
        all_properties = []
        for account in accounts:
            account_name = account.get("name")
            # List properties under this account
            properties_response = service.accounts().properties().list(parent=account_name).execute()
            properties = properties_response.get("properties", [])
            all_properties.extend(properties)
        
        logger.info(f"Found {len(all_properties)} GA4 properties")
        return all_properties
        
    except HttpError as e:
        logger.error(f"GA4 API error fetching properties: {e}")
        raise ValueError(f"Failed to fetch GA4 properties: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching GA4 properties: {e}")
        raise ValueError(f"Unexpected error: {e}")


async def fetch_ga_metrics(
    access_token: str,
    property_id: str,
    start_date: str,
    end_date: str,
    metrics: Optional[List[str]] = None,
    dimensions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch real GA4 metrics using Google Analytics Data API.

    Args:
        access_token: Google OAuth access token
        property_id: GA4 property ID (numeric, e.g., '123456789')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metrics: Metrics to retrieve (default: sessions, users, conversions)
        dimensions: Dimensions to group by (default: date)

    Returns:
        List of metric rows with requested dimensions and metrics
        
    Raises:
        ValueError: If API call fails
    """
    metrics = metrics or ["sessions", "users", "conversions"]
    dimensions = dimensions or ["date"]
    
    logger.info(f"Fetching GA4 metrics for property {property_id} from {start_date} to {end_date}")
    
    try:
        from google.oauth2.credentials import Credentials
        
        credentials = Credentials(access_token)
        service = build("analyticsdata", "v1beta", credentials=credentials)
        
        # Format metrics and dimensions for API
        metric_requests = [{"name": f"metricValue{i+1}"} for i in range(len(metrics))]
        for i, metric in enumerate(metrics):
            metric_requests[i]["name"] = metric
        
        dimension_requests = [{"name": dim} for dim in dimensions]
        
        # Call runReport
        report_request = {
            "dateRanges": [
                {
                    "startDate": start_date,
                    "endDate": end_date,
                }
            ],
            "metrics": metric_requests,
            "dimensions": dimension_requests,
            "limit": "100000",
        }
        
        response = service.properties().runReport(
            property=f"properties/{property_id}",
            body=report_request
        ).execute()
        
        rows = response.get("rows", [])
        logger.info(f"Got {len(rows)} rows from GA4 API")
        
        # Transform rows into dict format
        results = []
        for row in rows:
            row_dict = {}
            
            # Add dimensions
            dimension_values = row.get("dimensionValues", [])
            for i, dim in enumerate(dimensions):
                if i < len(dimension_values):
                    row_dict[dim] = dimension_values[i].get("value", "unknown")
            
            # Add metrics
            metric_values = row.get("metricValues", [])
            for i, metric in enumerate(metrics):
                if i < len(metric_values):
                    try:
                        value = float(metric_values[i].get("value", 0))
                        row_dict[metric] = value
                    except (ValueError, TypeError):
                        row_dict[metric] = 0
            
            results.append(row_dict)
        
        logger.info(f"Transformed {len(results)} rows from GA4 API")
        return results
        
    except HttpError as e:
        logger.error(f"GA4 API error: {e}")
        raise ValueError(f"Failed to fetch GA4 metrics: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching GA4 metrics: {e}")
        raise ValueError(f"Unexpected error: {e}")


async def sync_ga_data(
    access_token: str,
    property_id: str,
    start_date: str,
    end_date: str,
    project_id: Optional[str] = None,
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Sync real GA4 data for a project from Google Analytics 4 API.

    Fetches metrics and stores to database with deduplication.

    Args:
        access_token: Google OAuth access token
        property_id: GA4 property ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        project_id: UUID of project for database persistence
        db_session: Optional async DB session for storing results

    Returns:
        Sync result dict with metric count and summary stats
        
    Raises:
        ValueError: If API call fails
    """
    logger.info(f"Syncing GA4 data for property {property_id} from {start_date} to {end_date}")
    
    # Fetch real data from GA4 API
    metrics_data = await fetch_ga_metrics(
        access_token=access_token,
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        metrics=["sessions", "users", "newUsers", "pageviews", "bounceRate", "conversions"],
        dimensions=["date", "trafficSource"],
    )
    
    # Calculate summary stats
    total_sessions = sum(float(m.get("sessions", 0)) for m in metrics_data)
    total_users = sum(float(m.get("users", 0)) for m in metrics_data)
    total_conversions = sum(float(m.get("conversions", 0)) for m in metrics_data)
    avg_bounce_rate = (
        sum(float(m.get("bounceRate", 0)) for m in metrics_data) / len(metrics_data)
        if metrics_data else 0
    )
    
    logger.info(f"Synced {len(metrics_data)} GA4 records")
    
    # Bulk insert to database with deduplication and transaction handling
    if db_session and project_id:
        logger.info(f"Storing {len(metrics_data)} GA4 records to database for project {project_id}")
        try:
            from sqlalchemy import and_, delete
            from app.models.ga import GAData
            
            # Convert project_id string to UUID
            import uuid as uuid_module
            project_uuid = uuid_module.UUID(project_id) if isinstance(project_id, str) else project_id
            
            # Delete existing records for this date range to avoid duplicates
            await db_session.execute(
                delete(GAData).where(
                    and_(
                        GAData.project_id == project_uuid,
                        GAData.date == datetime.now(timezone.utc).date().isoformat()
                    )
                )
            )
            
            # Bulk insert new records
            records_to_insert = []
            seen_records = set()
            
            for metric_data in metrics_data:
                record_key = (
                    metric_data.get("date"),
                    metric_data.get("trafficSource", "unknown")
                )
                
                # Skip if we've already seen this record in this sync
                if record_key in seen_records:
                    logger.debug(f"Skipping duplicate GA4 record: {record_key}")
                    continue
                
                seen_records.add(record_key)
                
                ga_record = GAData(
                    id=uuid.uuid4(),
                    project_id=project_uuid,
                    sessions=int(float(metric_data.get("sessions", 0))),
                    users=int(float(metric_data.get("users", 0))),
                    new_users=int(float(metric_data.get("newUsers", 0))),
                    pageviews=int(float(metric_data.get("pageviews", 0))),
                    bounce_rate=float(metric_data.get("bounceRate", 0)),
                    conversions=int(float(metric_data.get("conversions", 0))),
                    traffic_source=metric_data.get("trafficSource", "unknown"),
                    date=metric_data.get("date"),
                )
                records_to_insert.append(ga_record)
            
            # Add all records to session
            for record in records_to_insert:
                db_session.add(record)
            
            # Commit transaction
            await db_session.commit()
            logger.info(f"Successfully stored {len(records_to_insert)} GA4 records to database")
            
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to store GA4 data to database: {e}")
            raise ValueError(f"Database persistence failed: {e}")
    
    return {
        "property_id": property_id,
        "metrics": metrics_data,
        "metric_count": len(metrics_data),
        "summary": {
            "total_sessions": int(total_sessions),
            "total_users": int(total_users),
            "total_conversions": int(total_conversions),
            "avg_bounce_rate": round(avg_bounce_rate, 4),
            "conversion_rate": round(total_conversions / total_sessions * 100, 2) if total_sessions > 0 else 0,
        },
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
