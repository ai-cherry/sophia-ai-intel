"""
Sophia Business Intelligence Service - Consolidated CRM & Sales
Domain: Salesforce, HubSpot, business analytics, sales intelligence
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from pydantic import BaseModel

class CRMRequest(BaseModel):
    action: str
    entity: str
    data: Dict[str, Any]

class CRMResponse(BaseModel):
    result: Dict[str, Any]
    source: str
    status: str

# Global instances
crm_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crm_manager
    from .crm import CRMManager
    crm_manager = CRMManager()
    await crm_manager.initialize()
    yield
    await crm_manager.cleanup()

app = FastAPI(
    title="Sophia Business Intelligence",
    description="Consolidated CRM and business analytics service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "sophia-business-intel",
        "integrations": await crm_manager.health_check()
    }

@app.post("/crm/{provider}/query", response_model=CRMResponse)
async def crm_query(provider: str, request: CRMRequest):
    try:
        result = await crm_manager.execute(provider, request.action, request.entity, request.data)
        return CRMResponse(result=result, source=provider, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/report")
async def generate_report(report_type: str, filters: Dict[str, Any]):
    return await crm_manager.generate_report(report_type, filters)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)