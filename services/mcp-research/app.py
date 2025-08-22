import os, time, json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx

# Environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-5")

app = FastAPI(title="sophia-mcp-research", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sophiaai-dashboard.fly.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalized_error(provider: str, code: str, message: str):
    """Return normalized error JSON format"""
    return {
        "error": {
            "provider": provider,
            "code": code,
            "message": message
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

class SearchRequest(BaseModel):
    query: str
    sources: List[str] = ["tavily", "serper"]
    max_results: int = 10

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    score: float

class SearchResponse(BaseModel):
    status: str
    query: str
    results: List[SearchResult]
    summary: dict
    timestamp: str
    execution_time_ms: int

@app.get("/healthz")
async def healthz():
    missing = []
    if not PORTKEY_API_KEY:
        missing.append("PORTKEY_API_KEY")
    
    if missing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-research",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_ms": int(time.time() * 1000),
                "dependencies": {
                    "tavily": "configured" if TAVILY_API_KEY else "missing",
                    "serper": "configured" if SERPER_API_KEY else "missing",
                    "portkey": "missing"
                },
                "error": normalized_error(
                    "research_service",
                    "MISSING_CREDENTIALS",
                    f"Missing required credentials: {', '.join(missing)}"
                )
            }
        )
    
    return {
        "status": "healthy",
        "service": "sophia-mcp-research",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_ms": int(time.time() * 1000),
        "dependencies": {
            "tavily": "configured" if TAVILY_API_KEY else "not_configured",
            "serper": "configured" if SERPER_API_KEY else "not_configured",
            "portkey": "configured"
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    start_time = time.time()
    
    # Check for required PORTKEY_API_KEY
    if not PORTKEY_API_KEY:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "research_service",
                "MISSING_CREDENTIALS",
                "PORTKEY_API_KEY is required for LLM routing"
            )
        )
    
    # Check for search provider keys
    missing_keys = []
    if not TAVILY_API_KEY and "tavily" in request.sources:
        missing_keys.append("TAVILY_API_KEY")
    if not SERPER_API_KEY and "serper" in request.sources:
        missing_keys.append("SERPER_API_KEY")
    
    if missing_keys and not any([TAVILY_API_KEY, SERPER_API_KEY]):
        # No search providers available at all
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "research_service",
                "NO_SEARCH_PROVIDERS",
                f"No search providers configured. Missing: {', '.join(missing_keys)}"
            )
        )
    
    # For now, return a basic success response
    # TODO: Implement actual search providers
    return SearchResponse(
        status="success",
        query=request.query,
        results=[
            SearchResult(
                title="Health Check Result",
                url="https://example.com",
                snippet="This is a health check response from the research service",
                source="health_check",
                score=1.0
            )
        ],
        summary={
            "text": f"Health check search for: {request.query}",
            "confidence": 1.0,
            "model": DEFAULT_LLM_MODEL,
            "sources": ["health_check"]
        },
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        execution_time_ms=int((time.time() - start_time) * 1000)
    )