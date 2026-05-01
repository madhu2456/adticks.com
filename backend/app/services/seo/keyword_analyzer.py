"""
Keyword analysis and optimization for SEO audit.
Analyzes keyword density, placement, LSI keywords, and content gaps.
"""

import logging
import re
from typing import Dict, Any, List, Set, Tuple
from collections import Counter
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Common stop words that should be ignored in keyword analysis
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "must", "shall", "it", "its", "this", "that", "these",
    "those", "which", "who", "whom", "what", "where", "when", "why", "how", "not",
    "no", "such", "than", "too", "so", "very", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "any", "many", "much", "only", "same",
    "just", "even", "if", "also", "up", "out", "about", "into", "through", "over",
    "under", "off", "above", "below", "between", "among", "around", "before", "after",
    "during", "within", "without", "against", "along", "across", "beside", "behind",
    "beyond", "inside", "outside", "above", "below", "down", "up", "i", "you", "he",
    "she", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her"
}

# Common LSI keywords to look for (extends based on primary keywords)
LSI_PATTERNS = {
    "seo": ["search engine", "organic", "ranking", "keyword", "backlink", "algorithm"],
    "marketing": ["advertising", "campaign", "promotion", "social media", "digital", "branding"],
    "content": ["blog", "article", "post", "writing", "copywriting", "editorial"],
}

TIMEOUT = 15.0


class KeywordAnalyzer:
    """Analyzes keywords, density, placement, and content quality."""

    def __init__(self, timeout: float = TIMEOUT):
        self.timeout = timeout

    async def analyze_keywords(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Analyze keywords in page content.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with keyword analysis results
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "keywords": [],
            "primary_keyword": None,
            "keyword_density": {},
            "keyword_placement": {},
            "lsi_keywords": [],
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(
                    f"Could not fetch page (HTTP {response.status_code})"
                )
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract text from different sections
            title = soup.find("title")
            title_text = title.get_text() if title else ""

            h1 = soup.find("h1")
            h1_text = h1.get_text() if h1 else ""

            meta_desc = soup.find("meta", attrs={"name": "description"})
            meta_text = meta_desc.get("content", "") if meta_desc else ""

            # Get body text (exclude script, style tags)
            for tag in soup(["script", "style"]):
                tag.decompose()
            body_text = soup.get_text()

            # Extract keywords from title, H1, and body
            title_keywords = self._extract_keywords(title_text)
            h1_keywords = self._extract_keywords(h1_text)
            body_keywords = self._extract_keywords(body_text)

            # Find primary keyword (most common, in title and H1)
            if title_keywords and h1_keywords:
                common_keywords = set(title_keywords) & set(h1_keywords)
                if common_keywords:
                    # Most frequent keyword that appears in both title and H1
                    all_keywords = title_keywords + h1_keywords + body_keywords
                    freq = Counter(all_keywords)
                    primary = max(
                        (k for k in common_keywords if k in freq),
                        key=lambda x: freq[x],
                        default=None,
                    )
                    result["primary_keyword"] = primary

            # Calculate keyword density (top 10 keywords)
            all_keywords = title_keywords + h1_keywords + body_keywords
            keyword_freq = Counter(all_keywords)
            total_keywords = len(all_keywords)

            result["keyword_density"] = {
                keyword: round((count / total_keywords) * 100, 2)
                for keyword, count in keyword_freq.most_common(10)
            }

            # Analyze keyword placement
            result["keyword_placement"] = {
                "in_title": len(title_keywords) > 0,
                "in_h1": len(h1_keywords) > 0,
                "in_meta_description": len(self._extract_keywords(meta_text)) > 0,
                "title_keyword_count": len(title_keywords),
                "h1_keyword_count": len(h1_keywords),
            }

            # Find LSI keywords
            lsi = self._find_lsi_keywords(body_text)
            result["lsi_keywords"] = lsi[:5]  # Top 5 LSI keywords

            # Validation checks
            if result["primary_keyword"]:
                result["passed"] = True
                density = result["keyword_density"].get(result["primary_keyword"], 0)

                # Check keyword density (optimal: 0.5% - 2.5%)
                if density < 0.5:
                    result["issues"].append(
                        f"Primary keyword density too low ({density}%), target 0.5-2.5%"
                    )
                elif density > 2.5:
                    result["issues"].append(
                        f"Primary keyword density too high ({density}%), target 0.5-2.5%"
                    )

                # Check keyword placement
                if not result["keyword_placement"]["in_title"]:
                    result["issues"].append("Primary keyword missing from title tag")
                if not result["keyword_placement"]["in_h1"]:
                    result["issues"].append("Primary keyword missing from H1 tag")

            if not result["passed"]:
                result["issues"].append("Unable to identify primary keyword")

        except Exception as e:
            result["issues"].append(f"Keyword analysis failed: {str(e)}")
            logger.error(f"Keyword analysis error: {e}")

        return result

    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract keywords from text (excluding stop words).

        Args:
            text: Text to extract keywords from
            min_length: Minimum word length

        Returns:
            List of keywords
        """
        # Clean text
        text = text.lower()
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        # Split into words
        words = text.split()
        # Filter out stop words and short words
        keywords = [
            w for w in words if len(w) >= min_length and w not in STOP_WORDS
        ]
        return keywords

    def _find_lsi_keywords(self, text: str, limit: int = 5) -> List[str]:
        """
        Find Latent Semantic Indexing (LSI) keywords.

        Args:
            text: Text to analyze
            limit: Maximum number of LSI keywords to return

        Returns:
            List of LSI keywords
        """
        text_lower = text.lower()
        lsi_keywords = []

        # Check predefined LSI patterns
        for primary, lsi_words in LSI_PATTERNS.items():
            for lsi_word in lsi_words:
                if lsi_word.lower() in text_lower:
                    # Count occurrences
                    count = len(re.findall(r"\b" + re.escape(lsi_word) + r"\b", text_lower))
                    lsi_keywords.append((lsi_word, count))

        # Sort by frequency and return top N
        lsi_keywords.sort(key=lambda x: x[1], reverse=True)
        return [keyword for keyword, _ in lsi_keywords[:limit]]

    async def analyze_content_quality(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Analyze content quality (word count, readability, etc.).

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with content quality metrics
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "word_count": 0,
            "unique_words": 0,
            "average_sentence_length": 0,
            "readability_score": 0,
            "content_type": "thin",  # thin, adequate, rich
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text()
            # Clean up whitespace
            text = " ".join(text.split())

            # Word count
            words = text.split()
            result["word_count"] = len(words)
            result["unique_words"] = len(set(words))

            # Content type classification
            if result["word_count"] < 300:
                result["content_type"] = "thin"
                result["issues"].append(
                    f"Thin content detected ({result['word_count']} words). Target: 300+ words"
                )
            elif result["word_count"] < 600:
                result["content_type"] = "adequate"
            else:
                result["content_type"] = "rich"
                result["passed"] = True

            # Calculate readability (Flesch Reading Ease simplified)
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if sentences:
                result["average_sentence_length"] = len(words) / len(sentences)
                # Simplified Flesch score: 100 - (avg_sent_len + avg_word_len)
                avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
                flesch_score = max(0, 100 - result["average_sentence_length"] - (avg_word_length * 0.5))
                result["readability_score"] = round(flesch_score)

                # Check readability
                if result["readability_score"] < 60:
                    result["issues"].append(
                        f"Low readability score ({result['readability_score']}). "
                        "Use simpler words and shorter sentences."
                    )

            if result["word_count"] >= 300:
                result["passed"] = True

        except Exception as e:
            result["issues"].append(f"Content quality analysis failed: {str(e)}")
            logger.error(f"Content quality error: {e}")

        return result

    def analyze_content_gaps(
        self, content: str, primary_keyword: str
    ) -> Dict[str, Any]:
        """
        Analyze content gaps based on primary keyword.

        Args:
            content: Page content
            primary_keyword: Primary keyword to analyze

        Returns:
            Dict with content gap analysis
        """
        result: Dict[str, Any] = {
            "gaps": [],
            "recommendations": [],
        }

        if not primary_keyword:
            return result

        content_lower = content.lower()

        # Common questions related to keywords
        questions = [
            f"how to {primary_keyword}",
            f"what is {primary_keyword}",
            f"why {primary_keyword}",
            f"where to {primary_keyword}",
            f"when to {primary_keyword}",
            f"best {primary_keyword}",
            f"top {primary_keyword}",
            f"{primary_keyword} guide",
            f"{primary_keyword} tutorial",
        ]

        missing_questions = []
        for question in questions:
            if question not in content_lower:
                missing_questions.append(question)

        if missing_questions:
            result["gaps"] = missing_questions[:5]
            result["recommendations"].append(
                f"Consider adding sections addressing: {', '.join(missing_questions[:3])}"
            )

        return result
