#!/usr/bin/env python3
"""
SOPHIA SUPREME AI ORCHESTRATOR
Production-ready, quality-first orchestrator with smart routing
Following best practices for OpenRouter, Perplexity, Anthropic integration
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, AsyncIterator
from enum import Enum
from dataclasses import dataclass
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from pathlib import Path
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys from environment only - no hardcoded defaults for security
API_KEYS = {
    "openrouter": os.getenv("OPENROUTER_API_KEY"),
    "perplexity": os.getenv("PERPLEXITY_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "tavily": os.getenv("TAVILY_API_KEY"),
    "serper": os.getenv("SERPER_API_KEY"),
    "brave": os.getenv("BRAVE_API_KEY"),
    "brightdata": os.getenv("BRIGHTDATA_API_KEY"),
    "exa": os.getenv("EXA_API_KEY"),
    "xai": os.getenv("XAI_API_KEY"),
    "agno": os.getenv("AGNO_API_KEY"),
    "apify": os.getenv("APIFY_API_TOKEN"),
}

class TaskType(Enum):
    """Task types for routing"""
    LIVE_RESEARCH = "live_research"  # Real-time web research with citations
    DEEP_ANALYSIS = "deep_analysis"  # Extended reasoning and synthesis
    CODE_SEARCH = "code_search"      # GitHub and code repository search
    QUICK_QA = "quick_qa"            # Speed-sensitive Q&A
    SYNTHESIS = "synthesis"          # Multi-source synthesis
    VALIDATION = "validation"        # Fact-checking and validation
    LOCAL_ANALYSIS = "local_analysis"  # Analyze local repository/files

class ModelClass(Enum):
    """Model classifications for task routing"""
    SONAR_DEEP = "sonar-deep-research"           # Perplexity deep research
    SONAR_PRO = "sonar-pro"                      # Perplexity pro search
    CLAUDE_SONNET = "anthropic/claude-3.5-sonnet"  # Via OpenRouter
    CLAUDE_OPUS = "anthropic/claude-3-opus"        # Via OpenRouter
    GPT4_TURBO = "openai/gpt-4-turbo"             # Via OpenRouter
    GPT4O = "openai/gpt-4o"                       # Via OpenRouter
    DEEPSEEK = "deepseek/deepseek-r1"             # Via OpenRouter
    GROK = "x-ai/grok-4"                          # xAI Grok via OpenRouter
    PERPLEXITY_SONAR = "perplexity/sonar-deep-research"  # Via OpenRouter

@dataclass
class RoutingDecision:
    """Routing decision with model and provider"""
    primary_model: str
    provider: str
    fallback_models: List[str]
    require_citations: bool
    enable_streaming: bool
    extended_thinking: bool
    max_latency_ms: int

class SmartRouter:
    """Quality-first smart router for model selection"""
    
    def __init__(self):
        # Task to model mapping (static rules)
        self.task_model_map = {
            TaskType.LIVE_RESEARCH: {
                "primary": ModelClass.SONAR_DEEP,
                "fallbacks": [ModelClass.SONAR_PRO, ModelClass.CLAUDE_SONNET],
                "require_citations": True,
                "max_latency_ms": 30000
            },
            TaskType.DEEP_ANALYSIS: {
                "primary": ModelClass.CLAUDE_OPUS,
                "fallbacks": [ModelClass.CLAUDE_SONNET, ModelClass.DEEPSEEK],
                "require_citations": False,
                "extended_thinking": True,
                "max_latency_ms": 60000
            },
            TaskType.QUICK_QA: {
                "primary": ModelClass.GPT4_TURBO,
                "fallbacks": [ModelClass.CLAUDE_SONNET],
                "require_citations": False,
                "max_latency_ms": 5000
            },
            TaskType.SYNTHESIS: {
                "primary": ModelClass.CLAUDE_SONNET,
                "fallbacks": [ModelClass.DEEPSEEK, ModelClass.GPT4_TURBO],
                "require_citations": True,
                "extended_thinking": True,
                "max_latency_ms": 45000
            }
        }
    
    def classify_task(self, query: str, context: Dict[str, Any]) -> TaskType:
        """Classify task based on query and context"""
        q_lower = query.lower()
        
        # Check for LOCAL repository queries FIRST - Sophia should control everything!
        if any(kw in q_lower for kw in ["this repository", "this repo", "local", "mcp server", "mcp layout", 
                                         "file structure", "directory", "our code", "this codebase", 
                                         "sophia", "outline", "structure of"]):
            return TaskType.LOCAL_ANALYSIS
        elif any(kw in q_lower for kw in ["latest", "recent", "news", "current", "today", "this week"]):
            return TaskType.LIVE_RESEARCH
        elif any(kw in q_lower for kw in ["analyze", "deep dive", "comprehensive", "detailed analysis"]):
            return TaskType.DEEP_ANALYSIS
        elif any(kw in q_lower for kw in ["code", "github", "repository", "implementation"]):
            return TaskType.CODE_SEARCH
        elif any(kw in q_lower for kw in ["synthesize", "combine", "integrate", "summarize sources"]):
            return TaskType.SYNTHESIS
        elif any(kw in q_lower for kw in ["verify", "fact check", "validate", "confirm"]):
            return TaskType.VALIDATION
        elif len(query.split()) < 10:  # Short queries likely need quick answers
            return TaskType.QUICK_QA
        else:
            return TaskType.LIVE_RESEARCH  # Default to research
    
    def route(self, query: str, context: Dict[str, Any] = {}) -> RoutingDecision:
        """Route query to optimal model"""
        task_type = self.classify_task(query, context)
        
        # Handle LOCAL_ANALYSIS specially - Sophia controls the repository!
        if task_type == TaskType.LOCAL_ANALYSIS:
            return RoutingDecision(
                primary_model="local_analysis",
                provider="local",
                fallback_models=[],
                require_citations=False,
                enable_streaming=False,
                extended_thinking=False,
                max_latency_ms=5000
            )
        
        config = self.task_model_map.get(task_type, self.task_model_map[TaskType.LIVE_RESEARCH])
        
        return RoutingDecision(
            primary_model=config["primary"].value,
            provider="perplexity" if "sonar" in config["primary"].value else "openrouter",
            fallback_models=[m.value for m in config.get("fallbacks", [])],
            require_citations=config.get("require_citations", False),
            enable_streaming=True,  # Always enable streaming for responsiveness
            extended_thinking=config.get("extended_thinking", False),
            max_latency_ms=config.get("max_latency_ms", 30000)
        )

class SophiaSupremeOrchestrator:
    """Production-ready orchestrator with quality-first approach"""
    
    def __init__(self):
        self.router = SmartRouter()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_perplexity_sonar(
        self, 
        query: str, 
        model: str = "sonar-deep-research",
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Call Perplexity Sonar for deep research with streaming"""
        headers = {
            "Authorization": f"Bearer {API_KEYS['perplexity']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": query}],
            "stream": stream,
            "reasoning_effort": "high",
            "return_citations": True
        }
        
        try:
            async with self.session.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if stream:
                    async for line in response.content:
                        if line:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith("data: "):
                                data = line_text[6:]
                                if data != "[DONE]":
                                    try:
                                        chunk = json.loads(data)
                                        if "choices" in chunk and chunk["choices"]:
                                            delta = chunk["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                yield delta["content"]
                                    except json.JSONDecodeError:
                                        continue
                else:
                    data = await response.json()
                    yield data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Perplexity error: {e}")
            yield f"Error calling Perplexity: {str(e)}"
    
    async def call_openrouter(
        self,
        query: str,
        model: str = "anthropic/claude-3.5-sonnet",
        provider_order: List[str] = ["Anthropic", "OpenAI"],
        stream: bool = True,
        extended_thinking: bool = False
    ) -> AsyncIterator[str]:
        """Call OpenRouter with quality-first provider controls"""
        headers = {
            "Authorization": f"Bearer {API_KEYS['openrouter']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sophia-ai.local",
            "X-Title": "Sophia Supreme Orchestrator"
        }
        
        # Provider configuration for quality control
        provider = {
            "order": provider_order,
            "allow_fallbacks": False,  # No fallback to lower quality
            "require_parameters": True  # Ensure features are supported
        }
        
        messages = [{"role": "user", "content": query}]
        
        # Add thinking budget for Anthropic models
        extra_params = {}
        if extended_thinking and "claude" in model.lower():
            extra_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 10000
            }
        
        payload = {
            "model": model,
            "messages": messages,
            "provider": provider,
            "stream": stream,
            "max_tokens": 4096,
            **extra_params
        }
        
        try:
            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if stream:
                    async for line in response.content:
                        if line:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith("data: "):
                                data = line_text[6:]
                                if data != "[DONE]":
                                    try:
                                        chunk = json.loads(data)
                                        if "choices" in chunk and chunk["choices"]:
                                            delta = chunk["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                yield delta["content"]
                                    except json.JSONDecodeError:
                                        continue
                else:
                    data = await response.json()
                    yield data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            yield f"Error calling OpenRouter: {str(e)}"
    
    async def call_serper(self, query: str) -> str:
        """Call Serper for Google search"""
        headers = {
            "X-API-KEY": API_KEYS["serper"],
            "Content-Type": "application/json"
        }
        
        payload = {"q": query, "num": 5}
        
        try:
            async with self.session.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                if "organic" in data:
                    results = []
                    for item in data["organic"][:5]:
                        results.append(f"• {item['title']}\n  {item['snippet']}\n  {item['link']}")
                    return "\n\n".join(results)
                return "No results found"
        except Exception as e:
            logger.error(f"Serper error: {e}")
            return f"Error with Serper: {str(e)}"
    
    async def call_brave(self, query: str) -> str:
        """Call Brave Search API"""
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": API_KEYS["brave"]
        }
        
        params = {"q": query, "count": 5}
        
        try:
            async with self.session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            ) as response:
                data = await response.json()
                if "web" in data and "results" in data["web"]:
                    results = []
                    for item in data["web"]["results"][:5]:
                        results.append(f"• {item.get('title', 'No title')}\n  {item.get('description', '')}\n  {item.get('url', '')}")
                    return "\n\n".join(results)
                return "No results found"
        except Exception as e:
            logger.error(f"Brave error: {e}")
            return f"Error with Brave: {str(e)}"
    
    async def call_tavily(self, query: str) -> str:
        """Call Tavily for AI-optimized search"""
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "api_key": API_KEYS["tavily"],
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }
        
        try:
            async with self.session.post(
                "https://api.tavily.com/search",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                if data.get("answer"):
                    result = data["answer"] + "\n\nSources:\n"
                    if data.get("results"):
                        for item in data["results"][:5]:
                            result += f"• {item.get('title', '')}: {item.get('url', '')}\n"
                    return result
                return "No results found"
        except Exception as e:
            logger.error(f"Tavily error: {e}")
            return f"Error with Tavily: {str(e)}"
    
    async def analyze_local_repository(self, query: str) -> str:
        """Analyze local repository structure and files"""
        try:
            # Get repository root (assuming we're in services/)
            repo_root = Path(__file__).parent.parent
            
            # Common patterns to search for based on query
            if "mcp" in query.lower() or "server" in query.lower():
                # Find MCP-related files
                mcp_services = list(repo_root.glob("services/mcp-*"))
                mcp_modules = list(repo_root.glob("mcp/*/"))
                
                result = "## MCP Server Layout Analysis\n\n"
                
                if mcp_services:
                    result += "### Core MCP Services (/services/mcp-*)\n"
                    for service in sorted(mcp_services):
                        if service.is_dir():
                            app_file = service / "app.py"
                            if app_file.exists():
                                result += f"- **{service.name}**: {app_file}\n"
                
                if mcp_modules:
                    result += "\n### Domain MCP Modules (/mcp/*)\n"
                    for module in sorted(mcp_modules):
                        result += f"- **{module.name}**: {module}\n"
                
                # Add port configuration if found
                env_file = repo_root / ".env"
                if env_file.exists():
                    result += "\n### MCP Port Configuration\n"
                    with open(env_file, 'r') as f:
                        for line in f:
                            if "MCP_" in line and "PORT" in line:
                                result += f"- {line.strip()}\n"
                
                return result if result else "No MCP servers found in repository"
                
            elif "structure" in query.lower() or "repository" in query.lower():
                # General repository structure
                result = "## Repository Structure\n\n"
                
                # Key directories
                dirs_to_check = ["services", "apps", "mcp", "scripts", "libs", "backend"]
                for dir_name in dirs_to_check:
                    dir_path = repo_root / dir_name
                    if dir_path.exists():
                        items = list(dir_path.iterdir())
                        result += f"### /{dir_name}/ ({len(items)} items)\n"
                        for item in sorted(items)[:5]:  # Show first 5
                            result += f"- {item.name}\n"
                        if len(items) > 5:
                            result += f"- ... and {len(items)-5} more\n"
                        result += "\n"
                
                return result
                
            else:
                # Search for specific files
                search_pattern = f"**/*{query.split()[-1]}*" if query.split() else "**/*.py"
                files = list(repo_root.glob(search_pattern))[:10]
                
                if files:
                    result = f"## Files matching '{query}':\n"
                    for file in files:
                        relative_path = file.relative_to(repo_root)
                        result += f"- {relative_path}\n"
                    return result
                else:
                    return f"No files found matching '{query}'"
                    
        except Exception as e:
            logger.error(f"Local analysis error: {e}")
            return f"Error analyzing repository: {str(e)}"
    
    async def call_exa(self, query: str) -> str:
        """Call Exa AI for semantic search"""
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": API_KEYS["exa"]
        }
        
        payload = {
            "query": query,
            "numResults": 5,
            "useAutoprompt": True,
            "type": "neural"
        }
        
        try:
            async with self.session.post(
                "https://api.exa.ai/search",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                if "results" in data:
                    results = []
                    for item in data["results"][:5]:
                        results.append(f"• {item.get('title', '')}\n  {item.get('url', '')}\n  Score: {item.get('score', 0):.2f}")
                    return "\n\n".join(results)
                return "No results found"
        except Exception as e:
            logger.error(f"Exa error: {e}")
            return f"Error with Exa: {str(e)}"
    
    async def orchestrate(
        self,
        query: str,
        session_id: str = "default",
        context: Dict[str, Any] = {}
    ) -> AsyncIterator[str]:
        """Main orchestration with quality-first routing"""
        
        # Get routing decision
        routing = self.router.route(query, context)
        logger.info(f"Routing decision: {routing.primary_model} via {routing.provider}")
        
        # Track metadata
        yield f"[METADATA: Model={routing.primary_model}, Provider={routing.provider}]\n\n"
        
        try:
            # Route based on provider
            if routing.provider == "local":
                # Handle LOCAL repository analysis - Sophia has FULL control!
                result = await self.analyze_local_repository(query)
                yield result
                
            elif routing.provider == "perplexity":
                # Use Perplexity for research
                async for chunk in self.call_perplexity_sonar(
                    query, 
                    model=routing.primary_model,
                    stream=routing.enable_streaming
                ):
                    yield chunk
                    
            elif routing.provider == "openrouter":
                # Use OpenRouter for reasoning models
                async for chunk in self.call_openrouter(
                    query,
                    model=routing.primary_model,
                    stream=routing.enable_streaming,
                    extended_thinking=routing.extended_thinking
                ):
                    yield chunk
                    
            else:
                # Parallel search across multiple providers for best results
                search_tasks = [
                    self.call_serper(query),
                    self.call_brave(query),
                    self.call_tavily(query),
                    self.call_exa(query)
                ]
                
                # Get results from all search providers
                search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                # Combine and yield results
                combined = []
                providers_used = []
                
                for i, result in enumerate(search_results):
                    if isinstance(result, str) and "No results" not in result and "Error" not in result:
                        provider_name = ["Serper", "Brave", "Tavily", "Exa"][i]
                        providers_used.append(provider_name)
                        combined.append(f"**{provider_name} Results:**\n{result}")
                
                if combined:
                    yield f"[Search Providers: {', '.join(providers_used)}]\n\n"
                    yield "\n\n---\n\n".join(combined)
                else:
                    yield "No search results available"
                
        except Exception as e:
            logger.error(f"Primary model failed: {e}")
            
            # Try fallbacks
            for fallback_model in routing.fallback_models:
                try:
                    logger.info(f"Trying fallback: {fallback_model}")
                    if "sonar" in fallback_model:
                        async for chunk in self.call_perplexity_sonar(query, model=fallback_model):
                            yield chunk
                        break
                    else:
                        async for chunk in self.call_openrouter(query, model=fallback_model):
                            yield chunk
                        break
                except Exception as fallback_error:
                    logger.error(f"Fallback {fallback_model} failed: {fallback_error}")
                    continue

# FastAPI Application
app = FastAPI(title="Sophia Supreme Orchestrator")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    context: Dict[str, Any] = {}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Streaming chat endpoint"""
    async def generate():
        async with SophiaSupremeOrchestrator() as orchestrator:
            async for chunk in orchestrator.orchestrate(
                request.message,
                request.session_id,
                request.context
            ):
                yield chunk
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "providers": {
            "perplexity": bool(API_KEYS["perplexity"]),
            "openrouter": bool(API_KEYS["openrouter"]),
            "anthropic": bool(API_KEYS["anthropic"]),
            "serper": bool(API_KEYS["serper"]),
            "exa": bool(API_KEYS["exa"]),
            "xai": bool(API_KEYS["xai"]),
        },
        "models": [m.value for m in ModelClass],
        "tasks": [t.value for t in TaskType]
    }

@app.get("/models")
def list_models():
    """List available models and routing"""
    return {
        "models": {
            "research": ["sonar-deep-research", "sonar-pro"],
            "reasoning": ["claude-3.5-sonnet", "claude-3-opus", "gpt-4-turbo"],
            "synthesis": ["claude-3.5-sonnet", "deepseek-r1"],
            "speed": ["gpt-4-turbo", "claude-3.5-sonnet"]
        },
        "routing_rules": {
            "live_research": "Perplexity Sonar Deep",
            "deep_analysis": "Claude Opus with extended thinking",
            "quick_qa": "GPT-4 Turbo via OpenRouter",
            "synthesis": "Claude Sonnet with citations"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500, log_level="info")