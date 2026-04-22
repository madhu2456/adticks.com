"""
Technical SEO checker for AdTicks.
Checks robots.txt, sitemap.xml, HTTPS, www redirect, and more.
"""

import logging
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
HEADERS = {
    "User-Agent": "AdTicks TechSEO Bot/1.0 (+https://adticks.io/bot)",
    "Accept": "*/*",
}


def _normalize_domain(domain: str) -> str:
    domain = domain.lower().strip().rstrip("/")
    if not domain.startswith("http"):
        domain = "https://" + domain
    return domain


async def _check_robots_txt(base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    robots_url = f"{base_url}/robots.txt"
    result: Dict[str, Any] = {
        "present": False,
        "url": robots_url,
        "has_sitemap_directive": False,
        "disallows_all": False,
        "issues": [],
    }
    try:
        resp = await client.get(robots_url, headers=HEADERS)
        if resp.status_code == 200:
            result["present"] = True
            content = resp.text
            result["has_sitemap_directive"] = "sitemap:" in content.lower()
            if re.search(r"Disallow:\s*/\s*$", content, re.MULTILINE | re.IGNORECASE):
                result["disallows_all"] = True
                result["issues"].append("robots.txt disallows all crawlers")
        else:
            result["issues"].append(f"robots.txt returned HTTP {resp.status_code}")
    except Exception as e:
        result["issues"].append(f"robots.txt check failed: {e}")
    return result


async def _check_sitemap(base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    sitemap_url = f"{base_url}/sitemap.xml"
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
        result["issues"].append(f"Sitemap check failed: {e}")
    return result


async def _check_https(domain_raw: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    parsed = urlparse(domain_raw)
    host = parsed.netloc or parsed.path
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
        result["issues"].append(f"HTTPS check failed: {e}")

    try:
        resp_http = await client.get(http_url, headers=HEADERS, follow_redirects=False)
        final = resp_http.headers.get("location", "")
        if resp_http.status_code in (301, 302, 307, 308) and "https" in final.lower():
            result["http_redirects_to_https"] = True
        elif resp_http.status_code < 400:
            result["issues"].append("HTTP version accessible without HTTPS redirect")
    except Exception as e:
        result["issues"].append(f"HTTP redirect check failed: {e}")

    if not result["https_available"]:
        result["issues"].append("CRITICAL: HTTPS not available")
    if not result["hsts_enabled"]:
        result["issues"].append("HSTS not enabled — consider Strict-Transport-Security header")

    return result


async def _check_www_redirect(domain_raw: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    parsed = urlparse(domain_raw)
    host = (parsed.netloc or parsed.path).replace("https://", "").replace("http://", "")

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
        result["issues"].append(f"www redirect check failed: {e}")

    return result


async def _check_page_speed_headers(base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "cache_control": None,
        "content_encoding": None,
        "x_content_type_options": None,
        "issues": [],
    }
    try:
        resp = await client.get(base_url, headers=HEADERS, follow_redirects=True)
        result["cache_control"] = resp.headers.get("Cache-Control")
        result["content_encoding"] = resp.headers.get("Content-Encoding")
        result["x_content_type_options"] = resp.headers.get("X-Content-Type-Options")

        if not result["cache_control"]:
            result["issues"].append("No Cache-Control header — pages not being cached")
        if not result["content_encoding"] or "gzip" not in (result["content_encoding"] or "").lower():
            result["issues"].append("Gzip/Brotli compression not detected — enable for faster load times")
    except Exception as e:
        result["issues"].append(f"Header check failed: {e}")
    return result


async def check_technical(domain: str) -> Dict[str, Any]:
    """
    Run a full technical SEO audit on a domain.

    Args:
        domain: Domain name (e.g. 'example.com' or 'https://example.com')

    Returns:
        Dict with checks results, aggregated issues list, and health score
    """
    logger.info(f"Running technical SEO check for domain: {domain}")
    base_url = _normalize_domain(domain)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
        robots = await _check_robots_txt(base_url, client)
        sitemap = await _check_sitemap(base_url, client)
        https_check = await _check_https(domain, client)
        www_check = await _check_www_redirect(domain, client)
        headers_check = await _check_page_speed_headers(base_url, client)

    all_issues: List[str] = []
    all_issues.extend(robots.get("issues", []))
    all_issues.extend(sitemap.get("issues", []))
    all_issues.extend(https_check.get("issues", []))
    all_issues.extend(www_check.get("issues", []))
    all_issues.extend(headers_check.get("issues", []))

    if not robots["present"]:
        all_issues.append("No robots.txt found — create one to guide crawlers")
    if not sitemap["present"]:
        all_issues.append("No sitemap.xml — create and submit to Search Console")

    total_checks = 5
    passed = sum([
        robots["present"] and not robots["disallows_all"],
        sitemap["present"] and sitemap["url_count"] > 0,
        https_check["https_available"] and https_check["http_redirects_to_https"],
        www_check["consistent"],
        bool(headers_check["cache_control"]),
    ])
    health_score = round((passed / total_checks) * 100)

    result = {
        "domain": domain,
        "robots_txt": robots,
        "sitemap": sitemap,
        "https": https_check,
        "www_redirect": www_check,
        "performance_headers": headers_check,
        "issues": all_issues,
        "issues_count": len(all_issues),
        "health_score": health_score,
        "checks_passed": passed,
        "checks_total": total_checks,
    }
    logger.info(f"Technical SEO complete for {domain}: score={health_score}, issues={len(all_issues)}")
    return result
