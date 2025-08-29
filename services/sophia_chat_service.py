#!/usr/bin/env python3
"""
Sophia Chat Service - FastAPI Service for Dashboard Integration
==============================================================

This service provides a clean REST API for the Sophia dashboard to
interact with the Sophia Supreme Orchestrator and all its capabilities.

Key Features:
- RESTful chat API for seamless dashboard integration
- Unified interface to Sophia's enhanced intelligence
- Dynamic API routing integration
- AGNO swarm orchestration
- Real-time processing with WebSocket support
- Comprehensive error handling and logging
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
import uvicorn
from datetime import datetime
import os

# Import Sophia components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from sophia_agno_orchestrator import SophiaSupremeOrchestrator
except ImportError:
    # Fallback for development
    SophiaSupremeOrchestrator = None
    logger.warning("Could not import SophiaSupremeOrchestrator - running in fallback mode")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sophia Chat Service",
    description="Enhanced AI Chat Service with Supreme Orchestration",
    version="1.0.0"
)

# CORS middleware for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],  # Dashboard URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Sophia instance
sophia_orchestrator: Optional[SophiaSupremeOrchestrator] = None

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    context: Dict[str, Any] = {}
    use_enhanced_intelligence: bool = True

class ChatResponse(BaseModel):
    response: str
    session_id: str
    processing_method: str
    execution_time: float
    api_providers_used: List[str] = []
    quality_score: float
    metadata: Dict[str, Any] = {}
    timestamp: str

class StatusResponse(BaseModel):
    service_status: str
    sophia_status: Dict[str, Any]
    available_capabilities: List[str]
    uptime: float

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize Sophia orchestrator on startup"""
    global sophia_orchestrator
    logger.info("🚀 Initializing Sophia Chat Service...")
    
    try:
        if SophiaSupremeOrchestrator:
            sophia_orchestrator = SophiaSupremeOrchestrator()
            logger.info("✅ Sophia Supreme Orchestrator initialized successfully")
        else:
            logger.warning("⚠️ SophiaSupremeOrchestrator not available - running in fallback mode")
            sophia_orchestrator = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sophia: {e}")
        # Continue startup but mark as degraded
        sophia_orchestrator = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Sophia Chat Service",
        "status": "active",
        "sophia_available": sophia_orchestrator is not None,
        "version": "1.0.0",
        "capabilities": [
            "Enhanced Intelligence Chat",
            "Dynamic API Routing", 
            "AGNO Swarm Orchestration",
            "Real-time WebSocket Support"
        ]
    }

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status"""
    if not sophia_orchestrator:
        raise HTTPException(status_code=503, detail="Sophia orchestrator not available")
    
    sophia_status = sophia_orchestrator.get_orchestrator_status()
    
    return StatusResponse(
        service_status="active",
        sophia_status=sophia_status,
        available_capabilities=[
            "Enhanced Intelligence Processing",
            "Dynamic API Routing",
            "Multi-Provider Intelligence",
            "AGNO Swarm Coordination",
            "Real-time Processing"
        ],
        uptime=sophia_status.get("uptime_seconds", 0)
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint using Sophia's enhanced intelligence"""
    if not sophia_orchestrator:
        raise HTTPException(status_code=503, detail="Sophia orchestrator not available")
    
    try:
        logger.info(f"💬 Chat request from session {request.session_id}: {request.message[:50]}...")
        
        if request.use_enhanced_intelligence:
            # Use Sophia's enhanced intelligence with dynamic API routing
            result = await sophia_orchestrator.enhanced_intelligence_request(
                request.message, 
                request.context
            )
        else:
            # Use basic orchestration
            result = await sophia_orchestrator.orchestrate_supreme_intelligence(request.message)
        
        # Handle both success and error cases
        if "error" in result:
            logger.error(f"Sophia processing error: {result['error']}")
            response_text = f"I encountered an issue processing your request: {result['error']}"
            processing_method = "error_handling"
            quality_score = 0.0
            api_providers = []
        else:
            response_text = result.get("response", result.get("synthesis_results", {}).get("synthesized_response", "No response generated"))
            processing_method = result.get("processing_method", "unknown")
            quality_score = result.get("quality_score", 0.0)
            api_providers = result.get("api_providers_used", [])
        
        response = ChatResponse(
            response=response_text,
            session_id=request.session_id,
            processing_method=processing_method,
            execution_time=result.get("execution_time", 0.0),
            api_providers_used=api_providers,
            quality_score=quality_score,
            metadata={
                "request_type": result.get("request_type", "unknown"),
                "external_intelligence": bool(result.get("external_intelligence")),
                "swarms_engaged": result.get("performance_metrics", {}).get("swarms_engaged", 0)
            },
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Chat response generated in {response.execution_time:.2f}s with quality {quality_score:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    logger.info(f"🔗 WebSocket connected for session: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create chat request
            request = ChatRequest(
                message=message_data.get("message", ""),
                session_id=session_id,
                context=message_data.get("context", {}),
                use_enhanced_intelligence=message_data.get("use_enhanced_intelligence", True)
            )
            
            # Process with Sophia
            if sophia_orchestrator:
                try:
                    if request.use_enhanced_intelligence:
                        result = await sophia_orchestrator.enhanced_intelligence_request(
                            request.message, request.context
                        )
                    else:
                        result = await sophia_orchestrator.orchestrate_supreme_intelligence(request.message)
                    
                    # Send response back
                    response_data = {
                        "type": "chat_response",
                        "response": result.get("response", result.get("synthesis_results", {}).get("synthesized_response", "No response")),
                        "processing_method": result.get("processing_method", "unknown"),
                        "execution_time": result.get("execution_time", 0.0),
                        "api_providers_used": result.get("api_providers_used", []),
                        "quality_score": result.get("quality_score", 0.0),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await manager.send_personal_message(json.dumps(response_data), websocket)
                    
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "message": f"Processing error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.send_personal_message(json.dumps(error_response), websocket)
            else:
                # Sophia not available
                fallback_response = {
                    "type": "chat_response",
                    "response": "I'm currently starting up. Please try again in a moment.",
                    "processing_method": "fallback",
                    "execution_time": 0.0,
                    "quality_score": 0.5,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(fallback_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(websocket)

@app.get("/providers/status")
async def get_provider_status():
    """Get status of all API providers"""
    if not sophia_orchestrator or not hasattr(sophia_orchestrator, 'api_router'):
        raise HTTPException(status_code=503, detail="API router not available")
    
    try:
        status = await sophia_orchestrator.api_router.get_provider_status()
        return {
            "providers": status,
            "total_providers": len(status),
            "active_providers": len([p for p in status.values() if p["available"]]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting provider status: {str(e)}")

@app.post("/optimize")
async def optimize_routing():
    """Trigger routing optimization"""
    if not sophia_orchestrator or not hasattr(sophia_orchestrator, 'api_router'):
        raise HTTPException(status_code=503, detail="API router not available")
    
    try:
        await sophia_orchestrator.api_router.optimize_routing()
        return {
            "status": "optimization_completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

if __name__ == "__main__":
    print("🌟 Starting Sophia Chat Service")
    print("="*50)
    print("Features:")
    print("- Enhanced Intelligence Chat API")
    print("- Dynamic API Provider Routing")
    print("- AGNO Swarm Orchestration")
    print("- Real-time WebSocket Support")
    print("- Dashboard Integration Ready")
    print("="*50)
    
    uvicorn.run(
        "sophia_chat_service:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )