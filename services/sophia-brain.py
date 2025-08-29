"""
Sophia Brain - Central AI Intelligence Coordinator
Complete integration of all MCP servers, agents, and capabilities
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum

app = FastAPI(title="Sophia Brain - Central Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"

class Message(BaseModel):
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class ConversationRequest(BaseModel):
    messages: List[Message]
    context: Optional[Dict[str, Any]] = {}
    capabilities: Optional[List[str]] = ["all"]

class ActionType(str, Enum):
    SEARCH = "search"
    CODE_GENERATE = "code_generate"
    CODE_EXECUTE = "code_execute"
    GITHUB_PUSH = "github_push"
    AGENT_CREATE = "agent_create"
    AGENT_EXECUTE = "agent_execute"
    WORKFLOW_RUN = "workflow_run"
    RESEARCH = "research"
    ANALYZE = "analyze"

class Action(BaseModel):
    type: ActionType
    parameters: Dict[str, Any]
    target_service: Optional[str] = None

class SophiaBrain:
    """Central intelligence that coordinates all services"""
    
    def __init__(self):
        # Use container names when running in Docker, localhost when running locally
        import os
        is_docker = os.environ.get('ENVIRONMENT') == 'production' or os.path.exists('/.dockerenv')
        
        if is_docker:
            # Use container names for Docker networking
            self.services = {
                "context": "http://mcp-context:8081",
                "research": "http://mcp-research:8085",
                "github": "http://mcp-github:8082",
                "hubspot": "http://mcp-hubspot:8083",
                "salesforce": "http://mcp-salesforce:8092",
                "gong": "http://mcp-gong:8091",
                "agents": "http://mcp-agents:8000",
                "coordinator": "http://agno-coordinator:8080",
                "orchestrator": "http://orchestrator:8088",
                "unified_swarm": "http://host.docker.internal:8100",  # Running on host
                "legacy_swarm": "http://agents-swarm:8008"
            }
        else:
            # Use localhost for local development
            self.services = {
                "context": "http://localhost:8081",
                "research": "http://localhost:8085",
                "github": "http://localhost:8082",
                "hubspot": "http://localhost:8083",
                "salesforce": "http://localhost:8092",
                "gong": "http://localhost:8091",
                "agents": "http://localhost:8000",
                "coordinator": "http://localhost:8080",
                "orchestrator": "http://localhost:8088",
                "unified_swarm": "http://localhost:8100",
                "legacy_swarm": "http://localhost:8008"
            }
        self.active_agents = {}
        self.conversation_memory = {}
        
    async def process_natural_language(self, query: str, context: Dict) -> Dict:
        """Process natural language and determine intent and actions"""
        
        query_lower = query.lower()
        actions = []
        
        # Analyze query for multiple intents
        intents = self.analyze_intents(query_lower)
        
        # Generate action plan
        for intent in intents:
            if intent == "search":
                actions.append(Action(
                    type=ActionType.SEARCH,
                    parameters={"query": query},
                    target_service="research"
                ))
            elif intent == "code":
                actions.append(Action(
                    type=ActionType.CODE_GENERATE,
                    parameters={"specification": query},
                    target_service="agents"
                ))
            elif intent == "github":
                actions.append(Action(
                    type=ActionType.GITHUB_PUSH,
                    parameters={"code": context.get("code", "")},
                    target_service="github"
                ))
            elif intent == "agent":
                actions.append(Action(
                    type=ActionType.AGENT_CREATE,
                    parameters={"task": query},
                    target_service="coordinator"
                ))
        
        # Execute actions in parallel where possible
        results = await self.execute_actions(actions)
        
        # Synthesize response
        response = self.synthesize_response(query, results)
        
        return {
            "response": response,
            "actions_taken": [a.type for a in actions],
            "services_used": list(set(a.target_service for a in actions if a.target_service)),
            "results": results
        }
    
    def analyze_intents(self, query: str) -> List[str]:
        """Analyze query for multiple intents"""
        intents = []
        
        # Search/Research intent
        if any(word in query for word in ["search", "find", "research", "what", "who", "when", "where"]):
            intents.append("search")
        
        # Code generation intent
        if any(word in query for word in ["code", "function", "class", "implement", "create", "build"]):
            intents.append("code")
        
        # GitHub intent
        if any(word in query for word in ["github", "commit", "push", "repository", "git"]):
            intents.append("github")
        
        # Agent intent
        if any(word in query for word in ["agent", "swarm", "automate", "orchestrate"]):
            intents.append("agent")
        
        # Default to general search if no specific intent
        if not intents:
            intents.append("search")
        
        return intents
    
    async def execute_actions(self, actions: List[Action]) -> List[Dict]:
        """Execute actions across services"""
        results = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for action in actions:
                if action.target_service in self.services:
                    service_url = self.services[action.target_service]
                    task = self.execute_single_action(client, service_url, action)
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def execute_single_action(self, client: httpx.AsyncClient, service_url: str, action: Action) -> Dict:
        """Execute a single action against a service"""
        try:
            if action.type == ActionType.SEARCH:
                response = await client.post(
                    f"{service_url}/research",
                    json={
                        "query": action.parameters["query"],
                        "sources": ["web", "academic", "news"],
                        "limit": 5
                    }
                )
            elif action.type == ActionType.CODE_GENERATE:
                response = await client.post(
                    f"{service_url}/generate",
                    json={"specification": action.parameters["specification"]}
                )
            elif action.type == ActionType.GITHUB_PUSH:
                response = await client.post(
                    f"{service_url}/push",
                    json={
                        "repo_id": "sophia-ai/generated",
                        "code": action.parameters.get("code", {}),
                        "message": "AI-generated code"
                    }
                )
            elif action.type == ActionType.AGENT_CREATE:
                # Use unified swarm service for agent/swarm creation
                swarm_url = self.services["unified_swarm"]
                response = await client.post(
                    f"{swarm_url}/swarms/create",
                    json={
                        "name": f"Agent_{uuid.uuid4().hex[:8]}",
                        "type": "task",
                        "capabilities": ["execute", "analyze"]
                    }
                )
            else:
                return {"error": f"Unknown action type: {action.type}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Service returned {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def synthesize_response(self, query: str, results: List[Dict]) -> str:
        """Synthesize a natural language response from results"""
        
        if not results:
            return f"I understand you're asking about '{query}'. Let me help you with that."
        
        # Build comprehensive response
        response_parts = []
        
        for result in results:
            if "error" in result:
                continue
            
            # Research results
            if "results" in result and isinstance(result["results"], list):
                if result["results"]:
                    top_result = result["results"][0]
                    response_parts.append(f"Based on my research: {top_result.get('summary', top_result.get('title', ''))}")
            
            # Agent results
            elif "agent_id" in result:
                response_parts.append(f"I've created an agent to help: {result.get('message', '')}")
            
            # Code generation results
            elif "code" in result:
                response_parts.append(f"I've generated the code you requested. {result.get('message', '')}")
            
            # GitHub results
            elif "commit_id" in result or "pr_id" in result:
                response_parts.append(f"Code has been pushed to GitHub: {result.get('url', result.get('message', ''))}")
        
        if response_parts:
            return " ".join(response_parts)
        else:
            return f"I've processed your request about '{query}'. The system is working on providing you the best answer."
    
    async def create_agent_swarm(self, task_description: str, agent_count: int = 3) -> Dict:
        """Create a swarm of agents for a complex task"""
        
        agents = []
        async with httpx.AsyncClient() as client:
            for i in range(agent_count):
                response = await client.post(
                    f"{self.services['coordinator']}/agents/create",
                    json={
                        "name": f"Swarm_Agent_{i+1}",
                        "type": "worker",
                        "capabilities": ["analyze", "execute", "report"]
                    }
                )
                if response.status_code == 200:
                    agents.append(response.json())
        
        # Orchestrate the swarm
        orchestration_response = await self.orchestrate_workflow({
            "name": f"Swarm Task: {task_description[:50]}",
            "agents": agents,
            "steps": [
                {"action": "analyze", "target": "all"},
                {"action": "execute", "target": "parallel"},
                {"action": "report", "target": "consolidate"}
            ]
        })
        
        return {
            "swarm_id": str(uuid.uuid4()),
            "agents": agents,
            "orchestration": orchestration_response,
            "status": "active"
        }
    
    async def orchestrate_workflow(self, workflow: Dict) -> Dict:
        """Orchestrate a complex workflow"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.services['orchestrator']}/orchestrate",
                json={"workflow": workflow}
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "Orchestration failed"}
    
    async def generate_and_execute_code(self, specification: str) -> Dict:
        """Generate code and optionally execute it"""
        
        # Generate code
        code = await self.generate_code(specification)
        
        # Analyze for safety
        is_safe = self.analyze_code_safety(code)
        
        if is_safe:
            # Execute in sandboxed environment
            result = await self.execute_code_safely(code)
            return {
                "code": code,
                "executed": True,
                "result": result
            }
        else:
            return {
                "code": code,
                "executed": False,
                "reason": "Code requires review before execution"
            }
    
    async def generate_code(self, specification: str) -> str:
        """Generate code based on specification"""
        
        # This would integrate with actual code generation service
        # For now, return a template
        return f"""
def generated_function():
    '''Generated based on: {specification}'''
    # Implementation here
    pass
"""
    
    def analyze_code_safety(self, code: str) -> bool:
        """Analyze code for safety before execution"""
        
        # Check for dangerous patterns
        dangerous_patterns = ["exec", "eval", "__import__", "os.system", "subprocess"]
        code_lower = code.lower()
        
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return False
        
        return True
    
    async def execute_code_safely(self, code: str) -> Dict:
        """Execute code in a safe environment"""
        
        # This would execute in a sandboxed container
        # For now, return mock result
        return {
            "output": "Code executed successfully",
            "return_value": None,
            "execution_time": "0.1s"
        }

# Initialize Sophia Brain
sophia_brain = SophiaBrain()

@app.post("/chat")
async def chat(request: ConversationRequest):
    """Main chat endpoint with full capabilities"""
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    latest_message = request.messages[-1]
    
    # Process through Sophia Brain
    result = await sophia_brain.process_natural_language(
        latest_message.content,
        request.context or {}
    )
    
    return {
        "response": result["response"],
        "metadata": {
            "actions": result["actions_taken"],
            "services": result["services_used"],
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/agent/create")
async def create_agent(task: str, agent_type: str = "general"):
    """Create an AI agent"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{sophia_brain.services['coordinator']}/agents/create",
            json={
                "name": f"Agent_{uuid.uuid4().hex[:8]}",
                "type": agent_type,
                "capabilities": ["analyze", "execute", "report"],
                "task": task
            }
        )
        if response.status_code == 200:
            return response.json()
    
    raise HTTPException(status_code=500, detail="Failed to create agent")

@app.post("/swarm/create")
async def create_swarm(task: str, size: int = 3):
    """Create an agent swarm"""
    
    result = await sophia_brain.create_agent_swarm(task, size)
    return result

@app.post("/code/generate")
async def generate_code(specification: str, execute: bool = False):
    """Generate and optionally execute code"""
    
    result = await sophia_brain.generate_and_execute_code(specification)
    return result

@app.post("/workflow/run")
async def run_workflow(workflow: Dict):
    """Run a complex workflow"""
    
    result = await sophia_brain.orchestrate_workflow(workflow)
    return result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time communication"""
    
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message
            result = await sophia_brain.process_natural_language(
                message.get("content", ""),
                message.get("context", {})
            )
            
            # Send response
            await websocket.send_json({
                "session_id": session_id,
                "response": result["response"],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "actions": result.get("actions_taken", [])
                }
            })
    
    except WebSocketDisconnect:
        pass

@app.get("/")
async def root():
    return {
        "service": "Sophia Brain",
        "version": "2.0",
        "status": "active",
        "capabilities": [
            "natural_language_processing",
            "multi_agent_orchestration",
            "code_generation_and_execution",
            "deep_web_research",
            "github_integration",
            "workflow_automation",
            "real_time_communication"
        ]
    }

@app.get("/health")
async def health():
    """Health check with service status"""
    
    # Map services to their actual health endpoints
    health_endpoints = {
        "context": "/healthz",
        "research": "/",
        "github": "/",
        "hubspot": "/health",
        "salesforce": "/health",
        "gong": "/health",
        "agents": "/",
        "coordinator": "/health",
        "orchestrator": "/health",
        "unified_swarm": "/health",
        "legacy_swarm": "/"
    }
    
    service_status = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in sophia_brain.services.items():
            try:
                endpoint = health_endpoints.get(name, "/health")
                response = await client.get(f"{url}{endpoint}")
                service_status[name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as e:
                service_status[name] = f"unreachable: {str(e)[:30]}"
    
    return {
        "status": "healthy",
        "services": service_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)