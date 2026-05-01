"""Unit tests for expanded technical SEO module with 14 checks."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from bs4 import BeautifulSoup

from app.services.seo.technical_seo import (
    check_technical,
    _check_meta_tags,
    _check_headings,
    _check_canonical,
    _check_structured_data,
    _check_mobile_friendly,
    _check_images,
    _check_url_structure,
    _check_security_headers,
    _check_hreflang,
    _normalize_domain,
    _get_root_url,
)


class TestNormalizeDomain:
    """Tests for domain normalization."""

    def test_normalize_bare_domain(self):
        """Bare domain gets https scheme."""
        result = _normalize_domain("example.com")
        assert result == "https://example.com"

    def test_normalize_domain_with_trailing_slash(self):
        """Trailing slash is removed."""
        result = _normalize_domain("https://example.com/")
        assert result == "https://example.com"

    def test_normalize_http_domain(self):
        """HTTP domain preserved."""
        result = _normalize_domain("http://example.com")
        assert result == "http://example.com"

    def test_normalize_domain_case_insensitive(self):
        """Domain is lowercased."""
        result = _normalize_domain("HTTPS://EXAMPLE.COM")
        assert result == "https://example.com"


class TestGetRootUrl:
    """Tests for root URL extraction."""

    def test_get_root_url_from_full_url(self):
        """Root URL extracted from full URL."""
        result = _get_root_url("https://example.com/path/page")
        assert result == "https://example.com"

    def test_get_root_url_with_port(self):
        """Port is preserved."""
        result = _get_root_url("https://example.com:8080/path")
        assert result == "https://example.com:8080"

    def test_get_root_url_bare_domain(self):
        """Bare domain normalized."""
        result = _get_root_url("example.com")
        assert result == "https://example.com"


class TestMetaTags:
    """Tests for meta tags check."""

    @pytest.mark.asyncio
    async def test_meta_tags_valid(self):
        """Valid meta tags detected."""
        html = """
        <html>
        <head>
            <title>Perfect Title Length For SEO Today</title>
            <meta name="description" content="This is a good meta description that is between 70 and 160 characters long for testing.">
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:title" content="OG Title">
            <meta name="twitter:card" content="summary">
        </head>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_meta_tags("https://example.com", client)
        
        assert result["meta_title"] is not None
        assert result["title_ok"] is True
        assert result["description_ok"] is True
        assert result["charset_present"] is True
        assert result["viewport_present"] is True
        assert len(result["og_tags"]) > 0
        assert result["twitter_card_present"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_meta_tags_missing_title(self):
        """Missing title detected."""
        html = "<html><head></head></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_meta_tags("https://example.com", client)
        
        assert result["meta_title"] is None
        assert "Missing title tag" in result["issues"]

    @pytest.mark.asyncio
    async def test_meta_tags_title_too_short(self):
        """Title too short detected."""
        html = '<html><head><title>Short</title></head></html>'
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_meta_tags("https://example.com", client)
        
        assert result["title_ok"] is False
        assert any("too short" in issue for issue in result["issues"])


class TestHeadings:
    """Tests for heading structure check."""

    @pytest.mark.asyncio
    async def test_headings_valid_structure(self):
        """Valid heading structure detected."""
        html = """
        <html>
        <body>
            <h1>Main Heading</h1>
            <h2>Subheading 1</h2>
            <h3>Sub-subheading</h3>
            <h2>Subheading 2</h2>
        </body>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_headings("https://example.com", client)
        
        assert result["h1_count"] == 1
        assert result["h1_ok"] is True
        assert result["h2_count"] == 2
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_headings_missing_h1(self):
        """Missing H1 detected."""
        html = "<html><body><h2>No H1</h2></body></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_headings("https://example.com", client)
        
        assert result["h1_count"] == 0
        assert result["h1_ok"] is False
        assert any("No H1 tag found" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_headings_multiple_h1(self):
        """Multiple H1 tags detected."""
        html = "<html><body><h1>H1 One</h1><h1>H1 Two</h1></body></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_headings("https://example.com", client)
        
        assert result["h1_count"] == 2
        assert result["h1_ok"] is False
        assert any("Multiple H1" in issue for issue in result["issues"])


class TestCanonical:
    """Tests for canonical tag check."""

    @pytest.mark.asyncio
    async def test_canonical_present_and_valid(self):
        """Valid canonical tag detected."""
        html = '<html><head><link rel="canonical" href="https://example.com/page"></head></html>'
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_canonical("https://example.com/page", client)
        
        assert result["canonical_present"] is True
        assert result["canonical_tag"] == "https://example.com/page"
        assert result["is_self_referential"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_canonical_missing(self):
        """Missing canonical tag detected."""
        html = "<html><head></head></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_canonical("https://example.com", client)
        
        assert result["canonical_present"] is False
        assert any("Missing canonical tag" in issue for issue in result["issues"])


class TestStructuredData:
    """Tests for structured data check."""

    @pytest.mark.asyncio
    async def test_json_ld_detected(self):
        """JSON-LD detected."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "Organization"}
            </script>
        </head>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_structured_data("https://example.com", client)
        
        assert result["has_json_ld"] is True
        assert len(result["json_ld_types"]) > 0

    @pytest.mark.asyncio
    async def test_no_structured_data(self):
        """No structured data detected."""
        html = "<html><head></head></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_structured_data("https://example.com", client)
        
        assert result["has_json_ld"] is False
        assert result["has_microdata"] is False
        assert any("No structured data found" in issue for issue in result["issues"])


class TestMobileFriendly:
    """Tests for mobile-friendly check."""

    @pytest.mark.asyncio
    async def test_mobile_friendly_valid(self):
        """Mobile-friendly page detected."""
        html = '<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head></html>'
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_mobile_friendly("https://example.com", client)
        
        assert result["viewport_present"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_mobile_friendly_missing_viewport(self):
        """Missing viewport detected."""
        html = "<html><head></head></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_mobile_friendly("https://example.com", client)
        
        assert result["viewport_present"] is False
        assert any("Viewport meta tag missing" in issue for issue in result["issues"])


class TestImages:
    """Tests for image alt text check."""

    @pytest.mark.asyncio
    async def test_images_with_alt_text(self):
        """Images with alt text detected."""
        html = """
        <html>
        <body>
            <img src="photo1.jpg" alt="Photo 1">
            <img src="photo2.jpg" alt="Photo 2">
        </body>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_images("https://example.com", client)
        
        assert result["total_images"] == 2
        assert result["images_with_alt"] == 2
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_images_missing_alt_text(self):
        """Images without alt text detected."""
        html = """
        <html>
        <body>
            <img src="photo1.jpg">
            <img src="photo2.jpg" alt="Photo 2">
        </body>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_images("https://example.com", client)
        
        assert result["total_images"] == 2
        assert result["images_with_alt"] == 1
        assert any("missing alt text" in issue for issue in result["issues"])


class TestUrlStructure:
    """Tests for URL structure check."""

    def test_url_structure_valid(self):
        """Valid URL structure detected."""
        result = _check_url_structure("https://example.com/blog/seo-guide/2024")
        
        assert result["depth"] == 2  # blog/seo-guide/2024 = 2 slashes
        assert result["param_count"] == 0
        assert result["has_hyphens"] is True
        assert result["has_underscores"] is False
        assert len(result["issues"]) == 0

    def test_url_structure_with_parameters(self):
        """URL parameters detected."""
        result = _check_url_structure("https://example.com/page?id=123&utm_source=google")
        
        assert result["param_count"] == 2
        assert result["is_seo_friendly"] is True  # 2 params is OK

    def test_url_structure_too_deep(self):
        """Deep URL path detected."""
        result = _check_url_structure("https://example.com/a/b/c/d/e/f/page")
        
        assert result["depth"] == 6
        assert result["is_seo_friendly"] is False
        assert any("depth" in issue.lower() for issue in result["issues"])


class TestSecurityHeaders:
    """Tests for security headers check."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Security headers detected."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"
        mock_response.headers = {
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin",
            "Permissions-Policy": "camera=(), microphone=()",
        }
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_security_headers("https://example.com", client)
        
        assert result["csp_present"] is True
        assert result["x_frame_options"] is not None
        assert result["x_content_type_options"] is not None
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_security_headers_missing(self):
        """Missing security headers detected."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"
        mock_response.headers = {}
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_security_headers("https://example.com", client)
        
        assert result["csp_present"] is False
        assert result["x_frame_options"] is None
        assert any("Missing" in issue for issue in result["issues"])


class TestHreflang:
    """Tests for hreflang tag check."""

    @pytest.mark.asyncio
    async def test_hreflang_present(self):
        """Hreflang tags detected."""
        html = """
        <html>
        <head>
            <link rel="alternate" hreflang="en" href="https://example.com/en">
            <link rel="alternate" hreflang="es" href="https://example.com/es">
            <link rel="alternate" hreflang="x-default" href="https://example.com">
        </head>
        </html>
        """
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_hreflang("https://example.com", client)
        
        assert result["has_hreflang"] is True
        assert len(result["hreflang_tags"]) == 3
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_hreflang_missing(self):
        """Missing hreflang tags (OK for single-language sites)."""
        html = "<html><head></head></html>"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html
        
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)
        
        result = await _check_hreflang("https://example.com", client)
        
        assert result["has_hreflang"] is False
        assert result["hreflang_tags"] == []


class TestCheckTechnical:
    """Integration tests for complete technical audit."""

    @pytest.mark.asyncio
    async def test_check_technical_comprehensive(self):
        """Complete 14-check technical audit."""
        # Mock minimal valid responses for all checks
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <title>Perfect Title 30 60</title>
            <meta name="description" content="This is a good meta description that is between 70 and 160 characters long for testing.">
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="canonical" href="https://example.com">
            <script type="application/ld+json">{"@type": "Organization"}</script>
            <h1>Main Heading</h1>
        </head>
        <body>
            <img src="test.jpg" alt="test">
        </body>
        </html>
        """
        mock_response.headers = {
            "Cache-Control": "max-age=3600",
            "Content-Encoding": "gzip",
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN",
            "Strict-Transport-Security": "max-age=31536000",
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await check_technical("https://example.com")
        
        # Verify result structure
        assert result["domain"] == "https://example.com"
        assert result["root_url"] == "https://example.com"
        assert result["checks"] is not None
        assert "crawlability" in result["checks"]
        assert "security" in result["checks"]
        assert "performance" in result["checks"]
        assert "on_page" in result["checks"]
        assert "structured_data" in result["checks"]
        assert "mobile" in result["checks"]
        assert "images" in result["checks"]
        assert "url_structure" in result["checks"]
        assert "international" in result["checks"]
        
        # Verify scoring
        assert result["checks_total"] == 14
        assert 0 <= result["health_score"] <= 100
        assert result["checks_passed"] >= 0
        assert isinstance(result["all_issues"], list)
        assert result["issues_count"] == len(result["all_issues"])
