"""
AdTicks — GEO Module Models.

Database models for location-based tracking including:
- Locations: Business locations for GEO tracking
- Local Ranks: Google Maps and local search rankings
- Reviews: Customer reviews and ratings
- Review Summary: Aggregated review statistics
- Citations: Business citations and NAP consistency
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Location(Base):
    """A business location tracked for local SEO visibility."""

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    google_business_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="locations")
    local_ranks = relationship(
        "LocalRank", back_populates="location", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="location", cascade="all, delete-orphan"
    )
    review_summary = relationship(
        "ReviewSummary",
        back_populates="location",
        cascade="all, delete-orphan",
        uselist=False,
    )
    citations = relationship(
        "Citation", back_populates="location", cascade="all, delete-orphan"
    )


class LocalRank(Base):
    """Google Maps and local search ranking data for a location."""

    __tablename__ = "local_ranks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    google_maps_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    local_pack_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    local_search_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device: Mapped[str] = mapped_column(String(32), default="desktop", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="local_ranks")


class Review(Base):
    """Customer review for a location."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(128), nullable=False)  # google, yelp, etc
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_label: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # positive, negative, neutral
    review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="reviews")


class ReviewSummary(Base):
    """Aggregated review statistics for a location."""

    __tablename__ = "review_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    five_star: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    four_star: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    three_star: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    two_star: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    one_star: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    positive_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negative_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    google_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yelp_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    facebook_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="review_summary")


class Citation(Base):
    """Business citation in online directories."""

    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    name_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    address_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    citation_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    citation_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_verified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="citations")
