"""
AdTicks — Prompt, Response and Mention models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prompt(Base):
    """An AI prompt template/record stored for a project."""

    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="prompts")
    responses = relationship(
        "Response", back_populates="prompt", cascade="all, delete-orphan"
    )


class Response(Base):
    """An AI model response to a Prompt, stored in object storage."""

    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )

    # Relationships
    prompt = relationship("Prompt", back_populates="responses")
    mentions = relationship(
        "Mention", back_populates="response", cascade="all, delete-orphan"
    )


class Mention(Base):
    """A brand mention detected inside an AI Response."""

    __tablename__ = "mentions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    response = relationship("Response", back_populates="mentions")
