"""
AdTicks — Advanced SEO models covering the superset of features found in
Ahrefs, SEMrush, and Moz Pro:
- Site audit issues (granular per-issue tracking)
- Crawled pages + Core Web Vitals snapshots
- Schema / structured data validation
- Anchor text distribution + toxic backlinks + link intersect
- Keyword Magic Tool entries (questions, related, broad/phrase/exact)
- SERP overview snapshots (top 10 ranking pages per keyword)
- Content briefs + content optimizer scores + topic clusters
- Local SEO (NAP citations consistency, local rank grid cells)
- Log file events (bot crawl analytics)
- Generated white-label reports
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Boolean,
    JSON,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Site audit — granular issue rows
# ---------------------------------------------------------------------------
class SiteAuditIssue(Base):
    """A single issue raised by the site audit crawler."""

    __tablename__ = "site_audit_issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # categories: crawlability, indexability, on_page, performance, security,
    #             international, structured_data, links, images, mobile, content
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="warning", index=True)
    # severity: error | warning | notice
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    project = relationship("Project", back_populates="site_audit_issues")

    __table_args__ = (
        Index("ix_audit_issues_project_severity", "project_id", "severity"),
    )


# ---------------------------------------------------------------------------
# Crawled pages
# ---------------------------------------------------------------------------
class CrawledPage(Base):
    """One row per page crawled during a site audit."""

    __tablename__ = "crawled_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    internal_links: Mapped[int] = mapped_column(Integer, default=0)
    external_links: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[int] = mapped_column(Integer, default=0)
    images_missing_alt: Mapped[int] = mapped_column(Integer, default=0)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_indexable: Mapped[bool] = mapped_column(Boolean, default=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    schema_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="crawled_pages")


# ---------------------------------------------------------------------------
# Core Web Vitals + PageSpeed snapshots
# ---------------------------------------------------------------------------
class CoreWebVitals(Base):
    """Core Web Vitals from Google PageSpeed Insights / CrUX."""

    __tablename__ = "core_web_vitals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    strategy: Mapped[str] = mapped_column(String(16), default="mobile")  # mobile | desktop
    lcp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    inp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cls: Mapped[float | None] = mapped_column(Float, nullable=True)
    fcp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    ttfb_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    si_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tbt_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accessibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_practices_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opportunities: Mapped[list] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="core_web_vitals")


# ---------------------------------------------------------------------------
# Schema markup validation
# ---------------------------------------------------------------------------
class SchemaMarkup(Base):
    """Detected JSON-LD / microdata schemas with validation results."""

    __tablename__ = "schema_markup"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    schema_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="schema_markups")


# ---------------------------------------------------------------------------
# Anchor text distribution
# ---------------------------------------------------------------------------
class AnchorText(Base):
    """Aggregated anchor text usage across the project's backlink profile."""

    __tablename__ = "anchor_texts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anchor: Mapped[str] = mapped_column(String(512), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), default="generic")
    # branded | exact | partial | generic | naked_url | image
    count: Mapped[int] = mapped_column(Integer, default=0)
    referring_domains: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="anchor_texts")


# ---------------------------------------------------------------------------
# Toxic backlinks
# ---------------------------------------------------------------------------
class ToxicBacklink(Base):
    """Backlinks flagged as toxic / spammy that may need disavowal."""

    __tablename__ = "toxic_backlinks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referring_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    spam_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    disavowed: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="toxic_backlinks")


# ---------------------------------------------------------------------------
# Link intersect — domains linking to competitors but not you
# ---------------------------------------------------------------------------
class LinkIntersect(Base):
    """Opportunity row: a referring domain that links to N competitors but not the project."""

    __tablename__ = "link_intersect"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referring_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    competitor_count: Mapped[int] = mapped_column(Integer, default=0)
    competitors: Mapped[list[str]] = mapped_column(JSON, default=list)
    domain_authority: Mapped[float] = mapped_column(Float, default=0.0)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="link_intersects")


# ---------------------------------------------------------------------------
# Keyword Magic / Explorer entries
# ---------------------------------------------------------------------------
class KeywordIdea(Base):
    """Generated keyword ideas with full metric set (Ahrefs Keywords Explorer / SEMrush KMT)."""

    __tablename__ = "keyword_ideas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seed: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    match_type: Mapped[str] = mapped_column(String(16), default="related")
    # related | broad | phrase | exact | question | also_rank | also_talk
    intent: Mapped[str] = mapped_column(String(32), default="informational")
    volume: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, default=0)
    cpc: Mapped[float] = mapped_column(Float, default=0.0)
    competition: Mapped[float] = mapped_column(Float, default=0.0)
    serp_features: Mapped[list[str]] = mapped_column(JSON, default=list)
    parent_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="keyword_ideas")


# ---------------------------------------------------------------------------
# SERP overview snapshot — top 10 ranking pages
# ---------------------------------------------------------------------------
class SerpOverview(Base):
    """Top 10 ranking pages snapshot for a keyword."""

    __tablename__ = "serp_overview"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keywords.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword_text: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str] = mapped_column(String(64), default="us")
    device: Mapped[str] = mapped_column(String(16), default="desktop")
    results: Mapped[list] = mapped_column(JSON, default=list)
    # results: list of {position, url, title, snippet, domain, domain_authority}
    features_present: Mapped[list[str]] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="serp_overviews")


# ---------------------------------------------------------------------------
# Content briefs
# ---------------------------------------------------------------------------
class ContentBrief(Base):
    """AI / TF-IDF generated content brief for a target keyword."""

    __tablename__ = "content_briefs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    title_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list)
    h1: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline: Mapped[list] = mapped_column(JSON, default=list)
    semantic_terms: Mapped[list[str]] = mapped_column(JSON, default=list)
    questions_to_answer: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_word_count: Mapped[int] = mapped_column(Integer, default=1500)
    avg_competitor_words: Mapped[int] = mapped_column(Integer, default=0)
    competitors_analyzed: Mapped[list[str]] = mapped_column(JSON, default=list)
    readability_target: Mapped[str] = mapped_column(String(32), default="grade-8")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="content_briefs")


# ---------------------------------------------------------------------------
# Content optimizer — score for a written draft
# ---------------------------------------------------------------------------
class ContentOptimizerScore(Base):
    """A scored content draft, like the Surfer SEO / Frase / Clearscope graders."""

    __tablename__ = "content_optimizer_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)
    grade_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    keyword_density: Mapped[float] = mapped_column(Float, default=0.0)
    headings_score: Mapped[int] = mapped_column(Integer, default=0)
    semantic_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    suggestions: Mapped[list] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="content_optimizer_scores")


# ---------------------------------------------------------------------------
# Topic clusters (pillar + supporting pages)
# ---------------------------------------------------------------------------
class TopicCluster(Base):
    """Pillar + supporting article structure."""

    __tablename__ = "topic_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pillar_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    pillar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    supporting_topics: Mapped[list] = mapped_column(JSON, default=list)
    # list of {topic, url, status, monthly_volume}
    total_volume: Mapped[int] = mapped_column(Integer, default=0)
    coverage_score: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="topic_clusters")


# ---------------------------------------------------------------------------
# Local SEO — citations / NAP consistency
# ---------------------------------------------------------------------------
class LocalCitation(Base):
    """A NAP citation discovered on a directory."""

    __tablename__ = "local_citations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    directory: Mapped[str] = mapped_column(String(128), nullable=False)
    listing_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    consistency_score: Mapped[int] = mapped_column(Integer, default=100)
    issues: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active")
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    project = relationship("Project", back_populates="local_citations")


class LocalRankGrid(Base):
    """A single grid cell in a local rank tracking heatmap."""

    __tablename__ = "local_rank_grid"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    grid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    grid_lng: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radius_km: Mapped[float] = mapped_column(Float, default=5.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="local_rank_grids")


# ---------------------------------------------------------------------------
# Log file analysis
# ---------------------------------------------------------------------------
class LogEvent(Base):
    """An aggregated log file event for bot crawl analysis."""

    __tablename__ = "log_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bot: Mapped[str] = mapped_column(String(64), default="googlebot", index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    hits: Mapped[int] = mapped_column(Integer, default=1)
    last_crawled: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="log_events")


# ---------------------------------------------------------------------------
# Generated reports
# ---------------------------------------------------------------------------
class GeneratedReport(Base):
    """White-label report deliverable."""

    __tablename__ = "generated_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(64), default="full_seo")
    # full_seo | technical_audit | keyword_research | backlinks | local_seo | content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    branding: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending | generating | ready | failed
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False, index=True
    )

    project = relationship("Project", back_populates="generated_reports")
