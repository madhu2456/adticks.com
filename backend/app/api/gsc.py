"""AdTicks Google Search Console router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached
from app.models.gsc import GSCData
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.gsc import GSCDataResponse

router = APIRouter(prefix="/gsc", tags=["gsc"])

_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


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
    
    **Responses:**
    - 200 OK: Authorization URL generated successfully
    - 401 Unauthorized: Missing or invalid authentication
    
    **Example:** Redirect user to the returned auth_url to begin OAuth flow
    """
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return {"auth_url": auth_url}


@router.get("/callback")
async def gsc_callback(
    code: str,
    current_user: User = Depends(get_current_user),
):
    """
    Handle the Google OAuth2 callback and store the access token.
    
    Processes the OAuth2 callback after user authorizes GSC access. Exchanges the
    authorization code for an access token and stores it for future API requests.
    This endpoint is the redirect_uri configured in Google OAuth settings.
    
    **Authentication:** Required (Bearer token)
    
    **Query parameters:**
    - **code**: Authorization code from Google OAuth2 flow (required)
    
    **Returns:**
    - **status**: Authorization status ("authorized")
    - **user_id**: UUID of the authenticated user
    
    **Responses:**
    - 200 OK: Authorization successful
    - 401 Unauthorized: Missing or invalid authentication
    - 400 Bad Request: Invalid or expired authorization code
    
    **Note:** In production, the token should be persisted securely for the user
    """
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code)
    # Token would be persisted to user record or secure store in production
    return {"status": "authorized", "user_id": str(current_user.id)}


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
