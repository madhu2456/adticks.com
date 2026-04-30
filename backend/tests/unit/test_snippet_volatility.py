"""Unit tests for app.services.seo.snippet_volatility."""
from __future__ import annotations

import pytest

from app.services.seo.snippet_volatility import (
    detect_featured_snippet,
    extract_paa_questions,
    detect_volatility_events,
    is_valid_prospect_status,
    progress_status,
    campaign_summary,
    PROSPECT_STATUS_FLOW,
)


class TestFeaturedSnippet:
    def test_no_snippet_when_feature_absent(self):
        out = detect_featured_snippet({"features_present": [], "results": []}, "example.com")
        assert out["has_snippet"] is False
        assert out["we_own"] is False

    def test_we_own_when_top_url_matches_domain(self):
        serp = {
            "features_present": ["featured_snippet"],
            "results": [{"url": "https://www.example.com/post", "snippet": "x"}],
        }
        out = detect_featured_snippet(serp, "example.com")
        assert out["has_snippet"] is True
        assert out["we_own"] is True
        assert out["current_owner_url"] == "https://www.example.com/post"

    def test_competitor_owns(self):
        serp = {
            "features_present": ["featured_snippet"],
            "results": [{"url": "https://other.com/post", "snippet": "x"}],
        }
        out = detect_featured_snippet(serp, "example.com")
        assert out["has_snippet"] is True
        assert out["we_own"] is False


class TestExtractPAA:
    def test_returns_empty_when_no_paa(self):
        out = extract_paa_questions({"features_present": []}, "seo")
        assert out == []

    def test_extracts_string_questions(self):
        out = extract_paa_questions(
            {"features_present": ["people_also_ask"], "paa_questions": ["What is SEO?", "Why does it matter?"]},
            "seo",
        )
        assert len(out) == 2
        assert out[0]["question"] == "What is SEO?"
        assert out[0]["seed_keyword"] == "seo"

    def test_extracts_dict_questions(self):
        out = extract_paa_questions(
            {"features_present": ["people_also_ask"],
             "paa_questions": [{"question": "What is SEO?", "link": "https://x.com", "snippet": "..."}]},
            "seo",
        )
        assert out[0]["answer_url"] == "https://x.com"
        assert out[0]["answer_snippet"] == "..."


class TestVolatility:
    def test_no_events_for_small_changes(self):
        diffs = [{"keyword": "kw", "previous_position": 5, "current_position": 6}]
        events = detect_volatility_events(diffs, drop_threshold=5, rise_threshold=5)
        assert events == []

    def test_significant_drop_flagged(self):
        diffs = [{"keyword": "kw", "previous_position": 3, "current_position": 12}]
        events = detect_volatility_events(diffs)
        assert len(events) == 1
        assert events[0]["direction"] == "down"
        assert events[0]["delta"] == 9

    def test_significant_rise_flagged(self):
        diffs = [{"keyword": "kw", "previous_position": 15, "current_position": 5}]
        events = detect_volatility_events(diffs)
        assert len(events) == 1
        assert events[0]["direction"] == "up"
        assert events[0]["delta"] == -10

    def test_entered_top_results(self):
        diffs = [{"keyword": "kw", "previous_position": None, "current_position": 8}]
        events = detect_volatility_events(diffs)
        assert len(events) == 1
        assert events[0]["direction"] == "up"

    def test_dropped_out_of_top(self):
        diffs = [{"keyword": "kw", "previous_position": 5, "current_position": None}]
        events = detect_volatility_events(diffs)
        assert len(events) == 1
        assert events[0]["direction"] == "down"

    def test_buried_movements_ignored(self):
        diffs = [{"keyword": "kw", "previous_position": 75, "current_position": 90}]
        events = detect_volatility_events(diffs)
        assert events == []

    def test_results_sorted_by_magnitude(self):
        diffs = [
            {"keyword": "small", "previous_position": 5, "current_position": 11},
            {"keyword": "big", "previous_position": 3, "current_position": 18},
        ]
        events = detect_volatility_events(diffs)
        assert events[0]["keyword"] == "big"


class TestOutreachHelpers:
    def test_status_validation(self):
        for s in PROSPECT_STATUS_FLOW:
            assert is_valid_prospect_status(s) is True
        assert is_valid_prospect_status("invalid") is False

    def test_progress_status(self):
        assert progress_status("new") == "contacted"
        assert progress_status("contacted") == "replied"
        # 'lost' is the last in the flow, returns None
        assert progress_status("lost") is None
        assert progress_status("invalid-input") is None

    def test_campaign_summary_empty(self):
        out = campaign_summary([])
        assert out["total_prospects"] == 0
        assert out["reply_rate"] == 0
        assert out["win_rate"] == 0

    def test_campaign_summary_aggregates(self):
        prospects = [
            {"status": "new"},
            {"status": "contacted"},
            {"status": "contacted"},
            {"status": "replied"},
            {"status": "won"},
            {"status": "lost"},
        ]
        out = campaign_summary(prospects)
        assert out["total_prospects"] == 6
        # contacted = 2 + 1 (replied) + 1 (won) + 1 (lost) = 5
        assert out["contacted"] == 5
        # replies = 1 + 1 + 1 = 3 of 5 = 0.6
        assert out["reply_rate"] == 0.6
        # wins = 1 of 5 = 0.2
        assert out["win_rate"] == 0.2
        assert out["by_status"]["won"] == 1
