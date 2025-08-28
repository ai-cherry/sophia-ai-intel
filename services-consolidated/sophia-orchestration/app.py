"""
Sophia Orchestration Service - Consolidated orchestrator, agno-coordinator, agno-teams
Domain: Workflow orchestration, team management, task coordination
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from pydantic import BaseModel

class OrchestratorRequest(BaseModel):
    component: str
    action: str
    data: Dict[str, Any]

orchestrator_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator_manager
    from .orchestration import OrchestrationManager
    orchestrator_manager = OrchestrationManager()
    await orchestrator_manager.initialize()
    yield
    await orchestrator_manager.cleanup()

app = FastAPI(title="Sophia Orchestration", description="Consolidated orchestration and team management", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sophia-orchestration", "components": await orchestrator_manager.health_check()}

@app.post("/orchestrate")
async def orchestrate_workflow(request: OrchestratorRequest):
    return await orchestrator_manager.execute(request.component, request.action, request.data)

@app.post("/teams/manage")
async def manage_teams(action: str, team_data: Dict[str, Any]):
    return await orchestrator_manager.manage_teams(action, team_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)