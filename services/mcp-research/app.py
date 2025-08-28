"""
Sophia AI Research & Data Acquisition MCP Service

This module provides a comprehensive Research MCP service that integrates with multiple
research and data providers including SerpAPI, Perplexity AI, Together AI, Anthropic,
and others for multi-source knowledge retrieval and analysis.

Key Features:
- Multi-provider research query execution across search engines and AI services
- Web scraping and data ingestion capabilities
- LLM-powered content summarization and analysis
- Vector database storage with Weaviate Cloud integration
- Comprehensive error handling and provider failover

Provider Integrations:
- SerpAPI: Google search results and web data
- Perplexity AI: Real-time AI-powered search and analysis
- Together AI: LLM inference for content generation and summarization
- Anthropic: Claude models for advanced reasoning tasks
- Voyage AI: Text embeddings for semantic search
- Cohere: Alternative embedding and reranking services
- Google AI: Search and language model services

Architecture:
- FastAPI-based async REST API
- PostgreSQL database integration for persistent storage
- Weaviate Cloud vector database for semantic search capabilities
- Multi-provider failover and cost optimization
- Comprehensive health monitoring and provider status tracking

Version: 2.0.0
Author: Sophia AI Intelligence Team
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
import asyncpg
import weaviate
from weaviate.classes.init import Auth
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import aggressive cache manager
from cache_manager import cache_manager, cached_research_query, CacheLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - Research Providers
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

app = FastAPI(
    title="sophia-mcp-research-v2",
    version="2.0.0",
    description="Research & Data Acquisition MCP for multi-source knowledge retrieval and analysis",
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
    Get or create database connection pool.
    
    Returns the global database connection pool, creating it if it doesn't exist.
    Used for storing research results, ingested data, and operational metadata.
    
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
    
    Standardizes error responses across all research providers and operations
    to ensure consistent debugging and error handling capabilities.
    
    Args:
        provider (str): Name of the research provider that generated the error
        code (str): Error code identifier for programmatic error handling
        message (str): Human-readable error message describing the issue
        details (Optional[Dict]): Additional error context and debugging information
        
    Returns:
        Dict[str, Any]: Normalized error object with standard MCP structure
        
    Example:
        >>> normalized_error("serpapi", "quota_exceeded", "Daily quota limit reached", {"limit": 1000})
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
    Check availability status of all research and data providers.
    
    Evaluates the configuration status of integrated research providers by checking
    for required API keys and environment variables. Does not test actual connectivity.
    
    Returns:
        Dict[str, str]: Provider status mapping with values:
            - "ready": Provider is configured with required credentials
            - "missing_secret": Required API keys or configuration missing
            
    Supported Research Providers:
        - serpapi: Google search results via SerpAPI
        - perplexity: Perplexity AI real-time search and analysis
        - together: Together AI LLM inference platform
        - anthropic: Anthropic Claude models for reasoning
        - voyage: Voyage AI embedding models for semantic search
        - cohere: Cohere embedding and reranking services
        - google: Google AI Platform services
        - weaviate: Vector database for semantic storage and retrieval
        - storage: PostgreSQL database for persistent data storage
        
    Note:
        Use the /healthz endpoint for comprehensive connectivity testing
    """
    return {
        "serpapi": "ready" if SERPAPI_API_KEY else "missing_secret",
        "perplexity": "ready" if PERPLEXITY_API_KEY else "missing_secret",
        "together": "ready" if TOGETHER_API_KEY else "missing_secret",
        "anthropic": "ready" if ANTHROPIC_API_KEY else "missing_secret",
        "voyage": "ready" if VOYAGE_API_KEY else "missing_secret",
        "cohere": "ready" if COHERE_API_KEY else "missing_secret",
        "google": "ready" if GOOGLE_API_KEY else "missing_secret",
        "weaviate": "ready" if (WEAVIATE_URL and WEAVIATE_API_KEY) else "missing_secret",
        "storage": "ready" if NEON_DATABASE_URL else "missing_secret",
    }


# Request/Response Models
class ResearchQuery(BaseModel):
    query: str = Field(..., description="Research query for data acquisition")
    providers: List[str] = Field(
        default=["serpapi"], description="Providers to use for research"
    )
    depth: int = Field(
        default=1,
        le=3,
        description="Depth of research (1-3, higher means more detailed)",
    )
    max_results: int = Field(
        default=5, le=20, description="Max results to return per query"
    )
    time_range: Optional[str] = Field(
        default=None, description="Time range for search (e.g., '1y', '1m', '1d')"
    )
    timeout_s: int = Field(default=60, le=300, description="Request timeout")
    cache_ttl_s: int = Field(default=3600, description="Cache time-to-live in seconds")


class ResearchResult(BaseModel):
    status: str
    query: str
    results: List[Dict]
    summary: Dict[str, Any]
    providers_used: List[str]
    providers_failed: List[Dict]
    execution_time_ms: int
    timestamp: str


class DataIngestRequest(BaseModel):
    source_url: HttpUrl = Field(..., description="URL of the data source")
    format: str = Field(
        default="auto", description="Format of the data (e.g., 'html', 'pdf', 'json')"
    )
    tags: List[str] = Field(default=[], description="Tags for the ingested data")


class DataAnalyzeRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to analyze")
    analysis_type: str = Field(
        default="summary", description="Type of analysis to perform"
    )


class WebScrapeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to scrape")
    css_selector: Optional[str] = Field(
        default=None, description="CSS selector for specific content"
    )


class WebScrapeResponse(BaseModel):
    url: HttpUrl
    content: str
    timestamp: str


class ProviderEnum(str, Enum):
    serpapi = "serpapi"
    perplexity = "perplexity"
    together = "together"
    anthropic = "anthropic"
    voyage = "voyage"
    cohere = "cohere"
    google = "google"


# Weaviate client initialization using official cloud connection pattern
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
) if WEAVIATE_URL and WEAVIATE_API_KEY else None


# Provider Implementations
class SerpAPIProvider:
    @staticmethod
    async def search(
        query: str, max_results: int = 5, time_range: Optional[str] = None
    ) -> List[Dict]:
        if not SERPAPI_API_KEY:
            raise ValueError("SERPAPI_API_KEY not configured")

        async with httpx.AsyncClient(timeout=30) as client:
            params = {"q": query, "api_key": SERPAPI_API_KEY, "num": max_results}
            if time_range:
                params["tbs"] = time_range  # Example: "qdr:1y" for last year

            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic_results", []):
                results.append(
                    {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                    }
                )
            return results


class PerplexityAIProvider:
    @staticmethod
    async def search(query: str) -> Dict[str, Any]:
        if not PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not configured")

        async with httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            timeout=60,
        ) as client:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": "llama-3-sonar-small-32k-online",
                    "messages": [{"role": "user", "content": query}],
                },
            )
            response.raise_for_status()
            data = response.json()

            return {
                "answer": data["choices"][0]["message"]["content"],
                "source_urls": [
                    c["raw_url"] for c in data.get("usage", {}).get("references", [])
                ],
            }


class TogetherAIProvider:
    @staticmethod
    async def generate_text(prompt: str) -> str:
        if not TOGETHER_API_KEY:
            raise ValueError("TOGETHER_API_KEY not configured")

        async with httpx.AsyncClient(
            base_url="https://api.together.xyz",
            headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
            timeout=120,
        ) as client:
            response = await client.post(
                "/inference",
                json={
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "prompt": f"[INST] {prompt} [/INST]",
                    "max_tokens": 512,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()

            return data["output"]["choices"][0]["text"]


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

    # Check Weaviate connectivity
    weaviate_status = "unknown"
    if WEAVIATE_URL and WEAVIATE_API_KEY:
        try:
            if weaviate_client and weaviate_client.is_ready():
                weaviate_status = "connected"
            else:
                weaviate_status = "error"
        except Exception as e:
            weaviate_status = f"error: {str(e)[:50]}"
    else:
        weaviate_status = "not_configured"

    ready_providers = [k for k, v in providers.items() if v == "ready"]
    missing_providers = [k for k, v in providers.items() if v == "missing_secret"]

    if len(ready_providers) == 0:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-research-v1",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "providers": providers,
                "database": db_status,
                "vector_database": weaviate_status,
                "capabilities": {
                    "search": len(
                        [
                            p
                            for p in ["serpapi", "perplexity", "google"]
                            if providers[p] == "ready"
                        ]
                    )
                    > 0,
                    "llm": len(
                        [
                            p
                            for p in ["together", "anthropic"]
                            if providers[p] == "ready"
                        ]
                    )
                    > 0,
                    "embed": len(
                        [p for p in ["voyage", "cohere"] if providers[p] == "ready"]
                    )
                    > 0,
                    "storage": providers["storage"] == "ready",
                },
                "error": normalized_error(
                    "research",
                    "no-providers",
                    f"No research providers configured. Missing: {', '.join(missing_providers[:5])}",
                ),
            },
        )

    return {
        "status": "healthy" if len(ready_providers) >= 2 else "degraded",
        "service": "sophia-mcp-research-v1",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "providers": providers,
        "database": db_status,
        "vector_database": weaviate_status,
        "capabilities": {
            "search": len(
                [
                    p
                    for p in ["serpapi", "perplexity", "google"]
                    if providers[p] == "ready"
                ]
            )
            > 0,
            "llm": len(
                [p for p in ["together", "anthropic"] if providers[p] == "ready"]
            )
            > 0,
            "embed": len([p for p in ["voyage", "cohere"] if providers[p] == "ready"])
            > 0,
            "storage": providers["storage"] == "ready",
        },
        "ready_providers": ready_providers,
        "missing_providers": missing_providers,
    }


@app.post("/research/query", response_model=ResearchResult)
@cached_research_query(ttl=3600, level=CacheLevel.WARM)
async def research_query(request: ResearchQuery):
    """
    Performs a cached research query across multiple providers, aggregates results,
    and returns a summarized response with intelligent caching.
    """
    start_time = time.time()
    
    # Check cache first (handled by decorator)
    cached_result = await cache_manager.get_cached_research_query(
        request.query, 
        request.providers,
        depth=request.depth,
        max_results=request.max_results,
        time_range=request.time_range
    )
    
    if cached_result:
        logger.info(f"Returning cached result for query: {request.query[:50]}...")
        return ResearchResult(**cached_result)

    results = []
    providers_used = []
    providers_failed = []

    # Prioritize providers based on depth and availability
    if "serpapi" in request.providers and SERPAPI_API_KEY:
        try:
            serp_results = await SerpAPIProvider.search(
                request.query, request.max_results, request.time_range
            )
            results.extend(serp_results)
            providers_used.append("serpapi")
        except Exception as e:
            logger.error(f"SerpAPI failed: {e}")
            providers_failed.append({"provider": "serpapi", "error": str(e)})

    if "perplexity" in request.providers and PERPLEXITY_API_KEY:
        try:
            perplexity_result = await PerplexityAIProvider.search(request.query)
            results.append(
                {"type": "perplexity_answer", "content": perplexity_result["answer"]}
            )
            if "source_urls" in perplexity_result:
                results.append(
                    {
                        "type": "perplexity_sources",
                        "urls": perplexity_result["source_urls"],
                    }
                )
            providers_used.append("perplexity")
        except Exception as e:
            logger.error(f"PerplexityAI failed: {e}")
            providers_failed.append({"provider": "perplexity", "error": str(e)})

    # Simple summarization based on results
    summary_text = (
        f"Research query: '{request.query}'. Found {len(results)} raw results. "
    )
    if "together" in request.providers and TOGETHER_API_KEY and results:
        try:
            summarized_content = " ".join(
                [
                    r.get("snippet", r.get("content", ""))
                    for r in results[: request.max_results]
                ]
            )
            if summarized_content:
                summary_prompt = f"Summarize the following research findings about '{request.query}':\n\n{summarized_content}"
                llm_summary = await TogetherAIProvider.generate_text(summary_prompt)
                summary_text = f"Summary: {llm_summary}"
                providers_used.append("together")
        except Exception as e:
            logger.error(f"TogetherAI summarization failed: {e}")
            providers_failed.append(
                {"provider": "together_summarization", "error": str(e)}
            )

    # Store research results in Weaviate for semantic search
    if research_vector_store and results:
        try:
            # Store each significant result in vector database
            for i, result in enumerate(results[:3]):  # Store top 3 results
                content = result.get("snippet", result.get("content", ""))
                source = result.get("link", result.get("title", f"result_{i}"))
                provider = result.get("type", "unknown")
                
                if content and len(content.strip()) > 20:  # Only store meaningful content
                    await research_vector_store.store_research_result(
                        query=request.query,
                        content=content,
                        source=source,
                        provider=provider,
                        confidence=0.8,
                        metadata={
                            "depth": request.depth,
                            "max_results": request.max_results,
                            "time_range": request.time_range,
                            "providers_used": providers_used
                        }
                    )
            logger.info(f"Stored research results in Weaviate for query: {request.query}")
        except Exception as e:
            logger.warning(f"Failed to store research results in Weaviate: {e}")
            # Don't fail the request if vector storage fails

    return ResearchResult(
        status="success" if results else "partial" if providers_failed else "failed",
        query=request.query,
        results=results,
        summary={
            "text": summary_text,
            "confidence": 0.8,
            "model": "research_v1",
            "sources": providers_used,
        },
        providers_used=providers_used,
        providers_failed=providers_failed,
        execution_time_ms=int((time.time() - start_time) * 1000),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@app.post("/data/ingest")
async def ingest_data(request: DataIngestRequest):
    """
    Ingests data from a specified URL and stores it. (Placeholder for full implementation)
    """
    start_time = time.time()

    if not NEON_DATABASE_URL:
        raise HTTPException(
            status_code=503,
            detail=normalized_error(
                "storage", "missing-database", "NEON_DATABASE_URL not configured"
            ),
        )

    try:
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO ingested_data (url, format, tags, content, metadata_json, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    str(request.source_url),
                    request.format,
                    request.tags,
                    "Placeholder content",
                    json.dumps({"status": "placeholder"}),
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
        logger.info(f"Ingested data from {request.source_url}")
    except Exception as e:
        logger.error(f"Data ingestion failed for {request.source_url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("data_ingestion", "ingestion-failed", str(e)),
        )

    return {
        "status": "success",
        "source_url": request.source_url,
        "tags": request.tags,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.post("/data/analyze")
async def analyze_data(request: DataAnalyzeRequest):
    """
    Performs specific analysis on provided data. (Placeholder for full implementation)
    """
    start_time = time.time()

    # This would integrate with LLMs, statistical models, etc.
    analysis_summary = (
        f"Analysis of type '{request.analysis_type}' performed "
        f"on provided data. Data size: {len(json.dumps(request.data))} bytes."
    )

    return {
        "status": "success",
        "analysis_type": request.analysis_type,
        "summary": analysis_summary,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.post("/web/scrape", response_model=WebScrapeResponse)
async def web_scrape(request: WebScrapeRequest):
    """
    Scrapes content from a given URL. (Placeholder for full implementation)
    """
    time.time()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(str(request.url))
            response.raise_for_status()
            content = response.text

            # Simple selector logic
            if request.css_selector:
                # This would typically use a library like BeautifulSoup or lxml
                content = (
                    f"Content for selector '{request.css_selector}': {content[:200]}..."
                )

        logger.info(f"Scraped content from {request.url}")

    except Exception as e:
        logger.error(f"Web scraping failed for {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("web_scrape", "scrape-failed", str(e)),
        )

    return WebScrapeResponse(
        url=request.url,
        content=content,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@app.on_event("startup")
async def startup_event():
    """Initialize all services and connections"""
    # Initialize database pool with defensive error handling
    if NEON_DATABASE_URL:
        try:
            await get_db_pool()
            logger.info("Research MCP v2 started with database connectivity")
        except Exception as e:
            logger.warning(f"Database connection failed at startup: {e}. Service will start without initial DB connection.")
    else:


@app.post("/research/search")
async def semantic_search_research(request: DocumentSearchRequest):
    """
    Performs semantic search on previously stored research results using Weaviate.
    """
    start_time = time.time()

    if not research_vector_store:
        raise HTTPException(
            status_code=503,
            detail=normalized_error(
                "weaviate", "missing-vector-store", "Research vector store not configured"
            ),
        )

    try:
        # Perform semantic search on stored research results
        search_results = await research_vector_store.semantic_search_research(
            query=request.query,
            limit=request.k,
            confidence_threshold=0.5
        )

        return {
            "status": "success",
            "query": request.query,
            "results": search_results,
            "summary": {
                "text": f"Found {len(search_results)} semantically relevant research results for '{request.query}'",
                "confidence": sum(r["similarity_score"] for r in search_results) / len(search_results) if search_results else 0,
                "model": "weaviate_semantic_search",
                "sources": ["weaviate_vector_store"]
            },
            "providers_used": ["weaviate"],
            "providers_failed": [],
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    except Exception as e:
        logger.error(f"Semantic research search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("weaviate", "search-failed", str(e)),
        )
        logger.warning("Research MCP v2 started without database - storage disabled")
    
    # Initialize aggressive cache manager
    cache_initialized = await cache_manager.initialize()
    if cache_initialized:
        logger.info("Aggressive cache manager initialized successfully")
        
        # Warm cache with common research queries
        common_queries = [
            "artificial intelligence trends 2025",
            "microservices architecture best practices", 
            "API security vulnerabilities",
            "database performance optimization",
            "cloud computing cost optimization"
        ]
        await cache_manager.warm_cache_for_common_queries(common_queries)
        
    else:
        logger.warning("Cache manager initialization failed - caching disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of all connections"""
    # Close database pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")
    
    # Close cache manager connections
    await cache_manager.close()
    logger.info("Cache manager closed")


# Add cache monitoring endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get comprehensive cache performance statistics"""
    try:
        stats = await cache_manager.get_cache_performance_stats()
        return {
            "status": "success",
            "cache_stats": {
                "total_requests": stats.total_requests,
                "cache_hits": stats.cache_hits, 
                "cache_misses": stats.cache_misses,
                "hit_ratio": stats.hit_ratio,
                "average_response_time_ms": stats.average_response_time_ms,
                "total_keys": stats.total_keys,
                "memory_usage_bytes": stats.memory_usage_bytes
            },
            "cache_health": cache_manager.get_cache_health(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}


@app.get("/cache/hot-queries")
async def get_hot_queries():
    """Get most frequently accessed queries"""
    try:
        hot_queries = await cache_manager.get_hot_queries(20)
        return {
            "status": "success",
            "hot_queries": hot_queries,
            "total_tracked": len(hot_queries),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        logger.error(f"Failed to get hot queries: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/cache/cleanup")
async def cleanup_cache():
    """Clean up expired and low-value cache entries"""
    try:
        cleaned_count = await cache_manager.cleanup_expired_entries()
        return {
            "status": "success",
            "entries_cleaned": cleaned_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/cache/optimize")
async def optimize_cache():
    """Optimize cache levels based on access patterns"""
    try:
        await cache_manager.optimize_cache_levels()
        return {
            "status": "success", 
            "message": "Cache optimization completed",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        logger.error(f"Cache optimization failed: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")



# Research Vector Operations with Weaviate
class ResearchVectorStore:
    """
    Weaviate-based vector storage for research results and semantic search.
    Provides research-specific vector operations following proven patterns.
    """
    
    def __init__(self, client):
        self.client = client
        self.class_name = "ResearchResult"
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Initialize Weaviate schema for research results"""
        if not self.client:
            return
        
        try:
            # Check if class already exists
            existing_classes = self.client.schema.get()["classes"]
            class_names = [cls["class"] for cls in existing_classes]
            
            if self.class_name not in class_names:
                # Create the ResearchResult class schema
                research_class = {
                    "class": self.class_name,
                    "description": "Research results with semantic search capabilities",
                    "properties": [
                        {
                            "name": "query",
                            "dataType": ["text"],
                            "description": "Original research query"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Research result content"
                        },
                        {
                            "name": "source",
                            "dataType": ["text"],
                            "description": "Source of the research result"
                        },
                        {
                            "name": "provider",
                            "dataType": ["text"],
                            "description": "Research provider used"
                        },
                        {
                            "name": "confidence",
                            "dataType": ["number"],
                            "description": "Confidence score of the result"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Additional metadata as JSON string"
                        },
                        {
                            "name": "created_at",
                            "dataType": ["date"],
                            "description": "Creation timestamp"
                        }
                    ],
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "text-embedding-3-large",
                            "modelVersion": "003",
                            "type": "text"
                        }
                    }
                }
                
                self.client.schema.create_class(research_class)
                logger.info(f"Created Weaviate class: {self.class_name}")
                
        except Exception as e:
            logger.warning(f"Failed to initialize Weaviate schema: {e}")
    
    async def store_research_result(
        self,
        query: str,
        content: str,
        source: str,
        provider: str,
        confidence: float = 0.8,
        metadata: dict = None
    ) -> bool:
        """Store a research result with vector embedding"""
        if not self.client:
            return False
        
        try:
            data_object = {
                "query": query,
                "content": content,
                "source": source,
                "provider": provider,
                "confidence": confidence,
                "metadata": json.dumps(metadata or {}),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            # Store with automatic vectorization
            result = self.client.data_object.create(
                data_object=data_object,
                class_name=self.class_name
            )
            
            logger.info(f"Stored research result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store research result: {e}")
            return False
    
    async def semantic_search_research(
        self,
        query: str,
        limit: int = 5,
        confidence_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on stored research results"""
        if not self.client:
            return []
        
        try:
            # Perform semantic search using Weaviate's vector search
            result = (
                self.client.query
                .get(self.class_name, [
                    "query", "content", "source", "provider", 
                    "confidence", "metadata", "created_at"
                ])
                .with_near_text({"concepts": [query]})
                .with_additional(["certainty", "id"])
                .with_limit(limit)
                .do()
            )
            
            # Process results
            search_results = []
            if result.get("data", {}).get("Get", {}).get(self.class_name):
                for item in result["data"]["Get"][self.class_name]:
                    # Convert certainty to similarity score
                    certainty = item.get("_additional", {}).get("certainty", 0)
                    
                    # Filter by confidence threshold
                    if certainty >= confidence_threshold:
                        search_results.append({
                            "id": item.get("_additional", {}).get("id"),
                            "query": item.get("query", ""),
                            "content": item.get("content", ""),
                            "source": item.get("source", ""),
                            "provider": item.get("provider", ""),
                            "confidence": item.get("confidence", 0),
                            "metadata": json.loads(item.get("metadata", "{}")),
                            "created_at": item.get("created_at", ""),
                            "similarity_score": certainty
                        })
            
            logger.info(f"Found {len(search_results)} relevant research results for: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []


# Initialize research vector store
research_vector_store = ResearchVectorStore(weaviate_client) if weaviate_client else None
