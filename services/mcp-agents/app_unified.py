"""
Unified Agents MCP Service
Manages AI agents and swarm coordination
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import asyncio
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_base.base import MCPService, MCPResponse, logger

# Request/Response models
class AgentCreateRequest(BaseModel):
    name: str
    capabilities: List[str]
    model: str = "gpt-4"
    system_prompt: str
    metadata: Optional[Dict] = {}

class TaskRequest(BaseModel):
    task_type: str
    description: str
    parameters: Dict[str, Any] = {}
    priority: int = 5
    timeout: Optional[int] = 300

class AgentResponse(BaseModel):
    agent_id: str
    name: str
    status: str
    capabilities: List[str]
    performance_score: float
    tasks_completed: int
    created_at: str
    last_active: str

class SwarmResponse(BaseModel):
    swarm_id: str
    name: str
    agents: List[str]
    status: str
    progress: float
    tasks_total: int
    tasks_completed: int

class AgentsMCPService(MCPService):
    """MCP Service for AI Agent Management and Orchestration"""
    
    def __init__(self):
        super().__init__(name="Agents MCP", version="2.0.0", port=8000)
        
        # In-memory storage (replace with database in production)
        self.agents: Dict[str, Dict] = {}
        self.swarms: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        
        # Register custom endpoints
        self.setup_endpoints()
        
        # Initialize some default agents
        self.initialize_default_agents()
        
    def initialize_default_agents(self):
        """Create default agents for testing"""
        default_agents = [
            {
                "id": "agent-research",
                "name": "Research Agent",
                "capabilities": ["web_search", "document_analysis", "summarization"],
                "model": "gpt-4",
                "status": "idle",
                "performance_score": 0.92,
                "tasks_completed": 145,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            },
            {
                "id": "agent-code",
                "name": "Code Agent",
                "capabilities": ["code_generation", "debugging", "optimization"],
                "model": "claude-3",
                "status": "idle",
                "performance_score": 0.88,
                "tasks_completed": 89,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            },
            {
                "id": "agent-analysis",
                "name": "Analysis Agent",
                "capabilities": ["data_analysis", "visualization", "reporting"],
                "model": "gpt-4",
                "status": "idle",
                "performance_score": 0.95,
                "tasks_completed": 203,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            }
        ]
        
        for agent in default_agents:
            self.agents[agent["id"]] = agent
            
        # Create a default swarm
        self.swarms["swarm-default"] = {
            "id": "swarm-default",
            "name": "Default Research Swarm",
            "agents": ["agent-research", "agent-analysis"],
            "status": "idle",
            "progress": 0.0,
            "tasks_total": 0,
            "tasks_completed": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
    def setup_endpoints(self):
        """Setup agent-specific endpoints"""
        
        @self.register_endpoint("/agents", "GET")
        async def list_agents():
            """List all available agents"""
            agents_list = [
                AgentResponse(
                    agent_id=agent["id"],
                    name=agent["name"],
                    status=agent["status"],
                    capabilities=agent["capabilities"],
                    performance_score=agent["performance_score"],
                    tasks_completed=agent["tasks_completed"],
                    created_at=agent["created_at"],
                    last_active=agent["last_active"]
                ).dict()
                for agent in self.agents.values()
            ]
            
            return {
                "agents": agents_list,
                "total": len(agents_list),
                "active": sum(1 for a in self.agents.values() if a["status"] == "busy")
            }
            
        @self.register_endpoint("/agents", "POST")
        async def create_agent(request: AgentCreateRequest):
            """Create a new AI agent"""
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            
            agent = {
                "id": agent_id,
                "name": request.name,
                "capabilities": request.capabilities,
                "model": request.model,
                "system_prompt": request.system_prompt,
                "metadata": request.metadata,
                "status": "idle",
                "performance_score": 0.5,  # Start with neutral score
                "tasks_completed": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            }
            
            self.agents[agent_id] = agent
            
            # Cache the agent
            await self.cache_set(f"agent:{agent_id}", agent, ttl=3600)
            
            logger.info(f"Created agent: {agent_id}")
            
            return {
                "agent_id": agent_id,
                "message": f"Agent '{request.name}' created successfully"
            }
            
        @self.register_endpoint("/agents/{agent_id}", "GET")
        async def get_agent(agent_id: str):
            """Get details of a specific agent"""
            # Try cache first
            cached = await self.cache_get(f"agent:{agent_id}")
            if cached:
                return cached
                
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
                
            agent = self.agents[agent_id]
            await self.cache_set(f"agent:{agent_id}", agent, ttl=600)
            
            return agent
            
        @self.register_endpoint("/agents/{agent_id}/execute", "POST")
        async def execute_task(agent_id: str, task: TaskRequest):
            """Execute a task with a specific agent"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
                
            agent = self.agents[agent_id]
            
            # Check if agent is available
            if agent["status"] == "busy":
                return MCPResponse.error(
                    "Agent is currently busy",
                    error_code="AGENT_BUSY"
                )
                
            # Create task
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            task_data = {
                "id": task_id,
                "agent_id": agent_id,
                "type": task.task_type,
                "description": task.description,
                "parameters": task.parameters,
                "priority": task.priority,
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
                "result": None
            }
            
            self.tasks[task_id] = task_data
            
            # Update agent status
            agent["status"] = "busy"
            agent["last_active"] = datetime.utcnow().isoformat()
            
            # Simulate task execution
            asyncio.create_task(self.simulate_task_execution(task_id, agent_id))
            
            return {
                "task_id": task_id,
                "agent_id": agent_id,
                "status": "accepted",
                "estimated_completion": 10  # seconds
            }
            
        @self.register_endpoint("/swarms", "GET")
        async def list_swarms():
            """List all agent swarms"""
            swarms_list = [
                SwarmResponse(
                    swarm_id=swarm["id"],
                    name=swarm["name"],
                    agents=swarm["agents"],
                    status=swarm["status"],
                    progress=swarm["progress"],
                    tasks_total=swarm["tasks_total"],
                    tasks_completed=swarm["tasks_completed"]
                ).dict()
                for swarm in self.swarms.values()
            ]
            
            return {
                "swarms": swarms_list,
                "total": len(swarms_list),
                "active": sum(1 for s in self.swarms.values() if s["status"] == "active")
            }
            
        @self.register_endpoint("/swarms", "POST")
        async def create_swarm(name: str, agent_ids: List[str]):
            """Create a new agent swarm"""
            # Validate agents exist
            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    return MCPResponse.error(
                        f"Agent {agent_id} not found",
                        error_code="INVALID_AGENT"
                    )
                    
            swarm_id = f"swarm-{uuid.uuid4().hex[:8]}"
            
            swarm = {
                "id": swarm_id,
                "name": name,
                "agents": agent_ids,
                "status": "idle",
                "progress": 0.0,
                "tasks_total": 0,
                "tasks_completed": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.swarms[swarm_id] = swarm
            
            return {
                "swarm_id": swarm_id,
                "message": f"Swarm '{name}' created with {len(agent_ids)} agents"
            }
            
        @self.register_endpoint("/dashboard", "GET")
        async def dashboard():
            """Get dashboard overview"""
            return {
                "agents": {
                    "total": len(self.agents),
                    "active": sum(1 for a in self.agents.values() if a["status"] == "busy"),
                    "idle": sum(1 for a in self.agents.values() if a["status"] == "idle"),
                    "performance_avg": sum(a["performance_score"] for a in self.agents.values()) / max(len(self.agents), 1)
                },
                "swarms": {
                    "total": len(self.swarms),
                    "active": sum(1 for s in self.swarms.values() if s["status"] == "active")
                },
                "tasks": {
                    "total": len(self.tasks),
                    "running": sum(1 for t in self.tasks.values() if t["status"] == "running"),
                    "completed": sum(1 for t in self.tasks.values() if t["status"] == "completed")
                },
                "system": {
                    "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                    "request_count": self.request_count,
                    "error_rate": self.error_count / max(self.request_count, 1)
                }
            }
            
        @self.register_endpoint("/performance", "GET")
        async def performance_metrics():
            """Get performance metrics for all agents"""
            metrics = []
            
            for agent in self.agents.values():
                metrics.append({
                    "agent_id": agent["id"],
                    "name": agent["name"],
                    "performance_score": agent["performance_score"],
                    "tasks_completed": agent["tasks_completed"],
                    "success_rate": agent["performance_score"],  # Simplified
                    "avg_task_time": 10.5,  # Simulated
                    "specialization": agent["capabilities"][0] if agent["capabilities"] else "general"
                })
                
            return {
                "metrics": metrics,
                "recommendations": [
                    "Consider creating more specialized agents for improved performance",
                    "Agent-research showing excellent performance in document analysis",
                    "Consider load balancing between agents with similar capabilities"
                ]
            }
            
    async def simulate_task_execution(self, task_id: str, agent_id: str):
        """Simulate task execution (replace with actual implementation)"""
        # Wait for simulated execution time
        await asyncio.sleep(5)
        
        # Update task status
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = {
                "output": "Task completed successfully",
                "confidence": 0.95,
                "metadata": {
                    "execution_time": 5.0,
                    "tokens_used": 1250
                }
            }
            
        # Update agent status
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "idle"
            self.agents[agent_id]["tasks_completed"] += 1
            # Slightly improve performance score
            self.agents[agent_id]["performance_score"] = min(
                1.0,
                self.agents[agent_id]["performance_score"] + 0.01
            )
            
        logger.info(f"Task {task_id} completed by agent {agent_id}")

# Main execution
if __name__ == "__main__":
    service = AgentsMCPService()
    service.run()