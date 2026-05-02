"""
Privacy-safe web spider for bot crawl analysis.

Crawls a website directly (instead of requiring access logs) and analyzes:
- Bot crawl patterns (response codes, redirects, crawl frequency)
- Orphan pages (crawled but not in sitemap)
- Crawl efficiency and waste

Uses configurable User-Agent headers to simulate different bots.
Respects robots.txt and enforces rate limiting.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Bot User-Agent patterns for simulation
BOT_USER_AGENTS = {
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "bingbot": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "yandexbot": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    "duckduckbot": "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)",
    "baiduspider": "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "applebot": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) AppleWebKit/537.36 (compatible; Applebot/0.1)",
    "facebookbot": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "ahrefsbot": "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "semrushbot": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
}


@dataclass
class CrawlResult:
    """Single page crawl result."""
    url: str
    status_code: int
    response_time_ms: float
    bot_name: str
    redirect_to: str | None = None
    crawl_timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    error: str | None = None


@dataclass
class SpiderStats:
    """Summary statistics from a crawl session."""
    total_urls_crawled: int
    unique_urls: int
    status_distribution: dict[int, int]
    avg_response_time_ms: float
    crawl_waste_pct: float
    top_status_codes: dict[str, int]
    crawl_errors: int


class RobotsParser:
    """Simple robots.txt parser."""

    def __init__(self, robots_txt: str):
        self.rules: dict[str, list[str]] = {"*": [], "googlebot": []}
        self._parse(robots_txt)

    def _parse(self, content: str) -> None:
        """Parse robots.txt content."""
        current_agent = None
        for line in content.split("\n"):
            line = line.strip().split("#")[0].strip()
            if not line:
                continue
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip().lower()
                if current_agent not in self.rules:
                    self.rules[current_agent] = []
            elif line.lower().startswith("disallow:") and current_agent:
                path = line.split(":", 1)[1].strip()
                self.rules[current_agent].append(path)

    def is_allowed(self, path: str, bot: str = "*") -> bool:
        """Check if a path is allowed for a bot."""
        # Check bot-specific rules first, then fallback to *
        agents_to_check = [bot.lower()] if bot.lower() != "*" else ["*"]
        if bot.lower() != "*":
            agents_to_check.append("*")

        for agent in agents_to_check:
            if agent in self.rules:
                for disallowed in self.rules[agent]:
                    if not disallowed:  # Empty disallow = allow all
                        continue
                    if path.startswith(disallowed):
                        return False
        return True


class WebSpider:
    """Privacy-safe web spider for crawl analysis."""

    def __init__(
        self,
        domain: str,
        bot_name: str = "googlebot",
        max_urls: int = 1000,
        max_depth: int = 5,
        timeout_seconds: int = 60,
        rate_limit_per_second: float = 2.0,
    ):
        self.domain = domain.rstrip("/")
        self.bot_name = bot_name.lower()
        self.user_agent = BOT_USER_AGENTS.get(self.bot_name, BOT_USER_AGENTS["googlebot"])
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.timeout_seconds = timeout_seconds
        self.rate_limit_per_second = rate_limit_per_second

        self.crawled_urls: set[str] = set()
        self.to_crawl: list[tuple[str, int]] = []  # (url, depth)
        self.results: list[CrawlResult] = []
        self.robots_parser: RobotsParser | None = None
        self._request_times: list[float] = []

    async def crawl(self) -> list[CrawlResult]:
        """Start crawling the domain."""
        # Fetch and parse robots.txt
        await self._fetch_robots_txt()

        # Start with domain root
        self.to_crawl.append((self.domain, 0))

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while self.to_crawl and len(self.crawled_urls) < self.max_urls:
                url, depth = self.to_crawl.pop(0)

                if url in self.crawled_urls or depth > self.max_depth:
                    continue

                # Rate limiting
                await self._rate_limit()

                self.crawled_urls.add(url)
                result = await self._fetch_url(client, url)
                self.results.append(result)

                # Extract links from successful responses and add to crawl queue
                if result.status_code == 200 and depth < self.max_depth:
                    new_urls = await self._extract_links(client, url, depth + 1)
                    self.to_crawl.extend(new_urls)

        return self.results

    async def _fetch_robots_txt(self) -> None:
        """Fetch and parse robots.txt."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.domain}/robots.txt",
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    self.robots_parser = RobotsParser(resp.text)
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt: {e}")

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        self._request_times = [t for t in self._request_times if now - t < 1.0]

        if len(self._request_times) >= self.rate_limit_per_second:
            sleep_time = 1.0 - (now - self._request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self._request_times = []

        self._request_times.append(asyncio.get_event_loop().time())

    async def _fetch_url(self, client: httpx.AsyncClient, url: str) -> CrawlResult:
        """Fetch a single URL and return crawl result."""
        start_time = asyncio.get_event_loop().time()

        try:
            resp = await client.get(
                url,
                headers={"User-Agent": self.user_agent},
                follow_redirects=False,
            )
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            redirect_to = None
            if resp.status_code in (301, 302, 303, 307, 308):
                redirect_to = resp.headers.get("location")

            return CrawlResult(
                url=url,
                status_code=resp.status_code,
                response_time_ms=elapsed_ms,
                bot_name=self.bot_name,
                redirect_to=redirect_to,
            )
        except Exception as e:
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return CrawlResult(
                url=url,
                status_code=0,
                response_time_ms=elapsed_ms,
                bot_name=self.bot_name,
                error=str(e),
            )

    async def _extract_links(
        self, client: httpx.AsyncClient, url: str, depth: int
    ) -> list[tuple[str, int]]:
        """Extract links from a page."""
        new_urls = []
        try:
            resp = await client.get(
                url,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                soup = BeautifulSoup(resp.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    absolute_url = urljoin(url, href)
                    parsed = urlparse(absolute_url)

                    # Only crawl same domain, ignore fragments and queries
                    if urlparse(self.domain).netloc == parsed.netloc:
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if clean_url not in self.crawled_urls:
                            # Check robots.txt
                            if self.robots_parser:
                                if not self.robots_parser.is_allowed(parsed.path, self.bot_name):
                                    continue

                            new_urls.append((clean_url, depth))
        except Exception as e:
            logger.debug(f"Error extracting links from {url}: {e}")

        return new_urls

    def get_stats(self) -> SpiderStats:
        """Calculate statistics from crawl results."""
        if not self.results:
            return SpiderStats(
                total_urls_crawled=0,
                unique_urls=0,
                status_distribution={},
                avg_response_time_ms=0.0,
                crawl_waste_pct=0.0,
                top_status_codes={},
                crawl_errors=0,
            )

        status_counts: dict[int, int] = {}
        total_time = 0.0
        error_count = 0

        for result in self.results:
            status_counts[result.status_code] = status_counts.get(result.status_code, 0) + 1
            total_time += result.response_time_ms
            if result.error:
                error_count += 1

        waste = sum(c for s, c in status_counts.items() if s >= 400)
        total = len(self.results)

        return SpiderStats(
            total_urls_crawled=total,
            unique_urls=len(self.crawled_urls),
            status_distribution=status_counts,
            avg_response_time_ms=total_time / total if total else 0.0,
            crawl_waste_pct=round((waste / total) * 100, 1) if total else 0.0,
            top_status_codes={str(s): c for s, c in sorted(status_counts.items(), key=lambda x: x[1], reverse=True)[:5]},
            crawl_errors=error_count,
        )
