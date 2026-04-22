"""AdTicks — Ads performance data model."""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AdsData(Base):
    """A single ad campaign performance row for a project."""

    __tablename__ = "ads_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign: Mapped[str | None] = mapped_column(String(512), nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpc: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spend: Mapped[float | None] = mapped_column(Float, nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    project = relationship("Project", back_populates="ads_data")
