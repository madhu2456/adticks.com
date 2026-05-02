"""
Test suite for Google Analytics 4 integration.
Tests OAuth flow, token exchange, and real API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import httpx

from app.services.analytics.ga_service import (
    get_auth_url,
    exchange_code,
    refresh_access_token,
    get_ga_properties,
    fetch_ga_metrics,
    sync_ga_data,
)


@pytest.fixture
def ga_credentials():
    """Sample GA OAuth credentials."""
    return {
        "client_id": "test-ga-client-id.apps.googleusercontent.com",
        "client_secret": "test-ga-secret",
        "redirect_uri": "https://adticks.com/ga-callback",
    }


@pytest.fixture
def valid_token_response():
    """Sample valid token response from Google."""
    return {
        "access_token": "ya29.a0AfH6SMBx...",
        "expires_in": 3599,
        "refresh_token": "1//0gF...",
        "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "token_type": "Bearer",
    }


@pytest.fixture
def ga_properties_response():
    """Sample GA4 properties response."""
    return {
        "accounts": [
            {
                "name": "accounts/123456789",
                "displayName": "Test Account",
            }
        ],
        "properties": [
            {
                "name": "properties/987654321",
                "displayName": "Test Property",
                "parent": "accounts/123456789",
            }
        ]
    }


@pytest.fixture
def ga_metrics_response():
    """Sample GA4 metrics response."""
    return {
        "rows": [
            {
                "dimensionValues": [
                    {"value": "2024-04-01"},
                    {"value": "Organic Search"}
                ],
                "metricValues": [
                    {"value": "1500"},
                    {"value": "1200"},
                    {"value": "45"},
                ]
            },
            {
                "dimensionValues": [
                    {"value": "2024-04-01"},
                    {"value": "Direct"}
                ],
                "metricValues": [
                    {"value": "800"},
                    {"value": "750"},
                    {"value": "20"},
                ]
            },
        ]
    }


class TestGAOAuthFlow:
    """Test OAuth2 authorization flow."""

    def test_get_auth_url(self, ga_credentials):
        """Test OAuth authorization URL generation."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = ga_credentials["client_id"]
            mock_settings.GOOGLE_REDIRECT_URI = ga_credentials["redirect_uri"]

            url = get_auth_url()

            assert "https://accounts.google.com/o/oauth2/v2/auth" in url
            assert ga_credentials["client_id"] in url
            assert "analytics.readonly" in url
            assert "offline" in url

    def test_get_auth_url_with_state(self, ga_credentials):
        """Test OAuth URL with CSRF state token."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = ga_credentials["client_id"]
            mock_settings.GOOGLE_REDIRECT_URI = ga_credentials["redirect_uri"]

            state_token = "test_csrf_token_ga_12345"
            url = get_auth_url(state=state_token)

            assert state_token in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, valid_token_response):
        """Test successful OAuth code exchange for GA."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client"
            mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
            mock_settings.GOOGLE_REDIRECT_URI = "https://adticks.com/ga-callback"

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
                assert "expires_in" in result
                assert result["access_token"] == valid_token_response["access_token"]

    @pytest.mark.asyncio
    async def test_exchange_code_missing_credentials(self):
        """Test exchange_code with missing credentials for GA."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = ""
            mock_settings.GOOGLE_CLIENT_SECRET = ""

            with pytest.raises(ValueError, match="credentials missing"):
                await exchange_code("test_code")

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, valid_token_response):
        """Test successful token refresh."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
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


class TestGADataFetching:
    """Test fetching real GA4 data."""

    @pytest.mark.asyncio
    async def test_get_ga_properties(self, ga_properties_response):
        """Test fetching GA4 properties."""
        access_token = "ya29.test_token"

        with patch("app.services.analytics.ga_service.build") as mock_build:
            mock_service = MagicMock()
            mock_accounts = MagicMock()
            mock_properties = MagicMock()
            
            mock_build.return_value = mock_service
            mock_service.accounts.return_value = mock_accounts
            mock_service.accounts().properties.return_value = mock_properties
            
            mock_accounts.list.return_value.execute.return_value = ga_properties_response
            mock_properties.list.return_value.execute.return_value = {"properties": []}

            result = await get_ga_properties(access_token=access_token)

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fetch_ga_metrics(self, ga_metrics_response):
        """Test fetching GA4 metrics data."""
        access_token = "ya29.test_token"
        property_id = "987654321"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("app.services.analytics.ga_service.build") as mock_build:
            mock_service = MagicMock()
            mock_properties = MagicMock()
            mock_run_report = MagicMock()

            mock_build.return_value = mock_service
            mock_service.properties.return_value = mock_properties
            mock_properties.runReport.return_value = mock_run_report
            mock_run_report.execute.return_value = ga_metrics_response

            result = await fetch_ga_metrics(
                access_token=access_token,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
                metrics=["sessions", "users", "conversions"],
                dimensions=["date", "trafficSource"],
            )

            assert len(result) == 2
            assert "date" in result[0]
            assert "trafficSource" in result[0]


class TestGADataSync:
    """Test GA4 data synchronization."""

    @pytest.mark.asyncio
    async def test_sync_ga_data(self, ga_metrics_response):
        """Test full GA4 data sync process."""
        access_token = "ya29.test_token"
        property_id = "987654321"
        start_date = "2024-04-01"
        end_date = "2024-04-30"

        with patch("app.services.analytics.ga_service.fetch_ga_metrics") as mock_fetch:
            # Setup mock response
            mock_metrics = [
                {
                    "date": "2024-04-01",
                    "trafficSource": "Organic Search",
                    "sessions": 1500,
                    "users": 1200,
                    "newUsers": 800,
                    "pageviews": 4500,
                    "bounceRate": 0.35,
                    "conversions": 45,
                },
                {
                    "date": "2024-04-01",
                    "trafficSource": "Direct",
                    "sessions": 800,
                    "users": 750,
                    "newUsers": 300,
                    "pageviews": 1600,
                    "bounceRate": 0.28,
                    "conversions": 20,
                },
            ]
            mock_fetch.return_value = mock_metrics

            result = await sync_ga_data(
                access_token=access_token,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert result["property_id"] == property_id
            assert result["metric_count"] == 2
            assert result["summary"]["total_sessions"] == 2300
            assert result["summary"]["total_users"] == 1950

    @pytest.mark.asyncio
    async def test_sync_ga_data_empty_results(self):
        """Test GA4 sync with no data."""
        with patch("app.services.analytics.ga_service.fetch_ga_metrics") as mock_fetch:
            mock_fetch.return_value = []

            result = await sync_ga_data(
                access_token="token",
                property_id="123456789",
                start_date="2024-04-01",
                end_date="2024-04-30",
            )

            assert result["metric_count"] == 0
            assert result["summary"]["total_sessions"] == 0


class TestGAErrorHandling:
    """Test error handling in GA service."""

    @pytest.mark.asyncio
    async def test_fetch_metrics_api_error(self):
        """Test handling of GA API errors."""
        from googleapiclient.errors import HttpError

        access_token = "ya29.test_token"

        with patch("app.services.analytics.ga_service.build") as mock_build:
            mock_service = MagicMock()
            mock_properties = MagicMock()
            mock_run_report = MagicMock()

            mock_build.return_value = mock_service
            mock_service.properties.return_value = mock_properties
            mock_properties.runReport.return_value = mock_run_report
            mock_run_report.execute.side_effect = HttpError(
                resp=MagicMock(status=403), content=b"Forbidden"
            )

            with pytest.raises(ValueError, match="Failed to fetch GA4 metrics"):
                await fetch_ga_metrics(
                    access_token=access_token,
                    property_id="123456789",
                    start_date="2024-04-01",
                    end_date="2024-04-30",
                )

    @pytest.mark.asyncio
    async def test_exchange_code_http_error(self):
        """Test handling of HTTP errors during token exchange."""
        with patch("app.services.analytics.ga_service.settings") as mock_settings:
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
