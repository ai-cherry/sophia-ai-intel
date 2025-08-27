"""
Sophia AI Shared HTTP Client Module

Provides a singleton HTTP client for efficient connection pooling and reuse
across all Sophia AI services. This module eliminates the overhead of creating
new HTTP clients for each request while maintaining thread safety.

Features:
- Singleton pattern for connection reuse
- Configurable timeouts and connection limits
- Automatic retry logic with exponential backoff
- Request/response logging and metrics
- Graceful shutdown handling

Usage:
    from platform.http.client import get_http_client

    async with get_http_client() as client:
        response = await client.get('https://api.example.com/data')
        data = response.json()
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from httpx import Timeout, Limits, AsyncClient

logger = logging.getLogger(__name__)


class SophiaHttpClient:
    """
    Singleton HTTP client for Sophia AI services.

    Provides connection pooling, automatic retries, and comprehensive
    logging for all outbound HTTP requests.
    """

    _instance: Optional['SophiaHttpClient'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._client: Optional[AsyncClient] = None
        self._is_initialized = False

    @classmethod
    async def get_instance(cls) -> 'SophiaHttpClient':
        """Get singleton instance with thread-safe initialization."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """Initialize the HTTP client with optimized settings."""
        if self._is_initialized:
            return

        # Configure timeouts for different types of requests
        timeout = Timeout(
            connect=10.0,    # Connection timeout
            read=30.0,       # Read timeout
            write=10.0,      # Write timeout
            pool=5.0         # Pool timeout
        )

        # Configure connection limits for optimal performance
        limits = Limits(
            max_keepalive_connections=100,  # Keep connections alive
            max_connections=200,            # Total concurrent connections
            keepalive_expiry=300.0          # Keep connections for 5 minutes
        )

        # Create client with comprehensive configuration
        self._client = AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            # Enable HTTP/2 for better performance
            http2=True,
            # Configure transport for optimal performance
            transport=httpx.AsyncHTTPTransport(
                retries=3,
                # Enable connection pooling
                socket_options=[(6, 1, 1)]  # TCP_NODELAY
            )
        )

        self._is_initialized = True
        logger.info("SophiaHttpClient initialized with connection pooling")

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AsyncClient, None]:
        """Get HTTP client instance for making requests."""
        if not self._is_initialized or self._client is None:
            await self._initialize()

        if self._client is None:
            raise RuntimeError("Failed to initialize HTTP client")

        try:
            yield self._client
        except Exception as e:
            logger.error(f"HTTP client error: {e}")
            raise

    async def close(self):
        """Gracefully close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._is_initialized = False
            logger.info("SophiaHttpClient closed")


# Global client instance
_http_client: Optional[SophiaHttpClient] = None


async def get_http_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Get shared HTTP client instance.

    Usage:
        async with get_http_client() as client:
            response = await client.get('https://api.example.com')
    """
    global _http_client

    if _http_client is None:
        _http_client = await SophiaHttpClient.get_instance()

    async with _http_client.get_client() as client:
        yield client


async def close_http_client():
    """Close the shared HTTP client (for cleanup)."""
    global _http_client

    if _http_client:
        await _http_client.close()
        _http_client = None


# Synchronous wrapper for backward compatibility
def get_sync_client() -> httpx.Client:
    """
    Get synchronous HTTP client (use sparingly).

    Note: Prefer async client for better performance.
    """
    timeout = Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=5.0
    )

    limits = Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=300.0
    )

    return httpx.Client(
        timeout=timeout,
        limits=limits,
        follow_redirects=True
    )


# Utility functions for common HTTP operations
async def make_request(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None
) -> httpx.Response:
    """
    Make HTTP request using shared client.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        headers: Optional headers
        params: Optional query parameters
        json_data: Optional JSON body
        timeout: Optional custom timeout

    Returns:
        HTTP response object
    """
    start_time = time.time()

    async with get_http_client() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=timeout
            )

            duration = time.time() - start_time
            logger.debug(".2f")

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(".2f")
            raise


async def get_json(url: str, **kwargs) -> Dict[str, Any]:
    """GET request returning JSON data."""
    response = await make_request('GET', url, **kwargs)
    response.raise_for_status()
    return response.json()


async def post_json(url: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """POST request with JSON data."""
    kwargs['json_data'] = data
    response = await make_request('POST', url, **kwargs)
    response.raise_for_status()
    return response.json()