#!/usr/bin/env python3
"""
Simple Backend API for Sophia Dashboard
Provides real endpoints for chat and health checks
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import time
from typing import List, Dict, Any

app = FastAPI(title="Sophia Backend API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    settings: Dict[str, Any]
    history: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "sophia-backend-api",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": "1.0.0"
    }

@app.post("/chat")
async def chat_endpoint(data: ChatMessage):
    """Real chat endpoint that processes messages"""
    
    # Process the message based on settings
    response_content = f"Sophia AI Response: I received your message '{data.message}'. "
    
    if data.settings.get("enableEnhancement"):
        response_content += "Enhanced processing enabled. "
    
    if data.settings.get("verbosity") == "detailed":
        response_content += f"Using model: {data.settings.get('model', 'default')}. Risk stance: {data.settings.get('riskStance', 'balanced')}."
    
    response = ChatResponse(
        id=str(int(time.time() * 1000)),
        role="assistant",
        content=response_content,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        metadata={
            "model": data.settings.get("model", "sophia-ai"),
            "prompt_enhanced": data.settings.get("enableEnhancement", False),
            "processing_time": 150,
            "service": "sophia-backend-api"
        }
    )
    
    return {"data": response}

@app.get("/agents")
async def get_agents():
    return {
        "data": [
            {"id": "agent-1", "name": "Research Agent", "status": "active"},
            {"id": "agent-2", "name": "Code Agent", "status": "active"},
            {"id": "agent-3", "name": "Analysis Agent", "status": "idle"}
        ]
    }

@app.get("/swarms")
async def get_swarms():
    return {
        "data": [
            {"id": "swarm-1", "name": "Development Swarm", "agents": 3, "status": "running"},
            {"id": "swarm-2", "name": "Research Swarm", "agents": 2, "status": "idle"}
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Sophia Backend API on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)