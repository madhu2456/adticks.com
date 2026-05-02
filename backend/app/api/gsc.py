"""AdTicks Google Search Console router."""
import logging
import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached
from app.models.gsc import GSCData
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.gsc import GSCDataResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/gsc", tags=["gsc"])

_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/webmasters" # Required for adding/verifying sites
]


async def _assert_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/auth")
async def gsc_auth(current_user: User = Depends(get_current_user)):
    """
    Retrieve the Google OAuth2 authorization URL for GSC access.
    
    Generates a Google OAuth2 consent URL that allows users to authenticate and grant
    the application permission to access their Google Search Console data. The user should
    visit the returned URL to authorize access.
    
    **Authentication:** Required (Bearer token)
    
    **Returns:**
    - **auth_url**: Google OAuth2 authorization URL for the user to visit
    - **state**: State parameter for session tracking
    
    **Responses:**
    - 200 OK: Authorization URL generated successfully
    - 401 Unauthorized: Missing or invalid authentication
    
    **Example:** Redirect user to the returned auth_url to begin OAuth flow
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the backend environment."
        )

    from google_auth_oauthlib.flow import Flow
    import json
    import base64
    from app.core.caching import get_redis_client
    
    # We include all possible URIs in the flow config to be safe
    redirect_uris = [
        settings.GOOGLE_REDIRECT_URI,
        f"{settings.BASE_URL.rstrip('/')}/api/gsc/callback",
        f"{settings.BASE_URL.rstrip('/')}/gsc-callback"
    ]
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": list(set(redirect_uris)), # Unique URIs
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    # Google now requires PKCE - enable code_challenge (automatically done by flow)
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
    
    # Store code_verifier in Redis with state as key (expires in 15 minutes)
    redis_client = await get_redis_client()
    if redis_client and flow.code_verifier:
        try:
            cache_key = f"gsc_pkce:{state}"
            await redis_client.setex(cache_key, 900, flow.code_verifier)
            logger.debug(f"Stored PKCE code_verifier in Redis for state: {state}")
        except Exception as e:
            logger.warning(f"Failed to store code_verifier in Redis: {e}")
    
    # Also send pkce_state for backward compatibility (in case Redis is unavailable)
    pkce_data = {
        "code_verifier": flow.code_verifier,
        "original_state": state,
    }
    pkce_state = base64.urlsafe_b64encode(json.dumps(pkce_data).encode()).decode()
    
    logger.info(f"Generated GSC auth URL with redirect_uri: {flow.redirect_uri}, PKCE enabled")
    return {
        "auth_url": auth_url,
        "state": state,
        "pkce_state": pkce_state  # Frontend needs to store this to pass back
    }


@router.get("/callback")
async def gsc_legacy_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """
    Legacy GET callback handler.
    
    If Google redirects here (due to old configuration), we redirect the user
    to the frontend /gsc-callback route which will handle the code properly.
    """
    params = []
    if code: params.append(f"code={code}")
    if state: params.append(f"state={state}")
    if error: params.append(f"error={error}")
    
    query_string = "&".join(params)
    frontend_url = f"{settings.BASE_URL.rstrip('/')}/gsc-callback?{query_string}"
    
    logger.info(f"Redirecting legacy GSC callback to frontend: {frontend_url}")
    return RedirectResponse(url=frontend_url)


class GSCAuthComplete(BaseModel):
    code: str
    state: str | None = None  # Google's state parameter for retrieving PKCE verifier
    pkce_state: str | None = None  # PKCE state with code_verifier (fallback)

@router.post("/complete")
async def complete_gsc_auth(
    payload: GSCAuthComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Complete the Google OAuth2 flow using the authorization code.
    
    The frontend should call this endpoint after receiving the 'code' from Google's
    redirect. This request must be authenticated with the user's AdTicks JWT.
    
    Required:
    - code: The authorization code from Google
    - state: The state parameter from Google's redirect (for PKCE retrieval)
    - pkce_state: The PKCE state returned from /auth endpoint (fallback)
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured."
        )

    from google_auth_oauthlib.flow import Flow
    from datetime import datetime, timezone, timedelta
    import json
    import base64
    from app.core.caching import get_redis_client
    
    # Try to get code_verifier from Redis first (using state), then fallback to pkce_state
    code_verifier = None
    
    # Primary method: Retrieve from Redis using state
    if payload.state:
        redis_client = await get_redis_client()
        if redis_client:
            try:
                cache_key = f"gsc_pkce:{payload.state}"
                code_verifier = await redis_client.get(cache_key)
                if code_verifier:
                    await redis_client.delete(cache_key)  # Clean up after use
                    logger.debug(f"Retrieved PKCE code_verifier from Redis for state: {payload.state}")
            except Exception as e:
                logger.warning(f"Failed to retrieve code_verifier from Redis: {e}")
    
    # Fallback method: Decode from pkce_state
    if not code_verifier and payload.pkce_state:
        try:
            pkce_data = json.loads(base64.urlsafe_b64decode(payload.pkce_state.encode()))
            code_verifier = pkce_data.get("code_verifier")
            if code_verifier:
                logger.debug(f"Retrieved PKCE code_verifier from pkce_state")
        except Exception as e:
            logger.warning(f"Failed to decode PKCE state: {e}")
    
    # We try both the current redirect URI and the legacy one to be robust
    # Note: Google determines which one is "correct" based on what was passed to /auth
    redirect_uris = [
        settings.GOOGLE_REDIRECT_URI,
        f"{settings.BASE_URL.rstrip('/')}/api/gsc/callback",
        f"{settings.BASE_URL.rstrip('/')}/gsc-callback"
    ]
    
    # Filter unique URIs to avoid redundant calls
    unique_uris = []
    for uri in redirect_uris:
        if uri not in unique_uris:
            unique_uris.append(uri)
    
    last_error = None
    for r_uri in unique_uris:
        logger.info(f"Attempting GSC token exchange with redirect_uri: {r_uri}")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": unique_uris,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=_SCOPES,
        )
        flow.redirect_uri = r_uri
        
        try:
            # If we have a code_verifier from PKCE, set it on the flow
            if code_verifier:
                flow.code_verifier = code_verifier
                logger.info(f"Using stored code_verifier for PKCE")
            
            flow.fetch_token(code=payload.code)
            token = flow.credentials
            
            # If we reached here, exchange was successful
            current_user.gsc_access_token = token.token
            if token.refresh_token:
                current_user.gsc_refresh_token = token.refresh_token
            
            if token.expiry:
                if hasattr(token.expiry, "replace"):
                    current_user.gsc_token_expiry = token.expiry.replace(tzinfo=timezone.utc)
                else:
                    current_user.gsc_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=3600)
            
            db.add(current_user)
            await db.commit()
            
            logger.info(f"GSC Auth successful using redirect_uri: {r_uri}")
            return {"status": "authorized", "message": "Google Search Console connected successfully"}
            
        except Exception as e:
            logger.warning(f"Failed to fetch Google token with {r_uri}: {str(e)}")
            last_error = e
            # If error is invalid_grant, code is dead, no point in retrying other URIs
            if "invalid_grant" in str(e).lower():
                break
    
    # If all fail
    logger.error(f"GSC Auth failed for all redirect URIs. Last error: {last_error}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Failed to exchange authorization code for tokens. Error: {str(last_error)}"
    )


@router.get("/properties")
async def list_gsc_properties(
    current_user: User = Depends(get_current_user),
):
    """List all Google Search Console properties available to the user."""
    if not current_user.gsc_access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GSC not connected")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=current_user.gsc_access_token,
        refresh_token=current_user.gsc_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    try:
        service = build("webmasters", "v3", credentials=creds)
        site_list = service.sites().list().execute()
        return site_list.get("siteEntry", [])
    except Exception as e:
        logger.error(f"Failed to fetch GSC properties: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch GSC properties")


@router.post("/connect/{project_id}")
async def connect_gsc_property(
    project_id: UUID,
    property_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link a specific GSC property to a project."""
    project = await _assert_owner(project_id, current_user, db)
    
    project.gsc_connected = True
    project.gsc_property_url = property_url
    
    db.add(project)
    await db.commit()
    
    return {"status": "success", "message": f"Connected to {property_url}"}


@router.get("/queries/{project_id}", response_model=PaginatedResponse[GSCDataResponse])
@cached(ttl=3600)  # 1 hour
async def get_gsc_queries(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve stored Google Search Console query performance data for a project with pagination.
    
    Returns paginated list of search queries from GSC including metrics like impressions,
    clicks, average position, and CTR. Data is synced from Google Search Console and
    cached for 1 hour. Results are sorted by most recent date first.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return per page (default: 50, max: 500)
    
    **Returns:**
    - Paginated response with:
      - **data**: Array of GSC query objects with query, date, impressions, clicks, position, ctr
      - **total**: Total number of query records
      - **skip**: Number of items skipped
      - **limit**: Number of items returned
      - **has_more**: Whether more items are available
    
    **Responses:**
    - 200 OK: Query data returned successfully (may be cached)
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Note:** GSC data is synced via /gsc/sync endpoint. Ensure user has authorized GSC access
    """
    await _assert_owner(project_id, current_user, db)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(GSCData.id)).where(GSCData.project_id == project_id)
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    result = await db.execute(
        select(GSCData)
        .where(GSCData.project_id == project_id)
        .order_by(GSCData.date.desc())
        .offset(skip)
        .limit(limit)
    )
    gsc_data = result.scalars().all()
    
    return PaginatedResponse.create(
        data=gsc_data,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/sync/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def sync_gsc(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an async Google Search Console data sync for a project.
    
    Starts a background job that pulls latest search query performance data from the
    user's authorized Google Search Console account. Fetches impressions, clicks, CTR,
    average position, and other metrics for all tracked properties and queries.
    Results are stored and available via /gsc/queries endpoint.
    
    **Authentication:** Required (Bearer token)
    
    **Path parameters:**
    - **project_id**: UUID of the project (required)
    
    **Returns:**
    - **status**: Task status ("queued")
    - **task_id**: Celery task ID for tracking async execution
    
    **Responses:**
    - 202 Accepted: Sync queued successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 404 Not Found: Project not found or not owned by user
    
    **Note:** Requires prior GSC authorization via /gsc/auth endpoint
    """
    project = await _assert_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import sync_gsc_data
        task = sync_gsc_data.delay(str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}
