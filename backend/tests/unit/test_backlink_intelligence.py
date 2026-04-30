"""Unit tests for app.services.seo.backlink_intelligence."""
from __future__ import annotations

import pytest

from app.services.seo.backlink_intelligence import (
    classify_anchor,
    aggregate_anchor_distribution,
    assess_toxicity,
    filter_toxic,
    link_intersect,
    diff_backlink_sets,
)


class TestAnchorClassification:
    def test_branded(self):
        assert classify_anchor("Adticks Inc", ["adticks"], ["seo tools"]) == "branded"

    def test_exact(self):
        assert classify_anchor("seo tools", ["adticks"], ["seo tools"]) == "exact"

    def test_partial(self):
        assert classify_anchor("the best seo tools out there", ["adticks"], ["seo tools"]) == "partial"

    def test_generic(self):
        assert classify_anchor("click here", ["adticks"], ["seo tools"]) == "generic"

    def test_naked_url(self):
        assert classify_anchor("https://example.com", ["adticks"], ["seo tools"]) == "naked_url"

    def test_image_when_empty(self):
        assert classify_anchor("", ["adticks"], ["seo tools"]) == "image"


class TestDistribution:
    def test_aggregates_counts_and_domains(self):
        rows = [
            {"referring_domain": "a.com", "anchor_text": "click here"},
            {"referring_domain": "b.com", "anchor_text": "click here"},
            {"referring_domain": "a.com", "anchor_text": "Adticks"},
            {"referring_domain": "c.com", "anchor_text": ""},
        ]
        out = aggregate_anchor_distribution(rows, ["adticks"], ["seo"])
        # 3 distinct (anchor, classification) pairs
        anchors = {r["anchor"]: r for r in out}
        assert "click here" in anchors
        assert anchors["click here"]["count"] == 2
        assert anchors["click here"]["referring_domains"] == 2
        assert anchors["Adticks"]["classification"] == "branded"
        assert any(r["classification"] == "image" for r in out)


class TestToxicity:
    def test_spammy_tld_bumps_score(self):
        score, reasons = assess_toxicity("cheap-loans.xyz", "click", None)
        assert score > 0
        assert any("TLD" in r for r in reasons)

    def test_excessive_hyphens(self):
        score, reasons = assess_toxicity("a-b-c-d-e.com", None, None)
        assert any("hyphens" in r.lower() for r in reasons)

    def test_spam_keyword_in_anchor(self):
        score, _ = assess_toxicity("legit-site.com", "casino bonus", None)
        assert score >= 30

    def test_low_authority_penalty(self):
        score, reasons = assess_toxicity("very-long-obscure-domain-name-with-low-authority.io", None, None)
        assert any("authority" in r for r in reasons)

    def test_clean_domain_low_score(self):
        score, _ = assess_toxicity("wikipedia.org", "wiki", None)
        assert score < 40

    def test_filter_toxic_threshold(self):
        rows = [
            {"referring_domain": "wikipedia.org", "anchor_text": "wiki", "target_url": None},
            {"referring_domain": "spam-loans.xyz", "anchor_text": "loan", "target_url": None},
        ]
        toxic = filter_toxic(rows, min_score=40)
        # only the spammy one should appear
        assert len(toxic) == 1
        assert toxic[0]["referring_domain"] == "spam-loans.xyz"
        assert toxic[0]["spam_score"] > 0
        assert toxic[0]["disavowed"] is False


class TestLinkIntersect:
    def test_basic_intersection(self):
        project = {"already-linking.com"}
        competitors = {
            "comp1.com": {"opportunity.com", "already-linking.com"},
            "comp2.com": {"opportunity.com", "another.com"},
        }
        out = link_intersect(project, competitors, min_competitors=2)
        domains = [r["referring_domain"] for r in out]
        assert "opportunity.com" in domains
        # excluded because we already have it
        assert "already-linking.com" not in domains
        # excluded because only one competitor links
        assert "another.com" not in domains

    def test_sorts_by_competitor_count_desc(self):
        project: set[str] = set()
        competitors = {
            "a.com": {"x.com"},
            "b.com": {"x.com", "y.com"},
            "c.com": {"y.com"},
        }
        out = link_intersect(project, competitors, min_competitors=1)
        assert out[0]["competitor_count"] >= out[-1]["competitor_count"]


class TestDiffBacklinks:
    def test_diff_returns_new_and_lost(self):
        new, lost = diff_backlink_sets({"a", "b"}, {"b", "c"})
        assert new == ["c"]
        assert lost == ["a"]
