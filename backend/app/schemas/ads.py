"""AdTicks ads Pydantic schemas."""
from datetime import date
from uuid import UUID
from pydantic import BaseModel

class AdsDataResponse(BaseModel):
    id: UUID
    project_id: UUID
    campaign: str | None
    clicks: int | None
    cpc: float | None
    conversions: int | None
    spend: float | None
    date: date | None
    model_config = {"from_attributes": True}
