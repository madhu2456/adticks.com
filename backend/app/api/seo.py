"""AdTicks SEO router."""
import uuid
from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.caching import cached, invalidate_cache
from app.models.keyword import Keyword, Ranking
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.keyword import KeywordCreate, RankingResponse

router = APIRouter(prefix="/seo", tags=["seo"])


from app.core.component_cache import ComponentCache


async def _assert_project_owner(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/keywords", status_code=status.HTTP_202_ACCEPTED)
async def trigger_keyword_research(
    payload: KeywordCreate,
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger async keyword research for a project.
    
    Creates a new keyword record and queues a background task to perform keyword research.
    The research generates related keywords, estimates search volume, calculates difficulty
    scores, and analyzes search intent. Results are stored and available via /seo/rankings.
    """
    await _assert_project_owner(project_id, current_user, db)
    keyword = Keyword(
        project_id=project_id,
        keyword=payload.keyword,
        intent=payload.intent,
        difficulty=payload.difficulty,
        volume=payload.volume,
    )
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    
    # Invalidate keyword cache
    await invalidate_cache(f"cache:get_rankings:{project_id}:*")
    
    try:
        from app.tasks.seo_tasks import generate_keywords_task
        generate_keywords_task.delay(
            project_id=str(project_id),
            domain="",
            industry="",
            seed_keywords=[payload.keyword],
        )
    except Exception:
        pass
    return {"status": "queued", "keyword_id": str(keyword.id)}


@router.post("/keywords/sync-gsc", status_code=status.HTTP_202_ACCEPTED)
async def trigger_gsc_keyword_import(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger keyword import from Google Search Console data.
    
    Requires prior GSC authentication via /gsc/auth endpoint.
    Imports search queries and performance metrics from GSC into keywords.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    if not current_user.gsc_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSC not authenticated. Please authorize via /gsc/auth first."
        )
    
    try:
        from app.tasks.seo_tasks import import_gsc_keywords_task
        task = import_gsc_keywords_task.delay(project_id=str(project_id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/audit", status_code=status.HTTP_202_ACCEPTED)
async def trigger_site_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an async technical SEO audit for a project.
    
    Starts a background job that crawls the website and performs comprehensive technical
    SEO analysis. Checks for issues like broken links, missing meta tags, slow pages,
    mobile usability, structured data, and more. Results are available via /seo/technical.
    """
    project = await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_audit_task
        task = run_seo_audit_task.delay(project_id=str(project.id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/audit/onpage", status_code=status.HTTP_202_ACCEPTED)
async def trigger_onpage_audit(
    project_id: UUID,
    url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an on-page SEO audit only."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_onpage_task
        task = run_seo_onpage_task.delay(project_id=str(project_id), url=url)
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/audit/technical", status_code=status.HTTP_202_ACCEPTED)
async def trigger_technical_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a technical SEO audit only."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import run_seo_technical_task
        task = run_seo_technical_task.delay(project_id=str(project_id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.post("/gaps/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_gap_sync(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger content gap analysis sync."""
    await _assert_project_owner(project_id, current_user, db)
    try:
        from app.tasks.seo_tasks import find_content_gaps_task
        task = find_content_gaps_task.delay(project_id=str(project_id))
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "queued", "task_id": None}


@router.get("/rankings/{project_id}", response_model=PaginatedResponse[RankingResponse])
@cached(ttl=300)  # 5 minutes
async def get_rankings(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve current keyword rankings for a project.
    Returns the latest ranking for each keyword associated with the project.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    try:
        # Get total keyword count for this project
        count_result = await db.execute(
            select(func.count(Keyword.id))
            .where(Keyword.project_id == project_id)
        )
        total = count_result.scalar() or 0
        
        # Subquery to get the latest ranking per keyword
        latest_rank_sub = (
            select(
                Ranking.id,
                Ranking.keyword_id,
                Ranking.position,
                Ranking.url,
                Ranking.timestamp,
                func.row_number().over(
                    partition_by=Ranking.keyword_id,
                    order_by=Ranking.timestamp.desc()
                ).label("rn")
            )
            .join(Keyword, Ranking.keyword_id == Keyword.id)
            .where(Keyword.project_id == project_id)
            .subquery()
        )
        
        # Main query: All keywords for the project with their latest ranking (if any)
        query = (
            select(Keyword, latest_rank_sub)
            .outerjoin(latest_rank_sub, Keyword.id == latest_rank_sub.c.keyword_id)
            .where(Keyword.project_id == project_id, (latest_rank_sub.c.rn == 1) | (latest_rank_sub.c.rn == None))
            .order_by(Keyword.keyword.asc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Get latest URLs per keyword for cannibalization check (last 24h)
        yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
        cannibal_res = await db.execute(
            select(Ranking.keyword_id, func.count(func.distinct(Ranking.url)))
            .join(Keyword, Ranking.keyword_id == Keyword.id)
            .where(Keyword.project_id == project_id, Ranking.timestamp >= yesterday)
            .group_by(Ranking.keyword_id)
            .having(func.count(func.distinct(Ranking.url)) > 1)
        )
        cannibal_ids = {r[0] for r in cannibal_res.all()}

        # Build response with keyword and latest ranking data
        response_data = []
        for row in rows:
            # SQLAlchemy result row contains Keyword then the columns from subquery
            kw = row[0]
            
            # Extract ranking fields from subquery columns (row[1:] contains the subquery fields)
            # row[1] is Ranking.id, row[2] is Ranking.keyword_id, etc.
            rank_id = row[1]
            position = row[3]
            url = row[4]
            timestamp = row[5] or kw.created_at # Fallback to keyword creation if no rankings
            
            response = RankingResponse(
                id=rank_id or kw.id, # Use keyword ID if no ranking record exists
                keyword_id=kw.id,
                position=position,
                url=url,
                timestamp=timestamp,
                keyword=kw.keyword,
                intent=kw.intent,
                difficulty=kw.difficulty,
                volume=kw.volume,
                is_cannibalized=kw.id in cannibal_ids
            )
            response_data.append(response)
        
        return PaginatedResponse.create(
            data=response_data,
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception(f"Error in get_rankings for project {project_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sov/{project_id}")
@cached(ttl=3600)
async def get_sov_stats(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate Share of Voice (SOV) for a project based on keyword rankings and volumes.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    # Get latest rank for every keyword
    from sqlalchemy import over
    
    # Subquery to get latest ranking per keyword
    latest_rank_sub = (
        select(
            Ranking.keyword_id,
            Ranking.position,
            Ranking.timestamp,
            func.row_number().over(
                partition_by=Ranking.keyword_id,
                order_by=Ranking.timestamp.desc()
            ).label("rn")
        )
        .join(Keyword, Ranking.keyword_id == Keyword.id)
        .where(Keyword.project_id == project_id)
        .subquery()
    )
    
    query = (
        select(Keyword.keyword, Keyword.volume, latest_rank_sub.c.position)
        .join(latest_rank_sub, Keyword.id == latest_rank_sub.c.keyword_id)
        .where(latest_rank_sub.c.rn == 1)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    def get_ctr(pos):
        if not pos: return 0
        if pos == 1: return 0.31
        if pos == 2: return 0.14
        if pos == 3: return 0.09
        if pos <= 5: return 0.06
        if pos <= 10: return 0.03
        return 0.01

    total_possible_reach = sum((r.volume or 0) for r in rows)
    estimated_reach = sum((r.volume or 0) * get_ctr(r.position) for r in rows)
    
    sov = (estimated_reach / total_possible_reach * 100) if total_possible_reach > 0 else 0
    
    return {
        "project_id": str(project_id),
        "share_of_voice": round(sov, 2),
        "estimated_monthly_traffic": int(estimated_reach),
        "total_market_volume": total_possible_reach,
        "keywords_tracked": len(rows)
    }


@router.get("/gaps/{project_id}")
async def get_keyword_gaps(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve keyword gap analysis for a project.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_gaps()
    
    if not cached_data:
        return {
            "project_id": str(project_id),
            "data": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "has_more": False,
            "message": "Run keyword research first"
        }
    
    raw_gaps = cached_data.get("gaps", [])
    
    # Aggregate gaps by topic to match frontend ContentGap schema
    import uuid
    aggregated = {}
    for gap in raw_gaps:
        topic = gap.get("topic", "Unknown").strip()
        topic_lower = topic.lower()
        if topic_lower not in aggregated:
            # Map priority_score (0-10) to opportunity_score (0-100)
            score = int(min(100, gap.get("priority_score", 0) * 10))
            aggregated[topic_lower] = {
                "id": str(uuid.uuid4()),
                "topic": topic,
                "estimated_volume": gap.get("estimated_monthly_traffic", 0),
                "competitor_domains": set(),
                "opportunity_score": score,
                "keywords": gap.get("example_keywords", [])
            }
        
        comp_domain = gap.get("competitor_domain")
        if comp_domain:
            aggregated[topic_lower]["competitor_domains"].add(comp_domain)
            
    # Finalize format
    formatted_gaps = []
    for data in aggregated.values():
        data["competitor_coverage"] = len(data.pop("competitor_domains"))
        formatted_gaps.append(data)
        
    # Sort by opportunity_score descending
    formatted_gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)
    
    total = len(formatted_gaps)
    paginated_data = formatted_gaps[skip : skip + limit]
    
    return {
        "project_id": str(project_id),
        "data": paginated_data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": total > skip + limit
    }


@router.get("/onpage/{project_id}")
async def get_onpage_audit(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve on-page SEO audit results for a project.
    
    Returns cached results from the most recent on-page SEO audit.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_audit()
    
    if not cached_data or "on_page" not in cached_data:
        return {
            "project_id": str(project_id),
            "on_page": None,
            "message": "Run /seo/audit first"
        }
    
    return {
        "project_id": str(project_id),
        "on_page": cached_data["on_page"]
    }


@router.get("/technical/{project_id}")
async def get_technical_seo(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return (max 500)"),
):
    """
    Retrieve technical SEO audit results for a project.
    
    Returns cached results from the most recent technical SEO audit.
    """
    await _assert_project_owner(project_id, current_user, db)
    
    cache = ComponentCache(str(project_id))
    cached_data = await cache.get_cached_audit()
    
    if not cached_data or "technical" not in cached_data:
        return {
            "project_id": str(project_id),
            "data": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "has_more": False,
            "message": "Run /seo/audit first"
        }
    
    technical = cached_data["technical"]
    
    # Transform technical data to frontend TechnicalCheck objects
    formatted_checks = []
    
    # Access nested structure from check_technical()
    checks = technical.get("checks", {})
    crawlability = checks.get("crawlability", {})
    security = checks.get("security", {})
    
    # 1. Robots.txt
    robots = crawlability.get("robots_txt", {})
    if robots.get("present"):
        if robots.get("disallows_all"):
            formatted_checks.append({
                "check": "Robots.txt",
                "status": "fail",
                "description": "robots.txt is present but disallows all crawlers.",
                "fix": "Remove 'Disallow: /' from your robots.txt file to allow search engines to index your site."
            })
        else:
            formatted_checks.append({
                "check": "Robots.txt",
                "status": "pass",
                "description": "robots.txt is present and properly configured.",
                "fix": None
            })
    else:
        formatted_checks.append({
            "check": "Robots.txt",
            "status": "fail",
            "description": "No robots.txt file found.",
            "fix": "Create a robots.txt file at the root of your domain to guide search engine crawlers."
        })
        
    # 2. Sitemap
    sitemap = crawlability.get("sitemap", {})
    if sitemap.get("present"):
        if sitemap.get("url_count", 0) > 0 or sitemap.get("is_sitemap_index"):
            formatted_checks.append({
                "check": "XML Sitemap",
                "status": "pass",
                "description": f"Valid XML sitemap found with {sitemap.get('url_count', 0)} URLs.",
                "fix": None
            })
        else:
            formatted_checks.append({
                "check": "XML Sitemap",
                "status": "warning",
                "description": "Sitemap exists but appears to contain no URLs.",
                "fix": "Ensure your sitemap generation tool is correctly outputting your site's pages."
            })
    else:
        formatted_checks.append({
            "check": "XML Sitemap",
            "status": "fail",
            "description": "No sitemap.xml found.",
            "fix": "Generate an XML sitemap and submit it via Google Search Console."
        })
        
    # 3. HTTPS
    https = security.get("https", {})
    if https.get("https_available"):
        if https.get("http_redirects_to_https"):
            formatted_checks.append({
                "check": "HTTPS Encryption",
                "status": "pass",
                "description": "Website is correctly served over HTTPS with proper HTTP redirects.",
                "fix": None
            })
        else:
            formatted_checks.append({
                "check": "HTTPS Encryption",
                "status": "warning",
                "description": "HTTPS is available, but HTTP does not automatically redirect to HTTPS.",
                "fix": "Configure your web server to 301 redirect all HTTP traffic to HTTPS."
            })
    else:
        formatted_checks.append({
            "check": "HTTPS Encryption",
            "status": "fail",
            "description": "HTTPS is not properly configured or the certificate is invalid.",
            "fix": "Install a valid SSL certificate (e.g., via Let's Encrypt) and force HTTPS."
        })
        
    # 4. WWW/Non-WWW Redirects
    www = security.get("www_redirect", {})
    if www.get("consistent"):
        formatted_checks.append({
            "check": "WWW Resolution",
            "status": "pass",
            "description": f"Successfully redirects to a single canonical version ({www.get('canonical_version')}).",
            "fix": None
        })
    else:
        formatted_checks.append({
            "check": "WWW Resolution",
            "status": "warning",
            "description": "Both www and non-www versions are accessible without redirecting.",
            "fix": "Choose one version as canonical and set up a 301 redirect from the other."
        })
        
    # 5. Performance
    perf = checks.get("performance", {})
    issues = perf.get("issues", [])
    ttfb = perf.get("ttfb_ms", 0)
    
    if not issues and ttfb < 800:
        formatted_checks.append({
            "check": "Performance",
            "status": "pass",
            "description": f"Page loaded quickly (TTFB: {ttfb}ms). Compression and Cache-Control are active.",
            "fix": None
        })
    else:
        formatted_checks.append({
            "check": "Performance",
            "status": "warning" if ttfb < 1500 else "fail",
            "description": f"Performance issues detected. TTFB: {ttfb}ms.",
            "fix": "Optimize server response time and ensure Gzip/Brotli and Cache-Control headers are active."
        })
    
    total = len(formatted_checks)
    paginated_data = formatted_checks[skip : skip + limit]
    
    return {
        "project_id": str(project_id),
        "data": paginated_data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": total > skip + limit
    }
