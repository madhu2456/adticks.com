"""
AdTicks — SEO Audit & Health models (meta tags, structured data, performance, crawlability).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MetaTagAudit(Base):
    """Meta tag audit for pages."""

    __tablename__ = "meta_tag_audit"

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
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_length: Mapped[int] = mapped_column(Integer, default=0)
    title_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_length: Mapped[int] = mapped_column(Integer, default=0)
    description_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    h1_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    h1_count: Mapped[int] = mapped_column(Integer, default=0)
    h1_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    og_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    og_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    twitter_card: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="meta_tag_audits")


class StructuredDataAudit(Base):
    """Structured data (JSON-LD) audit for pages."""

    __tablename__ = "structured_data_audit"

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
    schema_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    organization_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    article_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    breadcrumb_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    product_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    faq_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    local_business_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    event_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    review_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    schema_data: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    validation_errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="structured_data_audits")


class PageSpeedMetrics(Base):
    """Core Web Vitals and page speed metrics."""

    __tablename__ = "page_speed_metrics"

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
    device: Mapped[str] = mapped_column(String(32), default="desktop")  # desktop, mobile
    
    # Core Web Vitals
    lcp: Mapped[float | None] = mapped_column(Float, nullable=True)  # Largest Contentful Paint (ms)
    fid: Mapped[float | None] = mapped_column(Float, nullable=True)  # First Input Delay (ms)
    cls: Mapped[float | None] = mapped_column(Float, nullable=True)  # Cumulative Layout Shift
    ttfb: Mapped[float | None] = mapped_column(Float, nullable=True)  # Time to First Byte (ms)
    fcp: Mapped[float | None] = mapped_column(Float, nullable=True)  # First Contentful Paint (ms)
    
    # Performance scores
    performance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    accessibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_practices_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Page load info
    page_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_requests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="page_speed_metrics")


class CrawlabilityAudit(Base):
    """Crawlability and indexability audit results."""

    __tablename__ = "crawlability_audit"

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
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_redirected: Mapped[bool] = mapped_column(Boolean, default=False)
    redirect_chain: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    robots_txt_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    noindex_tag: Mapped[bool] = mapped_column(Boolean, default=False)
    nofollow_tag: Mapped[bool] = mapped_column(Boolean, default=False)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    internal_links_count: Mapped[int] = mapped_column(Integer, default=0)
    external_links_count: Mapped[int] = mapped_column(Integer, default=0)
    broken_links: Mapped[int] = mapped_column(Integer, default=0)
    images_without_alt: Mapped[int] = mapped_column(Integer, default=0)
    page_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    crawl_errors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="crawlability_audits")


class InternalLinkMap(Base):
    """Internal link structure mapping."""

    __tablename__ = "internal_link_map"

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
    anchor_text: Mapped[str] = mapped_column(String(500), nullable=False)
    link_type: Mapped[str] = mapped_column(String(32), default="internal")  # internal, external
    is_follow: Mapped[bool] = mapped_column(Boolean, default=True)
    link_text_length: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="internal_link_maps")


class SEOHealthScore(Base):
    """Overall SEO health score for a project."""

    __tablename__ = "seo_health_score"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    technical_score: Mapped[int] = mapped_column(Integer, default=0)
    content_score: Mapped[int] = mapped_column(Integer, default=0)
    performance_score: Mapped[int] = mapped_column(Integer, default=0)
    security_score: Mapped[int] = mapped_column(Integer, default=0)
    mobile_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metrics
    total_pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    pages_with_issues: Mapped[int] = mapped_column(Integer, default=0)
    critical_issues: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    
    # Recommendations
    top_opportunities: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    quick_wins: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    
    last_audit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="seo_health_score")
