#!/usr/bin/env python3
"""
Sophia Simple Chat Service - FastAPI Service for Dashboard Integration
====================================================================

A lightweight version of the Sophia chat service that integrates with 
the dynamic API router and provides enhanced intelligence capabilities.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
import uvicorn
from datetime import datetime
import os
import sys

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import our dynamic API router
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from sophia_dynamic_api_router import SophiaDynamicAPIRouter, RouteRequest, RequestType
    api_router_available = True
    logger.info("✅ Dynamic API Router imported successfully")
except ImportError as e:
    api_router_available = False
    logger.warning(f"⚠️ Dynamic API Router not available: {e}")
    SophiaDynamicAPIRouter = None
    RouteRequest = None
    RequestType = None

# Initialize FastAPI app
app = FastAPI(
    title="Sophia Simple Chat Service",
    description="Enhanced AI Chat Service with Dynamic API Routing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global API router
api_router: Optional[SophiaDynamicAPIRouter] = None

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

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global api_router
    logger.info("🚀 Starting Sophia Simple Chat Service...")
    
    if api_router_available and SophiaDynamicAPIRouter:
        try:
            api_router = SophiaDynamicAPIRouter()
            logger.info("✅ Dynamic API Router initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize API Router: {e}")
            api_router = None
    else:
        logger.warning("⚠️ Running without dynamic API routing")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Sophia Simple Chat Service",
        "status": "active",
        "api_router_available": api_router is not None,
        "version": "1.0.0",
        "capabilities": [
            "Enhanced Chat Interface",
            "Dynamic API Routing" if api_router else "Basic Responses",
            "Multiple Provider Support" if api_router else "Fallback Mode"
        ]
    }

@app.get("/status")
async def get_status():
    """Get service status"""
    provider_status = {}
    if api_router:
        try:
            provider_status = await api_router.get_provider_status()
        except Exception as e:
            logger.warning(f"Could not get provider status: {e}")
    
    return {
        "service_status": "active",
        "api_router_available": api_router is not None,
        "available_providers": len([p for p in provider_status.values() if p.get("available", False)]) if provider_status else 0,
        "total_providers": len(provider_status) if provider_status else 0,
        "capabilities": [
            "Chat Processing",
            "API Routing" if api_router else "Fallback Mode",
            "Multi-Provider Intelligence" if api_router else "Basic Responses"
        ]
    }

async def generate_intelligent_response(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate intelligent response using available APIs"""
    start_time = datetime.now()
    
    if not api_router:
        # Fallback response
        return {
            "response": f"I received your message: '{message}'. I'm currently running in basic mode. For enhanced intelligence with web search, research capabilities, and multi-provider API access, please ensure all services are properly configured.",
            "processing_method": "basic_fallback",
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "api_providers_used": [],
            "quality_score": 0.6,
            "metadata": {"mode": "fallback"}
        }
    
    try:
        # Analyze request intent
        request_type = await api_router.analyze_request_intent(message, context)
        logger.info(f"🎯 Request classified as: {request_type.value}")
        
        # Create route request
        route_request = RouteRequest(
            query=message,
            request_type=request_type,
            context=context,
            user_preferences={},
            max_providers=2
        )
        
        # Execute API routing
        api_responses = await api_router.execute_request(route_request)
        
        # Process responses
        successful_responses = [r for r in api_responses if r.success]
        
        if successful_responses:
            # Synthesize responses from multiple providers
            response_texts = []
            providers_used = []
            total_confidence = 0
            
            for api_response in successful_responses:
                providers_used.append(api_response.provider.value)
                total_confidence += api_response.confidence
                
                # Extract response content based on provider
                if api_response.provider.value == "perplexity":
                    content = api_response.data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        response_texts.append(f"🧠 **Perplexity AI Analysis:**\n{content}")
                
                elif api_response.provider.value == "tavily":
                    answer = api_response.data.get("answer", "")
                    results = api_response.data.get("results", [])
                    if answer:
                        response_texts.append(f"🔍 **Tavily Research:**\n{answer}")
                    if results:
                        sources = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('url', '')}" for r in results[:3]])
                        response_texts.append(f"📚 **Sources:**\n{sources}")
                
                elif api_response.provider.value == "serper":
                    organic = api_response.data.get("organic", [])
                    if organic:
                        search_results = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in organic[:3]])
                        response_texts.append(f"🌐 **Web Search Results:**\n{search_results}")
            
            # Create comprehensive response
            if response_texts:
                final_response = f"Here's what I found regarding your query: '{message}'\n\n" + "\n\n".join(response_texts)
                avg_confidence = total_confidence / len(successful_responses)
                quality_score = min(0.95, avg_confidence)
            else:
                final_response = f"I processed your query '{message}' using {len(providers_used)} API providers, but didn't get detailed content. The providers confirmed they processed your request successfully."
                quality_score = 0.7
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": final_response,
                "processing_method": "dynamic_api_routing",
                "execution_time": execution_time,
                "api_providers_used": providers_used,
                "quality_score": quality_score,
                "metadata": {
                    "request_type": request_type.value,
                    "successful_providers": len(successful_responses),
                    "total_providers": len(api_responses)
                }
            }
        else:
            # No successful API responses
            return {
                "response": f"I attempted to research '{message}' using multiple intelligence providers, but they're currently unavailable. I can still help with general questions and coding tasks.",
                "processing_method": "api_unavailable",
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "api_providers_used": [],
                "quality_score": 0.5,
                "metadata": {"providers_attempted": len(api_responses)}
            }
            
    except Exception as e:
        logger.error(f"Error in intelligent response generation: {e}")
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "response": f"I encountered an issue while processing '{message}': {str(e)}. I'm still here to help with other questions!",
            "processing_method": "error_fallback",
            "execution_time": execution_time,
            "api_providers_used": [],
            "quality_score": 0.3,
            "metadata": {"error": str(e)}
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        logger.info(f"💬 Chat request from session {request.session_id}: {request.message[:50]}...")
        
        # Generate intelligent response
        result = await generate_intelligent_response(request.message, request.context)
        
        # Create response
        response = ChatResponse(
            response=result["response"],
            session_id=request.session_id,
            processing_method=result["processing_method"],
            execution_time=result["execution_time"],
            api_providers_used=result["api_providers_used"],
            quality_score=result["quality_score"],
            metadata=result["metadata"],
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Response generated in {response.execution_time:.2f}s (quality: {response.quality_score:.2f})")
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/providers")
async def get_providers():
    """Get available API providers"""
    if not api_router:
        return {"providers": {}, "message": "API router not available"}
    
    try:
        status = await api_router.get_provider_status()
        return {
            "providers": status,
            "total": len(status),
            "active": len([p for p in status.values() if p["available"]])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting providers: {str(e)}")

if __name__ == "__main__":
    print("🌟 Starting Sophia Simple Chat Service")
    print("="*50)
    print("Features:")
    print("- Enhanced Chat Interface")
    print("- Dynamic API Provider Routing") 
    print("- Multi-Provider Intelligence")
    print("- Dashboard Integration")
    print("="*50)
    
    uvicorn.run(
        "sophia_chat_simple:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )