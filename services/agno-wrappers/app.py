#!/usr/bin/env python3
"""
AGNO Wrappers Service - MCP service wrappers for AGNO platform
Part of the Sophia AI Intel platform
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AGNO Wrappers Service",
    description="MCP service wrappers for AGNO platform integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: datetime
    environment: str

class WrapperRequest(BaseModel):
    """Wrapper request model"""
    service: str = Field(..., description="Target service name")
    method: str = Field(..., description="Method to call")
    payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")

class WrapperResponse(BaseModel):
    """Wrapper response model"""
    success: bool
    service: str
    method: str
    result: Optional[Any] = None
    message: str
    timestamp: datetime

# Global state
service_state = {
    "started_at": datetime.utcnow(),
    "requests_processed": 0,
    "environment": os.getenv("ENVIRONMENT", "development")
}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Log request details
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return response

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - returns service status"""
    return HealthResponse(
        status="running",
        service="agno-wrappers",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        environment=service_state["environment"]
    )

@app.get("/health", response_model=HealthResponse)
@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="agno-wrappers",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        environment=service_state["environment"]
    )

@app.get("/status")
async def get_status():
    """Get detailed service status"""
    uptime = (datetime.utcnow() - service_state["started_at"]).total_seconds()
    
    return {
        "service": "agno-wrappers",
        "status": "running",
        "version": "1.0.0",
        "environment": service_state["environment"],
        "uptime_seconds": uptime,
        "requests_processed": service_state["requests_processed"],
        "started_at": service_state["started_at"].isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
        "available_wrappers": [
            "mcp-context",
            "mcp-github", 
            "mcp-hubspot",
            "mcp-lambda",
            "mcp-research",
            "mcp-business"
        ]
    }

@app.post("/wrap", response_model=WrapperResponse)
async def wrap_service_call(request: WrapperRequest):
    """Wrap a service call through the AGNO platform"""
    try:
        service_state["requests_processed"] += 1
        
        logger.info(f"Wrapping call to {request.service}.{request.method}")
        
        # Mock service wrapping - in real implementation would:
        # 1. Validate service exists
        # 2. Transform request format
        # 3. Call actual service
        # 4. Transform response format
        # 5. Return wrapped result
        
        result = {
            "wrapped_service": request.service,
            "wrapped_method": request.method,
            "original_payload": request.payload,
            "transformed_result": f"Mock result from {request.service}.{request.method}",
            "wrapped_at": datetime.utcnow().isoformat(),
            "wrapper_version": "1.0.0"
        }
        
        return WrapperResponse(
            success=True,
            service=request.service,
            method=request.method,
            result=result,
            message=f"Successfully wrapped call to {request.service}.{request.method}",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error wrapping service call: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Service wrapping failed: {str(e)}"
        )

@app.get("/wrappers")
async def list_available_wrappers():
    """List all available service wrappers"""
    return {
        "wrappers": {
            "mcp-context": {
                "name": "MCP Context Service",
                "description": "Context management and retrieval",
                "methods": ["get_context", "store_context", "search_context"],
                "status": "available"
            },
            "mcp-github": {
                "name": "MCP GitHub Service",
                "description": "GitHub integration and repository management",
                "methods": ["get_repo", "create_issue", "get_commits"],
                "status": "available"
            },
            "mcp-hubspot": {
                "name": "MCP HubSpot Service", 
                "description": "CRM and sales pipeline management",
                "methods": ["get_contacts", "create_deal", "get_companies"],
                "status": "available"
            },
            "mcp-lambda": {
                "name": "MCP Lambda Service",
                "description": "Lambda Labs compute integration",
                "methods": ["launch_instance", "get_instances", "terminate_instance"],
                "status": "available"
            },
            "mcp-research": {
                "name": "MCP Research Service",
                "description": "Research and data gathering",
                "methods": ["search", "summarize", "analyze"],
                "status": "available"
            },
            "mcp-business": {
                "name": "MCP Business Service",
                "description": "Business intelligence and analytics",
                "methods": ["get_metrics", "generate_report", "analyze_trends"],
                "status": "available"
            }
        },
        "total_wrappers": 6,
        "service": "agno-wrappers",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def startup_event():
    """Startup event handler"""
    logger.info("🔧 AGNO Wrappers Service starting up...")
    logger.info(f"Environment: {service_state['environment']}")
    logger.info("✅ AGNO Wrappers Service ready for MCP service wrapping")

async def shutdown_event():
    """Shutdown event handler"""
    logger.info("🛑 AGNO Wrappers Service shutting down...")

# Add event handlers
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting AGNO Wrappers Service on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )