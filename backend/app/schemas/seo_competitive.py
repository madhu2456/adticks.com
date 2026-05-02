from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# --- Traffic Analytics ---

class TrafficEngagement(BaseModel):
    bounce_rate: float
    avg_visit_duration_sec: int
    pages_per_visit: float
    total_visits: int

class TopPage(BaseModel):
    url: str
    traffic_share: float
    avg_duration_sec: int

class TrafficAnalyticsResponse(BaseModel):
    domain: str
    monthly_visits: int
    organic_share: float
    paid_share: float
    engagement: TrafficEngagement
    top_countries: List[dict]  # e.g. {"country": "US", "share": 0.45}
    top_pages: List[TopPage]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- PPC Research ---

class PaidKeyword(BaseModel):
    keyword: str
    position: int
    cpc_usd: float
    traffic_share: float
    url: str

class AdCopy(BaseModel):
    title: str
    description: str
    visible_url: str

class PPCResearchResponse(BaseModel):
    domain: str
    est_monthly_spend_usd: float
    paid_keywords_count: int
    top_paid_keywords: List[PaidKeyword]
    sample_ads: List[AdCopy]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Brand Monitoring ---

class BrandMention(BaseModel):
    id: str
    source_name: str
    source_url: str
    snippet: str
    domain_authority: int
    sentiment: str  # positive, neutral, negative
    is_linked: bool
    published_at: datetime

class BrandMonitorResponse(BaseModel):
    project_id: UUID
    mentions: List[BrandMention]
    total_mentions: int

# --- Content Explorer ---

class ContentArticle(BaseModel):
    id: str
    title: str
    url: str
    author: Optional[str]
    published_at: datetime
    social_shares: dict  # {"twitter": 120, "facebook": 450, etc}
    referring_domains: int
    est_organic_traffic: int

class ContentExplorerResponse(BaseModel):
    query: str
    articles: List[ContentArticle]
    total_results: int

# --- Domain Overview (Site Explorer) ---

class DomainOverviewResponse(BaseModel):
    domain: str
    authority_score: int
    organic_traffic: int
    organic_keywords: int
    backlinks_count: int
    referring_domains: int
    paid_traffic: int
    paid_keywords: int
    display_ads: int
    main_competitors: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Bulk Keyword Analysis ---

class BulkKeywordRequest(BaseModel):
    keywords: List[str]

class KeywordMetric(BaseModel):
    keyword: str
    volume: int
    difficulty: int
    cpc_usd: float
    intent: str

class BulkKeywordResponse(BaseModel):
    results: List[KeywordMetric]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
