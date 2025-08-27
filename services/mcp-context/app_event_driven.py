#!/usr/bin/env python3
'''
MCP Context Service - Event Driven Architecture
Breaks circular dependencies using event bus pattern
'''

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import structlog
from typing import Dict, Any, List, Optional
import asyncio

# Import service discovery
import sys
sys.path.append('/app/platform/common')
from service_discovery import ServiceDiscovery, EVENT_TYPES

logger = structlog.get_logger()

app = FastAPI(
    title="Sophia MCP Context Service",
    description="Context management with event-driven architecture",
    version="2.0.0"
)

# Global service discovery instance
discovery: Optional[ServiceDiscovery] = None

class ContextRequest(BaseModel):
    query: str
    context_type: str = "general"
    max_results: int = 10

class ContextResponse(BaseModel):
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    '''Initialize service discovery on startup'''
    global discovery
    
    redis_url = os.getenv("REDIS_URL", "redis://sophia-event-bus:6379")
    discovery = ServiceDiscovery(redis_url)
    
    try:
        await discovery.connect()
        await discovery.register_service("mcp-context", "http://mcp-context:8080/health")
        
        # Subscribe to relevant events
        await discovery.subscribe_to_events([
            EVENT_TYPES["CONTEXT_REQUEST"]
        ], handle_context_request_event)
        
        logger.info("MCP Context service initialized with event bus")
    except Exception as e:
        logger.error("Failed to initialize service discovery", error=str(e))

async def handle_context_request_event(event_data: Dict[str, Any]):
    '''Handle context request events from other services'''
    try:
        request_data = event_data.get("data", {})
        query = request_data.get("query", "")
        
        # Process context request
        results = await process_context_query(query)
        
        # Publish response event
        response_data = {
            "request_id": request_data.get("request_id"),
            "results": results,
            "service": "mcp-context"
        }
        
        await discovery.publish_event(EVENT_TYPES["CONTEXT_RESPONSE"], response_data)
        
    except Exception as e:
        logger.error("Error handling context request event", error=str(e))

async def process_context_query(query: str) -> List[Dict[str, Any]]:
    '''Process context query - mock implementation'''
    # TODO: Implement actual context processing
    return [
        {
            "content": f"Context result for: {query}",
            "score": 0.95,
            "source": "mcp-context"
        }
    ]

@app.get("/health")
async def health_check():
    '''Health check endpoint'''
    try:
        if discovery and discovery.redis_client:
            await discovery.redis_client.ping()
            return {"status": "healthy", "service": "mcp-context", "event_bus": "connected"}
    except Exception:
        pass
    
    return {"status": "unhealthy", "service": "mcp-context", "event_bus": "disconnected"}

@app.post("/context/search")
async def search_context(request: ContextRequest) -> ContextResponse:
    '''Search context endpoint - now publishes events instead of direct calls'''
    
    # Publish context request event
    request_data = {
        "request_id": f"ctx_{asyncio.get_event_loop().time()}",
        "query": request.query,
        "context_type": request.context_type,
        "max_results": request.max_results
    }
    
    if discovery:
        await discovery.publish_event(EVENT_TYPES["CONTEXT_REQUEST"], request_data)
    
    # Process locally and return
    results = await process_context_query(request.query)
    
    return ContextResponse(
        results=results,
        metadata={"service": "mcp-context", "event_driven": True}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )
