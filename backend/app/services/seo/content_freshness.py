"""
Content freshness analysis for technical SEO audits.
Detects staleness indicators, Last-Modified headers, sitemap lastmod dates, and update patterns.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentFreshnessAnalyzer:
    """Analyzes content freshness indicators including Last-Modified headers and sitemap dates."""
    
    # Staleness thresholds (in days)
    FRESH_THRESHOLD = 30  # Updated within 30 days = fresh
    MODERATE_THRESHOLD = 90  # 31-90 days = moderately fresh
    STALE_THRESHOLD = 180  # 91-180 days = stale
    VERY_STALE_THRESHOLD = 365  # 180+ days = very stale
    
    def __init__(self, root_url: str, timeout: float = 15.0):
        """
        Initialize content freshness analyzer.
        
        Args:
            root_url: Base URL to analyze
            timeout: Request timeout in seconds
        """
        self.root_url = root_url
        self.timeout = timeout
        self.parsed_root = urlparse(root_url)
    
    async def analyze_page_freshness(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """
        Analyze freshness of a specific page.
        
        Returns:
            {
                "url": str,
                "last_modified": str | None,
                "last_modified_date": datetime | None,
                "age_days": int | None,
                "freshness_level": str,  # "fresh", "moderate", "stale", "very_stale", "unknown"
                "server_date": str | None,
                "content_hash": str,  # To detect content changes
            }
        """
        result: Dict[str, Any] = {
            "url": url,
            "last_modified": None,
            "last_modified_date": None,
            "age_days": None,
            "freshness_level": "unknown",
            "server_date": None,
            "content_hash": None,
        }
        
        try:
            response = await client.head(url, follow_redirects=True)
            
            # Get Last-Modified header
            last_modified = response.headers.get("last-modified")
            if last_modified:
                result["last_modified"] = last_modified
                try:
                    # Parse RFC 2822 format: "Wed, 21 Oct 2025 07:28:00 GMT"
                    from email.utils import parsedate_to_datetime
                    mod_date = parsedate_to_datetime(last_modified)
                    result["last_modified_date"] = mod_date.isoformat()
                    
                    # Calculate age
                    now = datetime.utcnow()
                    now_aware = datetime.fromisoformat(now.isoformat() + "+00:00")
                    age_delta = now_aware - mod_date
                    age_days = age_delta.days
                    result["age_days"] = age_days
                    
                    # Determine freshness level
                    if age_days <= self.FRESH_THRESHOLD:
                        result["freshness_level"] = "fresh"
                    elif age_days <= self.MODERATE_THRESHOLD:
                        result["freshness_level"] = "moderate"
                    elif age_days <= self.STALE_THRESHOLD:
                        result["freshness_level"] = "stale"
                    else:
                        result["freshness_level"] = "very_stale"
                
                except Exception as e:
                    logger.warning(f"Failed to parse Last-Modified header for {url}: {e}")
            
            # Get Server date for comparison
            server_date = response.headers.get("date")
            if server_date:
                result["server_date"] = server_date
        
        except Exception as e:
            logger.warning(f"Failed to check page freshness for {url}: {e}")
        
        return result
    
    async def analyze_sitemap_freshness(self, client: httpx.AsyncClient, root_url: str = None) -> Dict[str, Any]:
        """
        Analyze freshness data from XML sitemap (lastmod dates).
        
        Returns:
            {
                "sitemap_url": str,
                "found": bool,
                "last_updated": str | None,
                "urls_analyzed": int,
                "freshness_breakdown": {
                    "fresh": int,
                    "moderate": int,
                    "stale": int,
                    "very_stale": int,
                    "no_date": int,
                },
                "oldest_url": {"url": str, "lastmod": str, "age_days": int},
                "newest_url": {"url": str, "lastmod": str, "age_days": int},
                "average_age_days": float,
                "issues": [str],
            }
        """
        root_url = root_url or self.root_url
        result: Dict[str, Any] = {
            "sitemap_url": f"{root_url}/sitemap.xml",
            "found": False,
            "last_updated": None,
            "urls_analyzed": 0,
            "freshness_breakdown": {
                "fresh": 0,
                "moderate": 0,
                "stale": 0,
                "very_stale": 0,
                "no_date": 0,
            },
            "oldest_url": None,
            "newest_url": None,
            "average_age_days": 0,
            "issues": [],
        }
        
        try:
            sitemap_url = f"{root_url}/sitemap.xml"
            response = await client.get(sitemap_url, follow_redirects=True)
            
            if response.status_code != 200:
                result["issues"].append(f"Sitemap not found or inaccessible ({response.status_code})")
                return result
            
            result["found"] = True
            
            # Parse XML
            soup = BeautifulSoup(response.text, "xml")
            urls = soup.find_all("url")
            
            if not urls:
                result["issues"].append("Sitemap is empty or malformed")
                return result
            
            ages = []
            oldest_entry = None
            newest_entry = None
            oldest_age = -1
            newest_age = float('inf')
            
            for url_elem in urls:
                lastmod_elem = url_elem.find("lastmod")
                if not lastmod_elem or not lastmod_elem.text:
                    result["freshness_breakdown"]["no_date"] += 1
                    continue
                
                lastmod_text = lastmod_elem.text.strip()
                url_text = url_elem.find("loc")
                url_value = url_text.text if url_text else "unknown"
                
                try:
                    # Parse ISO format: "2025-10-21" or "2025-10-21T07:28:00Z"
                    if "T" in lastmod_text:
                        mod_date = datetime.fromisoformat(lastmod_text.replace("Z", "+00:00"))
                    else:
                        mod_date = datetime.fromisoformat(lastmod_text)
                    
                    # Calculate age
                    now = datetime.utcnow()
                    if mod_date.tzinfo is None:
                        # Assume UTC if no timezone
                        now_dt = now
                    else:
                        now_dt = datetime.now(mod_date.tzinfo)
                    
                    age_delta = now_dt - mod_date
                    age_days = age_delta.days
                    ages.append(age_days)
                    
                    # Categorize
                    if age_days <= self.FRESH_THRESHOLD:
                        result["freshness_breakdown"]["fresh"] += 1
                    elif age_days <= self.MODERATE_THRESHOLD:
                        result["freshness_breakdown"]["moderate"] += 1
                    elif age_days <= self.STALE_THRESHOLD:
                        result["freshness_breakdown"]["stale"] += 1
                    else:
                        result["freshness_breakdown"]["very_stale"] += 1
                    
                    # Track oldest and newest
                    if age_days > oldest_age:
                        oldest_age = age_days
                        oldest_entry = {
                            "url": url_value,
                            "lastmod": lastmod_text,
                            "age_days": age_days,
                        }
                    
                    if age_days < newest_age:
                        newest_age = age_days
                        newest_entry = {
                            "url": url_value,
                            "lastmod": lastmod_text,
                            "age_days": age_days,
                        }
                
                except Exception as e:
                    logger.warning(f"Failed to parse lastmod date '{lastmod_text}': {e}")
                    result["freshness_breakdown"]["no_date"] += 1
            
            result["urls_analyzed"] = result["freshness_breakdown"]["fresh"] + \
                                      result["freshness_breakdown"]["moderate"] + \
                                      result["freshness_breakdown"]["stale"] + \
                                      result["freshness_breakdown"]["very_stale"]
            
            if ages:
                result["average_age_days"] = round(sum(ages) / len(ages), 1)
            
            if oldest_entry:
                result["oldest_url"] = oldest_entry
            
            if newest_entry:
                result["newest_url"] = newest_entry
            
            # Check for issues
            stale_percent = (result["freshness_breakdown"]["stale"] + \
                            result["freshness_breakdown"]["very_stale"]) / max(result["urls_analyzed"], 1) * 100
            
            if stale_percent > 50:
                result["issues"].append(f"Over 50% of URLs are stale ({stale_percent:.1f}%)")
            
            if result["freshness_breakdown"]["no_date"] > 0:
                result["issues"].append(f"{result['freshness_breakdown']['no_date']} URLs missing lastmod dates")
        
        except Exception as e:
            result["issues"].append(f"Sitemap analysis failed: {str(e)}")
        
        return result
    
    async def detect_content_updates(self, client: httpx.AsyncClient, url: str, 
                                     sample_size: int = 5) -> Dict[str, Any]:
        """
        Analyze content update patterns by checking headers and metadata.
        
        Returns:
            {
                "last_modified": str | None,
                "has_etag": bool,
                "has_cache_control": bool,
                "cache_max_age": int | None,
                "time_since_update": str,  # Human readable like "5 days ago"
                "update_frequency_indicator": str,  # "frequent", "occasional", "rare", "unknown"
            }
        """
        result: Dict[str, Any] = {
            "last_modified": None,
            "has_etag": False,
            "has_cache_control": False,
            "cache_max_age": None,
            "time_since_update": "unknown",
            "update_frequency_indicator": "unknown",
        }
        
        try:
            response = await client.head(url, follow_redirects=True)
            
            # Last-Modified
            last_modified = response.headers.get("last-modified")
            result["last_modified"] = last_modified
            
            # ETag (indicates content versioning)
            result["has_etag"] = "etag" in response.headers
            
            # Cache-Control analysis
            cache_control = response.headers.get("cache-control", "")
            result["has_cache_control"] = bool(cache_control)
            
            # Extract max-age
            if "max-age=" in cache_control:
                try:
                    max_age_str = cache_control.split("max-age=")[1].split(",")[0].strip()
                    result["cache_max_age"] = int(max_age_str)
                except (IndexError, ValueError):
                    pass
            
            # Calculate time since update
            if last_modified:
                try:
                    from email.utils import parsedate_to_datetime
                    mod_date = parsedate_to_datetime(last_modified)
                    now = datetime.utcnow()
                    now_aware = datetime.fromisoformat(now.isoformat() + "+00:00")
                    delta = now_aware - mod_date
                    
                    if delta.days == 0:
                        result["time_since_update"] = "today"
                    elif delta.days == 1:
                        result["time_since_update"] = "1 day ago"
                    elif delta.days < 7:
                        result["time_since_update"] = f"{delta.days} days ago"
                    elif delta.days < 30:
                        weeks = delta.days // 7
                        result["time_since_update"] = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                    elif delta.days < 365:
                        months = delta.days // 30
                        result["time_since_update"] = f"{months} month{'s' if months > 1 else ''} ago"
                    else:
                        years = delta.days // 365
                        result["time_since_update"] = f"{years} year{'s' if years > 1 else ''} ago"
                    
                    # Infer update frequency
                    if delta.days <= 3:
                        result["update_frequency_indicator"] = "frequent"
                    elif delta.days <= 30:
                        result["update_frequency_indicator"] = "occasional"
                    elif delta.days <= 180:
                        result["update_frequency_indicator"] = "rare"
                    else:
                        result["update_frequency_indicator"] = "very_rare"
                
                except Exception as e:
                    logger.warning(f"Failed to parse Last-Modified: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to detect content updates: {e}")
        
        return result
    
    async def overall_freshness_assessment(self, client: httpx.AsyncClient, 
                                          main_url: str) -> Dict[str, Any]:
        """
        Comprehensive freshness assessment combining page and sitemap analysis.
        
        Returns:
            {
                "page_freshness": {...},
                "sitemap_freshness": {...},
                "content_updates": {...},
                "overall_freshness": str,  # "fresh", "acceptable", "stale", "very_stale"
                "issues": [str],
                "passed": bool,
                "recommendations": [str],
            }
        """
        result: Dict[str, Any] = {
            "page_freshness": {},
            "sitemap_freshness": {},
            "content_updates": {},
            "overall_freshness": "unknown",
            "issues": [],
            "passed": True,
            "recommendations": [],
        }
        
        try:
            root_url = self.root_url
            
            # Analyze main page
            page_freshness = await self.analyze_page_freshness(client, main_url)
            result["page_freshness"] = page_freshness
            
            # Analyze sitemap
            sitemap_freshness = await self.analyze_sitemap_freshness(client, root_url)
            result["sitemap_freshness"] = sitemap_freshness
            
            # Detect update patterns
            content_updates = await self.detect_content_updates(client, main_url)
            result["content_updates"] = content_updates
            
            # Combine for overall assessment
            page_level = page_freshness.get("freshness_level", "unknown")
            sitemap_avg_age = sitemap_freshness.get("average_age_days", 0)
            
            # Score: combine page freshness with sitemap data
            if page_level == "fresh" or sitemap_avg_age <= 30:
                result["overall_freshness"] = "fresh"
            elif page_level == "moderate" or sitemap_avg_age <= 90:
                result["overall_freshness"] = "acceptable"
            elif page_level == "stale" or sitemap_avg_age <= 180:
                result["overall_freshness"] = "stale"
                result["passed"] = False
            else:
                result["overall_freshness"] = "very_stale"
                result["passed"] = False
            
            # Collect issues
            result["issues"].extend(page_freshness.get("issues", []))
            result["issues"].extend(sitemap_freshness.get("issues", []))
            
            # Generate recommendations
            if page_level == "very_stale":
                result["recommendations"].append("Update main page content (no changes in 1+ year)")
            elif page_level == "stale":
                result["recommendations"].append("Consider updating main page (no changes in 6+ months)")
            
            if sitemap_freshness.get("urls_analyzed", 0) > 0:
                stale_pct = ((sitemap_freshness["freshness_breakdown"]["stale"] + \
                             sitemap_freshness["freshness_breakdown"]["very_stale"]) / \
                            sitemap_freshness["urls_analyzed"]) * 100
                if stale_pct > 30:
                    result["recommendations"].append(f"Review and update stale content ({stale_pct:.0f}% of sitemap)")
            
            if not content_updates.get("has_cache_control"):
                result["recommendations"].append("Set Cache-Control headers to indicate freshness")
            
            if not sitemap_freshness.get("found"):
                result["recommendations"].append("Create/enable XML sitemap with lastmod dates for better freshness tracking")
        
        except Exception as e:
            result["issues"].append(f"Overall freshness assessment failed: {str(e)}")
            result["passed"] = False
        
        return result
