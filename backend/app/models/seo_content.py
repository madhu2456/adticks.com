"""
AdTicks — Content analysis models (keywords density, readability, images, etc).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentAnalysis(Base):
    """Content analysis for pages including keyword density and readability."""

    __tablename__ = "content_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    
    # Word count metrics
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    unique_words: Mapped[int] = mapped_column(Integer, default=0)
    paragraphs: Mapped[int] = mapped_column(Integer, default=0)
    sentences: Mapped[int] = mapped_column(Integer, default=0)
    
    # Readability metrics
    reading_level: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "Grade 8"
    flesch_reading_ease: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    flesch_kincaid_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Keyword metrics
    primary_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keyword_density: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    keyword_frequency: Mapped[dict[str, int]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Heading structure
    heading_structure: Mapped[list[dict[str, str | int]]] = mapped_column(JSON, default=list, nullable=False)
    h2_tags: Mapped[int] = mapped_column(Integer, default=0)
    h3_tags: Mapped[int] = mapped_column(Integer, default=0)
    h4_tags: Mapped[int] = mapped_column(Integer, default=0)
    
    # Lists
    ordered_lists: Mapped[int] = mapped_column(Integer, default=0)
    unordered_lists: Mapped[int] = mapped_column(Integer, default=0)
    
    # Text formatting
    bold_count: Mapped[int] = mapped_column(Integer, default=0)
    italic_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Issues and recommendations
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    
    score: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="content_analysis")


class ImageAudit(Base):
    """Image optimization audit."""

    __tablename__ = "image_audit"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    has_alt: Mapped[bool] = mapped_column(Boolean, default=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dimensions: Mapped[dict[str, int]] = mapped_column(JSON, default=dict, nullable=False)  # width, height
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # jpg, png, webp, etc
    is_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    optimization_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="image_audits")


class DuplicateContent(Base):
    """Duplicate content detection across pages."""

    __tablename__ = "duplicate_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    duplicate_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    similarity_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    duplicate_type: Mapped[str] = mapped_column(String(32))  # exact, near, canonical
    primary_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    hash_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="duplicate_content")


class SEORecommendation(Base):
    """AI-powered SEO recommendations."""

    __tablename__ = "seo_recommendation"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_type: Mapped[str] = mapped_column(String(100))  # technical, content, backlink, etc
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(32))  # critical, high, medium, low
    estimated_impact: Mapped[str] = mapped_column(String(32))  # low, medium, high
    affected_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    implementation_steps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    resources_needed: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    estimated_effort: Mapped[str | None] = mapped_column(String(50), nullable=True)  # hours, days
    quick_win: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, in_progress, done
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="seo_recommendations")


class URLRedirect(Base):
    """URL redirect management."""

    __tablename__ = "url_redirect"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer)  # 301, 302, 307, 308
    is_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    chain_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_broken: Mapped[bool] = mapped_column(Boolean, default=False)
    redirect_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="url_redirects")


class BrokenLink(Base):
    """Broken link detection."""

    __tablename__ = "broken_link"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    broken_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer)
    link_type: Mapped[str] = mapped_column(String(32))  # internal, external
    anchor_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_detected: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, fixed
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="broken_links")
