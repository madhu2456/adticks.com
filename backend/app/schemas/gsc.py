"""AdTicks GSC Pydantic schemas."""
from datetime import date
from uuid import UUID
from pydantic import BaseModel

class GSCDataResponse(BaseModel):
    id: UUID
    project_id: UUID
    query: str | None
    clicks: int | None
    impressions: int | None
    ctr: float | None
    position: float | None
    page: str | None
    date: date | None
    model_config = {"from_attributes": True}
