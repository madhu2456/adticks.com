"""
AdTicks — HTTP client wrapper for external API calls.

Automatically injects request ID into all outgoing HTTP requests
as the X-Request-ID header, enabling end-to-end request tracing.

Wraps httpx.AsyncClient to transparently add request IDs to:
- External API calls (Ahrefs, GA4, etc.)
- Service-to-service communication
- Third-party integrations
"""

import logging
from typing import Any, AsyncGenerator, Optional

import httpx

from app.core.logging import get_logger, get_request_id

logger = get_logger(__name__)


class RequestIDAsyncClient(httpx.AsyncClient):
    """AsyncClient that automatically injects request ID in headers.
    
    Usage:
        async with RequestIDAsyncClient() as client:
            response = await client.get("https://api.example.com/data")
            # X-Request-ID header is automatically included
    """

    async def request(
        self,
        method: str | bytes,
        url: str | bytes,
        *,
        content: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        json: Optional[Any] = None,
        params: Optional[Any] = None,
        headers: Optional[Any] = None,
        cookies: Optional[Any] = None,
        auth: Optional[Any] = None,
        follow_redirects: Optional[bool] = None,
        allow_redirects: Optional[bool] = None,
        timeout: Optional[Any] = None,
        extensions: Optional[Any] = None,
    ) -> httpx.Response:
        """Override request to inject request ID header."""
        request_id = get_request_id()
        if request_id:
            headers = headers or {}
            if isinstance(headers, dict):
                headers["X-Request-ID"] = request_id
            else:
                # Handle httpx Headers objects
                headers = dict(headers) if headers else {}
                headers["X-Request-ID"] = request_id

        logger.debug(
            "external_api_call",
            extra={
                "method": method,
                "url": str(url),
                "has_request_id": bool(request_id),
            },
        )

        return await super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            allow_redirects=allow_redirects,
            timeout=timeout,
            extensions=extensions,
        )


def create_request_id_client(**kwargs) -> RequestIDAsyncClient:
    """Factory function to create a RequestIDAsyncClient.
    
    Args:
        **kwargs: Any arguments to pass to httpx.AsyncClient
        
    Returns:
        RequestIDAsyncClient instance
        
    Example:
        client = create_request_id_client(timeout=30.0)
        response = await client.get("https://api.example.com/data")
    """
    return RequestIDAsyncClient(**kwargs)
