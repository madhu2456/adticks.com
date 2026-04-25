"""
AdTicks — SEO Suite schemas (RankHistory, SerpFeatures, CompetitorKeywords, Backlinks).
"""

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Backlinks Schemas
# ============================================================================
class BacklinksBase(BaseModel):
    """Base backlinks data."""
    referring_domain: str = Field(description="Referring domain")
    target_url: str | None = Field(None, description="Target URL on project domain")
    anchor_text: str | None = Field(None, description="Anchor text of the link")
    status: str = Field("active", description="Link status (new, active, lost)")
    authority_score: float = Field(0.0, description="Authority score")


class BacklinksCreate(BacklinksBase):
    """Create backlinks entry."""
    pass


class BacklinksResponse(BacklinksBase):
    """Backlinks response."""
    id: UUID = Field(description="Backlink ID")
    project_id: UUID = Field(description="Associated project ID")
    first_seen: datetime = Field(description="When the link was first seen")
    last_seen: datetime = Field(description="When the link was last seen")
    timestamp: datetime = Field(description="Timestamp of the backlink")

    model_config = ConfigDict(from_attributes=True)


class BacklinkStatsResponse(BaseModel):
    """Summary statistics for backlinks."""
    total_backlinks: int
    total_referring_domains: int
    new_domains_30d: int
    lost_domains_30d: int
    avg_authority: float
    authority_distribution: dict[str, int] = Field(
        description="Count of domains per authority bracket (0-20, 21-40, etc.)"
    )
    top_anchor_texts: list[dict[str, Any]] = Field(default_factory=list)


class SiteAuditHistoryResponse(BaseModel):
    """Historical audit response."""
    id: UUID
    project_id: UUID
    url: str
    score: int
    total_errors: int
    total_warnings: int
    pages_crawled: int
    crawl_depth: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
