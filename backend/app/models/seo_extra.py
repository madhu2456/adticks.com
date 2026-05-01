"""
AdTicks — Additional SEO models filling remaining gaps vs market-leading
SEO platforms.

- KeywordCannibalization: pages competing for the same query
- InternalLink + OrphanPage: site graph analysis
- DomainComparison: side-by-side competitive snapshot
- BulkAnalysisJob + BulkAnalysisItem: queue/result rows for bulk audits
- SitemapGeneration: generated/validated sitemap snapshots
- RobotsValidation: robots.txt validation runs
- SchemaTemplate: generated JSON-LD blueprints
- OutreachCampaign + OutreachProspect: link-building outreach tracker
- FeaturedSnippetWatch + PAAQuestion: snippet/PAA tracking
- SerpVolatility: position-change events for alerts
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, String, Boolean, JSON, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Cannibalization
# ---------------------------------------------------------------------------
class KeywordCannibalization(Base):
    """A keyword for which two or more URLs on the project's domain rank.
    Storing the conflicting URLs and the recommendation."""

    __tablename__ = "keyword_cannibalization"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    urls: Mapped[list] = mapped_column(JSON, default=list)  # [{url, position, clicks, impressions}]
    severity: Mapped[str] = mapped_column(String(16), default="medium")  # low | medium | high
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True,
    )

    project = relationship("Project", back_populates="keyword_cannibalizations")


# ---------------------------------------------------------------------------
# Internal Link Graph
# ---------------------------------------------------------------------------
class InternalLink(Base):
    """An edge in the internal link graph (source URL → target URL)."""

    __tablename__ = "internal_links_graph"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    anchor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_nofollow: Mapped[bool] = mapped_column(Boolean, default=False)
    link_position: Mapped[str] = mapped_column(String(32), default="body")  # nav | body | footer | sidebar
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="internal_links_graph")


class OrphanPage(Base):
    """A page on the site that has no internal links pointing to it."""

    __tablename__ = "orphan_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    in_sitemap: Mapped[bool] = mapped_column(Boolean, default=False)
    page_authority: Mapped[float] = mapped_column(Float, default=0.0)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="orphan_pages")


# ---------------------------------------------------------------------------
# Domain Comparison
# ---------------------------------------------------------------------------
class DomainComparison(Base):
    """A snapshot row comparing several domains side-by-side."""

    __tablename__ = "domain_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    primary_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    competitor_domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    # metrics shape: {domain: {da, backlinks, referring_domains, organic_keywords, traffic_estimate}}
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True,
    )

    project = relationship("Project", back_populates="domain_comparisons")


# ---------------------------------------------------------------------------
# Bulk URL analyzer
# ---------------------------------------------------------------------------
class BulkAnalysisJob(Base):
    """A bulk analysis job covering many URLs."""

    __tablename__ = "bulk_analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(32), default="onpage")  # onpage | cwv | meta
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued | running | done | failed
    total_urls: Mapped[int] = mapped_column(Integer, default=0)
    completed_urls: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True,
    )

    project = relationship("Project", back_populates="bulk_analysis_jobs")


class BulkAnalysisItem(Base):
    """One URL row inside a bulk analysis job."""

    __tablename__ = "bulk_analysis_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bulk_analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | done | failed
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Sitemap & Robots
# ---------------------------------------------------------------------------
class SitemapGeneration(Base):
    """A generated XML sitemap snapshot."""

    __tablename__ = "sitemap_generations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url_count: Mapped[int] = mapped_column(Integer, default=0)
    file_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    xml_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True,
    )

    project = relationship("Project", back_populates="sitemap_generations")


class RobotsValidation(Base):
    """A robots.txt validation result."""

    __tablename__ = "robots_validations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    rules: Mapped[list] = mapped_column(JSON, default=list)
    sitemap_directives: Mapped[list[str]] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="robots_validations")


# ---------------------------------------------------------------------------
# Schema templates (generated JSON-LD)
# ---------------------------------------------------------------------------
class SchemaTemplate(Base):
    """A generated JSON-LD schema markup template (Article, Product, FAQ, etc.)."""

    __tablename__ = "schema_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schema_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    json_ld: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="schema_templates")


# ---------------------------------------------------------------------------
# Outreach
# ---------------------------------------------------------------------------
class OutreachCampaign(Base):
    """A link-building outreach campaign."""

    __tablename__ = "outreach_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | paused | finished
    target_link_count: Mapped[int] = mapped_column(Integer, default=0)
    won_link_count: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="outreach_campaigns")


class OutreachProspect(Base):
    """A target / prospect inside a campaign."""

    __tablename__ = "outreach_prospects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    # new | contacted | replied | won | lost
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    domain_authority: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    won_link_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )


# ---------------------------------------------------------------------------
# Featured Snippet + PAA
# ---------------------------------------------------------------------------
class FeaturedSnippetWatch(Base):
    """A keyword we watch for featured-snippet ownership."""

    __tablename__ = "featured_snippet_watch"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    we_own: Mapped[bool] = mapped_column(Boolean, default=False)
    current_owner_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    snippet_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # paragraph | list | table
    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="featured_snippet_watches")


class PAAQuestion(Base):
    """A People Also Ask question we are tracking."""

    __tablename__ = "paa_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seed_keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    answer_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False,
    )

    project = relationship("Project", back_populates="paa_questions_tracked")


# ---------------------------------------------------------------------------
# SERP Volatility
# ---------------------------------------------------------------------------
class SerpVolatilityEvent(Base):
    """A meaningful position change worth alerting on."""

    __tablename__ = "serp_volatility_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    previous_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delta: Mapped[int] = mapped_column(Integer, default=0)
    direction: Mapped[str] = mapped_column(String(8), default="up")  # up | down
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True,
    )

    project = relationship("Project", back_populates="serp_volatility_events")
