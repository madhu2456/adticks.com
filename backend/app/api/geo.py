"""
AdTicks GEO Module API Routes.

Endpoints for managing locations, local rankings, reviews, and citations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.caching import invalidate_cache
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.geo import Citation, Location, LocalRank, Review, ReviewSummary
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.geo import (
    CitationCreate,
    CitationResponse,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LocalRankResponse,
    NAPCheckResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewSummaryResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/geo", tags=["geo"])


# ============================================================================
# Utility Functions
# ============================================================================


async def _assert_project_owner(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """Verify user owns the project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


async def _assert_location_exists(
    location_id: UUID, user: User, db: AsyncSession
) -> Location:
    """Verify location exists and user owns parent project."""
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )

    # Verify ownership
    project_result = await db.execute(
        select(Project).where(
            Project.id == location.project_id, Project.user_id == user.id
        )
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return location


# ============================================================================
# Location Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    project_id: UUID,
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """
    Add a new location to a project.

    Creates a new business location for local SEO tracking within a project.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **project_id**: UUID of the project

    **Request body:**
    - **name**: Business location name
    - **address**: Street address
    - **city**: City name
    - **state**: State/Province
    - **country**: Country
    - **postal_code**: Optional postal code
    - **phone**: Optional phone number
    - **latitude**: Optional latitude
    - **longitude**: Optional longitude
    - **google_business_id**: Optional Google Business Profile ID

    **Returns:**
    - Location object with id, timestamps, and all details

    **Responses:**
    - 201 Created: Location created successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Project not found
    - 422 Unprocessable Entity: Invalid request body
    """
    await _assert_project_owner(project_id, current_user, db)

    location = Location(
        project_id=project_id,
        name=payload.name,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        phone=payload.phone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        google_business_id=payload.google_business_id,
    )

    db.add(location)
    await db.commit()
    await db.refresh(location)

    logger.info(
        "location_created",
        extra={
            "location_id": str(location.id),
            "project_id": str(project_id),
            "user_id": str(current_user.id),
        },
    )

    # Invalidate cache
    await invalidate_cache(f"cache:locations:{project_id}:*")

    return LocationResponse.model_validate(location)


@router.get(
    "/projects/{project_id}/locations",
    response_model=PaginatedResponse[LocationResponse],
)
async def list_locations(
    project_id: UUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[LocationResponse]:
    """
    List all locations for a project.

    Retrieves paginated list of business locations in a project with optional caching.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **project_id**: UUID of the project

    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return (default: 50, max: 500)

    **Returns:**
    - Paginated response with data, total, skip, limit, has_more

    **Responses:**
    - 200 OK: List retrieved successfully
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Project not found
    """
    await _assert_project_owner(project_id, current_user, db)

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Location).where(Location.project_id == project_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        select(Location)
        .where(Location.project_id == project_id)
        .order_by(Location.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    locations = result.scalars().all()

    return PaginatedResponse.create(
        data=[LocationResponse.model_validate(loc) for loc in locations],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """
    Get a specific location by ID.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Returns:**
    - Location object with all details

    **Responses:**
    - 200 OK: Location retrieved
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    location = await _assert_location_exists(location_id, current_user, db)
    return LocationResponse.model_validate(location)


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    payload: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LocationResponse:
    """
    Update a location.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Request body:**
    - All fields optional, only provided fields are updated

    **Returns:**
    - Updated location object

    **Responses:**
    - 200 OK: Location updated
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    location = await _assert_location_exists(location_id, current_user, db)

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)

    await db.commit()
    await db.refresh(location)

    logger.info(
        "location_updated",
        extra={
            "location_id": str(location_id),
            "project_id": str(location.project_id),
            "user_id": str(current_user.id),
        },
    )

    # Invalidate cache
    await invalidate_cache(f"cache:locations:{location.project_id}:*")

    return LocationResponse.model_validate(location)


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a location.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Responses:**
    - 204 No Content: Location deleted
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    location = await _assert_location_exists(location_id, current_user, db)
    project_id = location.project_id

    await db.delete(location)
    await db.commit()

    logger.info(
        "location_deleted",
        extra={
            "location_id": str(location_id),
            "project_id": str(project_id),
            "user_id": str(current_user.id),
        },
    )

    # Invalidate cache
    await invalidate_cache(f"cache:locations:{project_id}:*")


# ============================================================================
# Local Rank Endpoints
# ============================================================================


@router.get(
    "/locations/{location_id}/ranks",
    response_model=PaginatedResponse[LocalRankResponse],
)
async def get_local_ranks(
    location_id: UUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    keyword: str | None = Query(None, description="Filter by keyword"),
    device: str | None = Query(None, description="Filter by device (desktop/mobile)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[LocalRankResponse]:
    """
    Get local rankings for a location.

    Retrieves Google Maps and local search rankings with optional filtering.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return (default: 50, max: 500)
    - **keyword**: Optional keyword filter
    - **device**: Optional device filter (desktop/mobile)

    **Returns:**
    - Paginated response with ranking data

    **Responses:**
    - 200 OK: Rankings retrieved
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    await _assert_location_exists(location_id, current_user, db)

    # Build query
    query = select(LocalRank).where(LocalRank.location_id == location_id)

    if keyword:
        query = query.where(LocalRank.keyword.ilike(f"%{keyword}%"))
    if device:
        query = query.where(LocalRank.device == device)

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(LocalRank).where(LocalRank.location_id == location_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        query.order_by(LocalRank.timestamp.desc()).offset(skip).limit(limit)
    )
    ranks = result.scalars().all()

    return PaginatedResponse.create(
        data=[LocalRankResponse.model_validate(rank) for rank in ranks],
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================================
# Review Endpoints
# ============================================================================


@router.post(
    "/locations/{location_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    location_id: UUID,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewResponse:
    """
    Add a review for a location.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Request body:**
    - Review details (source, rating, text, etc.)

    **Returns:**
    - Review object with id and timestamps

    **Responses:**
    - 201 Created: Review created
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    await _assert_location_exists(location_id, current_user, db)

    review = Review(
        location_id=location_id,
        source=payload.source,
        external_id=payload.external_id,
        rating=payload.rating,
        text=payload.text,
        author=payload.author,
        sentiment_score=payload.sentiment_score,
        sentiment_label=payload.sentiment_label,
        review_date=payload.review_date,
        verified=payload.verified,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    logger.info(
        "review_created",
        extra={
            "review_id": str(review.id),
            "location_id": str(location_id),
            "user_id": str(current_user.id),
        },
    )

    # Invalidate cache
    await invalidate_cache(f"cache:reviews:{location_id}:*")

    return ReviewResponse.model_validate(review)


@router.get(
    "/locations/{location_id}/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
async def get_reviews(
    location_id: UUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    source: str | None = Query(None, description="Filter by source"),
    min_rating: float | None = Query(None, ge=1.0, le=5.0, description="Minimum rating"),
    max_rating: float | None = Query(None, ge=1.0, le=5.0, description="Maximum rating"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ReviewResponse]:
    """
    Get reviews for a location.

    Retrieves paginated reviews with optional filtering by source or rating.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return (default: 50, max: 500)
    - **source**: Optional source filter (google, yelp, etc.)
    - **min_rating**: Optional minimum rating filter
    - **max_rating**: Optional maximum rating filter

    **Returns:**
    - Paginated response with review data

    **Responses:**
    - 200 OK: Reviews retrieved
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    await _assert_location_exists(location_id, current_user, db)

    # Build query
    query = select(Review).where(Review.location_id == location_id)

    if source:
        query = query.where(Review.source == source)
    if min_rating is not None:
        query = query.where(Review.rating >= min_rating)
    if max_rating is not None:
        query = query.where(Review.rating <= max_rating)

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.location_id == location_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        query.order_by(Review.review_date.desc()).offset(skip).limit(limit)
    )
    reviews = result.scalars().all()

    return PaginatedResponse.create(
        data=[ReviewResponse.model_validate(review) for review in reviews],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/locations/{location_id}/reviews/summary",
    response_model=ReviewSummaryResponse,
)
async def get_review_summary(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewSummaryResponse:
    """
    Get review statistics for a location.

    Returns aggregated review data including ratings, sentiment, and counts by source.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Returns:**
    - Review summary with statistics

    **Responses:**
    - 200 OK: Summary retrieved
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    await _assert_location_exists(location_id, current_user, db)

    # Try to fetch existing summary
    result = await db.execute(
        select(ReviewSummary).where(ReviewSummary.location_id == location_id)
    )
    summary = result.scalar_one_or_none()

    # Return empty summary if none exists
    if not summary:
        # Create empty summary
        summary = ReviewSummary(location_id=location_id)
        db.add(summary)
        await db.commit()
        await db.refresh(summary)

    return ReviewSummaryResponse.model_validate(summary)


# ============================================================================
# Citation Endpoints
# ============================================================================


@router.post(
    "/locations/{location_id}/citations",
    response_model=CitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_citation(
    location_id: UUID,
    payload: CitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CitationResponse:
    """
    Add a citation for a location.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Request body:**
    - Citation details (source, URL, NAP data)

    **Returns:**
    - Citation object with consistency score

    **Responses:**
    - 201 Created: Citation created
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    location = await _assert_location_exists(location_id, current_user, db)

    # Calculate NAP consistency
    name_match = (
        payload.business_name
        and payload.business_name.lower() == location.name.lower()
    )
    address_match = (
        payload.citation_address
        and payload.citation_address.lower() == location.address.lower()
    )
    phone_match = (
        payload.citation_phone
        and payload.citation_phone.replace("-", "").replace(" ", "")
        == (location.phone or "").replace("-", "").replace(" ", "")
    )

    match_count = sum([name_match, address_match, phone_match])
    consistency_score = match_count / 3.0

    citation = Citation(
        location_id=location_id,
        source_name=payload.source_name,
        url=payload.url,
        business_name=payload.business_name,
        citation_address=payload.citation_address,
        citation_phone=payload.citation_phone,
        name_match=name_match,
        address_match=address_match,
        phone_match=phone_match,
        consistency_score=consistency_score,
    )

    db.add(citation)
    await db.commit()
    await db.refresh(citation)

    logger.info(
        "citation_created",
        extra={
            "citation_id": str(citation.id),
            "location_id": str(location_id),
            "user_id": str(current_user.id),
        },
    )

    # Invalidate cache
    await invalidate_cache(f"cache:citations:{location_id}:*")

    return CitationResponse.model_validate(citation)


@router.get(
    "/locations/{location_id}/citations",
    response_model=PaginatedResponse[CitationResponse],
)
async def get_citations(
    location_id: UUID,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    source: str | None = Query(None, description="Filter by source"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[CitationResponse]:
    """
    Get citations for a location.

    Retrieves paginated citations with optional source filtering.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Query parameters:**
    - **skip**: Number of items to skip (default: 0)
    - **limit**: Number of items to return (default: 50, max: 500)
    - **source**: Optional source filter

    **Returns:**
    - Paginated response with citation data

    **Responses:**
    - 200 OK: Citations retrieved
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    await _assert_location_exists(location_id, current_user, db)

    # Build query
    query = select(Citation).where(Citation.location_id == location_id)

    if source:
        query = query.where(Citation.source_name.ilike(f"%{source}%"))

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Citation).where(Citation.location_id == location_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        query.order_by(Citation.created_at.desc()).offset(skip).limit(limit)
    )
    citations = result.scalars().all()

    return PaginatedResponse.create(
        data=[CitationResponse.model_validate(citation) for citation in citations],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/locations/{location_id}/citations/nap-check",
    response_model=NAPCheckResponse,
)
async def nap_consistency_check(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NAPCheckResponse:
    """
    Check NAP (Name, Address, Phone) consistency across citations.

    Analyzes all citations for a location and identifies NAP inconsistencies.

    **Authentication:** Required (Bearer token)

    **Path parameters:**
    - **location_id**: UUID of the location

    **Returns:**
    - NAP check report with consistency score and issues

    **Responses:**
    - 200 OK: Check completed
    - 401 Unauthorized: Missing or invalid authentication
    - 403 Forbidden: User does not own the project
    - 404 Not Found: Location not found
    """
    location = await _assert_location_exists(location_id, current_user, db)

    # Get all citations
    result = await db.execute(
        select(Citation).where(Citation.location_id == location_id)
    )
    citations = result.scalars().all()

    if not citations:
        return NAPCheckResponse(
            location_id=location_id,
            total_citations=0,
            consistent_citations=0,
            consistency_percentage=0.0,
            issues=[],
        )

    # Calculate consistency
    consistent = sum(
        1
        for c in citations
        if c.name_match and c.address_match and c.phone_match
    )

    issues = []
    for citation in citations:
        issue_list = []
        if not citation.name_match:
            issue_list.append(
                f"Name mismatch: Expected '{location.name}', found '{citation.business_name}'"
            )
        if not citation.address_match:
            issue_list.append(
                f"Address mismatch: Expected '{location.address}', found '{citation.citation_address}'"
            )
        if not citation.phone_match:
            issue_list.append(
                f"Phone mismatch: Expected '{location.phone}', found '{citation.citation_phone}'"
            )
        if issue_list:
            issues.append(
                {
                    "citation_id": str(citation.id),
                    "source": citation.source_name,
                    "url": citation.url,
                    "issues": issue_list,
                }
            )

    return NAPCheckResponse(
        location_id=location_id,
        total_citations=len(citations),
        consistent_citations=consistent,
        consistency_percentage=(consistent / len(citations) * 100) if citations else 0.0,
        issues=issues,
    )
