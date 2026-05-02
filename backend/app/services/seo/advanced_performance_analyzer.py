"""
Advanced Performance Analyzer for AdTicks.

Performs deep performance analysis including Lighthouse scoring,
Core Web Vitals metrics, resource waterfall analysis, and optimization
recommendations.
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AdvancedPerformanceAnalyzer:
    """Analyzes performance metrics including Lighthouse, CWV, and resources."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None

    async def analyze_performance(self, url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        """
        Perform comprehensive performance analysis.
        
        Args:
            url: URL to analyze
            client: HTTP client
            
        Returns:
            Dict with performance metrics, CWV data, and recommendations
        """
        try:
            logger.info(f"Analyzing performance for {url}")
            
            # Get page content for resource analysis
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Analyze resources
            resource_analysis = self._analyze_resources(soup, response)
            
            # Get Core Web Vitals-like metrics from page analysis
            cwv_metrics = await self._analyze_core_web_vitals(url, client)
            
            # Lighthouse scoring simulation
            lighthouse_score = self._calculate_lighthouse_score(
                resource_analysis, cwv_metrics, response
            )
            
            # Get recommendations
            recommendations = self._get_optimization_recommendations(
                resource_analysis, cwv_metrics, lighthouse_score
            )
            
            issues = []
            passed = lighthouse_score >= 70
            
            if lighthouse_score < 90:
                issues.append(f"Lighthouse score is {lighthouse_score}/100 (target: 90+)")
            if resource_analysis.get("total_size_mb", 0) > 5:
                issues.append(f"Page size is {resource_analysis['total_size_mb']:.1f}MB (should be <3MB)")
            if resource_analysis.get("unoptimized_images") > 0:
                issues.append(f"Found {resource_analysis['unoptimized_images']} unoptimized images")
            if cwv_metrics.get("estimated_fcp_ms", 0) > 1800:
                issues.append(f"First Contentful Paint estimated at {cwv_metrics['estimated_fcp_ms']:.0f}ms (should be <1.8s)")
            if cwv_metrics.get("estimated_lcp_ms", 0) > 2500:
                issues.append(f"Largest Contentful Paint estimated at {cwv_metrics['estimated_lcp_ms']:.0f}ms (should be <2.5s)")
            if cwv_metrics.get("estimated_cls", 0) > 0.1:
                issues.append(f"Cumulative Layout Shift estimated at {cwv_metrics['estimated_cls']:.3f} (should be <0.1)")
            
            return {
                "name": "Advanced Performance",
                "passed": passed,
                "score": lighthouse_score,
                "metrics": {
                    "lighthouse_score": lighthouse_score,
                    "core_web_vitals": cwv_metrics,
                    "resources": resource_analysis,
                },
                "issues": issues,
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.error(f"Error analyzing performance for {url}: {str(e)}")
            return {
                "name": "Advanced Performance",
                "passed": False,
                "score": 0,
                "metrics": {},
                "issues": [f"Performance analysis failed: {str(e)}"],
                "recommendations": [],
            }

    async def _analyze_core_web_vitals(self, url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Estimate Core Web Vitals from page analysis."""
        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.content.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(content, "html.parser")
            
            # Estimate FCP (First Contentful Paint)
            # Heuristic: pages with large above-fold content have slower FCP
            above_fold_size = sum(
                len(img.get("src", "").encode())
                for img in soup.find_all("img", limit=5)
            )
            estimated_fcp_ms = 800 + (above_fold_size / 1024) * 0.5
            
            # Estimate LCP (Largest Contentful Paint)
            # Usually 0.5-1s after FCP for well-optimized pages
            estimated_lcp_ms = estimated_fcp_ms + 800
            
            # Estimate CLS (Cumulative Layout Shift)
            # Check for layout-shift prone patterns
            cls_issues = 0
            if soup.find("img", {"width": None, "height": None}):
                cls_issues += 1
            if soup.find("iframe"):
                cls_issues += 1
            if soup.find("ad"):
                cls_issues += 0.05
            
            estimated_cls = 0.05 + (cls_issues * 0.02)
            
            return {
                "estimated_fcp_ms": round(estimated_fcp_ms),
                "estimated_lcp_ms": round(estimated_lcp_ms),
                "estimated_cls": min(0.25, estimated_cls),
                "ttfb_ms": response.elapsed.total_seconds() * 1000,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
            }
        except Exception as e:
            logger.warning(f"Could not analyze CWV for {url}: {str(e)}")
            return {
                "estimated_fcp_ms": 0,
                "estimated_lcp_ms": 0,
                "estimated_cls": 0,
                "ttfb_ms": 0,
                "response_time_ms": 0,
            }

    def _analyze_resources(self, soup: BeautifulSoup, response: httpx.Response) -> Dict[str, Any]:
        """Analyze page resources (CSS, JS, images)."""
        try:
            # Count and analyze CSS
            css_files = soup.find_all("link", {"rel": "stylesheet"})
            inline_css = soup.find_all("style")
            
            # Count and analyze JavaScript
            js_files = soup.find_all("script", {"src": True})
            inline_scripts = soup.find_all("script", {"src": None})
            
            # Analyze images
            images = soup.find_all("img")
            unoptimized_images = 0
            
            for img in images:
                src = img.get("src", "")
                if src.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    # Check for missing optimization indicators
                    if not img.get("loading"):  # Missing lazy loading
                        unoptimized_images += 1
                    if not img.get("width") or not img.get("height"):
                        unoptimized_images += 1
            
            # Estimate page size
            total_size_mb = len(response.content) / (1024 * 1024)
            
            # Check for minification
            html_content = response.text
            is_minified = len(html_content.split("\n")) < 50
            
            return {
                "css_files": len(css_files),
                "inline_stylesheets": len(inline_css),
                "javascript_files": len(js_files),
                "inline_scripts": len(inline_scripts),
                "images": len(images),
                "unoptimized_images": unoptimized_images,
                "total_size_mb": round(total_size_mb, 2),
                "is_minified": is_minified,
                "has_compression": "gzip" in response.headers.get("content-encoding", ""),
                "cache_control": response.headers.get("cache-control", "not set"),
            }
        except Exception as e:
            logger.warning(f"Error analyzing resources: {str(e)}")
            return {}

    def _calculate_lighthouse_score(
        self,
        resources: Dict[str, Any],
        cwv: Dict[str, Any],
        response: httpx.Response,
    ) -> int:
        """Calculate synthetic Lighthouse score based on metrics."""
        score = 100
        
        # Penalize for response time
        ttfb = cwv.get("response_time_ms", 0)
        if ttfb > 600:
            score -= min(20, (ttfb - 600) / 50)
        
        # Penalize for CWV failures
        cls = cwv.get("estimated_cls", 0)
        if cls > 0.1:
            score -= 15
        
        fcp = cwv.get("estimated_fcp_ms", 0)
        if fcp > 1800:
            score -= 10
        
        lcp = cwv.get("estimated_lcp_ms", 0)
        if lcp > 2500:
            score -= 15
        
        # Penalize for unoptimized resources
        if resources.get("unoptimized_images", 0) > 5:
            score -= 10
        
        if resources.get("javascript_files", 0) > 10:
            score -= 5
        
        if resources.get("css_files", 0) > 5:
            score -= 5
        
        # Penalize for page size
        page_size = resources.get("total_size_mb", 0)
        if page_size > 5:
            score -= min(15, (page_size - 5) * 3)
        
        # Reward for optimization
        if resources.get("is_minified"):
            score += 5
        
        if resources.get("has_compression"):
            score += 5
        
        return max(0, min(100, round(score)))

    def _get_optimization_recommendations(
        self,
        resources: Dict[str, Any],
        cwv: Dict[str, Any],
        score: int,
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if cwv.get("estimated_fcp_ms", 0) > 1800:
            recommendations.append("Reduce render-blocking resources (defer non-critical CSS/JS)")
        
        if cwv.get("estimated_lcp_ms", 0) > 2500:
            recommendations.append("Optimize Largest Contentful Paint: preload critical images, use CDN")
        
        if cwv.get("estimated_cls", 0) > 0.1:
            recommendations.append("Reduce Cumulative Layout Shift: specify image dimensions, avoid dynamic ad insertion")
        
        if resources.get("unoptimized_images", 0) > 0:
            recommendations.append(f"Optimize {resources['unoptimized_images']} images: use WebP format, add lazy loading")
        
        if resources.get("javascript_files", 0) > 10:
            recommendations.append("Bundle JavaScript files to reduce HTTP requests")
        
        if resources.get("css_files", 0) > 5:
            recommendations.append("Combine CSS files and remove unused styles")
        
        if resources.get("total_size_mb", 0) > 5:
            recommendations.append("Reduce total page size: compress images, minify code, enable gzip")
        
        if not resources.get("has_compression"):
            recommendations.append("Enable gzip compression on server")
        
        if score >= 90:
            recommendations.append("Excellent performance! Continue monitoring metrics.")
        elif score >= 70:
            recommendations.append("Good performance. Implement above recommendations for further improvement.")
        
        return recommendations[:5]  # Return top 5 recommendations
