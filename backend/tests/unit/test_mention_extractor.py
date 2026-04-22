"""Unit tests for mention_extractor.extract_mentions."""
from app.services.ai.mention_extractor import extract_mentions, aggregate_mention_stats


# ---------------------------------------------------------------------------
# Basic detection
# ---------------------------------------------------------------------------

def test_brand_present_in_text_is_detected():
    """Target brand found in text produces at least one mention."""
    mentions = extract_mentions(
        response_text="Optivio is a great SEO platform that helps you rank.",
        target_brand="Optivio",
    )
    assert len(mentions) >= 1
    target_mentions = [m for m in mentions if m["is_target_brand"]]
    assert len(target_mentions) >= 1


def test_competitor_present_is_detected():
    """Competitor brand found in text produces a non-target mention."""
    mentions = extract_mentions(
        response_text="You could also use Ahrefs for backlink analysis.",
        target_brand="Optivio",
        competitor_brands=["Ahrefs"],
    )
    competitor_mentions = [m for m in mentions if not m["is_target_brand"]]
    assert len(competitor_mentions) >= 1
    assert competitor_mentions[0]["brand"] == "Ahrefs"


def test_no_brand_in_text_returns_empty():
    """Text without any brand name returns empty list."""
    mentions = extract_mentions(
        response_text="Search engines use complex algorithms to rank content.",
        target_brand="Optivio",
        competitor_brands=["Ahrefs"],
    )
    assert mentions == []


def test_empty_text_returns_empty_list():
    """Empty string input returns empty list without raising."""
    result = extract_mentions("", target_brand="Optivio")
    assert result == []


def test_none_like_empty_text_no_crash():
    """Falsy text input returns empty list."""
    result = extract_mentions("", target_brand="Brand")
    assert isinstance(result, list)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# Mention dict structure
# ---------------------------------------------------------------------------

def test_mention_has_required_keys():
    """Each mention dict must contain brand, position, and confidence keys."""
    mentions = extract_mentions(
        response_text="Optivio is recommended for mid-size SaaS companies.",
        target_brand="Optivio",
    )
    assert len(mentions) >= 1
    for m in mentions:
        assert "brand" in m
        assert "position" in m
        assert "confidence" in m


def test_mention_has_full_schema():
    """Mention dict has all expected fields from the implementation."""
    mentions = extract_mentions(
        response_text="Optivio is a solid choice for SEO.",
        target_brand="Optivio",
    )
    assert len(mentions) >= 1
    m = mentions[0]
    assert "id" in m
    assert "brand" in m
    assert "is_target_brand" in m
    assert "position" in m
    assert "confidence" in m
    assert "context" in m
    assert "sentiment" in m
    assert "char_offset" in m


def test_confidence_is_float_between_0_and_1():
    """Confidence values are floats in [0.0, 1.0]."""
    mentions = extract_mentions(
        response_text="I recommend Optivio for all your SEO needs. Optivio is the best.",
        target_brand="Optivio",
    )
    for m in mentions:
        assert isinstance(m["confidence"], float)
        assert 0.0 <= m["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_case_insensitive_matching():
    """Brand detection is case-insensitive."""
    mentions_upper = extract_mentions("OPTIVIO is great.", target_brand="Optivio")
    mentions_lower = extract_mentions("optivio is great.", target_brand="Optivio")
    assert len(mentions_upper) >= 1
    assert len(mentions_lower) >= 1


def test_mixed_case_target_and_text():
    """Mixed-case brand name matches regardless of text case."""
    mentions = extract_mentions(
        "Have you tried optivio? OPTIVIO has great features.",
        target_brand="Optivio",
    )
    assert len(mentions) >= 2


# ---------------------------------------------------------------------------
# Position detection
# ---------------------------------------------------------------------------

def test_position_values_are_valid():
    """Position field is one of 'first', 'middle', or 'last'."""
    text = " ".join(["filler"] * 100) + " Optivio " + " ".join(["filler"] * 100)
    mentions = extract_mentions(text, target_brand="Optivio")
    for m in mentions:
        assert m["position"] in ("first", "middle", "last")


def test_first_position_for_early_mention():
    """Brand appearing at the start of text gets position 'first'."""
    mentions = extract_mentions("Optivio is great for SEO.", target_brand="Optivio")
    assert len(mentions) >= 1
    assert mentions[0]["position"] == "first"


# ---------------------------------------------------------------------------
# response_id linkage
# ---------------------------------------------------------------------------

def test_response_id_is_attached():
    """response_id kwarg is attached to each mention dict."""
    mentions = extract_mentions(
        "Optivio stands out in the market.",
        target_brand="Optivio",
        response_id="resp-001",
    )
    assert len(mentions) >= 1
    assert mentions[0]["response_id"] == "resp-001"


def test_response_id_none_by_default():
    """response_id is None when not provided."""
    mentions = extract_mentions("Optivio is good.", target_brand="Optivio")
    assert mentions[0]["response_id"] is None


# ---------------------------------------------------------------------------
# aggregate_mention_stats
# ---------------------------------------------------------------------------

def test_aggregate_empty_mentions():
    """aggregate_mention_stats handles empty list gracefully."""
    stats = aggregate_mention_stats([], target_brand="Optivio")
    assert stats["total_mentions"] == 0
    assert stats["target_mentions"] == 0
    assert stats["competitor_mentions"] == 0
    assert stats["avg_confidence"] == 0.0


def test_aggregate_counts_correctly():
    """aggregate_mention_stats counts target vs competitor correctly."""
    mentions = extract_mentions(
        "Optivio is the best. Ahrefs is also popular.",
        target_brand="Optivio",
        competitor_brands=["Ahrefs"],
    )
    stats = aggregate_mention_stats(mentions, target_brand="Optivio")
    assert stats["target_mentions"] >= 1
    assert stats["competitor_mentions"] >= 1
    assert stats["total_mentions"] == stats["target_mentions"] + stats["competitor_mentions"]
