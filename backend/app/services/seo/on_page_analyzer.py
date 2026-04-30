"""
On-page SEO analysis service for AdTicks.
Fetches and analyzes URL content using httpx + BeautifulSoup.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import json

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)

IDEAL_TITLE_MIN = 50
IDEAL_TITLE_MAX = 60
IDEAL_META_MIN = 150
IDEAL_META_MAX = 160

HEADERS = {
    "User-Agent": f"AdTicks SEO Analyzer/1.0 (compatible; +{settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else 'https://adticks.com'})",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _compute_keyword_density(text: str, keywords: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Compute keyword density for a list of keywords against the page text.

    Args:
        text: Full page text content
        keywords: Optional list of keywords to check density for

    Returns:
        Dict mapping keyword -> density percentage
    """
    if not text or not keywords:
        return {}
    text_lower = text.lower()
    total_words = len(text_lower.split())
    if total_words == 0:
        return {}
    density = {}
    for kw in keywords:
        kw_lower = kw.lower()
        count = len(re.findall(r'\b' + re.escape(kw_lower) + r'\b', text_lower))
        density[kw] = round((count / total_words) * 100, 2)
    return density


def _check_heading_hierarchy(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Check heading hierarchy (H1 -> H2 -> H3).

    Returns:
        Dict with counts, hierarchy_valid bool, issues list
    """
    h1s = soup.find_all("h1")
    h2s = soup.find_all("h2")
    h3s = soup.find_all("h3")
    h4s = soup.find_all("h4")

    issues = []
    hierarchy_valid = True

    if len(h1s) == 0:
        issues.append("Missing H1 tag")
        hierarchy_valid = False
    elif len(h1s) > 1:
        issues.append(f"Multiple H1 tags found ({len(h1s)}); only one recommended")
        hierarchy_valid = False

    if h3s and not h2s:
        issues.append("H3 tags present without H2 tags — broken hierarchy")
        hierarchy_valid = False

    if h4s and not h3s:
        issues.append("H4 tags present without H3 tags — broken hierarchy")

    return {
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "h3_count": len(h3s),
        "h4_count": len(h4s),
        "hierarchy_valid": hierarchy_valid,
        "h1_texts": [h.get_text(strip=True) for h in h1s],
        "issues": issues,
    }


def _check_images(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Audit image alt tags.

    Returns:
        Dict with total_images, images_missing_alt, images_with_empty_alt, alt_coverage_pct
    """
    imgs = soup.find_all("img")
    total = len(imgs)
    missing_alt = sum(1 for img in imgs if not img.has_attr("alt"))
    empty_alt = sum(1 for img in imgs if img.has_attr("alt") and img["alt"].strip() == "")
    coverage = round(((total - missing_alt) / total * 100), 1) if total > 0 else 100.0
    return {
        "total_images": total,
        "images_missing_alt": missing_alt,
        "images_with_empty_alt": empty_alt,
        "alt_coverage_pct": coverage,
    }


def _check_links(soup: BeautifulSoup, base_domain: str) -> Dict[str, Any]:
    """
    Count internal and external links.

    Args:
        soup: BeautifulSoup object
        base_domain: The domain of the page being analyzed

    Returns:
        Dict with internal_links, external_links, total_links, nofollow_count
    """
    anchors = soup.find_all("a", href=True)
    internal = 0
    external = 0
    nofollow = 0

    for a in anchors:
        href = a["href"]
        rel = a.get("rel", [])
        if "nofollow" in rel:
            nofollow += 1

        if href.startswith("http"):
            parsed = urlparse(href)
            if base_domain.lower() in parsed.netloc.lower():
                internal += 1
            else:
                external += 1
        elif href.startswith("/") or href.startswith("#") or not href.startswith("mailto"):
            internal += 1

    return {
        "internal_links": internal,
        "external_links": external,
        "total_links": internal + external,
        "nofollow_count": nofollow,
    }


def _check_schema_markup(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Detect schema.org markup (JSON-LD, Microdata, RDFa).

    Returns:
        Dict with has_schema, schema_types list, schema_count
    """
    json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    schema_types = []
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, dict):
                schema_types.append(data.get("@type", "Unknown"))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        schema_types.append(item.get("@type", "Unknown"))
        except Exception:
            schema_types.append("Unparseable")

    # Check for Microdata
    microdata = soup.find_all(attrs={"itemtype": True})
    for elem in microdata:
        itemtype = elem.get("itemtype", "")
        if "schema.org" in itemtype:
            type_name = itemtype.split("/")[-1]
            if type_name not in schema_types:
                schema_types.append(type_name)

    return {
        "has_schema": len(schema_types) > 0,
        "schema_types": schema_types,
        "schema_count": len(schema_types),
        "json_ld_blocks": len(json_ld_scripts),
    }


def _score_page(analysis: Dict[str, Any]) -> int:
    """
    Compute an overall on-page SEO score (0-100) from analysis results.

    Args:
        analysis: The full analysis dict

    Returns:
        Integer score 0-100
    """
    score = 100
    deductions = []

    # Title
    if not analysis["title"]["present"]:
        score -= 15
        deductions.append("Missing title (-15)")
    elif not analysis["title"]["length_ok"]:
        score -= 5
        deductions.append("Title length suboptimal (-5)")

    # Meta description
    if not analysis["meta_description"]["present"]:
        score -= 10
        deductions.append("Missing meta description (-10)")
    elif not analysis["meta_description"]["length_ok"]:
        score -= 3
        deductions.append("Meta description length suboptimal (-3)")

    # H1
    h = analysis["headings"]
    if h["h1_count"] == 0:
        score -= 15
        deductions.append("Missing H1 (-15)")
    elif h["h1_count"] > 1:
        score -= 7
        deductions.append("Multiple H1s (-7)")
    if not h["hierarchy_valid"]:
        score -= 5
        deductions.append("Broken heading hierarchy (-5)")

    # Images
    img = analysis["images"]
    if img["total_images"] > 0 and img["alt_coverage_pct"] < 80:
        score -= 8
        deductions.append(f"Poor alt coverage {img['alt_coverage_pct']}% (-8)")

    # Schema
    if not analysis["schema"]["has_schema"]:
        score -= 5
        deductions.append("No schema markup (-5)")

    # Word count
    wc = analysis["word_count"]
    if wc < 300:
        score -= 10
        deductions.append(f"Low word count {wc} (-10)")
    elif wc < 600:
        score -= 5
        deductions.append(f"Low word count {wc} (-5)")

    analysis["_score_deductions"] = deductions
    return max(0, score)


async def analyze_url(
    url: str,
    target_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch and perform comprehensive on-page SEO analysis on a URL.

    Args:
        url: Full URL to analyze (e.g. 'https://example.com/page')
        target_keywords: Optional keywords to check density for

    Returns:
        Scored dict with full SEO analysis and issues list
    """
    logger.info(f"Analyzing URL: {url}")
    parsed_url = urlparse(url)
    base_domain = parsed_url.netloc

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            final_url = str(response.url)
            status_code = response.status_code
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        return {"url": url, "error": f"HTTP {e.response.status_code}", "score": 0, "issues": [f"Failed to fetch URL: HTTP {e.response.status_code}"]}
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return {"url": url, "error": str(e), "score": 0, "issues": ["Failed to fetch URL"]}

    soup = BeautifulSoup(html, "html.parser")

    # --- Title ---
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title_text)
    title_analysis = {
        "present": bool(title_text),
        "text": title_text,
        "length": title_len,
        "length_ok": IDEAL_TITLE_MIN <= title_len <= IDEAL_TITLE_MAX,
        "recommendation": f"Title is {title_len} chars; ideal is {IDEAL_TITLE_MIN}-{IDEAL_TITLE_MAX}" if title_text else "Add a title tag",
    }

    # --- Meta Description ---
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc_text = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""
    meta_len = len(meta_desc_text)
    meta_analysis = {
        "present": bool(meta_desc_text),
        "text": meta_desc_text,
        "length": meta_len,
        "length_ok": IDEAL_META_MIN <= meta_len <= IDEAL_META_MAX,
        "recommendation": f"Meta description is {meta_len} chars; ideal is {IDEAL_META_MIN}-{IDEAL_META_MAX}" if meta_desc_text else "Add a meta description",
    }

    # --- Headings ---
    heading_analysis = _check_heading_hierarchy(soup)

    # --- Body Text ---
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    body_text = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    # --- Keyword Density ---
    kw_density = _compute_keyword_density(body_text, target_keywords)

    # --- Images ---
    image_analysis = _check_images(soup)

    # --- Links ---
    link_analysis = _check_links(soup, base_domain)

    # --- Schema ---
    schema_analysis = _check_schema_markup(soup)

    # --- Canonical ---
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical_url = canonical_tag.get("href", "") if canonical_tag else ""

    # --- Robots Meta ---
    robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = robots_meta.get("content", "") if robots_meta else ""

    # --- Compile Issues ---
    issues: List[str] = []
    if not title_analysis["present"]:
        issues.append("CRITICAL: Missing <title> tag")
    elif not title_analysis["length_ok"]:
        issues.append(f"Title length {title_len} chars — aim for {IDEAL_TITLE_MIN}-{IDEAL_TITLE_MAX}")

    if not meta_analysis["present"]:
        issues.append("Missing meta description")
    elif not meta_analysis["length_ok"]:
        issues.append(f"Meta description {meta_len} chars — aim for {IDEAL_META_MIN}-{IDEAL_META_MAX}")

    issues.extend(heading_analysis.get("issues", []))

    if image_analysis["images_missing_alt"] > 0:
        issues.append(f"{image_analysis['images_missing_alt']} image(s) missing alt text")

    if not schema_analysis["has_schema"]:
        issues.append("No structured data/schema markup found")

    if word_count < 300:
        issues.append(f"Low word count ({word_count} words) — aim for 600+ for most pages")

    if not canonical_url:
        issues.append("No canonical URL specified")

    if "noindex" in robots_content.lower():
        issues.append("WARNING: Page has noindex — will not be indexed by search engines")

    analysis = {
        "url": url,
        "final_url": final_url,
        "status_code": status_code,
        "title": title_analysis,
        "meta_description": meta_analysis,
        "headings": heading_analysis,
        "word_count": word_count,
        "keyword_density": kw_density,
        "images": image_analysis,
        "links": link_analysis,
        "schema": schema_analysis,
        "canonical_url": canonical_url,
        "robots_meta": robots_content,
        "issues": issues,
        "issues_count": len(issues),
    }

    score = _score_page(analysis)
    analysis["score"] = score
    analysis["overall_score"] = score
    
    # --- Build frontend-compatible items list ---
    items = []
    
    # Title check
    items.append({
        "check": "Title Tag",
        "status": "pass" if title_analysis["present"] and title_analysis["length_ok"] else "warning" if title_analysis["present"] else "fail",
        "message": title_analysis["recommendation"],
        "score": 100 if title_analysis["present"] and title_analysis["length_ok"] else 70 if title_analysis["present"] else 0
    })
    
    # Meta Description check
    items.append({
        "check": "Meta Description",
        "status": "pass" if meta_analysis["present"] and meta_analysis["length_ok"] else "warning" if meta_analysis["present"] else "fail",
        "message": meta_analysis["recommendation"],
        "score": 100 if meta_analysis["present"] and meta_analysis["length_ok"] else 70 if meta_analysis["present"] else 0
    })
    
    # H1 check
    items.append({
        "check": "H1 Heading",
        "status": "pass" if heading_analysis["h1_count"] == 1 else "fail",
        "message": f"Found {heading_analysis['h1_count']} H1 tag(s). One is ideal." if heading_analysis["h1_count"] != 1 else "H1 tag is present and unique.",
        "score": 100 if heading_analysis["h1_count"] == 1 else 0
    })
    
    # Content Length
    items.append({
        "check": "Content Length",
        "status": "pass" if word_count >= 600 else "warning" if word_count >= 300 else "fail",
        "message": f"Page has {word_count} words." + (" Ideal is 600+." if word_count < 600 else ""),
        "score": 100 if word_count >= 600 else 60 if word_count >= 300 else 30
    })
    
    # Image Alts
    items.append({
        "check": "Image Alt Text",
        "status": "pass" if image_analysis["alt_coverage_pct"] >= 90 else "warning" if image_analysis["alt_coverage_pct"] >= 50 else "fail",
        "message": f"{image_analysis['alt_coverage_pct']}% of images have alt text." + (f" Missing {image_analysis['images_missing_alt']} alts." if image_analysis["images_missing_alt"] > 0 else ""),
        "score": int(image_analysis["alt_coverage_pct"])
    })
    
    # Schema check
    items.append({
        "check": "Structured Data",
        "status": "pass" if schema_analysis["has_schema"] else "warning",
        "message": f"Found {schema_analysis['schema_count']} schema types." if schema_analysis["has_schema"] else "No structured data found.",
        "score": 100 if schema_analysis["has_schema"] else 0
    })
    
    analysis["items"] = items

    logger.info(f"On-page analysis complete for {url}: score={analysis['score']}, issues={len(issues)}")
    return analysis
