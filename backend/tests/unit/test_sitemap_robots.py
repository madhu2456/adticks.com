"""Unit tests for app.services.seo.sitemap_robots."""
from __future__ import annotations

import pytest

from app.services.seo.sitemap_robots import (
    generate_sitemap_xml,
    validate_robots_txt,
    evaluate_robots_path,
    generate_json_ld,
    SUPPORTED_SCHEMA_TYPES,
)


class TestSitemap:
    def test_basic_sitemap_structure(self):
        urls = [{"url": "https://x.com/"}, {"url": "https://x.com/about"}]
        xml = generate_sitemap_xml(urls)
        assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in xml
        assert "<loc>https://x.com/</loc>" in xml
        assert "<loc>https://x.com/about</loc>" in xml
        assert xml.count("<url>") == 2
        assert "</urlset>" in xml

    def test_escapes_special_chars(self):
        urls = [{"url": "https://x.com/foo?a=1&b=2"}]
        xml = generate_sitemap_xml(urls)
        assert "a=1&amp;b=2" in xml

    def test_uses_provided_priority_and_changefreq(self):
        urls = [{"url": "https://x.com/", "changefreq": "daily", "priority": 1.0}]
        xml = generate_sitemap_xml(urls)
        assert "<changefreq>daily</changefreq>" in xml
        assert "<priority>1.0</priority>" in xml

    def test_skips_urls_without_loc(self):
        urls = [{"url": "https://x.com/"}, {}]
        xml = generate_sitemap_xml(urls)
        assert xml.count("<url>") == 1


class TestRobots:
    def test_valid_robots(self):
        content = """User-agent: *
Disallow: /admin/
Allow: /admin/public/
Sitemap: https://example.com/sitemap.xml"""
        result = validate_robots_txt(content)
        assert result["is_valid"] is True
        assert len(result["rules"]) == 1
        assert result["sitemap_directives"] == ["https://example.com/sitemap.xml"]

    def test_disallow_all_is_error(self):
        content = "User-agent: *\nDisallow: /"
        result = validate_robots_txt(content)
        assert result["is_valid"] is False
        codes = [i["message"] for i in result["issues"]]
        assert any("blocks ALL" in m for m in codes)

    def test_no_sitemap_warning(self):
        content = "User-agent: *\nDisallow: /admin/"
        result = validate_robots_txt(content)
        msgs = [i["message"] for i in result["issues"]]
        assert any("Sitemap" in m for m in msgs)

    def test_malformed_lines_flagged(self):
        content = "User-agent: *\nthis is not a directive"
        result = validate_robots_txt(content)
        msgs = [i["message"] for i in result["issues"]]
        assert any("Malformed" in m for m in msgs)

    def test_relative_sitemap_warning(self):
        content = "User-agent: *\nSitemap: /sitemap.xml"
        result = validate_robots_txt(content)
        msgs = [i["message"] for i in result["issues"]]
        assert any("absolute" in m for m in msgs)

    def test_path_test_allows_when_no_match(self):
        content = "User-agent: *\nDisallow: /admin/"
        result = validate_robots_txt(content)
        out = evaluate_robots_path(result["rules"], "Googlebot", "/")
        assert out["allowed"] is True

    def test_path_test_disallows_match(self):
        content = "User-agent: *\nDisallow: /admin/"
        result = validate_robots_txt(content)
        out = evaluate_robots_path(result["rules"], "Googlebot", "/admin/secret")
        assert out["allowed"] is False

    def test_specific_user_agent_overrides_wildcard(self):
        content = """User-agent: *
Disallow: /admin/
User-agent: Googlebot
Allow: /admin/google/"""
        result = validate_robots_txt(content)
        out = evaluate_robots_path(result["rules"], "Googlebot", "/admin/google/x")
        assert out["allowed"] is True


class TestSchemaGenerator:
    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError):
            generate_json_ld("NotASchema", {})

    def test_article_schema(self):
        out = generate_json_ld("Article", {
            "headline": "Test",
            "author_name": "Jane",
            "publisher_name": "Adticks",
        })
        assert out["@context"] == "https://schema.org"
        assert out["@type"] == "Article"
        assert out["headline"] == "Test"
        assert out["author"]["name"] == "Jane"
        assert out["publisher"]["name"] == "Adticks"
        # None values stripped
        assert "image" not in out

    def test_product_schema(self):
        out = generate_json_ld("Product", {
            "name": "Widget", "price": 19.99, "sku": "W-001",
            "brand": "Acme", "currency": "USD",
        })
        assert out["@type"] == "Product"
        assert out["name"] == "Widget"
        assert out["offers"]["price"] == 19.99
        assert out["brand"]["name"] == "Acme"

    def test_faq_schema(self):
        out = generate_json_ld("FAQPage", {
            "questions": [
                {"question": "What is SEO?", "answer": "Search engine optimization."},
                {"question": "Why?", "answer": "To rank higher."},
            ],
        })
        assert out["@type"] == "FAQPage"
        assert len(out["mainEntity"]) == 2
        assert out["mainEntity"][0]["@type"] == "Question"

    def test_breadcrumb_schema_positions(self):
        out = generate_json_ld("BreadcrumbList", {
            "items": [{"name": "Home", "url": "/"}, {"name": "Blog", "url": "/blog"}],
        })
        assert out["itemListElement"][0]["position"] == 1
        assert out["itemListElement"][1]["position"] == 2

    def test_supported_types_complete(self):
        for t in ["Article", "Product", "FAQPage", "HowTo", "BreadcrumbList",
                  "Organization", "LocalBusiness", "Event", "Review", "VideoObject"]:
            assert t in SUPPORTED_SCHEMA_TYPES
