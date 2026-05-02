"""
AdTicks — Google Analytics 4 data model.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GAData(Base):
    """A single Google Analytics 4 performance row for a project."""

    __tablename__ = "ga_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Core metrics
    sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pageviews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bounce_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_session_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Conversion metrics
    conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Traffic source
    traffic_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Device type
    device_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Country
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Page path
    page_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    
    # Reporting date
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Relationships
    project = relationship("Project", back_populates="ga_data")
