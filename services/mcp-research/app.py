import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - Search Providers
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY") 
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

# Environment variables - Scraping Providers
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")

# Environment variables - LLM Routing
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Environment variables - Caching
REDIS_URL = os.getenv("REDIS_URL")

# Environment variables - Configuration
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
COST_LIMIT_USD = float(os.getenv("COST_LIMIT_USD", "10.0"))
MAX_RESULTS_PER_PROVIDER = int(os.getenv("MAX_RESULTS_PER_PROVIDER", "5"))

app = FastAPI(
    title="sophia-mcp-research-v2",
    version="2.0.0",
    description="Multi-provider research meta-aggregator with search, scraping, and AI summarization"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sophiaai-dashboard.fly.dev", "https://github.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalized_error(provider: str, code: str, message: str, details: Optional[Dict] = None):
    """Return normalized error JSON format"""
    error_obj = {
        "error": {
            "provider": provider,
            "code": code,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }
    if details:
        error_obj["error"]["details"] = details
    return error_obj

def get_provider_status():
    """Get current provider availability status"""
    return {
        "search_providers": {
            "tavily": "ready" if TAVILY_API_KEY else "missing_secret",
            "serper": "ready" if SERPER_API_KEY else "missing_secret", 
            "perplexity": "ready" if PERPLEXITY_API_KEY else "missing_secret",
            "exa": "ready" if EXA_API_KEY else "missing_secret"
        },
        "scraping_providers": {
            "apify": "ready" if APIFY_API_KEY else "missing_secret",
            "zenrows": "ready" if ZENROWS_API_KEY else "missing_secret", 
            "brightdata": "ready" if BRIGHTDATA_API_KEY else "missing_secret"
        },
        "llm_routing": {
            "portkey": "ready" if PORTKEY_API_KEY else "missing_secret",
            "openrouter": "ready" if OPENROUTER_API_KEY else "missing_secret"
        },
        "caching": {
            "redis": "ready" if REDIS_URL else "missing_secret"
        }
    }

# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    providers: List[str] = Field(default=["tavily", "serper"], description="Search providers to use")
    max_results: int = Field(default=10, le=50, description="Maximum results per provider")
    summarize: bool = Field(default=True, description="Generate AI summary")
    cost_limit_usd: float = Field(default=1.0, le=10.0, description="Cost limit in USD")

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    providers: List[str] = Field(default=["zenrows"], description="Scraping providers to try")
    extract_type: str = Field(default="content", description="Type of extraction: content, links, images")
    javascript_enabled: bool = Field(default=False, description="Enable JavaScript rendering")

class SummarizeRequest(BaseModel):
    content: str = Field(..., description="Content to summarize")
    style: str = Field(default="concise", description="Summary style: concise, detailed, bullet_points")
    max_length: int = Field(default=500, le=2000, description="Maximum summary length")

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    score: float
    provider: str
    timestamp: str

class ScrapeResult(BaseModel):
    url: str
    content: str
    status_code: int
    provider: str
    extraction_type: str
    timestamp: str
    metadata: Optional[Dict] = None

class SearchResponse(BaseModel):
    status: str
    query: str
    results: List[SearchResult]
    summary: Optional[Dict] = None
    providers_used: List[str]
    providers_failed: List[Dict] = []
    cost_breakdown: Dict[str, float]
    total_cost_usd: float
    execution_time_ms: int
    timestamp: str

class ScrapeResponse(BaseModel):
    status: str
    url: str
    results: List[ScrapeResult]
    providers_used: List[str]
    providers_failed: List[Dict] = []
    cost_breakdown: Dict[str, float]
    total_cost_usd: float
    execution_time_ms: int
    timestamp: str

class SummarizeResponse(BaseModel):
    status: str
    summary: str
    style: str
    input_length: int
    output_length: int
    model_used: str
    cost_usd: float
    execution_time_ms: int
    timestamp: str

# Provider Implementations
class TavilyProvider:
    @staticmethod
    async def search(query: str, max_results: int) -> tuple[List[SearchResult], float]:
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": min(max_results, MAX_RESULTS_PER_PROVIDER),
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_images": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:500],
                    source="web",
                    score=item.get("score", 0.0),
                    provider="tavily",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                ))
            
            cost = len(results) * 0.001  # $0.001 per result
            return results, cost

class SerperProvider:
    @staticmethod
    async def search(query: str, max_results: int) -> tuple[List[SearchResult], float]:
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY not configured")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                json={
                    "q": query,
                    "num": min(max_results, MAX_RESULTS_PER_PROVIDER)
                },
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")[:500],
                    source="google",
                    score=1.0,  # Serper doesn't provide scores
                    provider="serper",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                ))
            
            cost = len(results) * 0.001  # $0.001 per result
            return results, cost

class ZenRowsProvider:
    @staticmethod
    async def scrape(url: str, javascript_enabled: bool = False) -> tuple[ScrapeResult, float]:
        if not ZENROWS_API_KEY:
            raise ValueError("ZENROWS_API_KEY not configured")
            
        params = {
            "api_key": ZENROWS_API_KEY,
            "url": url,
        }
        if javascript_enabled:
            params["js_render"] = "true"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=60.0
            )
            
            result = ScrapeResult(
                url=url,
                content=response.text[:10000],  # Limit content size
                status_code=response.status_code,
                provider="zenrows",
                extraction_type="full_content",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                metadata={"content_length": len(response.text)}
            )
            
            cost = 0.01 if javascript_enabled else 0.005  # Higher cost for JS rendering
            return result, cost

class PortkeyProvider:
    @staticmethod
    async def summarize(content: str, style: str, max_length: int) -> tuple[str, float]:
        if not PORTKEY_API_KEY:
            raise ValueError("PORTKEY_API_KEY not configured")
        
        style_prompts = {
            "concise": "Provide a concise summary in 2-3 sentences.",
            "detailed": "Provide a detailed summary with key points and context.",
            "bullet_points": "Provide a summary in bullet point format with main ideas."
        }
        
        prompt = f"{style_prompts.get(style, style_prompts['concise'])}\n\nContent to summarize:\n{content[:5000]}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                json={
                    "model": DEFAULT_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that creates accurate summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": min(max_length, 1000),
                    "temperature": 0.3
                },
                headers={
                    "Authorization": f"Bearer {PORTKEY_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            summary = data["choices"][0]["message"]["content"]
            
            # Estimate cost based on tokens (rough approximation)
            input_tokens = len(content.split()) * 1.3  # Rough token estimate
            output_tokens = len(summary.split()) * 1.3
            cost = (input_tokens * 0.00001) + (output_tokens * 0.00003)  # GPT-4o-mini pricing
            
            return summary, cost

# API Endpoints
@app.get("/healthz")
async def healthz():
    """Health check endpoint with provider status"""
    providers = get_provider_status()
    
    # Check if we have at least one provider in each category
    has_search = any(status == "ready" for status in providers["search_providers"].values())
    has_llm = any(status == "ready" for status in providers["llm_routing"].values())
    
    missing_critical = []
    if not has_llm:
        missing_critical.extend([k for k, v in providers["llm_routing"].items() if v == "missing_secret"])
    
    if missing_critical:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "service": "sophia-mcp-research-v2", 
                "version": "2.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "providers": providers,
                "capabilities": {
                    "search": has_search,
                    "scrape": any(status == "ready" for status in providers["scraping_providers"].values()),
                    "summarize": has_llm,
                    "cache": providers["caching"]["redis"] == "ready"
                },
                "error": normalized_error(
                    "research_service",
                    "MISSING_CRITICAL_PROVIDERS", 
                    f"Missing critical providers: {', '.join(missing_critical)}"
                )
            }
        )
    
    return {
        "status": "healthy" if has_search and has_llm else "degraded",
        "service": "sophia-mcp-research-v2",
        "version": "2.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "providers": providers,
        "capabilities": {
            "search": has_search,
            "scrape": any(status == "ready" for status in providers["scraping_providers"].values()),
            "summarize": has_llm,
            "cache": providers["caching"]["redis"] == "ready"
        },
        "cost_limits": {
            "max_cost_usd": COST_LIMIT_USD,
            "max_results_per_provider": MAX_RESULTS_PER_PROVIDER
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Multi-provider search with optional AI summarization"""
    start_time = time.time()
    
    # Validate cost limit
    if request.cost_limit_usd > COST_LIMIT_USD:
        return JSONResponse(
            status_code=400,
            content=normalized_error(
                "research_service",
                "COST_LIMIT_EXCEEDED",
                f"Requested cost limit ${request.cost_limit_usd} exceeds maximum ${COST_LIMIT_USD}"
            )
        )
    
    results = []
    providers_used = []
    providers_failed = []
    cost_breakdown = {}
    total_cost = 0.0
    
    # Execute search providers in parallel
    search_tasks = []
    for provider in request.providers:
        if provider == "tavily" and TAVILY_API_KEY:
            search_tasks.append(("tavily", TavilyProvider.search(request.query, request.max_results)))
        elif provider == "serper" and SERPER_API_KEY:
            search_tasks.append(("serper", SerperProvider.search(request.query, request.max_results)))
        else:
            providers_failed.append({
                "provider": provider,
                "error": f"Provider {provider} not configured or unsupported"
            })
    
    # Execute searches
    for provider_name, task in search_tasks:
        try:
            provider_results, cost = await task
            results.extend(provider_results)
            providers_used.append(provider_name)
            cost_breakdown[provider_name] = cost
            total_cost += cost
            
            if total_cost > request.cost_limit_usd:
                logger.warning(f"Cost limit ${request.cost_limit_usd} exceeded, stopping additional searches")
                break
                
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {str(e)}")
            providers_failed.append({
                "provider": provider_name,
                "error": str(e)
            })
    
    # Generate summary if requested and we have LLM capability
    summary = None
    if request.summarize and results and (PORTKEY_API_KEY or OPENROUTER_API_KEY):
        try:
            combined_content = "\n\n".join([f"{r.title}: {r.snippet}" for r in results[:10]])
            if PORTKEY_API_KEY and total_cost < request.cost_limit_usd:
                summary_text, summary_cost = await PortkeyProvider.summarize(
                    combined_content, "concise", 300
                )
                summary = {
                    "text": summary_text,
                    "model": DEFAULT_LLM_MODEL,
                    "provider": "portkey",
                    "confidence": 0.8
                }
                cost_breakdown["summarization"] = summary_cost
                total_cost += summary_cost
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
    
    return SearchResponse(
        status="success" if results else "partial" if providers_failed else "failed",
        query=request.query,
        results=sorted(results, key=lambda x: x.score, reverse=True)[:request.max_results],
        summary=summary,
        providers_used=providers_used,
        providers_failed=providers_failed,
        cost_breakdown=cost_breakdown,
        total_cost_usd=round(total_cost, 4),
        execution_time_ms=int((time.time() - start_time) * 1000),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest):
    """Multi-provider web scraping"""
    start_time = time.time()
    
    results = []
    providers_used = []
    providers_failed = []
    cost_breakdown = {}
    total_cost = 0.0
    
    # Try scraping providers in order of preference
    for provider in request.providers:
        if provider == "zenrows" and ZENROWS_API_KEY:
            try:
                result, cost = await ZenRowsProvider.scrape(request.url, request.javascript_enabled)
                results.append(result)
                providers_used.append(provider)
                cost_breakdown[provider] = cost
                total_cost += cost
                break  # Success, stop trying other providers
                
            except Exception as e:
                logger.error(f"Provider {provider} failed: {str(e)}")
                providers_failed.append({
                    "provider": provider,
                    "error": str(e)
                })
        else:
            providers_failed.append({
                "provider": provider,
                "error": f"Provider {provider} not configured or unsupported"
            })
    
    return ScrapeResponse(
        status="success" if results else "failed",
        url=request.url,
        results=results,
        providers_used=providers_used,
        providers_failed=providers_failed,
        cost_breakdown=cost_breakdown,
        total_cost_usd=round(total_cost, 4),
        execution_time_ms=int((time.time() - start_time) * 1000),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """AI-powered content summarization"""
    start_time = time.time()
    
    if not (PORTKEY_API_KEY or OPENROUTER_API_KEY):
        return JSONResponse(
            status_code=503,
            content=normalized_error(
                "research_service",
                "NO_LLM_PROVIDERS",
                "No LLM providers configured for summarization"
            )
        )
    
    try:
        # Try Portkey first, then fallback to OpenRouter
        if PORTKEY_API_KEY:
            summary, cost = await PortkeyProvider.summarize(
                request.content, request.style, request.max_length
            )
            model_used = DEFAULT_LLM_MODEL
        else:
            # OpenRouter implementation would go here
            raise ValueError("OpenRouter not yet implemented")
        
        return SummarizeResponse(
            status="success",
            summary=summary,
            style=request.style,
            input_length=len(request.content),
            output_length=len(summary),
            model_used=model_used,
            cost_usd=round(cost, 4),
            execution_time_ms=int((time.time() - start_time) * 1000),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=normalized_error(
                "llm_provider",
                "SUMMARIZATION_FAILED",
                str(e)
            )
        )

@app.get("/providers")
async def get_providers():
    """Get current provider status and capabilities"""
    return {
        "status": "success",
        "providers": get_provider_status(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")