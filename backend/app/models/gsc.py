"""
AdTicks — Google Search Console data model.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GSCData(Base):
    """A single Google Search Console performance row for a project."""

    __tablename__ = "gsc_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    position: Mapped[float | None] = mapped_column(Float, nullable=True)
    page: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Relationships
    project = relationship("Project", back_populates="gsc_data")
