"""Unit tests for app.services.seo.local_seo."""
from __future__ import annotations

import pytest

from app.services.seo.local_seo import (
    CanonicalNAP,
    DIRECTORIES,
    _normalize_phone,
    _normalize_address,
    _normalize_name,
    check_consistency,
    aggregate_consistency,
    generate_grid_points,
    grid_visibility_score,
)


class TestNormalizers:
    def test_normalize_phone_strips_non_digits(self):
        assert _normalize_phone("+1 (555) 123-4567") == "15551234567"

    def test_normalize_address_strips_suffixes(self):
        assert _normalize_address("123 Main Street") == _normalize_address("123 main st")

    def test_normalize_name_strips_company_suffix(self):
        assert _normalize_name("Acme Corp Inc.") == _normalize_name("acme corp")


class TestCheckConsistency:
    def _canon(self) -> CanonicalNAP:
        return CanonicalNAP(
            name="Acme Corp",
            address="123 Main Street",
            phone="555-123-4567",
            website="https://acme.com",
        )

    def test_perfect_match_returns_100(self):
        canon = self._canon()
        score, issues = check_consistency({
            "business_name": "Acme Corp",
            "address": "123 Main St",
            "phone": "(555) 123-4567",
            "website": "https://www.acme.com",
        }, canon)
        assert score == 100
        assert issues == []

    def test_name_mismatch_drops_score(self):
        canon = self._canon()
        score, issues = check_consistency({
            "business_name": "Acme Inc Different",
            "address": "123 Main St",
            "phone": "555-123-4567",
            "website": "https://acme.com",
        }, canon)
        assert score < 100
        assert any("name" in i.lower() for i in issues)

    def test_phone_mismatch_drops_score(self):
        canon = self._canon()
        score, issues = check_consistency({
            "business_name": "Acme Corp",
            "address": "123 Main St",
            "phone": "555-999-9999",
            "website": "https://acme.com",
        }, canon)
        assert score < 100
        assert any("phone" in i.lower() for i in issues)


class TestAggregateConsistency:
    def test_empty_returns_zero(self):
        out = aggregate_consistency([])
        assert out["score"] == 0
        assert out["directories_listed"] == 0
        assert out["directories_total"] == len(DIRECTORIES)

    def test_aggregates_score_listed_and_missing(self):
        rows = [
            {"directory": "Yelp", "consistency_score": 100, "issues": []},
            {"directory": "Google Business Profile", "consistency_score": 75, "issues": ["Phone differs"]},
        ]
        out = aggregate_consistency(rows)
        assert out["score"] == 88  # avg(100, 75) = 87.5 rounded
        assert out["directories_listed"] == 2
        assert out["issues_count"] == 1
        # Yelp + GBP are listed, others should be in missing
        assert "Yelp" not in out["directories_missing"]


class TestGrid:
    def test_grid_points_count(self):
        pts = generate_grid_points(40.7, -74.0, radius_km=5, grid_size=5)
        assert len(pts) == 25
        # Center cell should be the original point (or very close)
        center = pts[12]  # 5x5 grid index 12 == (2,2)
        assert abs(center[0] - 40.7) < 0.001
        assert abs(center[1] - (-74.0)) < 0.001

    def test_visibility_score_with_no_cells(self):
        out = grid_visibility_score([])
        assert out["avg_rank"] is None
        assert out["top3_pct"] == 0
        assert out["not_ranked_pct"] == 100

    def test_visibility_score_buckets(self):
        cells = [
            {"rank": 1}, {"rank": 2}, {"rank": 3},
            {"rank": 5}, {"rank": 8},
            {"rank": None}, {"rank": None},
        ]
        out = grid_visibility_score(cells)
        # 3 of 7 cells in top 3 ≈ 42.9%
        assert out["top3_pct"] == pytest.approx(42.9, rel=0.05)
        # 5 of 7 in top 10 ≈ 71.4%
        assert out["top10_pct"] == pytest.approx(71.4, rel=0.05)
        # 2 of 7 not ranked ≈ 28.6%
        assert out["not_ranked_pct"] == pytest.approx(28.6, rel=0.05)
