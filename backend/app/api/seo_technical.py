"""
AdTicks — XML Sitemap and robots.txt generation endpoints.
"""

from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.user import User
from app.models.keyword import Keyword

router = APIRouter(prefix="/seo", tags=["seo"])


async def _assert_project_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


# ============================================================================
# XML Sitemap Endpoints
# ============================================================================

@router.get("/sitemap/{project_id}.xml", response_class=Response)
async def get_sitemap_xml(
    project_id: UUID,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate XML sitemap for the project.
    
    Returns sitemap in standard XML format for search engines.
    Supports pagination with /sitemap-{page}.xml format.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    items_per_page = 50000  # Google limit
    offset = (page - 1) * items_per_page
    
    # Get URLs from keywords (assuming these are tracked URLs)
    result = await db.execute(
        select(Keyword.keyword, func.max(Keyword.created_at).label("updated_at"))
        .where(Keyword.project_id == project_id)
        .group_by(Keyword.keyword)
        .offset(offset)
        .limit(items_per_page)
    )
    keywords = result.all()
    
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No URLs found for sitemap"
        )
    
    # Build sitemap XML
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for keyword, updated_at in keywords:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{keyword}</loc>\n'
        if updated_at:
            sitemap_xml += f'    <lastmod>{updated_at.date().isoformat()}</lastmod>\n'
        sitemap_xml += '    <changefreq>weekly</changefreq>\n'
        sitemap_xml += '    <priority>0.8</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    return Response(content=sitemap_xml, media_type="application/xml")


@router.get("/sitemap/{project_id}/index.xml", response_class=Response)
async def get_sitemap_index(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate sitemap index XML for large sites.
    
    Returns index file that references multiple sitemap pages.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    # Get total URL count
    result = await db.execute(
        select(func.count(func.distinct(Keyword.keyword)))
        .where(Keyword.project_id == project_id)
    )
    total_urls = result.scalar() or 0
    
    if total_urls == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No URLs found for sitemap"
        )
    
    items_per_page = 50000
    total_pages = (total_urls + items_per_page - 1) // items_per_page
    
    # Build sitemap index XML
    sitemap_index = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_index += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page_num in range(1, total_pages + 1):
        sitemap_index += '  <sitemap>\n'
        sitemap_index += f'    <loc>https://api.adticks.com/api/seo/sitemap/{project_id}-{page_num}.xml</loc>\n'
        sitemap_index += f'    <lastmod>{datetime.now(tz=timezone.utc).date().isoformat()}</lastmod>\n'
        sitemap_index += '  </sitemap>\n'
    
    sitemap_index += '</sitemapindex>'
    
    return Response(content=sitemap_index, media_type="application/xml")


@router.get("/sitemap/{project_id}.txt", response_class=Response)
async def get_sitemap_txt(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate text-format sitemap (one URL per line).
    
    Alternative format for simpler sitemap delivery.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    result = await db.execute(
        select(Keyword.keyword)
        .where(Keyword.project_id == project_id)
        .order_by(Keyword.created_at.desc())
        .limit(50000)
    )
    keywords = result.scalars().all()
    
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No URLs found for sitemap"
        )
    
    sitemap_text = "\n".join(keywords)
    
    return Response(content=sitemap_text, media_type="text/plain")


# ============================================================================
# robots.txt Endpoints
# ============================================================================

@router.get("/robots.txt/{project_id}", response_class=Response)
async def get_robots_txt(
    project_id: UUID,
    allow_ai: bool = Query(True, description="Allow AI bots"),
    crawl_delay: int = Query(1, ge=0, le=60, description="Crawl delay in seconds"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate robots.txt for the project.
    
    Returns robots.txt with configurable crawl rules for different bots.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    robots_txt = "# AdTicks Auto-Generated robots.txt\n"
    robots_txt += f"# Generated: {datetime.now(tz=timezone.utc).isoformat()}\n\n"
    
    # Google
    robots_txt += "User-agent: Googlebot\n"
    robots_txt += "Allow: /\n"
    if crawl_delay:
        robots_txt += f"Crawl-delay: {crawl_delay}\n"
    robots_txt += "\n"
    
    # Bing
    robots_txt += "User-agent: Bingbot\n"
    robots_txt += "Allow: /\n"
    if crawl_delay:
        robots_txt += f"Crawl-delay: {crawl_delay}\n"
    robots_txt += "\n"
    
    # AI Bots (optional)
    if not allow_ai:
        robots_txt += "User-agent: GPTBot\n"
        robots_txt += "Disallow: /\n\n"
        robots_txt += "User-agent: CCBot\n"
        robots_txt += "Disallow: /\n\n"
        robots_txt += "User-agent: anthropic-ai\n"
        robots_txt += "Disallow: /\n\n"
    
    # Bad bots
    robots_txt += "User-agent: AhrefsBot\n"
    robots_txt += "Disallow: /\n\n"
    
    robots_txt += "User-agent: SemrushBot\n"
    robots_txt += "Disallow: /\n\n"
    
    # Sitemap
    robots_txt += f"Sitemap: https://api.adticks.com/api/seo/sitemap/{project_id}/index.xml\n"
    
    return Response(content=robots_txt, media_type="text/plain")


@router.post("/sitemap/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_sitemap_to_search_engines(
    project_id: UUID,
    gsc_enabled: bool = Query(True, description="Submit to Google Search Console"),
    bing_webmaster: bool = Query(True, description="Submit to Bing Webmaster"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit sitemap to search engines (Google Search Console, Bing Webmaster).
    
    Requires GSC/Bing authentication on the project.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        from app.tasks.seo_tasks import submit_sitemap_task
        task = submit_sitemap_task.delay(
            project_id=str(project_id),
            gsc_enabled=gsc_enabled,
            bing_webmaster=bing_webmaster,
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Sitemap submission started",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue task: {str(e)}"
        )


# ============================================================================
# Canonical URL Endpoints
# ============================================================================

@router.get("/canonical/{project_id}")
async def get_canonical_url_report(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get canonical URL audit report.
    
    Identifies pages with missing, incorrect, or conflicting canonical tags.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    return {
        "message": "Canonical URL audit not yet implemented. Use /seo/audit/crawlability for canonical tag checks."
    }


# ============================================================================
# Hreflang Tags Endpoints
# ============================================================================

@router.get("/hreflang/{project_id}")
async def get_hreflang_report(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get hreflang tag audit report for international SEO.
    
    Identifies missing, incorrect, or conflicting hreflang annotations.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    return {
        "message": "Hreflang audit endpoint placeholder. Implement hreflang validation for international sites."
    }
