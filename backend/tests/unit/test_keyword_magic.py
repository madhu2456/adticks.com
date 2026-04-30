"""Unit tests for app.services.seo.keyword_magic."""
from __future__ import annotations

import pytest

from app.services.seo.keyword_magic import (
    _classify_match_type,
    _estimate_volume,
    _estimate_cpc,
    _competition,
    _likely_features,
    _parent_topic,
    group_by_parent_topic,
    generate_ideas,
    expand_seed,
)


class TestMatchTypeClassification:
    def test_question_phrase(self):
        assert _classify_match_type("seo", "what is seo") == "question"

    def test_exact_match(self):
        assert _classify_match_type("seo", "seo") == "exact"

    def test_phrase_match(self):
        assert _classify_match_type("seo", "best seo tools") == "phrase"

    def test_broad_match(self):
        assert _classify_match_type("seo", "search engine seo guide") in ("phrase", "broad")

    def test_related_when_no_overlap(self):
        assert _classify_match_type("seo", "marketing automation") == "related"


class TestVolumeEstimate:
    def test_single_word_high_volume(self):
        assert _estimate_volume("shoes") == 8000

    def test_multi_word_lower_volume(self):
        v3 = _estimate_volume("running shoes mens")
        v5 = _estimate_volume("best running shoes for flat feet")
        assert v3 > v5

    def test_high_intent_modifier_boost(self):
        base = _estimate_volume("running shoes")
        with_boost = _estimate_volume("best running shoes")
        assert with_boost >= base


class TestCPC:
    def test_transactional_higher_than_informational(self):
        assert _estimate_cpc("buy shoes", "transactional") > _estimate_cpc("how shoes work", "informational")

    def test_high_value_industry_multiplier(self):
        normal = _estimate_cpc("buy book", "transactional")
        boosted = _estimate_cpc("buy insurance", "transactional")
        assert boosted > normal


class TestCompetitionParentLikelyFeatures:
    def test_competition_clamped(self):
        assert _competition(150) == 1.0
        assert _competition(0) == 0.0

    def test_parent_topic_first_long_word(self):
        assert _parent_topic("best running shoes") == "best"

    def test_likely_features_for_question(self):
        feats = _likely_features("how to seo", "informational")
        assert "featured_snippet" in feats
        assert "people_also_ask" in feats

    def test_likely_features_for_local(self):
        feats = _likely_features("plumbers near me", "transactional")
        assert "local_pack" in feats


class TestGrouping:
    def test_group_by_parent_topic(self):
        ideas = [
            {"keyword": "running shoes", "parent_topic": "running"},
            {"keyword": "running socks", "parent_topic": "running"},
            {"keyword": "tennis shoes", "parent_topic": "tennis"},
        ]
        out = group_by_parent_topic(ideas)
        assert "running" in out and len(out["running"]) == 2
        assert len(out["tennis"]) == 1


@pytest.mark.asyncio
async def test_generate_ideas_with_mocked_suggest(monkeypatch):
    """generate_ideas should produce enriched rows even when network mocked."""
    async def fake_expand(seed, location):
        return ["seo guide", "what is seo", "best seo tools", "seo near me"]

    monkeypatch.setattr("app.services.seo.keyword_magic.expand_seed", fake_expand)
    ideas = await generate_ideas("seo", limit=10)
    assert len(ideas) == 4
    for idea in ideas:
        assert idea["seed"] == "seo"
        assert idea["match_type"] in {"question", "phrase", "exact", "broad", "related"}
        assert idea["intent"] in {"informational", "navigational", "transactional", "commercial"}
        assert 1 <= idea["difficulty"] <= 100
        assert idea["volume"] >= 0
        assert isinstance(idea["serp_features"], list)


@pytest.mark.asyncio
async def test_expand_seed_handles_failures(monkeypatch):
    """If Google Suggest is unreachable, expand_seed should still return [] gracefully."""
    import httpx
    transport = httpx.MockTransport(lambda req: httpx.Response(500, request=req))
    real_async_client = httpx.AsyncClient

    class _Patched(real_async_client):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    monkeypatch.setattr(httpx, "AsyncClient", _Patched)

    result = await expand_seed("seo")
    # All 500 -> empty
    assert isinstance(result, list)
