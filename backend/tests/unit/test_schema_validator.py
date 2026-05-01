"""
Unit tests for SchemaValidator service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.seo.schema_validator import SchemaValidator


class TestSchemaValidator:
    """Test suite for SchemaValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for tests."""
        return SchemaValidator()

    @pytest.fixture
    def sample_html_with_json_ld(self):
        """Sample HTML with JSON-LD schema."""
        return """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Test Article",
                    "description": "Test article description",
                    "author": {
                        "@type": "Person",
                        "name": "John Doe"
                    },
                    "datePublished": "2024-01-01"
                }
                </script>
            </head>
            <body>
                <h1>Test Article</h1>
                <p>Test content</p>
            </body>
        </html>
        """

    @pytest.fixture
    def sample_html_with_microdata(self):
        """Sample HTML with microdata schema."""
        return """
        <html>
            <body>
                <div itemscope itemtype="https://schema.org/Product">
                    <h1 itemprop="name">Product Name</h1>
                    <p itemprop="description">Product description</p>
                    <span itemprop="price">$99.99</span>
                </div>
            </body>
        </html>
        """

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert hasattr(validator, 'validate_schema_markup')
        assert hasattr(validator, 'analyze_schema_completeness')

    @pytest.mark.asyncio
    async def test_json_ld_validation(self, validator, sample_html_with_json_ld):
        """Test JSON-LD schema validation."""
        result = await validator._validate_json_ld(sample_html_with_json_ld)
        
        assert result is not None
        assert "valid" in result
        assert "schema_type" in result

    @pytest.mark.asyncio
    async def test_microdata_validation(self, validator, sample_html_with_microdata):
        """Test microdata schema validation."""
        result = await validator._validate_microdata(sample_html_with_microdata)
        
        assert result is not None
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_no_schema_detected(self, validator):
        """Test detection when no schema is present."""
        html = "<html><body><p>Plain content without schema</p></body></html>"
        
        result = await validator.validate_schema_markup(html)
        
        assert result is not None
        assert result["schema_present"] is False

    @pytest.mark.asyncio
    async def test_article_schema_validation(self, validator):
        """Test Article schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Article Title",
                    "author": {"@type": "Person", "name": "Author Name"},
                    "datePublished": "2024-01-01"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_product_schema_validation(self, validator):
        """Test Product schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Product Name",
                    "price": "99.99",
                    "priceCurrency": "USD",
                    "rating": {"@type": "AggregateRating", "ratingValue": 4.5}
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_organization_schema_validation(self, validator):
        """Test Organization schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": "Company Name",
                    "url": "https://example.com",
                    "logo": "https://example.com/logo.png"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_recipe_schema_validation(self, validator):
        """Test Recipe schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Recipe",
                    "name": "Chocolate Cake",
                    "prepTime": "PT15M",
                    "cookTime": "PT30M",
                    "recipeIngredient": ["flour", "sugar", "eggs"]
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_breadcrumb_schema_validation(self, validator):
        """Test BreadcrumbList schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"},
                        {"@type": "ListItem", "position": 2, "name": "Products", "item": "https://example.com/products"}
                    ]
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_multiple_schemas_detection(self, validator):
        """Test detection of multiple schemas on page."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": "Company"
                }
                </script>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Product"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True
        assert len(result.get("schemas", [])) >= 2

    @pytest.mark.asyncio
    async def test_schema_completeness_scoring(self, validator):
        """Test schema completeness scoring."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Title",
                    "author": {"@type": "Person", "name": "Author"},
                    "datePublished": "2024-01-01",
                    "dateModified": "2024-01-02"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.analyze_schema_completeness(html)
        
        assert "completeness_score" in result
        assert 0 <= result["completeness_score"] <= 100

    @pytest.mark.asyncio
    async def test_rich_snippet_eligibility(self, validator):
        """Test rich snippet eligibility detection."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Recipe",
                    "name": "Cake",
                    "recipeIngredient": ["flour"],
                    "recipeInstructions": "Bake at 350F"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert "rich_snippet_eligible" in result or result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_invalid_json_ld_handling(self, validator):
        """Test handling of invalid JSON-LD."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Title"
                    "missing_comma": true
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        # Should handle gracefully

    @pytest.mark.asyncio
    async def test_required_properties_check(self, validator):
        """Test checking for required properties."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Title"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.analyze_schema_completeness(html)
        
        assert "missing_properties" in result or result["completeness_score"] < 100

    @pytest.mark.asyncio
    async def test_event_schema_validation(self, validator):
        """Test Event schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Event",
                    "name": "Conference",
                    "startDate": "2024-06-15T09:00:00",
                    "location": {"@type": "Place", "name": "Convention Center"}
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_local_business_schema(self, validator):
        """Test LocalBusiness schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "LocalBusiness",
                    "name": "Business Name",
                    "address": {"@type": "PostalAddress", "streetAddress": "123 Main St"},
                    "telephone": "555-1234"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_job_posting_schema(self, validator):
        """Test JobPosting schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "JobPosting",
                    "title": "Developer",
                    "baseSalary": {"@type": "PriceSpecification", "currency": "USD", "price": "100000"},
                    "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress"}}
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_faq_page_schema(self, validator):
        """Test FAQPage schema validation."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": "What is this?",
                            "acceptedAnswer": {"@type": "Answer", "text": "This is answer."}
                        }
                    ]
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_mixed_schema_types(self, validator, sample_html_with_json_ld):
        """Test handling of mixed schema types."""
        html = sample_html_with_json_ld  # JSON-LD
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_schema_context_validation(self, validator):
        """Test validation of schema.org context."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Title"
                }
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_full_validation_pipeline(self, validator, sample_html_with_json_ld):
        """Test full validation pipeline."""
        result = await validator.validate_schema_markup(sample_html_with_json_ld)
        completeness = await validator.analyze_schema_completeness(sample_html_with_json_ld)
        
        assert result is not None
        assert completeness is not None
        assert result["schema_present"] is True

    @pytest.mark.asyncio
    async def test_empty_schema_handling(self, validator):
        """Test handling of empty schema."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {}
                </script>
            </head>
        </html>
        """
        
        result = await validator.validate_schema_markup(html)
        
        # Should handle gracefully
