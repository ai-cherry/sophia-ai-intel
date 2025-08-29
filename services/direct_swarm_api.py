#!/usr/bin/env python3
"""
Direct Swarm API - Actually executes swarms and returns real results
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import uuid
from datetime import datetime

# Import the real executor
from real_swarm_executor import execute_swarm_task

app = FastAPI(title="Direct Swarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SwarmRequest(BaseModel):
    swarm_type: str
    task: str
    context: Optional[Dict] = {}

class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = "research"

@app.get("/")
async def root():
    return {
        "service": "Direct Swarm API",
        "status": "active",
        "message": "This actually executes swarms and returns real results"
    }

@app.post("/execute")
async def execute_swarm(request: SwarmRequest):
    """Direct execution endpoint that actually works"""
    
    print(f"\n{'='*60}")
    print(f"EXECUTING {request.swarm_type.upper()} SWARM")
    print(f"Task: {request.task}")
    print(f"{'='*60}\n")
    
    # Execute the swarm with real functionality
    result = await execute_swarm_task(
        swarm_type=request.swarm_type,
        task=request.task,
        context=request.context
    )
    
    # Format the response based on swarm type
    if request.swarm_type == "coding":
        if result.get("code"):
            print(f"\n📝 GENERATED CODE:")
            print(f"{'-'*40}")
            print(result["code"][:500])
            print(f"{'-'*40}\n")
            
            return {
                "success": True,
                "swarm_type": request.swarm_type,
                "task": request.task,
                "code": result.get("code"),
                "language": result.get("language", "python"),
                "summary": result.get("summary"),
                "github_pr": result.get("github_pr"),
                "task_id": result.get("task_id")
            }
    
    elif request.swarm_type == "research":
        if result.get("results"):
            print(f"\n🔍 RESEARCH RESULTS: {len(result.get('results', []))} found")
            print(f"Sources: {', '.join(result.get('sources_used', []))}")
            
            return {
                "success": True,
                "swarm_type": request.swarm_type,
                "task": request.task,
                "results": result.get("results", []),
                "sources_used": result.get("sources_used", []),
                "summary": result.get("summary"),
                "total_results": result.get("total_results", 0),
                "task_id": result.get("task_id")
            }
    
    elif request.swarm_type == "planning":
        if result.get("plans"):
            plans = result["plans"]
            print(f"\n📋 PLANNING COMPLETE")
            print(f"Recommendation: {result.get('recommendation', 'synthesis')}")
            
            return {
                "success": True,
                "swarm_type": request.swarm_type,
                "task": request.task,
                "plans": plans,
                "recommendation": result.get("recommendation"),
                "summary": result.get("summary"),
                "task_id": result.get("task_id")
            }
    
    elif request.swarm_type == "analysis":
        if result.get("analysis"):
            analysis = result["analysis"]
            print(f"\n📊 ANALYSIS COMPLETE")
            print(f"Insights: {len(analysis.get('insights', []))}")
            
            return {
                "success": True,
                "swarm_type": request.swarm_type,
                "task": request.task,
                "analysis": analysis,
                "summary": result.get("summary"),
                "task_id": result.get("task_id")
            }
    
    # Default response
    return {
        "success": True,
        "swarm_type": request.swarm_type,
        "task": request.task,
        "result": result,
        "task_id": result.get("task_id")
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint that maps to appropriate swarm"""
    
    # Determine swarm type based on message content - better detection
    message_lower = request.message.lower()
    
    # More specific coding detection
    coding_keywords = ["write", "code", "function", "class", "implement", "create", "build", "develop", 
                       "python", "javascript", "algorithm", "script", "program", "api", "component"]
    planning_keywords = ["plan", "design", "architect", "strategy", "roadmap", "blueprint", "outline"]
    analysis_keywords = ["analyze", "compare", "evaluate", "assess", "review", "examine", "study"]
    
    # Check for coding first (most specific)
    if any(word in message_lower for word in coding_keywords) and not any(word in message_lower for word in ["research", "find", "search"]):
        swarm_type = "coding"
    elif any(word in message_lower for word in planning_keywords):
        swarm_type = "planning"
    elif any(word in message_lower for word in analysis_keywords):
        swarm_type = "analysis"
    else:
        swarm_type = "research"
    
    # Override with explicit agent type if provided
    agent_map = {
        "code": "coding",
        "coding": "coding",
        "research": "research",
        "planning": "planning",
        "analysis": "analysis"
    }
    
    if request.agent_type:
        swarm_type = agent_map.get(request.agent_type.lower(), swarm_type)
    
    print(f"\n💬 CHAT REQUEST")
    print(f"Message: {request.message}")
    print(f"Mapped to: {swarm_type} swarm\n")
    
    # Execute the appropriate swarm
    result = await execute_swarm_task(
        swarm_type=swarm_type,
        task=request.message,
        context={"source": "chat"}
    )
    
    # Format chat response
    response_text = ""
    
    if swarm_type == "coding" and result.get("code"):
        response_text = f"I've generated the code you requested:\n\n```python\n{result['code']}\n```\n\n{result.get('summary', '')}"
    
    elif swarm_type == "research" and result.get("results"):
        response_text = f"Here's what I found:\n\n"
        for i, res in enumerate(result["results"][:3], 1):
            response_text += f"{i}. **{res.get('title', 'Result')}**\n"
            response_text += f"   {res.get('content', '')[:200]}...\n\n"
        response_text += f"\n{result.get('summary', '')}"
    
    elif swarm_type == "planning" and result.get("plans"):
        plans = result["plans"]
        response_text = f"I've created a comprehensive plan with three approaches:\n\n"
        response_text += f"**Recommended: {result.get('recommendation', 'Synthesis').title()} Approach**\n\n"
        
        if "synthesis" in plans:
            response_text += "**Balanced Approach (Recommended):**\n"
            for step in plans["synthesis"]["steps"]:
                response_text += f"• {step}\n"
    
    elif swarm_type == "analysis" and result.get("analysis"):
        analysis = result["analysis"]
        response_text = f"Analysis Complete:\n\n"
        for insight in analysis.get("insights", []):
            response_text += f"• {insight}\n"
        
        metrics = analysis.get("metrics", {})
        if metrics:
            response_text += f"\n**Confidence:** {metrics.get('confidence', 0) * 100:.0f}%"
    
    else:
        response_text = result.get("summary", "Task completed successfully")
    
    return {
        "response": response_text,
        "swarm_type": swarm_type,
        "task_id": result.get("task_id"),
        "timestamp": datetime.now().isoformat(),
        "raw_result": result
    }

@app.get("/test/{swarm_type}")
async def test_swarm(swarm_type: str):
    """Test endpoint for each swarm type"""
    
    test_tasks = {
        "coding": "Write a Python function that implements binary search on a sorted list",
        "research": "What are the latest developments in quantum computing 2024",
        "planning": "Create a plan for building a real-time chat application",
        "analysis": "Analyze the pros and cons of microservices architecture"
    }
    
    if swarm_type not in test_tasks:
        raise HTTPException(status_code=400, detail=f"Unknown swarm type: {swarm_type}")
    
    task = test_tasks[swarm_type]
    
    result = await execute_swarm_task(
        swarm_type=swarm_type,
        task=task,
        context={"test": True}
    )
    
    return {
        "test": True,
        "swarm_type": swarm_type,
        "task": task,
        "result": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)