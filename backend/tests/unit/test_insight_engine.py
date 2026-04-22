"""Unit tests for InsightEngine."""
import pytest
from app.services.insights.insight_engine import InsightEngine


@pytest.fixture
def engine():
    """Provide a default InsightEngine for Optivio / SaaS."""
    return InsightEngine(brand_name="Optivio", industry="SaaS")


def test_returns_list(engine):
    """generate_insights always returns a list."""
    result = engine.generate_insights(
        "test-id",
        {},
        {"visibility_pct": 10, "brand_name": "Optivio", "prompt_count": 50},
        {"queries": []},
        {"daily_data": [], "summary": {}},
    )
    assert isinstance(result, list)


def test_no_crash_on_empty_data(engine):
    """generate_insights must not raise on fully empty data."""
    result = engine.generate_insights(
        "test-id",
        {},
        {},
        {"queries": []},
        {"daily_data": [], "summary": {}},
    )
    assert isinstance(result, list)


def test_no_crash_on_none_args(engine):
    """generate_insights accepts None for all optional args."""
    result = engine.generate_insights("test-id")
    assert isinstance(result, list)


def test_high_impressions_low_ctr_fires(engine):
    """Rule 1 fires when impressions >= 1000, CTR < 2%, position <= 20."""
    gsc_data = {
        "queries": [
            {
                "query": "best seo tool",
                "impressions": 5000,
                "ctr": 0.01,
                "ctr_pct": 1.0,
                "clicks": 50,
                "position": 8,
            }
        ]
    }
    insights = engine.generate_insights(
        "test-id",
        {},
        {"visibility_pct": 30, "brand_name": "Optivio", "prompt_count": 100},
        gsc_data,
        {"daily_data": [], "summary": {}},
    )
    texts = " ".join(i["text"] for i in insights).lower()
    assert any(word in texts for word in ["ctr", "impression", "meta", "click"])


def test_high_impressions_low_ctr_does_not_fire_below_threshold(engine):
    """Rule 1 does not fire when impressions < 1000."""
    gsc_data = {
        "queries": [
            {
                "query": "rare query",
                "impressions": 50,
                "ctr": 0.01,
                "ctr_pct": 1.0,
                "clicks": 1,
                "position": 5,
            }
        ]
    }
    insights = engine.generate_insights("test-id", {}, {}, gsc_data, {})
    insight_types = [i.get("insight_type") for i in insights]
    assert "high_impressions_low_ctr" not in insight_types


def test_insight_structure(engine):
    """Every insight dict contains required keys with correct types."""
    insights = engine.generate_insights(
        "test-id",
        {},
        {"visibility_pct": 5, "brand_name": "Optivio", "prompt_count": 100},
        {
            "queries": [
                {
                    "query": "q",
                    "impressions": 2000,
                    "ctr": 0.005,
                    "ctr_pct": 0.5,
                    "clicks": 10,
                    "position": 5,
                }
            ]
        },
        {"daily_data": [], "summary": {}},
    )
    for i in insights:
        assert "id" in i
        assert "text" in i
        assert "category" in i
        assert "priority" in i
        assert isinstance(i["priority"], int)
        assert 1 <= i["priority"] <= 5


def test_priority_values_valid(engine):
    """All priorities are in the range 1-5."""
    insights = engine.generate_insights(
        "test-id",
        {},
        {"visibility_pct": 2, "brand_name": "Optivio", "prompt_count": 100},
        {"queries": []},
        {"daily_data": [], "summary": {}},
    )
    for i in insights:
        assert i["priority"] in [1, 2, 3, 4, 5]


def test_insights_sorted_by_priority(engine):
    """generate_insights returns list sorted ascending by priority."""
    gsc_data = {
        "queries": [
            {
                "query": "seo platform",
                "impressions": 3000,
                "ctr": 0.008,
                "ctr_pct": 0.8,
                "clicks": 24,
                "position": 6,
            }
        ]
    }
    insights = engine.generate_insights(
        "test-id",
        {},
        {
            "score": {"visibility_score": 0.01, "prompts_analyzed": 10},
        },
        gsc_data,
        {},
    )
    if len(insights) >= 2:
        priorities = [i["priority"] for i in insights]
        assert priorities == sorted(priorities), "Insights should be sorted by priority"


def test_insight_has_rank_field(engine):
    """Each insight has a sequential rank field starting at 1."""
    gsc_data = {
        "queries": [
            {
                "query": "test query",
                "impressions": 4000,
                "ctr": 0.005,
                "ctr_pct": 0.5,
                "clicks": 20,
                "position": 4,
            }
        ]
    }
    insights = engine.generate_insights("test-id", {}, {}, gsc_data, {})
    for idx, insight in enumerate(insights):
        assert insight["rank"] == idx + 1


def test_ai_visibility_gap_fires_when_well_below_benchmark(engine):
    """Rule 6 fires when visibility is well below the industry benchmark."""
    ai_data = {
        "score": {
            "visibility_score": 0.01,
            "prompts_analyzed": 20,
        }
    }
    insights = engine.generate_insights("test-id", {}, ai_data, {}, {})
    insight_types = [i.get("insight_type") for i in insights]
    assert "ai_visibility_gap" in insight_types


def test_trial_usage_nudge_fires_in_range(engine):
    """Rule 9 fires when scan usage is between 60-95% of the free limit."""
    ai_data = {
        "score": {
            "scan_count": 35,
            "visibility_score": 0.3,
        }
    }
    insights = engine.generate_insights("test-id", {}, ai_data, {}, {})
    insight_types = [i.get("insight_type") for i in insights]
    assert "trial_usage_nudge" in insight_types


def test_trial_usage_nudge_does_not_fire_below_60_pct(engine):
    """Rule 9 does not fire when usage is below 60%."""
    ai_data = {
        "score": {
            "scan_count": 20,
            "visibility_score": 0.3,
        }
    }
    insights = engine.generate_insights("test-id", {}, ai_data, {}, {})
    insight_types = [i.get("insight_type") for i in insights]
    assert "trial_usage_nudge" not in insight_types


def test_engine_uses_industry_benchmark():
    """InsightEngine sets the correct benchmark for the given industry."""
    saas_engine = InsightEngine(brand_name="Acme", industry="SaaS")
    tech_engine = InsightEngine(brand_name="Acme", industry="Technology")
    marketing_engine = InsightEngine(brand_name="Acme", industry="Marketing")
    assert saas_engine.benchmark_visibility == 0.28
    assert tech_engine.benchmark_visibility == 0.32
    assert marketing_engine.benchmark_visibility == 0.35


def test_engine_unknown_industry_uses_default():
    """InsightEngine falls back to default benchmark for unknown industry."""
    e = InsightEngine(brand_name="Acme", industry="UnknownIndustry")
    assert e.benchmark_visibility == 0.25
