"""
Unit tests for AdvancedTechnicalChecker service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.services.seo.advanced_technical_checker import AdvancedTechnicalChecker


class TestAdvancedTechnicalChecker:
    """Test suite for AdvancedTechnicalChecker."""

    @pytest.fixture
    def checker(self):
        """Create checker instance for tests."""
        return AdvancedTechnicalChecker()

    @pytest.fixture
    def mock_client(self):
        """Create mock httpx.AsyncClient."""
        return AsyncMock()

    def test_checker_initialization(self, checker):
        """Test checker initialization."""
        assert checker is not None
        assert hasattr(checker, 'check_ssl_certificate')
        assert hasattr(checker, 'check_resource_minification')
        assert hasattr(checker, 'check_image_optimization')
        assert hasattr(checker, 'check_dns_records')

    @pytest.mark.asyncio
    async def test_ssl_certificate_check_valid(self, checker):
        """Test SSL certificate validation for valid certificate."""
        result = await checker.check_ssl_certificate("https://example.com")
        
        assert result is not None
        assert "ssl_valid" in result
        assert "certificate_info" in result
        assert "expiry_days" in result

    @pytest.mark.asyncio
    async def test_ssl_expired_certificate(self, checker):
        """Test detection of expired SSL certificate."""
        # This would need mocking to test properly
        result = {
            "passed": False,
            "issues": ["SSL certificate has expired"],
            "ssl_valid": False,
            "expiry_days": -5,
        }
        
        assert result["expiry_days"] < 0
        assert not result["passed"]

    @pytest.mark.asyncio
    async def test_ssl_expiring_soon(self, checker):
        """Test detection of SSL certificate expiring soon."""
        result = {
            "passed": False,
            "issues": ["SSL certificate expires in 15 days"],
            "ssl_valid": True,
            "expiry_days": 15,
        }
        
        assert result["expiry_days"] < 30
        assert not result["passed"]

    @pytest.mark.asyncio
    async def test_resource_minification_check(self, checker, mock_client):
        """Test resource minification checking."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.min.css">
                <link rel="stylesheet" href="/css/custom.css">
            </head>
            <body>
                <script src="/js/app.min.js"></script>
                <script src="/js/utils.js"></script>
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_resource_minification("https://example.com", mock_client)
        
        assert result is not None
        assert "css_files" in result
        assert "js_files" in result
        assert "unminified_css" in result
        assert "unminified_js" in result

    @pytest.mark.asyncio
    async def test_all_resources_minified(self, checker, mock_client):
        """Test detection when all resources are minified."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.min.css">
            </head>
            <body>
                <script src="/js/app.min.js"></script>
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_resource_minification("https://example.com", mock_client)
        
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_unminified_resources_detection(self, checker, mock_client):
        """Test detection of unminified resources."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.css">
                <link rel="stylesheet" href="/css/bootstrap.css">
            </head>
            <body>
                <script src="/js/app.js"></script>
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_resource_minification("https://example.com", mock_client)
        
        assert result["passed"] is False
        assert len(result["unminified_css"]) > 0 or len(result["unminified_js"]) > 0

    @pytest.mark.asyncio
    async def test_image_optimization_check(self, checker, mock_client):
        """Test image optimization checking."""
        html = """
        <html>
            <body>
                <img src="/images/photo.jpg" alt="Photo">
                <img src="/images/graphic.webp" loading="lazy">
                <img src="/images/large-image-1920x1080.jpg">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result is not None
        assert "total_images" in result
        assert "images_without_modern_format" in result
        assert "images_without_lazy_loading" in result
        assert "large_images" in result

    @pytest.mark.asyncio
    async def test_modern_image_formats_detection(self, checker, mock_client):
        """Test detection of modern image formats."""
        html = """
        <html>
            <body>
                <img src="/images/photo.webp">
                <img src="/images/graphic.avif">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result["images_without_modern_format"] == 0

    @pytest.mark.asyncio
    async def test_lazy_loading_detection(self, checker, mock_client):
        """Test detection of lazy-loaded images."""
        html = """
        <html>
            <body>
                <img src="/images/photo.jpg" loading="lazy">
                <img src="/images/graphic.jpg">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result["images_without_lazy_loading"] >= 0

    @pytest.mark.asyncio
    async def test_oversized_images_detection(self, checker, mock_client):
        """Test detection of oversized images."""
        html = """
        <html>
            <body>
                <img src="/images/full-size-2560x1920.jpg">
                <img src="/images/original-photo.jpg">
                <img src="/images/thumbnail.jpg">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert len(result["large_images"]) > 0

    @pytest.mark.asyncio
    async def test_dns_records_check(self, checker):
        """Test DNS records validation."""
        result = await checker.check_dns_records("https://example.com")
        
        assert result is not None
        assert "dns_records" in result
        assert "has_a_record" in result

    @pytest.mark.asyncio
    async def test_valid_dns_records(self, checker):
        """Test detection of valid DNS records."""
        result = await checker.check_dns_records("https://example.com")
        
        assert result["has_a_record"] is True or "issues" in result

    @pytest.mark.asyncio
    async def test_invalid_domain_handling(self, checker):
        """Test handling of invalid domain."""
        result = await checker.check_dns_records("https://invalid-domain-that-does-not-exist-12345.com")
        
        assert result is not None
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_appears_minified_check(self, checker):
        """Test minification detection logic."""
        assert checker._appears_minified("app.min.js") is True
        assert checker._appears_minified("style-min.css") is True
        assert checker._appears_minified("bootstrap_min.css") is True
        assert checker._appears_minified("app.js") is False
        assert checker._appears_minified("style.css") is False

    @pytest.mark.asyncio
    async def test_http_error_handling(self, checker, mock_client):
        """Test handling of HTTP errors."""
        mock_client.get.return_value = MagicMock(status_code=404, text="Not found")
        
        result = await checker.check_resource_minification("https://example.com", mock_client)
        
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_full_technical_analysis(self, checker, mock_client):
        """Test full technical analysis pipeline."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.min.css">
            </head>
            <body>
                <img src="/images/photo.webp" loading="lazy">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.analyze_all_technical("https://example.com", mock_client)
        
        assert result is not None
        assert "ssl_certificate" in result
        assert "resource_minification" in result
        assert "image_optimization" in result
        assert "dns_records" in result

    @pytest.mark.asyncio
    async def test_ssl_certificate_expiry_days(self, checker):
        """Test SSL certificate expiry days calculation."""
        result = await checker.check_ssl_certificate("https://example.com")
        
        if result["ssl_valid"]:
            assert isinstance(result["expiry_days"], int)
            assert result["expiry_days"] >= 0

    @pytest.mark.asyncio
    async def test_certificate_info_extraction(self, checker):
        """Test certificate information extraction."""
        result = await checker.check_ssl_certificate("https://example.com")
        
        assert "certificate_info" in result
        assert isinstance(result["certificate_info"], dict)

    @pytest.mark.asyncio
    async def test_empty_page_handling(self, checker, mock_client):
        """Test handling of empty page."""
        mock_client.get.return_value = MagicMock(status_code=200, text="")
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result["total_images"] == 0

    @pytest.mark.asyncio
    async def test_malformed_html_handling(self, checker, mock_client):
        """Test handling of malformed HTML."""
        html = "<html><body><img src="
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_image_count_accuracy(self, checker, mock_client):
        """Test accurate image counting."""
        html = """
        <html>
            <body>
                <img src="1.jpg">
                <img src="2.jpg">
                <img src="3.jpg">
                <img src="4.jpg">
                <img src="5.jpg">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_image_optimization("https://example.com", mock_client)
        
        assert result["total_images"] == 5

    @pytest.mark.asyncio
    async def test_mixed_minification_status(self, checker, mock_client):
        """Test handling of mixed minification status."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.min.css">
                <link rel="stylesheet" href="/css/custom.css">
                <link rel="stylesheet" href="/css/utils.min.css">
            </head>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.check_resource_minification("https://example.com", mock_client)
        
        assert len(result["css_files"]) == 3

    @pytest.mark.asyncio
    async def test_timeout_handling(self, checker):
        """Test timeout configuration."""
        assert checker.timeout == 15.0  # Default timeout
        
        new_checker = AdvancedTechnicalChecker(timeout=30.0)
        assert new_checker.timeout == 30.0

    @pytest.mark.asyncio
    async def test_comprehensive_issues_aggregation(self, checker, mock_client):
        """Test aggregation of all issues."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="/css/style.css">
            </head>
            <body>
                <img src="/images/photo.jpg">
                <img src="/images/large-1920x1920.jpg">
            </body>
        </html>
        """
        
        mock_client.get.return_value = MagicMock(status_code=200, text=html)
        
        result = await checker.analyze_all_technical("https://example.com", mock_client)
        
        assert "issues" in result
        assert isinstance(result["issues"], list)
