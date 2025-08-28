"""
Sophia Infrastructure Service - Consolidated agno-wrappers & monitoring
Domain: API wrappers, monitoring, health checks, utility services
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from pydantic import BaseModel

class InfraRequest(BaseModel):
    service: str
    action: str
    data: Dict[str, Any]

infra_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global infra_manager
    from infrastructure import InfrastructureManager
    infra_manager = InfrastructureManager()
    await infra_manager.initialize()
    yield
    await infra_manager.cleanup()

app = FastAPI(title="Sophia Infrastructure", description="Infrastructure services and API wrappers", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sophia-infrastructure", "services": await infra_manager.health_check()}

@app.post("/wrapper/{service}")
async def api_wrapper(service: str, request: InfraRequest):
    return await infra_manager.execute_wrapper(service, request.action, request.data)

@app.get("/metrics")
async def get_metrics():
    return await infra_manager.get_metrics()

@app.get("/system/status")
async def system_status():
    return await infra_manager.get_system_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)