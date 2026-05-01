"""
Content quality analysis including plagiarism, duplicate content, and thin content detection.
"""

import hashlib
import logging
import re
from typing import Dict, Any, List, Tuple
from collections import Counter

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 15.0


class ContentQualityAnalyzer:
    """Analyzes content for duplicates, plagiarism, and thin content issues."""

    def __init__(self, timeout: float = TIMEOUT):
        self.timeout = timeout

    async def check_duplicate_content(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Check for duplicate content within a domain.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with duplicate content analysis
        """
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "duplicate_meta_titles": [],
            "duplicate_meta_descriptions": [],
            "content_hash": None,
            "has_duplicate_tags": False,
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Check for duplicate meta tags within page
            titles = [t.get_text() for t in soup.find_all("title")]
            meta_titles = [
                t.get("content")
                for t in soup.find_all("meta", attrs={"property": "og:title"})
            ]
            meta_descs = [
                t.get("content")
                for t in soup.find_all("meta", attrs={"name": "description"})
            ]

            # Check for duplicates
            if len(set(titles)) < len(titles):
                result["issues"].append("Multiple title tags detected")
                result["has_duplicate_tags"] = True
                result["passed"] = False

            if len(set(meta_titles)) < len(meta_titles):
                result["duplicate_meta_titles"] = [
                    t for t, count in Counter(meta_titles).items() if count > 1
                ]
                result["issues"].append(
                    f"Duplicate OG titles: {len(result['duplicate_meta_titles'])}"
                )
                result["passed"] = False

            if len(set(meta_descs)) < len(meta_descs):
                result["duplicate_meta_descriptions"] = [
                    d for d, count in Counter(meta_descs).items() if count > 1
                ]
                result["issues"].append(
                    f"Duplicate meta descriptions: {len(result['duplicate_meta_descriptions'])}"
                )
                result["passed"] = False

            # Generate content hash for duplicate detection
            body = soup.find("body")
            if body:
                # Remove script and style tags for content hash
                for tag in body(["script", "style"]):
                    tag.decompose()
                content = body.get_text()
                # Normalize whitespace
                content = " ".join(content.split())
                result["content_hash"] = hashlib.md5(content.encode()).hexdigest()

        except Exception as e:
            result["issues"].append(f"Duplicate content check failed: {str(e)}")
            logger.error(f"Duplicate content error: {e}")

        return result

    async def check_thin_content(
        self, url: str, client: httpx.AsyncClient, min_word_count: int = 300
    ) -> Dict[str, Any]:
        """
        Check for thin content (insufficient word count).

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance
            min_word_count: Minimum acceptable word count

        Returns:
            Dict with thin content analysis
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "word_count": 0,
            "min_required": min_word_count,
            "is_thin": False,
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style
            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text()
            # Clean whitespace
            text = " ".join(text.split())
            
            # Count words
            words = text.split()
            result["word_count"] = len(words)

            if result["word_count"] < min_word_count:
                result["is_thin"] = True
                result["issues"].append(
                    f"Thin content: {result['word_count']} words (minimum: {min_word_count})"
                )
            else:
                result["passed"] = True

        except Exception as e:
            result["issues"].append(f"Thin content check failed: {str(e)}")
            logger.error(f"Thin content error: {e}")

        return result

    async def analyze_plagiarism_risk(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Analyze plagiarism risk based on content patterns.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with plagiarism risk assessment
        """
        result: Dict[str, Any] = {
            "passed": True,
            "plagiarism_risk": "low",
            "risk_score": 0,
            "issues": [],
            "suspicions": [],
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style
            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text()

            # Check for plagiarism indicators
            risk_factors = []

            # 1. Check for common phrases (potential indicator of copying)
            common_phrases = [
                "in conclusion",
                "in summary",
                "as mentioned",
                "it is important to note",
            ]
            phrase_count = sum(text.lower().count(phrase) for phrase in common_phrases)
            if phrase_count > 5:
                risk_factors.append(("High use of common phrases", phrase_count))

            # 2. Check quoted content
            quoted_text = len(re.findall(r'"[^"]{50,}"', text))
            if quoted_text > 5:
                risk_factors.append(("Multiple long quotes (>50 chars)", quoted_text))
                result["suspicions"].append("Multiple unattributed quotes detected")

            # 3. Check for citations/references
            citations = len(re.findall(r"according to|research shows|studies found", text.lower()))
            if quoted_text > 5 and citations < 2:
                result["suspicions"].append(
                    "Many quotes but few citations - potential plagiarism risk"
                )

            # 4. Check sentence length consistency (varies normally in original content)
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                sentence_lengths = [len(s.split()) for s in sentences]
                # Calculate variance
                avg_length = sum(sentence_lengths) / len(sentence_lengths)
                variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(
                    sentence_lengths
                )
                if variance < 5:
                    result["suspicions"].append(
                        "Very consistent sentence structure - might indicate copied content"
                    )

            # Calculate risk score
            if result["suspicions"]:
                result["risk_score"] = min(70, len(result["suspicions"]) * 25)
                if result["risk_score"] < 30:
                    result["plagiarism_risk"] = "low"
                elif result["risk_score"] < 60:
                    result["plagiarism_risk"] = "medium"
                    result["issues"].append("Medium plagiarism risk detected")
                    result["passed"] = False
                else:
                    result["plagiarism_risk"] = "high"
                    result["issues"].append("High plagiarism risk detected")
                    result["passed"] = False

        except Exception as e:
            result["issues"].append(f"Plagiarism analysis failed: {str(e)}")
            logger.error(f"Plagiarism analysis error: {e}")

        return result

    def calculate_readability_score(self, text: str) -> Tuple[int, str]:
        """
        Calculate Flesch Reading Ease readability score.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (score, grade_level)
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Count sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(len(sentences), 1)

        # Count words
        words = text.split()
        word_count = len(words)

        # Count syllables (simplified: vowel count approximation)
        vowels = "aeiou"
        syllable_count = 0
        for word in words:
            word = word.lower()
            syllables = 0
            previous_was_vowel = False
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not previous_was_vowel:
                    syllables += 1
                previous_was_vowel = is_vowel
            syllable_count += max(1, syllables)  # At least 1 per word

        # Flesch Reading Ease formula
        if word_count > 0 and sentence_count > 0:
            score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (
                syllable_count / word_count
            )
            score = max(0, min(100, score))  # Clamp between 0-100
        else:
            score = 0

        # Grade level interpretation
        if score >= 90:
            grade = "5th grade (very easy)"
        elif score >= 80:
            grade = "6th grade (easy)"
        elif score >= 70:
            grade = "7th grade (fairly easy)"
        elif score >= 60:
            grade = "8th-9th grade (standard)"
        elif score >= 50:
            grade = "10th-12th grade (fairly difficult)"
        elif score >= 30:
            grade = "College (difficult)"
        else:
            grade = "College graduate (very difficult)"

        return (int(score), grade)

    async def analyze_full_content_quality(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Comprehensive content quality analysis.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with comprehensive quality metrics
        """
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "duplicate_content": {},
            "thin_content": {},
            "plagiarism_risk": {},
            "readability": {
                "score": 0,
                "grade": "",
            },
        }

        try:
            # Run all checks
            duplicate_result = await self.check_duplicate_content(url, client)
            thin_result = await self.check_thin_content(url, client)
            plagiarism_result = await self.analyze_plagiarism_risk(url, client)

            result["duplicate_content"] = duplicate_result
            result["thin_content"] = thin_result
            result["plagiarism_risk"] = plagiarism_result

            # Calculate readability if we can get content
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()
                text = soup.get_text()
                score, grade = self.calculate_readability_score(text)
                result["readability"]["score"] = score
                result["readability"]["grade"] = grade

            # Determine overall pass/fail
            if not duplicate_result["passed"] or not thin_result["passed"] or not plagiarism_result["passed"]:
                result["passed"] = False

            result["issues"].extend(duplicate_result.get("issues", []))
            result["issues"].extend(thin_result.get("issues", []))
            result["issues"].extend(plagiarism_result.get("issues", []))

        except Exception as e:
            result["issues"].append(f"Content quality analysis failed: {str(e)}")
            logger.error(f"Content quality analysis error: {e}")

        return result
