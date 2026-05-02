"""
AdTicks — Project model.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """An AdTicks visibility project belonging to a user."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # GSC Settings
    gsc_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gsc_property_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # AI Settings
    ai_scans_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Log Settings
    remote_log_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    log_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    competitors = relationship(
        "Competitor", back_populates="project", cascade="all, delete-orphan"
    )
    keywords = relationship(
        "Keyword", back_populates="project", cascade="all, delete-orphan"
    )
    prompts = relationship(
        "Prompt", back_populates="project", cascade="all, delete-orphan"
    )
    clusters = relationship(
        "Cluster", back_populates="project", cascade="all, delete-orphan"
    )
    scores = relationship(
        "Score", back_populates="project", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="project", cascade="all, delete-orphan"
    )
    gsc_data = relationship(
        "GSCData", back_populates="project", cascade="all, delete-orphan"
    )
    audit_history = relationship(
        "SiteAuditHistory", back_populates="project", cascade="all, delete-orphan"
    )
    ads_data = relationship(
        "AdsData", back_populates="project", cascade="all, delete-orphan"
    )
    competitor_keywords = relationship(
        "CompetitorKeywords", back_populates="project", cascade="all, delete-orphan"
    )
    backlinks = relationship(
        "Backlinks", back_populates="project", cascade="all, delete-orphan"
    )
    locations = relationship(
        "Location", back_populates="project", cascade="all, delete-orphan"
    )
    meta_tag_audits = relationship(
        "MetaTagAudit", back_populates="project", cascade="all, delete-orphan"
    )
    structured_data_audits = relationship(
        "StructuredDataAudit", back_populates="project", cascade="all, delete-orphan"
    )
    page_speed_metrics = relationship(
        "PageSpeedMetrics", back_populates="project", cascade="all, delete-orphan"
    )
    crawlability_audits = relationship(
        "CrawlabilityAudit", back_populates="project", cascade="all, delete-orphan"
    )
    internal_link_maps = relationship(
        "InternalLinkMap", back_populates="project", cascade="all, delete-orphan"
    )
    seo_health_score = relationship(
        "SEOHealthScore", back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    content_analysis = relationship(
        "ContentAnalysis", back_populates="project", cascade="all, delete-orphan"
    )
    image_audits = relationship(
        "ImageAudit", back_populates="project", cascade="all, delete-orphan"
    )
    duplicate_content = relationship(
        "DuplicateContent", back_populates="project", cascade="all, delete-orphan"
    )
    seo_recommendations = relationship(
        "SEORecommendation", back_populates="project", cascade="all, delete-orphan"
    )
    url_redirects = relationship(
        "URLRedirect", back_populates="project", cascade="all, delete-orphan"
    )
    broken_links = relationship(
        "BrokenLink", back_populates="project", cascade="all, delete-orphan"
    )

    # Advanced SEO Suite Relationships
    site_audit_issues = relationship(
        "SiteAuditIssue", back_populates="project", cascade="all, delete-orphan"
    )
    crawled_pages = relationship(
        "CrawledPage", back_populates="project", cascade="all, delete-orphan"
    )
    core_web_vitals = relationship(
        "CoreWebVitals", back_populates="project", cascade="all, delete-orphan"
    )
    schema_markups = relationship(
        "SchemaMarkup", back_populates="project", cascade="all, delete-orphan"
    )
    anchor_texts = relationship(
        "AnchorText", back_populates="project", cascade="all, delete-orphan"
    )
    toxic_backlinks = relationship(
        "ToxicBacklink", back_populates="project", cascade="all, delete-orphan"
    )
    link_intersects = relationship(
        "LinkIntersect", back_populates="project", cascade="all, delete-orphan"
    )
    keyword_ideas = relationship(
        "KeywordIdea", back_populates="project", cascade="all, delete-orphan"
    )
    serp_overviews = relationship(
        "SerpOverview", back_populates="project", cascade="all, delete-orphan"
    )
    content_briefs = relationship(
        "ContentBrief", back_populates="project", cascade="all, delete-orphan"
    )
    content_optimizer_scores = relationship(
        "ContentOptimizerScore", back_populates="project", cascade="all, delete-orphan"
    )
    topic_clusters = relationship(
        "TopicCluster", back_populates="project", cascade="all, delete-orphan"
    )
    local_citations = relationship(
        "LocalCitation", back_populates="project", cascade="all, delete-orphan"
    )
    local_rank_grids = relationship(
        "LocalRankGrid", back_populates="project", cascade="all, delete-orphan"
    )
    log_events = relationship(
        "LogEvent", back_populates="project", cascade="all, delete-orphan"
    )
    generated_reports = relationship(
        "GeneratedReport", back_populates="project", cascade="all, delete-orphan"
    )

    # Extra SEO Features
    keyword_cannibalizations = relationship(
        "KeywordCannibalization", back_populates="project", cascade="all, delete-orphan"
    )
    internal_links_graph = relationship(
        "InternalLink", back_populates="project", cascade="all, delete-orphan"
    )
    orphan_pages = relationship(
        "OrphanPage", back_populates="project", cascade="all, delete-orphan"
    )
    domain_comparisons = relationship(
        "DomainComparison", back_populates="project", cascade="all, delete-orphan"
    )
    bulk_analysis_jobs = relationship(
        "BulkAnalysisJob", back_populates="project", cascade="all, delete-orphan"
    )
    sitemap_generations = relationship(
        "SitemapGeneration", back_populates="project", cascade="all, delete-orphan"
    )
    robots_validations = relationship(
        "RobotsValidation", back_populates="project", cascade="all, delete-orphan"
    )
    schema_templates = relationship(
        "SchemaTemplate", back_populates="project", cascade="all, delete-orphan"
    )
    outreach_campaigns = relationship(
        "OutreachCampaign", back_populates="project", cascade="all, delete-orphan"
    )
    featured_snippet_watches = relationship(
        "FeaturedSnippetWatch", back_populates="project", cascade="all, delete-orphan"
    )
    paa_questions_tracked = relationship(
        "PAAQuestion", back_populates="project", cascade="all, delete-orphan"
    )
    serp_volatility_events = relationship(
        "SerpVolatilityEvent", back_populates="project", cascade="all, delete-orphan"
    )

    # AEO Relationships
    aeo_visibility = relationship(
        "AEOVisibility", back_populates="project", cascade="all, delete-orphan"
    )
    aeo_trends = relationship(
        "AEOTrends", back_populates="project", cascade="all, delete-orphan"
    )
    content_recommendations = relationship(
        "ContentRecommendation", back_populates="project", cascade="all, delete-orphan"
    )
    generated_faqs = relationship(
        "GeneratedFAQ", back_populates="project", cascade="all, delete-orphan"
    )
