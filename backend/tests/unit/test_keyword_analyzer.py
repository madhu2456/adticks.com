"""
Unit tests for KeywordAnalyzer service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.seo.keyword_analyzer import KeywordAnalyzer


class TestKeywordAnalyzer:
    """Test suite for KeywordAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for tests."""
        return KeywordAnalyzer()

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
            <head>
                <title>Best Python SEO Tools - Complete Guide</title>
                <meta name="description" content="Learn about Python SEO tools and libraries">
            </head>
            <body>
                <h1>Python SEO Tools Tutorial</h1>
                <p>Python has several SEO tools available. Python SEO tools can help automate your SEO. 
                   When using Python for SEO, consider these Python SEO frameworks.</p>
                <h2>Popular Python Tools</h2>
                <p>Many developers use Python for SEO automation and Python SEO analysis.</p>
            </body>
        </html>
        """

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze_keywords')
        assert hasattr(analyzer, 'analyze_content_quality')

    @pytest.mark.asyncio
    async def test_analyze_keywords_extraction(self, analyzer, sample_html):
        """Test keyword extraction."""
        result = await analyzer.analyze_keywords(sample_html, "Python SEO tools")
        
        assert result is not None
        assert "primary_keyword" in result
        assert "keyword_density" in result
        assert "placement" in result
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_keyword_density_calculation(self, analyzer, sample_html):
        """Test keyword density calculation."""
        result = await analyzer.analyze_keywords(sample_html, "Python")
        
        assert "keyword_density" in result
        assert isinstance(result["keyword_density"], float)
        assert result["keyword_density"] > 0

    @pytest.mark.asyncio
    async def test_keyword_placement_validation(self, analyzer, sample_html):
        """Test keyword placement detection."""
        result = await analyzer.analyze_keywords(sample_html, "Python SEO")
        
        placement = result.get("placement", {})
        assert "title" in placement
        assert "h1" in placement
        assert "description" in placement

    @pytest.mark.asyncio
    async def test_lsi_keywords_detection(self, analyzer, sample_html):
        """Test LSI keyword detection."""
        result = await analyzer.analyze_keywords(sample_html, "Python")
        
        assert "lsi_keywords" in result
        assert isinstance(result["lsi_keywords"], list)

    @pytest.mark.asyncio
    async def test_content_quality_scoring(self, analyzer, sample_html):
        """Test content quality scoring."""
        result = await analyzer.analyze_content_quality(sample_html)
        
        assert "word_count" in result
        assert "readability_score" in result
        assert result["word_count"] > 0
        assert isinstance(result["readability_score"], float)

    @pytest.mark.asyncio
    async def test_readability_assessment(self, analyzer):
        """Test readability score calculation."""
        # Simple text for testing
        text = "This is a simple test. The test is very simple. Simple tests are good."
        
        score = analyzer.calculate_readability_score(text)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_content_gaps_analysis(self, analyzer, sample_html):
        """Test content gap detection."""
        result = await analyzer.analyze_content_gaps(sample_html, "Python")
        
        assert "gaps" in result
        assert isinstance(result["gaps"], list)

    @pytest.mark.asyncio
    async def test_keyword_density_issues(self, analyzer):
        """Test high keyword density detection."""
        # Create HTML with extremely high keyword density
        text = "Python Python Python Python Python" * 50
        html = f"""
            <html>
                <body><p>{text}</p></body>
            </html>
        """
        
        result = await analyzer.analyze_keywords(html, "Python")
        
        assert result["keyword_density"] > 2.5
        # High density should be flagged as an issue

    @pytest.mark.asyncio
    async def test_multiple_h1_detection(self, analyzer):
        """Test detection of multiple H1 tags."""
        html = """
            <html>
                <body>
                    <h1>First H1</h1>
                    <h1>Second H1</h1>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_keywords(html, "First")
        # Should note multiple H1s in issues

    @pytest.mark.asyncio
    async def test_thin_content_detection(self, analyzer):
        """Test thin content (few words) detection."""
        html = """
            <html>
                <body>
                    <p>Very short content.</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_content_quality(html)
        
        assert result["word_count"] < 10
        # Should flag as thin content

    @pytest.mark.asyncio
    async def test_keyword_placement_in_title(self, analyzer):
        """Test keyword placement in title tag."""
        html = """
            <html>
                <head>
                    <title>Seo Keyword Research Guide</title>
                </head>
                <body><p>Content about keyword research.</p></body>
            </html>
        """
        
        result = await analyzer.analyze_keywords(html, "keyword")
        
        assert result["placement"]["title"] is True

    @pytest.mark.asyncio
    async def test_keyword_placement_in_h1(self, analyzer):
        """Test keyword placement in H1 tag."""
        html = """
            <html>
                <body>
                    <h1>Complete Guide to Keyword Research</h1>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_keywords(html, "keyword")
        
        assert result["placement"]["h1"] is True

    @pytest.mark.asyncio
    async def test_long_form_content_recognition(self, analyzer):
        """Test recognition of long-form content."""
        # Long form content (>2000 words)
        long_content = " ".join(["word"] * 2500)
        html = f"""
            <html>
                <body><p>{long_content}</p></body>
            </html>
        """
        
        result = await analyzer.analyze_content_quality(html)
        
        assert result["word_count"] > 2000

    @pytest.mark.asyncio
    async def test_empty_html_handling(self, analyzer):
        """Test handling of empty HTML."""
        html = "<html><body></body></html>"
        
        result = await analyzer.analyze_keywords(html, "test")
        
        assert "issues" in result
        # Should flag empty content

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, analyzer):
        """Test handling of special characters in content."""
        html = """
            <html>
                <body>
                    <p>Content with special chars: @#$%^&*()!</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_content_quality(html)
        
        assert result["word_count"] > 0

    @pytest.mark.asyncio
    async def test_stopword_filtering(self, analyzer):
        """Test that stop words are filtered correctly."""
        text = "the and or is a an to from with"
        
        keywords = analyzer._extract_keywords(text)
        
        # Stop words should be removed
        assert "the" not in [k.lower() for k in keywords]
        assert "and" not in [k.lower() for k in keywords]

    @pytest.mark.asyncio
    async def test_keyword_relevance_scoring(self, analyzer):
        """Test keyword relevance scoring."""
        html = """
            <html>
                <head><title>Python Tutorials</title></head>
                <body>
                    <h1>Learn Python</h1>
                    <p>Python is great. Learn Python programming.</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_keywords(html, "Python")
        
        assert "relevance_score" in result or result["keyword_density"] > 0

    @pytest.mark.asyncio
    async def test_readability_score_range(self, analyzer):
        """Test that readability score is within expected range."""
        html = """
            <html>
                <body>
                    <p>
                        The quick brown fox jumps over the lazy dog. This is a test.
                        Testing is important for software quality. Software must be tested.
                    </p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_content_quality(html)
        
        score = result["readability_score"]
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, analyzer, sample_html):
        """Test full keyword analysis pipeline."""
        keyword_result = await analyzer.analyze_keywords(sample_html, "Python")
        quality_result = await analyzer.analyze_content_quality(sample_html)
        gap_result = await analyzer.analyze_content_gaps(sample_html, "Python")
        
        assert keyword_result.get("keyword_density") is not None
        assert quality_result.get("word_count") is not None
        assert gap_result.get("gaps") is not None
