"""
Schema markup validation for SEO audit.
Validates JSON-LD, microdata, and RDFa schema tags.
"""

import json
import logging
from typing import Dict, Any, List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 15.0

# Common schema.org types and their required properties
SCHEMA_REQUIREMENTS = {
    "Article": ["headline", "author", "datePublished"],
    "BlogPosting": ["headline", "author", "datePublished", "articleBody"],
    "NewsArticle": ["headline", "author", "datePublished"],
    "Product": ["name", "offers"],
    "Organization": ["name", "url"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Event": ["name", "startDate", "location"],
    "Recipe": ["name", "author", "ingredients", "instructions"],
    "FAQPage": ["mainEntity"],
    "BreadcrumbList": ["itemListElement"],
}

# Rich snippet eligible schemas
RICH_SNIPPET_SCHEMAS = [
    "Article",
    "BlogPosting",
    "NewsArticle",
    "Product",
    "Recipe",
    "Event",
    "FAQPage",
    "JobPosting",
    "LocalBusiness",
]


class SchemaValidator:
    """Validates and analyzes schema markup (JSON-LD, microdata, RDFa)."""

    def __init__(self, timeout: float = TIMEOUT):
        self.timeout = timeout

    async def validate_schema_markup(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Validate schema markup on a page.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with schema validation results
        """
        result: Dict[str, Any] = {
            "passed": False,
            "issues": [],
            "json_ld_schemas": [],
            "microdata_schemas": [],
            "rdfa_schemas": [],
            "rich_snippet_eligible": False,
            "missing_properties": [],
        }

        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            if response.status_code != 200:
                result["issues"].append(f"Could not fetch page (HTTP {response.status_code})")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Check for JSON-LD schemas
            json_ld_results = self._validate_json_ld(soup)
            result["json_ld_schemas"] = json_ld_results["schemas"]
            result["issues"].extend(json_ld_results["issues"])

            # Check for microdata
            microdata_results = self._validate_microdata(soup)
            result["microdata_schemas"] = microdata_results["schemas"]
            result["issues"].extend(microdata_results["issues"])

            # Check for RDFa
            rdfa_results = self._validate_rdfa(soup)
            result["rdfa_schemas"] = rdfa_results["schemas"]
            result["issues"].extend(rdfa_results["issues"])

            # Check for rich snippet eligibility
            for schema in result["json_ld_schemas"] + result["microdata_schemas"]:
                if schema.get("type") in RICH_SNIPPET_SCHEMAS:
                    result["rich_snippet_eligible"] = True
                    break

            # Overall validation
            if result["json_ld_schemas"] or result["microdata_schemas"]:
                result["passed"] = True
            else:
                result["issues"].append("No structured data found on page")

        except Exception as e:
            result["issues"].append(f"Schema validation failed: {str(e)}")
            logger.error(f"Schema validation error: {e}")

        return result

    def _validate_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Validate JSON-LD schemas."""
        result: Dict[str, Any] = {
            "schemas": [],
            "issues": [],
        }

        json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

        if not json_ld_scripts:
            return result

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                schema_type = data.get("@type", "Unknown")

                schema_info: Dict[str, Any] = {
                    "type": "JSON-LD",
                    "schema_type": schema_type,
                    "properties": list(data.keys()),
                    "is_valid": True,
                    "missing_required": [],
                }

                # Check for required properties
                if schema_type in SCHEMA_REQUIREMENTS:
                    required = SCHEMA_REQUIREMENTS[schema_type]
                    missing = [prop for prop in required if prop not in data]
                    if missing:
                        schema_info["missing_required"] = missing
                        schema_info["is_valid"] = False
                        result["issues"].append(
                            f"JSON-LD {schema_type} missing: {', '.join(missing)}"
                        )

                result["schemas"].append(schema_info)

            except json.JSONDecodeError as e:
                result["issues"].append(f"Invalid JSON-LD: {str(e)}")
            except Exception as e:
                result["issues"].append(f"JSON-LD parsing error: {str(e)}")

        return result

    def _validate_microdata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Validate microdata schemas."""
        result: Dict[str, Any] = {
            "schemas": [],
            "issues": [],
        }

        microdata_items = soup.find_all(attrs={"itemtype": True})

        if not microdata_items:
            return result

        for item in microdata_items:
            itemtype = item.get("itemtype", "").split("/")[-1]
            properties = []

            # Find all properties within this item
            for prop in item.find_all(attrs={"itemprop": True}):
                prop_name = prop.get("itemprop")
                properties.append(prop_name)

            schema_info: Dict[str, Any] = {
                "type": "Microdata",
                "schema_type": itemtype,
                "properties": properties,
                "is_valid": True,
                "missing_required": [],
            }

            # Check for required properties
            if itemtype in SCHEMA_REQUIREMENTS:
                required = SCHEMA_REQUIREMENTS[itemtype]
                missing = [prop for prop in required if prop not in properties]
                if missing:
                    schema_info["missing_required"] = missing
                    schema_info["is_valid"] = False
                    result["issues"].append(
                        f"Microdata {itemtype} missing: {', '.join(missing)}"
                    )

            result["schemas"].append(schema_info)

        return result

    def _validate_rdfa(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Validate RDFa schemas."""
        result: Dict[str, Any] = {
            "schemas": [],
            "issues": [],
        }

        rdfa_items = soup.find_all(attrs={"typeof": True})

        if not rdfa_items:
            return result

        for item in rdfa_items:
            rdfa_type = item.get("typeof", "").split("/")[-1]
            properties = []

            # Find all properties
            for prop in item.find_all(attrs={"property": True}):
                prop_name = prop.get("property")
                properties.append(prop_name)

            schema_info: Dict[str, Any] = {
                "type": "RDFa",
                "schema_type": rdfa_type,
                "properties": properties,
                "is_valid": True,
                "missing_required": [],
            }

            result["schemas"].append(schema_info)

        return result

    def get_rich_snippet_recommendations(
        self, schemas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations for rich snippet optimization.

        Args:
            schemas: List of detected schemas

        Returns:
            List of recommendations
        """
        recommendations = []

        if not schemas:
            recommendations.append(
                "Add JSON-LD schema markup for rich snippets (Article, Product, Recipe, etc.)"
            )
            return recommendations

        for schema in schemas:
            schema_type = schema.get("schema_type")

            if schema_type not in RICH_SNIPPET_SCHEMAS:
                recommendations.append(
                    f"Change schema type from {schema_type} to an eligible type for rich snippets"
                )

            if schema.get("missing_required"):
                recommendations.append(
                    f"Add missing properties for {schema_type}: {', '.join(schema['missing_required'])}"
                )

        if not any(s.get("schema_type") in RICH_SNIPPET_SCHEMAS for s in schemas):
            recommendations.append(
                "Implement a rich snippet-eligible schema (Article, Product, Recipe, etc.)"
            )

        return recommendations

    async def analyze_schema_completeness(
        self, url: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """
        Analyze completeness and correctness of schema markup.

        Args:
            url: Full URL to analyze
            client: httpx.AsyncClient instance

        Returns:
            Dict with completeness analysis
        """
        result: Dict[str, Any] = {
            "passed": False,
            "completeness_score": 0,
            "issues": [],
            "recommendations": [],
        }

        validation = await self.validate_schema_markup(url, client)

        all_schemas = (
            validation["json_ld_schemas"]
            + validation["microdata_schemas"]
            + validation["rdfa_schemas"]
        )

        if not all_schemas:
            result["issues"].append("No structured data detected")
            result["completeness_score"] = 0
            return result

        # Calculate completeness score
        valid_schemas = sum(1 for s in all_schemas if s.get("is_valid"))
        result["completeness_score"] = int((valid_schemas / len(all_schemas)) * 100)

        if result["completeness_score"] >= 80:
            result["passed"] = True

        # Generate recommendations
        result["recommendations"] = self.get_rich_snippet_recommendations(all_schemas)
        result["issues"] = validation["issues"]

        return result
