"""
Technical SEO checker for AdTicks.
Comprehensive 19-point enterprise-grade technical SEO audit including crawlability, security,
performance, on-page optimization, structured data, mobile, images, international SEO, and visual analysis.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.seo.link_analyzer import LinkAnalyzer
from app.services.seo.content_freshness import ContentFreshnessAnalyzer
from app.services.seo.screenshot_analyzer import ScreenshotAnalyzer

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


async def _check_meta_tags(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check meta tags: title, description, charset, viewport, OG, Twitter Card."""
    result: Dict[str, Any] = {
        "meta_title": None,
        "meta_title_length": 0,
        "title_ok": False,
        "meta_description": None,
        "meta_description_length": 0,
        "description_ok": False,
        "charset_present": False,
        "viewport_present": False,
        "og_tags": [],
        "twitter_card_present": False,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Title tag
            title_tag = soup.find("title")
            if title_tag:
                result["meta_title"] = title_tag.get_text()
                result["meta_title_length"] = len(result["meta_title"])
                result["title_ok"] = 30 <= result["meta_title_length"] <= 60
                if result["meta_title_length"] < 30:
                    result["issues"].append(f"Title too short ({result['meta_title_length']} chars, need 30-60)")
                elif result["meta_title_length"] > 60:
                    result["issues"].append(f"Title too long ({result['meta_title_length']} chars, need 30-60)")
            else:
                result["issues"].append("Missing title tag")
            
            # Meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["meta_description"] = meta_desc["content"]
                result["meta_description_length"] = len(result["meta_description"])
                result["description_ok"] = 70 <= result["meta_description_length"] <= 160
                if result["meta_description_length"] < 70:
                    result["issues"].append(f"Description too short ({result['meta_description_length']} chars, need 70-160)")
                elif result["meta_description_length"] > 160:
                    result["issues"].append(f"Description too long ({result['meta_description_length']} chars, need 70-160)")
            else:
                result["issues"].append("Missing meta description")
            
            # Charset
            charset = soup.find("meta", attrs={"charset": True})
            if charset:
                result["charset_present"] = True
            else:
                result["issues"].append("Missing charset meta tag")
            
            # Viewport
            viewport = soup.find("meta", attrs={"name": "viewport"})
            if viewport:
                result["viewport_present"] = True
            else:
                result["issues"].append("Missing viewport meta tag (mobile-unfriendly)")
            
            # OG tags
            og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.IGNORECASE)})
            result["og_tags"] = [tag.get("property") for tag in og_tags if tag.get("property")]
            
            # Twitter Card
            twitter = soup.find("meta", attrs={"name": "twitter:card"})
            result["twitter_card_present"] = bool(twitter)
    except Exception as e:
        result["issues"].append(f"Meta tags check failed: {str(e)}")
    
    return result


async def _check_headings(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check H1 count, H2/H3 presence, and heading hierarchy."""
    result: Dict[str, Any] = {
        "h1_count": 0,
        "h2_count": 0,
        "h3_count": 0,
        "h1_ok": False,
        "hierarchy_ok": True,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            h1_tags = soup.find_all("h1")
            h2_tags = soup.find_all("h2")
            h3_tags = soup.find_all("h3")
            
            result["h1_count"] = len(h1_tags)
            result["h2_count"] = len(h2_tags)
            result["h3_count"] = len(h3_tags)
            
            # H1 validation
            if result["h1_count"] == 0:
                result["issues"].append("CRITICAL: No H1 tag found")
            elif result["h1_count"] > 1:
                result["issues"].append(f"Multiple H1 tags ({result['h1_count']}) — should have exactly one")
            else:
                result["h1_ok"] = True
            
            # H2/H3 presence
            if result["h2_count"] == 0 and result["h3_count"] == 0:
                result["issues"].append("No H2 or H3 tags — improve content structure")
            
            # Simple hierarchy check: H3 should not appear before H2
            h_order = []
            for tag in soup.find_all(["h1", "h2", "h3"]):
                h_order.append(tag.name)
            
            if "h3" in h_order and h_order.index("h3") < h_order.index("h2") if "h2" in h_order else False:
                result["issues"].append("H3 appears before H2 — fix heading hierarchy")
                result["hierarchy_ok"] = False
    except Exception as e:
        result["issues"].append(f"Headings check failed: {str(e)}")
    
    return result


async def _check_canonical(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check canonical tag presence, self-referential validation, and HTTPS."""
    result: Dict[str, Any] = {
        "canonical_tag": None,
        "canonical_present": False,
        "is_self_referential": False,
        "is_https": False,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            canonical = soup.find("link", attrs={"rel": "canonical"})
            
            if canonical and canonical.get("href"):
                result["canonical_tag"] = canonical["href"]
                result["canonical_present"] = True
                result["is_https"] = canonical["href"].startswith("https://")
                result["is_self_referential"] = canonical["href"].rstrip("/") == full_url.rstrip("/")
                
                if not result["is_self_referential"]:
                    result["issues"].append(f"Canonical tag points to different URL: {canonical['href']}")
                if not result["is_https"]:
                    result["issues"].append("Canonical tag should use HTTPS")
            else:
                result["issues"].append("Missing canonical tag")
    except Exception as e:
        result["issues"].append(f"Canonical check failed: {str(e)}")
    
    return result


async def _check_structured_data(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Detect JSON-LD, microdata, and RDFa structured data."""
    result: Dict[str, Any] = {
        "has_json_ld": False,
        "has_microdata": False,
        "has_rdfa": False,
        "json_ld_types": [],
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # JSON-LD
            json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
            if json_ld_scripts:
                result["has_json_ld"] = True
                for script in json_ld_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and "@type" in data:
                            result["json_ld_types"].append(data["@type"])
                    except Exception:
                        pass
            
            # Microdata (itemscope)
            if soup.find(attrs={"itemscope": True}):
                result["has_microdata"] = True
            
            # RDFa (about attribute)
            if soup.find(attrs={"about": True}):
                result["has_rdfa"] = True
            
            # Issue if no structured data
            if not (result["has_json_ld"] or result["has_microdata"] or result["has_rdfa"]):
                result["issues"].append("No structured data found (JSON-LD, microdata, or RDFa)")
    except Exception as e:
        result["issues"].append(f"Structured data check failed: {str(e)}")
    
    return result


async def _check_mobile_friendly(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check viewport meta tag and responsive design indicators."""
    result: Dict[str, Any] = {
        "viewport_present": False,
        "viewport_content": None,
        "responsive_indicators": [],
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            viewport = soup.find("meta", attrs={"name": "viewport"})
            if viewport and viewport.get("content"):
                result["viewport_present"] = True
                result["viewport_content"] = viewport["content"]
            else:
                result["issues"].append("Viewport meta tag missing — site not mobile-friendly")
            
            # Check for responsive indicators
            link_tags = soup.find_all("link", attrs={"rel": "stylesheet"})
            for link in link_tags:
                href = link.get("href", "")
                if "media=" in str(link):
                    result["responsive_indicators"].append(f"Media query: {link.get('media')}")
            
            # Check for Bootstrap or Tailwind hints
            html_str = str(soup)
            if "bootstrap" in html_str.lower():
                result["responsive_indicators"].append("Bootstrap detected")
            if "tailwind" in html_str.lower():
                result["responsive_indicators"].append("Tailwind CSS detected")
    except Exception as e:
        result["issues"].append(f"Mobile friendly check failed: {str(e)}")
    
    return result


async def _check_images(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check alt text presence and lazy loading detection."""
    result: Dict[str, Any] = {
        "total_images": 0,
        "images_with_alt": 0,
        "images_without_alt": 0,
        "lazy_loading_count": 0,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            img_tags = soup.find_all("img")
            result["total_images"] = len(img_tags)
            
            for img in img_tags:
                alt = img.get("alt")
                if alt and alt.strip():
                    result["images_with_alt"] += 1
                else:
                    result["images_without_alt"] += 1
                
                loading = img.get("loading", "").lower()
                if loading == "lazy":
                    result["lazy_loading_count"] += 1
            
            # Issue if images without alt
            if result["total_images"] > 0 and result["images_without_alt"] > 0:
                result["issues"].append(f"{result['images_without_alt']} images missing alt text")
            
            # Recommendation for lazy loading
            if result["total_images"] > 5 and result["lazy_loading_count"] == 0:
                result["issues"].append("Consider implementing lazy loading for images")
    except Exception as e:
        result["issues"].append(f"Images check failed: {str(e)}")
    
    return result


def _check_url_structure(full_url: str) -> Dict[str, Any]:
    """Analyze SEO-friendly URL structure (readable slugs, param count, depth)."""
    result: Dict[str, Any] = {
        "url": full_url,
        "depth": 0,
        "param_count": 0,
        "has_numbers": False,
        "has_hyphens": False,
        "has_underscores": False,
        "is_seo_friendly": True,
        "issues": [],
    }
    try:
        parsed = urlparse(full_url)
        path = parsed.path.strip("/")
        
        # Depth (number of slashes)
        result["depth"] = path.count("/")
        
        # Parameter count
        result["param_count"] = len(parsed.query.split("&")) if parsed.query else 0
        
        # Check for URL characteristics
        result["has_numbers"] = bool(re.search(r"\d", path))
        result["has_hyphens"] = "-" in path
        result["has_underscores"] = "_" in path
        
        # Depth > 4 is typically not ideal
        if result["depth"] > 4:
            result["issues"].append(f"Deep URL structure (depth: {result['depth']}) — aim for 3 or less")
            result["is_seo_friendly"] = False
        
        # Parameters are less SEO-friendly
        if result["param_count"] > 3:
            result["issues"].append(f"Too many query parameters ({result['param_count']}) — use clean URLs")
            result["is_seo_friendly"] = False
        
        # Underscores less ideal than hyphens
        if result["has_underscores"]:
            result["issues"].append("URLs use underscores — use hyphens instead for better SEO")
            result["is_seo_friendly"] = False
        
        # Empty path is okay
        if not path:
            result["is_seo_friendly"] = True
    except Exception as e:
        result["issues"].append(f"URL structure check failed: {str(e)}")
    
    return result


async def _check_security_headers(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check security headers: CSP, X-Frame-Options, X-Content-Type, Referrer-Policy."""
    result: Dict[str, Any] = {
        "csp_present": False,
        "x_frame_options": None,
        "x_content_type_options": None,
        "referrer_policy": None,
        "permissions_policy": None,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            headers = resp.headers
            
            csp = headers.get("Content-Security-Policy") or headers.get("Content-Security-Policy-Report-Only")
            result["csp_present"] = bool(csp)
            
            result["x_frame_options"] = headers.get("X-Frame-Options")
            result["x_content_type_options"] = headers.get("X-Content-Type-Options")
            result["referrer_policy"] = headers.get("Referrer-Policy")
            result["permissions_policy"] = headers.get("Permissions-Policy")
            
            if not result["csp_present"]:
                result["issues"].append("Missing Content-Security-Policy header")
            
            if not result["x_frame_options"]:
                result["issues"].append("Missing X-Frame-Options header (clickjacking protection)")
            
            if not result["x_content_type_options"]:
                result["issues"].append("Missing X-Content-Type-Options header")
            
            if not result["referrer_policy"]:
                result["issues"].append("Missing Referrer-Policy header")
    except Exception as e:
        result["issues"].append(f"Security headers check failed: {str(e)}")
    
    return result


async def _check_hreflang(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check for international SEO hreflang tags."""
    result: Dict[str, Any] = {
        "hreflang_tags": [],
        "has_hreflang": False,
        "languages": [],
        "has_x_default": False,
        "issues": [],
    }
    try:
        resp = await client.get(full_url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code < 400:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            hreflang_links = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
            
            if hreflang_links:
                result["has_hreflang"] = True
                for link in hreflang_links:
                    hreflang = link.get("hreflang")
                    result["hreflang_tags"].append(hreflang)
                    if hreflang != "x-default":
                        lang = hreflang.split("-")[0]
                        if lang not in result["languages"]:
                            result["languages"].append(lang)
                    if hreflang == "x-default":
                        result["has_x_default"] = True
                
                # Warning if x-default missing
                if len(result["hreflang_tags"]) > 1 and not result["has_x_default"]:
                    result["issues"].append("Missing hreflang='x-default' for international sites")
            else:
                # No hreflang is only an issue if it's an international site (hard to detect)
                pass
    except Exception as e:
        result["issues"].append(f"Hreflang check failed: {str(e)}")
    
    return result


async def _check_broken_links(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Check for broken links (404s, 410s, timeouts) by crawling internal links.
    
    Returns:
        {
            "broken_count": int,
            "broken_links": [{"url": str, "status": int, "text": str}],
            "redirects_count": int,
            "internal_checked": int,
            "external_checked": int,
            "issues": [str],
        }
    """
    result: Dict[str, Any] = {
        "broken_count": 0,
        "broken_links": [],
        "redirects_count": 0,
        "internal_checked": 0,
        "external_checked": 0,
        "issues": [],
    }
    
    try:
        # Fetch the main page HTML
        response = await client.get(full_url, follow_redirects=True)
        if response.status_code != 200:
            result["issues"].append(f"Failed to fetch page: HTTP {response.status_code}")
            return result
        
        html_content = response.text
        root_url = _get_root_url(full_url)
        
        # Use LinkAnalyzer to check broken links
        analyzer = LinkAnalyzer(root_url, timeout=TIMEOUT, max_links=200)
        link_results = await analyzer.check_broken_links(html_content)
        
        result["broken_count"] = link_results.get("broken_count", 0)
        result["broken_links"] = link_results.get("broken_links", [])
        result["redirects_count"] = link_results.get("redirects_count", 0)
        result["internal_checked"] = link_results.get("internal_checked", 0)
        result["external_checked"] = link_results.get("external_checked", 0)
        
        # Determine pass/fail
        if result["broken_count"] > 0:
            result["issues"].append(f"Found {result['broken_count']} broken links")
            # Add details for top broken links
            for link in result["broken_links"][:5]:
                status = link.get("status", 0)
                url = link.get("url", "unknown")
                result["issues"].append(f"  {status}: {url}")
    
    except Exception as e:
        result["issues"].append(f"Broken link check failed: {str(e)}")
    
    return result


async def _check_redirect_chains(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Detect redirect loops, excessive chains (>3 hops), and protocol mixing.
    
    Returns:
        {
            "max_chain_length": int,
            "chains": [...],
            "issues": [str],
            "passed": bool,
        }
    """
    result: Dict[str, Any] = {
        "max_chain_length": 0,
        "chains": [],
        "issues": [],
        "passed": True,
    }
    
    try:
        root_url = _get_root_url(full_url)
        analyzer = LinkAnalyzer(root_url, timeout=TIMEOUT)
        
        redirect_results = await analyzer.analyze_redirect_chains(full_url)
        
        result["max_chain_length"] = redirect_results.get("max_chain_length", 0)
        result["chains"] = redirect_results.get("chains", [])
        result["issues"] = redirect_results.get("issues", [])
        result["passed"] = redirect_results.get("passed", True)
        
        if not result["passed"]:
            result["issues"].insert(0, f"Redirect chain issues found (max {result['max_chain_length']} hops)")
    
    except Exception as e:
        result["issues"].append(f"Redirect chain check failed: {str(e)}")
        result["passed"] = False
    
    return result


async def _check_link_metrics(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Analyze external and internal links with quality scoring (authority flow proxy).
    
    Returns:
        {
            "internal_links": int,
            "external_links": int,
            "toxic_links": int,
            "quality_external_links": int,
            "external_domains": int,
            "top_external_domains": [{"domain": str, "count": int, "quality": str}],
            "issues": [str],
            "passed": bool,
        }
    """
    result: Dict[str, Any] = {
        "internal_links": 0,
        "external_links": 0,
        "toxic_links": 0,
        "quality_external_links": 0,
        "external_domains": 0,
        "top_external_domains": [],
        "issues": [],
        "passed": True,
    }
    
    try:
        # Fetch the main page HTML
        response = await client.get(full_url, follow_redirects=True)
        if response.status_code != 200:
            result["issues"].append(f"Failed to fetch page: HTTP {response.status_code}")
            return result
        
        html_content = response.text
        root_url = _get_root_url(full_url)
        
        analyzer = LinkAnalyzer(root_url, timeout=TIMEOUT)
        metrics = await analyzer.analyze_link_metrics(html_content)
        
        result["internal_links"] = metrics.get("internal_links", 0)
        result["external_links"] = metrics.get("external_links", 0)
        result["toxic_links"] = metrics.get("toxic_links", 0)
        result["quality_external_links"] = metrics.get("quality_external_links", 0)
        result["external_domains"] = metrics.get("external_domains", 0)
        result["top_external_domains"] = metrics.get("top_external_domains", [])
        result["passed"] = metrics.get("passed", True)
        
        if result["toxic_links"] > 0:
            result["issues"].append(f"Found {result['toxic_links']} links to potentially toxic domains (shorteners, etc.)")
        
        if result["external_links"] > result["internal_links"] * 2:
            result["issues"].append(f"Too many external links ({result['external_links']}) relative to internal ({result['internal_links']})")
    
    except Exception as e:
        result["issues"].append(f"Link metrics check failed: {str(e)}")
        result["passed"] = False
    
    return result


async def _check_content_freshness(full_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Analyze content freshness using Last-Modified headers and sitemap dates.
    
    Returns:
        {
            "overall_freshness": str,  # "fresh", "acceptable", "stale", "very_stale"
            "page_age_days": int | None,
            "sitemap_average_age_days": float,
            "urls_analyzed": int,
            "freshness_breakdown": {...},
            "last_update": str,
            "update_frequency": str,
            "issues": [str],
            "recommendations": [str],
            "passed": bool,
        }
    """
    result: Dict[str, Any] = {
        "overall_freshness": "unknown",
        "page_age_days": None,
        "sitemap_average_age_days": 0,
        "urls_analyzed": 0,
        "freshness_breakdown": {},
        "last_update": "unknown",
        "update_frequency": "unknown",
        "issues": [],
        "recommendations": [],
        "passed": True,
    }
    
    try:
        root_url = _get_root_url(full_url)
        analyzer = ContentFreshnessAnalyzer(root_url, timeout=TIMEOUT)
        
        # Run comprehensive assessment
        assessment = await analyzer.overall_freshness_assessment(client, full_url)
        
        # Extract key data
        page_fresh = assessment.get("page_freshness", {})
        sitemap_fresh = assessment.get("sitemap_freshness", {})
        content_updates = assessment.get("content_updates", {})
        
        result["overall_freshness"] = assessment.get("overall_freshness", "unknown")
        result["page_age_days"] = page_fresh.get("age_days")
        result["sitemap_average_age_days"] = sitemap_fresh.get("average_age_days", 0)
        result["urls_analyzed"] = sitemap_fresh.get("urls_analyzed", 0)
        result["freshness_breakdown"] = sitemap_fresh.get("freshness_breakdown", {})
        result["last_update"] = content_updates.get("time_since_update", "unknown")
        result["update_frequency"] = content_updates.get("update_frequency_indicator", "unknown")
        result["issues"] = assessment.get("issues", [])
        result["recommendations"] = assessment.get("recommendations", [])
        result["passed"] = assessment.get("passed", True)
        
        # Add context to recommendations
        if page_fresh.get("age_days") and page_fresh["age_days"] > 365:
            if "Update main page content" not in str(result["recommendations"]):
                result["recommendations"].append(
                    f"Main page hasn't been updated in {page_fresh['age_days']} days"
                )
        
    except Exception as e:
        result["issues"].append(f"Content freshness check failed: {str(e)}")
        result["passed"] = False
    
    return result


async def _check_page_screenshots(
    full_url: str, client: httpx.AsyncClient
) -> Dict[str, Any]:
    """
    Analyze page screenshots at multiple breakpoints.

    Args:
        full_url: Full URL to analyze
        client: httpx.AsyncClient instance

    Returns:
        Dict with screenshot analysis results
    """
    result: Dict[str, Any] = {
        "name": "page_screenshots",
        "passed": False,
        "issues": [],
        "screenshots": {},
    }

    try:
        analyzer = ScreenshotAnalyzer(timeout=TIMEOUT)
        screenshots = await analyzer.capture_screenshots(full_url, client)

        if screenshots["passed"]:
            result["passed"] = True
            result["screenshots"] = screenshots["screenshots"]
            result["visual_metrics"] = screenshots.get("visual_metrics", {})
            result["summary"] = screenshots.get("summary", "")

            # Analyze responsive behavior
            responsive = await analyzer.analyze_responsive_behavior(full_url, client)
            result["responsive_score"] = responsive.get("responsive_score", 0)
            result["responsive_analysis"] = {
                "breakpoints_analyzed": responsive.get("breakpoints_analyzed", 0),
                "issues": responsive.get("issues", []),
                "recommendations": responsive.get("recommendations", []),
            }

            # Add visual metrics to issues if any problems found
            for device, metrics in result.get("visual_metrics", {}).items():
                checks = metrics.get("readability_checks", {})
                if checks.get("low_contrast_risk"):
                    result["issues"].append(f"{device}: Potential low contrast detected")
                if checks.get("very_large_viewport"):
                    result["issues"].append(f"{device}: Viewport very large (>2560px)")
                if checks.get("very_small_viewport"):
                    result["issues"].append(f"{device}: Viewport very small (<320px)")
        else:
            result["issues"].extend(screenshots.get("issues", []))

    except Exception as e:
        result["issues"].append(f"Screenshot analysis failed: {str(e)}")
        logger.error(f"Screenshot check error: {e}")

    return result




async def check_technical(domain: str) -> Dict[str, Any]:
    """
    Run a full technical SEO audit on a domain or specific path (19 checks).

    Args:
        domain: Domain name or URL (e.g. 'example.com' or 'https://example.com/blog')

    Returns:
        Dict with 19 checks results, aggregated issues list, and health score (0-100)
    """
    logger.info(f"Running technical SEO check for: {domain}")
    full_url = _normalize_domain(domain)
    root_url = _get_root_url(full_url)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
        # Run all 19 checks in parallel
        (robots, sitemap, https_check, www_check, perf_check,
         meta_tags, headings, canonical, structured_data, 
         mobile, images, security, broken_links, redirect_chains, link_metrics, content_freshness, page_screenshots) = await asyncio.gather(
        _check_robots_txt(root_url, client),
        _check_sitemap(root_url, client),
        _check_https(domain, client),
        _check_www_redirect(domain, client),
        _check_page_performance(full_url, client),
        _check_meta_tags(full_url, client),
        _check_headings(full_url, client),
        _check_canonical(full_url, client),
        _check_structured_data(full_url, client),
        _check_mobile_friendly(full_url, client),
        _check_images(full_url, client),
        _check_security_headers(full_url, client),
        _check_broken_links(full_url, client),
        _check_redirect_chains(full_url, client),
        _check_link_metrics(full_url, client),
        _check_content_freshness(full_url, client),
        _check_page_screenshots(full_url, client),
        )
        
    # URL structure doesn't need async
    url_structure = _check_url_structure(full_url)
        
    # Hreflang as 16th check
    hreflang = await _check_hreflang(full_url, client)

    # Aggregate all issues
    all_issues: List[str] = []
    all_issues.extend(robots.get("issues", []))
    all_issues.extend(sitemap.get("issues", []))
    all_issues.extend(https_check.get("issues", []))
    all_issues.extend(www_check.get("issues", []))
    all_issues.extend(perf_check.get("issues", []))
    all_issues.extend(meta_tags.get("issues", []))
    all_issues.extend(headings.get("issues", []))
    all_issues.extend(canonical.get("issues", []))
    all_issues.extend(structured_data.get("issues", []))
    all_issues.extend(mobile.get("issues", []))
    all_issues.extend(images.get("issues", []))
    all_issues.extend(url_structure.get("issues", []))
    all_issues.extend(security.get("issues", []))
    all_issues.extend(hreflang.get("issues", []))
    all_issues.extend(broken_links.get("issues", []))
    all_issues.extend(redirect_chains.get("issues", []))
    all_issues.extend(link_metrics.get("issues", []))
    all_issues.extend(content_freshness.get("issues", []))
    all_issues.extend(page_screenshots.get("issues", []))

    # Score each check (1 pass, 0 fail)
    checks_passed = sum([
    robots["present"] and not robots["disallows_all"],  # 1. robots
    sitemap["present"] and sitemap["url_count"] > 0,  # 2. sitemap
    https_check["https_available"] and https_check["http_redirects_to_https"],  # 3. https
    www_check["consistent"],  # 4. www
    bool(perf_check["cache_control"]),  # 5. performance
    meta_tags["title_ok"],  # 6. meta_title
    meta_tags["description_ok"],  # 7. meta_desc
    headings["h1_ok"],  # 8. h1
    canonical["canonical_present"],  # 9. canonical
    structured_data["has_json_ld"] or structured_data["has_microdata"],  # 10. structured_data
    mobile["viewport_present"],  # 11. mobile
    images["total_images"] == 0 or images["images_with_alt"] > 0,  # 12. images
    security["csp_present"] and bool(security["x_frame_options"]),  # 13. security_headers
    hreflang["has_hreflang"] or True,  # 14. hreflang (N/A if not international)
    broken_links.get("broken_count", 0) == 0,  # 15. broken_links
    redirect_chains.get("passed", True),  # 16. redirect_chains
    link_metrics.get("passed", True),  # 17. link_metrics
    content_freshness.get("passed", True),  # 18. content_freshness
    page_screenshots.get("passed", True),  # 19. page_screenshots
    ])

    total_checks = 19
    health_score = round((checks_passed / total_checks) * 100)

    result = {
    "domain": domain,
    "root_url": root_url,
    "checks": {
        "crawlability": {
            "robots_txt": robots,
            "sitemap": sitemap,
            "broken_links": broken_links,
        },
        "security": {
            "https": https_check,
            "www_redirect": www_check,
            "security_headers": security,
        },
        "performance": perf_check,
        "on_page": {
            "meta_tags": meta_tags,
            "headings": headings,
            "canonical": canonical,
        },
        "structured_data": structured_data,
        "mobile": mobile,
        "images": images,
        "url_structure": url_structure,
        "international": hreflang,
        "link_analysis": {
            "redirect_chains": redirect_chains,
            "link_metrics": link_metrics,
        },
        "content": {
            "freshness": content_freshness,
        },
        "visual": page_screenshots,
    },
    "all_issues": all_issues,
    "issues_count": len(all_issues),
    "health_score": health_score,
    "checks_passed": checks_passed,
    "checks_total": total_checks,
    }
    logger.info(f"Technical SEO complete for {domain}: score={health_score}, issues={len(all_issues)}")
    return result






