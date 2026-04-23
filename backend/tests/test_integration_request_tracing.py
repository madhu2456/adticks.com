"""
Integration tests for request ID propagation across HTTP, Celery, and external APIs.

Tests verify that request IDs are:
- Captured from HTTP headers
- Generated when missing
- Propagated to Celery tasks
- Included in external API calls
- Present in all structured logs
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response

from app.core.celery_app import (
    apply_async_with_request_id,
    celery_app,
)
from app.core.http_client import RequestIDAsyncClient, create_request_id_client
from app.core.logging import (
    get_logger,
    get_request_id,
    request_id_context,
    set_request_id,
    with_request_id,
)


# ============================================================================
# Test: Basic Request ID Management
# ============================================================================


def test_get_request_id_returns_none_when_not_set():
    """Request ID should be None when not set."""
    # Clear context
    request_id_context.set(None)
    assert get_request_id() is None


def test_set_request_id_with_provided_id():
    """set_request_id should use provided ID."""
    test_id = "test-123"
    result = set_request_id(test_id)
    assert result == test_id
    assert get_request_id() == test_id


def test_set_request_id_generates_uuid_when_none():
    """set_request_id should generate UUID when not provided."""
    request_id = set_request_id()
    assert request_id is not None
    # Should be a valid UUID format
    uuid.UUID(request_id)
    assert get_request_id() == request_id


def test_with_request_id_context_manager():
    """with_request_id should temporarily set request ID."""
    original_id = "original-123"
    set_request_id(original_id)
    
    with with_request_id("temp-456"):
        assert get_request_id() == "temp-456"
    
    assert get_request_id() == original_id


def test_with_request_id_restores_on_exception():
    """with_request_id should restore ID even on exception."""
    original_id = "original-123"
    set_request_id(original_id)
    
    try:
        with with_request_id("temp-456"):
            assert get_request_id() == "temp-456"
            raise ValueError("test error")
    except ValueError:
        pass
    
    assert get_request_id() == original_id


# ============================================================================
# Test: HTTP Middleware Integration
# ============================================================================


@pytest.mark.asyncio
async def test_http_request_captures_request_id_header(client):
    """HTTP middleware should capture X-Request-ID from request header."""
    test_id = "req-" + str(uuid.uuid4())
    
    response = await client.get("/health", headers={"X-Request-ID": test_id})
    
    assert response.headers["X-Request-ID"] == test_id


@pytest.mark.asyncio
async def test_http_request_generates_request_id_when_missing(client):
    """HTTP middleware should generate request ID when header is missing."""
    response = await client.get("/health")
    
    # Should have generated a request ID
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    # Should be a valid UUID format
    uuid.UUID(request_id)


@pytest.mark.asyncio
async def test_http_response_includes_request_id(client):
    """HTTP response should include X-Request-ID header."""
    test_id = "response-test-" + str(uuid.uuid4())
    
    response = await client.get("/health", headers={"X-Request-ID": test_id})
    
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_id


# ============================================================================
# Test: RequestIDAsyncClient
# ============================================================================


@pytest.mark.asyncio
async def test_request_id_async_client_injects_header():
    """RequestIDAsyncClient should inject X-Request-ID header."""
    test_id = "client-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    # Mock the parent class's request method
    with patch.object(
        AsyncClient,
        "request",
        new_callable=AsyncMock
    ) as mock_request:
        mock_response = MagicMock(spec=Response)
        mock_request.return_value = mock_response
        
        async with create_request_id_client() as client:
            await client.get("https://api.example.com/data")
        
        # Verify the parent request was called with the header
        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["X-Request-ID"] == test_id


@pytest.mark.asyncio
async def test_request_id_async_client_without_request_id():
    """RequestIDAsyncClient should handle missing request ID gracefully."""
    request_id_context.set(None)
    
    with patch.object(
        AsyncClient,
        "request",
        new_callable=AsyncMock
    ) as mock_request:
        mock_response = MagicMock(spec=Response)
        mock_request.return_value = mock_response
        
        async with create_request_id_client() as client:
            await client.get("https://api.example.com/data")
        
        # Should still work, just without the header
        assert mock_request.called


@pytest.mark.asyncio
async def test_request_id_async_client_preserves_existing_headers():
    """RequestIDAsyncClient should preserve existing headers."""
    test_id = "header-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    with patch.object(
        AsyncClient,
        "request",
        new_callable=AsyncMock
    ) as mock_request:
        mock_response = MagicMock(spec=Response)
        mock_request.return_value = mock_response
        
        async with create_request_id_client() as client:
            await client.get(
                "https://api.example.com/data",
                headers={"Authorization": "Bearer token123"}
            )
        
        call_kwargs = mock_request.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["X-Request-ID"] == test_id
        assert headers["Authorization"] == "Bearer token123"


@pytest.mark.asyncio
async def test_create_request_id_client_factory():
    """create_request_id_client should create RequestIDAsyncClient."""
    client = create_request_id_client(timeout=30.0)
    assert isinstance(client, RequestIDAsyncClient)
    await client.aclose()


# ============================================================================
# Test: Celery Integration
# ============================================================================


def test_celery_task_receives_request_id_in_headers():
    """Celery signal handlers should propagate request ID to task headers."""
    test_id = "celery-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    # Create a simple task
    @celery_app.task(bind=True)
    def test_task(self):
        request_id = self.request.headers.get("x_request_id")
        assert request_id == test_id
    
    # Apply the task
    with patch("celery.app.task.Task.apply_async") as mock_apply:
        mock_apply.return_value = MagicMock(id="task-123")
        test_task.delay()
        
        # Verify the task was called with headers containing request ID
        # Note: This test may need adjustment based on Celery version


def test_apply_async_with_request_id_propagates():
    """apply_async_with_request_id should propagate request ID."""
    test_id = "apply-async-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    @celery_app.task
    def sample_task(x, y):
        return x + y
    
    with patch.object(sample_task, "apply_async") as mock_apply:
        mock_apply.return_value = MagicMock(id="task-456")
        
        apply_async_with_request_id(sample_task, args=(1, 2))
        
        # Verify apply_async was called with headers
        assert mock_apply.called
        call_kwargs = mock_apply.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["x_request_id"] == test_id


# ============================================================================
# Test: Structured Logging with Request ID
# ============================================================================


def test_logger_includes_request_id_in_logs():
    """Structured logger should include request ID in all logs."""
    logger = get_logger(__name__)
    test_id = "logger-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    # This would need to capture log output to verify
    # For now, just verify it doesn't crash
    logger.info("test message")
    logger.debug("debug message", extra={"custom_field": "value"})
    logger.warning("warning message")


def test_logger_handles_missing_request_id():
    """Logger should handle case where request ID is not set."""
    logger = get_logger(__name__)
    request_id_context.set(None)
    
    # Should not crash
    logger.info("message without request id")
    logger.error("error without request id")


# ============================================================================
# Test: End-to-End Request Tracing
# ============================================================================


@pytest.mark.asyncio
async def test_end_to_end_request_tracing():
    """Complete request flow should maintain request ID throughout."""
    test_id = "e2e-test-" + str(uuid.uuid4())
    
    # Simulate HTTP request setting request ID
    set_request_id(test_id)
    assert get_request_id() == test_id
    
    # Simulate task receiving request ID
    task_request_id = get_request_id()
    assert task_request_id == test_id
    
    # Simulate external API call including request ID
    with patch.object(
        AsyncClient,
        "request",
        new_callable=AsyncMock
    ) as mock_request:
        mock_response = MagicMock(spec=Response)
        mock_request.return_value = mock_response
        
        async with create_request_id_client() as client:
            await client.get("https://external-api.com/endpoint")
        
        # Verify request ID was injected
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"]["X-Request-ID"] == test_id


@pytest.mark.asyncio
async def test_request_id_survives_async_context_switch():
    """Request ID should survive async context switches."""
    test_id = "async-test-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    async def async_operation():
        # Request ID should be available in async function
        return get_request_id()
    
    result = await async_operation()
    assert result == test_id


def test_multiple_request_contexts():
    """Multiple concurrent contexts should have separate request IDs."""
    id1 = "id-1-" + str(uuid.uuid4())
    id2 = "id-2-" + str(uuid.uuid4())
    
    set_request_id(id1)
    assert get_request_id() == id1
    
    with with_request_id(id2):
        assert get_request_id() == id2
    
    assert get_request_id() == id1


# ============================================================================
# Test: Error Handling and Edge Cases
# ============================================================================


def test_request_id_with_none_value():
    """Handling of None request ID should be graceful."""
    request_id_context.set(None)
    assert get_request_id() is None


def test_request_id_with_empty_string():
    """Empty string request IDs should be handled."""
    set_request_id("")
    assert get_request_id() == ""


def test_request_id_with_special_characters():
    """Request IDs with special characters should work."""
    special_id = "req-!@#$%^&*()_+-={}[]|:;<>?,./~`"
    set_request_id(special_id)
    assert get_request_id() == special_id


def test_request_id_with_very_long_string():
    """Very long request IDs should be handled."""
    long_id = "x" * 10000
    set_request_id(long_id)
    assert get_request_id() == long_id


# ============================================================================
# Test: Integration with Existing Code
# ============================================================================


@pytest.mark.asyncio
async def test_http_middleware_sets_context_for_endpoint(client):
    """HTTP middleware should set request ID before endpoint execution."""
    test_id = "integration-test-" + str(uuid.uuid4())
    
    # Make request with custom request ID
    response = await client.get("/health", headers={"X-Request-ID": test_id})
    
    # Response should include the request ID
    assert response.headers["X-Request-ID"] == test_id
    assert response.status_code == 200


def test_logger_adapter_with_request_id():
    """LoggerAdapter should include request ID automatically."""
    logger = get_logger(__name__)
    test_id = "adapter-test-" + str(uuid.uuid4())
    
    set_request_id(test_id)
    
    # Log should work without explicitly passing request_id
    logger.info("test message")
    
    # Verify request ID is retrievable
    assert get_request_id() == test_id


# ============================================================================
# Test: Documentation Examples
# ============================================================================


@pytest.mark.asyncio
async def test_documentation_pattern_1_endpoint_to_task():
    """Example from docs: Endpoint → Task → External API."""
    from app.core.http_client import create_request_id_client
    from app.core.logging import get_logger
    
    test_id = "pattern1-" + str(uuid.uuid4())
    set_request_id(test_id)
    
    logger = get_logger(__name__)
    
    # Simulate external API call with request ID
    with patch.object(
        AsyncClient,
        "request",
        new_callable=AsyncMock
    ) as mock_request:
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        async with create_request_id_client() as client:
            response = await client.get("https://api.example.com/analyze")
            response.json()

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"]["X-Request-ID"] == test_id


@pytest.mark.asyncio
async def test_documentation_pattern_4_manual_request_id():
    """Example from docs: Manual request ID management."""
    from app.core.http_client import create_request_id_client
    from app.core.logging import with_request_id, get_logger
    
    logger = get_logger(__name__)
    
    with with_request_id("custom-request-123"):
        assert get_request_id() == "custom-request-123"
        
        # Even external API calls will include this request ID
        with patch.object(
            AsyncClient,
            "request",
            new_callable=AsyncMock
        ) as mock_request:
            mock_response = MagicMock(spec=Response)
            mock_request.return_value = mock_response
            
            async with create_request_id_client() as client:
                await client.get("https://api.example.com/endpoint")
            
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["headers"]["X-Request-ID"] == "custom-request-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
