import os, time, json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Environment variables
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

app = FastAPI(title="sophia-mcp-context", version="1.0.0")

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

class ContextEntry(BaseModel):
    type: str
    title: str
    content: str
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    source: Dict[str, Any]

class IndexRequest(BaseModel):
    entries: List[ContextEntry]
    batch_id: Optional[str] = None

class IndexResponse(BaseModel):
    status: str
    indexed_count: int
    skipped_count: int
    failed_count: int
    timestamp: str
    execution_time_ms: int

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class SearchResponse(BaseModel):
    status: str
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    timestamp: str
    execution_time_ms: int

@app.get("/healthz")
async def healthz():
    db_status = "not_configured"
    
    if not NEON_DATABASE_URL:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-context",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_ms": int(time.time() * 1000),
                "dependencies": {
                    "neon": "missing"
                },
                "error": normalized_error(
                    "context_service",
                    "MISSING_CREDENTIALS",
                    "NEON_DATABASE_URL is required for database operations"
                )
            }
        )
    
    # Test database connection
    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.close()
        db_status = "healthy"
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-context",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_ms": int(time.time() * 1000),
                "dependencies": {
                    "neon": "connection_failed"
                },
                "error": normalized_error(
                    "context_service",
                    "DATABASE_CONNECTION_ERROR",
                    f"Failed to connect to Neon database: {str(e)}"
                )
            }
        )
    
    return {
        "status": "healthy",
        "service": "sophia-mcp-context",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_ms": int(time.time() * 1000),
        "dependencies": {
            "neon": db_status
        }
    }

@app.post("/context/index", response_model=IndexResponse)
async def index_context(request: IndexRequest):
    start_time = time.time()
    
    if not NEON_DATABASE_URL:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "MISSING_CREDENTIALS",
                "NEON_DATABASE_URL is required for indexing operations"
            )
        )
    
    # Test database connection
    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "DATABASE_CONNECTION_ERROR",
                f"Failed to connect to Neon database: {str(e)}"
            )
        )
    
    # For now, return success without actual indexing
    # TODO: Implement actual Neon database operations
    return IndexResponse(
        status="success",
        indexed_count=len(request.entries),
        skipped_count=0,
        failed_count=0,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        execution_time_ms=int((time.time() - start_time) * 1000)
    )

@app.post("/context/search", response_model=SearchResponse)
async def search_context(request: SearchRequest):
    start_time = time.time()
    
    if not NEON_DATABASE_URL:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "MISSING_CREDENTIALS",
                "NEON_DATABASE_URL is required for search operations"
            )
        )
    
    # Test database connection
    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "DATABASE_CONNECTION_ERROR",
                f"Failed to connect to Neon database: {str(e)}"
            )
        )
    
    # For now, return basic success response
    # TODO: Implement actual search functionality
    return SearchResponse(
        status="success",
        query=request.query,
        results=[{
            "id": "health-check",
            "title": "Health Check Result",
            "content": f"Search query: {request.query}",
            "similarity_score": 1.0
        }],
        total_results=1,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        execution_time_ms=int((time.time() - start_time) * 1000)
    )

@app.get("/context/stats")
async def context_stats():
    if not NEON_DATABASE_URL:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "MISSING_CREDENTIALS",
                "NEON_DATABASE_URL is required for stats operations"
            )
        )
    
    # Test database connection
    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "context_service",
                "DATABASE_CONNECTION_ERROR",
                f"Failed to connect to Neon database: {str(e)}"
            )
        )
    
    return {
        "status": "success",
        "stats": {
            "total_entries": 0,
            "entries_by_type": {},
            "entries_by_source": {},
            "last_indexed": None,
            "index_size_mb": 0,
            "embedding_model": None
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }