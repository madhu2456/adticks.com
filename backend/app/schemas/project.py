"""AdTicks project Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator

class ProjectCreate(BaseModel):
    brand_name: str
    domain: str
    industry: str | None = None
    competitors: list[str] | None = None
    seed_keywords: list[str] | None = None

class ProjectUpdate(BaseModel):
    brand_name: str | None = None
    domain: str | None = None
    industry: str | None = None
    ai_scans_enabled: bool | None = None
    competitors: list[str] | None = None

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    brand_name: str
    domain: str
    industry: str | None
    ai_scans_enabled: bool
    competitors: list[str] = []
    created_at: datetime
    
    @field_validator("competitors", mode="before")
    @classmethod
    def extract_competitor_domains(cls, v):
        if isinstance(v, list) and len(v) > 0 and not isinstance(v[0], str):
            return [c.domain for c in v]
        return v

    model_config = {"from_attributes": True}
