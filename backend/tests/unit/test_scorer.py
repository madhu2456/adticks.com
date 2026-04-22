"""Unit tests for compute_visibility_score in app.services.ai.scorer."""
import pytest
from app.services.ai.scorer import compute_visibility_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prompt_result(category="brand_awareness", mentioned=False, confidence=0.7):
    """Build a minimal prompt_result dict."""
    mention = (
        [
            {
                "brand": "Optivio",
                "is_target_brand": True,
                "confidence": confidence,
                "position": "first",
            }
        ]
        if mentioned
        else []
    )
    return {
        "prompt": {"id": "p1", "text": "Who is the best SEO tool?", "category": category},
        "mentions": mention,
        "all_mentions": mention,
    }


# ---------------------------------------------------------------------------
# Zero mentions
# ---------------------------------------------------------------------------

def test_zero_mentions_visibility_score_is_zero():
    """No brand mentions across all prompts produces visibility_score == 0.0."""
    results = [_make_prompt_result(mentioned=False) for _ in range(5)]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert score["visibility_score"] == 0.0


def test_empty_prompt_results_returns_zero_scores():
    """Empty prompt list returns all zeros without crashing."""
    score = compute_visibility_score("proj-1", [], "Optivio")
    assert score["visibility_score"] == 0.0
    assert score["impact_score"] == 0.0
    assert score["sov_score"] == 0.0


# ---------------------------------------------------------------------------
# Some mentions
# ---------------------------------------------------------------------------

def test_some_mentions_visibility_score_greater_than_zero():
    """Having at least one mentioned prompt produces visibility_score > 0."""
    results = [
        _make_prompt_result(mentioned=True),
        _make_prompt_result(mentioned=False),
    ]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert score["visibility_score"] > 0.0


def test_all_mentioned_visibility_score_is_one():
    """All prompts mentioned gives visibility_score of 1.0."""
    results = [_make_prompt_result(mentioned=True) for _ in range(4)]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert score["visibility_score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Required keys
# ---------------------------------------------------------------------------

def test_returns_dict_with_required_keys():
    """Score dict contains visibility_score, sov_score, and impact_score."""
    score = compute_visibility_score("proj-1", [], "Optivio")
    assert "visibility_score" in score
    assert "sov_score" in score
    assert "impact_score" in score


def test_returns_full_schema():
    """Score dict has all expected top-level fields."""
    results = [_make_prompt_result(mentioned=True)]
    score = compute_visibility_score("proj-1", results, "Optivio")
    expected_keys = [
        "project_id",
        "visibility_score",
        "impact_score",
        "sov_score",
        "mention_rate",
        "prompts_analyzed",
        "prompts_with_mention",
        "total_target_mentions",
        "industry_benchmark",
        "benchmark_status",
        "timestamp",
    ]
    for key in expected_keys:
        assert key in score, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Value ranges
# ---------------------------------------------------------------------------

def test_visibility_score_between_0_and_1():
    """visibility_score is clamped to [0.0, 1.0]."""
    results = [_make_prompt_result(mentioned=True) for _ in range(3)]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert 0.0 <= score["visibility_score"] <= 1.0


def test_sov_score_between_0_and_1():
    """sov_score is within [0.0, 1.0]."""
    results = [_make_prompt_result(mentioned=True)]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert 0.0 <= score["sov_score"] <= 1.0


def test_impact_score_non_negative():
    """impact_score is non-negative."""
    results = [_make_prompt_result(mentioned=True, category="transactional")]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert score["impact_score"] >= 0.0


# ---------------------------------------------------------------------------
# Benchmark comparison
# ---------------------------------------------------------------------------

def test_benchmark_status_below_when_low_visibility():
    """Low visibility triggers benchmark_status == 'below'."""
    results = [_make_prompt_result(mentioned=False) for _ in range(10)]
    score = compute_visibility_score("proj-1", results, "Optivio", industry="Technology")
    assert score["benchmark_status"] == "below"


def test_benchmark_status_above_when_high_visibility():
    """100% visibility triggers benchmark_status == 'above'."""
    results = [_make_prompt_result(mentioned=True) for _ in range(10)]
    score = compute_visibility_score("proj-1", results, "Optivio", industry="Technology")
    assert score["benchmark_status"] == "above"


# ---------------------------------------------------------------------------
# Intent weighting
# ---------------------------------------------------------------------------

def test_transactional_category_contributes_higher_impact():
    """Transactional prompts carry higher intent weight than informational."""
    transactional = [_make_prompt_result(category="transactional", mentioned=True)]
    informational = [_make_prompt_result(category="informational", mentioned=True)]
    score_t = compute_visibility_score("proj-1", transactional, "Optivio")
    score_i = compute_visibility_score("proj-1", informational, "Optivio")
    # Both have equal visibility (1.0), but transactional has higher raw impact weight
    assert score_t["impact_score"] >= score_i["impact_score"]


# ---------------------------------------------------------------------------
# Category breakdown
# ---------------------------------------------------------------------------

def test_category_breakdown_present():
    """Score dict contains category_breakdown when prompts have categories."""
    results = [
        _make_prompt_result(category="comparison", mentioned=True),
        _make_prompt_result(category="brand_awareness", mentioned=False),
    ]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert "category_breakdown" in score
    assert "comparison" in score["category_breakdown"]


def test_mention_rate_is_percentage():
    """mention_rate == visibility_score * 100."""
    results = [
        _make_prompt_result(mentioned=True),
        _make_prompt_result(mentioned=False),
    ]
    score = compute_visibility_score("proj-1", results, "Optivio")
    assert score["mention_rate"] == pytest.approx(score["visibility_score"] * 100)


# ---------------------------------------------------------------------------
# Scan count
# ---------------------------------------------------------------------------

def test_scan_count_included_in_score():
    """scan_count parameter is passed through to the score dict."""
    score = compute_visibility_score("proj-1", [], "Optivio", scan_count=25)
    assert score["scan_count"] == 25


def test_scans_remaining_computed_correctly():
    """scans_remaining == max_free_scans - scan_count."""
    score = compute_visibility_score(
        "proj-1", [], "Optivio", scan_count=30, max_free_scans=50
    )
    assert score["scans_remaining"] == 20
