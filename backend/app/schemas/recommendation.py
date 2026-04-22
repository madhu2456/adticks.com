"""AdTicks recommendation Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class RecommendationResponse(BaseModel):
    id: UUID
    project_id: UUID
    text: str
    priority: int
    category: str | None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
