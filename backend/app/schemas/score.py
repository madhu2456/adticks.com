"""AdTicks score Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ScoreResponse(BaseModel):
    id: UUID
    project_id: UUID
    visibility_score: float | None
    impact_score: float | None
    sov_score: float | None
    timestamp: datetime
    model_config = {"from_attributes": True}
