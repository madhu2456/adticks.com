"""
Test suite for Google Search Console integration.
Tests OAuth flow, token exchange, and real API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import httpx

from app.services.gsc.gsc_service import (
    get_auth_url,
    exchange_code,
    refresh_access_token,
    fetch_search_performance,
    sync_gsc_data,
)


@pytest.fixture
def gsc_credentials():
    """Sample GSC OAuth credentials."""
    return {
        "client_id": "test-client-id.apps.googleusercontent.com",
        "client_secret": "test-secret",
        "redirect_uri": "https://adticks.com/gsc-callback",
    }


@pytest.fixture
def valid_token_response():
    """Sample valid token response from Google."""
    return {
        "access_token": "ya29.a0AfH6SMBx...",
        "expires_in": 3599,
        "refresh_token": "1//0gF...",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "token_type": "Bearer",
    }


@pytest.fixture
def gsc_query_response():
    """Sample GSC search analytics response."""
    return {
        "rows": [
            {
                "keys": ["python tutorial"],
                "clicks": 150,
                "impressions": 5000,
                "ctr": 0.03,
                "position": 2.5,
            },
            {
                "keys": ["learn python"],
                "clicks": 120,
                "impressions": 4200,
                "ctr": 0.0286,
                "position": 3.1,
            },
            {
                "keys": ["python for beginners"],
                "clicks": 80,
                "impressions": 2500,
                "ctr": 0.032,
                "position": 4.2,
            },
        ]
    }


class TestGSCOAuthFlow:
    """Test OAuth2 authorization flow."""

    def test_get_auth_url(self, gsc_credentials):
        """Test OAuth authorization URL generation."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = gsc_credentials["client_id"]
            mock_settings.GOOGLE_REDIRECT_URI = gsc_credentials["redirect_uri"]

            url = get_auth_url()

            assert "https://accounts.google.com/o/oauth2/v2/auth" in url
            assert gsc_credentials["client_id"] in url
            assert "webmasters.readonly" in url
            assert "offline" in url

    def test_get_auth_url_with_state(self, gsc_credentials):
        """Test OAuth URL with CSRF state token."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = gsc_credentials["client_id"]
            mock_settings.GOOGLE_REDIRECT_URI = gsc_credentials["redirect_uri"]

            state_token = "test_csrf_token_12345"
            url = get_auth_url(state=state_token)

            assert state_token in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, valid_token_response):
        """Test successful OAuth code exchange."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
            mock_settings.GOOGLE_REDIRECT_URI = "https://adticks.com/gsc-callback"

            with patch("httpx.AsyncClient.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = valid_token_response
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value.__aenter__.return_value.post.return_value = mock_response

                with patch("httpx.AsyncClient") as mock_client:
                    mock_instance = MagicMock()
                    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                    mock_instance.__aexit__ = AsyncMock(return_value=None)
                    mock_instance.post = AsyncMock(return_value=mock_response)
                    mock_client.return_value = mock_instance

                    result = await exchange_code("test_auth_code")

                    assert "access_token" in result
                    assert "refresh_token" in result
                    assert "expires_in" in result
                    assert result["access_token"] == valid_token_response["access_token"]

    @pytest.mark.asyncio
    async def test_exchange_code_missing_credentials(self):
        """Test exchange_code with missing credentials."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = ""
            mock_settings.GOOGLE_CLIENT_SECRET = ""

            with pytest.raises(ValueError, match="credentials missing"):
                await exchange_code("test_code")

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, valid_token_response):
        """Test successful token refresh."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"

            refresh_token = "1//0gF..."
            new_token_response = {
                "access_token": "ya29.new_token_xyz...",
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
                assert result["expires_in"] == 3600


class TestGSCDataFetching:
    """Test fetching real GSC data."""

    @pytest.mark.asyncio
    async def test_fetch_search_performance(self, gsc_query_response):
        """Test fetching GSC search performance data."""
        access_token = "ya29.test_token"
        site_url = "https://example.com/"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("app.services.gsc.gsc_service.build") as mock_build:
            # Setup the mock service
            mock_service = MagicMock()
            mock_analytics = MagicMock()
            mock_query = MagicMock()

            mock_build.return_value = mock_service
            mock_service.searchanalytics.return_value = mock_analytics
            mock_analytics.query.return_value = mock_query
            mock_query.execute.return_value = gsc_query_response

            result = await fetch_search_performance(
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
    async def test_fetch_search_performance_with_dimensions(self):
        """Test fetching with custom dimensions."""
        access_token = "ya29.test_token"
        site_url = "https://example.com/"

        with patch("app.services.gsc.gsc_service.build") as mock_build:
            mock_service = MagicMock()
            mock_analytics = MagicMock()
            mock_query = MagicMock()

            mock_build.return_value = mock_service
            mock_service.searchanalytics.return_value = mock_analytics
            mock_analytics.query.return_value = mock_query
            mock_query.execute.return_value = {"rows": []}

            result = await fetch_search_performance(
                access_token=access_token,
                site_url=site_url,
                start_date="2024-04-01",
                end_date="2024-04-30",
                dimensions=["query", "page"],
            )

            assert result == []


class TestGSCDataSync:
    """Test GSC data synchronization."""

    @pytest.mark.asyncio
    async def test_sync_gsc_data(self, gsc_query_response):
        """Test full GSC data sync process."""
        access_token = "ya29.test_token"
        site_url = "https://example.com/"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("app.services.gsc.gsc_service.fetch_search_performance") as mock_fetch:
            # Setup mock response
            mock_queries = [
                {
                    "query": "python tutorial",
                    "clicks": 150,
                    "impressions": 5000,
                    "ctr": 0.03,
                    "ctr_pct": 3.0,
                    "position": 2.5,
                },
                {
                    "query": "learn python",
                    "clicks": 120,
                    "impressions": 4200,
                    "ctr": 0.0286,
                    "ctr_pct": 2.86,
                    "position": 3.1,
                },
            ]
            mock_fetch.return_value = mock_queries

            result = await sync_gsc_data(
                access_token=access_token,
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
            )

            assert result["site_url"] == site_url
            assert result["query_count"] == 2
            assert result["summary"]["total_clicks"] == 270
            assert result["summary"]["total_impressions"] == 9200
            assert result["summary"]["top_query"] == "python tutorial"
            assert result["summary"]["top_query_clicks"] == 150

    @pytest.mark.asyncio
    async def test_sync_gsc_data_empty_results(self):
        """Test GSC sync with no data."""
        with patch("app.services.gsc.gsc_service.fetch_search_performance") as mock_fetch:
            mock_fetch.return_value = []

            result = await sync_gsc_data(
                access_token="token",
                site_url="https://example.com/",
                start_date="2024-04-01",
                end_date="2024-04-30",
            )

            assert result["query_count"] == 0
            assert result["summary"]["total_clicks"] == 0
            assert result["summary"]["total_impressions"] == 0
            assert result["summary"]["top_query"] is None


class TestGSCErrorHandling:
    """Test error handling in GSC service."""

    @pytest.mark.asyncio
    async def test_fetch_performance_api_error(self):
        """Test handling of GSC API errors."""
        from googleapiclient.errors import HttpError

        access_token = "ya29.test_token"

        with patch("app.services.gsc.gsc_service.build") as mock_build:
            mock_service = MagicMock()
            mock_analytics = MagicMock()
            mock_query = MagicMock()

            mock_build.return_value = mock_service
            mock_service.searchanalytics.return_value = mock_analytics
            mock_analytics.query.return_value = mock_query
            mock_query.execute.side_effect = HttpError(
                resp=MagicMock(status=403), content=b"Forbidden"
            )

            with pytest.raises(ValueError, match="Failed to fetch GSC data"):
                await fetch_search_performance(
                    access_token=access_token,
                    site_url="https://example.com/",
                    start_date="2024-04-01",
                    end_date="2024-04-30",
                )

    @pytest.mark.asyncio
    async def test_exchange_code_http_error(self):
        """Test handling of HTTP errors during token exchange."""
        with patch("app.services.gsc.gsc_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test"
            mock_settings.GOOGLE_CLIENT_SECRET = "test"
            mock_settings.GOOGLE_REDIRECT_URI = "https://example.com"

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
