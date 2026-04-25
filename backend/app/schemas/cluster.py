"""AdTicks topic cluster Pydantic schemas."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ClusterBase(BaseModel):
    topic_name: str
    keywords: list[str] = []

class ClusterCreate(ClusterBase):
    pass

class ClusterUpdate(BaseModel):
    topic_name: str | None = None
    keywords: list[str] | None = None

class ClusterResponse(ClusterBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}
