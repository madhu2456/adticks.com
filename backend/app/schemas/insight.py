"""AdTicks insight Pydantic schemas."""
from pydantic import BaseModel

class InsightResponse(BaseModel):
    text: str
    category: str
    priority: int
    supporting_data: dict
