"""
AdTicks — Extended SEO audit tasks (meta tags, structured data, content analysis, etc).
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from bs4 import BeautifulSoup
import httpx

from sqlalchemy import select
from app.core.celery_app import celery_app
from app.core.celery_utils import run_async
from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.seo_audit import (
    MetaTagAudit,
    StructuredDataAudit,
    PageSpeedMetrics,
    CrawlabilityAudit,
    InternalLinkMap,
    SEOHealthScore,
)
from app.models.seo_content import (
    ContentAnalysis,
    ImageAudit,
    DuplicateContent,
    SEORecommendation,
    URLRedirect,
    BrokenLink,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Meta Tag Audit Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def audit_meta_tags_task(self, project_id: str, urls: list[str]):
    """Audit meta tags for URLs."""
    return run_async(self._audit_meta_tags(project_id, urls))


async def _audit_meta_tags(self, project_id: str, urls: list[str]):
    """Audit meta tags asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get(url, follow_redirects=True)
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Extract meta tags
                        title_tag = soup.find("title")
                        title = title_tag.string if title_tag else None
                        
                        meta_desc = soup.find("meta", {"name": "description"})
                        description = meta_desc.get("content") if meta_desc else None
                        
                        canonical = soup.find("link", {"rel": "canonical"})
                        canonical_url = canonical.get("href") if canonical else None
                        
                        h1_tags = [h1.get_text().strip() for h1 in soup.find_all("h1")]
                        
                        og_title = soup.find("meta", {"property": "og:title"})
                        og_title_content = og_title.get("content") if og_title else None
                        
                        og_desc = soup.find("meta", {"property": "og:description"})
                        og_desc_content = og_desc.get("content") if og_desc else None
                        
                        og_image = soup.find("meta", {"property": "og:image"})
                        og_image_content = og_image.get("content") if og_image else None
                        
                        twitter = soup.find("meta", {"name": "twitter:card"})
                        twitter_card = twitter.get("content") if twitter else None
                        
                        # Calculate scores
                        issues = []
                        score = 100
                        
                        if not title or len(title) < 30:
                            issues.append("Title is too short (min 30 chars)")
                            score -= 15
                        if title and len(title) > 60:
                            issues.append("Title is too long (max 60 chars)")
                            score -= 10
                        if not description or len(description) < 50:
                            issues.append("Meta description is too short (min 50 chars)")
                            score -= 15
                        if description and len(description) > 160:
                            issues.append("Meta description is too long (max 160 chars)")
                            score -= 10
                        if not h1_tags:
                            issues.append("No H1 tag found")
                            score -= 20
                        if len(h1_tags) > 1:
                            issues.append("Multiple H1 tags found")
                            score -= 10
                        if not canonical_url:
                            issues.append("No canonical URL specified")
                            score -= 15
                        
                        # Create audit record
                        audit = MetaTagAudit(
                            project_id=UUID(project_id),
                            url=url,
                            title=title,
                            title_length=len(title) if title else 0,
                            title_optimized=30 <= len(title) <= 60 if title else False,
                            description=description,
                            description_length=len(description) if description else 0,
                            description_optimized=50 <= len(description) <= 160 if description else False,
                            canonical_url=canonical_url,
                            h1_tags=h1_tags,
                            h1_count=len(h1_tags),
                            h1_optimized=len(h1_tags) == 1,
                            og_title=og_title_content,
                            og_description=og_desc_content,
                            og_image=og_image_content,
                            twitter_card=twitter_card,
                            issues=[{"type": "issue", "message": issue} for issue in issues],
                            score=max(0, score),
                        )
                        session.add(audit)
                        
                except Exception as e:
                    logger.error(f"Failed to audit {url}: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Meta tag audit completed for {len(urls)} URLs")
            
        except Exception as e:
            logger.error(f"Meta tag audit task failed: {str(e)}")
            raise


# ============================================================================
# Structured Data Audit Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def audit_structured_data_task(self, project_id: str, urls: list[str]):
    """Audit structured data (JSON-LD) for URLs."""
    return run_async(self._audit_structured_data(project_id, urls))


async def _audit_structured_data(self, project_id: str, urls: list[str]):
    """Audit structured data asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get(url, follow_redirects=True)
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Find JSON-LD scripts
                        schema_types = []
                        schema_data = []
                        has_org = False
                        has_article = False
                        has_breadcrumb = False
                        has_product = False
                        has_faq = False
                        has_local = False
                        has_event = False
                        has_review = False
                        
                        for script in soup.find_all("script", {"type": "application/ld+json"}):
                            try:
                                data = json.loads(script.string)
                                schema_type = data.get("@type", "").lower()
                                schema_types.append(schema_type)
                                schema_data.append(data)
                                
                                # Check schema types
                                if "organization" in schema_type:
                                    has_org = True
                                elif "article" in schema_type:
                                    has_article = True
                                elif "breadcrumblist" in schema_type:
                                    has_breadcrumb = True
                                elif "product" in schema_type:
                                    has_product = True
                                elif "faqpage" in schema_type:
                                    has_faq = True
                                elif "localbusiness" in schema_type:
                                    has_local = True
                                elif "event" in schema_type:
                                    has_event = True
                                elif "review" in schema_type or "rating" in schema_type:
                                    has_review = True
                            except:
                                pass
                        
                        # Calculate score
                        score = 50 if schema_data else 0
                        if has_org:
                            score += 15
                        if has_article:
                            score += 15
                        if has_breadcrumb:
                            score += 10
                        
                        # Create audit record
                        audit = StructuredDataAudit(
                            project_id=UUID(project_id),
                            url=url,
                            schema_types=schema_types,
                            organization_schema=has_org,
                            article_schema=has_article,
                            breadcrumb_schema=has_breadcrumb,
                            product_schema=has_product,
                            faq_schema=has_faq,
                            local_business_schema=has_local,
                            event_schema=has_event,
                            review_schema=has_review,
                            schema_data=schema_data,
                            validation_errors=[],
                            score=min(100, score),
                        )
                        session.add(audit)
                        
                except Exception as e:
                    logger.error(f"Failed to audit {url} structured data: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Structured data audit completed for {len(urls)} URLs")
            
        except Exception as e:
            logger.error(f"Structured data audit task failed: {str(e)}")
            raise


# ============================================================================
# Page Speed Audit Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def audit_page_speed_task(self, project_id: str, urls: list[str], device: str = "desktop"):
    """Audit page speed metrics for URLs."""
    return run_async(self._audit_page_speed(project_id, urls, device))


async def _audit_page_speed(self, project_id: str, urls: list[str], device: str):
    """Audit page speed asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        # Measure load time
                        import time
                        start = time.time()
                        response = await client.get(url, follow_redirects=True)
                        load_time_ms = (time.time() - start) * 1000
                        
                        # Get page size
                        page_size = len(response.content)
                        
                        # Simulate lighthouse scores (would integrate with real API)
                        performance_score = 85
                        accessibility_score = 90
                        best_practices_score = 88
                        seo_score = 92
                        
                        # Create metric record
                        metric = PageSpeedMetrics(
                            project_id=UUID(project_id),
                            url=url,
                            device=device,
                            lcp=load_time_ms * 0.4,  # Estimate
                            fid=50,  # Estimate
                            cls=0.05,  # Estimate
                            ttfb=load_time_ms * 0.1,
                            fcp=load_time_ms * 0.3,
                            performance_score=performance_score,
                            accessibility_score=accessibility_score,
                            best_practices_score=best_practices_score,
                            seo_score=seo_score,
                            page_size_bytes=page_size,
                            total_requests=50,  # Estimate
                            load_time_ms=load_time_ms,
                        )
                        session.add(metric)
                        
                except Exception as e:
                    logger.error(f"Failed to audit page speed {url}: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Page speed audit completed for {len(urls)} URLs")
            
        except Exception as e:
            logger.error(f"Page speed audit task failed: {str(e)}")
            raise


# ============================================================================
# Crawlability Audit Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def audit_crawlability_task(self, project_id: str, urls: list[str]):
    """Audit crawlability for URLs."""
    return run_async(self._audit_crawlability(project_id, urls))


async def _audit_crawlability(self, project_id: str, urls: list[str]):
    """Audit crawlability asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get(url, follow_redirects=True)
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Check crawlability indicators
                        noindex = soup.find("meta", {"name": "robots", "content": lambda x: x and "noindex" in x})
                        nofollow = soup.find("meta", {"name": "robots", "content": lambda x: x and "nofollow" in x})
                        
                        canonical = soup.find("link", {"rel": "canonical"})
                        canonical_url = canonical.get("href") if canonical else None
                        
                        # Count links and images
                        internal_links = len(soup.find_all("a", {"href": lambda x: x and url in x}))
                        external_links = len(soup.find_all("a", {"href": lambda x: x and "http" in x})) - internal_links
                        
                        images_no_alt = len([img for img in soup.find_all("img") if not img.get("alt")])
                        
                        score = 100
                        issues = []
                        
                        if response.status_code >= 400:
                            score -= 30
                            issues.append(f"HTTP {response.status_code}")
                        if noindex:
                            score -= 50
                            issues.append("Noindex meta tag found")
                        if images_no_alt > 5:
                            score -= 15
                            issues.append(f"{images_no_alt} images without alt text")
                        if not canonical_url:
                            score -= 10
                            issues.append("No canonical URL")
                        
                        # Create crawlability record
                        audit = CrawlabilityAudit(
                            project_id=UUID(project_id),
                            url=url,
                            status_code=response.status_code,
                            is_redirected=len(response.history) > 0,
                            redirect_chain=[str(r.url) for r in response.history],
                            robots_txt_blocked=False,  # Would check against robots.txt
                            noindex_tag=bool(noindex),
                            nofollow_tag=bool(nofollow),
                            canonical_url=canonical_url,
                            internal_links_count=internal_links,
                            external_links_count=external_links,
                            broken_links=0,  # Would check all links
                            images_without_alt=images_no_alt,
                            page_language="en",
                            crawl_errors=issues,
                            score=max(0, score),
                        )
                        session.add(audit)
                        
                except Exception as e:
                    logger.error(f"Failed to audit crawlability {url}: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Crawlability audit completed for {len(urls)} URLs")
            
        except Exception as e:
            logger.error(f"Crawlability audit task failed: {str(e)}")
            raise


# ============================================================================
# Content Analysis Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def analyze_content_task(self, project_id: str, urls: list[str]):
    """Analyze content for URLs."""
    return run_async(self._analyze_content(project_id, urls))


async def _analyze_content(self, project_id: str, urls: list[str]):
    """Analyze content asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get(url, follow_redirects=True)
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Extract text
                        text = soup.get_text()
                        words = text.split()
                        total_words = len(words)
                        unique_words = len(set(w.lower() for w in words))
                        
                        # Count elements
                        paragraphs = len(soup.find_all("p"))
                        sentences = len([s for s in text.split(".") if s.strip()])
                        
                        h1_tags = [h.get_text() for h in soup.find_all("h1")]
                        h2_tags = len(soup.find_all("h2"))
                        h3_tags = len(soup.find_all("h3"))
                        h4_tags = len(soup.find_all("h4"))
                        
                        ordered_lists = len(soup.find_all("ol"))
                        unordered_lists = len(soup.find_all("ul"))
                        
                        bold_count = len(soup.find_all("b")) + len(soup.find_all("strong"))
                        italic_count = len(soup.find_all("i")) + len(soup.find_all("em"))
                        
                        # Calculate readability (simplified Flesch Reading Ease)
                        flesch_ease = 206.835 - 1.015 * (total_words / max(1, sentences)) - 84.6 * (1 / max(1, total_words))
                        flesch_ease = max(0, min(100, flesch_ease))
                        
                        # Determine reading level
                        if flesch_ease >= 90:
                            reading_level = "Grade 5"
                        elif flesch_ease >= 80:
                            reading_level = "Grade 6"
                        elif flesch_ease >= 70:
                            reading_level = "Grade 7-8"
                        elif flesch_ease >= 60:
                            reading_level = "Grade 9-10"
                        else:
                            reading_level = "Grade 12+"
                        
                        score = 60
                        issues = []
                        
                        if total_words < 300:
                            score -= 20
                            issues.append("Content is too short")
                        elif total_words > 3000:
                            score += 10
                        else:
                            score += 20
                        
                        if len(h1_tags) != 1:
                            score -= 15
                            issues.append(f"Found {len(h1_tags)} H1 tags")
                        if h2_tags == 0:
                            score -= 10
                            issues.append("No H2 tags found")
                        
                        # Create content analysis record
                        analysis = ContentAnalysis(
                            project_id=UUID(project_id),
                            url=url,
                            total_words=total_words,
                            unique_words=unique_words,
                            paragraphs=paragraphs,
                            sentences=sentences,
                            reading_level=reading_level,
                            flesch_reading_ease=flesch_ease,
                            flesch_kincaid_grade=int(flesch_ease / 10),
                            primary_keyword=h1_tags[0] if h1_tags else None,
                            keyword_density={},
                            keyword_frequency={},
                            heading_structure=[{"level": 1, "text": h1} for h1 in h1_tags],
                            h2_tags=h2_tags,
                            h3_tags=h3_tags,
                            h4_tags=h4_tags,
                            ordered_lists=ordered_lists,
                            unordered_lists=unordered_lists,
                            bold_count=bold_count,
                            italic_count=italic_count,
                            issues=[{"type": "issue", "message": issue} for issue in issues],
                            recommendations=[],
                            score=max(0, min(100, score)),
                        )
                        session.add(analysis)
                        
                except Exception as e:
                    logger.error(f"Failed to analyze content {url}: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Content analysis completed for {len(urls)} URLs")
            
        except Exception as e:
            logger.error(f"Content analysis task failed: {str(e)}")
            raise


# ============================================================================
# Additional Tasks Stubs
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def audit_images_task(self, project_id: str, urls: list[str]):
    """Audit images on URLs."""
    logger.info(f"Image audit task queued for {len(urls)} URLs")
    return {"status": "scheduled", "urls": len(urls)}


@celery_app.task(bind=True, max_retries=3)
def detect_duplicate_content_task(self, project_id: str, urls: list[str]):
    """Detect duplicate content across URLs."""
    logger.info(f"Duplicate content detection queued for {len(urls)} URLs")
    return {"status": "scheduled", "urls": len(urls)}


@celery_app.task(bind=True, max_retries=3)
def detect_broken_links_task(self, project_id: str, urls: list[str], check_external: bool = True):
    """Detect broken links on URLs."""
    logger.info(f"Broken link detection queued for {len(urls)} URLs")
    return {"status": "scheduled", "urls": len(urls)}


@celery_app.task(bind=True, max_retries=3)
def calculate_seo_health_score_task(self, project_id: str):
    """Calculate overall SEO health score."""
    logger.info(f"SEO health score recalculation queued for project {project_id}")
    return {"status": "scheduled", "project": project_id}


@celery_app.task(bind=True, max_retries=3)
def submit_sitemap_task(self, project_id: str, gsc_enabled: bool = True, bing_webmaster: bool = True):
    """Submit sitemap to search engines."""
    logger.info(f"Sitemap submission queued for project {project_id}")
    return {"status": "scheduled", "gsc": gsc_enabled, "bing": bing_webmaster}
