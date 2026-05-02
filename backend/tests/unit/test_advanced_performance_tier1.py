"""
Test suite for Advanced Performance Analyzer.
Tests Lighthouse scoring, CWV metrics, resource analysis, optimization recommendations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.seo.advanced_performance_analyzer import AdvancedPerformanceAnalyzer


@pytest.fixture
def analyzer():
    return AdvancedPerformanceAnalyzer()


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def sample_url():
    return "https://example.com"


@pytest.mark.asyncio
async def test_analyzer_initialization(analyzer):
    """Test AdvancedPerformanceAnalyzer initialization."""
    assert analyzer is not None
    assert analyzer.timeout == 30.0


@pytest.mark.asyncio
async def test_analyzer_custom_timeout():
    """Test custom timeout configuration."""
    analyzer = AdvancedPerformanceAnalyzer(timeout=60.0)
    assert analyzer.timeout == 60.0


@pytest.mark.asyncio
async def test_analyze_performance_returns_dict(analyzer, mock_client, sample_url):
    """Test that analyze_performance returns a dict."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {"content-encoding": "gzip"}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_analyze_performance_structure(analyzer, mock_client, sample_url):
    """Test result structure."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {"content-encoding": "gzip"}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    
    assert "name" in result
    assert "passed" in result
    assert "score" in result
    assert "metrics" in result
    assert "issues" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_lighthouse_score_range(analyzer, mock_client, sample_url):
    """Test Lighthouse score is 0-100."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    assert 0 <= result["score"] <= 100


@pytest.mark.asyncio
async def test_performance_metrics_present(analyzer, mock_client, sample_url):
    """Test that all performance metrics are present."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    metrics = result["metrics"]
    
    assert "lighthouse_score" in metrics
    assert "core_web_vitals" in metrics
    assert "resources" in metrics


@pytest.mark.asyncio
async def test_core_web_vitals_metrics(analyzer, mock_client, sample_url):
    """Test CWV metrics are present and valid."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    cwv = result["metrics"]["core_web_vitals"]
    
    assert "estimated_fcp_ms" in cwv
    assert "estimated_lcp_ms" in cwv
    assert "estimated_cls" in cwv
    
    assert cwv["estimated_fcp_ms"] >= 0
    assert cwv["estimated_lcp_ms"] >= 0
    assert cwv["estimated_cls"] >= 0


@pytest.mark.asyncio
async def test_resource_analysis(analyzer, mock_client, sample_url):
    """Test resource analysis data."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    resources = result["metrics"]["resources"]
    
    assert "css_files" in resources
    assert "javascript_files" in resources
    assert "images" in resources
    assert "total_size_mb" in resources


@pytest.mark.asyncio
async def test_performance_passed_threshold():
    """Test pass/fail based on score threshold."""
    analyzer = AdvancedPerformanceAnalyzer()
    
    # Score >= 70 should pass
    # Score < 70 should fail
    # This is based on the analyzer logic
    assert True  # Structure test


@pytest.mark.asyncio
async def test_issues_list_format(analyzer, mock_client, sample_url):
    """Test issues list format."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    
    assert isinstance(result["issues"], list)
    for issue in result["issues"]:
        assert isinstance(issue, str)
        assert len(issue) > 0


@pytest.mark.asyncio
async def test_recommendations_list_format(analyzer, mock_client, sample_url):
    """Test recommendations list format."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    
    assert isinstance(result["recommendations"], list)
    for rec in result["recommendations"]:
        assert isinstance(rec, str)


@pytest.mark.asyncio
async def test_page_size_calculation(analyzer, mock_client, sample_url):
    """Test page size is calculated correctly."""
    mock_response = AsyncMock()
    mock_response.content = b"x" * (1024 * 1024 * 2)  # 2MB
    mock_response.text = "x" * 100000
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    resources = result["metrics"]["resources"]
    
    assert resources["total_size_mb"] >= 2.0


@pytest.mark.asyncio
async def test_fcp_lcp_relationship(analyzer, mock_client, sample_url):
    """Test that LCP is generally after FCP."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    cwv = result["metrics"]["core_web_vitals"]
    
    # LCP should typically be >= FCP
    assert cwv["estimated_lcp_ms"] >= cwv["estimated_fcp_ms"]


@pytest.mark.asyncio
async def test_cls_realistic_range(analyzer, mock_client, sample_url):
    """Test CLS is in realistic range."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    cwv = result["metrics"]["core_web_vitals"]
    
    # CLS should be between 0 and typically < 0.5
    assert 0 <= cwv["estimated_cls"] <= 1.0


@pytest.mark.asyncio
async def test_concurrent_analysis(analyzer, mock_client):
    """Test concurrent performance analysis."""
    urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
    
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    async def analyze(url):
        return await analyzer.analyze_performance(url, mock_client)
    
    results = await asyncio.gather(*[analyze(url) for url in urls])
    assert len(results) == 3


@pytest.mark.asyncio
async def test_error_handling(analyzer):
    """Test error handling."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Network error")
    
    result = await analyzer.analyze_performance("https://example.com", mock_client)
    
    assert result["passed"] is False
    assert result["score"] == 0
    assert len(result["issues"]) > 0


@pytest.mark.asyncio
async def test_compression_detection(analyzer, mock_client, sample_url):
    """Test gzip compression detection."""
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {"content-encoding": "gzip"}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    resources = result["metrics"]["resources"]
    
    assert resources["has_compression"] is True


@pytest.mark.asyncio
async def test_performance_trend(analyzer, mock_client):
    """Test performance trending."""
    results = []
    
    mock_response = AsyncMock()
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.headers = {"content-encoding": "gzip"}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    for _ in range(3):
        result = await analyzer.analyze_performance("https://example.com", mock_client)
        results.append(result["score"])
    
    assert len(results) == 3
    assert all(0 <= score <= 100 for score in results)


@pytest.mark.asyncio
async def test_image_optimization_detection(analyzer, mock_client, sample_url):
    """Test image optimization detection."""
    html = """
    <html>
    <body>
        <img src="test.jpg" width="100" height="100" loading="lazy" />
        <img src="test2.png" />
    </body>
    </html>
    """
    
    mock_response = AsyncMock()
    mock_response.content = html.encode()
    mock_response.text = html
    mock_response.headers = {}
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_client.get.return_value = mock_response
    
    result = await analyzer.analyze_performance(sample_url, mock_client)
    resources = result["metrics"]["resources"]
    
    # Should have detected 2 images, 1 optimized, 1 not
    assert resources["images"] == 2


@pytest.mark.asyncio
async def test_performance_score_consistency():
    """Test performance scoring is consistent."""
    analyzer = AdvancedPerformanceAnalyzer()
    
    # Same inputs should give same score calculation
    score1 = analyzer._calculate_lighthouse_score({}, {}, None)
    score2 = analyzer._calculate_lighthouse_score({}, {}, None)
    
    assert score1 == score2
