"""
AdTicks — AEO (AI-Powered SEO) Pydantic schemas.

Request/response schemas for AEO endpoints.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# AI Visibility Tracking
# ============================================================================

class AEOVisibilityCreate(BaseModel):
    """Create a new AI visibility record."""
    ai_model: str = Field(..., description="AI model (chatgpt/perplexity/claude)")
    is_mentioned: bool = Field(default=False)
    mention_context: Optional[str] = Field(None, description="Text snippet from AI response")
    position: Optional[int] = Field(None, description="Rank position if mentioned")
    confidence_score: float = Field(default=0.0, ge=0.0, le=100.0)


class AEOVisibilityResponse(BaseModel):
    """AEO visibility data."""
    id: UUID
    project_id: UUID
    keyword_id: UUID
    ai_model: str
    is_mentioned: bool
    mention_context: Optional[str] = None
    position: Optional[int] = None
    confidence_score: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AEOTrendsResponse(BaseModel):
    """Aggregate visibility trends."""
    id: UUID
    project_id: UUID
    keyword_id: UUID
    ai_model: str
    visibility_percentage: float = Field(ge=0.0, le=100.0)
    mention_count: int
    avg_position: Optional[float] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AIVisibilitySummary(BaseModel):
    """Summary of AI visibility across all models."""
    keyword: str
    chatgpt: Optional[AEOVisibilityResponse] = None
    perplexity: Optional[AEOVisibilityResponse] = None
    claude: Optional[AEOVisibilityResponse] = None
    overall_mentioned: bool
    models_mentioning: list[str]


class VisibilityCheckRequest(BaseModel):
    """Request to manually check AI visibility."""
    keyword_id: UUID
    ai_models: list[str] = Field(default=["chatgpt", "perplexity", "claude"])


class KeywordIdRequest(BaseModel):
    """Simple request with only a keyword_id."""
    keyword_id: UUID


# ============================================================================
# Featured Snippets & PAA
# ============================================================================

class SnippetTrackingCreate(BaseModel):
    """Create/update snippet tracking record."""
    has_snippet: bool = Field(default=False)
    snippet_type: Optional[str] = Field(None, description="featured/answer/list")
    snippet_text: Optional[str] = None
    snippet_source_url: Optional[str] = None
    position_before_snippet: Optional[int] = None


class SnippetTrackingResponse(BaseModel):
    """Snippet tracking data."""
    id: UUID
    keyword_id: UUID
    has_snippet: bool
    snippet_type: Optional[str] = None
    snippet_text: Optional[str] = None
    snippet_source_url: Optional[str] = None
    position_before_snippet: Optional[int] = None
    date_captured: datetime
    lost_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PAA_Create(BaseModel):
    """Create a PAA query record."""
    paa_query: str = Field(..., description="The 'People Also Ask' question")
    answer_source_url: Optional[str] = None
    answer_snippet: Optional[str] = None
    position: Optional[int] = None


class PAA_Response(BaseModel):
    """PAA query data."""
    id: UUID
    keyword_id: UUID
    paa_query: str
    answer_source_url: Optional[str] = None
    answer_snippet: Optional[str] = None
    position: Optional[int] = None
    date_found: datetime

    model_config = ConfigDict(from_attributes=True)


class SnippetOpportunity(BaseModel):
    """Snippet optimization opportunity analysis."""
    keyword_id: UUID
    keyword: str
    current_position: Optional[int] = None
    has_featured_snippet: bool
    recommendation: str
    difficulty: str = Field(description="easy/medium/hard")
    potential_traffic_gain: str = Field(description="low/medium/high")


# ============================================================================
# Content Recommendations
# ============================================================================

class ContentRecommendationCreate(BaseModel):
    """Create a content recommendation."""
    recommendation_type: str = Field(..., description="optimize/faq/expand/rewrite")
    recommendation_text: str
    implementation_difficulty: str = Field(default="medium")
    estimated_impact: str = Field(default="medium")


class ContentRecommendationResponse(BaseModel):
    """Content recommendation data."""
    id: UUID
    project_id: UUID
    keyword_id: UUID
    recommendation_type: str
    recommendation_text: str
    implementation_difficulty: str
    estimated_impact: str
    created_at: datetime
    user_action: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContentRecommendationUpdate(BaseModel):
    """Update recommendation status."""
    user_action: str = Field(..., description="implemented/rejected/pending")


class GeneratedFAQCreate(BaseModel):
    """Create a generated FAQ."""
    question: str
    answer: str
    paa_id: Optional[UUID] = None


class GeneratedFAQResponse(BaseModel):
    """Generated FAQ data."""
    id: UUID
    project_id: UUID
    keyword_id: UUID
    paa_id: Optional[UUID] = None
    question: str
    answer: str
    approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GeneratedFAQUpdate(BaseModel):
    """Update FAQ approval status."""
    approved: bool


class ContentOutlineRequest(BaseModel):
    """Request content outline generation."""
    keyword_id: UUID
    content_type: Optional[str] = Field(default="blog", description="blog/guide/article")
    target_length: Optional[str] = Field(default="medium", description="short/medium/long")


class ContentOutline(BaseModel):
    """Generated content outline."""
    keyword: str
    outline: list[str]
    estimated_word_count: int
    key_topics: list[str]


class AEO_DashboardSummary(BaseModel):
    """Overall AEO dashboard summary."""
    total_keywords: int
    ai_visibility_count: int
    featured_snippet_count: int
    paa_queries_count: int
    recommendation_count: int
    pending_recommendations: int
    implemented_recommendations: int
    avg_ai_visibility_percentage: float
    snippet_opportunities: int
