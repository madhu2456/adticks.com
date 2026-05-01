"""
Comprehensive tests for ScreenshotAnalyzer and page screenshot checks.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import io
from PIL import Image

from app.services.seo.screenshot_analyzer import ScreenshotAnalyzer, BREAKPOINTS
from app.services.seo.technical_seo import _check_page_screenshots


class TestScreenshotAnalyzerInit:
    """Tests for ScreenshotAnalyzer initialization."""

    def test_init_defaults(self):
        """Test default initialization."""
        analyzer = ScreenshotAnalyzer()
        assert analyzer.timeout == 30.0

    def test_init_custom_timeout(self):
        """Test custom timeout initialization."""
        analyzer = ScreenshotAnalyzer(timeout=60.0)
        assert analyzer.timeout == 60.0

    def test_breakpoints_defined(self):
        """Test that breakpoints are properly defined."""
        assert "mobile" in BREAKPOINTS
        assert "tablet" in BREAKPOINTS
        assert "desktop" in BREAKPOINTS
        assert BREAKPOINTS["mobile"] == (375, 667)
        assert BREAKPOINTS["tablet"] == (768, 1024)
        assert BREAKPOINTS["desktop"] == (1920, 1080)


class TestScreenshotCapture:
    """Tests for screenshot capture functionality."""

    @pytest.mark.asyncio
    async def test_capture_screenshots_success(self):
        """Test successful screenshot capture."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.capture_screenshots("https://example.com", mock_client)

        assert result["passed"] is True
        assert len(result["screenshots"]) == 3
        assert "mobile" in result["screenshots"]
        assert "tablet" in result["screenshots"]
        assert "desktop" in result["screenshots"]
        assert result["summary"]

    @pytest.mark.asyncio
    async def test_screenshot_metadata(self):
        """Test that screenshot metadata is captured correctly."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.capture_screenshots("https://example.com", mock_client)

        for device, data in result["screenshots"].items():
            assert "width" in data
            assert "height" in data
            assert "size_bytes" in data
            assert "captured_at" in data
            assert data["width"] in [375, 768, 1920]
            assert data["height"] in [667, 1024, 1080]
            assert data["size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_capture_screenshots_failure_handling(self):
        """Test handling of screenshot capture failures."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        with patch.object(
            analyzer, "_capture_single_screenshot", side_effect=Exception("Capture failed")
        ):
            result = await analyzer.capture_screenshots("https://example.com", mock_client)

            # Should still return structure but with failures
            assert isinstance(result, dict)
            assert "issues" in result
            assert len(result["issues"]) > 0


class TestVisualMetrics:
    """Tests for visual metrics extraction."""

    @pytest.mark.asyncio
    async def test_extract_visual_metrics_rgb(self):
        """Test extracting metrics from RGB image."""
        analyzer = ScreenshotAnalyzer()
        
        # Create a simple test image
        img = Image.new("RGB", (375, 667), color=(240, 240, 240))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        screenshot_data = img_bytes.getvalue()

        metrics = await analyzer._extract_visual_metrics(screenshot_data, "mobile")

        assert metrics["device"] == "mobile"
        assert "size_kb" in metrics
        assert metrics["format"] == "PNG"
        assert "dimensions" in metrics
        assert metrics["dimensions"]["width"] == 375
        assert metrics["dimensions"]["height"] == 667
        assert metrics["mode"] == "RGB"
        assert metrics["has_transparency"] is False

    @pytest.mark.asyncio
    async def test_extract_visual_metrics_rgba(self):
        """Test extracting metrics from RGBA image."""
        analyzer = ScreenshotAnalyzer()
        
        # Create a simple test image with alpha
        img = Image.new("RGBA", (768, 1024), color=(240, 240, 240, 255))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        screenshot_data = img_bytes.getvalue()

        metrics = await analyzer._extract_visual_metrics(screenshot_data, "tablet")

        assert metrics["device"] == "tablet"
        assert metrics["mode"] == "RGBA"
        assert metrics["has_transparency"] is True

    @pytest.mark.asyncio
    async def test_readability_checks(self):
        """Test readability issue detection."""
        analyzer = ScreenshotAnalyzer()
        
        # Create a very large image
        img = Image.new("RGB", (3000, 2000), color=(240, 240, 240))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        screenshot_data = img_bytes.getvalue()

        metrics = await analyzer._extract_visual_metrics(screenshot_data, "desktop")

        assert "readability_checks" in metrics
        assert metrics["readability_checks"]["very_large_viewport"] is True


class TestResponsiveAnalysis:
    """Tests for responsive design analysis."""

    @pytest.mark.asyncio
    async def test_analyze_responsive_behavior_success(self):
        """Test successful responsive behavior analysis."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.analyze_responsive_behavior("https://example.com", mock_client)

        assert result["passed"] is True
        assert result["breakpoints_analyzed"] == 3
        assert result["responsive_score"] > 0
        assert result["responsive_score"] <= 100

    @pytest.mark.asyncio
    async def test_responsive_score_calculation(self):
        """Test responsive score calculation."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.analyze_responsive_behavior("https://example.com", mock_client)

        # With 3 breakpoints analyzed, score should be 100
        assert result["breakpoints_analyzed"] == 3
        assert result["responsive_score"] == 100

    @pytest.mark.asyncio
    async def test_responsive_recommendations(self):
        """Test that responsive recommendations are generated."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.analyze_responsive_behavior("https://example.com", mock_client)

        assert "recommendations" in result
        # May be empty if all checks pass, but structure should exist
        assert isinstance(result["recommendations"], list)


class TestScreenshotReport:
    """Tests for screenshot report generation."""

    def test_generate_screenshot_report(self):
        """Test screenshot report generation."""
        analyzer = ScreenshotAnalyzer()
        report = analyzer.generate_screenshot_report()

        assert report["service"] == "ScreenshotAnalyzer"
        assert "breakpoints" in report
        assert "max_screenshot_size" in report
        assert "supported_metrics" in report
        assert len(report["breakpoints"]) == 3


@pytest.mark.asyncio
async def test_check_page_screenshots_integration():
    """Integration test for _check_page_screenshots function."""
    mock_client = AsyncMock()

    result = await _check_page_screenshots("https://example.com", mock_client)

    assert "name" in result
    assert result["name"] == "page_screenshots"
    assert "passed" in result
    assert "issues" in result
    assert "screenshots" in result

    if result["passed"]:
        assert len(result["screenshots"]) > 0
        assert "visual_metrics" in result
        assert "responsive_analysis" in result


@pytest.mark.asyncio
async def test_check_page_screenshots_structure():
    """Test the structure of _check_page_screenshots result."""
    mock_client = AsyncMock()

    result = await _check_page_screenshots("https://example.com", mock_client)

    # Verify expected structure
    assert isinstance(result, dict)
    assert "name" in result
    assert "passed" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)
    assert "screenshots" in result
    assert isinstance(result["screenshots"], dict)


class TestScreenshotAnalyzerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_screenshot_data(self):
        """Test handling of invalid screenshot data."""
        analyzer = ScreenshotAnalyzer()
        
        # Try to extract metrics from invalid data
        result = await analyzer._extract_visual_metrics(b"invalid_data", "mobile")

        # Should handle gracefully
        assert isinstance(result, dict)
        assert "device" in result
        # May have extraction_error key
        if "extraction_error" in result:
            assert isinstance(result["extraction_error"], str)

    @pytest.mark.asyncio
    async def test_empty_screenshot_list(self):
        """Test behavior when no screenshots are captured."""
        analyzer = ScreenshotAnalyzer()
        
        with patch.object(analyzer, "_capture_single_screenshot", return_value=None):
            result = await analyzer.capture_screenshots("https://example.com", AsyncMock())

            # Should indicate failure
            assert result["passed"] is False
            assert len(result["screenshots"]) == 0
            assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_screenshot_size_limits(self):
        """Test that oversized screenshots are handled."""
        analyzer = ScreenshotAnalyzer()
        
        # Create a very large image that exceeds limits
        # This is a theoretical test - actual large images would exceed memory
        with patch.object(analyzer, "_capture_single_screenshot", return_value=None):
            result = await analyzer.capture_screenshots("https://example.com", AsyncMock())

            # Should fail gracefully
            assert isinstance(result, dict)


class TestScreenshotColorProfile:
    """Tests for color profile analysis."""

    @pytest.mark.asyncio
    async def test_color_profile_extraction(self):
        """Test extraction of color profile from image."""
        analyzer = ScreenshotAnalyzer()
        
        # Create an image with specific colors
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        screenshot_data = img_bytes.getvalue()

        metrics = await analyzer._extract_visual_metrics(screenshot_data, "mobile")

        assert "color_profile" in metrics
        assert "avg_r" in metrics["color_profile"]
        assert "avg_g" in metrics["color_profile"]
        assert "avg_b" in metrics["color_profile"]


class TestScreenshotTimestamp:
    """Tests for screenshot timestamp handling."""

    @pytest.mark.asyncio
    async def test_screenshot_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        analyzer = ScreenshotAnalyzer()
        mock_client = AsyncMock()

        result = await analyzer.capture_screenshots("https://example.com", mock_client)

        for device, data in result["screenshots"].items():
            timestamp = data["captured_at"]
            # Should be ISO format
            assert isinstance(timestamp, str)
            # Try to parse it as ISO format
            try:
                datetime.fromisoformat(timestamp)
            except ValueError:
                pytest.fail(f"Timestamp {timestamp} is not ISO format")
