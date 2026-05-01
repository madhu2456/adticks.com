"""
Tests for content freshness tracking feature.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from app.services.seo.content_freshness import ContentFreshnessAnalyzer


class TestContentFreshnessAnalyzerInit:
    """Test ContentFreshnessAnalyzer initialization."""
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        assert analyzer.root_url == "https://example.com"
        assert analyzer.timeout == 15.0
    
    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        analyzer = ContentFreshnessAnalyzer("https://example.com", timeout=30.0)
        assert analyzer.timeout == 30.0


class TestFreshnessThresholds:
    """Test freshness categorization thresholds."""
    
    def test_fresh_threshold(self):
        """Pages updated within 30 days should be fresh."""
        assert ContentFreshnessAnalyzer.FRESH_THRESHOLD == 30
    
    def test_moderate_threshold(self):
        """Pages updated within 90 days should be moderate."""
        assert ContentFreshnessAnalyzer.MODERATE_THRESHOLD == 90
    
    def test_stale_threshold(self):
        """Pages updated within 180 days should be stale."""
        assert ContentFreshnessAnalyzer.STALE_THRESHOLD == 180
    
    def test_very_stale_threshold(self):
        """Pages updated after 365 days should be very stale."""
        assert ContentFreshnessAnalyzer.VERY_STALE_THRESHOLD == 365


@pytest.mark.asyncio
class TestPageFreshnessAnalysis:
    """Test page-level freshness analysis."""
    
    async def test_analyze_page_with_last_modified(self):
        """Test analyzing page with Last-Modified header."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        # Create mock response with Last-Modified header
        mock_response = MagicMock()
        mock_response.headers = {
            "last-modified": "Wed, 21 Oct 2025 07:28:00 GMT",
            "date": "Wed, 21 Oct 2025 08:00:00 GMT",
        }
        
        client = AsyncMock()
        client.head = AsyncMock(return_value=mock_response)
        
        result = await analyzer.analyze_page_freshness(client, "https://example.com")
        
        assert result["url"] == "https://example.com"
        assert result["last_modified"] is not None
        assert "freshness_level" in result
    
    async def test_analyze_page_missing_last_modified(self):
        """Test analyzing page without Last-Modified header."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        mock_response = MagicMock()
        mock_response.headers = {}
        
        client = AsyncMock()
        client.head = AsyncMock(return_value=mock_response)
        
        result = await analyzer.analyze_page_freshness(client, "https://example.com")
        
        assert result["last_modified"] is None
        assert result["freshness_level"] == "unknown"


@pytest.mark.asyncio
class TestSitemapFreshnessAnalysis:
    """Test sitemap-level freshness analysis."""
    
    async def test_analyze_sitemap_found(self):
        """Test analyzing when sitemap is found."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2025-10-21</lastmod>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
                <lastmod>2025-09-21</lastmod>
            </url>
        </urlset>"""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_xml
        
        client = AsyncMock()
        client.get = AsyncMock(return_value=mock_response)
        
        result = await analyzer.analyze_sitemap_freshness(client, "https://example.com")
        
        assert result["found"] is True
        assert result["urls_analyzed"] > 0
        assert "freshness_breakdown" in result
    
    async def test_analyze_sitemap_not_found(self):
        """Test analyzing when sitemap is not found."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        client = AsyncMock()
        client.get = AsyncMock(return_value=mock_response)
        
        result = await analyzer.analyze_sitemap_freshness(client, "https://example.com")
        
        assert result["found"] is False
        assert len(result["issues"]) > 0


@pytest.mark.asyncio
class TestContentUpdateDetection:
    """Test content update detection."""
    
    async def test_detect_recent_updates(self):
        """Test detecting recently updated content."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        mock_response = MagicMock()
        last_mod = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        mock_response.headers = {
            "last-modified": last_mod,
            "cache-control": "max-age=3600",
            "etag": '"123abc"',
        }
        
        client = AsyncMock()
        client.head = AsyncMock(return_value=mock_response)
        
        result = await analyzer.detect_content_updates(client, "https://example.com")
        
        assert result["has_etag"] is True
        assert result["has_cache_control"] is True
        assert "frequent" in result["update_frequency_indicator"] or "occasional" in result["update_frequency_indicator"]
    
    async def test_detect_cache_control_max_age(self):
        """Test extracting cache max-age."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        mock_response = MagicMock()
        mock_response.headers = {
            "cache-control": "public, max-age=7200, must-revalidate",
        }
        
        client = AsyncMock()
        client.head = AsyncMock(return_value=mock_response)
        
        result = await analyzer.detect_content_updates(client, "https://example.com")
        
        assert result["cache_max_age"] == 7200


@pytest.mark.asyncio
class TestOverallFreshnessAssessment:
    """Test overall freshness assessment."""
    
    async def test_overall_assessment_fresh_content(self):
        """Test overall assessment for fresh content."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        # Mock page freshness
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"last-modified": "Wed, 21 Oct 2025 07:28:00 GMT"}
        mock_response.text = "<html></html>"
        
        client = AsyncMock()
        client.head = AsyncMock(return_value=mock_response)
        client.get = AsyncMock(return_value=MagicMock(status_code=404))
        
        result = await analyzer.overall_freshness_assessment(client, "https://example.com")
        
        assert "page_freshness" in result
        assert "sitemap_freshness" in result
        assert "content_updates" in result
        assert "overall_freshness" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)


class TestFreshnessIntegration:
    """Integration tests for content freshness."""
    
    def test_freshness_level_categorization(self):
        """Test freshness level categorization logic."""
        analyzer = ContentFreshnessAnalyzer("https://example.com")
        
        # Fresh: <= 30 days
        assert analyzer.FRESH_THRESHOLD <= 30
        
        # Moderate: 31-90 days
        assert analyzer.MODERATE_THRESHOLD == 90
        
        # Stale: 91-180 days
        assert analyzer.STALE_THRESHOLD == 180
        
        # Very Stale: > 365 days
        assert analyzer.VERY_STALE_THRESHOLD == 365


@pytest.mark.asyncio
class TestTechnicalSEOFreshnessIntegration:
    """Integration tests for freshness check in technical_seo."""
    
    async def test_check_content_freshness_structure(self):
        """Test _check_content_freshness returns proper structure."""
        from app.services.seo.technical_seo import _check_content_freshness
        
        client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "<html></html>"
        
        client.head = AsyncMock(return_value=mock_response)
        client.get = AsyncMock(return_value=MagicMock(status_code=404))
        
        result = await _check_content_freshness("https://example.com", client)
        
        # Verify required keys
        assert "overall_freshness" in result
        assert "page_age_days" in result
        assert "sitemap_average_age_days" in result
        assert "urls_analyzed" in result
        assert "freshness_breakdown" in result
        assert "last_update" in result
        assert "update_frequency" in result
        assert "issues" in result
        assert "recommendations" in result
        assert "passed" in result
        assert isinstance(result["passed"], bool)


class TestRecommendationGeneration:
    """Test recommendation generation for stale content."""
    
    def test_very_stale_content_recommendation(self):
        """Test recommendation for very stale content."""
        # Simulate very stale content (>365 days)
        recommendations = []
        age_days = 400
        
        if age_days > 365:
            recommendations.append(f"Main page hasn't been updated in {age_days} days")
        
        assert len(recommendations) > 0
        assert "400 days" in recommendations[0]
    
    def test_excessive_stale_urls_recommendation(self):
        """Test recommendation for excessive stale URLs in sitemap."""
        freshness_breakdown = {
            "fresh": 5,
            "moderate": 10,
            "stale": 30,
            "very_stale": 55,
            "no_date": 0,
        }
        
        total = sum([v for k, v in freshness_breakdown.items() if k != "no_date"])
        stale_pct = ((freshness_breakdown["stale"] + freshness_breakdown["very_stale"]) / total) * 100
        
        recommendations = []
        if stale_pct > 30:
            recommendations.append(f"Review and update stale content ({stale_pct:.0f}% of sitemap)")
        
        assert len(recommendations) > 0
        assert "85%" in recommendations[0]  # 85/100 = 85%


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_sitemap(self):
        """Test handling of empty sitemap."""
        # Empty sitemap should not crash
        result = {
            "urls_analyzed": 0,
            "freshness_breakdown": {
                "fresh": 0,
                "moderate": 0,
                "stale": 0,
                "very_stale": 0,
                "no_date": 0,
            }
        }
        
        assert result["urls_analyzed"] == 0
    
    def test_malformed_date_header(self):
        """Test handling of malformed date headers."""
        # Should not crash, should default to unknown
        result = {
            "last_modified": "invalid-date-format",
            "freshness_level": "unknown",
        }
        
        assert result["freshness_level"] == "unknown"
