"""AdTicks prompt / response / mention Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class PromptResponse(BaseModel):
    id: UUID
    project_id: UUID
    text: str
    category: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class ResponseResponse(BaseModel):
    id: UUID
    prompt_id: UUID
    response_text: str
    storage_path: str
    model: str | None
    timestamp: datetime
    model_config = {"from_attributes": True}

class MentionResponse(BaseModel):
    id: UUID
    response_id: UUID
    brand: str
    position: int | None
    confidence: float | None
    model_config = {"from_attributes": True}
