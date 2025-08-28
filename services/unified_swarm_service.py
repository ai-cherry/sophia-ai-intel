"""
Unified Swarm Service API
Consolidates all swarm implementations into a single service
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the canonical SwarmManager
try:
    from libs.agents.swarm_manager import SwarmManager, SwarmConfiguration
except ImportError:
    print("Warning: SwarmManager not found, using mock implementation")
    SwarmManager = None
    SwarmConfiguration = None

app = FastAPI(
    title="Unified Swarm Service",
    version="1.0.0",
    description="Single API for all swarm operations"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SwarmType(str, Enum):
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    PLANNING = "planning"


class PlannerType(str, Enum):
    CUTTING_EDGE = "cutting_edge"
    CONSERVATIVE = "conservative"
    SYNTHESIS = "synthesis"


class SwarmRequest(BaseModel):
    swarm_type: SwarmType
    task: str
    context: Optional[Dict[str, Any]] = {}
    config: Optional[Dict[str, Any]] = {}


class AgentInfo(BaseModel):
    id: str
    name: str
    type: str
    capabilities: List[str]
    status: str = "idle"


class PlanResponse(BaseModel):
    planner_type: PlannerType
    plan: str
    risk_assessment: Optional[Dict[str, Any]] = {}
    artifacts: Optional[List[str]] = []


class SwarmStatus(BaseModel):
    swarm_id: str
    swarm_type: SwarmType
    status: str
    agents: List[AgentInfo]
    current_task: Optional[str] = None
    progress: float = 0.0
    results: Optional[Dict[str, Any]] = None


class UnifiedSwarmService:
    """
    Unified service that delegates to SwarmManager and other implementations
    """
    
    def __init__(self):
        self.swarm_manager = SwarmManager() if SwarmManager else None
        self.active_swarms = {}
        self.planners = {
            PlannerType.CUTTING_EDGE: self.create_cutting_edge_planner(),
            PlannerType.CONSERVATIVE: self.create_conservative_planner(),
            PlannerType.SYNTHESIS: self.create_synthesis_planner()
        }
    
    def create_cutting_edge_planner(self):
        """Create cutting-edge planner agent"""
        return {
            "id": "cutting_edge_planner",
            "name": "Cutting-Edge Planner",
            "type": "planner",
            "persona": "innovative and experimental",
            "capabilities": ["explore new technologies", "propose novel solutions", "high-risk high-reward strategies"]
        }
    
    def create_conservative_planner(self):
        """Create conservative planner agent"""
        return {
            "id": "conservative_planner",
            "name": "Conservative Planner",
            "type": "planner",
            "persona": "stable and proven",
            "capabilities": ["use established patterns", "minimize risk", "ensure reliability"]
        }
    
    def create_synthesis_planner(self):
        """Create synthesis/mediator planner agent"""
        return {
            "id": "synthesis_planner",
            "name": "Synthesis Planner",
            "type": "mediator",
            "persona": "balanced and pragmatic",
            "capabilities": ["synthesize multiple viewpoints", "resolve conflicts", "create unified plans"]
        }
    
    async def create_swarm(self, request: SwarmRequest) -> str:
        """Create and deploy a new swarm"""
        swarm_id = str(uuid.uuid4())
        
        # Create swarm configuration
        swarm_config = {
            "swarm_id": swarm_id,
            "swarm_type": request.swarm_type,
            "task": request.task,
            "context": request.context,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Initialize agents based on swarm type
        agents = []
        
        if request.swarm_type == SwarmType.CODING:
            agents = [
                AgentInfo(id="architect", name="Code Architect", type="orchestrator", 
                         capabilities=["system design", "architecture planning"]),
                AgentInfo(id="frontend", name="Frontend Specialist", type="developer",
                         capabilities=["React", "TypeScript", "UI/UX"]),
                AgentInfo(id="backend", name="Backend Specialist", type="developer",
                         capabilities=["Python", "FastAPI", "databases"]),
                AgentInfo(id="reviewer", name="Code Reviewer", type="quality",
                         capabilities=["code review", "best practices", "security"])
            ]
        
        elif request.swarm_type == SwarmType.RESEARCH:
            agents = [
                AgentInfo(id="coordinator", name="Research Coordinator", type="orchestrator",
                         capabilities=["research planning", "synthesis"]),
                AgentInfo(id="web_researcher", name="Web Researcher", type="researcher",
                         capabilities=["web search", "data extraction"]),
                AgentInfo(id="academic", name="Academic Researcher", type="researcher",
                         capabilities=["papers", "citations", "analysis"]),
                AgentInfo(id="analyst", name="Data Analyst", type="analyzer",
                         capabilities=["statistics", "insights", "visualization"])
            ]
        
        elif request.swarm_type == SwarmType.PLANNING:
            # Use the three-planner system
            agents = [
                AgentInfo(id="cutting_edge", name="Cutting-Edge Planner", type="planner",
                         capabilities=["innovative solutions", "experimental approaches"]),
                AgentInfo(id="conservative", name="Conservative Planner", type="planner",
                         capabilities=["stable patterns", "proven methods"]),
                AgentInfo(id="synthesis", name="Synthesis Planner", type="mediator",
                         capabilities=["conflict resolution", "plan synthesis"])
            ]
        
        # Store swarm information
        self.active_swarms[swarm_id] = SwarmStatus(
            swarm_id=swarm_id,
            swarm_type=request.swarm_type,
            status="initializing",
            agents=agents,
            current_task=request.task
        )
        
        # If SwarmManager is available, delegate to it
        if self.swarm_manager:
            try:
                # Create SwarmConfiguration and execute
                if SwarmConfiguration:
                    config = SwarmConfiguration(
                        task_type=request.swarm_type.value,
                        max_iterations=5,
                        timeout=300
                    )
                    # Start async task execution
                    asyncio.create_task(self.execute_with_swarm_manager(swarm_id, request.task, config))
            except Exception as e:
                print(f"SwarmManager execution failed: {e}")
        
        # Update status
        self.active_swarms[swarm_id].status = "active"
        
        return swarm_id
    
    async def execute_with_swarm_manager(self, swarm_id: str, task: str, config: Any):
        """Execute task using SwarmManager"""
        try:
            result = await self.swarm_manager.execute_task(task, config)
            self.active_swarms[swarm_id].status = "completed"
            self.active_swarms[swarm_id].results = result
            self.active_swarms[swarm_id].progress = 1.0
        except Exception as e:
            self.active_swarms[swarm_id].status = "failed"
            self.active_swarms[swarm_id].results = {"error": str(e)}
    
    async def generate_plans(self, task: str, context: Dict[str, Any]) -> Dict[PlannerType, PlanResponse]:
        """Generate plans from all three planners"""
        plans = {}
        
        # Cutting-edge plan
        plans[PlannerType.CUTTING_EDGE] = PlanResponse(
            planner_type=PlannerType.CUTTING_EDGE,
            plan=f"Innovative approach for {task}:\n1. Use latest AI models\n2. Implement experimental patterns\n3. Leverage cutting-edge tools",
            risk_assessment={"risk_level": "high", "innovation_score": 9},
            artifacts=["new_architecture.md", "experimental_code.py"]
        )
        
        # Conservative plan
        plans[PlannerType.CONSERVATIVE] = PlanResponse(
            planner_type=PlannerType.CONSERVATIVE,
            plan=f"Stable approach for {task}:\n1. Use proven patterns\n2. Follow best practices\n3. Ensure backward compatibility",
            risk_assessment={"risk_level": "low", "stability_score": 9},
            artifacts=["standard_implementation.py", "tests.py"]
        )
        
        # Synthesis plan (mediator)
        plans[PlannerType.SYNTHESIS] = PlanResponse(
            planner_type=PlannerType.SYNTHESIS,
            plan=f"Balanced approach for {task}:\n1. Adopt proven core with innovative features\n2. Phase rollout: stable base, then experimental\n3. Include fallback mechanisms",
            risk_assessment={"risk_level": "medium", "balance_score": 8},
            artifacts=["phased_implementation.py", "rollback_plan.md"]
        )
        
        return plans
    
    def get_swarm_status(self, swarm_id: str) -> Optional[SwarmStatus]:
        """Get status of a specific swarm"""
        return self.active_swarms.get(swarm_id)
    
    def list_active_swarms(self) -> List[SwarmStatus]:
        """List all active swarms"""
        return list(self.active_swarms.values())
    
    def get_available_agents(self) -> List[AgentInfo]:
        """Get list of all available agent types"""
        return [
            # Coding agents
            AgentInfo(id="code_architect", name="Code Architect", type="orchestrator",
                     capabilities=["system design", "architecture", "planning"]),
            AgentInfo(id="frontend_dev", name="Frontend Developer", type="developer",
                     capabilities=["React", "Vue", "Angular", "UI/UX"]),
            AgentInfo(id="backend_dev", name="Backend Developer", type="developer",
                     capabilities=["Python", "Node.js", "databases", "APIs"]),
            AgentInfo(id="devops", name="DevOps Engineer", type="infrastructure",
                     capabilities=["Docker", "Kubernetes", "CI/CD", "cloud"]),
            
            # Research agents
            AgentInfo(id="web_scraper", name="Web Scraper", type="researcher",
                     capabilities=["web search", "data extraction", "crawling"]),
            AgentInfo(id="academic_miner", name="Academic Miner", type="researcher",
                     capabilities=["paper search", "citations", "academic analysis"]),
            AgentInfo(id="patent_hunter", name="Patent Hunter", type="researcher",
                     capabilities=["patent search", "IP analysis", "prior art"]),
            
            # Analysis agents
            AgentInfo(id="data_analyst", name="Data Analyst", type="analyzer",
                     capabilities=["statistics", "visualization", "insights"]),
            AgentInfo(id="sentiment_analyzer", name="Sentiment Analyzer", type="analyzer",
                     capabilities=["sentiment analysis", "opinion mining", "trends"]),
            
            # Planning agents (three-planner system)
            AgentInfo(id="cutting_edge_planner", name="Cutting-Edge Planner", type="planner",
                     capabilities=["innovative solutions", "experimental", "high-risk"]),
            AgentInfo(id="conservative_planner", name="Conservative Planner", type="planner",
                     capabilities=["stable patterns", "proven methods", "low-risk"]),
            AgentInfo(id="synthesis_planner", name="Synthesis Planner", type="mediator",
                     capabilities=["mediation", "synthesis", "conflict resolution"])
        ]


# Initialize service
service = UnifiedSwarmService()


@app.get("/")
async def root():
    return {
        "service": "Unified Swarm Service",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/swarms - List active swarms",
            "/swarms/create - Create new swarm",
            "/swarms/{id}/status - Get swarm status",
            "/agents - List available agents",
            "/plans - Generate plans from three-planner system"
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_swarms": len(service.active_swarms),
        "swarm_manager": "connected" if service.swarm_manager else "not available"
    }


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all available agent types"""
    return service.get_available_agents()


@app.post("/swarms/create")
async def create_swarm(request: SwarmRequest):
    """Create and deploy a new swarm"""
    try:
        swarm_id = await service.create_swarm(request)
        return {
            "success": True,
            "swarm_id": swarm_id,
            "message": f"{request.swarm_type} swarm created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/swarms", response_model=List[SwarmStatus])
async def list_swarms():
    """List all active swarms"""
    return service.list_active_swarms()


@app.get("/swarms/{swarm_id}/status", response_model=SwarmStatus)
async def get_swarm_status(swarm_id: str):
    """Get status of a specific swarm"""
    status = service.get_swarm_status(swarm_id)
    if not status:
        raise HTTPException(status_code=404, detail="Swarm not found")
    return status


@app.post("/plans")
async def generate_plans(task: str, context: Optional[Dict[str, Any]] = None):
    """Generate plans using three-planner system"""
    plans = await service.generate_plans(task, context or {})
    
    return {
        "task": task,
        "plans": {
            "cutting_edge": plans[PlannerType.CUTTING_EDGE].dict(),
            "conservative": plans[PlannerType.CONSERVATIVE].dict(),
            "synthesis": plans[PlannerType.SYNTHESIS].dict()
        },
        "recommendation": "Use synthesis plan for balanced approach"
    }


@app.websocket("/ws/swarm/{swarm_id}")
async def swarm_websocket(websocket: WebSocket, swarm_id: str):
    """WebSocket for real-time swarm updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send swarm status updates
            status = service.get_swarm_status(swarm_id)
            if status:
                await websocket.send_json(status.dict())
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        print(f"Client disconnected from swarm {swarm_id}")


@app.post("/swarms/{swarm_id}/stop")
async def stop_swarm(swarm_id: str):
    """Stop a running swarm"""
    if swarm_id in service.active_swarms:
        service.active_swarms[swarm_id].status = "stopped"
        return {"success": True, "message": "Swarm stopped"}
    else:
        raise HTTPException(status_code=404, detail="Swarm not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("unified_swarm_service:app", host="0.0.0.0", port=8100, reload=True)