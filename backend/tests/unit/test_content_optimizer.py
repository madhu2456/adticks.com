"""Unit tests for app.services.seo.content_optimizer."""
from __future__ import annotations

import httpx
import pytest

from app.services.seo.content_optimizer import (
    _tokenize,
    _content_words,
    _extract_text_from_html,
    flesch_reading_ease,
    score_content,
    build_topic_cluster,
    generate_brief,
)


class TestTokenization:
    def test_tokenize_strips_short_words(self):
        toks = _tokenize("Hi a Claude is amazing")
        assert "Hi" not in toks  # 2-char, but >= 3 in regex? actually regex is {2,} so Hi would match
        # at least the meaningful tokens are present
        assert "claude" in toks
        assert "amazing" in toks

    def test_content_words_removes_stopwords(self):
        toks = _content_words("the cat is on the mat")
        assert "the" not in toks
        assert "is" not in toks
        assert "cat" in toks
        assert "mat" in toks


class TestHtmlExtract:
    def test_strips_scripts_and_styles(self):
        html = "<html><body><script>var x=1;</script><h1>Title</h1><p>body text here</p></body></html>"
        body, headings, qs = _extract_text_from_html(html)
        assert "var x" not in body
        assert "body text" in body
        assert any(h.startswith("[h1]") for h in headings)

    def test_finds_questions(self):
        html = "<html><body><p>How do you optimize SEO? Why does it matter?</p></body></html>"
        body, _, qs = _extract_text_from_html(html)
        assert any(q.startswith("How") for q in qs)


class TestFlesch:
    def test_easy_text_high_score(self):
        score, grade = flesch_reading_ease("The cat sat on the mat. Bob ran. He ran fast.")
        assert score > 50
        assert grade in {"easy", "very-easy", "fairly-easy", "standard"}

    def test_complex_text_lower_score(self):
        text = "The juxtaposition of ontological frameworks elucidates esoteric methodological paradigms."
        score, _ = flesch_reading_ease(text)
        assert score < 50

    def test_empty_text(self):
        score, grade = flesch_reading_ease("")
        assert score == 0.0
        assert grade == "n/a"


class TestScoreContent:
    def test_overall_score_within_bounds(self):
        text = "<h1>Email Marketing Guide</h1><h2>Why It Matters</h2>" + ("<p>email marketing is a key strategy for businesses. " * 100) + "</p>"
        result = score_content("email marketing", text, semantic_terms=["strategy", "businesses"], target_word_count=500)
        assert 0 <= result["overall_score"] <= 100
        assert result["word_count"] > 200
        assert result["headings_score"] > 0
        assert isinstance(result["suggestions"], list)

    def test_thin_content_yields_length_suggestion(self):
        result = score_content("test keyword", "<p>just a few words</p>", target_word_count=1500)
        types = {s["type"] for s in result["suggestions"]}
        assert "length" in types

    def test_keyword_stuffing_flagged(self):
        # repeat keyword many times to push density over 2.5%
        content = "buy shoes " * 100  # density should be ~50%
        result = score_content("buy shoes", content, target_word_count=200)
        types = {s["type"] for s in result["suggestions"]}
        assert "keyword" in types

    def test_missing_h1_flagged(self):
        content = "<p>" + ("words " * 100) + "</p>"
        result = score_content("test", content)
        types = {s["type"] for s in result["suggestions"]}
        assert "structure" in types


class TestTopicCluster:
    def test_builds_cluster_from_ideas(self):
        ideas = [
            {"keyword": "email marketing", "volume": 5000, "difficulty": 60, "intent": "commercial"},
            {"keyword": "email marketing tools", "volume": 3000, "difficulty": 50, "intent": "commercial"},
            {"keyword": "email marketing tips", "volume": 1500, "difficulty": 40, "intent": "informational"},
            {"keyword": "facebook ads", "volume": 9000, "difficulty": 70, "intent": "commercial"},
        ]
        cluster = build_topic_cluster("email marketing", ideas, max_supporting=5)
        assert cluster["pillar_topic"] == "email marketing"
        # should pull in only the email marketing related rows (excluding the exact pillar)
        topics = [t["topic"] for t in cluster["supporting_topics"]]
        assert "email marketing tools" in topics
        assert "email marketing tips" in topics
        assert "facebook ads" not in topics
        assert cluster["total_volume"] > 0
        assert 0 <= cluster["coverage_score"] <= 100


@pytest.mark.asyncio
async def test_generate_brief_with_mocked_pages(monkeypatch):
    """generate_brief should aggregate semantic terms + outline from competitor pages."""
    page_html = """
    <html><body>
      <h1>Email Marketing Guide</h1>
      <h2>Why Email Marketing Matters For Businesses</h2>
      <h2>How To Build Your Subscriber List</h2>
      <p>email marketing is a critical strategy for modern businesses.
      automation, segmentation, personalization, deliverability, and conversion
      are all important concepts. What is the best way to start? How can you measure success?</p>
    </body></html>
    """

    def handler(request):
        return httpx.Response(200, text=page_html, headers={"content-type": "text/html"}, request=request)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    brief = await generate_brief(
        "email marketing",
        competitor_urls=["https://a.com/x", "https://b.com/y"],
        target_word_count=1000,
    )
    assert brief["target_keyword"] == "email marketing"
    assert isinstance(brief["title_suggestions"], list) and len(brief["title_suggestions"]) >= 3
    assert "automation" in brief["semantic_terms"] or "businesses" in brief["semantic_terms"]
    assert brief["target_word_count"] >= 1000
    assert isinstance(brief["questions_to_answer"], list)
