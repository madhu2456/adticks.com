"""Unit tests for app.services.seo.log_analyzer."""
from __future__ import annotations

import pytest

from app.services.seo.log_analyzer import (
    detect_bot,
    parse_lines,
    detect_orphans,
)


SAMPLE_LOG = '''66.249.66.1 - - [28/Apr/2026:10:00:00 +0000] "GET /page1 HTTP/1.1" 200 1234 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
66.249.66.2 - - [28/Apr/2026:10:00:01 +0000] "GET /page1 HTTP/1.1" 200 1234 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
40.77.167.1 - - [28/Apr/2026:10:00:02 +0000] "GET /page2 HTTP/1.1" 404 0 "-" "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
20.171.207.1 - - [28/Apr/2026:10:00:03 +0000] "GET /page3 HTTP/1.1" 200 5678 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +claudebot@anthropic.com"
1.2.3.4 - - [28/Apr/2026:10:00:04 +0000] "GET /page4 HTTP/1.1" 200 100 "-" "Mozilla/5.0"
'''


class TestDetectBot:
    def test_googlebot(self):
        assert detect_bot("compatible; Googlebot/2.1") == "googlebot"

    def test_bingbot(self):
        assert detect_bot("compatible; bingbot/2.0") == "bingbot"

    def test_claudebot(self):
        assert detect_bot("ClaudeBot/1.0") == "anthropic"

    def test_gptbot(self):
        assert detect_bot("Mozilla/5.0 (compatible) GPTBot/1.0") == "openai"

    def test_perplexity(self):
        assert detect_bot("PerplexityBot/1.0") == "perplexity"

    def test_human_browser_returns_none(self):
        assert detect_bot("Mozilla/5.0 Chrome/120.0") is None


class TestParseLines:
    def test_aggregates_bot_hits(self):
        result = parse_lines(SAMPLE_LOG.splitlines())
        # 4 bot hits (one human request ignored)
        assert result.summary["total_hits"] == 4
        # 3 unique bot URLs
        assert result.summary["unique_urls"] == 3
        # Googlebot, bingbot, anthropic
        assert "googlebot" in result.summary["bots"]
        assert result.summary["bots"]["googlebot"] == 2
        assert result.summary["bots"]["bingbot"] == 1
        assert result.summary["bots"]["anthropic"] == 1

    def test_status_distribution(self):
        result = parse_lines(SAMPLE_LOG.splitlines())
        # 3x 200, 1x 404
        assert result.summary["status_distribution"]["200"] == 3
        assert result.summary["status_distribution"]["404"] == 1

    def test_crawl_waste_pct(self):
        result = parse_lines(SAMPLE_LOG.splitlines())
        # 1/4 = 25%
        assert result.summary["crawl_waste_pct"] == 25.0

    def test_aggregated_rows(self):
        result = parse_lines(SAMPLE_LOG.splitlines())
        # /page1 with googlebot, status 200 -> hits 2
        page1 = next(r for r in result.aggregated if r["url"] == "/page1" and r["bot"] == "googlebot")
        assert page1["hits"] == 2

    def test_empty_input(self):
        result = parse_lines([])
        assert result.summary["total_hits"] == 0
        assert result.aggregated == []

    def test_malformed_lines_ignored(self):
        lines = ["this is not a log line", "neither is this"]
        result = parse_lines(lines)
        assert result.summary["total_hits"] == 0


class TestOrphans:
    def test_diff_returns_both_directions(self):
        crawled = {"/a", "/b", "/c"}
        sitemap = {"/a", "/d"}
        out = detect_orphans(crawled, sitemap)
        assert "/b" in out["crawled_not_in_sitemap"]
        assert "/c" in out["crawled_not_in_sitemap"]
        assert "/d" in out["in_sitemap_not_crawled"]
        assert "/a" not in out["crawled_not_in_sitemap"]
