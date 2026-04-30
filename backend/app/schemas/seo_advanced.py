"""Pydantic schemas for advanced SEO features."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Site audit -------------------------------------------------------------
class SiteAuditIssueResponse(BaseModel):
    id: UUID
    url: str
    category: str
    severity: str
    code: str
    message: str
    recommendation: str | None = None
    details: dict = {}
    resolved: bool = False
    discovered_at: datetime

    model_config = {"from_attributes": True}


class CrawledPageResponse(BaseModel):
    id: UUID
    url: str
    status_code: int | None = None
    title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    word_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images: int = 0
    images_missing_alt: int = 0
    canonical_url: str | None = None
    is_indexable: bool = True
    response_time_ms: int | None = None
    page_size_bytes: int | None = None
    depth: int = 0
    schema_types: list[str] = []
    timestamp: datetime

    model_config = {"from_attributes": True}


class SiteAuditTriggerRequest(BaseModel):
    url: str = Field(..., description="Starting URL to crawl")
    max_pages: int = Field(50, ge=1, le=500)
    max_depth: int = Field(3, ge=1, le=8)


class SiteAuditSummary(BaseModel):
    total_pages: int
    total_issues: int
    errors: int
    warnings: int
    notices: int
    avg_response_time_ms: float
    score: int
    issues_by_category: dict[str, int]


# --- Core Web Vitals --------------------------------------------------------
class CoreWebVitalsResponse(BaseModel):
    id: UUID
    url: str
    strategy: str
    lcp_ms: float | None = None
    inp_ms: float | None = None
    cls: float | None = None
    fcp_ms: float | None = None
    ttfb_ms: float | None = None
    si_ms: float | None = None
    tbt_ms: float | None = None
    performance_score: int | None = None
    seo_score: int | None = None
    accessibility_score: int | None = None
    best_practices_score: int | None = None
    opportunities: list[Any] = []
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Schema markup ----------------------------------------------------------
class SchemaMarkupResponse(BaseModel):
    id: UUID
    url: str
    schema_type: str
    is_valid: bool
    validation_errors: list[str] = []
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Anchor texts -----------------------------------------------------------
class AnchorTextResponse(BaseModel):
    id: UUID
    anchor: str
    classification: str
    count: int
    referring_domains: int
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Toxic backlinks --------------------------------------------------------
class ToxicBacklinkResponse(BaseModel):
    id: UUID
    referring_domain: str
    target_url: str | None = None
    spam_score: float
    reasons: list[str] = []
    disavowed: bool
    discovered_at: datetime

    model_config = {"from_attributes": True}


# --- Link intersect ---------------------------------------------------------
class LinkIntersectResponse(BaseModel):
    id: UUID
    referring_domain: str
    competitor_count: int
    competitors: list[str] = []
    domain_authority: float
    discovered_at: datetime

    model_config = {"from_attributes": True}


# --- Keyword ideas ----------------------------------------------------------
class KeywordIdeaResponse(BaseModel):
    id: UUID
    seed: str
    keyword: str
    match_type: str
    intent: str
    volume: int
    difficulty: int
    cpc: float
    competition: float
    serp_features: list[str] = []
    parent_topic: str | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class KeywordMagicRequest(BaseModel):
    seed: str = Field(..., min_length=1, max_length=255)
    location: str = "us"
    include_questions: bool = True
    limit: int = Field(50, ge=10, le=500)


# --- SERP overview ----------------------------------------------------------
class SerpOverviewResponse(BaseModel):
    id: UUID
    keyword_text: str
    location: str
    device: str
    results: list[Any] = []
    features_present: list[str] = []
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Content brief / optimizer / clusters -----------------------------------
class ContentBriefRequest(BaseModel):
    target_keyword: str = Field(..., min_length=1)
    competitors: list[str] | None = None
    target_word_count: int = 1500


class ContentBriefResponse(BaseModel):
    id: UUID
    target_keyword: str
    title_suggestions: list[str] = []
    h1: str | None = None
    outline: list[Any] = []
    semantic_terms: list[str] = []
    questions_to_answer: list[str] = []
    target_word_count: int
    avg_competitor_words: int
    competitors_analyzed: list[str] = []
    readability_target: str
    notes: str | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class ContentOptimizerRequest(BaseModel):
    target_keyword: str
    content: str = Field(..., min_length=1)
    url: str | None = None


class ContentOptimizerResponse(BaseModel):
    id: UUID
    target_keyword: str
    url: str | None = None
    word_count: int
    readability_score: float
    grade_level: str | None = None
    keyword_density: float
    headings_score: int
    semantic_coverage: float
    overall_score: int
    suggestions: list[Any] = []
    timestamp: datetime

    model_config = {"from_attributes": True}


class TopicClusterResponse(BaseModel):
    id: UUID
    pillar_topic: str
    pillar_url: str | None = None
    supporting_topics: list[Any] = []
    total_volume: int
    coverage_score: int
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Local SEO --------------------------------------------------------------
class LocalCitationResponse(BaseModel):
    id: UUID
    directory: str
    listing_url: str | None = None
    business_name: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    consistency_score: int
    issues: list[str] = []
    status: str
    discovered_at: datetime

    model_config = {"from_attributes": True}


class LocalRankGridCell(BaseModel):
    id: UUID
    keyword: str
    grid_lat: float
    grid_lng: float
    rank: int | None = None
    radius_km: float
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Logs / Reports ---------------------------------------------------------
class LogEventResponse(BaseModel):
    id: UUID
    bot: str
    url: str
    status_code: int
    hits: int
    last_crawled: datetime

    model_config = {"from_attributes": True}


class ReportRequest(BaseModel):
    report_type: str = "full_seo"
    title: str
    branding: dict = {}


class GeneratedReportResponse(BaseModel):
    id: UUID
    report_type: str
    title: str
    file_url: str | None = None
    summary: dict = {}
    status: str
    timestamp: datetime

    model_config = {"from_attributes": True}
