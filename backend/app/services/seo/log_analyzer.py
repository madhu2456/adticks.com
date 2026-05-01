"""
AdTicks — Log file analyzer for bot crawl analytics.

Parses Apache/Nginx Combined Log Format and extracts bot hits per URL,
status code distribution, crawl waste (4xx/5xx ratio), orphan pages
(crawled by bot but not in sitemap), and crawl frequency by section.

Equivalent to SEMrush Log File Analyzer / Screaming Frog Log Analyser.
"""
from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Combined log format regex
COMBINED_LOG = re.compile(
    r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<url>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)"'
)

BOT_PATTERNS = {
    "googlebot": re.compile(r"Googlebot|AdsBot-Google|Mediapartners", re.I),
    "bingbot": re.compile(r"Bingbot|MSNBot", re.I),
    "yandexbot": re.compile(r"YandexBot", re.I),
    "duckduckbot": re.compile(r"DuckDuckBot", re.I),
    "baidu": re.compile(r"Baiduspider", re.I),
    "applebot": re.compile(r"Applebot", re.I),
    "facebook": re.compile(r"facebookexternalhit", re.I),
    "ahrefsbot": re.compile(r"AhrefsBot", re.I),
    "semrushbot": re.compile(r"SemrushBot", re.I),
    "openai": re.compile(r"GPTBot|OAI-SearchBot|ChatGPT-User", re.I),
    "anthropic": re.compile(r"ClaudeBot|anthropic-ai", re.I),
    "perplexity": re.compile(r"PerplexityBot", re.I),
}


@dataclass
class LogParseResult:
    aggregated: list[dict[str, Any]]
    summary: dict[str, Any]


def detect_bot(ua: str) -> str | None:
    for name, pat in BOT_PATTERNS.items():
        if pat.search(ua):
            return name
    return None


def parse_lines(lines: Iterable[str]) -> LogParseResult:
    """Parse lines from a log file. Returns aggregated rows + summary."""
    bucket: dict[tuple[str, str, int], int] = Counter()
    last_seen: dict[tuple[str, str, int], datetime] = {}
    bot_hits: Counter[str] = Counter()
    status_counts: Counter[int] = Counter()
    section_counts: Counter[str] = Counter()
    total = 0

    for line in lines:
        m = COMBINED_LOG.search(line)
        if not m:
            continue
        ua = m.group("ua")
        bot = detect_bot(ua)
        if not bot:
            continue
        url = m.group("url")
        status = int(m.group("status"))
        try:
            ts = datetime.strptime(m.group("time"), "%d/%b/%Y:%H:%M:%S %z")
        except Exception:
            ts = datetime.now(tz=timezone.utc)
        key = (bot, url, status)
        bucket[key] += 1
        last_seen[key] = max(last_seen.get(key, ts), ts)
        bot_hits[bot] += 1
        status_counts[status] += 1
        section = url.split("/")[1] if "/" in url[1:] else "root"
        section_counts[f"/{section}"] += 1
        total += 1

    aggregated: list[dict[str, Any]] = []
    for (bot, url, status), hits in bucket.most_common():
        aggregated.append({
            "bot": bot,
            "url": url,
            "status_code": status,
            "hits": hits,
            "last_crawled": last_seen.get((bot, url, status)),
        })

    waste = sum(c for s, c in status_counts.items() if s >= 400)
    summary = {
        "total_hits": total,
        "unique_urls": len({k[1] for k in bucket.keys()}),
        "bots": dict(bot_hits),
        "status_distribution": {str(s): c for s, c in status_counts.items()},
        "crawl_waste_pct": round((waste / total) * 100, 1) if total else 0.0,
        "top_sections": dict(section_counts.most_common(10)),
    }
    return LogParseResult(aggregated=aggregated, summary=summary)


def detect_orphans(crawled_urls: set[str], sitemap_urls: set[str]) -> dict[str, list[str]]:
    """Compare crawled URLs (from logs) against URLs in sitemap.xml."""
    return {
        "crawled_not_in_sitemap": sorted(crawled_urls - sitemap_urls),
        "in_sitemap_not_crawled": sorted(sitemap_urls - crawled_urls),
    }
