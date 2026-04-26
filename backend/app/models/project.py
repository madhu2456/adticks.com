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
    clusters = relationship(
        "Cluster", back_populates="project", cascade="all, delete-orphan"
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
