"""
Keyword generation and clustering service for AdTicks SEO module.
Uses OpenAI for generation and scikit-learn TF-IDF + KMeans for clustering.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

INTENT_TYPES = ["informational", "navigational", "transactional", "commercial"]


def _classify_intent(keyword: str) -> str:
    """Heuristic fallback intent classification based on keyword patterns."""
    kw = keyword.lower()
    transactional_signals = ["buy", "purchase", "order", "shop", "price", "cost", "cheap", "deal", "discount", "coupon", "subscribe", "download", "get", "trial", "free"]
    commercial_signals = ["best", "top", "review", "vs", "compare", "alternative", "recommend", "rated", "ranking"]
    navigational_signals = ["login", "sign in", "account", "official", "website", "portal", "app"]

    for sig in transactional_signals:
        if sig in kw:
            return "transactional"
    for sig in commercial_signals:
        if sig in kw:
            return "commercial"
    for sig in navigational_signals:
        if sig in kw:
            return "navigational"
    return "informational"


def _estimate_difficulty(keyword: str) -> int:
    """Heuristic fallback difficulty estimation based on keyword length and specificity."""
    words = keyword.split()
    length_factor = len(words)
    base = 70
    # Longer tail = lower difficulty
    reduction = min(length_factor * 8, 50)
    return max(10, base - reduction + np.random.randint(-5, 5))


async def generate_keywords(
    domain: str,
    industry: str,
    seed_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate 50-100 relevant keywords with intent classification and difficulty scores.

    Args:
        domain: The target domain (e.g. 'example.com')
        industry: Industry category (e.g. 'SaaS', 'E-commerce')
        seed_keywords: Initial seed keywords to expand from

    Returns:
        List of dicts with keys: keyword, intent, difficulty, volume
    """
    logger.info(f"Generating keywords for domain={domain} industry={industry} seeds={seed_keywords}")

    keywords: List[Dict[str, Any]] = []

    from app.core.config import settings
    if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
        try:
            client = AsyncOpenAI()
            seed_str = ", ".join(seed_keywords)
            prompt = f"""You are an SEO expert. Generate 80 highly relevant keywords for:
Domain: {domain}
Industry: {industry}
Seed Keywords: {seed_str}

For each keyword provide:
- keyword: the keyword phrase
- intent: one of [informational, navigational, transactional, commercial]
- difficulty: integer 1-100 (100 = hardest to rank for)
- volume: estimated monthly search volume as integer

Return a valid JSON array of objects with exactly these fields. No extra text."""

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            for item in parsed:
                keywords.append({
                    "keyword": str(item.get("keyword", "")),
                    "intent": item.get("intent", "informational") if item.get("intent") in INTENT_TYPES else "informational",
                    "difficulty": max(1, min(100, int(item.get("difficulty", 50)))),
                    "volume": max(0, int(item.get("volume", 100))),
                })
            logger.info(f"OpenAI generated {len(keywords)} keywords")
        except Exception as e:
            logger.warning(f"OpenAI keyword generation failed: {e}. Falling back to heuristic generation.")
            keywords = []

    if not keywords:
        # Fallback: expand seeds heuristically
        modifiers_info = ["what is", "how to use", "guide to", "introduction to", "understanding", "benefits of", "examples of"]
        modifiers_commercial = ["best", "top", "review", "vs", "alternative to", "compare", "pricing", "features of"]
        modifiers_transactional = ["buy", "get", "download", "free trial", "sign up for", "purchase", "subscribe to", "cheap"]
        modifiers_nav = [f"{domain} login", f"{domain} official", f"{domain} pricing page"]

        for seed in seed_keywords:
            for mod in modifiers_info:
                keywords.append({"keyword": f"{mod} {seed}", "intent": "informational", "difficulty": _estimate_difficulty(f"{mod} {seed}"), "volume": np.random.randint(100, 3000)})
            for mod in modifiers_commercial:
                keywords.append({"keyword": f"{mod} {seed}", "intent": "commercial", "difficulty": _estimate_difficulty(f"{mod} {seed}"), "volume": np.random.randint(200, 8000)})
            for mod in modifiers_transactional:
                keywords.append({"keyword": f"{mod} {seed}", "intent": "transactional", "difficulty": _estimate_difficulty(f"{mod} {seed}"), "volume": np.random.randint(50, 2000)})
        for nav in modifiers_nav:
            keywords.append({"keyword": nav, "intent": "navigational", "difficulty": 20, "volume": np.random.randint(500, 5000)})

        # Trim/extend to roughly 60-80
        keywords = keywords[:80] if len(keywords) > 80 else keywords

    logger.info(f"Total keywords generated: {len(keywords)}")
    return keywords


def cluster_keywords(keywords: List[Dict[str, Any]], n_clusters: Optional[int] = None) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster keywords into topic groups using TF-IDF + KMeans.

    Args:
        keywords: List of keyword dicts (must contain 'keyword' field)
        n_clusters: Number of clusters; auto-determined if None

    Returns:
        Dict mapping cluster_id -> list of keyword dicts (with added 'cluster' field)
    """
    if not keywords:
        logger.warning("No keywords to cluster")
        return {}

    texts = [kw["keyword"] for kw in keywords]
    n = len(texts)

    if n < 3:
        # Too few to cluster meaningfully
        for i, kw in enumerate(keywords):
            kw["cluster"] = 0
        return {0: keywords}

    # Auto-determine cluster count: sqrt(n/2) capped between 3 and 15
    if n_clusters is None:
        n_clusters = max(3, min(15, int(np.sqrt(n / 2))))

    logger.info(f"Clustering {n} keywords into {n_clusters} clusters")

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
            stop_words="english",
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        tfidf_normalized = normalize(tfidf_matrix)

        kmeans = KMeans(
            n_clusters=n_clusters,
            init="k-means++",
            max_iter=300,
            n_init=10,
            random_state=42,
        )
        labels = kmeans.fit_predict(tfidf_normalized)

        clustered: Dict[int, List[Dict[str, Any]]] = {}
        for kw, label in zip(keywords, labels):
            kw_copy = dict(kw)
            kw_copy["cluster"] = int(label)
            clustered.setdefault(int(label), []).append(kw_copy)

        logger.info(f"Clustering complete. Cluster sizes: { {k: len(v) for k, v in clustered.items()} }")
        return clustered

    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        # Fallback: single cluster
        for kw in keywords:
            kw["cluster"] = 0
        return {0: keywords}
