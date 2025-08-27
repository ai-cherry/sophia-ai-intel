"""
Sophia AI Service Base Module

Provides a unified foundation for all FastAPI services in the Sophia AI ecosystem.
This module eliminates boilerplate code while maintaining flexibility for service-specific needs.

Usage:
    from platform.common.service_base import create_app, ServiceConfig
    
    app = create_app(
        ServiceConfig(
            name="mcp-context",
            version="1.0.0",
            description="Context management service for Sophia AI"
        )
    )
"""

import os
import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel


# Assuming these imports exist and are correctly structured in the project
from platform.common.errors import SophiaError, error_handler as common_error_handler # Renamed to avoid conflict
from platform.common.audit import AuditLogger
from platform.observability.otel import setup_telemetry


@dataclass
class ServiceConfig:
    """Configuration for service initialization."""
    name: str
    version: str
    description: str
    port: int = 8000
    host: str = "0.0.0.0"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_metrics: bool = True
    enable_health_check: bool = True
    enable_audit: bool = True
    debug: bool = False
    startup_event: Optional[callable] = None
    shutdown_event: Optional[callable] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)


class HealthResponse(BaseModel):
    """Standard health check response."""
    status: str
    service: str
    version: str
    uptime: float
    timestamp: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ServiceBase:
    """Base service class providing common functionality and FastAPI app creation."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.start_time = None
        self.audit_logger = None
        self.logger = self._setup_logging()
        self._ready = False # Internal readiness state

    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging."""
        logger = logging.getLogger(self.config.name)
        logger.setLevel(logging.DEBUG if self.config.debug else logging.INFO)
        
        # Prevent adding multiple handlers if re-initialized
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Manage service lifecycle."""
        self.start_time = time.time()
        self.logger.info(f"Starting {self.config.name} v{self.config.version}")
        
        if self.config.enable_audit:
            self.audit_logger = AuditLogger(self.config.name)
            
        if self.config.enable_metrics:
            setup_telemetry(self.config.name, self.config.version)
        
        # Execute custom startup event if provided
        if self.config.startup_event:
            self.logger.info(f"Executing custom startup event for {self.config.name}")
            await self.config.startup_event()

        self._ready = True # Service is ready after startup tasks
        yield
        self._ready = False # Service is shutting down
        self.logger.info(f"Shutting down {self.config.name}")

        # Execute custom shutdown event if provided
        if self.config.shutdown_event:
            self.logger.info(f"Executing custom shutdown event for {self.config.name}")
            await self.config.shutdown_event()
    
    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title=self.config.name,
            description=self.config.description,
            version=self.config.version,
            lifespan=self.lifespan if self.config.enable_health_check else None, # Only enable lifespan if health check is enabled
            # Additional OpenAPI info can be added via self.config.extra_config
            **self.config.extra_config
        )

        # CORS Middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # GZip Middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Global Exception Handler for SophiaError
        @app.exception_handler(SophiaError)
        async def sophia_exception_handler(request: Request, exc: SophiaError):
            self.logger.error(f"SophiaError caught: {exc.message}", extra={"details": exc.details})
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(error=exc.error_code, message=exc.message, details=exc.details).model_dump()
            )

        # Global Exception Handler for FastAPI's HTTPException
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            self.logger.error(f"HTTPException caught: {exc.detail}", extra={"status_code": exc.status_code})
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(error="HTTP_ERROR", message=exc.detail).model_dump()
            )

        # Catch-all for unhandled exceptions
        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            self.logger.exception("Unhandled exception caught")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(error="INTERNAL_SERVER_ERROR", message="An unexpected error occurred.").model_dump()
            )

        # Health check endpoint
        @app.get("/healthz", summary="Liveness Probe", tags=["Health"])
        async def health_check():
            uptime = time.time() - self.start_time if self.start_time else 0
            return HealthResponse(
                status="ok",
                service=self.config.name,
                version=self.config.version,
                uptime=uptime,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            )

        # Readiness probe endpoint
        @app.get("/readyz", summary="Readiness Probe", tags=["Health"])
        async def readiness_probe():
            if self._ready:
                return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ready"})
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service is not ready")

        # Stream endpoint for SSE ping
        @app.get("/stream", summary="Server-Sent Events Ping", tags=["SSE"])
        async def sse_stream():
            async def generate_pings():
                while True:
                    await asyncio.sleep(25) # Ping every 25 seconds
                    yield "event: ping\ndata: \n\n"
            return StreamingResponse(generate_pings(), media_type="text/event-stream")

        return app

# Public function to create an app instance easily
def create_app(config: ServiceConfig) -> FastAPI:
    return ServiceBase(config).create_app()
