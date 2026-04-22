"""
AdTicks — SEO Suite schemas (RankHistory, SerpFeatures, CompetitorKeywords, Backlinks).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# RankHistory Schemas
# ============================================================================
class RankHistoryBase(BaseModel):
    """Base rank history data."""
    rank: int | None = Field(None, description="Ranking position")
    search_volume: int | None = Field(None, description="Search volume for keyword")
    cpc: float | None = Field(None, description="Cost per click")
    device: str = Field("desktop", description="Device type (desktop/mobile)")
    location: str | None = Field(None, description="Geographic location")


class RankHistoryCreate(RankHistoryBase):
    """Create rank history entry."""
    pass


class RankHistoryResponse(RankHistoryBase):
    """Rank history response."""
    id: UUID = Field(description="Rank history ID")
    keyword_id: UUID = Field(description="Associated keyword ID")
    timestamp: datetime = Field(description="Timestamp of the ranking")

    class Config:
        from_attributes = True


# ============================================================================
# SerpFeatures Schemas
# ============================================================================
class SerpFeaturesBase(BaseModel):
    """Base SERP features data."""
    featured_snippet: bool = Field(False, description="Has featured snippet")
    rich_snippets: bool = Field(False, description="Has rich snippets")
    ads: bool = Field(False, description="Has ads in SERP")
    knowledge_panel: bool = Field(False, description="Has knowledge panel")


class SerpFeaturesCreate(SerpFeaturesBase):
    """Create SERP features entry."""
    pass


class SerpFeaturesResponse(SerpFeaturesBase):
    """SERP features response."""
    id: UUID = Field(description="SERP features ID")
    keyword_id: UUID = Field(description="Associated keyword ID")
    timestamp: datetime = Field(description="Timestamp of the features")

    class Config:
        from_attributes = True


# ============================================================================
# CompetitorKeywords Schemas
# ============================================================================
class CompetitorKeywordsBase(BaseModel):
    """Base competitor keywords data."""
    competitor_domain: str = Field(description="Competitor domain")
    keywords: list[str] = Field(default_factory=list, description="List of keywords")


class CompetitorKeywordsCreate(CompetitorKeywordsBase):
    """Create competitor keywords entry."""
    pass


class CompetitorKeywordsResponse(CompetitorKeywordsBase):
    """Competitor keywords response."""
    id: UUID = Field(description="Competitor keywords ID")
    project_id: UUID = Field(description="Associated project ID")
    count: int = Field(description="Number of keywords")
    timestamp: datetime = Field(description="Timestamp of the data")

    class Config:
        from_attributes = True


# ============================================================================
# Backlinks Schemas
# ============================================================================
class BacklinksBase(BaseModel):
    """Base backlinks data."""
    referring_domain: str = Field(description="Referring domain")
    authority_score: float = Field(0.0, description="Authority score")


class BacklinksCreate(BacklinksBase):
    """Create backlinks entry."""
    pass


class BacklinksResponse(BacklinksBase):
    """Backlinks response."""
    id: UUID = Field(description="Backlink ID")
    project_id: UUID = Field(description="Associated project ID")
    timestamp: datetime = Field(description="Timestamp of the backlink")

    class Config:
        from_attributes = True
