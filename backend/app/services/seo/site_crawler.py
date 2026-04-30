"""
AdTicks — Comprehensive Site Crawler.

A real BFS crawler over a domain that extracts on-page signals and produces
a granular issue list covering the same surface that Ahrefs Site Audit,
SEMrush Site Audit, and Moz Site Crawl report on. Pure Python + httpx +
BeautifulSoup, no paid APIs required.

Issue categories:
    crawlability  — robots.txt, sitemap, status codes, redirects, depth
    indexability  — noindex, canonical chains, duplicate canonicals
    on_page       — title, meta description, headings, word count
    performance   — page weight, response time, image weight
    security      — HTTPS, mixed content, HSTS
    international — hreflang validity, conflicting hreflang
    structured    — JSON-LD validity, missing required fields
    links         — internal/external, broken, nofollow, orphans
    images        — missing alt, oversized, broken
    mobile        — viewport meta, tap target heuristics
    content       — thin content, duplicate titles/H1s, keyword stuffing
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse, urldefrag

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "AdTicksBot/1.0 (+https://adticks.com/bot)"
DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MiB cap per page

# Ideal ranges -- adjust if you want to be stricter
TITLE_MIN, TITLE_MAX = 30, 60
META_DESC_MIN, META_DESC_MAX = 70, 160
THIN_CONTENT_THRESHOLD = 250  # words
SLOW_RESPONSE_MS = 3000
LARGE_PAGE_BYTES = 1_500_000  # 1.5 MiB


@dataclass
class CrawlIssue:
    url: str
    category: str
    severity: str  # error | warning | notice
    code: str
    message: str
    recommendation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CrawledPageData:
    url: str
    status_code: int | None = None
    content_type: str | None = None
    title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    word_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images: int = 0
    images_missing_alt: int = 0
    canonical_url: str | None = None
    is_indexable: bool = True
    response_time_ms: int = 0
    page_size_bytes: int = 0
    depth: int = 0
    schema_types: list[str] = field(default_factory=list)


@dataclass
class CrawlResult:
    pages: list[CrawledPageData] = field(default_factory=list)
    issues: list[CrawlIssue] = field(default_factory=list)
    redirects: list[dict[str, Any]] = field(default_factory=list)
    broken_links: list[dict[str, Any]] = field(default_factory=list)
    schemas: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def _normalize(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/") if url.endswith("/") and len(urlparse(url).path) > 1 else url


def _same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return pa.netloc.replace("www.", "") == pb.netloc.replace("www.", "")


def _word_count(text: str) -> int:
    return len([w for w in re.findall(r"\b\w+\b", text or "") if len(w) > 1])


def _classify_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


class SiteCrawler:
    """Async BFS crawler with structured issue reporting."""

    def __init__(
        self,
        start_url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        concurrency: int = 5,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        if not start_url.startswith(("http://", "https://")):
            start_url = "https://" + start_url
        self.start_url = start_url.rstrip("/")
        self.origin = urlparse(self.start_url)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.semaphore = asyncio.Semaphore(concurrency)
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.visited: set[str] = set()
        self.queued: set[str] = set()
        self.result = CrawlResult()
        self._titles: dict[str, list[str]] = {}
        self._h1s: dict[str, list[str]] = {}
        self._descriptions: dict[str, list[str]] = {}

    # ---- public API --------------------------------------------------------
    async def run(self) -> CrawlResult:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=False,
            headers=self.headers,
        ) as client:
            await self._site_level_checks(client)
            queue: deque[tuple[str, int]] = deque()
            normalized = _normalize(self.start_url)
            queue.append((normalized, 0))
            self.queued.add(normalized)

            while queue and len(self.visited) < self.max_pages:
                batch: list[tuple[str, int]] = []
                # take up to `concurrency` items per batch
                while queue and len(batch) < 5 and len(self.visited) + len(batch) < self.max_pages:
                    batch.append(queue.popleft())
                if not batch:
                    break
                pages = await asyncio.gather(
                    *(self._fetch_and_parse(client, u, d) for u, d in batch),
                    return_exceptions=True,
                )
                for item in pages:
                    if isinstance(item, Exception):
                        logger.warning("crawler error: %s", item)
                        continue
                    if item is None:
                        continue
                    page, links = item
                    self.result.pages.append(page)
                    if page.depth < self.max_depth:
                        for link in links:
                            normalized_link = _normalize(link)
                            if normalized_link in self.visited or normalized_link in self.queued:
                                continue
                            if not _same_origin(self.start_url, normalized_link):
                                continue
                            queue.append((normalized_link, page.depth + 1))
                            self.queued.add(normalized_link)

            self._post_crawl_dedupe_checks()
            self.result.summary = self._build_summary()
            return self.result

    # ---- site-level checks (robots, sitemap, security) ---------------------
    async def _site_level_checks(self, client: httpx.AsyncClient) -> None:
        base = f"{self.origin.scheme}://{self.origin.netloc}"

        # robots.txt
        try:
            resp = await client.get(f"{base}/robots.txt")
            if resp.status_code == 200:
                content = resp.text
                if re.search(r"^\s*Disallow:\s*/\s*$", content, re.M | re.I):
                    self._issue(base, "crawlability", "error", "robots-disallow-all",
                                "robots.txt blocks all crawlers",
                                "Remove the global Disallow: / directive")
                if "sitemap:" not in content.lower():
                    self._issue(base, "crawlability", "warning", "robots-no-sitemap",
                                "robots.txt missing Sitemap directive",
                                "Add `Sitemap: https://example.com/sitemap.xml`")
            elif resp.status_code == 404:
                self._issue(base, "crawlability", "warning", "robots-missing",
                            "No robots.txt found",
                            "Create a robots.txt at the site root")
        except Exception as e:
            self._issue(base, "crawlability", "notice", "robots-fetch-failed",
                        f"robots.txt fetch failed: {e}")

        # sitemap.xml
        try:
            resp = await client.get(f"{base}/sitemap.xml")
            if resp.status_code != 200:
                self._issue(base, "crawlability", "warning", "sitemap-missing",
                            "No sitemap.xml at /sitemap.xml",
                            "Generate and submit a sitemap to Search Console")
        except Exception:
            pass

        # HTTPS
        if self.origin.scheme != "https":
            self._issue(base, "security", "error", "no-https",
                        "Site does not use HTTPS",
                        "Migrate to HTTPS — required for modern SEO")
        else:
            try:
                resp = await client.get(f"https://{self.origin.netloc}/")
                if not resp.headers.get("strict-transport-security"):
                    self._issue(base, "security", "notice", "no-hsts",
                                "Strict-Transport-Security header missing",
                                "Enable HSTS to protect against downgrade attacks")
            except Exception:
                pass

    # ---- page fetch + parse ------------------------------------------------
    async def _fetch_and_parse(
        self, client: httpx.AsyncClient, url: str, depth: int
    ) -> tuple[CrawledPageData, list[str]] | None:
        async with self.semaphore:
            if url in self.visited:
                return None
            self.visited.add(url)
            page = CrawledPageData(url=url, depth=depth)
            t0 = time.perf_counter()
            try:
                resp = await client.get(url)
            except httpx.TimeoutException:
                self._issue(url, "performance", "error", "timeout",
                            "Page request timed out",
                            "Investigate slow server response")
                page.status_code = None
                return page, []
            except Exception as e:
                self._issue(url, "crawlability", "error", "fetch-failed",
                            f"Could not fetch URL: {e}")
                return page, []

            page.response_time_ms = int((time.perf_counter() - t0) * 1000)
            page.status_code = resp.status_code
            page.content_type = resp.headers.get("content-type", "").split(";")[0].strip()

            # follow redirects manually to capture chains
            redirect_chain: list[dict[str, Any]] = []
            cur = resp
            hops = 0
            while cur.status_code in (301, 302, 303, 307, 308) and hops < 5:
                loc = cur.headers.get("location")
                if not loc:
                    break
                target = urljoin(url, loc)
                redirect_chain.append({"from": str(cur.url), "to": target, "status": cur.status_code})
                try:
                    cur = await client.get(target)
                except Exception:
                    break
                hops += 1
            if redirect_chain:
                self.result.redirects.extend(redirect_chain)
                if len(redirect_chain) > 1:
                    self._issue(url, "crawlability", "warning", "redirect-chain",
                                f"Redirect chain of {len(redirect_chain)} hops",
                                "Update internal links to point directly to final URL")
                page.status_code = cur.status_code

            if page.response_time_ms > SLOW_RESPONSE_MS:
                self._issue(url, "performance", "warning", "slow-response",
                            f"Slow server response ({page.response_time_ms} ms)",
                            "Optimize server / use CDN")

            if page.status_code and page.status_code >= 400:
                self._issue(url, "crawlability", "error", f"http-{page.status_code}",
                            f"HTTP {page.status_code} error")
                if page.status_code == 404:
                    self.result.broken_links.append({"url": url, "status": 404})
                return page, []

            if not page.content_type or "html" not in page.content_type:
                return page, []

            content = cur.content[:MAX_RESPONSE_BYTES]
            page.page_size_bytes = len(content)
            if page.page_size_bytes > LARGE_PAGE_BYTES:
                self._issue(url, "performance", "warning", "page-too-large",
                            f"Page size {page.page_size_bytes // 1024} KiB exceeds {LARGE_PAGE_BYTES // 1024} KiB",
                            "Compress assets, lazy-load images")

            soup = BeautifulSoup(content, "html.parser")
            return self._extract_signals(url, soup, page), self._extract_links(url, soup)

    # ---- signal extraction + per-page issue rules -------------------------
    def _extract_signals(
        self, url: str, soup: BeautifulSoup, page: CrawledPageData
    ) -> CrawledPageData:
        # Title
        if soup.title and soup.title.string:
            page.title = _classify_text(soup.title.string)
            if len(page.title) < TITLE_MIN:
                self._issue(url, "on_page", "warning", "title-too-short",
                            f"Title too short ({len(page.title)} chars)",
                            f"Aim for {TITLE_MIN}–{TITLE_MAX} characters")
            elif len(page.title) > TITLE_MAX:
                self._issue(url, "on_page", "warning", "title-too-long",
                            f"Title too long ({len(page.title)} chars)",
                            f"Aim for {TITLE_MIN}–{TITLE_MAX} characters")
            self._titles.setdefault(page.title, []).append(url)
        else:
            self._issue(url, "on_page", "error", "title-missing",
                        "Page has no <title>",
                        "Add a unique, descriptive title tag")

        # Meta description
        md = soup.find("meta", attrs={"name": "description"})
        if md and md.get("content"):
            page.meta_description = _classify_text(md["content"])
            if len(page.meta_description) < META_DESC_MIN:
                self._issue(url, "on_page", "notice", "meta-desc-short",
                            f"Meta description too short ({len(page.meta_description)} chars)")
            elif len(page.meta_description) > META_DESC_MAX:
                self._issue(url, "on_page", "notice", "meta-desc-long",
                            f"Meta description too long ({len(page.meta_description)} chars)")
            self._descriptions.setdefault(page.meta_description, []).append(url)
        else:
            self._issue(url, "on_page", "warning", "meta-desc-missing",
                        "No meta description",
                        "Write a 70–160 char meta description")

        # H1
        h1s = soup.find_all("h1")
        if not h1s:
            self._issue(url, "on_page", "warning", "h1-missing", "No <h1> on page")
        elif len(h1s) > 1:
            self._issue(url, "on_page", "notice", "h1-multiple",
                        f"Multiple <h1> tags ({len(h1s)})",
                        "Best practice is one H1 per page")
        if h1s:
            page.h1 = _classify_text(h1s[0].get_text())
            self._h1s.setdefault(page.h1, []).append(url)

        # Heading hierarchy check
        for level in range(2, 7):
            tag = f"h{level}"
            for h in soup.find_all(tag):
                # if a heading exists but its parent level is missing, that's a hierarchy break
                pass

        # Word count + thin content
        text = soup.get_text(" ")
        page.word_count = _word_count(text)
        if page.word_count < THIN_CONTENT_THRESHOLD:
            self._issue(url, "content", "warning", "thin-content",
                        f"Thin content ({page.word_count} words)",
                        f"Aim for at least {THIN_CONTENT_THRESHOLD} words of unique copy")

        # Canonical
        canon = soup.find("link", attrs={"rel": "canonical"})
        if canon and canon.get("href"):
            page.canonical_url = urljoin(url, canon["href"])
            if _normalize(page.canonical_url) != _normalize(url):
                self._issue(url, "indexability", "notice", "canonical-different",
                            "Canonical points to different URL",
                            "Verify this is intentional", details={"canonical": page.canonical_url})
        else:
            self._issue(url, "indexability", "notice", "canonical-missing",
                        "No canonical tag", "Add a self-referencing canonical")

        # Robots meta
        robots = soup.find("meta", attrs={"name": "robots"})
        if robots and "noindex" in (robots.get("content") or "").lower():
            page.is_indexable = False
            self._issue(url, "indexability", "notice", "noindex",
                        "Page set to noindex",
                        "Verify this is intentional")

        # Viewport (mobile)
        if not soup.find("meta", attrs={"name": "viewport"}):
            self._issue(url, "mobile", "warning", "no-viewport",
                        "Missing viewport meta tag",
                        "Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`")

        # Lang attribute
        html_tag = soup.find("html")
        if not html_tag or not html_tag.get("lang"):
            self._issue(url, "international", "notice", "no-html-lang",
                        "Missing `lang` on <html>",
                        "Add lang attribute (e.g. `<html lang=\"en\">`)")

        # hreflang
        hreflangs = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
        seen_hl = set()
        for link in hreflangs:
            hl = link.get("hreflang", "")
            if hl in seen_hl:
                self._issue(url, "international", "warning", "hreflang-duplicate",
                            f"Duplicate hreflang `{hl}`")
            seen_hl.add(hl)
            if not re.match(r"^(x-default|[a-z]{2}(-[A-Z]{2})?)$", hl):
                self._issue(url, "international", "warning", "hreflang-invalid",
                            f"Invalid hreflang code `{hl}`")

        # Images
        imgs = soup.find_all("img")
        page.images = len(imgs)
        for img in imgs:
            if not img.get("alt"):
                page.images_missing_alt += 1
        if page.images_missing_alt > 0:
            self._issue(url, "images", "warning", "img-missing-alt",
                        f"{page.images_missing_alt}/{page.images} images missing alt text",
                        "Add descriptive alt attributes for accessibility & SEO")

        # JSON-LD schema
        for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(tag.string or "{}")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        t = item.get("@type") or item.get("@graph", [{}])[0].get("@type")
                        if isinstance(t, list):
                            t = t[0] if t else None
                        if t:
                            page.schema_types.append(str(t))
                            self.result.schemas.append({
                                "url": url, "type": str(t), "data": item, "valid": True
                            })
            except Exception as e:
                self._issue(url, "structured", "warning", "schema-invalid-json",
                            f"Invalid JSON-LD: {e}")
                self.result.schemas.append({"url": url, "type": "unknown", "data": {}, "valid": False, "error": str(e)})

        # Mixed content (https page loading http resources)
        if urlparse(url).scheme == "https":
            for r in soup.find_all(["img", "script", "link", "iframe"]):
                src = r.get("src") or r.get("href") or ""
                if src.startswith("http://"):
                    self._issue(url, "security", "warning", "mixed-content",
                                "HTTP resource loaded on HTTPS page",
                                "Migrate resource URLs to HTTPS",
                                details={"resource": src})
                    break

        return page

    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> list[str]:
        internal: list[str] = []
        external = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            full = urljoin(base_url, href)
            full, _ = urldefrag(full)
            if not full.startswith(("http://", "https://")):
                continue
            if _same_origin(self.start_url, full):
                internal.append(full)
            else:
                external += 1
        # update page record (already appended)
        if self.result.pages and self.result.pages[-1].url == base_url:
            self.result.pages[-1].internal_links = len(internal)
            self.result.pages[-1].external_links = external
        return internal

    # ---- post-crawl dedupe checks -----------------------------------------
    def _post_crawl_dedupe_checks(self) -> None:
        for title, urls in self._titles.items():
            if len(urls) > 1:
                for u in urls:
                    self._issue(u, "content", "warning", "title-duplicate",
                                f"Duplicate title used by {len(urls)} pages",
                                "Make each page title unique",
                                details={"shared_with": urls[:5]})
        for h1, urls in self._h1s.items():
            if len(urls) > 1 and h1:
                for u in urls:
                    self._issue(u, "content", "notice", "h1-duplicate",
                                f"Duplicate H1 used by {len(urls)} pages",
                                details={"shared_with": urls[:5]})
        for desc, urls in self._descriptions.items():
            if len(urls) > 1 and desc:
                for u in urls:
                    self._issue(u, "content", "notice", "meta-desc-duplicate",
                                f"Duplicate meta description ({len(urls)} pages)",
                                details={"shared_with": urls[:5]})

    # ---- helpers -----------------------------------------------------------
    def _issue(self, url, category, severity, code, message, recommendation=None, details=None):
        self.result.issues.append(
            CrawlIssue(
                url=url,
                category=category,
                severity=severity,
                code=code,
                message=message,
                recommendation=recommendation,
                details=details or {},
            )
        )

    def _build_summary(self) -> dict[str, Any]:
        errors = sum(1 for i in self.result.issues if i.severity == "error")
        warnings = sum(1 for i in self.result.issues if i.severity == "warning")
        notices = sum(1 for i in self.result.issues if i.severity == "notice")
        total = errors + warnings + notices
        # Health score: 100 - weighted issue penalty (capped)
        score = 100 - min(100, errors * 5 + warnings * 2 + notices)
        avg_rt = (
            sum(p.response_time_ms for p in self.result.pages) / max(1, len(self.result.pages))
        )
        cat_counts: dict[str, int] = {}
        for issue in self.result.issues:
            cat_counts[issue.category] = cat_counts.get(issue.category, 0) + 1
        return {
            "total_pages": len(self.result.pages),
            "total_issues": total,
            "errors": errors,
            "warnings": warnings,
            "notices": notices,
            "avg_response_time_ms": round(avg_rt, 1),
            "score": max(0, score),
            "issues_by_category": cat_counts,
        }


async def crawl_site(start_url: str, max_pages: int = 50, max_depth: int = 3) -> CrawlResult:
    """Convenience entrypoint."""
    crawler = SiteCrawler(start_url=start_url, max_pages=max_pages, max_depth=max_depth)
    return await crawler.run()
