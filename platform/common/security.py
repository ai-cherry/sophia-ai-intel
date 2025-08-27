"""
SOPHIA AI Security Middleware
=============================

This module provides basic security middleware for SOPHIA AI microservices including:
- API key authentication
- Redis-based rate limiting
- Request logging and monitoring

Usage:
    from platform.common.security import SecurityMiddleware, APIKeyAuth, RateLimiter

    app = FastAPI()
    app.add_middleware(SecurityMiddleware)
"""

import asyncio
import hashlib
import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps

import redis
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Configuration for security middleware"""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,  # seconds
        api_key_header: str = "X-API-Key",
        enable_logging: bool = True,
    ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.api_key_header = api_key_header
        self.enable_logging = enable_logging


class RedisClient:
    """Redis client wrapper for rate limiting"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        if self.client is None:
            self.client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
            )
        return self.client

    def is_rate_limited(self, identifier: str) -> tuple[bool, int]:
        """
        Check if identifier is rate limited
        Returns: (is_limited, remaining_requests)
        """
        try:
            client = self.get_client()
            key = f"rate_limit:{identifier}"
            window_key = f"{key}:window"

            # Get current window
            current_window = int(time.time() / self.config.rate_limit_window)

            # Check if we need to reset the window
            stored_window = client.get(window_key)
            if stored_window is None or int(stored_window) != current_window:
                client.setex(window_key, self.config.rate_limit_window, current_window)
                client.setex(key, self.config.rate_limit_window, 0)

            # Increment request count
            count = client.incr(key)
            remaining = max(0, self.config.rate_limit_requests - count)

            return count > self.config.rate_limit_requests, remaining

        except Exception as e:
            logger.warning(f"Rate limiting check failed: {e}")
            return False, self.config.rate_limit_requests  # Allow request on error


class APIKeyAuth:
    """API Key authentication handler"""

    def __init__(self, valid_api_keys: list[str], header_name: str = "X-API-Key"):
        self.valid_api_keys = set(valid_api_keys)
        self.header_name = header_name
        self.security = APIKeyHeader(name=header_name, auto_error=False)

    def authenticate(self, request: Request) -> Optional[str]:
        """Authenticate request and return API key if valid"""
        api_key = request.headers.get(self.header_name)
        if api_key and api_key in self.valid_api_keys:
            return api_key
        return None

    async def __call__(self, request: Request) -> Optional[str]:
        """Dependency for FastAPI"""
        return self.authenticate(request)


class RateLimiter:
    """Rate limiting middleware"""

    def __init__(self, config: SecurityConfig, redis_client: RedisClient):
        self.config = config
        self.redis_client = redis_client

    def get_identifier(self, request: Request) -> str:
        """Generate identifier for rate limiting (IP + API key hash)"""
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get(self.config.api_key_header, "")
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8] if api_key else "no_key"
        return f"{client_ip}:{key_hash}"

    async def check_rate_limit(self, request: Request) -> tuple[bool, int]:
        """Check if request should be rate limited"""
        identifier = self.get_identifier(request)
        return self.redis_client.is_rate_limited(identifier)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware combining authentication and rate limiting"""

    def __init__(
        self,
        app,
        config: SecurityConfig,
        valid_api_keys: list[str],
        exclude_paths: list[str] = ["/health", "/docs", "/openapi.json"]
    ):
        super().__init__(app)
        self.config = config
        self.valid_api_keys = set(valid_api_keys)
        self.exclude_paths = set(exclude_paths)
        self.redis_client = RedisClient(config)
        self.rate_limiter = RateLimiter(config, self.redis_client)

    async def dispatch(self, request: Request, call_next):
        # Skip security for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # API Key Authentication
        api_key = request.headers.get(self.config.api_key_header)
        if not api_key or api_key not in self.valid_api_keys:
            logger.warning(f"Unauthorized access attempt from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"}
            )

        # Rate Limiting
        is_limited, remaining = await self.rate_limiter.check_rate_limit(request)
        if is_limited:
            logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.config.rate_limit_window
                },
                headers={"Retry-After": str(self.config.rate_limit_window)}
            )

        # Log request if enabled
        if self.config.enable_logging:
            logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'} (remaining: {remaining})")

        # Add security headers
        response = await call_next(request)
        response.headers["X-API-Key-Valid"] = "true"
        response.headers["X-Rate-Limit-Remaining"] = str(remaining)
        response.headers["X-Rate-Limit-Limit"] = str(self.config.rate_limit_requests)

        return response


# Convenience functions for easy setup
def create_security_middleware(
    valid_api_keys: list[str],
    redis_host: str = "localhost",
    redis_port: int = 6379,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    api_key_header: str = "X-API-Key",
    exclude_paths: list[str] = ["/health", "/docs", "/openapi.json"]
) -> Callable:
    """Factory function to create security middleware"""

    config = SecurityConfig(
        redis_host=redis_host,
        redis_port=redis_port,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window=rate_limit_window,
        api_key_header=api_key_header,
    )

    def middleware_factory(app):
        return SecurityMiddleware(
            app=app,
            config=config,
            valid_api_keys=valid_api_keys,
            exclude_paths=exclude_paths
        )

    return middleware_factory


def require_api_key(valid_api_keys: list[str], header_name: str = "X-API-Key"):
    """Dependency for protecting individual endpoints"""
    auth = APIKeyAuth(valid_api_keys, header_name)

    async def dependency(request: Request):
        api_key = auth.authenticate(request)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )
        return api_key

    return dependency