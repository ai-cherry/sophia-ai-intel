"""
Sophia AI Agent Swarm MCP Service

MCP service that provides AI agent swarm capabilities including:
- Repository analysis and code intelligence  
- Multi-agent planning and synthesis
- Code generation workflows
- Quality assessment and recommendations

Key Features:
- Integration with existing MCP services
- LangGraph-powered workflow orchestration
- Embedding-based code understanding
- Human approval workflows
- Real-time task tracking

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our agent swarm components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../libs'))

from agents.swarm_manager import (
    SophiaAgentSwarmManager, 
    SwarmConfiguration, 
    SwarmTaskRequest,
    process_chat_request
)
from agents.base_agent import AgentRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Lambda Labs Infrastructure
DASHBOARD_ORIGIN = os.getenv("DASHBOARD_ORIGIN", "http://sophia-dashboard:3000")
GITHUB_MCP_URL = os.getenv("GITHUB_MCP_URL", "http://sophia-github:8080")
CONTEXT_MCP_URL = os.getenv("CONTEXT_MCP_URL", "http://sophia-context:8080")
RESEARCH_MCP_URL = os.getenv("RESEARCH_MCP_URL", "http://sophia-research:8080")
BUSINESS_MCP_URL = os.getenv("BUSINESS_MCP_URL", "http://sophia-business:8080")

# Global swarm manager
swarm_manager: Optional[SophiaAgentSwarmManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global swarm_manager
    
    try:
        logger.info("Initializing Agent Swarm Service")
        
        # Configure MCP clients
        mcp_clients = {
            'github': create_github_client(),
            'context': create_context_client(), 
            'research': create_research_client()
        }
        
        # Create swarm configuration
        config = SwarmConfiguration(
            max_concurrent_workflows=3,
            default_timeout_seconds=1800,
            enable_human_approval=True,
            embedding_model="all-mpnet-base-v2",
            llm_models={
                'cutting_edge': 'gpt-5',
                'conservative': 'claude-3.5-sonnet', 
                'synthesis': 'gpt-5',
                'repository': 'gpt-4o',
                'default': 'gpt-5'
            }
        )
        
        # Initialize swarm manager
        swarm_manager = SophiaAgentSwarmManager(config, mcp_clients)
        success = await swarm_manager.initialize()
        
        if not success:
            logger.error(f"Failed to initialize swarm: {swarm_manager.initialization_error}")
        else:
            logger.info("Agent Swarm Service initialized successfully")
        
        yield
        
        # Shutdown
        if swarm_manager:
            await swarm_manager.shutdown()
        logger.info("Agent Swarm Service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during lifespan management: {e}")
        yield


# Create FastAPI app with lifespan
app = FastAPI(
    title="Sophia AI Agent Swarm Service",
    description="AI agent swarm for repository analysis, code generation, and intelligent planning",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[DASHBOARD_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatProcessRequest(BaseModel):
    message: str = Field(..., description="The chat message to process")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")


class SwarmTaskCreateRequest(BaseModel):
    task_description: str = Field(..., description="Description of the task")
    task_type: str = Field("repository_analysis", description="Type of task to execute")
    priority: str = Field("medium", description="Task priority level")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional task context")


class SwarmStatusResponse(BaseModel):
    is_initialized: bool
    total_agents: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    system_status: str


# Helper functions for MCP client creation
def create_github_client():
    """Create GitHub MCP client interface"""
    class GitHubMCPClient:
        def __init__(self):
            self.base_url = GITHUB_MCP_URL
            
        async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None):
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                return response.json() if response.status_code == 200 else None
    
    return GitHubMCPClient()


def create_context_client():
    """Create Context MCP client interface"""
    class ContextMCPClient:
        def __init__(self):
            self.base_url = CONTEXT_MCP_URL
            
        async def post(self, endpoint: str, data: Dict[str, Any]):
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}{endpoint}", json=data)
                return response.json() if response.status_code == 200 else None
    
    return ContextMCPClient()


def create_research_client():
    """Create Research MCP client interface"""
    class ResearchMCPClient:
        def __init__(self):
            self.base_url = RESEARCH_MCP_URL
            
        async def post(self, endpoint: str, data: Dict[str, Any]):
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}{endpoint}", json=data)
                return response.json() if response.status_code == 200 else None
    
    return ResearchMCPClient()


# API Endpoints
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    global swarm_manager
    
    health_status = {
        "service": "sophia-mcp-agents",
        "version": "1.0.0", 
        "status": "healthy",
        "timestamp": "2025-01-25T13:01:40Z",
        "swarm_initialized": swarm_manager is not None and swarm_manager.is_initialized,
        "swarm_error": swarm_manager.initialization_error if swarm_manager else None
    }
    
    if swarm_manager and not swarm_manager.is_initialized:
        health_status["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=health_status)
    
    return health_status


@app.post("/agent-swarm/process")
async def process_chat_message(request: ChatProcessRequest):
    """Process a chat message using the agent swarm"""
    global swarm_manager
    
    if not swarm_manager or not swarm_manager.is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Agent swarm not initialized"
        )
    
    try:
        result = await swarm_manager.process_chat_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@app.post("/agent-swarm/task")
async def create_swarm_task(request: SwarmTaskCreateRequest, background_tasks: BackgroundTasks):
    """Create and execute a swarm task"""
    global swarm_manager
    
    if not swarm_manager or not swarm_manager.is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Agent swarm not initialized"
        )
    
    try:
        # Create task request
        task_request = SwarmTaskRequest(
            task_description=request.task_description,
            task_type=request.task_type,
            priority=request.priority,
            context=request.context or {}
        )
        
        # Execute task asynchronously
        task_id = await swarm_manager.execute_task(task_request)
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created and processing started"
        }
        
    except Exception as e:
        logger.error(f"Error creating swarm task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@app.get("/agent-swarm/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        task_status = await swarm_manager.get_task_status(task_id)
        
        if task_status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@app.get("/agent-swarm/task/{task_id}/result")
async def get_task_result(task_id: str):
    """Get detailed result of a completed task"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        task_result = await swarm_manager.get_task_result(task_id)
        
        if task_result is None:
            raise HTTPException(status_code=404, detail="Task result not found")
        
        return task_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task result: {str(e)}"
        )


@app.get("/agent-swarm/status")
async def get_swarm_status():
    """Get overall agent swarm status"""
    global swarm_manager
    
    if not swarm_manager:
        return SwarmStatusResponse(
            is_initialized=False,
            total_agents=0,
            active_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            system_status="not_initialized"
        )
    
    try:
        status = await swarm_manager.get_swarm_status()
        
        return SwarmStatusResponse(
            is_initialized=status['is_initialized'],
            total_agents=status['total_agents'],
            active_tasks=status['active_tasks'],
            completed_tasks=status['completed_tasks'],
            failed_tasks=status['failed_tasks'],
            system_status="healthy" if status['is_initialized'] else "unhealthy"
        )
        
    except Exception as e:
        logger.error(f"Error getting swarm status: {e}")
        return SwarmStatusResponse(
            is_initialized=False,
            total_agents=0,
            active_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            system_status="error"
        )


@app.get("/agent-swarm/summary")
async def get_swarm_summary():
    """Get swarm summary for chat display"""
    global swarm_manager
    
    if not swarm_manager:
        return {
            "summary": "⚠️ Agent swarm is not initialized.",
            "status": "not_initialized"
        }
    
    try:
        summary = swarm_manager.get_swarm_summary()
        return {
            "summary": summary,
            "status": "initialized" if swarm_manager.is_initialized else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting swarm summary: {e}")
        return {
            "summary": f"Error getting swarm summary: {str(e)}",
            "status": "error"
        }


@app.get("/agent-swarm/agents")
async def get_agent_list():
    """Get list of available agents"""
    global swarm_manager
    
    if not swarm_manager:
        return {"agents": []}
    
    try:
        status = await swarm_manager.get_swarm_status()
        return {
            "agents": status.get('agent_statuses', {}),
            "total_agents": status.get('total_agents', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent list: {e}")
        return {"agents": [], "error": str(e)}


@app.get("/agent-swarm/metrics")
async def get_swarm_metrics():
    """Get detailed swarm metrics"""
    global swarm_manager
    
    if not swarm_manager:
        return {"metrics": {}, "error": "Swarm not initialized"}
    
    try:
        metrics = await swarm_manager.get_agent_metrics()
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Error getting swarm metrics: {e}")
        return {"metrics": {}, "error": str(e)}


@app.post("/agent-swarm/approve/{workflow_id}")
async def approve_workflow(workflow_id: str, approved: bool, comments: Optional[str] = None):
    """Process human approval for a workflow"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        success = await swarm_manager.process_human_approval(workflow_id, approved, comments)
        
        return {
            "workflow_id": workflow_id,
            "approved": approved,
            "processed": success,
            "comments": comments
        }
        
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process approval: {str(e)}"
        )


# Repository-specific endpoints
@app.get("/repository/analyze")
async def analyze_repository():
    """Quick repository analysis endpoint"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        # Create a repository analysis task
        task_request = SwarmTaskRequest(
            task_description="Analyze the current repository structure, patterns, and quality",
            task_type="repository_analysis",
            priority="medium"
        )
        
        task_id = await swarm_manager.execute_task(task_request)
        
        # Wait briefly for quick analysis
        await asyncio.sleep(5)
        
        # Try to get results
        result = await swarm_manager.get_task_result(task_id)
        
        if result:
            return {
                "task_id": task_id,
                "status": "completed",
                "analysis": result
            }
        else:
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Analysis in progress, check back later"
            }
            
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Repository analysis failed: {str(e)}"
        )


@app.get("/repository/patterns")
async def get_repository_patterns():
    """Get detected repository patterns"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        task_request = SwarmTaskRequest(
            task_description="Identify architectural and design patterns in the repository",
            task_type="pattern_recognition",
            priority="low"
        )
        
        task_id = await swarm_manager.execute_task(task_request)
        
        # Wait for pattern analysis
        await asyncio.sleep(3)
        
        result = await swarm_manager.get_task_result(task_id)
        
        return {
            "task_id": task_id,
            "patterns": result.get("patterns", {}) if result else {},
            "status": "completed" if result else "processing"
        }
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pattern analysis failed: {str(e)}"
        )


# Development and testing endpoints
@app.get("/debug/swarm-config")
async def get_swarm_config():
    """Get swarm configuration for debugging"""
    global swarm_manager
    
    if not swarm_manager:
        return {"config": None, "error": "Swarm not initialized"}
    
    return {
        "config": {
            "max_concurrent_workflows": swarm_manager.config.max_concurrent_workflows,
            "default_timeout_seconds": swarm_manager.config.default_timeout_seconds,
            "enable_human_approval": swarm_manager.config.enable_human_approval,
            "embedding_model": swarm_manager.config.embedding_model,
            "llm_models": swarm_manager.config.llm_models
        },
        "initialized": swarm_manager.is_initialized,
        "initialization_error": swarm_manager.initialization_error
    }


@app.post("/debug/test-swarm")
async def test_swarm():
    """Test the swarm system with a simple task"""
    global swarm_manager
    
    if not swarm_manager:
        raise HTTPException(status_code=503, detail="Agent swarm not available")
    
    try:
        test_result = await process_chat_request(
            message="Analyze this repository and tell me about its structure",
            session_id="test_session",
            user_id="test_user",
            mcp_clients={
                'github': create_github_client(),
                'context': create_context_client(),
                'research': create_research_client()
            }
        )
        
        return {
            "test_result": test_result,
            "status": "success",
            "timestamp": "2025-01-25T13:01:40Z"
        }
        
    except Exception as e:
        logger.error(f"Swarm test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Swarm test failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
