"""Unit tests for app.services.seo.serp_analyzer."""
from __future__ import annotations

import httpx
import pytest

from app.services.seo.serp_analyzer import (
    _domain,
    _da_estimate,
    _features_from_serpapi,
    analyze_serp,
)


class TestDomainExtraction:
    def test_simple_https(self):
        assert _domain("https://example.com/foo") == "example.com"

    def test_strips_www(self):
        assert _domain("https://www.example.com") == "example.com"

    def test_returns_empty_on_garbage(self):
        assert _domain("not a url") == ""


class TestDAEstimate:
    def test_known_authority_lookup(self):
        assert _da_estimate("wikipedia.org") == 95.0
        assert _da_estimate("youtube.com") == 100.0

    def test_unknown_uses_tld_weight(self):
        assert _da_estimate("randomdomain.com") > 0
        # gov gets a high weight
        assert _da_estimate("agency.gov") >= 80

    def test_empty_returns_zero(self):
        assert _da_estimate("") == 0.0


class TestFeaturesFromSerpAPI:
    def test_detects_featured_snippet(self):
        feats = _features_from_serpapi({"answer_box": {"answer": "x"}})
        assert "featured_snippet" in feats

    def test_detects_paa(self):
        feats = _features_from_serpapi({"related_questions": [{}]})
        assert "people_also_ask" in feats

    def test_detects_knowledge_panel(self):
        feats = _features_from_serpapi({"knowledge_graph": {}})
        assert "knowledge_panel" in feats

    def test_detects_local_pack(self):
        feats = _features_from_serpapi({"local_results": [{}]})
        assert "local_pack" in feats

    def test_empty_payload_returns_empty(self):
        assert _features_from_serpapi({}) == []


@pytest.mark.asyncio
async def test_analyze_serp_uses_ddg_fallback(monkeypatch):
    """When no SerpAPI key is set, analyzer should use DuckDuckGo HTML."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    sample_html = """
    <html><body>
      <div class="result">
        <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Ffoo">First Result</a>
        <a class="result__snippet">First snippet.</a>
      </div>
      <div class="result">
        <a class="result__a" href="/l/?uddg=https%3A%2F%2Fwikipedia.org%2Fwiki%2FX">Wiki</a>
        <a class="result__snippet">Wiki snippet.</a>
      </div>
    </body></html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=sample_html, request=request)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    out = await analyze_serp("seo tools", location="us", device="desktop")
    assert out["keyword_text"] == "seo tools"
    assert out["location"] == "us"
    assert out["device"] == "desktop"
    assert isinstance(out["results"], list)
    assert len(out["results"]) >= 1
    assert out["results"][0]["url"].startswith("https://")
    # DA estimate populated
    for r in out["results"]:
        assert "domain_authority" in r
