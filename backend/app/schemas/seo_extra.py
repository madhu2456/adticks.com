"""Pydantic schemas for the gap-fill SEO features."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Cannibalization --------------------------------------------------------
class CannibalizationResponse(BaseModel):
    id: UUID
    keyword: str
    urls: list[Any] = []
    severity: str
    recommendation: str | None = None
    detected_at: datetime
    model_config = {"from_attributes": True}


class CannibalizationRunRequest(BaseModel):
    rows: list[dict[str, Any]] | None = Field(
        None,
        description="Optional list of {keyword, url, position, clicks, impressions}; if omitted, server uses GSC + rankings",
    )
    min_pages: int = Field(2, ge=2, le=10)


# --- Internal links ---------------------------------------------------------
class InternalLinkResponse(BaseModel):
    id: UUID
    source_url: str
    target_url: str
    anchor_text: str | None = None
    is_nofollow: bool
    link_position: str
    timestamp: datetime
    model_config = {"from_attributes": True}


class OrphanPageResponse(BaseModel):
    id: UUID
    url: str
    in_sitemap: bool
    page_authority: float
    detected_at: datetime
    model_config = {"from_attributes": True}


class InternalLinkAnalyzeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=500)


# --- Domain comparison ------------------------------------------------------
class DomainComparisonRequest(BaseModel):
    primary_domain: str
    competitor_domains: list[str] = Field(default_factory=list, max_length=10)


class DomainComparisonResponse(BaseModel):
    id: UUID
    primary_domain: str
    competitor_domains: list[str]
    metrics: dict
    timestamp: datetime
    model_config = {"from_attributes": True}


# --- Bulk analyzer ----------------------------------------------------------
class BulkAnalysisRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=200)
    job_type: str = Field("onpage", description="onpage | cwv")


class BulkAnalysisItemResponse(BaseModel):
    id: UUID
    url: str
    status: str
    result: dict = {}
    error: str | None = None
    model_config = {"from_attributes": True}


class BulkAnalysisJobResponse(BaseModel):
    id: UUID
    job_type: str
    status: str
    total_urls: int
    completed_urls: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    timestamp: datetime
    model_config = {"from_attributes": True}


# --- Sitemap / robots / schema ----------------------------------------------
class SitemapGenerateRequest(BaseModel):
    urls: list[dict[str, Any]] = Field(..., min_length=1)
    default_changefreq: str = "weekly"
    default_priority: float = 0.7


class SitemapGenerationResponse(BaseModel):
    id: UUID
    url_count: int
    file_url: str | None = None
    xml_preview: str | None = None
    timestamp: datetime
    model_config = {"from_attributes": True}


class RobotsValidationRequest(BaseModel):
    url: str | None = None
    raw_content: str | None = None


class RobotsValidationResponse(BaseModel):
    id: UUID
    url: str
    raw_content: str | None = None
    is_valid: bool
    issues: list = []
    rules: list = []
    sitemap_directives: list[str] = []
    timestamp: datetime
    model_config = {"from_attributes": True}


class SchemaGenerateRequest(BaseModel):
    schema_type: str
    name: str
    inputs: dict


class SchemaTemplateResponse(BaseModel):
    id: UUID
    schema_type: str
    name: str
    inputs: dict
    json_ld: dict
    timestamp: datetime
    model_config = {"from_attributes": True}


# --- Outreach ---------------------------------------------------------------
class OutreachCampaignCreate(BaseModel):
    name: str
    goal: str | None = None
    target_link_count: int = 0


class OutreachCampaignResponse(BaseModel):
    id: UUID
    name: str
    goal: str | None = None
    status: str
    target_link_count: int
    won_link_count: int
    timestamp: datetime
    model_config = {"from_attributes": True}


class OutreachProspectCreate(BaseModel):
    domain: str
    contact_email: str | None = None
    contact_name: str | None = None
    domain_authority: float = 0.0
    notes: str | None = None


class OutreachProspectUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    won_link_url: str | None = None


class OutreachProspectResponse(BaseModel):
    id: UUID
    domain: str
    contact_email: str | None = None
    contact_name: str | None = None
    status: str
    last_contacted_at: datetime | None = None
    domain_authority: float
    notes: str | None = None
    won_link_url: str | None = None
    timestamp: datetime
    model_config = {"from_attributes": True}


# --- Featured snippet / PAA / volatility -----------------------------------
class FeaturedSnippetResponse(BaseModel):
    id: UUID
    keyword: str
    we_own: bool
    current_owner_url: str | None = None
    snippet_text: str | None = None
    snippet_type: str | None = None
    last_checked: datetime
    model_config = {"from_attributes": True}


class PAAQuestionResponse(BaseModel):
    id: UUID
    seed_keyword: str
    question: str
    answer_url: str | None = None
    answer_snippet: str | None = None
    timestamp: datetime
    model_config = {"from_attributes": True}


class SerpVolatilityEventResponse(BaseModel):
    id: UUID
    keyword: str
    previous_position: int | None = None
    current_position: int | None = None
    delta: int
    direction: str
    detected_at: datetime
    model_config = {"from_attributes": True}


class SerpVolatilityScanRequest(BaseModel):
    rank_diffs: list[dict[str, Any]] = Field(...,
        description="List of {keyword, previous_position, current_position}")
    drop_threshold: int = 5
    rise_threshold: int = 5
