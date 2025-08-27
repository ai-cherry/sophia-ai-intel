#!/usr/bin/env python3
"""
Health Check Implementation for agno-teams
Comprehensive health monitoring with dependency validation
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import os
import asyncio
import aiohttp
import time
import structlog
from typing import Dict, Any, List, Optional
import redis.asyncio as redis
import psycopg
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

logger = structlog.get_logger()

class HealthStatus(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str
    dependencies: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class DependencyCheck:
    """Check external dependencies"""
    
    @staticmethod
    async def check_redis(redis_url: str) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            client = redis.from_url(redis_url)
            start_time = time.time()
            await client.ping()
            latency = (time.time() - start_time) * 1000
            await client.aclose()
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "success"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "connection": "failed"
            }
    
    @staticmethod
    async def check_postgres(db_url: str) -> Dict[str, Any]:
        """Check PostgreSQL connectivity"""
        try:
            engine = create_engine(db_url)
            start_time = time.time()
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "success"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    @staticmethod
    async def check_qdrant(qdrant_url: str, api_key: str) -> Dict[str, Any]:
        """Check Qdrant connectivity"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{qdrant_url}/health", headers=headers) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "latency_ms": round(latency, 2),
                            "connection": "success"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "http_status": response.status,
                            "connection": "failed"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    @staticmethod
    async def check_http_service(service_url: str, service_name: str) -> Dict[str, Any]:
        """Check HTTP service connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{service_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "latency_ms": round(latency, 2),
                            "connection": "success"
                        }
                    else:
                        return {
                            "status": "unhealthy", 
                            "http_status": response.status,
                            "connection": "failed"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }

async def comprehensive_health_check() -> HealthStatus:
    """Perform comprehensive health check"""
    
    start_time = time.time()
    service_healthy = True
    dependencies = {}
    
    # Check Redis if configured
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        dependencies["redis"] = await DependencyCheck.check_redis(redis_url)
        if dependencies["redis"]["status"] != "healthy":
            service_healthy = False
    
    # Check PostgreSQL if configured
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        dependencies["postgres"] = await DependencyCheck.check_postgres(postgres_url)
        if dependencies["postgres"]["status"] != "healthy":
            service_healthy = False
    
    # Check Qdrant if configured
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    if qdrant_url:
        dependencies["qdrant"] = await DependencyCheck.check_qdrant(qdrant_url, qdrant_key)
        if dependencies["qdrant"]["status"] != "healthy":
            service_healthy = False
    
    # Check dependent MCP services
    dependent_services = [
        ("mcp-context", os.getenv("CONTEXT_MCP_URL")),
        ("mcp-agents", os.getenv("AGENTS_MCP_URL")), 
        ("mcp-research", os.getenv("RESEARCH_MCP_URL")),
        ("mcp-business", os.getenv("BUSINESS_MCP_URL"))
    ]
    
    for service_name, service_url in dependent_services:
        if service_url and service_name != "agno-teams":  # Don't check self
            dependencies[service_name] = await DependencyCheck.check_http_service(service_url, service_name)
            if dependencies[service_name]["status"] != "healthy":
                # Don't fail health check for dependent services, just log
                logger.warning(f"Dependent service {service_name} is unhealthy")
    
    # Performance metrics
    total_latency = (time.time() - start_time) * 1000
    performance_metrics = {
        "total_health_check_latency_ms": round(total_latency, 2),
        "dependency_count": len(dependencies),
        "healthy_dependencies": sum(1 for dep in dependencies.values() if dep.get("status") == "healthy")
    }
    
    return HealthStatus(
        status="healthy" if service_healthy else "unhealthy",
        service="agno-teams",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        dependencies=dependencies,
        performance_metrics=performance_metrics
    )

def add_health_endpoints_to_app(app: FastAPI):
    """Add health check endpoints to FastAPI app"""
    
    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """Comprehensive health check endpoint"""
        try:
            health_status = await comprehensive_health_check()
            
            if health_status.status == "unhealthy":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=health_status.dict()
                )
            
            return health_status
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Health check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unhealthy", "error": str(e)}
            )
    
    @app.get("/health/quick")
    async def quick_health_check():
        """Quick health check endpoint for load balancers"""
        return {"status": "healthy", "service": "agno-teams"}
    
    @app.get("/health/ready")
    async def readiness_check():
        """Kubernetes readiness probe endpoint"""
        health_status = await comprehensive_health_check()
        
        # Service is ready if core dependencies are healthy
        core_deps = ["redis", "postgres"]
        ready = all(
            dependencies.get(dep, {}).get("status") == "healthy" 
            for dep in core_deps 
            if dep in health_status.dependencies
        )
        
        if not ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "not_ready", "dependencies": health_status.dependencies}
            )
        
        return {"status": "ready", "service": "agno-teams"}
    
    @app.get("/health/live") 
    async def liveness_check():
        """Kubernetes liveness probe endpoint"""
        # Simple check to ensure service is alive
        return {"status": "alive", "service": "agno-teams"}

# Health check configuration
HEALTH_CHECK_CONFIG = {
    "redis_required": {"redis_url" if "context" in service_name or "agent" in service_name else "False"},
    "postgres_required": {"postgres_url" if "context" in service_name else "False"}, 
    "qdrant_required": {"qdrant_url" if "context" in service_name else "False"},
    "dependent_services": []
}
