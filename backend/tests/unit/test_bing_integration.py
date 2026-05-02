"""
Test suite for Bing Webmaster Tools integration.
Tests OAuth flow, token exchange, and real API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx

from app.services.bing.bing_service import (
    get_auth_url,
    exchange_code,
    refresh_access_token,
    get_sites,
    fetch_search_queries,
    fetch_crawl_issues,
    sync_bing_data,
)


@pytest.fixture
def bing_credentials():
    """Sample Bing OAuth credentials."""
    return {
        "client_id": "test-bing-client-id",
        "client_secret": "test-bing-secret",
        "redirect_uri": "https://adticks.com/bing-callback",
    }


@pytest.fixture
def valid_token_response():
    """Sample valid token response from Bing."""
    return {
        "access_token": "M.R3_BAY...",
        "expires_in": 3599,
        "refresh_token": "M.R3_BAY_refresh...",
        "token_type": "Bearer",
    }


@pytest.fixture
def bing_sites_response():
    """Sample Bing sites response."""
    return {
        "d": {
            "Sites": [
                {
                    "SiteId": "12345678-1234-1234-1234-123456789012",
                    "Url": "https://example.com",
                    "VerificationMethod": "Metatag",
                },
                {
                    "SiteId": "87654321-4321-4321-4321-210987654321",
                    "Url": "https://example2.com",
                    "VerificationMethod": "File",
                },
            ]
        }
    }


@pytest.fixture
def bing_queries_response():
    """Sample Bing query stats response."""
    return {
        "d": {
            "QueryStats": [
                {
                    "Query": "python tutorial",
                    "Clicks": 150,
                    "Impressions": 5000,
                    "Ctr": 0.03,
                    "AvgPosition": 2.5,
                },
                {
                    "Query": "learn python",
                    "Clicks": 120,
                    "Impressions": 4200,
                    "Ctr": 0.0286,
                    "AvgPosition": 3.1,
                },
                {
                    "Query": "python for beginners",
                    "Clicks": 80,
                    "Impressions": 2500,
                    "Ctr": 0.032,
                    "AvgPosition": 4.2,
                },
            ]
        }
    }


@pytest.fixture
def bing_issues_response():
    """Sample Bing crawl issues response."""
    return {
        "d": {
            "CrawlIssues": [
                {
                    "IssueType": "Not found (404)",
                    "Url": "https://example.com/old-page",
                    "IssueStatus": "open",
                    "IssueLevel": "high",
                },
                {
                    "IssueType": "Blocked by robots.txt",
                    "Url": "https://example.com/admin",
                    "IssueStatus": "open",
                    "IssueLevel": "medium",
                },
            ]
        }
    }


class TestBingOAuthFlow:
    """Test OAuth2 authorization flow for Bing."""

    def test_get_auth_url(self, bing_credentials):
        """Test Bing OAuth authorization URL generation."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = bing_credentials["client_id"]
            mock_settings.BING_REDIRECT_URI = bing_credentials["redirect_uri"]

            url = get_auth_url()

            assert "https://login.live.com/oauth20_authorize.srf" in url
            assert bing_credentials["client_id"] in url
            assert "bingwebmaster.api" in url

    def test_get_auth_url_with_state(self, bing_credentials):
        """Test Bing OAuth URL with CSRF state token."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = bing_credentials["client_id"]
            mock_settings.BING_REDIRECT_URI = bing_credentials["redirect_uri"]

            state_token = "test_csrf_token_bing_12345"
            url = get_auth_url(state=state_token)

            assert state_token in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, valid_token_response):
        """Test successful Bing OAuth code exchange."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = "test-bing-client"
            mock_settings.BING_CLIENT_SECRET = "test-bing-secret"
            mock_settings.BING_REDIRECT_URI = "https://adticks.com/bing-callback"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)

                mock_response = MagicMock()
                mock_response.json.return_value = valid_token_response
                mock_response.raise_for_status = MagicMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance

                result = await exchange_code("test_auth_code")

                assert "access_token" in result
                assert "refresh_token" in result
                assert result["access_token"] == valid_token_response["access_token"]

    @pytest.mark.asyncio
    async def test_exchange_code_missing_credentials(self):
        """Test Bing exchange_code with missing credentials."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = ""
            mock_settings.BING_CLIENT_SECRET = ""

            with pytest.raises(ValueError, match="credentials missing"):
                await exchange_code("test_code")

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, valid_token_response):
        """Test successful Bing token refresh."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = "test-client"
            mock_settings.BING_CLIENT_SECRET = "test-secret"

            refresh_token = "M.R3_BAY_refresh..."
            new_token_response = {
                "access_token": "M.R3_BAY_new_token...",
                "expires_in": 3600,
                "token_type": "Bearer",
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)

                mock_response = MagicMock()
                mock_response.json.return_value = new_token_response
                mock_response.raise_for_status = MagicMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance

                result = await refresh_access_token(refresh_token)

                assert result["access_token"] == new_token_response["access_token"]


class TestBingDataFetching:
    """Test fetching real Bing data."""

    @pytest.mark.asyncio
    async def test_get_sites(self, bing_sites_response):
        """Test fetching Bing sites."""
        access_token = "M.R3_BAY_test"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.json.return_value = bing_sites_response
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            result = await get_sites(access_token=access_token)

            assert len(result) == 2
            assert result[0]["Url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_fetch_search_queries(self, bing_queries_response):
        """Test fetching Bing search queries."""
        access_token = "M.R3_BAY_test"
        site_url = "https://example.com"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.json.return_value = bing_queries_response
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            result = await fetch_search_queries(
                access_token=access_token,
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
            )

            assert len(result) == 3
            assert result[0]["query"] == "python tutorial"
            assert result[0]["clicks"] == 150
            assert result[0]["impressions"] == 5000
            assert result[0]["ctr"] == 0.03
            assert result[0]["position"] == 2.5

    @pytest.mark.asyncio
    async def test_fetch_crawl_issues(self, bing_issues_response):
        """Test fetching Bing crawl issues."""
        access_token = "M.R3_BAY_test"
        site_url = "https://example.com"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.json.return_value = bing_issues_response
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            result = await fetch_crawl_issues(
                access_token=access_token,
                site_url=site_url,
            )

            assert len(result) == 2
            assert result[0]["IssueType"] == "Not found (404)"


class TestBingDataSync:
    """Test Bing data synchronization."""

    @pytest.mark.asyncio
    async def test_sync_bing_data(self, bing_queries_response, bing_issues_response):
        """Test full Bing data sync process."""
        access_token = "M.R3_BAY_test"
        site_url = "https://example.com"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("app.services.bing.bing_service.fetch_search_queries") as mock_queries, \
             patch("app.services.bing.bing_service.fetch_crawl_issues") as mock_issues:
            
            # Setup mock responses
            mock_queries_data = [
                {
                    "query": "python tutorial",
                    "clicks": 150,
                    "impressions": 5000,
                    "ctr": 0.03,
                    "position": 2.5,
                    "date": "2024-04-30",
                },
                {
                    "query": "learn python",
                    "clicks": 120,
                    "impressions": 4200,
                    "ctr": 0.0286,
                    "position": 3.1,
                    "date": "2024-04-30",
                },
            ]
            mock_queries.return_value = mock_queries_data
            
            mock_issues_data = [
                {
                    "IssueType": "Not found (404)",
                    "Url": "https://example.com/old-page",
                    "IssueStatus": "open",
                },
            ]
            mock_issues.return_value = mock_issues_data

            result = await sync_bing_data(
                access_token=access_token,
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
            )

            assert result["site_url"] == site_url
            assert result["query_count"] == 2
            assert result["issue_count"] == 1
            assert result["summary"]["total_clicks"] == 270
            assert result["summary"]["total_impressions"] == 9200
            assert result["summary"]["top_query"] == "python tutorial"

    @pytest.mark.asyncio
    async def test_sync_bing_data_empty_results(self):
        """Test Bing sync with no data."""
        with patch("app.services.bing.bing_service.fetch_search_queries") as mock_queries, \
             patch("app.services.bing.bing_service.fetch_crawl_issues") as mock_issues:
            
            mock_queries.return_value = []
            mock_issues.return_value = []

            result = await sync_bing_data(
                access_token="token",
                site_url="https://example.com",
                start_date="2024-04-01",
                end_date="2024-04-30",
            )

            assert result["query_count"] == 0
            assert result["issue_count"] == 0
            assert result["summary"]["total_clicks"] == 0


class TestBingErrorHandling:
    """Test error handling in Bing service."""

    @pytest.mark.asyncio
    async def test_fetch_queries_http_error(self):
        """Test handling of HTTP errors during query fetch."""
        access_token = "M.R3_BAY_test"
        site_url = "https://example.com"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=MagicMock()
            )
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            with pytest.raises(ValueError, match="Failed to fetch Bing search queries"):
                await fetch_search_queries(
                    access_token=access_token,
                    site_url=site_url,
                    start_date="2024-04-01",
                    end_date="2024-04-30",
                )

    @pytest.mark.asyncio
    async def test_exchange_code_http_error(self):
        """Test handling of HTTP errors during token exchange."""
        with patch("app.services.bing.bing_service.settings") as mock_settings:
            mock_settings.BING_CLIENT_ID = "test"
            mock_settings.BING_CLIENT_SECRET = "test"
            mock_settings.BING_REDIRECT_URI = "https://example.com"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = MagicMock()
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)

                mock_response = MagicMock()
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "400 Bad Request", request=MagicMock(), response=MagicMock()
                )
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance

                with pytest.raises(ValueError, match="Failed to exchange OAuth code"):
                    await exchange_code("bad_code")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
