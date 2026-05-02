"""Sitemap fetcher for orphan page detection."""
from __future__ import annotations

import logging
from typing import Set
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SitemapFetcher:
    """Fetch and parse sitemap.xml files."""

    def __init__(self, domain: str, timeout_seconds: int = 30):
        self.domain = domain.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def fetch_urls(self) -> set[str]:
        """Fetch all URLs from sitemap.xml and sitemap index files."""
        urls: set[str] = set()

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Try sitemap.xml first
                sitemap_url = f"{self.domain}/sitemap.xml"
                resp = await client.get(sitemap_url, follow_redirects=True)

                if resp.status_code == 200:
                    # Check if it's a sitemap index
                    if self._is_sitemap_index(resp.text):
                        # Extract sitemap URLs and fetch each
                        sitemaps = self._extract_sitemaps(resp.text, self.domain)
                        for sitemap in sitemaps:
                            sitemap_urls = await self._fetch_sitemap(client, sitemap)
                            urls.update(sitemap_urls)
                    else:
                        # Regular sitemap
                        parsed_urls = self._extract_urls(resp.text)
                        urls.update(parsed_urls)
                else:
                    logger.warning(f"Sitemap not found at {sitemap_url} (status: {resp.status_code})")
        except Exception as e:
            logger.error(f"Error fetching sitemap: {e}")

        return urls

    async def _fetch_sitemap(self, client: httpx.AsyncClient, sitemap_url: str) -> set[str]:
        """Fetch a single sitemap file."""
        try:
            resp = await client.get(sitemap_url, follow_redirects=True)
            if resp.status_code == 200:
                return self._extract_urls(resp.text)
        except Exception as e:
            logger.warning(f"Error fetching sitemap {sitemap_url}: {e}")
        return set()

    def _is_sitemap_index(self, content: str) -> bool:
        """Check if the sitemap is an index (contains sitemap URLs, not page URLs)."""
        return "<sitemapindex" in content.lower()

    def _extract_sitemaps(self, content: str, domain: str) -> list[str]:
        """Extract sitemap URLs from sitemap index."""
        sitemaps = []
        try:
            soup = BeautifulSoup(content, "xml")
            for sitemap in soup.find_all("sitemap"):
                loc = sitemap.find("loc")
                if loc:
                    sitemaps.append(loc.text.strip())
        except Exception as e:
            logger.warning(f"Error parsing sitemap index: {e}")
        return sitemaps

    def _extract_urls(self, content: str) -> set[str]:
        """Extract page URLs from sitemap."""
        urls: set[str] = set()
        try:
            soup = BeautifulSoup(content, "xml")
            for url in soup.find_all("url"):
                loc = url.find("loc")
                if loc:
                    urls.add(loc.text.strip())
        except Exception as e:
            logger.warning(f"Error parsing sitemap: {e}")
        return urls
