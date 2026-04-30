"""
AdTicks — Sitemap generator + robots.txt validator + JSON-LD schema generator.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from xml.sax.saxutils import escape

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sitemap generator
# ---------------------------------------------------------------------------
def generate_sitemap_xml(
    urls: list[dict[str, Any]],
    default_changefreq: str = "weekly",
    default_priority: float = 0.7,
) -> str:
    """Generate a sitemap.xml string from a list of URL rows.

    Each row: {url, lastmod?, changefreq?, priority?}
    """
    parts: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>']
    parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for row in urls:
        url = row.get("url")
        if not url:
            continue
        parts.append("  <url>")
        parts.append(f"    <loc>{escape(url)}</loc>")
        lastmod = row.get("lastmod")
        if lastmod:
            if isinstance(lastmod, datetime):
                lastmod = lastmod.strftime("%Y-%m-%d")
            parts.append(f"    <lastmod>{lastmod}</lastmod>")
        parts.append(f"    <changefreq>{row.get('changefreq', default_changefreq)}</changefreq>")
        parts.append(f"    <priority>{row.get('priority', default_priority)}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# robots.txt validator
# ---------------------------------------------------------------------------
def validate_robots_txt(content: str) -> dict[str, Any]:
    """Parse and validate a robots.txt body. Returns issues + parsed rules."""
    issues: list[dict[str, str]] = []
    rules: list[dict[str, Any]] = []
    sitemap_directives: list[str] = []
    current: dict[str, Any] | None = None

    for lineno, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            issues.append({"line": str(lineno), "severity": "error",
                           "message": f"Malformed line: {line!r}"})
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip().split("#", 1)[0].strip()

        if key == "user-agent":
            current = {"user_agent": value, "allow": [], "disallow": [], "crawl_delay": None}
            rules.append(current)
        elif key == "allow":
            if current is None:
                issues.append({"line": str(lineno), "severity": "warning",
                               "message": "Allow before any User-agent directive"})
            else:
                current["allow"].append(value)
        elif key == "disallow":
            if current is None:
                issues.append({"line": str(lineno), "severity": "warning",
                               "message": "Disallow before any User-agent directive"})
            else:
                current["disallow"].append(value)
                if value == "/" and current.get("user_agent") == "*":
                    issues.append({"line": str(lineno), "severity": "error",
                                   "message": "Disallow: / for User-agent: * blocks ALL crawlers"})
        elif key == "crawl-delay":
            if current:
                try:
                    current["crawl_delay"] = float(value)
                except ValueError:
                    issues.append({"line": str(lineno), "severity": "warning",
                                   "message": f"Invalid Crawl-delay value: {value!r}"})
        elif key == "sitemap":
            if not value.startswith(("http://", "https://")):
                issues.append({"line": str(lineno), "severity": "warning",
                               "message": "Sitemap URL should be absolute"})
            sitemap_directives.append(value)
        else:
            issues.append({"line": str(lineno), "severity": "notice",
                           "message": f"Unknown directive: {key}"})

    if not sitemap_directives:
        issues.append({"line": "0", "severity": "warning",
                       "message": "No Sitemap: directive found"})
    if not rules:
        issues.append({"line": "0", "severity": "warning",
                       "message": "No User-agent rules found"})

    return {
        "is_valid": not any(i["severity"] == "error" for i in issues),
        "issues": issues,
        "rules": rules,
        "sitemap_directives": sitemap_directives,
    }


def evaluate_robots_path(rules: list[dict[str, Any]], user_agent: str, path: str) -> dict[str, Any]:
    """Given parsed rules, decide whether `user_agent` can crawl `path`."""
    candidate = None
    for rule in rules:
        ua = rule.get("user_agent", "*")
        if ua == "*" or ua.lower() == user_agent.lower():
            candidate = rule
            if ua != "*":
                break
    if not candidate:
        return {"allowed": True, "matched_rule": None}

    def _matches(directive: str, p: str) -> bool:
        if not directive:
            return False
        # crude but effective: support * and $
        pat = re.escape(directive).replace(r"\*", ".*").replace(r"\$", "$")
        return re.match(pat, p) is not None

    longest_match = ("", None)  # (directive, decision)
    for d in candidate.get("allow", []):
        if _matches(d, path) and len(d) > len(longest_match[0]):
            longest_match = (d, "allow")
    for d in candidate.get("disallow", []):
        if _matches(d, path) and len(d) > len(longest_match[0]):
            longest_match = (d, "disallow")
    decision = longest_match[1] or "allow"
    return {"allowed": decision == "allow", "matched_rule": longest_match[0] or None}


# ---------------------------------------------------------------------------
# JSON-LD schema generator
# ---------------------------------------------------------------------------
SUPPORTED_SCHEMA_TYPES = {
    "Article", "BlogPosting", "Product", "FAQPage", "HowTo",
    "BreadcrumbList", "Organization", "LocalBusiness", "Event",
    "Recipe", "Review", "VideoObject", "JobPosting", "WebSite", "Person",
}


def generate_json_ld(schema_type: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Generate a JSON-LD blob for the requested schema type from form inputs."""
    if schema_type not in SUPPORTED_SCHEMA_TYPES:
        raise ValueError(f"Unsupported schema type: {schema_type}")
    base = {"@context": "https://schema.org", "@type": schema_type}

    if schema_type in ("Article", "BlogPosting"):
        base.update({
            "headline": inputs.get("headline"),
            "image": inputs.get("image"),
            "datePublished": inputs.get("date_published"),
            "dateModified": inputs.get("date_modified") or inputs.get("date_published"),
            "author": {"@type": "Person", "name": inputs.get("author_name")},
            "publisher": {
                "@type": "Organization",
                "name": inputs.get("publisher_name"),
                "logo": {"@type": "ImageObject", "url": inputs.get("publisher_logo")} if inputs.get("publisher_logo") else None,
            },
            "description": inputs.get("description"),
        })
    elif schema_type == "Product":
        base.update({
            "name": inputs.get("name"),
            "image": inputs.get("image"),
            "description": inputs.get("description"),
            "sku": inputs.get("sku"),
            "brand": {"@type": "Brand", "name": inputs.get("brand")},
            "offers": {
                "@type": "Offer",
                "url": inputs.get("offer_url"),
                "priceCurrency": inputs.get("currency", "USD"),
                "price": inputs.get("price"),
                "availability": inputs.get("availability", "https://schema.org/InStock"),
            },
        })
    elif schema_type == "FAQPage":
        base["mainEntity"] = [
            {
                "@type": "Question",
                "name": q.get("question"),
                "acceptedAnswer": {"@type": "Answer", "text": q.get("answer")},
            }
            for q in inputs.get("questions", [])
        ]
    elif schema_type == "HowTo":
        base.update({
            "name": inputs.get("name"),
            "description": inputs.get("description"),
            "step": [
                {"@type": "HowToStep", "name": s.get("name"), "text": s.get("text")}
                for s in inputs.get("steps", [])
            ],
        })
    elif schema_type == "BreadcrumbList":
        base["itemListElement"] = [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item.get("name"),
                "item": item.get("url"),
            }
            for i, item in enumerate(inputs.get("items", []))
        ]
    elif schema_type == "Organization":
        base.update({
            "name": inputs.get("name"),
            "url": inputs.get("url"),
            "logo": inputs.get("logo"),
            "sameAs": inputs.get("same_as", []),
        })
    elif schema_type == "LocalBusiness":
        base.update({
            "name": inputs.get("name"),
            "url": inputs.get("url"),
            "telephone": inputs.get("telephone"),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": inputs.get("street_address"),
                "addressLocality": inputs.get("city"),
                "addressRegion": inputs.get("region"),
                "postalCode": inputs.get("postal_code"),
                "addressCountry": inputs.get("country"),
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": inputs.get("latitude"),
                "longitude": inputs.get("longitude"),
            } if inputs.get("latitude") and inputs.get("longitude") else None,
        })
    elif schema_type == "Event":
        base.update({
            "name": inputs.get("name"),
            "startDate": inputs.get("start_date"),
            "endDate": inputs.get("end_date"),
            "location": {
                "@type": "Place", "name": inputs.get("location_name"),
                "address": inputs.get("address"),
            },
        })
    elif schema_type == "Review":
        base.update({
            "reviewBody": inputs.get("review_body"),
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": inputs.get("rating"),
                "bestRating": inputs.get("best_rating", 5),
            },
            "author": {"@type": "Person", "name": inputs.get("author_name")},
        })
    elif schema_type == "VideoObject":
        base.update({
            "name": inputs.get("name"),
            "description": inputs.get("description"),
            "thumbnailUrl": inputs.get("thumbnail"),
            "uploadDate": inputs.get("upload_date"),
            "duration": inputs.get("duration"),
            "contentUrl": inputs.get("content_url"),
        })

    # strip None values recursively
    return _strip_none(base)


def _strip_none(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(v) for v in obj if v is not None]
    return obj
