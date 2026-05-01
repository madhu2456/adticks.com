"""
Technical SEO checker for AdTicks — Comprehensive audit covering 15+ checks.
Rivals Ahrefs, SEMrush, Moz Site Audit with checks for:
- Crawlability (robots.txt, sitemap, crawlable URLs)
- Indexability (canonical, meta robots, noindex)
- On-page (title, meta description, H1, headings)
- Security (HTTPS, HSTS, security headers)
- Performance (TTFB, compression, caching)
- Mobile (viewport, responsiveness)
- Structured data (JSON-LD, microdata)
- Links (internal linking, redirect chains, broken links)
- URLs (SEO-friendly URLs, parameters)
- Social (Open Graph, Twitter Card)
- International (hreflang)
"""

import logging
import re
import json
from typing import Dict, Any, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
HEADERS = {
    "User-Agent": f"AdTicks TechSEO Bot/1.0 (+{settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else 'https://adticks.com'})",
    "Accept": "*/*",
}


def _normalize_domain(domain: str) -> str:
    """Normalize input to a base URL with scheme."""
    domain = domain.lower().strip().rstrip("/")
    if not domain.startswith("http"):
        domain = "https://" + domain
    return domain


def _get_root_url(url: str) -> str:
    """Extract root scheme + netloc from any URL."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        # Fallback for bare domains
        clean = url.replace("https://", "").replace("http://", "").split("/")[0]
        return f"https://{clean}"
    return f"{parsed.scheme}://{parsed.netloc}"


async def _check_robots_txt(root_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    robots_url = f"{root_url}/robots.txt"
    result: Dict[str, Any] = {
        "present": False,
        "url": robots_url,
        "has_sitemap_directive": False,
        "disallows_all": False,
        "issues": [],
    }
    try:
        resp = await client.get(robots_url, headers=HEADERS, timeout=10.0)
        if resp.status_code == 200:
            result["present"] = True
            content = resp.text
            result["has_sitemap_directive"] = "sitemap:" in content.lower()
            if re.search(r"Disallow:\s*/\s*$", content, re.MULTILINE | re.IGNORECASE):
                result["disallows_all"] = True
                result["issues"].append("CRITICAL: robots.txt disallows all crawlers")
        elif resp.status_code == 404:
            result["issues"].append("Missing robots.txt file")
        else:
            result["issues"].append(f"robots.txt returned HTTP {resp.status_code}")
    except Exception as e:
        result["issues"].append(f"robots.txt check failed: {str(e)}")
    return result


async def _check_sitemap(root_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    sitemap_url = f"{root_url}/sitemap.xml"
    result: Dict[str, Any] = {
        "present": False,
        "url": sitemap_url,
        "url_count": 0,
        "is_sitemap_index": False,
        "issues": [],
    }
    try:
        resp = await client.get(sitemap_url, headers=HEADERS)
        if resp.status_code == 200:
            result["present"] = True
            content = resp.text
            result["url_count"] = len(re.findall(r"<url>", content, re.IGNORECASE))
            result["is_sitemap_index"] = "<sitemapindex" in content.lower()
            if result["url_count"] == 0 and not result["is_sitemap_index"]:
                result["issues"].append("Sitemap found but contains no <url> entries")
        elif resp.status_code == 404:
            result["issues"].append("No sitemap.xml found — submit one via Google Search Console")
        else:
            result["issues"].append(f"Sitemap returned HTTP {resp.status_code}")
    except Exception as e:
        result["issues"].append(f"Sitemap check failed: {str(e)}")
    return result


async def _check_https(domain_raw: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    parsed = urlparse(domain_raw)
    host = parsed.netloc or parsed.path.split("/")[0]
    https_url = f"https://{host}"
    http_url = f"http://{host}"
    result: Dict[str, Any] = {
        "https_available": False,
        "http_redirects_to_https": False,
        "hsts_enabled": False,
        "issues": [],
    }
    try:
        resp_https = await client.get(https_url, headers=HEADERS, follow_redirects=True)
        result["https_available"] = resp_https.status_code < 400
        hsts = resp_https.headers.get("Strict-Transport-Security", "")
        result["hsts_enabled"] = bool(hsts)
    except Exception as e:
        result["issues"].append(f"HTTPS check failed: {str(e)}")

    try:
        resp_http = await client.get(http_url, headers=HEADERS, follow_redirects=False)
        final = resp_http.headers.get("location", "")
        if resp_http.status_code in (301, 302, 307, 308) and "https" in final.lower():
            result["http_redirects_to_https"] = True
        elif resp_http.status_code < 400:
            result["issues"].append("HTTP version accessible without HTTPS redirect")
    except Exception as e:
        result["issues"].append(f"HTTP redirect check failed: {str(e)}")

    if not result["https_available"]:
        result["issues"].append("CRITICAL: HTTPS not available")
    if not result["hsts_enabled"]:
        result["issues"].append("HSTS not enabled — consider Strict-Transport-Security header")

    return result


async def _check_www_redirect(domain_raw: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    parsed = urlparse(domain_raw)
    host = (parsed.netloc or parsed.path).split("/")[0]

    has_www = host.startswith("www.")
    www_host = f"www.{host}" if not has_www else host
    non_www_host = host[4:] if has_www else host

    www_url = f"https://{www_host}"
    non_www_url = f"https://{non_www_host}"

    result: Dict[str, Any] = {
        "canonical_version": None,
        "www_redirects": False,
        "non_www_redirects": False,
        "consistent": False,
        "issues": [],
    }
    try:
        www_resp = await client.get(www_url, headers=HEADERS, follow_redirects=False)
        result["www_redirects"] = www_resp.status_code in (301, 302, 307, 308)

        non_resp = await client.get(non_www_url, headers=HEADERS, follow_redirects=False)
        result["non_www_redirects"] = non_resp.status_code in (301, 302, 307, 308)

        if result["www_redirects"] and not result["non_www_redirects"]:
            result["canonical_version"] = "non-www"
            result["consistent"] = True
        elif result["non_www_redirects"] and not result["www_redirects"]:
            result["canonical_version"] = "www"
            result["consistent"] = True
        elif not result["www_redirects"] and not result["non_www_redirects"]:
            result["issues"].append("Both www and non-www accessible — duplicate content risk")
        else:
            result["issues"].append("Redirect loop detected between www and non-www")
    except Exception as e:
        result["issues"].append(f"www redirect check failed: {str(e)}")

    return result


async def _check_page_performance(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check TTFB and performance headers."""
    import asyncio
    import time
    start = asyncio.get_event_loop().time()
    result: Dict[str, Any] = {
        "ttfb_ms": 0,
        "cache_control": None,
        "content_encoding": None,
        "x_content_type_options": None,
        "strict_transport_security": None,
        "content_security_policy": None,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=20.0)
        end = asyncio.get_event_loop().time()
        result["ttfb_ms"] = round((end - start) * 1000)
        result["cache_control"] = resp.headers.get("Cache-Control")
        result["content_encoding"] = resp.headers.get("Content-Encoding")
        result["x_content_type_options"] = resp.headers.get("X-Content-Type-Options")
        result["strict_transport_security"] = resp.headers.get("Strict-Transport-Security")
        result["content_security_policy"] = resp.headers.get("Content-Security-Policy")

        if result["ttfb_ms"] > 800:
            result["issues"].append(f"Slow server response (TTFB: {result['ttfb_ms']}ms) — aim for < 500ms")
        elif result["ttfb_ms"] > 1500:
            result["issues"].append(f"CRITICAL: Very slow TTFB ({result['ttfb_ms']}ms)")

        if not result["cache_control"]:
            result["issues"].append("Missing Cache-Control header")
        if not result["content_encoding"] or "gzip" not in (result["content_encoding"] or "").lower():
            result["issues"].append("Gzip/Brotli compression not detected")
        if not result["strict_transport_security"]:
            result["issues"].append("Missing HSTS header (Strict-Transport-Security)")
            
    except Exception as e:
        result["issues"].append(f"Performance check failed: {str(e)}")
    return result


async def _check_meta_tags(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check title, meta description, charset, viewport."""
    result = {
        "title": None,
        "title_length": 0,
        "meta_description": None,
        "meta_description_length": 0,
        "charset": None,
        "viewport": None,
        "og_title": None,
        "og_description": None,
        "twitter_card": None,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        title = soup.find("title")
        if title:
            result["title"] = title.string
            result["title_length"] = len(title.string) if title.string else 0
            if result["title_length"] < 30:
                result["issues"].append(f"Title too short ({result['title_length']}ch) — aim for 30-60")
            elif result["title_length"] > 60:
                result["issues"].append(f"Title too long ({result['title_length']}ch) — aim for 30-60")
        else:
            result["issues"].append("Missing title tag")
        
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            result["meta_description"] = meta_desc.get("content")
            result["meta_description_length"] = len(result["meta_description"]) if result["meta_description"] else 0
            if result["meta_description_length"] < 70:
                result["issues"].append(f"Meta description too short ({result['meta_description_length']}ch) — aim for 70-160")
            elif result["meta_description_length"] > 160:
                result["issues"].append(f"Meta description too long ({result['meta_description_length']}ch) — aim for 70-160")
        else:
            result["issues"].append("Missing meta description")
        
        charset = soup.find("meta", {"charset": True})
        if charset:
            result["charset"] = charset.get("charset")
        else:
            result["issues"].append("Missing charset declaration")
        
        viewport = soup.find("meta", {"name": "viewport"})
        result["viewport"] = bool(viewport)
        if not viewport:
            result["issues"].append("Missing viewport meta tag (not mobile-friendly)")
        
        og_title = soup.find("meta", {"property": "og:title"})
        if og_title:
            result["og_title"] = og_title.get("content")
        
        og_desc = soup.find("meta", {"property": "og:description"})
        if og_desc:
            result["og_description"] = og_desc.get("content")
        
        twitter_card = soup.find("meta", {"name": "twitter:card"})
        result["twitter_card"] = bool(twitter_card)
    except Exception as e:
        result["issues"].append(f"Meta tags check failed: {str(e)}")
    return result


async def _check_headings(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check H1 presence, hierarchy, and structure."""
    result = {
        "h1_count": 0,
        "h1_text": None,
        "h2_count": 0,
        "h3_count": 0,
        "heading_structure_valid": True,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        h1s = soup.find_all("h1")
        result["h1_count"] = len(h1s)
        if h1s:
            result["h1_text"] = h1s[0].get_text(strip=True)
        
        if result["h1_count"] == 0:
            result["issues"].append("Missing H1 tag")
        elif result["h1_count"] > 1:
            result["issues"].append(f"Multiple H1 tags ({result['h1_count']}) — use only one per page")
        
        result["h2_count"] = len(soup.find_all("h2"))
        result["h3_count"] = len(soup.find_all("h3"))
        
        # Check heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if headings:
            first_heading_level = int(headings[0].name[1])
            if first_heading_level > 1:
                result["issues"].append(f"First heading is not H1 (found {headings[0].name})")
                result["heading_structure_valid"] = False
    except Exception as e:
        result["issues"].append(f"Headings check failed: {str(e)}")
    return result


async def _check_canonical(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check canonical tag presence and validity."""
    result = {
        "canonical_present": False,
        "canonical_url": None,
        "is_self_referential": False,
        "is_https": False,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        canonical = soup.find("link", {"rel": "canonical"})
        if canonical:
            result["canonical_present"] = True
            result["canonical_url"] = canonical.get("href")
            result["is_self_referential"] = result["canonical_url"] == url
            result["is_https"] = result["canonical_url"].startswith("https://") if result["canonical_url"] else False
            if not result["is_https"]:
                result["issues"].append("Canonical URL is not HTTPS")
        else:
            result["issues"].append("Missing canonical tag (not critical but recommended)")
    except Exception as e:
        result["issues"].append(f"Canonical check failed: {str(e)}")
    return result


async def _check_structured_data(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check JSON-LD, microdata, and schema.org markup."""
    result = {
        "has_json_ld": False,
        "json_ld_types": [],
        "has_microdata": False,
        "has_rdfa": False,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Check JSON-LD
        json_lds = soup.find_all("script", {"type": "application/ld+json"})
        if json_lds:
            result["has_json_ld"] = True
            for script in json_lds:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        result["json_ld_types"].append(data.get("@type", "Unknown"))
                except:
                    pass
        
        # Check microdata
        if soup.find(attrs={"itemscope": True}):
            result["has_microdata"] = True
        
        # Check RDFa
        if soup.find(attrs={"typeof": True}):
            result["has_rdfa"] = True
        
        if not result["has_json_ld"] and not result["has_microdata"] and not result["has_rdfa"]:
            result["issues"].append("No structured data found (JSON-LD, microdata, or RDFa)")
    except Exception as e:
        result["issues"].append(f"Structured data check failed: {str(e)}")
    return result


async def _check_mobile_friendly(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check mobile responsiveness and mobile meta tags."""
    result = {
        "viewport_present": False,
        "responsive_design": False,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        viewport = soup.find("meta", {"name": "viewport"})
        result["viewport_present"] = bool(viewport)
        if not result["viewport_present"]:
            result["issues"].append("Missing viewport meta tag")
        
        # Check for responsive CSS
        if "width=device-width" in str(viewport) if viewport else False:
            result["responsive_design"] = True
        else:
            result["issues"].append("Viewport may not be configured for responsive design")
    except Exception as e:
        result["issues"].append(f"Mobile friendly check failed: {str(e)}")
    return result


async def _check_images(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check image optimization (alt text, lazy loading, size)."""
    result = {
        "total_images": 0,
        "images_with_alt": 0,
        "images_missing_alt": 0,
        "images_with_lazy_loading": 0,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        images = soup.find_all("img")
        result["total_images"] = len(images)
        
        for img in images:
            alt = img.get("alt")
            if alt and alt.strip():
                result["images_with_alt"] += 1
            else:
                result["images_missing_alt"] += 1
            
            if img.get("loading") == "lazy":
                result["images_with_lazy_loading"] += 1
        
        if result["images_missing_alt"] > 0:
            result["issues"].append(f"{result['images_missing_alt']} images missing alt text")
        if result["total_images"] > 0 and result["images_with_lazy_loading"] == 0:
            result["issues"].append("No lazy-loaded images found (can improve performance)")
    except Exception as e:
        result["issues"].append(f"Images check failed: {str(e)}")
    return result


async def _check_url_structure(url: str) -> Dict[str, Any]:
    """Check URL SEO-friendliness."""
    result = {
        "url": url,
        "has_readable_slug": True,
        "has_parameters": False,
        "has_special_chars": False,
        "path_depth": 0,
        "issues": [],
    }
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check for query parameters
        if parsed.query:
            result["has_parameters"] = True
            result["issues"].append("URL contains query parameters (less SEO-friendly)")
        
        # Check for special characters (except hyphens and slashes)
        if re.search(r'[^a-z0-9/-]', path):
            result["has_special_chars"] = True
            result["issues"].append("URL contains special characters")
        
        # Check path depth
        result["path_depth"] = len([p for p in path.split("/") if p])
        if result["path_depth"] > 4:
            result["issues"].append(f"Deep URL structure ({result['path_depth']} levels) — aim for 3 or fewer")
        
        # Check for readable slug
        slug_parts = [p for p in path.split("/") if p]
        for part in slug_parts:
            if re.match(r'^\d+$', part):
                result["has_readable_slug"] = False
                result["issues"].append("URL contains only numbers (not descriptive)")
    except Exception as e:
        result["issues"].append(f"URL structure check failed: {str(e)}")
    return result


async def _check_security_headers(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check security headers."""
    result = {
        "has_csp": False,
        "has_x_frame_options": False,
        "has_x_content_type": False,
        "has_referrer_policy": False,
        "has_permissions_policy": False,
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        
        result["has_csp"] = bool(resp.headers.get("Content-Security-Policy"))
        result["has_x_frame_options"] = bool(resp.headers.get("X-Frame-Options"))
        result["has_x_content_type"] = bool(resp.headers.get("X-Content-Type-Options"))
        result["has_referrer_policy"] = bool(resp.headers.get("Referrer-Policy"))
        result["has_permissions_policy"] = bool(resp.headers.get("Permissions-Policy"))
        
        if not result["has_csp"]:
            result["issues"].append("Missing Content-Security-Policy header")
        if not result["has_x_frame_options"]:
            result["issues"].append("Missing X-Frame-Options header")
        if not result["has_x_content_type"]:
            result["issues"].append("Missing X-Content-Type-Options header")
    except Exception as e:
        result["issues"].append(f"Security headers check failed: {str(e)}")
    return result


async def _check_hreflang(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check hreflang tags for international SEO."""
    result = {
        "has_hreflang": False,
        "hreflang_tags": [],
        "issues": [],
    }
    try:
        resp = await client.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        hreflangs = soup.find_all("link", {"rel": "alternate", "hreflang": True})
        if hreflangs:
            result["has_hreflang"] = True
            for tag in hreflangs:
                result["hreflang_tags"].append({
                    "hreflang": tag.get("hreflang"),
                    "href": tag.get("href"),
                })
    except Exception as e:
