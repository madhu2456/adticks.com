"""AdTicks project Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    brand_name: str
    domain: str
    industry: str | None = None

class ProjectUpdate(BaseModel):
    brand_name: str | None = None
    domain: str | None = None
    industry: str | None = None
    ai_scans_enabled: bool | None = None

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    brand_name: str
    domain: str
    industry: str | None
    ai_scans_enabled: bool
    created_at: datetime
    model_config = {"from_attributes": True}
