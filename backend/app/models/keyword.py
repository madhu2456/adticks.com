"""
AdTicks — Keyword and Ranking models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Keyword(Base):
    """A tracked keyword associated with a project."""

    __tablename__ = "keywords"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="keywords")
    rankings = relationship(
        "Ranking", back_populates="keyword", cascade="all, delete-orphan"
    )
    rank_history = relationship(
        "RankHistory", back_populates="keyword", cascade="all, delete-orphan"
    )
    serp_features = relationship(
        "SerpFeatures", back_populates="keyword", cascade="all, delete-orphan"
    )


class Ranking(Base):
    """A point-in-time SERP ranking for a keyword."""

    __tablename__ = "rankings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="rankings")
