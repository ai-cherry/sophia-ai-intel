"""
Unified MCP Base Class for Standardized Service Implementation
Provides consistent patterns for all MCP services
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import asyncpg
import redis.asyncio as redis
import logging
import time
import os
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPResponse:
    """Standardized response format for all MCP services"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", metadata: Dict = None) -> Dict:
        """Create a success response"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if data is not None:
            response["data"] = data
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def error(message: str, error_code: str = None, details: Any = None) -> Dict:
        """Create an error response"""
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error_code:
            response["error_code"] = error_code
            
        if details:
            response["details"] = details
            
        return response

class MCPService:
    """Base class for all MCP services providing standard functionality"""
    
    def __init__(self, name: str, version: str = "1.0.0", port: int = 8000):
        self.name = name
        self.version = version
        self.port = port
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title=f"{name} MCP Server",
            description=f"Model Context Protocol server for {name}",
            version=version,
        )
        
        # Database connections
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Metrics
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
        # Setup middleware and routes
        self.setup_middleware()
        self.setup_base_routes()
        
    def setup_middleware(self):
        """Setup standard middleware for all services"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            
            # Increment request counter
            self.request_count += 1
            
            try:
                response = await call_next(request)
                
                # Log request
                process_time = time.time() - start_time
                logger.info(
                    f"{request.method} {request.url.path} "
                    f"completed in {process_time:.3f}s "
                    f"with status {response.status_code}"
                )
                
                # Add custom headers
                response.headers["X-Process-Time"] = str(process_time)
                response.headers["X-Service-Name"] = self.name
                response.headers["X-Service-Version"] = self.version
                
                return response
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Request failed: {str(e)}")
                raise
                
    def setup_base_routes(self):
        """Setup standard routes for all services"""
        
        @self.app.get("/healthz")
        async def health_check():
            """Standard health check endpoint"""
            health_status = {
                "status": "healthy",
                "service": self.name,
                "version": self.version,
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "metrics": {
                    "request_count": self.request_count,
                    "error_count": self.error_count,
                    "error_rate": self.error_count / max(self.request_count, 1)
                }
            }
            
            # Check database connection
            if self.db_pool:
                try:
                    async with self.db_pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        health_status["database"] = "connected"
                except:
                    health_status["status"] = "degraded"
                    health_status["database"] = "disconnected"
                    
            # Check Redis connection
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    health_status["cache"] = "connected"
                except:
                    health_status["status"] = "degraded"
                    health_status["cache"] = "disconnected"
                    
            return MCPResponse.success(health_status)
        
        @self.app.get("/info")
        async def service_info():
            """Get service information"""
            return MCPResponse.success({
                "name": self.name,
                "version": self.version,
                "description": self.app.description,
                "endpoints": [route.path for route in self.app.routes],
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
            })
        
        @self.app.get("/metrics")
        async def metrics():
            """Get service metrics"""
            return MCPResponse.success({
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "start_time": self.start_time.isoformat(),
            })
            
    async def connect_database(self, database_url: str = None):
        """Connect to PostgreSQL database"""
        try:
            db_url = database_url or os.getenv("DATABASE_URL")
            if db_url:
                self.db_pool = await asyncpg.create_pool(
                    db_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info(f"{self.name}: Database connected")
                return True
        except Exception as e:
            logger.error(f"{self.name}: Database connection failed: {e}")
            return False
            
    async def connect_redis(self, redis_url: str = None):
        """Connect to Redis cache"""
        try:
            redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = await redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info(f"{self.name}: Redis connected")
            return True
        except Exception as e:
            logger.error(f"{self.name}: Redis connection failed: {e}")
            return False
            
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
        return None
        
    async def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
            
        try:
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
            return False
            
    def register_endpoint(self, path: str, method: str = "GET"):
        """Decorator to register custom endpoints with standard error handling"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    if isinstance(result, dict) and "status" in result:
                        return result
                    return MCPResponse.success(result)
                except HTTPException as e:
                    self.error_count += 1
                    return JSONResponse(
                        status_code=e.status_code,
                        content=MCPResponse.error(e.detail)
                    )
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Endpoint {path} failed: {str(e)}")
                    return JSONResponse(
                        status_code=500,
                        content=MCPResponse.error(
                            "Internal server error",
                            error_code="INTERNAL_ERROR",
                            details=str(e) if os.getenv("DEBUG") else None
                        )
                    )
                    
            # Register with FastAPI
            if method.upper() == "GET":
                self.app.get(path)(wrapper)
            elif method.upper() == "POST":
                self.app.post(path)(wrapper)
            elif method.upper() == "PUT":
                self.app.put(path)(wrapper)
            elif method.upper() == "DELETE":
                self.app.delete(path)(wrapper)
                
            return wrapper
        return decorator
        
    async def startup(self):
        """Startup hook for service initialization"""
        logger.info(f"{self.name} MCP Server starting on port {self.port}")
        await self.connect_database()
        await self.connect_redis()
        
    async def shutdown(self):
        """Shutdown hook for cleanup"""
        logger.info(f"{self.name} MCP Server shutting down")
        
        if self.db_pool:
            await self.db_pool.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
    def run(self):
        """Run the service"""
        import uvicorn
        
        # Register lifecycle events
        self.app.add_event_handler("startup", self.startup)
        self.app.add_event_handler("shutdown", self.shutdown)
        
        # Run server
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )

# Export for use in services
__all__ = ["MCPService", "MCPResponse", "logger"]