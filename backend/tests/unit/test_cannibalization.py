"""Unit tests for app.services.seo.cannibalization."""
from __future__ import annotations

import pytest

from app.services.seo.cannibalization import detect_cannibalization, _severity, _recommend


class TestSeverity:
    def test_high_severity_when_3_pages_in_top_20(self):
        assert _severity(3, 5) == "high"

    def test_medium_severity_for_2_pages(self):
        assert _severity(2, 25) == "medium"

    def test_low_severity_when_buried(self):
        assert _severity(2, 50) == "low"


class TestDetect:
    def test_no_cannibalization_when_only_one_url_per_keyword(self):
        rows = [
            {"keyword": "seo", "url": "/a", "position": 5},
            {"keyword": "ppc", "url": "/b", "position": 7},
        ]
        out = detect_cannibalization(rows)
        assert out == []

    def test_basic_cannibalization_two_pages(self):
        rows = [
            {"keyword": "seo", "url": "/a", "position": 5, "clicks": 100, "impressions": 5000},
            {"keyword": "seo", "url": "/b", "position": 8, "clicks": 30, "impressions": 1500},
        ]
        out = detect_cannibalization(rows)
        assert len(out) == 1
        assert out[0]["keyword"] == "seo"
        assert len(out[0]["urls"]) == 2
        # Sorted best position first
        assert out[0]["urls"][0]["position"] == 5
        assert out[0]["severity"] in ("medium", "high")
        assert "consolidate" in out[0]["recommendation"].lower() or "redirect" in out[0]["recommendation"].lower()

    def test_dedupes_same_url_keeping_best_position(self):
        rows = [
            {"keyword": "seo", "url": "/a", "position": 8},
            {"keyword": "seo", "url": "/a", "position": 5},  # better, keep this
            {"keyword": "seo", "url": "/b", "position": 12},
        ]
        out = detect_cannibalization(rows)
        urls = out[0]["urls"]
        a_row = next(u for u in urls if u["url"] == "/a")
        assert a_row["position"] == 5

    def test_min_pages_threshold(self):
        rows = [
            {"keyword": "seo", "url": "/a", "position": 5},
            {"keyword": "seo", "url": "/b", "position": 10},
        ]
        out = detect_cannibalization(rows, min_pages=3)
        assert out == []

    def test_handles_missing_keyword_or_url(self):
        rows = [
            {"keyword": "", "url": "/a", "position": 1},
            {"url": "/b", "position": 2},
            {"keyword": "seo"},
        ]
        out = detect_cannibalization(rows)
        assert out == []

    def test_recommendation_for_three_or_more_pages(self):
        rows = [
            {"keyword": "kw", "url": "/a", "position": 3},
            {"keyword": "kw", "url": "/b", "position": 7},
            {"keyword": "kw", "url": "/c", "position": 12},
        ]
        out = detect_cannibalization(rows)
        assert "3 pages" in out[0]["recommendation"] or "competing" in out[0]["recommendation"].lower()

    def test_results_sorted_by_severity(self):
        rows = [
            # Low severity (buried)
            {"keyword": "low", "url": "/a", "position": 60},
            {"keyword": "low", "url": "/b", "position": 80},
            # High severity (top 20, 3 pages)
            {"keyword": "high", "url": "/x", "position": 3},
            {"keyword": "high", "url": "/y", "position": 8},
            {"keyword": "high", "url": "/z", "position": 15},
        ]
        out = detect_cannibalization(rows)
        # high comes first because of severity sort
        assert out[0]["keyword"] == "high"
        assert out[1]["keyword"] == "low"
