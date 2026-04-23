"""
AdTicks — GEO Module Schemas.

Pydantic models for GEO module API requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Location Schemas
class LocationCreate(BaseModel):
    """Request to create a new location."""

    name: str = Field(..., min_length=1, max_length=255, description="Location name")
    address: str = Field(
        ..., min_length=1, max_length=512, description="Street address"
    )
    city: str = Field(..., min_length=1, max_length=128, description="City")
    state: str = Field(..., min_length=1, max_length=128, description="State/Province")
    country: str = Field(..., min_length=1, max_length=128, description="Country")
    postal_code: Optional[str] = Field(None, max_length=32, description="Postal code")
    phone: Optional[str] = Field(None, max_length=32, description="Phone number")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    google_business_id: Optional[str] = Field(
        None, max_length=255, description="Google Business Profile ID"
    )


class LocationUpdate(BaseModel):
    """Request to update a location."""

    name: Optional[str] = Field(None, max_length=255, description="Location name")
    address: Optional[str] = Field(None, max_length=512, description="Street address")
    city: Optional[str] = Field(None, max_length=128, description="City")
    state: Optional[str] = Field(None, max_length=128, description="State/Province")
    country: Optional[str] = Field(None, max_length=128, description="Country")
    postal_code: Optional[str] = Field(None, max_length=32, description="Postal code")
    phone: Optional[str] = Field(None, max_length=32, description="Phone number")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    google_business_id: Optional[str] = Field(
        None, max_length=255, description="Google Business Profile ID"
    )


class LocationResponse(BaseModel):
    """Location response model."""

    id: UUID = Field(description="Location ID")
    project_id: UUID = Field(description="Project ID")
    name: str = Field(description="Location name")
    address: str = Field(description="Street address")
    city: str = Field(description="City")
    state: str = Field(description="State/Province")
    country: str = Field(description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    phone: Optional[str] = Field(None, description="Phone number")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    google_business_id: Optional[str] = Field(
        None, description="Google Business Profile ID"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# Local Rank Schemas
class LocalRankResponse(BaseModel):
    """Local rank response model."""

    id: UUID = Field(description="Local rank ID")
    location_id: UUID = Field(description="Location ID")
    keyword_id: Optional[UUID] = Field(None, description="Keyword ID")
    keyword: str = Field(description="Keyword term")
    google_maps_rank: Optional[int] = Field(None, description="Google Maps position")
    local_pack_position: Optional[int] = Field(None, description="Local pack position")
    local_search_rank: Optional[int] = Field(None, description="Local search rank")
    device: str = Field(description="Device type (desktop/mobile)")
    timestamp: datetime = Field(description="Rank timestamp")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# Review Schemas
class ReviewCreate(BaseModel):
    """Request to create a review record."""

    source: str = Field(..., max_length=128, description="Review source")
    external_id: Optional[str] = Field(None, max_length=255, description="External ID")
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating (1-5)")
    text: Optional[str] = Field(None, description="Review text")
    author: str = Field(..., max_length=255, description="Author name")
    sentiment_score: Optional[float] = Field(
        None, ge=-1.0, le=1.0, description="Sentiment score"
    )
    sentiment_label: Optional[str] = Field(
        None, description="Sentiment label (positive/negative/neutral)"
    )
    review_date: Optional[datetime] = Field(None, description="Review date")
    verified: bool = Field(default=False, description="Is verified review")


class ReviewResponse(BaseModel):
    """Review response model."""

    id: UUID = Field(description="Review ID")
    location_id: UUID = Field(description="Location ID")
    source: str = Field(description="Review source")
    external_id: Optional[str] = Field(None, description="External ID")
    rating: float = Field(description="Rating (1-5)")
    text: Optional[str] = Field(None, description="Review text")
    author: str = Field(description="Author name")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    sentiment_label: Optional[str] = Field(None, description="Sentiment label")
    review_date: Optional[datetime] = Field(None, description="Review date")
    verified: bool = Field(description="Is verified review")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# Review Summary Schemas
class ReviewSummaryResponse(BaseModel):
    """Review summary response model."""

    id: UUID = Field(description="Summary ID")
    location_id: UUID = Field(description="Location ID")
    total_reviews: int = Field(description="Total number of reviews")
    average_rating: Optional[float] = Field(None, description="Average rating")
    five_star: int = Field(description="5-star reviews count")
    four_star: int = Field(description="4-star reviews count")
    three_star: int = Field(description="3-star reviews count")
    two_star: int = Field(description="2-star reviews count")
    one_star: int = Field(description="1-star reviews count")
    positive_count: int = Field(description="Positive sentiment count")
    negative_count: int = Field(description="Negative sentiment count")
    neutral_count: int = Field(description="Neutral sentiment count")
    google_reviews: int = Field(description="Google reviews count")
    yelp_reviews: int = Field(description="Yelp reviews count")
    facebook_reviews: int = Field(description="Facebook reviews count")
    last_updated: datetime = Field(description="Last update timestamp")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# Citation Schemas
class CitationCreate(BaseModel):
    """Request to create a citation."""

    source_name: str = Field(..., max_length=255, description="Citation source")
    url: str = Field(..., max_length=2048, description="Citation URL")
    business_name: Optional[str] = Field(None, max_length=255, description="Business name in citation")
    citation_address: Optional[str] = Field(
        None, max_length=512, description="Address in citation"
    )
    citation_phone: Optional[str] = Field(None, max_length=32, description="Phone in citation")


class CitationResponse(BaseModel):
    """Citation response model."""

    id: UUID = Field(description="Citation ID")
    location_id: UUID = Field(description="Location ID")
    source_name: str = Field(description="Citation source")
    url: str = Field(description="Citation URL")
    consistency_score: float = Field(description="NAP consistency score (0-1)")
    name_match: bool = Field(description="Business name matches")
    address_match: bool = Field(description="Address matches")
    phone_match: bool = Field(description="Phone matches")
    business_name: Optional[str] = Field(None, description="Business name in citation")
    citation_address: Optional[str] = Field(None, description="Address in citation")
    citation_phone: Optional[str] = Field(None, description="Phone in citation")
    last_verified: Optional[datetime] = Field(None, description="Last verification time")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class NAPCheckResponse(BaseModel):
    """NAP (Name, Address, Phone) consistency check response."""

    location_id: UUID = Field(description="Location ID")
    total_citations: int = Field(description="Total citations")
    consistent_citations: int = Field(description="Citations with full NAP match")
    consistency_percentage: float = Field(description="Percentage of consistent citations")
    issues: list[dict] = Field(description="List of NAP inconsistencies")

    model_config = ConfigDict(from_attributes=True)
