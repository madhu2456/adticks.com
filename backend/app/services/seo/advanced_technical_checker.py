"""
Advanced technical SEO checks: DNS, SSL, resources, minification, etc.
"""

import logging
import socket
import ssl
import requests
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 15.0


class AdvancedTechnicalChecker:
    """Advanced technical checks for SEO audit."""

    def __init__(self, timeout: float = TIMEOUT):
        self.timeout = timeout

    async def check_ssl_certificate(self, url: str) -> Dict[str, Any]:
        """
        Check SSL certificate validity and configuration.

        Args:
            url: Full URL to analyze

        Returns:
            Dict with SSL certificate analysis
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "ssl_valid": False,
            "certificate_info": {},
            "expiry_days": 0,
        }

        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc.split(":")[0]

            # Create SSL context
            context = ssl.create_default_context()

            # Get certificate info
            with socket.create_connection((hostname, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    bin_cert = ssock.getpeercert(binary_form=True)

                    if cert:
                        result["ssl_valid"] = True
                        result["passed"] = True

                        # Extract certificate details
                        result["certificate_info"] = {
                            "subject": dict(x[0] for x in cert.get("subject", [])),
                            "issuer": dict(x[0] for x in cert.get("issuer", [])),
                        }

                        # Check expiry
                        import ssl as ssl_module

                        expiry_str = cert.get("notAfter")
                        if expiry_str:
                            expiry_date = datetime.strptime(
                                expiry_str, "%b %d %H:%M:%S %Y %Z"
                            )
                            days_until_expiry = (expiry_date - datetime.now()).days
                            result["expiry_days"] = days_until_expiry

                            if days_until_expiry < 0:
                                result["issues"].append("SSL certificate has expired")
                                result["passed"] = False
                            elif days_until_expiry < 30:
                                result["issues"].append(
                                    f"SSL certificate expires in {days_until_expiry} days"
                                )
                            elif days_until_expiry < 90:
                                result["issues"].append(
                                    f"SSL certificate expiring soon ({days_until_expiry} days)"
                                )

        except ssl.SSLError as e:
            result["issues"].append(f"SSL certificate error: {str(e)}")
            logger.error(f"SSL check error: {e}")
        except Exception as e:
            result["issues"].append(f"SSL certificate check failed: {str(e)}")
            logger.error(f"SSL check error: {e}")

        return result

    async def check_resource_minification(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Check if CSS/JS resources are minified.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with minification analysis
        """
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "css_files": [],
            "js_files": [],
            "unminified_css": [],
            "unminified_js": [],
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Check CSS minification
            css_links = soup.find_all("link", {"rel": "stylesheet"})
            for link in css_links:
                href = link.get("href")
                if href:
                    result["css_files"].append(href)
                    # Check if minified (simplified check)
                    if ".min.css" not in href and not self._appears_minified(href):
                        result["unminified_css"].append(href)
                        result["issues"].append(f"Unminified CSS: {href}")
                        result["passed"] = False

            # Check JS minification
            scripts = soup.find_all("script", {"src": True})
            for script in scripts:
                src = script.get("src")
                if src:
                    result["js_files"].append(src)
                    if ".min.js" not in src and not self._appears_minified(src):
                        result["unminified_js"].append(src)
                        result["issues"].append(f"Unminified JavaScript: {src}")
                        result["passed"] = False

        except Exception as e:
            result["issues"].append(f"Minification check failed: {str(e)}")
            logger.error(f"Minification check error: {e}")

        return result

    def _appears_minified(self, filename: str) -> bool:
        """
        Check if filename suggests minified version.

        Args:
            filename: Resource filename/URL

        Returns:
            True if appears minified
        """
        return any(
            indicator in filename.lower()
            for indicator in [".min.", "-min.", "_min.", "minified"]
        )

    async def check_image_optimization(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Check image optimization and compression.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with image optimization analysis
        """
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "total_images": 0,
            "images_without_modern_format": 0,
            "images_without_lazy_loading": 0,
            "large_images": [],
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Check images
            images = soup.find_all("img")
            result["total_images"] = len(images)

            for img in images:
                src = img.get("src", "")

                # Check for modern formats (WebP, AVIF)
                if not any(
                    fmt in src.lower() for fmt in [".webp", ".avif"]
                ):
                    result["images_without_modern_format"] += 1

                # Check for lazy loading
                if not img.get("loading") == "lazy":
                    result["images_without_lazy_loading"] += 1

                # Check for oversized images (heuristic)
                if any(
                    dim in src.lower()
                    for dim in ["1920", "2560", "original", "full-size"]
                ):
                    result["large_images"].append(src)

            if result["images_without_modern_format"] > 0:
                result["issues"].append(
                    f"{result['images_without_modern_format']} images not in modern format (WebP/AVIF)"
                )
                result["passed"] = False

            if result["images_without_lazy_loading"] > 0:
                result["issues"].append(
                    f"{result['images_without_lazy_loading']} images missing lazy loading"
                )
                result["passed"] = False

            if result["large_images"]:
                result["issues"].append(
                    f"{len(result['large_images'])} potentially oversized images detected"
                )
                result["passed"] = False

        except Exception as e:
            result["issues"].append(f"Image optimization check failed: {str(e)}")
            logger.error(f"Image optimization error: {e}")

        return result

    async def check_dns_records(self, url: str) -> Dict[str, Any]:
        """
        Validate DNS records for the domain.

        Args:
            url: Full URL to analyze

        Returns:
            Dict with DNS record analysis
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "dns_records": {},
            "has_a_record": False,
            "has_mx_record": False,
            "has_txt_record": False,
        }

        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc.split(":")[0]

            # Check A record
            try:
                a_records = socket.gethostbyname_ex(hostname)
                result["dns_records"]["A"] = a_records[2]
                result["has_a_record"] = True
            except socket.gaierror:
                result["issues"].append("No A record found (DNS resolution failed)")

            # Check MX records
            try:
                import dns.resolver

                mx_records = dns.resolver.resolve(hostname, "MX")
                result["dns_records"]["MX"] = [str(mx) for mx in mx_records]
                result["has_mx_record"] = len(result["dns_records"]["MX"]) > 0
            except Exception as e:
                logger.debug(f"MX record check not available: {e}")

            # Check TXT records
            try:
                import dns.resolver

                txt_records = dns.resolver.resolve(hostname, "TXT")
                result["dns_records"]["TXT"] = [str(txt) for txt in txt_records]
                result["has_txt_record"] = len(result["dns_records"]["TXT"]) > 0
            except Exception as e:
                logger.debug(f"TXT record check not available: {e}")

            if result["has_a_record"]:
                result["passed"] = True

        except Exception as e:
            result["issues"].append(f"DNS check failed: {str(e)}")
            logger.error(f"DNS check error: {e}")

        return result

    async def analyze_all_technical(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Run all advanced technical checks.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with all technical analysis
        """
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "ssl_certificate": {},
            "resource_minification": {},
            "image_optimization": {},
            "dns_records": {},
        }

        try:
            # Run all checks in parallel would be better, but doing sequentially for simplicity
            ssl_result = await self.check_ssl_certificate(url)
            result["ssl_certificate"] = ssl_result
            if not ssl_result["passed"]:
                result["passed"] = False

            minification_result = await self.check_resource_minification(url, client)
            result["resource_minification"] = minification_result
            if not minification_result["passed"]:
                result["passed"] = False

            image_result = await self.check_image_optimization(url, client)
            result["image_optimization"] = image_result
            if not image_result["passed"]:
                result["passed"] = False

            dns_result = await self.check_dns_records(url)
            result["dns_records"] = dns_result
            if not dns_result["passed"]:
                result["passed"] = False

            # Aggregate issues
            for check in [ssl_result, minification_result, image_result, dns_result]:
                result["issues"].extend(check.get("issues", []))

        except Exception as e:
            result["issues"].append(f"Advanced technical analysis failed: {str(e)}")
            result["passed"] = False
            logger.error(f"Advanced technical error: {e}")

        return result
