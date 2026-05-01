"""
Unit tests for ContentQualityAnalyzer service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.seo.content_quality_analyzer import ContentQualityAnalyzer


class TestContentQualityAnalyzer:
    """Test suite for ContentQualityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for tests."""
        return ContentQualityAnalyzer()

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
            <head>
                <title>Complete Guide to Content Quality</title>
                <meta name="description" content="Learn how to create high-quality content">
            </head>
            <body>
                <h1>Content Quality Guide</h1>
                <p>Content quality is crucial for SEO success. High-quality content engages readers 
                   and improves rankings. When creating content, focus on providing value to your audience.</p>
                <h2>Best Practices</h2>
                <p>Always proofread your content. Ensure your content is original and provides unique value.
                   Good content drives traffic and builds authority.</p>
            </body>
        </html>
        """

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer is not None
        assert hasattr(analyzer, 'check_duplicate_content')
        assert hasattr(analyzer, 'check_thin_content')
        assert hasattr(analyzer, 'analyze_plagiarism_risk')

    @pytest.mark.asyncio
    async def test_duplicate_content_detection(self, analyzer):
        """Test duplicate content detection."""
        html = """
            <html>
                <head>
                    <title>Duplicate Title</title>
                    <meta name="description" content="Duplicate description">
                </head>
                <body><p>Content</p></body>
            </html>
        """
        
        result = await analyzer.check_duplicate_content(html)
        
        assert result is not None
        assert "duplicate_title" in result
        assert "duplicate_description" in result
        assert "content_hash" in result

    @pytest.mark.asyncio
    async def test_thin_content_detection(self, analyzer):
        """Test thin content detection."""
        thin_html = """
            <html>
                <body>
                    <p>Very thin.</p>
                </body>
            </html>
        """
        
        result = await analyzer.check_thin_content(thin_html)
        
        assert result is not None
        assert "is_thin" in result
        assert "word_count" in result
        assert result["is_thin"] is True

    @pytest.mark.asyncio
    async def test_sufficient_content_length(self, analyzer, sample_html):
        """Test detection of sufficient content length."""
        result = await analyzer.check_thin_content(sample_html)
        
        assert result["is_thin"] is False
        assert result["word_count"] > 300

    @pytest.mark.asyncio
    async def test_plagiarism_risk_assessment(self, analyzer, sample_html):
        """Test plagiarism risk assessment."""
        result = await analyzer.analyze_plagiarism_risk(sample_html)
        
        assert result is not None
        assert "plagiarism_risk" in result
        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_readability_score_calculation(self, analyzer, sample_html):
        """Test readability score calculation."""
        result = await analyzer.calculate_readability_score(sample_html)
        
        assert isinstance(result, float)
        assert 0 <= result <= 100

    @pytest.mark.asyncio
    async def test_high_plagiarism_indicators(self, analyzer):
        """Test detection of high plagiarism risk indicators."""
        risky_html = """
            <html>
                <body>
                    <p>As stated in the original publication, "This is a quote from another source."
                    "Another quoted passage" according to sources.</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_plagiarism_risk(risky_html)
        
        assert result["risk_level"] in ["medium", "high"]

    @pytest.mark.asyncio
    async def test_unique_content_low_risk(self, analyzer):
        """Test unique content receives low plagiarism risk."""
        unique_html = """
            <html>
                <body>
                    <p>This is my personal opinion about content marketing strategy. Based on my experience,
                    I believe that original research leads to better results. My methodology involves testing.</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_plagiarism_risk(unique_html)
        
        assert result["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_content_hash_generation(self, analyzer):
        """Test content hash generation."""
        html = "<html><body><p>Test content</p></body></html>"
        
        result = await analyzer.check_duplicate_content(html)
        
        assert "content_hash" in result
        assert isinstance(result["content_hash"], str)
        assert len(result["content_hash"]) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_identical_hashes_for_same_content(self, analyzer):
        """Test identical hashes for identical content."""
        html = "<html><body><p>Test content</p></body></html>"
        
        result1 = await analyzer.check_duplicate_content(html)
        result2 = await analyzer.check_duplicate_content(html)
        
        assert result1["content_hash"] == result2["content_hash"]

    @pytest.mark.asyncio
    async def test_different_hashes_for_different_content(self, analyzer):
        """Test different hashes for different content."""
        html1 = "<html><body><p>Test content 1</p></body></html>"
        html2 = "<html><body><p>Test content 2</p></body></html>"
        
        result1 = await analyzer.check_duplicate_content(html1)
        result2 = await analyzer.check_duplicate_content(html2)
        
        assert result1["content_hash"] != result2["content_hash"]

    @pytest.mark.asyncio
    async def test_minimum_word_count_threshold(self, analyzer):
        """Test minimum word count threshold."""
        # Content with exactly 300 words
        words = " ".join(["word"] * 300)
        html = f"<html><body><p>{words}</p></body></html>"
        
        result = await analyzer.check_thin_content(html)
        
        assert result["is_thin"] is False

    @pytest.mark.asyncio
    async def test_just_below_threshold(self, analyzer):
        """Test content just below minimum threshold."""
        # Content with 299 words
        words = " ".join(["word"] * 299)
        html = f"<html><body><p>{words}</p></body></html>"
        
        result = await analyzer.check_thin_content(html)
        
        assert result["is_thin"] is True

    @pytest.mark.asyncio
    async def test_grammar_check_indicators(self, analyzer):
        """Test detection of potential grammar issues."""
        poor_grammar = """
            <html>
                <body>
                    <p>The content are very good. It don't have any issues. 
                    We was happy with the results.</p>
                </body>
            </html>
        """
        
        result = await analyzer.check_thin_content(poor_grammar)
        # Should return some indicator of issues

    @pytest.mark.asyncio
    async def test_full_quality_analysis(self, analyzer, sample_html):
        """Test full content quality analysis."""
        dup_result = await analyzer.check_duplicate_content(sample_html)
        thin_result = await analyzer.check_thin_content(sample_html)
        plag_result = await analyzer.analyze_plagiarism_risk(sample_html)
        read_result = await analyzer.calculate_readability_score(sample_html)
        
        assert dup_result is not None
        assert thin_result is not None
        assert plag_result is not None
        assert 0 <= read_result <= 100

    @pytest.mark.asyncio
    async def test_empty_content_handling(self, analyzer):
        """Test handling of empty content."""
        html = "<html><body></body></html>"
        
        result = await analyzer.check_thin_content(html)
        
        assert result["is_thin"] is True
        assert result["word_count"] == 0

    @pytest.mark.asyncio
    async def test_special_characters_word_count(self, analyzer):
        """Test word count with special characters."""
        html = """
            <html>
                <body>
                    <p>Test!@#$%^ content&*() with special!!!### characters......</p>
                </body>
            </html>
        """
        
        result = await analyzer.check_thin_content(html)
        
        assert result["word_count"] >= 0

    @pytest.mark.asyncio
    async def test_multilingual_content(self, analyzer):
        """Test handling of multilingual content."""
        html = """
            <html>
                <body>
                    <p>English content mixed with 中文 and Español words.</p>
                </body>
            </html>
        """
        
        result = await analyzer.check_thin_content(html)
        
        assert result["word_count"] > 0

    @pytest.mark.asyncio
    async def test_readability_simple_text(self, analyzer):
        """Test readability score for simple text."""
        simple_html = """
            <html>
                <body>
                    <p>I like cats. I like dogs. Cats are fun. Dogs are fun.</p>
                </body>
            </html>
        """
        
        score = await analyzer.calculate_readability_score(simple_html)
        
        assert score > 60  # Simple text should have high readability

    @pytest.mark.asyncio
    async def test_readability_complex_text(self, analyzer):
        """Test readability score for complex text."""
        complex_html = """
            <html>
                <body>
                    <p>The implementation of comprehensive, multifaceted methodological approaches 
                    facilitates the optimization of organizational synergistic capabilities through 
                    sophisticated technological infrastructure integration.</p>
                </body>
            </html>
        """
        
        score = await analyzer.calculate_readability_score(complex_html)
        
        assert score < 60  # Complex text should have lower readability

    @pytest.mark.asyncio
    async def test_duplicate_title_detection(self, analyzer):
        """Test detection of duplicate title meta tags."""
        html = """
            <html>
                <head>
                    <title>Page Title</title>
                </head>
                <body><p>Unique content here with many words to make it substantial.</p></body>
            </html>
        """
        
        result = await analyzer.check_duplicate_content(html)
        
        assert "duplicate_title" in result

    @pytest.mark.asyncio
    async def test_quote_density_detection(self, analyzer):
        """Test detection of high quote density."""
        quote_heavy = """
            <html>
                <body>
                    <p>"Quote one from source." "Quote two from source." "Quote three from source."
                    "Quote four from source."</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_plagiarism_risk(quote_heavy)
        
        # High quote density should indicate plagiarism risk

    @pytest.mark.asyncio
    async def test_citation_pattern_analysis(self, analyzer):
        """Test analysis of citation patterns."""
        cited_content = """
            <html>
                <body>
                    <p>According to Smith (2020), "This is important." 
                    As Johnson et al. note, "This is also important."</p>
                </body>
            </html>
        """
        
        result = await analyzer.analyze_plagiarism_risk(cited_content)
        
        assert "risk_level" in result

    @pytest.mark.asyncio
    async def test_comprehensive_quality_report(self, analyzer, sample_html):
        """Test comprehensive quality analysis report."""
        result = await analyzer.analyze_full_content_quality(sample_html)
        
        assert result is not None
        assert "duplicate_check" in result or "thin_content" in result
        assert "quality_score" in result or "issues" in result
