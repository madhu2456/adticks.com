"""
AdTicks — Content analysis schemas.
"""

from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# ContentAnalysis Schemas
# ============================================================================
class ContentAnalysisBase(BaseModel):
    """Base content analysis."""
    url: str = Field(description="URL being analyzed")
    primary_keyword: str | None = Field(None, description="Primary keyword")


class ContentAnalysisResponse(ContentAnalysisBase):
    """Content analysis response."""
    id: UUID = Field(description="Analysis ID")
    project_id: UUID = Field(description="Project ID")
    
    # Word count metrics
    total_words: int = Field(description="Total word count")
    unique_words: int = Field(description="Unique word count")
    paragraphs: int = Field(description="Number of paragraphs")
    sentences: int = Field(description="Number of sentences")
    
    # Readability metrics
    reading_level: str | None = Field(None, description="Reading level (e.g., Grade 8)")
    flesch_reading_ease: float | None = Field(None, description="Flesch Reading Ease score 0-100")
    flesch_kincaid_grade: float | None = Field(None, description="Flesch Kincaid Grade Level")
    
    # Keyword metrics
    keyword_density: dict[str, float] = Field(default_factory=dict, description="Keyword density percentages")
    keyword_frequency: dict[str, int] = Field(default_factory=dict, description="Keyword frequencies")
    
    # Heading structure
    heading_structure: list[dict[str, str | int]] = Field(default_factory=list, description="Heading structure")
    h2_tags: int = Field(description="Number of H2 tags")
    h3_tags: int = Field(description="Number of H3 tags")
    h4_tags: int = Field(description="Number of H4 tags")
    
    # Lists
    ordered_lists: int = Field(description="Number of ordered lists")
    unordered_lists: int = Field(description="Number of unordered lists")
    
    # Text formatting
    bold_count: int = Field(description="Number of bold elements")
    italic_count: int = Field(description="Number of italic elements")
    
    # Issues and recommendations
    issues: list[dict[str, Any]] = Field(default_factory=list, description="Issues found")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")
    
    score: int = Field(description="Analysis score 0-100")
    timestamp: datetime = Field(description="When analysis was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ImageAudit Schemas
# ============================================================================
class ImageAuditBase(BaseModel):
    """Base image audit."""
    url: str = Field(description="Page URL")
    image_url: str = Field(description="Image URL")
    alt_text: str | None = Field(None, description="Alt text")
    title_text: str | None = Field(None, description="Title text")


class ImageAuditResponse(ImageAuditBase):
    """Image audit response."""
    id: UUID = Field(description="Audit ID")
    project_id: UUID = Field(description="Project ID")
    has_alt: bool = Field(description="Has alt text")
    file_size_bytes: int | None = Field(None, description="File size in bytes")
    dimensions: dict[str, int] = Field(default_factory=dict, description="Image dimensions (width, height)")
    file_type: str | None = Field(None, description="File type (jpg, png, webp, etc)")
    is_optimized: bool = Field(description="Image is optimized")
    optimization_suggestions: list[str] = Field(default_factory=list, description="Optimization suggestions")
    timestamp: datetime = Field(description="When audit was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DuplicateContent Schemas
# ============================================================================
class DuplicateContentBase(BaseModel):
    """Base duplicate content."""
    page_url: str = Field(description="Page URL")
    duplicate_urls: list[str] = Field(default_factory=list, description="Duplicate URLs")


class DuplicateContentResponse(DuplicateContentBase):
    """Duplicate content response."""
    id: UUID = Field(description="Detection ID")
    project_id: UUID = Field(description="Project ID")
    similarity_percentage: float = Field(description="Similarity percentage 0-100")
    duplicate_type: str = Field(description="Type of duplicate (exact, near, canonical)")
    primary_url: str | None = Field(None, description="Primary URL for this content")
    hash_value: str | None = Field(None, description="Content hash value")
    timestamp: datetime = Field(description="When detection was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SEORecommendation Schemas
# ============================================================================
class SEORecommendationBase(BaseModel):
    """Base SEO recommendation."""
    recommendation_type: str = Field(description="Recommendation type")
    title: str = Field(description="Recommendation title")
    description: str = Field(description="Recommendation description")


class SEORecommendationResponse(SEORecommendationBase):
    """SEO recommendation response."""
    id: UUID = Field(description="Recommendation ID")
    project_id: UUID = Field(description="Project ID")
    priority: str = Field(description="Priority (critical, high, medium, low)")
    estimated_impact: str = Field(description="Estimated impact (low, medium, high)")
    affected_urls: list[str] = Field(default_factory=list, description="Affected URLs")
    implementation_steps: list[str] = Field(default_factory=list, description="Implementation steps")
    resources_needed: list[str] = Field(default_factory=list, description="Resources needed")
    estimated_effort: str | None = Field(None, description="Estimated effort")
    quick_win: bool = Field(description="Is quick win")
    status: str = Field(description="Status (pending, in_progress, done)")
    timestamp: datetime = Field(description="When recommendation was created")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# URLRedirect Schemas
# ============================================================================
class URLRedirectBase(BaseModel):
    """Base URL redirect."""
    source_url: str = Field(description="Source URL")
    target_url: str = Field(description="Target URL")
    status_code: int = Field(description="HTTP status code (301, 302, 307, 308)")


class URLRedirectResponse(URLRedirectBase):
    """URL redirect response."""
    id: UUID = Field(description="Redirect ID")
    project_id: UUID = Field(description="Project ID")
    is_chain: bool = Field(description="Is redirect chain")
    chain_length: int | None = Field(None, description="Chain length")
    is_broken: bool = Field(description="Target is broken")
    redirect_reason: str | None = Field(None, description="Reason for redirect")
    last_checked: datetime | None = Field(None, description="Last check time")
    timestamp: datetime = Field(description="When redirect was created")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BrokenLink Schemas
# ============================================================================
class BrokenLinkBase(BaseModel):
    """Base broken link."""
    source_url: str = Field(description="Source URL")
    broken_url: str = Field(description="Broken URL")
    status_code: int = Field(description="HTTP status code")


class BrokenLinkResponse(BrokenLinkBase):
    """Broken link response."""
    id: UUID = Field(description="Link ID")
    project_id: UUID = Field(description="Project ID")
    link_type: str = Field(description="Link type (internal/external)")
    anchor_text: str | None = Field(None, description="Anchor text")
    first_detected: datetime = Field(description="When link was first detected")
    last_checked: datetime = Field(description="When link was last checked")
    status: str = Field(description="Status (active/fixed)")
    timestamp: datetime = Field(description="When record was created")

    model_config = ConfigDict(from_attributes=True)
