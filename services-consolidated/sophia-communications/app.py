"""
Sophia Communications Service - Consolidated Slack & Gong
Domain: Team communication, conversation intelligence, chat operations
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from pydantic import BaseModel

class CommRequest(BaseModel):
    platform: str
    action: str
    data: Dict[str, Any]

class CommResponse(BaseModel):
    result: Dict[str, Any]
    platform: str
    status: str

comm_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global comm_manager
    from .communications import CommunicationsManager
    comm_manager = CommunicationsManager()
    await comm_manager.initialize()
    yield
    await comm_manager.cleanup()

app = FastAPI(title="Sophia Communications", description="Consolidated communications service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sophia-communications", "platforms": await comm_manager.health_check()}

@app.post("/message/send", response_model=CommResponse)
async def send_message(request: CommRequest):
    try:
        result = await comm_manager.send_message(request.platform, request.data)
        return CommResponse(result=result, platform=request.platform, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/analyze")
async def analyze_conversation(platform: str, conversation_id: str):
    return await comm_manager.analyze_conversation(platform, conversation_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)