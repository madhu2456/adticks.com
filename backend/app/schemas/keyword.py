"""AdTicks keyword Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class KeywordCreate(BaseModel):
    keyword: str
    intent: str | None = None
    difficulty: float | None = None
    volume: int | None = None

class KeywordResponse(BaseModel):
    id: UUID
    project_id: UUID
    keyword: str
    intent: str | None
    difficulty: float | None
    volume: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class RankingResponse(BaseModel):
    id: UUID
    keyword_id: UUID
    position: int | None
    url: str | None
    timestamp: datetime
    # These fields will be populated by the endpoint
    keyword: str | None = None
    intent: str | None = None
    difficulty: float | None = None
    volume: int | None = None
    position_change: int | None = None
    is_cannibalized: bool = False
    model_config = {"from_attributes": True}
