"""
AdTicks — AEO (AI-Powered Search Engine Optimization) models.

Tables for:
1. AI chatbot visibility tracking
2. Featured snippets and PAA queries
3. AI-generated content recommendations
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIModel(str, Enum):
    """Supported AI models for visibility tracking."""
    CHATGPT = "chatgpt"
    PERPLEXITY = "perplexity"
    CLAUDE = "claude"


class SnippetType(str, Enum):
    """Types of featured snippets."""
    FEATURED = "featured"
    ANSWER = "answer"
    LIST = "list"


class RecommendationType(str, Enum):
    """Types of content recommendations."""
    OPTIMIZE = "optimize"
    FAQ = "faq"
    EXPAND = "expand"
    REWRITE = "rewrite"


class DifficultyLevel(str, Enum):
    """Implementation difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ImpactLevel(str, Enum):
    """Estimated impact levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# Task 1: AI Chatbot Visibility Tracking
# ============================================================================

class AEOVisibility(Base):
    """Track visibility of keywords in AI chatbot responses."""

    __tablename__ = "aeo_visibility"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_model: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    is_mentioned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    mention_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="aeo_visibility")
    keyword = relationship("Keyword", foreign_keys=[keyword_id])


class AEOTrends(Base):
    """Aggregate visibility trends for keywords across AI models."""

    __tablename__ = "aeo_trends"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_model: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    visibility_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="aeo_trends")
    keyword = relationship("Keyword", foreign_keys=[keyword_id])


# ============================================================================
# Task 2: Featured Snippets & PAA Tracking
# ============================================================================

class SnippetTracking(Base):
    """Track featured snippets for keywords in Google SERPs."""

    __tablename__ = "snippet_tracking"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    has_snippet: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    snippet_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    snippet_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet_source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    position_before_snippet: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_captured: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )
    lost_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    keyword = relationship("Keyword", foreign_keys=[keyword_id])


class PAA(Base):
    """Track 'People Also Ask' queries and answers for keywords."""

    __tablename__ = "paa_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paa_query: Mapped[str] = mapped_column(String(512), nullable=False)
    answer_source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    answer_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_found: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    keyword = relationship("Keyword", foreign_keys=[keyword_id])


# ============================================================================
# Task 3: AI Content Recommendations
# ============================================================================

class ContentRecommendation(Base):
    """AI-generated content optimization recommendations."""

    __tablename__ = "content_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_difficulty: Mapped[str] = mapped_column(String(32), default="medium")
    estimated_impact: Mapped[str] = mapped_column(String(32), default="medium")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )
    user_action: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="content_recommendations")
    keyword = relationship("Keyword", foreign_keys=[keyword_id])


class GeneratedFAQ(Base):
    """AI-generated FAQ entries from PAA queries."""

    __tablename__ = "generated_faqs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("paa_queries.id", ondelete="SET NULL"),
        nullable=True,
    )
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="generated_faqs")
    keyword = relationship("Keyword", foreign_keys=[keyword_id])
    paa = relationship("PAA", foreign_keys=[paa_id])
