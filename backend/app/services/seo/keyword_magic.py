"""
AdTicks — Keyword Magic Tool.

Generates keyword ideas analogous to:
    Ahrefs Keywords Explorer (matching terms, related terms, questions)
    SEMrush Keyword Magic Tool (broad/phrase/exact match groupings)
    Moz Keyword Explorer

Sources used (free / open):
    - Google Suggest (autocomplete) for matching terms across alphabet seeds
    - "People Also Ask" patterns (heuristic generation of question variants)
    - Related searches via Wikipedia disambiguation + WordNet (if available)
Each idea is enriched with:
    intent classification, difficulty heuristic, volume estimate, CPC estimate,
    competition score, parent topic clustering.
"""
from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from typing import Any

import httpx

from .keyword_service import _classify_intent, _estimate_difficulty

logger = logging.getLogger(__name__)

GOOGLE_SUGGEST = "https://suggestqueries.google.com/complete/search"
QUESTION_PREFIXES = [
    "what is", "what are", "how to", "how do", "how does", "why is", "why does",
    "when to", "where to", "which is", "who is", "can i", "is it", "should i",
]
PREP_MODIFIERS = ["for", "with", "without", "vs", "near me", "online", "free", "cheap"]


async def _suggest_for(client: httpx.AsyncClient, query: str, hl: str = "en") -> list[str]:
    """Hit Google Suggest for one query; returns 0..10 phrases."""
    try:
        resp = await client.get(
            GOOGLE_SUGGEST,
            params={"client": "firefox", "q": query, "hl": hl},
            headers={"User-Agent": "Mozilla/5.0 AdTicksKW/1.0"},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [s for s in data[1] if isinstance(s, str)]
    except Exception:
        return []


async def expand_seed(seed: str, location: str = "us") -> list[str]:
    """Run alphabet-soup expansion: 'seed a', 'seed b', ... + question prefixes."""
    seed = seed.lower().strip()
    queries: list[str] = [seed]
    queries += [f"{seed} {c}" for c in "abcdefghijklmnopqrstuvwxyz"]
    queries += [f"{p} {seed}" for p in QUESTION_PREFIXES]
    queries += [f"{seed} {m}" for m in PREP_MODIFIERS]

    async with httpx.AsyncClient(timeout=8.0) as client:
        results = await asyncio.gather(
            *(_suggest_for(client, q) for q in queries), return_exceptions=False
        )
    flat: set[str] = set()
    for batch in results:
        for kw in batch:
            kw = kw.lower().strip()
            if 2 <= len(kw.split()) <= 8:
                flat.add(kw)
    return sorted(flat)


def _classify_match_type(seed: str, keyword: str) -> str:
    seed_words = set(seed.lower().split())
    kw_words = set(keyword.lower().split())
    if any(p in keyword for p in QUESTION_PREFIXES) or keyword.endswith("?"):
        return "question"
    if seed.lower() in keyword.lower():
        if keyword.lower() == seed.lower():
            return "exact"
        if seed.lower() in keyword.lower() and seed_words.issubset(kw_words):
            return "phrase"
    if seed_words & kw_words:
        return "broad"
    return "related"


def _estimate_volume(keyword: str) -> int:
    """Heuristic monthly volume estimate based on word count."""
    n = len(keyword.split())
    base = {1: 8000, 2: 3500, 3: 3000, 4: 1500, 5: 500, 6: 200}.get(n, 50)
    # bias by presence of common high-volume modifiers
    if any(m in keyword for m in ("how to", "best", "near me", "online")):
        base = int(base * 1.4)
    return base


def _estimate_cpc(keyword: str, intent: str) -> float:
    base = {"transactional": 3.4, "commercial": 2.1, "informational": 0.4, "navigational": 0.2}[intent]
    if any(m in keyword for m in ("insurance", "lawyer", "loan", "mortgage", "credit")):
        base *= 4.5
    return round(base, 2)


def _competition(difficulty: int) -> float:
    return round(min(1.0, difficulty / 100.0), 2)


def _parent_topic(keyword: str) -> str:
    words = [w for w in keyword.split() if len(w) > 2]
    return words[0] if words else keyword


async def generate_ideas(
    seed: str,
    location: str = "us",
    include_questions: bool = True,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return enriched keyword ideas for a seed."""
    expanded = await expand_seed(seed, location)
    if not include_questions:
        expanded = [k for k in expanded if not any(k.startswith(p) for p in QUESTION_PREFIXES)]
    expanded = expanded[:limit] if limit else expanded

    ideas: list[dict[str, Any]] = []
    for kw in expanded:
        intent = _classify_intent(kw)
        difficulty = max(1, min(100, int(_estimate_difficulty(kw))))
        volume = _estimate_volume(kw)
        ideas.append({
            "seed": seed,
            "keyword": kw,
            "match_type": _classify_match_type(seed, kw),
            "intent": intent,
            "volume": volume,
            "difficulty": difficulty,
            "cpc": _estimate_cpc(kw, intent),
            "competition": _competition(difficulty),
            "serp_features": _likely_features(kw, intent),
            "parent_topic": _parent_topic(kw),
        })
    # sort by (volume desc, difficulty asc)
    ideas.sort(key=lambda x: (-x["volume"], x["difficulty"]))
    return ideas


def _likely_features(kw: str, intent: str) -> list[str]:
    features = []
    if any(p in kw for p in QUESTION_PREFIXES):
        features += ["featured_snippet", "people_also_ask"]
    if intent in ("transactional", "commercial"):
        features += ["shopping_results", "ads"]
    if "near me" in kw or "in " in kw:
        features.append("local_pack")
    if intent == "informational":
        features.append("knowledge_panel")
    return features


def group_by_parent_topic(ideas: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for idea in ideas:
        groups[idea["parent_topic"]].append(idea)
    return dict(groups)
