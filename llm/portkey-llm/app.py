import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import json
import os
import logging
import time
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sophia AI Standardized LLM Service")

class SummarizeRequest(BaseModel):
    content: str
    prompt_template: Optional[str] = None
    max_tokens: Optional[int] = 500
    model: Optional[str] = "o1-preview"  # Updated to use standardized primary model
    use_fallback: Optional[bool] = True

class SummarizeResponse(BaseModel):
    summary: str
    model_used: str
    provider: str
    token_count: int
    processing_time_ms: int
    fallback_used: bool

class ModelHealth(BaseModel):
    model: str
    provider: str
    status: str
    response_time_ms: Optional[int]
    last_used: Optional[str]

# Standardized model hierarchy - OpenRouter removed
STANDARDIZED_MODELS = {
    "primary": [
        {"name": "o1-preview", "provider": "openai", "virtual_key": "openai-o1-preview"},
        {"name": "gpt-5", "provider": "openai", "virtual_key": "openai-gpt-5"}
    ],
    "secondary": [
        {"name": "grok-4", "provider": "xai", "virtual_key": "xai-grok-4"}
    ],
    "efficiency": [
        {"name": "gpt-4o-mini", "provider": "openai", "virtual_key": "openai-gpt-4o-mini"},
        {"name": "grok-1-beta", "provider": "xai", "virtual_key": "xai-grok-1-beta"}
    ],
    "backup": [
        {"name": "claude-3-5-sonnet-20241022", "provider": "anthropic", "virtual_key": "anthropic-claude-3-5-sonnet"}
    ]
}

class StandardizedLLMClient:
    """Standardized LLM client using Portkey virtual keys - OpenRouter removed"""

    def __init__(self):
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        self.session: Optional[httpx.AsyncClient] = None
        self.model_health: Dict[str, Dict] = {}
        self.request_count = 0
        self.error_count = 0

    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={"User-Agent": "Sophia-AI-Standardized-LLM/2.0"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    def get_model_hierarchy(self, requested_model: str = None) -> List[Dict]:
        """Get model hierarchy for routing decisions"""
        if requested_model:
            # Find specific model in hierarchy
            for tier in ["primary", "secondary", "efficiency", "backup"]:
                for model in STANDARDIZED_MODELS[tier]:
                    if model["name"] == requested_model:
                        return [model]

        # Return full hierarchy in order of preference
        hierarchy = []
        hierarchy.extend(STANDARDIZED_MODELS["primary"])
        hierarchy.extend(STANDARDIZED_MODELS["secondary"])
        hierarchy.extend(STANDARDIZED_MODELS["efficiency"])
        hierarchy.extend(STANDARDIZED_MODELS["backup"])
        return hierarchy

    async def call_standardized_llm(self, model_config: Dict, messages: List[Dict],
                                   max_tokens: int = 500, temperature: float = 0.3) -> Dict:
        """Call LLM using standardized Portkey routing"""
        if not self.session or not self.portkey_api_key:
            raise Exception("LLM client not properly initialized")

        start_time = time.time()

        headers = {
            "x-portkey-api-key": self.portkey_api_key,
            "x-portkey-virtual-key": model_config["virtual_key"],
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_config["name"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = await self.session.post(
                "https://api.portkey.ai/v1/chat/completions",
                json=payload,
                headers=headers
            )

            response_time = int((time.time() - start_time) * 1000)
            self.request_count += 1

            # Update health metrics
            self.model_health[model_config["name"]] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response_time,
                "last_used": datetime.now(timezone.utc).isoformat(),
                "provider": model_config["provider"]
            }

            response.raise_for_status()
            data = response.json()

            return {
                "response": data,
                "model_used": model_config["name"],
                "provider": model_config["provider"],
                "response_time_ms": response_time,
                "fallback_used": False
            }

        except Exception as e:
            self.error_count += 1
            response_time = int((time.time() - start_time) * 1000)

            # Update health metrics
            self.model_health[model_config["name"]] = {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "last_used": datetime.now(timezone.utc).isoformat(),
                "provider": model_config["provider"],
                "error": str(e)
            }

            raise Exception(f"LLM call failed for {model_config['name']}: {str(e)}")

    async def call_with_fallback(self, messages: List[Dict], requested_model: str = None,
                               max_tokens: int = 500, temperature: float = 0.3) -> Dict:
        """Call LLM with automatic fallback using standardized hierarchy"""
        model_hierarchy = self.get_model_hierarchy(requested_model)

        last_error = None

        for model_config in model_hierarchy:
            try:
                logger.info(f"Attempting LLM call with {model_config['name']} ({model_config['provider']})")
                result = await self.call_standardized_llm(model_config, messages, max_tokens, temperature)

                if model_config != model_hierarchy[0]:  # If not the first choice
                    result["fallback_used"] = True
                    logger.warning(f"Used fallback model: {model_config['name']} (requested: {requested_model or 'auto'})")

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_config['name']} failed: {str(e)}")
                continue

        # All models failed
        raise Exception(f"All standardized models failed. Last error: {str(last_error)}")

# Global client instance
llm_client = StandardizedLLMClient()

# SSE keep-alive
async def sse_keepalive():
    while True:
        await asyncio.sleep(25)
        # In production, send SSE ping here

@app.on_event("startup")
async def startup():
    asyncio.create_task(sse_keepalive())
    logger.info("Sophia AI Standardized LLM Service started")

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Summarize content using standardized LLM routing with intelligent fallback"""

    start_time = time.time()

    # Default prompt template for call summarization
    if not request.prompt_template:
        request.prompt_template = """
        Summarize the following content in a concise manner:
        - Key points and main ideas
        - Important details and context
        - Action items or conclusions if applicable
        - Next steps or recommendations if mentioned

        Content:
        {content}

        Summary:
        """

    prompt = request.prompt_template.format(content=request.content)

    messages = [
        {"role": "system", "content": "You are a professional summarizer providing clear, concise summaries."},
        {"role": "user", "content": prompt}
    ]

    try:
        async with llm_client as client:
            result = await client.call_with_fallback(
                messages=messages,
                requested_model=request.model,
                max_tokens=request.max_tokens,
                temperature=0.3
            )

        summary = result["response"]["choices"][0]["message"]["content"]
        token_count = result["response"].get("usage", {}).get("total_tokens", 0)
        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Summary completed using {result['model_used']} ({result['provider']}) in {processing_time}ms")

        return SummarizeResponse(
            summary=summary,
            model_used=result["model_used"],
            provider=result["provider"],
            token_count=token_count,
            processing_time_ms=processing_time,
            fallback_used=result.get("fallback_used", False)
        )

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Summarization failed after {processing_time}ms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check with standardized model status"""
    return {
        "status": "healthy",
        "service": "sophia-standardized-llm",
        "request_count": llm_client.request_count,
        "error_count": llm_client.error_count,
        "model_health": llm_client.model_health,
        "standardized_routing": True,
        "openrouter_removed": True
    }

@app.get("/models")
async def list_models():
    """List all standardized models with their hierarchy"""
    return {
        "hierarchy": STANDARDIZED_MODELS,
        "routing_enabled": True,
        "fallback_enabled": True,
        "openrouter_removed": True
    }

@app.get("/metrics")
async def get_metrics():
    """Get LLM service metrics"""
    return {
        "total_requests": llm_client.request_count,
        "total_errors": llm_client.error_count,
        "success_rate": (llm_client.request_count - llm_client.error_count) / max(llm_client.request_count, 1),
        "model_usage": llm_client.model_health,
        "standardized_routing_active": True
    }