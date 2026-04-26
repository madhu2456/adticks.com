"""
AdTicks — SEO Audit schemas (meta tags, structured data, performance, crawlability).
"""

from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# MetaTagAudit Schemas
# ============================================================================
class MetaTagAuditBase(BaseModel):
    """Base meta tag audit data."""
    url: str = Field(description="URL being audited")
    title: str | None = Field(None, description="Page title")
    description: str | None = Field(None, description="Meta description")
    canonical_url: str | None = Field(None, description="Canonical URL")
    h1_tags: list[str] = Field(default_factory=list, description="H1 tags found")
    og_title: str | None = Field(None, description="Open Graph title")
    og_description: str | None = Field(None, description="Open Graph description")
    og_image: str | None = Field(None, description="Open Graph image URL")
    twitter_card: str | None = Field(None, description="Twitter card type")


class MetaTagAuditResponse(MetaTagAuditBase):
    """Meta tag audit response."""
    id: UUID = Field(description="Audit ID")
    project_id: UUID = Field(description="Project ID")
    title_length: int = Field(description="Title length")
    title_optimized: bool = Field(description="Title is optimized")
    description_length: int = Field(description="Description length")
    description_optimized: bool = Field(description="Description is optimized")
    h1_count: int = Field(description="Number of H1 tags")
    h1_optimized: bool = Field(description="H1 structure is optimized")
    issues: list[dict[str, Any]] = Field(default_factory=list, description="Issues found")
    score: int = Field(description="Audit score 0-100")
    timestamp: datetime = Field(description="When audit was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# StructuredDataAudit Schemas
# ============================================================================
class StructuredDataAuditBase(BaseModel):
    """Base structured data audit."""
    url: str = Field(description="URL being audited")
    schema_types: list[str] = Field(default_factory=list, description="Schema types found")


class StructuredDataAuditResponse(StructuredDataAuditBase):
    """Structured data audit response."""
    id: UUID = Field(description="Audit ID")
    project_id: UUID = Field(description="Project ID")
    organization_schema: bool = Field(description="Has Organization schema")
    article_schema: bool = Field(description="Has Article schema")
    breadcrumb_schema: bool = Field(description="Has BreadcrumbList schema")
    product_schema: bool = Field(description="Has Product schema")
    faq_schema: bool = Field(description="Has FAQ schema")
    local_business_schema: bool = Field(description="Has LocalBusiness schema")
    event_schema: bool = Field(description="Has Event schema")
    review_schema: bool = Field(description="Has Review schema")
    schema_data: list[dict[str, Any]] = Field(default_factory=list, description="Schema markup data")
    validation_errors: list[dict[str, Any]] = Field(default_factory=list, description="Validation errors")
    score: int = Field(description="Audit score 0-100")
    timestamp: datetime = Field(description="When audit was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PageSpeedMetrics Schemas
# ============================================================================
class PageSpeedMetricsBase(BaseModel):
    """Base page speed metrics."""
    url: str = Field(description="URL being measured")
    device: str = Field("desktop", description="Device type (desktop/mobile)")


class PageSpeedMetricsResponse(PageSpeedMetricsBase):
    """Page speed metrics response."""
    id: UUID = Field(description="Metric ID")
    project_id: UUID = Field(description="Project ID")
    
    # Core Web Vitals
    lcp: float | None = Field(None, description="Largest Contentful Paint (ms)")
    fid: float | None = Field(None, description="First Input Delay (ms)")
    cls: float | None = Field(None, description="Cumulative Layout Shift")
    ttfb: float | None = Field(None, description="Time to First Byte (ms)")
    fcp: float | None = Field(None, description="First Contentful Paint (ms)")
    
    # Performance scores
    performance_score: int | None = Field(None, description="Performance score 0-100")
    accessibility_score: int | None = Field(None, description="Accessibility score 0-100")
    best_practices_score: int | None = Field(None, description="Best practices score 0-100")
    seo_score: int | None = Field(None, description="SEO score 0-100")
    
    # Page load info
    page_size_bytes: int | None = Field(None, description="Page size in bytes")
    total_requests: int | None = Field(None, description="Total HTTP requests")
    load_time_ms: float | None = Field(None, description="Total load time in ms")
    
    timestamp: datetime = Field(description="When metrics were captured")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CrawlabilityAudit Schemas
# ============================================================================
class CrawlabilityAuditBase(BaseModel):
    """Base crawlability audit."""
    url: str = Field(description="URL being audited")


class CrawlabilityAuditResponse(CrawlabilityAuditBase):
    """Crawlability audit response."""
    id: UUID = Field(description="Audit ID")
    project_id: UUID = Field(description="Project ID")
    status_code: int | None = Field(None, description="HTTP status code")
    is_redirected: bool = Field(description="Page is redirected")
    redirect_chain: list[str] = Field(default_factory=list, description="Redirect chain URLs")
    robots_txt_blocked: bool = Field(description="Blocked by robots.txt")
    noindex_tag: bool = Field(description="Has noindex tag")
    nofollow_tag: bool = Field(description="Has nofollow tag")
    canonical_url: str | None = Field(None, description="Canonical URL")
    internal_links_count: int = Field(description="Number of internal links")
    external_links_count: int = Field(description="Number of external links")
    broken_links: int = Field(description="Number of broken links")
    images_without_alt: int = Field(description="Images without alt text")
    page_language: str | None = Field(None, description="Page language code")
    crawl_errors: list[str] = Field(default_factory=list, description="Crawl errors encountered")
    score: int = Field(description="Audit score 0-100")
    timestamp: datetime = Field(description="When audit was performed")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# InternalLinkMap Schemas
# ============================================================================
class InternalLinkMapBase(BaseModel):
    """Base internal link map."""
    source_url: str = Field(description="Source URL")
    target_url: str = Field(description="Target URL")
    anchor_text: str = Field(description="Anchor text of the link")


class InternalLinkMapResponse(InternalLinkMapBase):
    """Internal link map response."""
    id: UUID = Field(description="Link ID")
    project_id: UUID = Field(description="Project ID")
    link_type: str = Field(description="Link type (internal/external)")
    is_follow: bool = Field(description="Is nofollow link")
    link_text_length: int = Field(description="Length of anchor text")
    timestamp: datetime = Field(description="When link was discovered")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SEOHealthScore Schemas
# ============================================================================
class SEOHealthScoreResponse(BaseModel):
    """SEO health score response."""
    id: UUID = Field(description="Score ID")
    project_id: UUID = Field(description="Project ID")
    overall_score: int = Field(description="Overall score 0-100")
    technical_score: int = Field(description="Technical score 0-100")
    content_score: int = Field(description="Content score 0-100")
    performance_score: int = Field(description="Performance score 0-100")
    security_score: int = Field(description="Security score 0-100")
    mobile_score: int = Field(description="Mobile score 0-100")
    
    total_pages_crawled: int = Field(description="Total pages crawled")
    pages_with_issues: int = Field(description="Pages with issues")
    critical_issues: int = Field(description="Critical issues count")
    warnings: int = Field(description="Warnings count")
    
    top_opportunities: list[dict[str, Any]] = Field(default_factory=list, description="Top opportunities")
    quick_wins: list[dict[str, Any]] = Field(default_factory=list, description="Quick wins")
    
    last_audit_date: datetime | None = Field(None, description="Last audit date")
    timestamp: datetime = Field(description="When score was calculated")

    model_config = ConfigDict(from_attributes=True)
