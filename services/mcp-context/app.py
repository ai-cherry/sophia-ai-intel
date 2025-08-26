"""
Sophia AI Context Abstraction Layer MCP Service

This module provides a unified context abstraction layer that integrates document storage,
vector search, and knowledge retrieval capabilities. It serves as the central context
management system for the Sophia AI intelligence platform.

Key Features:
- Document creation and storage in PostgreSQL and Qdrant vector database
- Semantic document search using vector embeddings
- Unified context provider abstraction
- Health monitoring and provider status tracking
- Normalized error handling across all operations

Architecture:
- PostgreSQL for structured document metadata and content storage
- Qdrant vector database for semantic search and similarity matching
- FastAPI async REST API with comprehensive error handling
- Database connection pooling for high-performance operations

Provider Integrations:
- PostgreSQL (Neon): Primary document and metadata storage
- Qdrant: Vector database for embedding storage and semantic search

Version: 2.0.0
Author: Sophia AI Intelligence Team
"""

import os
import time
import json
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
from qdrant_client import QdrantClient

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import real embeddings engine
from real_embeddings import (
    embedding_engine,
    store_with_real_embedding,
    semantic_search_documents
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

app = FastAPI(
    title="sophia-mcp-context-v2",
    version="2.0.0",
    description="Unified context abstraction layer for Sophia AI",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://sophia-dashboard:3000", "https://github.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database connection pool
db_pool = None


async def get_db_pool():
    """
    Get or create database connection pool for document storage.
    
    Returns the global PostgreSQL connection pool, creating it if it doesn't exist.
    Used for storing document content, metadata, and search indexes.
    
    Returns:
        asyncpg.Pool: Database connection pool instance, or None if not configured
        
    Note:
        Requires NEON_DATABASE_URL environment variable for PostgreSQL connectivity
    """
    global db_pool
    if not db_pool and NEON_DATABASE_URL:
        db_pool = await asyncpg.create_pool(NEON_DATABASE_URL)
    return db_pool


def normalized_error(
    provider: str, code: str, message: str, details: Optional[Dict] = None
):
    """
    Create normalized error response format for consistent error handling.
    
    Standardizes error responses across context operations to ensure consistent
    debugging and error handling capabilities throughout the system.
    
    Args:
        provider (str): Context provider that generated the error (storage/qdrant)
        code (str): Error code identifier for programmatic error handling
        message (str): Human-readable error message describing the issue
        details (Optional[Dict]): Additional error context and debugging information
        
    Returns:
        Dict[str, Any]: Normalized error object with standard MCP structure
        
    Example:
        >>> normalized_error("qdrant", "connection_failed", "Vector database unavailable")
    """
    error_obj = {
        "status": "failure",
        "query": "",
        "results": [],
        "summary": {"text": message, "confidence": 1.0, "model": "n/a", "sources": []},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_time_ms": 0,
        "errors": [{"provider": provider, "code": code, "message": message}],
    }
    if details:
        error_obj["errors"][0]["details"] = details
    return error_obj


def get_provider_status():
    """
    Check availability status of context storage providers.
    
    Evaluates the configuration status of integrated context providers by checking
    for required environment variables and connection parameters.
    
    Returns:
        Dict[str, str]: Provider status mapping with values:
            - "ready": Provider is configured with required credentials
            - "missing_secret": Required configuration is missing
            
    Context Providers:
        - storage: PostgreSQL database for document and metadata storage
        - qdrant: Vector database for semantic search and embeddings
        
    Note:
        Use the /healthz endpoint for comprehensive connectivity testing
    """
    return {
        "storage": "ready" if NEON_DATABASE_URL else "missing_secret",
        "qdrant": "ready" if QDRANT_URL else "missing_secret",
    }


# Request/Response Models
class DocumentCreateRequest(BaseModel):
    content: str = Field(..., description="Content of the document")
    source: str = Field(..., description="Source of the document")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, le=20, description="Number of results to return")


class Document(BaseModel):
    id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    created_at: str


class DocumentSearchResponse(BaseModel):
    status: str
    query: str
    results: List[Document]
    summary: Dict[str, Any]
    providers_used: List[str]
    providers_failed: List[Dict]
    execution_time_ms: int
    timestamp: str


# Qdrant client
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


# API Endpoints
@app.get("/healthz")
async def healthz():
    """Health check with provider status"""
    providers = get_provider_status()

    # Check database connectivity
    db_status = "unknown"
    if NEON_DATABASE_URL:
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    db_status = "connected" if result == 1 else "error"
            else:
                db_status = "pool_failed"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
    else:
        db_status = "not_configured"

    # Check Qdrant connectivity
    qdrant_status = "unknown"
    if QDRANT_URL and QDRANT_API_KEY:
        try:
            health = qdrant_client.health_check()
            qdrant_status = "connected" if health["status"] == "ok" else "error"
        except Exception as e:
            qdrant_status = f"error: {str(e)[:50]}"
    else:
        qdrant_status = "not_configured"

    ready_providers = [k for k, v in providers.items() if v == "ready"]
    missing_providers = [k for k, v in providers.items() if v == "missing_secret"]

    if len(ready_providers) == 0:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-context-v1",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "providers": providers,
                "database": db_status,
                "vector_database": qdrant_status,
                "error": normalized_error(
                    "context",
                    "no-providers",
                    f"No context providers configured. Missing: {', '.join(missing_providers[:5])}",
                ),
            },
        )

    return {
        "status": "healthy" if len(ready_providers) >= 1 else "degraded",
        "service": "sophia-mcp-context-v1",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "providers": providers,
        "database": db_status,
        "vector_database": qdrant_status,
        "ready_providers": ready_providers,
        "missing_providers": missing_providers,
    }


@app.post("/documents/create")
async def create_document(request: DocumentCreateRequest):
    """
    Creates a new document and stores it in database and vector store.
    """
    start_time = time.time()

    if not NEON_DATABASE_URL:
        raise HTTPException(
            status_code=503,
            detail=normalized_error(
                "storage", "missing-database", "NEON_DATABASE_URL not configured"
            ),
        )

    doc_id = str(uuid.uuid4())
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Store in Postgres
    try:
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO documents (id, content, source, metadata, created_at)
                       VALUES ($1, $2, $3, $4, $5)""",
                    doc_id,
                    request.content,
                    request.source,
                    json.dumps(request.metadata),
                    created_at,
                )
    except Exception as e:
        logger.error(f"Database storage failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("storage", "database-error", str(e)),
        )

    # Store in Qdrant with real embeddings
    if QDRANT_URL and QDRANT_API_KEY:
        try:
            # Use real embedding engine to store document
            success = await store_with_real_embedding(
                doc_id=doc_id,
                content=request.content,
                source=request.source,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=normalized_error("qdrant", "embedding-failed", "Failed to generate or store embedding")
                )
                
        except Exception as e:
            logger.error(f"Real embedding storage failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=normalized_error("qdrant", "qdrant-error", str(e)),
            )

    return {
        "status": "success",
        "document": Document(
            id=doc_id,
            content=request.content,
            source=request.source,
            metadata=request.metadata,
            created_at=created_at,
        ),
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """
    Searches for relevant documents using real semantic search.
    """
    start_time = time.time()

    if not (QDRANT_URL and QDRANT_API_KEY):
        raise HTTPException(
            status_code=503,
            detail=normalized_error(
                "qdrant", "missing-qdrant", "Qdrant not configured for search"
            ),
        )

    try:
        # Use real semantic search with embeddings
        search_results = await semantic_search_documents(
            query=request.query,
            limit=request.k
        )
        
        # Convert search results to Document objects
        documents = []
        for result in search_results:
            documents.append(Document(
                id=result.id,
                content=result.content,
                source=result.source,
                metadata=result.metadata,
                created_at=result.metadata.get('created_at', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            ))
        
        # Get cache statistics for summary
        cache_stats = await embedding_engine.get_cache_stats()
        
        return DocumentSearchResponse(
            status="success",
            query=request.query,
            results=documents,
            summary={
                "text": f"Found {len(documents)} semantically relevant documents for '{request.query}'",
                "confidence": sum(r.similarity_score for r in search_results) / len(search_results) if search_results else 0,
                "model": "real_embeddings_v2",
                "sources": ["qdrant_real_embeddings", "storage"],
                "cache_hit_ratio": cache_stats.get("cache_hit_ratio", "N/A"),
                "embedding_model": "text-embedding-3-large"
            },
            providers_used=["qdrant_real_embeddings", "storage"],
            providers_failed=[],
            execution_time_ms=int((time.time() - start_time) * 1000),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("qdrant", "search-failed", str(e)),
        )


@app.on_event("startup")
async def startup_event():
    if NEON_DATABASE_URL:
        try:
            await get_db_pool()
            logger.info("Context MCP v1 started with database connectivity")
        except Exception as e:
            logger.warning(f"Database connection failed at startup: {e}. Service will start without initial DB connection.")
    else:
        logger.warning("Context MCP v1 started without database - storage disabled")


@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


qdrant_client.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
