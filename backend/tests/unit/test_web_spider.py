"""Tests for web spider and related components."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.seo.web_spider import WebSpider, RobotsParser, CrawlResult, BOT_USER_AGENTS
from app.services.seo.sitemap_fetcher import SitemapFetcher
from app.services.seo.spider_analyzer import analyze_spider_results


class TestRobotsParser:
    """Test robots.txt parsing."""

    def test_parse_simple_disallow(self):
        content = """
User-agent: *
Disallow: /admin/
Disallow: /private/
"""
        parser = RobotsParser(content)
        assert not parser.is_allowed("/admin/page")
        assert not parser.is_allowed("/private/data")
        assert parser.is_allowed("/public/page")

    def test_parse_bot_specific(self):
        content = """
User-agent: googlebot
Disallow: /no-google/

User-agent: *
Disallow: /private/
"""
        parser = RobotsParser(content)
        # Googlebot blocked from /no-google/
        assert not parser.is_allowed("/no-google/page", "googlebot")
        # But other bots can access
        assert parser.is_allowed("/no-google/page", "bingbot")
        # All bots blocked from /private/
        assert not parser.is_allowed("/private/page", "googlebot")
        assert not parser.is_allowed("/private/page", "bingbot")

    def test_empty_disallow_allows_all(self):
        content = """
User-agent: *
Disallow:
"""
        parser = RobotsParser(content)
        assert parser.is_allowed("/any/path")


class TestWebSpider:
    """Test web spider functionality."""

    def test_init_default_googlebot(self):
        spider = WebSpider("https://example.com")
        assert spider.bot_name == "googlebot"
        assert spider.user_agent == BOT_USER_AGENTS["googlebot"]

    def test_init_custom_bot(self):
        spider = WebSpider("https://example.com", bot_name="bingbot")
        assert spider.bot_name == "bingbot"
        assert spider.user_agent == BOT_USER_AGENTS["bingbot"]

    def test_domain_normalization(self):
        spider1 = WebSpider("https://example.com/")
        spider2 = WebSpider("https://example.com")
        assert spider1.domain == spider2.domain

    def test_max_urls_limit(self):
        spider = WebSpider("https://example.com", max_urls=10)
        assert spider.max_urls == 10

    @pytest.mark.asyncio
    async def test_fetch_url_success(self):
        spider = WebSpider("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time = MagicMock(side_effect=[0.0, 0.1])
            result = await spider._fetch_url(mock_client, "https://example.com/page")

        assert result.status_code == 200
        assert result.url == "https://example.com/page"
        assert result.bot_name == "googlebot"
        assert result.response_time_ms > 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_fetch_url_redirect(self):
        spider = WebSpider("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 301
        mock_response.headers = {"location": "https://example.com/new-page"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time = MagicMock(side_effect=[0.0, 0.05])
            result = await spider._fetch_url(mock_client, "https://example.com/old-page")

        assert result.status_code == 301
        assert result.redirect_to == "https://example.com/new-page"

    @pytest.mark.asyncio
    async def test_fetch_url_error(self):
        spider = WebSpider("https://example.com")
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection timeout"))

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.time = MagicMock(side_effect=[0.0, 0.5])
            result = await spider._fetch_url(mock_client, "https://example.com/page")

        assert result.status_code == 0
        assert result.error == "Connection timeout"

    def test_get_stats_empty(self):
        spider = WebSpider("https://example.com")
        stats = spider.get_stats()
        
        assert stats.total_urls_crawled == 0
        assert stats.unique_urls == 0
        assert stats.crawl_waste_pct == 0.0
        assert stats.avg_response_time_ms == 0.0

    def test_get_stats_with_results(self):
        spider = WebSpider("https://example.com")
        spider.results = [
            CrawlResult("https://example.com/page1", 200, 100.0, "googlebot"),
            CrawlResult("https://example.com/page2", 404, 50.0, "googlebot"),
            CrawlResult("https://example.com/page3", 500, 200.0, "googlebot"),
        ]
        spider.crawled_urls = {"https://example.com/page1", "https://example.com/page2", "https://example.com/page3"}

        stats = spider.get_stats()
        
        assert stats.total_urls_crawled == 3
        assert stats.unique_urls == 3
        assert stats.status_distribution[200] == 1
        assert stats.status_distribution[404] == 1
        assert stats.status_distribution[500] == 1
        assert stats.crawl_waste_pct == 66.7  # 2 errors out of 3
        assert stats.avg_response_time_ms == pytest.approx(116.67, rel=0.1)


class TestSitemapFetcher:
    """Test sitemap fetching."""

    def test_is_sitemap_index(self):
        fetcher = SitemapFetcher("https://example.com")
        
        index_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap1.xml</loc>
  </sitemap>
</sitemapindex>"""
        
        assert fetcher._is_sitemap_index(index_content)

        regular_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
  </url>
</urlset>"""
        
        assert not fetcher._is_sitemap_index(regular_content)

    def test_extract_urls_from_sitemap(self):
        fetcher = SitemapFetcher("https://example.com")
        
        content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
  </url>
  <url>
    <loc>https://example.com/page2</loc>
  </url>
</urlset>"""
        
        urls = fetcher._extract_urls(content)
        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    def test_extract_sitemaps_from_index(self):
        fetcher = SitemapFetcher("https://example.com")
        
        content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap2.xml</loc>
  </sitemap>
</sitemapindex>"""
        
        sitemaps = fetcher._extract_sitemaps(content, "https://example.com")
        assert len(sitemaps) == 2
        assert "https://example.com/sitemap1.xml" in sitemaps
        assert "https://example.com/sitemap2.xml" in sitemaps


class TestSpiderAnalyzer:
    """Test spider result analysis."""

    def test_analyze_simple_crawl(self):
        from app.services.seo.web_spider import SpiderStats

        crawl_results = [
            CrawlResult("https://example.com/page1", 200, 100.0, "googlebot"),
            CrawlResult("https://example.com/page2", 200, 120.0, "googlebot"),
            CrawlResult("https://example.com/page3", 404, 50.0, "googlebot"),
        ]
        
        spider_stats = SpiderStats(
            total_urls_crawled=3,
            unique_urls=3,
            status_distribution={200: 2, 404: 1},
            avg_response_time_ms=90.0,
            crawl_waste_pct=33.3,
            top_status_codes={"200": 2, "404": 1},
            crawl_errors=0,
        )

        result = analyze_spider_results(crawl_results, spider_stats)
        
        assert result.summary["total_urls_crawled"] == 3
        assert result.summary["crawl_waste_pct"] == 33.3
        assert len(result.aggregated) == 3

    def test_analyze_with_orphans(self):
        from app.services.seo.web_spider import SpiderStats

        crawl_results = [
            CrawlResult("https://example.com/page1", 200, 100.0, "googlebot"),
            CrawlResult("https://example.com/orphan", 200, 100.0, "googlebot"),
        ]
        
        spider_stats = SpiderStats(
            total_urls_crawled=2,
            unique_urls=2,
            status_distribution={200: 2},
            avg_response_time_ms=100.0,
            crawl_waste_pct=0.0,
            top_status_codes={"200": 2},
            crawl_errors=0,
        )

        sitemap_urls = {"https://example.com/page1"}

        result = analyze_spider_results(crawl_results, spider_stats, sitemap_urls)
        
        assert "https://example.com/orphan" in result.orphans["crawled_not_in_sitemap"]
        assert "https://example.com/page1" not in result.orphans["in_sitemap_not_crawled"]
