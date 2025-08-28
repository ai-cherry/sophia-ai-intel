"""
Sophia AI Core Service - Consolidated MCP Agents, Context, Research
Domain: AI/ML capabilities, agent orchestration, vector search, research workflows
"""
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Import consolidated modules
from .agents import AgentOrchestrator
from .context import ContextManager  
from .research import ResearchEngine

class InferenceRequest(BaseModel):
    query: str
    agent_type: str = "general"
    context_limit: int = 10
    research_depth: int = 1

class InferenceResponse(BaseModel):
    result: str
    agent_used: str
    context_sources: List[str]
    research_citations: List[str]
    processing_time_ms: float

# Global instances
agent_orchestrator: AgentOrchestrator = None
context_manager: ContextManager = None
research_engine: ResearchEngine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_orchestrator, context_manager, research_engine
    
    # Initialize services
    agent_orchestrator = AgentOrchestrator()
    context_manager = ContextManager()
    research_engine = ResearchEngine()
    
    await agent_orchestrator.initialize()
    await context_manager.initialize()
    await research_engine.initialize()
    
    yield
    
    # Cleanup
    await agent_orchestrator.cleanup()
    await context_manager.cleanup()
    await research_engine.cleanup()

app = FastAPI(
    title="Sophia AI Core",
    description="Consolidated AI/ML service - agents, context, research",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "sophia-ai-core",
        "agents": await agent_orchestrator.health_check(),
        "context": await context_manager.health_check(),
        "research": await research_engine.health_check()
    }

@app.post("/inference", response_model=InferenceResponse)
async def ai_inference(request: InferenceRequest):
    import time
    start_time = time.time()
    
    try:
        # Get relevant context
        context_results = await context_manager.search(
            query=request.query,
            limit=request.context_limit
        )
        
        # Run research if needed
        research_results = []
        if request.research_depth > 0:
            research_results = await research_engine.research(
                query=request.query,
                depth=request.research_depth
            )
        
        # Generate response with agent
        agent_result = await agent_orchestrator.process(
            query=request.query,
            agent_type=request.agent_type,
            context=context_results,
            research=research_results
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return InferenceResponse(
            result=agent_result.response,
            agent_used=agent_result.agent_type,
            context_sources=[c.source for c in context_results],
            research_citations=[r.citation for r in research_results],
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_type}/execute")
async def execute_agent(agent_type: str, payload: Dict[str, Any]):
    return await agent_orchestrator.execute_specific(agent_type, payload)

@app.post("/context/index")
async def index_context(content: str, metadata: Dict[str, Any]):
    return await context_manager.index(content, metadata)

@app.get("/context/search")
async def search_context(query: str, limit: int = 10):
    return await context_manager.search(query, limit)

@app.post("/research/query")
async def research_query(query: str, depth: int = 1):
    return await research_engine.research(query, depth)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)