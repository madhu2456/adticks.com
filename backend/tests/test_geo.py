"""
GEO Module Backend Tests.

Comprehensive test suite for locations, local ranks, reviews, and citations.
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geo import Citation, Location, LocalRank, Review, ReviewSummary
from app.models.project import Project
from app.models.user import User


# ============================================================================
# Location Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_location(
    client: AsyncClient,
    test_user: User,
    test_project: Project,
):
    """Test creating a new location."""
    response = await client.post(
        f"/api/geo/projects/{test_project.id}/locations",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "name": "New York Branch",
            "address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
            "phone": "+1-212-555-0123",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New York Branch"
    assert data["city"] == "New York"
    assert data["phone"] == "+1-212-555-0123"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_locations(
    client: AsyncClient,
    test_user: User,
    test_project: Project,
    db_session: AsyncSession,
):
    """Test listing locations."""
    # Create multiple locations
    for i in range(5):
        location = Location(
            project_id=test_project.id,
            name=f"Location {i}",
            address=f"{i} Main St",
            city="City",
            state="ST",
            country="USA",
        )
        db_session.add(location)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/projects/{test_project.id}/locations",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["data"]) == 5
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_list_locations_pagination(
    client: AsyncClient,
    test_user: User,
    test_project: Project,
    db_session: AsyncSession,
):
    """Test location pagination."""
    # Create 100 locations
    for i in range(100):
        location = Location(
            project_id=test_project.id,
            name=f"Location {i}",
            address=f"{i} Main St",
            city="City",
            state="ST",
            country="USA",
        )
        db_session.add(location)
    await db_session.commit()

    # Test pagination
    response = await client.get(
        f"/api/geo/projects/{test_project.id}/locations?skip=0&limit=30",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 30
    assert data["total"] == 100
    assert data["has_more"] is True

    # Test second page
    response = await client.get(
        f"/api/geo/projects/{test_project.id}/locations?skip=30&limit=30",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 30
    assert data["skip"] == 30


@pytest.mark.asyncio
async def test_get_location(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test getting a specific location."""
    response = await client.get(
        f"/api/geo/locations/{test_location.id}",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_location.id)
    assert data["name"] == test_location.name
    assert data["city"] == test_location.city


@pytest.mark.asyncio
async def test_update_location(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test updating a location."""
    response = await client.put(
        f"/api/geo/locations/{test_location.id}",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "phone": "+1-555-0999",
            "city": "Los Angeles",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1-555-0999"
    assert data["city"] == "Los Angeles"
    assert data["name"] == test_location.name


@pytest.mark.asyncio
async def test_delete_location(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test deleting a location."""
    response = await client.delete(
        f"/api/geo/locations/{test_location.id}",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/geo/locations/{test_location.id}",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_location_authorization(
    client: AsyncClient,
    test_user: User,
    test_project: Project,
    db_session: AsyncSession,
):
    """Test that users can't access other users' locations."""
    # Create another user
    other_user = User(
        id=uuid.uuid4(),
        email="other@adticks.com",
        hashed_password="hashed",
        full_name="Other User",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    # Create location for test_user's project
    location = Location(
        project_id=test_project.id,
        name="Test Location",
        address="123 St",
        city="City",
        state="ST",
        country="USA",
    )
    db_session.add(location)
    await db_session.commit()

    # Try to access with other_user
    response = await client.get(
        f"/api/geo/locations/{location.id}",
        headers={"Authorization": f"Bearer {other_user.token}"},
    )
    assert response.status_code == 403


# ============================================================================
# Local Rank Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_local_ranks(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test retrieving local ranks."""
    # Create ranks
    for i in range(5):
        rank = LocalRank(
            location_id=test_location.id,
            keyword=f"keyword {i}",
            google_maps_rank=i + 1,
            local_pack_position=i + 1,
            local_search_rank=i + 1,
            device="desktop",
        )
        db_session.add(rank)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/locations/{test_location.id}/ranks",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["data"]) == 5


@pytest.mark.asyncio
async def test_get_local_ranks_with_filters(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test local ranks with filtering."""
    # Create ranks
    for i in range(3):
        rank = LocalRank(
            location_id=test_location.id,
            keyword="pizza near me",
            device="desktop",
        )
        db_session.add(rank)

    for i in range(2):
        rank = LocalRank(
            location_id=test_location.id,
            keyword="pizza near me",
            device="mobile",
        )
        db_session.add(rank)
    await db_session.commit()

    # Filter by device
    response = await client.get(
        f"/api/geo/locations/{test_location.id}/ranks?device=mobile",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    # All have same keyword
    for rank in data["data"]:
        assert rank["keyword"] == "pizza near me"


# ============================================================================
# Review Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_review(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test creating a review."""
    response = await client.post(
        f"/api/geo/locations/{test_location.id}/reviews",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "source": "google",
            "rating": 4.5,
            "author": "John Doe",
            "text": "Great service!",
            "sentiment_score": 0.85,
            "sentiment_label": "positive",
            "verified": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 4.5
    assert data["author"] == "John Doe"
    assert data["sentiment_label"] == "positive"


@pytest.mark.asyncio
async def test_get_reviews(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test retrieving reviews."""
    # Create reviews
    for i in range(3):
        review = Review(
            location_id=test_location.id,
            source="google",
            rating=float(i + 3),
            author=f"Author {i}",
        )
        db_session.add(review)

    for i in range(2):
        review = Review(
            location_id=test_location.id,
            source="yelp",
            rating=4.0,
            author=f"Yelp Author {i}",
        )
        db_session.add(review)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/locations/{test_location.id}/reviews",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_get_reviews_with_rating_filter(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test reviews with rating filters."""
    # Create reviews
    for rating in [5.0, 4.0, 3.0, 2.0, 1.0]:
        review = Review(
            location_id=test_location.id,
            source="google",
            rating=rating,
            author="Test",
        )
        db_session.add(review)
    await db_session.commit()

    # Get high ratings only
    response = await client.get(
        f"/api/geo/locations/{test_location.id}/reviews?min_rating=4.0",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    for review in data["data"]:
        assert review["rating"] >= 4.0


@pytest.mark.asyncio
async def test_get_review_summary(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test getting review summary."""
    # Create summary
    summary = ReviewSummary(
        location_id=test_location.id,
        total_reviews=50,
        average_rating=4.5,
        five_star=30,
        four_star=15,
        three_star=5,
        positive_count=45,
        negative_count=5,
        google_reviews=30,
        yelp_reviews=20,
    )
    db_session.add(summary)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/locations/{test_location.id}/reviews/summary",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_reviews"] == 50
    assert data["average_rating"] == 4.5
    assert data["five_star"] == 30
    assert data["google_reviews"] == 30


# ============================================================================
# Citation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_citation(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test creating a citation."""
    response = await client.post(
        f"/api/geo/locations/{test_location.id}/citations",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "source_name": "Google Business",
            "url": "https://business.google.com/123",
            "business_name": test_location.name,
            "citation_address": test_location.address,
            "citation_phone": test_location.phone,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_name"] == "Google Business"
    assert data["name_match"] is True
    assert data["address_match"] is True
    assert data["consistency_score"] > 0.66


@pytest.mark.asyncio
async def test_get_citations(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test retrieving citations."""
    # Create citations
    for i in range(5):
        citation = Citation(
            location_id=test_location.id,
            source_name=f"Directory {i}",
            url=f"https://directory{i}.com",
            consistency_score=0.8,
        )
        db_session.add(citation)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/locations/{test_location.id}/citations",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_nap_consistency_check(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
    db_session: AsyncSession,
):
    """Test NAP consistency check."""
    # Create citations with mixed consistency
    # Perfect match
    cit1 = Citation(
        location_id=test_location.id,
        source_name="Directory 1",
        url="https://dir1.com",
        business_name=test_location.name,
        citation_address=test_location.address,
        citation_phone=test_location.phone,
        name_match=True,
        address_match=True,
        phone_match=True,
        consistency_score=1.0,
    )
    db_session.add(cit1)

    # Partial match
    cit2 = Citation(
        location_id=test_location.id,
        source_name="Directory 2",
        url="https://dir2.com",
        business_name=test_location.name,
        citation_address="Wrong Address",
        citation_phone=test_location.phone,
        name_match=True,
        address_match=False,
        phone_match=True,
        consistency_score=0.66,
    )
    db_session.add(cit2)

    # No match
    cit3 = Citation(
        location_id=test_location.id,
        source_name="Directory 3",
        url="https://dir3.com",
        business_name="Wrong Name",
        citation_address="Wrong Address",
        citation_phone="9999999999",
        name_match=False,
        address_match=False,
        phone_match=False,
        consistency_score=0.0,
    )
    db_session.add(cit3)
    await db_session.commit()

    response = await client.get(
        f"/api/geo/locations/{test_location.id}/citations/nap-check",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_citations"] == 3
    assert data["consistent_citations"] == 1
    assert data["consistency_percentage"] > 0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that unauthorized users can't access GEO endpoints."""
    response = await client.get("/api/geo/projects/123/locations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_location_id(
    client: AsyncClient,
    test_user: User,
):
    """Test accessing non-existent location."""
    response = await client.get(
        f"/api/geo/locations/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_project_id(
    client: AsyncClient,
    test_user: User,
):
    """Test accessing non-existent project."""
    response = await client.get(
        f"/api/geo/projects/{uuid.uuid4()}/locations",
        headers={"Authorization": f"Bearer {test_user.token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_location_invalid_data(
    client: AsyncClient,
    test_user: User,
    test_project: Project,
):
    """Test creating location with invalid data."""
    response = await client.post(
        f"/api/geo/projects/{test_project.id}/locations",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "name": "",  # Empty name
            "address": "123 St",
            "city": "City",
            "state": "ST",
            "country": "USA",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_rating(
    client: AsyncClient,
    test_user: User,
    test_location: Location,
):
    """Test creating review with invalid rating."""
    response = await client.post(
        f"/api/geo/locations/{test_location.id}/reviews",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "source": "google",
            "rating": 10.0,  # Invalid: > 5
            "author": "Test",
        },
    )
    assert response.status_code == 422
