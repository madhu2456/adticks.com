"""Unit tests for app.services.seo.core_web_vitals."""
from __future__ import annotations

import httpx
import pytest

from app.services.seo.core_web_vitals import (
    run_pagespeed,
    run_both_strategies,
    _score_to_int,
    _empty_result,
)


class TestHelpers:
    def test_score_conversion(self):
        assert _score_to_int(0.92) == 92
        assert _score_to_int(0) == 0
        assert _score_to_int(None) is None

    def test_empty_result_shape(self):
        out = _empty_result("https://x.com", "mobile")
        for key in ("lcp_ms", "inp_ms", "cls", "performance_score", "opportunities"):
            assert key in out
        assert out["url"] == "https://x.com"


@pytest.mark.asyncio
async def test_run_pagespeed_with_mocked_response(monkeypatch):
    """Mock the PSI endpoint and verify normalization."""
    payload = {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.85},
                "seo": {"score": 0.92},
                "accessibility": {"score": 0.78},
                "best-practices": {"score": 0.95},
            },
            "audits": {
                "largest-contentful-paint": {"numericValue": 2400},
                "cumulative-layout-shift": {"numericValue": 0.05},
                "first-contentful-paint": {"numericValue": 1700},
                "server-response-time": {"numericValue": 250},
                "speed-index": {"numericValue": 3000},
                "total-blocking-time": {"numericValue": 150},
                "uses-optimized-images": {
                    "title": "Optimize images",
                    "description": "Compress images",
                    "details": {"type": "opportunity", "overallSavingsMs": 800},
                    "score": 0.4,
                },
            },
        },
        "loadingExperience": {
            "metrics": {
                "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2200},
                "INTERACTION_TO_NEXT_PAINT": {"percentile": 180},
                "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 8},
            },
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    result = await run_pagespeed("https://example.com", strategy="mobile")
    assert result["url"] == "https://example.com"
    # field LCP wins over lab LCP (2200 vs 2400)
    assert result["lcp_ms"] == 2200
    assert result["inp_ms"] == 180
    # field CLS = percentile / 100 = 0.08
    assert abs(result["cls"] - 0.08) < 0.001
    assert result["performance_score"] == 85
    assert result["seo_score"] == 92
    # one opportunity, ranked by savings
    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["savings_ms"] == 800


@pytest.mark.asyncio
async def test_run_pagespeed_handles_failure(monkeypatch):
    """A non-200 response should return an empty result, not raise."""
    def handler(request):
        return httpx.Response(429, request=request)
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    result = await run_pagespeed("https://example.com")
    assert result["lcp_ms"] is None
    assert result["performance_score"] is None
    assert result["opportunities"] == []
