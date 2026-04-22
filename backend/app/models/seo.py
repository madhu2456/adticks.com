"""
AdTicks — SEO Suite models (rank_history, serp_features, competitor_keywords, backlinks).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RankHistory(Base):
    """Historical ranking data for keywords."""

    __tablename__ = "rank_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpc: Mapped[float | None] = mapped_column(Float, nullable=True)
    device: Mapped[str] = mapped_column(String(32), default="desktop", nullable=False)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="rank_history")


class SerpFeatures(Base):
    """SERP features data for keywords."""

    __tablename__ = "serp_features"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    featured_snippet: Mapped[bool] = mapped_column(Boolean, default=False)
    rich_snippets: Mapped[bool] = mapped_column(Boolean, default=False)
    ads: Mapped[bool] = mapped_column(Boolean, default=False)
    knowledge_panel: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="serp_features")


class CompetitorKeywords(Base):
    """Competitor keywords for competitive analysis."""

    __tablename__ = "competitor_keywords"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    keywords: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="competitor_keywords")


class Backlinks(Base):
    """Backlink data for projects."""

    __tablename__ = "backlinks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referring_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    authority_score: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="backlinks")
