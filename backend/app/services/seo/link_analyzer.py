"""
Advanced link analysis for technical SEO audits.
Includes broken link detection, redirect chain analysis, and link metrics.
"""

import asyncio
import logging
from typing import Dict, Any, List, Set, Tuple
from urllib.parse import urljoin, urlparse
from collections import defaultdict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# HTTP status codes for link classification
OK_STATUSES = {200, 203, 206}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
CLIENT_ERROR_STATUSES = {400, 401, 403, 404, 405}
SERVER_ERROR_STATUSES = {500, 502, 503, 504}
GONE_STATUSES = {410}

# Link quality indicators (simplified PageRank-like scoring)
TOXIC_DOMAINS = {
    'bit.ly', 'tinyurl.com', 'ow.ly', 'goo.gl',  # URL shorteners
}

QUALITY_DOMAINS = {
    'wikipedia.org', 'github.com', 'stackoverflow.com', 'medium.com',
    'edu', 'gov',  # Educational and government domains
}


class LinkAnalyzer:
    """Analyzes links in a page including broken links, redirects, and quality."""
    
    def __init__(self, root_url: str, timeout: float = 15.0, max_links: int = 500):
        """
        Initialize link analyzer.
        
        Args:
            root_url: Base URL to analyze (e.g., https://example.com)
            timeout: Request timeout in seconds
            max_links: Maximum number of links to check (prevent resource exhaustion)
        """
        self.root_url = root_url
        self.timeout = timeout
        self.max_links = max_links
        self.parsed_root = urlparse(root_url)
        
    async def check_broken_links(self, html_content: str) -> Dict[str, Any]:
        """
        Detect broken links (404s, 410s, timeouts) in page HTML.
        
        Returns:
            {
                "broken_count": int,
                "broken_links": [{"url": str, "status": int, "text": str}],
                "redirects_count": int,
                "unreachable_count": int,
                "internal_checked": int,
                "external_checked": int,
            }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = self._extract_links(soup)
        
        broken_links = []
        redirects_count = 0
        unreachable_count = 0
        internal_checked = 0
        external_checked = 0
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            # Check links in batches to avoid overwhelming the server
            batch_size = 10
            for i in range(0, min(len(links), self.max_links), batch_size):
                batch = links[i:i+batch_size]
                tasks = [self._check_link(client, link) for link in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for link_url, link_text, result in zip([l[0] for l in batch], [l[1] for l in batch], results):
                    if isinstance(result, Exception):
                        unreachable_count += 1
                        broken_links.append({
                            "url": link_url,
                            "status": 0,
                            "text": link_text,
                            "error": str(result)
                        })
                        continue
                    
                    status = result
                    is_internal = self._is_internal_link(link_url)
                    
                    if is_internal:
                        internal_checked += 1
                    else:
                        external_checked += 1
                    
                    if status in CLIENT_ERROR_STATUSES or status in SERVER_ERROR_STATUSES or status in GONE_STATUSES:
                        broken_links.append({
                            "url": link_url,
                            "status": status,
                            "text": link_text
                        })
                    elif status in REDIRECT_STATUSES:
                        redirects_count += 1
        
        return {
            "broken_count": len(broken_links),
            "broken_links": broken_links[:20],  # Return top 20 for display
            "redirects_count": redirects_count,
            "unreachable_count": unreachable_count,
            "internal_checked": internal_checked,
            "external_checked": external_checked,
            "total_checked": internal_checked + external_checked,
            "passed": len(broken_links) == 0,  # Pass if no broken links
        }
    
    async def analyze_redirect_chains(self, test_url: str = None) -> Dict[str, Any]:
        """
        Analyze redirect chains for loops, excessive hops, and protocol mixing.
        
        Args:
            test_url: Optional specific URL to test; uses root_url if not provided
            
        Returns:
            {
                "max_chain_length": int,
                "chains": [{"url": str, "hops": int, "statuses": [int], "has_loop": bool, "mixed_protocol": bool}],
                "issues": [str],
                "passed": bool,
            }
        """
        test_urls = [test_url or self.root_url]
        chains = []
        issues = []
        max_chain_length = 0
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            for url in test_urls:
                chain = await self._trace_redirects(client, url)
                chains.append(chain)
                
                if chain["has_loop"]:
                    issues.append(f"Redirect loop detected: {url}")
                if chain["hops"] > 3:
                    issues.append(f"Excessive redirects ({chain['hops']} hops): {url}")
                if chain["mixed_protocol"]:
                    issues.append(f"Mixed protocol redirects: {url}")
                
                max_chain_length = max(max_chain_length, chain["hops"])
        
        passed = len(issues) == 0 and max_chain_length <= 3
        
        return {
            "max_chain_length": max_chain_length,
            "chains": chains,
            "issues": issues,
            "passed": passed,
        }
    
    async def analyze_link_metrics(self, html_content: str) -> Dict[str, Any]:
        """
        Analyze external and internal links with quality scoring.
        
        Returns:
            {
                "internal_links": int,
                "external_links": int,
                "toxic_links": int,
                "quality_external_links": int,
                "nofollow_external": int,
                "external_domains": [str],
                "top_external_domains": [{"domain": str, "count": int, "quality": str}],
                "passed": bool,
            }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        internal_count = 0
        external_count = 0
        toxic_count = 0
        quality_count = 0
        nofollow_count = 0
        domain_counts = defaultdict(int)
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            full_url = urljoin(self.root_url, href)
            is_internal = self._is_internal_link(full_url)
            
            if is_internal:
                internal_count += 1
            else:
                external_count += 1
                domain = urlparse(full_url).netloc
                domain_counts[domain] += 1
                
                # Check quality
                is_toxic = any(toxic in domain.lower() for toxic in TOXIC_DOMAINS)
                is_quality = any(quality in domain.lower() for quality in QUALITY_DOMAINS)
                
                if is_toxic:
                    toxic_count += 1
                elif is_quality:
                    quality_count += 1
                
                # Check rel="nofollow"
                rel = link.get('rel', [])
                if 'nofollow' in rel:
                    nofollow_count += 1
        
        # Get top external domains
        top_domains = sorted(
            domain_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        top_external = []
        for domain, count in top_domains:
            is_toxic = any(toxic in domain.lower() for toxic in TOXIC_DOMAINS)
            is_quality = any(quality in domain.lower() for quality in QUALITY_DOMAINS)
            quality = "toxic" if is_toxic else ("quality" if is_quality else "neutral")
            top_external.append({"domain": domain, "count": count, "quality": quality})
        
        # Scoring: prefer internal links, quality external links, avoid toxic
        passed = (
            internal_count >= external_count * 0.5 and  # At least 33% internal
            toxic_count <= external_count * 0.1  # Less than 10% toxic
        )
        
        return {
            "internal_links": internal_count,
            "external_links": external_count,
            "toxic_links": toxic_count,
            "quality_external_links": quality_count,
            "nofollow_external": nofollow_count,
            "external_domains": len(domain_counts),
            "top_external_domains": top_external,
            "passed": passed,
        }
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extract all links from HTML with their text."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            full_url = urljoin(self.root_url, href)
            link_text = link.get_text(strip=True)[:100]  # Truncate text to 100 chars
            links.append((full_url, link_text))
        
        return links[:self.max_links]
    
    def _is_internal_link(self, url: str) -> bool:
        """Check if URL is internal (same domain)."""
        parsed = urlparse(url)
        return parsed.netloc.lower() == self.parsed_root.netloc.lower()
    
    async def _check_link(self, client: httpx.AsyncClient, link: Tuple[str, str]) -> int:
        """
        Check a single link and return its status code.
        
        Returns status code or raises exception if unreachable.
        """
        url, _ = link
        try:
            response = await client.head(url, follow_redirects=False)
            return response.status_code
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
            raise
    
    async def _trace_redirects(self, client: httpx.AsyncClient, url: str, max_hops: int = 10) -> Dict[str, Any]:
        """
        Trace redirect chain for a URL.
        
        Returns:
            {
                "url": str,
                "hops": int,
                "statuses": [int],
                "final_url": str,
                "has_loop": bool,
                "mixed_protocol": bool,
            }
        """
        visited_urls = set()
        statuses = []
        current_url = url
        mixed_protocol = False
        initial_protocol = urlparse(url).scheme
        
        for _ in range(max_hops):
            if current_url in visited_urls:
                # Loop detected
                return {
                    "url": url,
                    "hops": len(statuses),
                    "statuses": statuses,
                    "final_url": current_url,
                    "has_loop": True,
                    "mixed_protocol": mixed_protocol,
                }
            
            visited_urls.add(current_url)
            
            try:
                response = await client.get(
                    current_url,
                    follow_redirects=False,
                )
                statuses.append(response.status_code)
                
                # Check for protocol mixing
                current_protocol = urlparse(current_url).scheme
                if current_protocol != initial_protocol:
                    mixed_protocol = True
                
                if response.status_code not in REDIRECT_STATUSES:
                    # Not a redirect, chain ended
                    return {
                        "url": url,
                        "hops": len(statuses),
                        "statuses": statuses,
                        "final_url": current_url,
                        "has_loop": False,
                        "mixed_protocol": mixed_protocol,
                    }
                
                # Follow redirect
                location = response.headers.get("location")
                if not location:
                    break
                
                current_url = urljoin(current_url, location)
                
            except Exception:
                return {
                    "url": url,
                    "hops": len(statuses),
                    "statuses": statuses,
                    "final_url": current_url,
                    "has_loop": False,
                    "mixed_protocol": mixed_protocol,
                }
        
        return {
            "url": url,
            "hops": len(statuses),
            "statuses": statuses,
            "final_url": current_url,
            "has_loop": False,
            "mixed_protocol": mixed_protocol,
        }
