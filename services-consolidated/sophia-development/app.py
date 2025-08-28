"""
Sophia Development Service - Consolidated GitHub & Lambda
Domain: Code management, CI/CD, serverless functions
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from pydantic import BaseModel

class DevRequest(BaseModel):
    service: str
    action: str
    data: Dict[str, Any]

class DevResponse(BaseModel):
    result: Dict[str, Any]
    service: str
    status: str

dev_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dev_manager
    from .development import DevelopmentManager
    dev_manager = DevelopmentManager()
    await dev_manager.initialize()
    yield
    await dev_manager.cleanup()

app = FastAPI(title="Sophia Development", description="Consolidated development and serverless service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sophia-development", "services": await dev_manager.health_check()}

@app.post("/github/{action}", response_model=DevResponse)
async def github_action(action: str, request: DevRequest):
    try:
        result = await dev_manager.github_execute(action, request.data)
        return DevResponse(result=result, service="github", status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lambda/invoke")
async def invoke_lambda(function_name: str, payload: Dict[str, Any]):
    return await dev_manager.lambda_invoke(function_name, payload)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)