#!/usr/bin/env python3
"""
AGNO Orchestrator - Sophia Supreme
One persona, one chat, full orchestra
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import redis
import aiohttp
from dataclasses import dataclass, asdict

class SwarmType(Enum):
    STRATEGY = "strategy"
    RESEARCH = "research"
    PLANNING = "planning"
    CODING = "coding"
    QC_UX = "qc_ux"
    COMMIT_DEPLOY = "commit_deploy"

@dataclass
class SwarmConfig:
    swarm_type: SwarmType
    models: List[str]
    max_agents: int
    timeout_seconds: int
    enable_websocket: bool = True
    enable_memory: bool = True

@dataclass
class MicroAgent:
    """Spawn-on-demand, single-task agents"""
    id: str
    task: str
    lifetime_seconds: int = 60
    result: Optional[Dict] = None

class AGNOOrchestrator:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.active_swarms = {}
        self.micro_agents = {}
        self.ws_clients = set()
        
        # Swarm pipeline configuration
        self.pipeline = [
            SwarmConfig(SwarmType.STRATEGY, ["claude-sonnet-4"], 1, 30),
            SwarmConfig(SwarmType.RESEARCH, ["qwen3-235b-cheap", "mistral-7b", "deepseek-v3"], 3, 120),
            SwarmConfig(SwarmType.PLANNING, ["claude-sonnet-4", "gemini-2.5-pro"], 2, 60),
            SwarmConfig(SwarmType.CODING, ["qwen3-coder-480b", "gpt-4o-mini"], 2, 180),
            SwarmConfig(SwarmType.QC_UX, ["claude-sonnet-4"], 1, 60),
            SwarmConfig(SwarmType.COMMIT_DEPLOY, ["gpt-4o-mini"], 1, 30)
        ]
    
    async def execute_pipeline(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full 6-stage pipeline"""
        pipeline_id = f"pipeline_{datetime.now().timestamp()}"
        results = {"pipeline_id": pipeline_id, "stages": {}}
        
        # Execute stages sequentially with context passing
        previous_output = None
        for config in self.pipeline:
            stage_result = await self.execute_swarm(
                config,
                task,
                {**context, "previous_stage": previous_output}
            )
            
            results["stages"][config.swarm_type.value] = stage_result
            previous_output = stage_result
            
            # Broadcast progress
            await self.broadcast_event({
                "type": "pipeline.progress",
                "pipeline_id": pipeline_id,
                "stage": config.swarm_type.value,
                "status": "completed" if stage_result else "failed"
            })
        
        return results
    
    async def execute_swarm(self, config: SwarmConfig, task: str, context: Dict) -> Dict[str, Any]:
        """Execute a single swarm with specified configuration"""
        swarm_id = f"swarm_{config.swarm_type.value}_{datetime.now().timestamp()}"
        
        # Store in Redis for tracking
        self.redis.setex(
            f"swarm:{swarm_id}",
            config.timeout_seconds,
            json.dumps({"task": task, "status": "running", "config": asdict(config)})
        )
        
        # Create agent tasks
        agent_tasks = []
        for i, model in enumerate(config.models[:config.max_agents]):
            agent_tasks.append(
                self.run_agent(f"{swarm_id}_agent_{i}", model, task, context)
            )
        
        # Execute agents in parallel
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*agent_tasks, return_exceptions=True),
                timeout=config.timeout_seconds
            )
            
            # Filter successful results
            valid_results = [r for r in results if isinstance(r, dict) and "error" not in r]
            
            # Synthesize results based on swarm type
            synthesis = await self.synthesize_results(config.swarm_type, valid_results)
            
            # Update Redis
            self.redis.setex(
                f"swarm:{swarm_id}",
                300,  # Keep for 5 minutes after completion
                json.dumps({"task": task, "status": "completed", "result": synthesis})
            )
            
            # Broadcast completion
            if config.enable_websocket:
                await self.broadcast_event({
                    "type": "swarm.completed",
                    "swarm_id": swarm_id,
                    "swarm_type": config.swarm_type.value,
                    "result": synthesis
                })
            
            return synthesis
            
        except asyncio.TimeoutError:
            self.redis.setex(
                f"swarm:{swarm_id}",
                60,
                json.dumps({"task": task, "status": "timeout"})
            )
            return {"error": "Swarm timeout", "swarm_id": swarm_id}
    
    async def run_agent(self, agent_id: str, model: str, task: str, context: Dict) -> Dict[str, Any]:
        """Run a single agent with specified model"""
        # Call model router
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8090/route",  # Model router endpoint
                json={"message": task, "model": model, "context": context}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"Agent {agent_id} failed"}
    
    async def spawn_micro_agent(self, task: str) -> MicroAgent:
        """Spawn a micro-agent for a single task"""
        agent = MicroAgent(
            id=f"micro_{datetime.now().timestamp()}",
            task=task,
            lifetime_seconds=60
        )
        
        self.micro_agents[agent.id] = agent
        
        # Execute task
        result = await self.run_agent(agent.id, "mistral-7b", task, {})
        agent.result = result
        
        # Store result in Redis L1 cache
        self.redis.setex(
            f"micro:{agent.id}",
            agent.lifetime_seconds,
            json.dumps({"task": task, "result": result})
        )
        
        # Schedule cleanup
        asyncio.create_task(self.cleanup_micro_agent(agent.id, agent.lifetime_seconds))
        
        return agent
    
    async def cleanup_micro_agent(self, agent_id: str, delay: int):
        """Clean up micro-agent after lifetime expires"""
        await asyncio.sleep(delay)
        if agent_id in self.micro_agents:
            del self.micro_agents[agent_id]
            self.redis.delete(f"micro:{agent_id}")
    
    async def synthesize_results(self, swarm_type: SwarmType, results: List[Dict]) -> Dict[str, Any]:
        """Synthesize results based on swarm type"""
        if not results:
            return {"error": "No valid results to synthesize"}
        
        if swarm_type == SwarmType.STRATEGY:
            # Return strategic plans
            return {
                "plans": {
                    "cutting_edge": results[0] if results else {},
                    "conservative": results[1] if len(results) > 1 else results[0],
                    "synthesis": self.merge_strategies(results)
                },
                "recommendation": "synthesis"
            }
        
        elif swarm_type == SwarmType.RESEARCH:
            # Aggregate research findings
            all_findings = []
            for r in results:
                if "findings" in r:
                    all_findings.extend(r["findings"])
            return {"findings": all_findings, "sources": len(results)}
        
        elif swarm_type == SwarmType.CODING:
            # Merge code outputs
            return {
                "files": self.merge_code_files(results),
                "language": "python",
                "agents_used": len(results)
            }
        
        else:
            # Default: return first valid result
            return results[0] if results else {"status": "completed"}
    
    def merge_strategies(self, strategies: List[Dict]) -> Dict:
        """Merge multiple strategy proposals"""
        if not strategies:
            return {}
        
        # Simple merge: combine key points
        merged = {"approach": [], "risks": [], "benefits": []}
        for s in strategies:
            if isinstance(s, dict):
                merged["approach"].extend(s.get("approach", []))
                merged["risks"].extend(s.get("risks", []))
                merged["benefits"].extend(s.get("benefits", []))
        
        return merged
    
    def merge_code_files(self, code_results: List[Dict]) -> List[Dict]:
        """Merge code files from multiple agents"""
        files = []
        seen_paths = set()
        
        for result in code_results:
            if "files" in result:
                for file in result["files"]:
                    if file.get("path") not in seen_paths:
                        files.append(file)
                        seen_paths.add(file.get("path"))
        
        return files
    
    async def broadcast_event(self, event: Dict):
        """Broadcast event to all WebSocket clients"""
        event_json = json.dumps(event)
        
        # Store in Redis for replay
        self.redis.lpush("events:stream", event_json)
        self.redis.ltrim("events:stream", 0, 999)  # Keep last 1000 events
        
        # Send to WebSocket hub
        async with aiohttp.ClientSession() as session:
            await session.post(
                "http://localhost:8096/broadcast",
                json=event
            )
    
    async def route_chat(self, message: str, session_id: str, context: Dict) -> Dict[str, Any]:
        """Main chat routing - detect intent and execute appropriate action"""
        intent = self.detect_intent(message)
        
        sections = {
            "summary": "",
            "actions": [],
            "research": [],
            "plans": None,
            "code": None,
            "github": None,
            "events": []
        }
        
        if intent == "full-pipeline":
            # Execute complete 6-stage pipeline
            result = await self.execute_pipeline(message, context)
            sections["summary"] = "Executing full development pipeline"
            sections["actions"] = [
                {"type": f"{stage}.initiated", "status": "running"}
                for stage in ["strategy", "research", "planning", "coding", "qc_ux", "commit_deploy"]
            ]
            sections["events"] = [{"type": "pipeline.started", "id": result["pipeline_id"]}]
            
        elif intent == "research":
            # Execute research swarm only
            config = SwarmConfig(SwarmType.RESEARCH, ["qwen3-235b-cheap", "deepseek-v3"], 2, 120)
            result = await self.execute_swarm(config, message, context)
            sections["research"] = result.get("findings", [])
            sections["summary"] = f"Found {len(result.get('findings', []))} research results"
            
        elif intent == "code":
            # Execute coding swarm
            config = SwarmConfig(SwarmType.CODING, ["qwen3-coder-480b"], 1, 180)
            result = await self.execute_swarm(config, message, context)
            sections["code"] = result
            sections["summary"] = "Code generation complete"
            
        elif intent == "micro-task":
            # Spawn micro-agent for quick task
            agent = await self.spawn_micro_agent(message)
            sections["summary"] = f"Micro-agent {agent.id} completed task"
            sections["actions"] = [{"type": "micro.completed", "id": agent.id}]
            
        else:
            # General routing
            sections["summary"] = "Processing your request"
            sections["actions"] = [{"type": "general.processing"}]
        
        return sections
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        msg = message.lower()
        
        if any(word in msg for word in ["build", "create", "implement", "develop"]) and \
           any(word in msg for word in ["feature", "system", "application", "service"]):
            return "full-pipeline"
        
        if any(word in msg for word in ["research", "find", "search", "investigate"]):
            return "research"
        
        if any(word in msg for word in ["code", "implement", "write", "generate"]):
            return "code"
        
        if any(word in msg for word in ["quick", "simple", "check", "test"]):
            return "micro-task"
        
        return "general"

# Background agents
class BackgroundAgents:
    def __init__(self, orchestrator: AGNOOrchestrator):
        self.orchestrator = orchestrator
        self.running = True
    
    async def indexer_agent(self):
        """Continuously index repository changes"""
        while self.running:
            # Check for repo changes
            # Chunk and embed to Qdrant
            await asyncio.sleep(30)
    
    async def health_sentry(self):
        """Monitor service health"""
        while self.running:
            services = [
                "http://localhost:8081/health",
                "http://localhost:8082/health",
                "http://localhost:8085/health",
                "http://localhost:8088/health",
                "http://localhost:8096/health"
            ]
            
            health_status = []
            async with aiohttp.ClientSession() as session:
                for service in services:
                    try:
                        async with session.get(service, timeout=1) as resp:
                            health_status.append({
                                "service": service,
                                "status": "healthy" if resp.status == 200 else "unhealthy"
                            })
                    except:
                        health_status.append({"service": service, "status": "dead"})
            
            # Store in Redis
            self.orchestrator.redis.setex(
                "health:status",
                60,
                json.dumps(health_status)
            )
            
            await asyncio.sleep(10)
    
    async def eval_agent(self):
        """Sample requests for evaluation"""
        while self.running:
            # Sample recent requests
            # Calculate metrics
            # Store eval scores
            await asyncio.sleep(300)  # Every 5 minutes

# API Server
from aiohttp import web

orchestrator = AGNOOrchestrator()
background = BackgroundAgents(orchestrator)

async def handle_chat(request):
    """Main chat endpoint"""
    data = await request.json()
    message = data.get("message", "")
    session_id = data.get("session_id", f"session_{datetime.now().timestamp()}")
    context = data.get("context", {})
    
    sections = await orchestrator.route_chat(message, session_id, context)
    
    return web.json_response({
        "service": "agno-orchestrator",
        "sections": sections
    })

async def handle_swarm_create(request):
    """Create a specific swarm"""
    data = await request.json()
    swarm_type = SwarmType[data.get("swarm_type", "RESEARCH").upper()]
    task = data.get("task", "")
    
    config = SwarmConfig(swarm_type, ["qwen3-235b-cheap"], 1, 120)
    result = await orchestrator.execute_swarm(config, task, {})
    
    return web.json_response(result)

async def handle_health(request):
    """Health check endpoint"""
    health = orchestrator.redis.get("health:status")
    if health:
        return web.json_response(json.loads(health))
    return web.json_response({"status": "initializing"})

async def start_background_tasks(app):
    """Start background agents"""
    app['background_tasks'] = [
        asyncio.create_task(background.indexer_agent()),
        asyncio.create_task(background.health_sentry()),
        asyncio.create_task(background.eval_agent())
    ]

async def cleanup_background_tasks(app):
    """Stop background agents"""
    background.running = False
    for task in app.get('background_tasks', []):
        task.cancel()

def create_app():
    app = web.Application()
    app.router.add_post('/chat', handle_chat)
    app.router.add_post('/swarm/create', handle_swarm_create)
    app.router.add_get('/health', handle_health)
    
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8400)