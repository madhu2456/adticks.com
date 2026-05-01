"""
Technical SEO checker for AdTicks.
Checks robots.txt, sitemap.xml, HTTPS, www redirect, and more.
"""

import logging
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

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


async def check_technical(domain: str) -> Dict[str, Any]:
    """
    Run a full technical SEO audit on a domain or specific path.

    Args:
        domain: Domain name or URL (e.g. 'example.com' or 'https://example.com/blog')

    Returns:
        Dict with checks results, aggregated issues list, and health score
    """
    logger.info(f"Running technical SEO check for: {domain}")
    full_url = _normalize_domain(domain)
    root_url = _get_root_url(full_url)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
        robots = await _check_robots_txt(root_url, client)
        sitemap = await _check_sitemap(root_url, client)
        https_check = await _check_https(domain, client)
        www_check = await _check_www_redirect(domain, client)
        perf_check = await _check_page_performance(full_url, client)

    all_issues: List[str] = []
    all_issues.extend(robots.get("issues", []))
    all_issues.extend(sitemap.get("issues", []))
    all_issues.extend(https_check.get("issues", []))
    all_issues.extend(www_check.get("issues", []))
    all_issues.extend(perf_check.get("issues", []))

    if not robots["present"]:
        all_issues.append("No robots.txt found")
    if not sitemap["present"]:
        all_issues.append("No sitemap.xml found")

    total_checks = 6
    passed = sum([
        robots["present"] and not robots["disallows_all"],
        sitemap["present"] and sitemap["url_count"] > 0,
        https_check["https_available"] and https_check["http_redirects_to_https"],
        www_check["consistent"],
        bool(perf_check["cache_control"]),
        perf_check["ttfb_ms"] < 1000,
    ])
    health_score = round((passed / total_checks) * 100)

    result = {
        "domain": domain,
        "root_url": root_url,
        "robots_txt": robots,
        "sitemap": sitemap,
        "https": https_check,
        "www_redirect": www_check,
        "performance": perf_check,
        "issues": all_issues,
        "issues_count": len(all_issues),
        "health_score": health_score,
        "checks_passed": passed,
        "checks_total": total_checks,
    }
    logger.info(f"Technical SEO complete for {domain}: score={health_score}, issues={len(all_issues)}")
    return result
