"""
AdTicks — Internal link graph + orphan-page analysis.

Builds the internal link graph from a crawl pass and computes:
    - per-page in-degree / out-degree
    - orphan pages (no in-links)
    - simple PageRank-style authority distribution
    - dead-end pages (no out-links)
    - over-linked pages
"""
from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urldefrag, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {"User-Agent": "AdTicksBot/1.0 InternalLinks"}


@dataclass
class LinkRow:
    source_url: str
    target_url: str
    anchor_text: str | None = None
    is_nofollow: bool = False
    link_position: str = "body"  # nav | body | footer | sidebar


@dataclass
class GraphResult:
    edges: list[LinkRow] = field(default_factory=list)
    nodes: set[str] = field(default_factory=set)
    in_degree: dict[str, int] = field(default_factory=dict)
    out_degree: dict[str, int] = field(default_factory=dict)
    orphans: list[str] = field(default_factory=list)
    dead_ends: list[str] = field(default_factory=list)
    page_authority: dict[str, float] = field(default_factory=dict)


def _same_origin(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.replace("www.", "") == urlparse(b).netloc.replace("www.", "")
    except Exception:
        return False


def _link_position(tag) -> str:
    """Heuristic — walks ancestors looking for nav/footer/header/aside markers."""
    for parent in tag.parents:
        name = getattr(parent, "name", None)
        if name in ("nav", "footer", "header", "aside"):
            return name if name != "header" else "body"
        cls = " ".join(parent.get("class", []) if hasattr(parent, "get") else []).lower()
        if any(k in cls for k in ("nav", "menu", "sidebar")):
            return "nav" if "nav" in cls or "menu" in cls else "sidebar"
        if "footer" in cls:
            return "footer"
    return "body"


def parse_links_for_page(html: str, base_url: str) -> list[LinkRow]:
    """Parse a single page's <a> tags and return LinkRow rows for same-origin links."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[LinkRow] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        full = urljoin(base_url, href)
        full, _ = urldefrag(full)
        if not full.startswith(("http://", "https://")):
            continue
        if not _same_origin(base_url, full):
            continue
        rel = " ".join(a.get("rel", [])).lower() if a.get("rel") else ""
        rows.append(LinkRow(
            source_url=base_url,
            target_url=full,
            anchor_text=(a.get_text() or "").strip()[:1024] or None,
            is_nofollow="nofollow" in rel,
            link_position=_link_position(a),
        ))
    return rows


async def build_graph_from_urls(urls: list[str], concurrency: int = 5) -> GraphResult:
    """Fetch each URL and build the in-memory link graph."""
    if not urls:
        return GraphResult()
    sem = asyncio.Semaphore(concurrency)

    async def fetch(client, url):
        async with sem:
            try:
                r = await client.get(url, follow_redirects=True, timeout=10)
                if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
                    return url, r.text
            except Exception as e:
                logger.debug("internal-link fetch failed for %s: %s", url, e)
            return url, None

    rows: list[LinkRow] = []
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        results = await asyncio.gather(*(fetch(client, u) for u in urls))
    for url, html in results:
        if not html:
            continue
        rows.extend(parse_links_for_page(html, url))
    return analyze_graph(rows, all_pages=set(urls))


def analyze_graph(rows: list[LinkRow], all_pages: set[str] | None = None) -> GraphResult:
    """Compute degree, orphans, dead-ends, and approximate page authority."""
    edges = list(rows)
    nodes: set[str] = set()
    in_deg: dict[str, int] = defaultdict(int)
    out_deg: dict[str, int] = defaultdict(int)
    for e in edges:
        nodes.add(e.source_url)
        nodes.add(e.target_url)
        in_deg[e.target_url] += 1
        out_deg[e.source_url] += 1
    if all_pages:
        nodes |= all_pages

    orphans = sorted(p for p in nodes if in_deg.get(p, 0) == 0 and (not all_pages or p in all_pages))
    dead_ends = sorted(p for p in nodes if out_deg.get(p, 0) == 0 and (not all_pages or p in all_pages))

    # Cheap authority estimate: log(in_degree + 1) normalized
    import math
    max_in = max((in_deg.get(p, 0) for p in nodes), default=0)
    pa: dict[str, float] = {}
    for p in nodes:
        if max_in == 0:
            pa[p] = 0.0
        else:
            pa[p] = round(math.log(in_deg.get(p, 0) + 1) / math.log(max_in + 1) * 100, 1)

    return GraphResult(
        edges=edges,
        nodes=nodes,
        in_degree=dict(in_deg),
        out_degree=dict(out_deg),
        orphans=orphans,
        dead_ends=dead_ends,
        page_authority=pa,
    )
