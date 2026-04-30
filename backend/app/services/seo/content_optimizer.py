"""
AdTicks — Content Optimizer + Brief Generator + Topic Cluster builder.

Functionally analogous to:
    Surfer SEO Content Editor / Frase Optimize / Clearscope grader
    Ahrefs Content Explorer briefs
    Moz Topic-modelling style cluster builds.

Approach: Pull the top SERP results for the target keyword, fetch and parse
each result, extract heading structure + key terms via TF-IDF, derive a
recommended outline, semantic terms, target word count, and questions to
answer. Then score user-supplied draft text against those references.
"""
from __future__ import annotations

import logging
import re
import statistics
from collections import Counter
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

STOPWORDS = set("""a an the and or but if then else for of in on at to from by with about as is are was were
be been being have has had do does did this that these those it its i you he she we they
us them my your his her their our not no yes can could should would will may might
will what which who whom whose where when why how than too very also more most some any
each every either neither both few many several here there now today""".split())


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text or "")]


def _content_words(text: str) -> list[str]:
    return [w for w in _tokenize(text) if w not in STOPWORDS]


def _extract_text_from_html(html: str) -> tuple[str, list[str], list[str]]:
    """Return (body_text, headings, questions)."""
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.select("script, style, nav, footer, header, aside"):
        s.decompose()
    headings: list[str] = []
    for level in ("h1", "h2", "h3"):
        for h in soup.find_all(level):
            t = h.get_text(" ", strip=True)
            if t:
                headings.append(f"[{level}] {t}")
    body = soup.get_text(" ", strip=True)
    body = re.sub(r"\s+", " ", body)
    questions = re.findall(r"(?:What|How|Why|When|Where|Who|Which)[^.?!]{8,80}\?", body)
    return body, headings, questions


async def _fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, follow_redirects=True, timeout=12)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            return r.text
    except Exception:
        pass
    return ""


async def generate_brief(
    target_keyword: str,
    competitor_urls: list[str] | None = None,
    target_word_count: int = 1500,
) -> dict[str, Any]:
    """Build a content brief by fetching competitor pages and TF-extracting."""
    competitor_urls = competitor_urls or []
    headers = {"User-Agent": "Mozilla/5.0 AdTicksContentBot/1.0"}
    pages: list[dict[str, Any]] = []
    if competitor_urls:
        async with httpx.AsyncClient(headers=headers) as client:
            import asyncio
            html_list = await asyncio.gather(*(_fetch(client, u) for u in competitor_urls))
        for url, html in zip(competitor_urls, html_list):
            if not html:
                continue
            body, headings, questions = _extract_text_from_html(html)
            pages.append({
                "url": url,
                "word_count": len(body.split()),
                "headings": headings,
                "questions": questions,
                "tokens": _content_words(body),
            })

    # Aggregate semantic terms via term frequency
    all_tokens = [t for p in pages for t in p["tokens"]]
    term_freq = Counter(all_tokens)
    seed_words = set(target_keyword.lower().split())
    semantic_terms = [
        w for w, _ in term_freq.most_common(40) if w not in seed_words and len(w) > 3
    ][:25]

    avg_words = (
        int(statistics.mean(p["word_count"] for p in pages)) if pages else target_word_count
    )

    # outline: most common H2/H3 themes
    headings: list[str] = []
    for p in pages:
        headings.extend(p["headings"])
    h2_h3 = [h for h in headings if h.startswith("[h2]") or h.startswith("[h3]")]
    common_outline = [h for h, _ in Counter(h2_h3).most_common(8)]

    # questions to answer
    qs: list[str] = []
    for p in pages:
        qs.extend(p["questions"])
    questions_to_answer = [q for q, _ in Counter(qs).most_common(8)]

    title_suggestions = [
        f"The Complete Guide to {target_keyword.title()}",
        f"{target_keyword.title()}: Everything You Need to Know in 2026",
        f"How to Master {target_keyword.title()} (Step-by-Step)",
        f"{target_keyword.title()} — A Practical Walkthrough",
    ]

    return {
        "target_keyword": target_keyword,
        "title_suggestions": title_suggestions,
        "h1": title_suggestions[0],
        "outline": common_outline,
        "semantic_terms": semantic_terms,
        "questions_to_answer": questions_to_answer,
        "target_word_count": max(target_word_count, int(avg_words * 1.05)) if pages else target_word_count,
        "avg_competitor_words": avg_words,
        "competitors_analyzed": [p["url"] for p in pages],
        "readability_target": "grade-8",
    }


# ---------------------------------------------------------------------------
# Optimizer scoring (Flesch-Kincaid + keyword density + heading + semantic)
# ---------------------------------------------------------------------------
def _syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev = False
    for c in word:
        is_v = c in vowels
        if is_v and not prev:
            count += 1
        prev = is_v
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> tuple[float, str]:
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return 0.0, "n/a"
    syllables = sum(_syllables(w) for w in words)
    score = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))
    grade = "easy"
    if score < 30:
        grade = "very-difficult"
    elif score < 50:
        grade = "difficult"
    elif score < 60:
        grade = "fairly-difficult"
    elif score < 70:
        grade = "standard"
    elif score < 80:
        grade = "fairly-easy"
    elif score < 90:
        grade = "easy"
    else:
        grade = "very-easy"
    return round(score, 1), grade


def score_content(
    target_keyword: str,
    content: str,
    semantic_terms: list[str] | None = None,
    target_word_count: int = 1500,
) -> dict[str, Any]:
    """Score a content draft. Returns a dict matching the optimizer model."""
    semantic_terms = semantic_terms or []
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(" ", strip=True) or content
    word_count = len(re.findall(r"\b\w+\b", text))

    # Keyword density
    target_words = target_keyword.lower().split()
    occurrences = len(re.findall(re.escape(target_keyword.lower()), text.lower()))
    density = (occurrences / max(1, word_count)) * 100

    # Headings score: h1 present, h2/h3 distribution
    h1 = soup.find_all("h1")
    h2 = soup.find_all("h2")
    h3 = soup.find_all("h3")
    headings_score = 0
    if h1:
        headings_score += 30
    if len(h2) >= 3:
        headings_score += 40
    elif len(h2) >= 1:
        headings_score += 25
    if len(h3) >= 2:
        headings_score += 30
    else:
        headings_score += 15
    headings_score = min(100, headings_score)

    # Semantic coverage
    text_lower = text.lower()
    covered = sum(1 for term in semantic_terms if term in text_lower)
    coverage = (covered / len(semantic_terms)) if semantic_terms else 0.5

    # Readability
    fre, grade = flesch_reading_ease(text)

    # Word count band score
    wc_score = 100 - min(100, abs(word_count - target_word_count) / target_word_count * 100)

    # Density band score (sweet spot 0.5%..2.5%)
    if 0.5 <= density <= 2.5:
        density_score = 100
    elif density < 0.5:
        density_score = max(0, 100 - (0.5 - density) * 100)
    else:
        density_score = max(0, 100 - (density - 2.5) * 30)

    overall = int(round(
        wc_score * 0.20
        + density_score * 0.20
        + headings_score * 0.20
        + coverage * 100 * 0.25
        + min(100, max(0, fre)) * 0.15
    ))

    suggestions: list[dict[str, Any]] = []
    if word_count < target_word_count * 0.85:
        suggestions.append({"type": "length", "text": f"Add ~{target_word_count - word_count} words to match competitor depth"})
    if density < 0.5:
        suggestions.append({"type": "keyword", "text": f"Increase usage of \"{target_keyword}\" — currently {density:.2f}% density"})
    if density > 2.5:
        suggestions.append({"type": "keyword", "text": "Reduce keyword density to avoid keyword stuffing (<2.5% recommended)"})
    if not h1:
        suggestions.append({"type": "structure", "text": "Add an H1 heading"})
    if len(h2) < 3:
        suggestions.append({"type": "structure", "text": "Add more H2 subsections (3+ recommended)"})
    if coverage < 0.6 and semantic_terms:
        missing = [t for t in semantic_terms if t not in text_lower][:5]
        suggestions.append({"type": "semantic", "text": f"Cover related terms: {', '.join(missing)}"})

    return {
        "target_keyword": target_keyword,
        "word_count": word_count,
        "readability_score": fre,
        "grade_level": grade,
        "keyword_density": round(density, 2),
        "headings_score": headings_score,
        "semantic_coverage": round(coverage, 2),
        "overall_score": max(0, min(100, overall)),
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Topic cluster builder
# ---------------------------------------------------------------------------
def build_topic_cluster(
    pillar_topic: str,
    keyword_ideas: list[dict[str, Any]],
    max_supporting: int = 8,
) -> dict[str, Any]:
    """Build a pillar + supporting article cluster from keyword ideas."""
    pillar_lower = pillar_topic.lower()
    related = [
        k for k in keyword_ideas
        if pillar_lower in k.get("keyword", "").lower() and k.get("keyword", "").lower() != pillar_lower
    ]
    related.sort(key=lambda k: -k.get("volume", 0))
    supporting = related[:max_supporting]
    total_volume = sum(k.get("volume", 0) for k in supporting)
    coverage = min(100, len(supporting) * 10 + 20)
    return {
        "pillar_topic": pillar_topic,
        "supporting_topics": [
            {
                "topic": k["keyword"],
                "monthly_volume": k.get("volume", 0),
                "difficulty": k.get("difficulty", 0),
                "intent": k.get("intent"),
                "status": "planned",
            }
            for k in supporting
        ],
        "total_volume": total_volume,
        "coverage_score": coverage,
    }
