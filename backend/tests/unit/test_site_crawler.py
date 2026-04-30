"""Unit tests for app.services.seo.site_crawler.

These tests stub out the network layer so they run fully offline. The crawler
is exercised against synthetic HTML responses and we assert that the right
issue codes are surfaced.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from app.services.seo.site_crawler import (
    SiteCrawler,
    crawl_site,
    _normalize,
    _same_origin,
    _word_count,
)


def _make_response(status: int = 200, content_type: str = "text/html",
                   body: bytes = b"<html></html>", headers: dict | None = None,
                   url: str = "https://example.com/") -> httpx.Response:
    h = {"content-type": content_type}
    if headers:
        h.update(headers)
    request = httpx.Request("GET", url)
    return httpx.Response(status, content=body, headers=h, request=request)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_normalize_strips_trailing_slash(self):
        assert _normalize("https://x.com/foo/") == "https://x.com/foo"

    def test_normalize_strips_fragment(self):
        assert _normalize("https://x.com/foo#bar") == "https://x.com/foo"

    def test_normalize_keeps_root_slash(self):
        # only one path char meaning the root, leave alone
        assert _normalize("https://x.com/").startswith("https://x.com")

    def test_same_origin_ignores_www(self):
        assert _same_origin("https://example.com/a", "https://www.example.com/b")

    def test_same_origin_rejects_different_host(self):
        assert not _same_origin("https://a.com/", "https://b.com/")

    def test_word_count_filters_short_tokens(self):
        assert _word_count("Hi I am Claude") == 3  # "Hi", "am", "Claude" (single chars filtered)

    def test_word_count_handles_empty(self):
        assert _word_count("") == 0
        assert _word_count(None) == 0  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Page-level extraction
# ---------------------------------------------------------------------------
class TestExtractSignals:
    def _crawler(self) -> SiteCrawler:
        return SiteCrawler("https://example.com", max_pages=5, max_depth=2)

    def test_missing_title_raises_error_issue(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        soup = BeautifulSoup("<html><body><h1>Hi</h1></body></html>", "html.parser")
        page = c._extract_signals("https://example.com/x", soup, CrawledPageData(url="https://example.com/x"))
        codes = [i.code for i in c.result.issues]
        assert "title-missing" in codes
        assert page.h1 == "Hi"

    def test_short_title_is_warning(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        soup = BeautifulSoup("<html><head><title>Hi</title></head><body></body></html>", "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "title-too-short" in codes

    def test_meta_description_missing_warning(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        soup = BeautifulSoup("<html><head><title>" + "X" * 40 + "</title></head><body><h1>Heading One Test</h1></body></html>", "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "meta-desc-missing" in codes

    def test_thin_content_is_flagged(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><head><title>" + "X" * 40 + "</title><meta name='description' content='" + "x" * 90 + "'/></head><body><h1>Title</h1><p>Short.</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "thin-content" in codes

    def test_images_missing_alt(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><body><img src='a.png'/><img src='b.png' alt='b'/></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        page = c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        assert page.images == 2
        assert page.images_missing_alt == 1
        codes = [i.code for i in c.result.issues]
        assert "img-missing-alt" in codes

    def test_jsonld_schema_extracted(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = """<html><body>
        <script type='application/ld+json'>{"@type": "Article", "headline": "x"}</script>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        page = c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        assert "Article" in page.schema_types
        assert any(s["type"] == "Article" for s in c.result.schemas)

    def test_invalid_jsonld_raises_warning(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = """<html><body>
        <script type='application/ld+json'>{ this is not json }</script>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "schema-invalid-json" in codes

    def test_mixed_content_detected(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><body><img src='http://insecure.com/x.png'/></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "mixed-content" in codes

    def test_canonical_extraction(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><head><link rel='canonical' href='https://example.com/canonical'/></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        page = c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        assert page.canonical_url == "https://example.com/canonical"
        codes = [i.code for i in c.result.issues]
        # different from current url -> notice
        assert "canonical-different" in codes

    def test_noindex_robots_meta(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><head><meta name='robots' content='noindex, follow'/></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        page = c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        assert page.is_indexable is False
        codes = [i.code for i in c.result.issues]
        assert "noindex" in codes

    def test_invalid_hreflang(self):
        from bs4 import BeautifulSoup
        from app.services.seo.site_crawler import CrawledPageData
        c = self._crawler()
        html = "<html><body><link rel='alternate' hreflang='zzzz' href='https://x.com'/></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        c._extract_signals("https://example.com/", soup, CrawledPageData(url="https://example.com/"))
        codes = [i.code for i in c.result.issues]
        assert "hreflang-invalid" in codes


# ---------------------------------------------------------------------------
# Post-crawl dedupe
# ---------------------------------------------------------------------------
class TestDedupe:
    def test_duplicate_titles_flagged(self):
        c = SiteCrawler("https://example.com")
        c._titles["Same Title For Two Pages X"] = ["a", "b"]
        c._post_crawl_dedupe_checks()
        codes = [i.code for i in c.result.issues]
        assert "title-duplicate" in codes
        # both pages get an issue
        assert codes.count("title-duplicate") == 2


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
class TestSummary:
    def test_score_decreases_with_issues(self):
        c = SiteCrawler("https://example.com")
        c._issue("/a", "on_page", "error", "x", "msg")
        c._issue("/a", "on_page", "warning", "y", "msg")
        c._issue("/a", "on_page", "notice", "z", "msg")
        from app.services.seo.site_crawler import CrawledPageData
        c.result.pages = [CrawledPageData(url="/a", response_time_ms=100)]
        s = c._build_summary()
        assert s["errors"] == 1
        assert s["warnings"] == 1
        assert s["notices"] == 1
        assert s["total_issues"] == 3
        assert s["total_pages"] == 1
        # score = 100 - (5 + 2 + 1) = 92
        assert s["score"] == 92
        assert s["issues_by_category"]["on_page"] == 3

    def test_score_clamped_to_zero(self):
        c = SiteCrawler("https://example.com")
        for _ in range(50):
            c._issue("/a", "on_page", "error", "x", "msg")
        s = c._build_summary()
        assert s["score"] == 0


# ---------------------------------------------------------------------------
# Run end-to-end with mocked transport
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_crawl_site_against_mocked_transport(monkeypatch):
    """Crawl a tiny synthetic site and verify pages + issues are produced."""
    pages_html = {
        "https://example.com": (
            b"<html><head><title>Home Page Of Example For Testing</title>"
            b"<meta name='description' content='" + b"x" * 100 + b"'/>"
            b"</head><body><h1>Welcome</h1>"
            b"<p>" + b"word " * 300 + b"</p>"
            b"<a href='/about'>About</a></body></html>"
        ),
        "https://example.com/": (
            b"<html><head><title>Home Page Of Example For Testing</title>"
            b"<meta name='description' content='" + b"x" * 100 + b"'/>"
            b"</head><body><h1>Welcome</h1>"
            b"<p>" + b"word " * 300 + b"</p>"
            b"<a href='/about'>About</a></body></html>"
        ),

        "https://example.com/about": (
            b"<html><head><title>About Us Page At Example Site</title>"
            b"<meta name='description' content='" + b"x" * 100 + b"'/>"
            b"</head><body><h1>About</h1>"
            b"<p>" + b"about " * 300 + b"</p></body></html>"
        ),
        "https://example.com/robots.txt": b"User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml",
        "https://example.com/sitemap.xml": b"<urlset><url><loc>https://example.com/</loc></url></urlset>",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        body = pages_html.get(url)
        if body is None:
            return httpx.Response(404, request=request)
        ct = "text/plain" if url.endswith("robots.txt") else (
            "application/xml" if url.endswith("sitemap.xml") else "text/html"
        )
        return httpx.Response(200, content=body, headers={"content-type": ct}, request=request)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    result = await crawl_site("https://example.com", max_pages=5, max_depth=2)
    assert len(result.pages) >= 1
    # Home page should at least have been crawled
    home = next(p for p in result.pages if p.url.endswith(".com"))
    assert home.status_code == 200
    assert home.title and "Home Page Of Example" in home.title
    assert home.word_count > 50
    # summary populated
    assert "score" in result.summary
    assert result.summary["total_pages"] == len(result.pages)
