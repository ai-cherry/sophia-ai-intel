#!/usr/bin/env python3
"""
Sophia Dynamic API Router
========================

Revolutionary API routing system that intelligently selects and orchestrates
multiple premium APIs based on natural language requests and context.

Key Features:
- Intelligent API selection based on request semantics
- Dynamic fallback chains for reliability
- Contextual routing with cost optimization
- Real-time performance monitoring
- Multi-provider redundancy

Supported APIs:
- Perplexity (AI-powered search and reasoning)
- Tavily (Advanced research and answer generation)
- Serper (Google search results with structured data)
- Exa (Semantic search and knowledge extraction)
- Apify (Large-scale web scraping)
- ZenRows (Residential proxies, JS rendering)
- Brave (Privacy-focused search)
- BrightData (Enterprise web scraping)
- Hugging Face (ML models and embeddings)
- xAI/Grok (Advanced reasoning and analysis)

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Enumeration of available API providers"""
    PERPLEXITY = "perplexity"
    TAVILY = "tavily" 
    SERPER = "serper"
    EXA = "exa"
    APIFY = "apify"
    ZENROWS = "zenrows"
    BRAVE = "brave"
    BRIGHTDATA = "brightdata"
    HUGGINGFACE = "huggingface"
    XAI_GROK = "xai_grok"
    NEWSDATA = "newsdata"


class RequestType(Enum):
    """Types of requests the router can handle"""
    RESEARCH = "research"
    WEB_SEARCH = "web_search"
    SEMANTIC_SEARCH = "semantic_search"
    WEB_SCRAPING = "web_scraping"
    NEWS_ANALYSIS = "news_analysis"
    CODE_ANALYSIS = "code_analysis"
    DATA_EXTRACTION = "data_extraction"
    AI_REASONING = "ai_reasoning"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"


@dataclass
class APIConfig:
    """Configuration for individual API providers"""
    provider: APIProvider
    api_key: str
    base_url: str
    rate_limit: int  # requests per minute
    cost_per_request: float  # in USD
    capabilities: List[RequestType]
    priority: int  # 1-10, higher is better
    is_available: bool = True
    last_used: Optional[datetime] = None
    success_rate: float = 1.0


@dataclass
class RouteRequest:
    """Request object for API routing"""
    query: str
    request_type: RequestType
    context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    budget_limit: Optional[float] = None
    max_providers: int = 3
    require_fallback: bool = True


@dataclass
class APIResponse:
    """Standardized response from any API provider"""
    provider: APIProvider
    success: bool
    data: Any
    response_time: float
    cost: float
    confidence: float  # 0.0-1.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class SophiaDynamicAPIRouter:
    """
    Sophia's Dynamic API Router - Intelligently routes requests to optimal APIs
    """
    
    def __init__(self):
        self.api_configs: Dict[APIProvider, APIConfig] = {}
        self.performance_metrics: Dict[APIProvider, Dict] = {}
        self.session = None
        self._initialize_api_configs()
        self._initialize_performance_tracking()
        
        # OpenAI client for intelligent routing decisions
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        logger.info("Sophia Dynamic API Router initialized with {} providers".format(
            len([c for c in self.api_configs.values() if c.is_available])
        ))

    def _initialize_api_configs(self):
        """Initialize API provider configurations"""
        configs = [
            APIConfig(
                provider=APIProvider.PERPLEXITY,
                api_key=os.getenv("PERPLEXITY_API_KEY", ""),
                base_url="https://api.perplexity.ai",
                rate_limit=60,
                cost_per_request=0.002,
                capabilities=[RequestType.RESEARCH, RequestType.AI_REASONING, RequestType.WEB_SEARCH],
                priority=9,
                is_available=bool(os.getenv("PERPLEXITY_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.TAVILY,
                api_key=os.getenv("TAVILY_API_KEY", ""),
                base_url="https://api.tavily.com",
                rate_limit=100,
                cost_per_request=0.001,
                capabilities=[RequestType.RESEARCH, RequestType.WEB_SEARCH, RequestType.NEWS_ANALYSIS],
                priority=8,
                is_available=bool(os.getenv("TAVILY_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.SERPER,
                api_key=os.getenv("SERPER_API_KEY", ""),
                base_url="https://google.serper.dev",
                rate_limit=200,
                cost_per_request=0.0005,
                capabilities=[RequestType.WEB_SEARCH, RequestType.MARKET_RESEARCH],
                priority=7,
                is_available=bool(os.getenv("SERPER_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.EXA,
                api_key=os.getenv("EXA_API_KEY", ""),
                base_url="https://api.exa.ai",
                rate_limit=150,
                cost_per_request=0.001,
                capabilities=[RequestType.SEMANTIC_SEARCH, RequestType.RESEARCH],
                priority=6,
                is_available=bool(os.getenv("EXA_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.APIFY,
                api_key=os.getenv("APIFY_API_TOKEN", ""),
                base_url="https://api.apify.com",
                rate_limit=50,
                cost_per_request=0.01,
                capabilities=[RequestType.WEB_SCRAPING, RequestType.DATA_EXTRACTION],
                priority=8,
                is_available=bool(os.getenv("APIFY_API_TOKEN"))
            ),
            APIConfig(
                provider=APIProvider.ZENROWS,
                api_key=os.getenv("ZENROWS_API_KEY", ""),
                base_url="https://api.zenrows.com",
                rate_limit=100,
                cost_per_request=0.005,
                capabilities=[RequestType.WEB_SCRAPING, RequestType.DATA_EXTRACTION],
                priority=7,
                is_available=bool(os.getenv("ZENROWS_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.BRAVE,
                api_key=os.getenv("BRAVE_API_KEY", ""),
                base_url="https://api.search.brave.com",
                rate_limit=500,
                cost_per_request=0.0003,
                capabilities=[RequestType.WEB_SEARCH, RequestType.NEWS_ANALYSIS],
                priority=6,
                is_available=bool(os.getenv("BRAVE_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.BRIGHTDATA,
                api_key=os.getenv("BRIGHTDATA_API_KEY", ""),
                base_url="https://api.brightdata.com",
                rate_limit=200,
                cost_per_request=0.02,
                capabilities=[RequestType.WEB_SCRAPING, RequestType.COMPETITIVE_ANALYSIS],
                priority=9,
                is_available=bool(os.getenv("BRIGHTDATA_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.HUGGINGFACE,
                api_key=os.getenv("HUGGINGFACE_API_TOKEN", ""),
                base_url="https://api-inference.huggingface.co",
                rate_limit=1000,
                cost_per_request=0.0001,
                capabilities=[RequestType.CODE_ANALYSIS, RequestType.AI_REASONING],
                priority=5,
                is_available=bool(os.getenv("HUGGINGFACE_API_TOKEN"))
            ),
            APIConfig(
                provider=APIProvider.XAI_GROK,
                api_key=os.getenv("XAI_API_KEY", ""),
                base_url="https://api.x.ai",
                rate_limit=60,
                cost_per_request=0.003,
                capabilities=[RequestType.AI_REASONING, RequestType.RESEARCH, RequestType.CODE_ANALYSIS],
                priority=9,
                is_available=bool(os.getenv("XAI_API_KEY"))
            ),
            APIConfig(
                provider=APIProvider.NEWSDATA,
                api_key=os.getenv("NEWSDATA_API_KEY", ""),
                base_url="https://newsdata.io/api",
                rate_limit=200,
                cost_per_request=0.0002,
                capabilities=[RequestType.NEWS_ANALYSIS, RequestType.MARKET_RESEARCH],
                priority=6,
                is_available=bool(os.getenv("NEWSDATA_API_KEY"))
            )
        ]
        
        for config in configs:
            self.api_configs[config.provider] = config
            if config.is_available:
                logger.info(f"✅ {config.provider.value} API configured and available")
            else:
                logger.warning(f"❌ {config.provider.value} API key not found - provider disabled")

    def _initialize_performance_tracking(self):
        """Initialize performance tracking for each provider"""
        for provider in self.api_configs:
            self.performance_metrics[provider] = {
                'total_requests': 0,
                'successful_requests': 0,
                'average_response_time': 0.0,
                'total_cost': 0.0,
                'last_24h_requests': 0,
                'error_count': 0,
                'last_error': None
            }

    async def analyze_request_intent(self, query: str, context: Dict[str, Any]) -> RequestType:
        """Use AI to analyze user intent and determine optimal request type"""
        try:
            system_prompt = """
            You are an expert at analyzing user queries and determining the best API approach.
            Analyze the query and return ONE of these request types:
            - research: Deep research requiring multiple sources and synthesis
            - web_search: Simple web search for current information
            - semantic_search: Finding conceptually related content
            - web_scraping: Extracting data from specific websites
            - news_analysis: Current news and trending information  
            - code_analysis: Programming and technical analysis
            - data_extraction: Structured data extraction
            - ai_reasoning: Complex reasoning and problem solving
            - market_research: Business intelligence and market analysis
            - competitive_analysis: Competitor research and analysis
            
            Respond with just the request type, nothing else.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\nContext: {json.dumps(context)}"}
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Map response to RequestType enum
            for request_type in RequestType:
                if request_type.value in intent:
                    logger.info(f"🧠 Intent analysis: '{query}' → {request_type.value}")
                    return request_type
                    
            # Default fallback
            return RequestType.RESEARCH
            
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}, defaulting to research")
            return RequestType.RESEARCH

    def _score_provider_for_request(self, provider: APIConfig, request: RouteRequest) -> float:
        """Score a provider's suitability for a specific request"""
        if not provider.is_available or request.request_type not in provider.capabilities:
            return 0.0
        
        score = 0.0
        
        # Base capability score
        score += provider.priority * 10
        
        # Success rate bonus
        score += provider.success_rate * 20
        
        # Cost efficiency (lower cost = higher score)
        if provider.cost_per_request > 0:
            cost_score = max(0, 20 - (provider.cost_per_request * 1000))
            score += cost_score
        
        # Performance metrics
        metrics = self.performance_metrics.get(provider.provider, {})
        if metrics.get('total_requests', 0) > 0:
            success_rate = metrics['successful_requests'] / metrics['total_requests']
            score += success_rate * 15
            
            # Response time penalty
            avg_time = metrics.get('average_response_time', 0)
            if avg_time > 0:
                time_score = max(0, 10 - (avg_time / 2))
                score += time_score
        
        # Budget consideration
        if request.budget_limit and provider.cost_per_request > request.budget_limit:
            score *= 0.1  # Heavy penalty for over-budget providers
        
        return score

    async def select_optimal_providers(self, request: RouteRequest) -> List[APIProvider]:
        """Select the optimal providers for a given request"""
        provider_scores = []
        
        for provider_enum, config in self.api_configs.items():
            score = self._score_provider_for_request(config, request)
            if score > 0:
                provider_scores.append((provider_enum, score))
        
        # Sort by score (highest first)
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top providers up to max_providers limit
        selected = [p[0] for p in provider_scores[:request.max_providers]]
        
        logger.info(f"🎯 Selected providers for {request.request_type.value}: {[p.value for p in selected]}")
        return selected

    async def execute_perplexity_request(self, request: RouteRequest) -> APIResponse:
        """Execute request using Perplexity API"""
        start_time = time.time()
        config = self.api_configs[APIProvider.PERPLEXITY]
        
        try:
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {'role': 'user', 'content': request.query}
                ],
                'max_tokens': 800,
                'temperature': 0.2
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{config.base_url}/chat/completions", 
                                      headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        return APIResponse(
                            provider=APIProvider.PERPLEXITY,
                            success=True,
                            data=data,
                            response_time=response_time,
                            cost=config.cost_per_request,
                            confidence=0.9,
                            metadata={'citations': data.get('citations', [])}
                        )
                    else:
                        error_data = await response.text()
                        return self._create_error_response(APIProvider.PERPLEXITY, 
                                                         f"HTTP {response.status}: {error_data}",
                                                         time.time() - start_time)
                        
        except Exception as e:
            return self._create_error_response(APIProvider.PERPLEXITY, str(e), 
                                             time.time() - start_time)

    async def execute_tavily_request(self, request: RouteRequest) -> APIResponse:
        """Execute request using Tavily API"""
        start_time = time.time()
        config = self.api_configs[APIProvider.TAVILY]
        
        try:
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                'api_key': config.api_key,
                'query': request.query,
                'search_depth': request.context.get('depth', 'advanced'),
                'include_answer': True,
                'include_images': request.context.get('include_images', False),
                'include_raw_content': request.context.get('include_raw', False),
                'max_results': request.context.get('max_results', 10)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{config.base_url}/search", 
                                      headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        return APIResponse(
                            provider=APIProvider.TAVILY,
                            success=True,
                            data=data,
                            response_time=response_time,
                            cost=config.cost_per_request,
                            confidence=0.85,
                            metadata={'sources': len(data.get('results', []))}
                        )
                    else:
                        error_data = await response.text()
                        return self._create_error_response(APIProvider.TAVILY,
                                                         f"HTTP {response.status}: {error_data}",
                                                         time.time() - start_time)
                        
        except Exception as e:
            return self._create_error_response(APIProvider.TAVILY, str(e),
                                             time.time() - start_time)

    async def execute_serper_request(self, request: RouteRequest) -> APIResponse:
        """Execute request using Serper API"""
        start_time = time.time()
        config = self.api_configs[APIProvider.SERPER]
        
        try:
            headers = {
                'X-API-KEY': config.api_key,
                'Content-Type': 'application/json'
            }
            
            search_type = request.context.get('search_type', 'search')
            payload = {
                'q': request.query,
                'num': request.context.get('num_results', 10),
                'gl': request.context.get('location', 'us'),
                'hl': request.context.get('language', 'en')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{config.base_url}/{search_type}", 
                                      headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        return APIResponse(
                            provider=APIProvider.SERPER,
                            success=True,
                            data=data,
                            response_time=response_time,
                            cost=config.cost_per_request,
                            confidence=0.8,
                            metadata={'organic_results': len(data.get('organic', []))}
                        )
                    else:
                        error_data = await response.text()
                        return self._create_error_response(APIProvider.SERPER,
                                                         f"HTTP {response.status}: {error_data}",
                                                         time.time() - start_time)
                        
        except Exception as e:
            return self._create_error_response(APIProvider.SERPER, str(e),
                                             time.time() - start_time)

    def _create_error_response(self, provider: APIProvider, error: str, 
                             response_time: float) -> APIResponse:
        """Create standardized error response"""
        return APIResponse(
            provider=provider,
            success=False,
            data=None,
            response_time=response_time,
            cost=0.0,
            confidence=0.0,
            error=error
        )

    def _update_performance_metrics(self, provider: APIProvider, response: APIResponse):
        """Update performance metrics for a provider"""
        metrics = self.performance_metrics[provider]
        
        metrics['total_requests'] += 1
        if response.success:
            metrics['successful_requests'] += 1
        else:
            metrics['error_count'] += 1
            metrics['last_error'] = response.error
        
        # Update average response time
        total_requests = metrics['total_requests']
        current_avg = metrics['average_response_time']
        metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response.response_time) / total_requests
        )
        
        metrics['total_cost'] += response.cost
        
        # Update success rate in config
        if total_requests > 0:
            self.api_configs[provider].success_rate = (
                metrics['successful_requests'] / total_requests
            )

    async def execute_request(self, request: RouteRequest) -> List[APIResponse]:
        """Execute request using optimal providers with fallback chain"""
        # Analyze intent if not provided
        if not hasattr(request, 'request_type') or not request.request_type:
            request.request_type = await self.analyze_request_intent(
                request.query, request.context
            )
        
        # Select optimal providers
        selected_providers = await self.select_optimal_providers(request)
        
        if not selected_providers:
            logger.error("No suitable providers found for request")
            return []
        
        responses = []
        successful_responses = 0
        
        # Execute requests with selected providers
        for provider in selected_providers:
            try:
                if provider == APIProvider.PERPLEXITY:
                    response = await self.execute_perplexity_request(request)
                elif provider == APIProvider.TAVILY:
                    response = await self.execute_tavily_request(request)
                elif provider == APIProvider.SERPER:
                    response = await self.execute_serper_request(request)
                else:
                    # For other providers, create placeholder response
                    # TODO: Implement remaining provider integrations
                    response = APIResponse(
                        provider=provider,
                        success=False,
                        data=None,
                        response_time=0.0,
                        cost=0.0,
                        confidence=0.0,
                        error="Provider implementation pending"
                    )
                
                responses.append(response)
                self._update_performance_metrics(provider, response)
                
                if response.success:
                    successful_responses += 1
                    logger.info(f"✅ {provider.value} responded successfully in {response.response_time:.2f}s")
                else:
                    logger.warning(f"❌ {provider.value} failed: {response.error}")
                
                # If we have enough successful responses, we can stop
                if successful_responses >= 1 and not request.require_fallback:
                    break
                    
            except Exception as e:
                logger.error(f"Error executing request with {provider.value}: {e}")
                continue
        
        if successful_responses == 0:
            logger.error("All providers failed for the request")
        else:
            logger.info(f"🎉 Request completed with {successful_responses}/{len(responses)} successful responses")
        
        return responses

    async def get_provider_status(self) -> Dict[str, Dict]:
        """Get status and metrics for all providers"""
        status = {}
        
        for provider, config in self.api_configs.items():
            metrics = self.performance_metrics[provider]
            status[provider.value] = {
                'available': config.is_available,
                'priority': config.priority,
                'capabilities': [c.value for c in config.capabilities],
                'cost_per_request': config.cost_per_request,
                'success_rate': config.success_rate,
                'total_requests': metrics['total_requests'],
                'average_response_time': metrics['average_response_time'],
                'total_cost': metrics['total_cost'],
                'error_count': metrics['error_count']
            }
        
        return status

    async def optimize_routing(self):
        """Perform periodic optimization of routing decisions"""
        logger.info("🔧 Performing routing optimization...")
        
        # Disable poorly performing providers temporarily
        for provider, config in self.api_configs.items():
            if config.success_rate < 0.5 and self.performance_metrics[provider]['total_requests'] > 10:
                logger.warning(f"⚠️ Temporarily disabling {provider.value} due to poor performance")
                config.is_available = False
        
        # Re-enable providers after cooldown period
        # TODO: Implement cooldown logic
        
        logger.info("✅ Routing optimization completed")


async def main():
    """Demo of Sophia Dynamic API Router"""
    print("🚀 SOPHIA DYNAMIC API ROUTER - DEMO")
    print("="*50)
    
    router = SophiaDynamicAPIRouter()
    
    # Test different types of requests
    test_requests = [
        RouteRequest(
            query="What are the latest developments in AI agent frameworks?",
            request_type=RequestType.RESEARCH,
            context={"depth": "advanced", "max_results": 5},
            user_preferences={"prefer_recent": True},
            max_providers=2
        ),
        RouteRequest(
            query="Find information about AGNO framework",
            request_type=RequestType.WEB_SEARCH,
            context={"include_images": False},
            user_preferences={},
            max_providers=1
        ),
        RouteRequest(
            query="Analyze the competitive landscape for AI orchestration tools",
            request_type=RequestType.COMPETITIVE_ANALYSIS,
            context={"business_focus": True},
            user_preferences={"detailed_analysis": True},
            max_providers=3
        )
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📋 TEST REQUEST {i}")
        print(f"Query: {request.query}")
        print(f"Type: {request.request_type.value}")
        
        responses = await router.execute_request(request)
        
        print(f"Responses received: {len(responses)}")
        for response in responses:
            if response.success:
                print(f"  ✅ {response.provider.value}: {response.confidence:.2f} confidence, {response.response_time:.2f}s")
            else:
                print(f"  ❌ {response.provider.value}: {response.error}")
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Show provider status
    print("\n📊 PROVIDER STATUS")
    print("="*30)
    status = await router.get_provider_status()
    for provider, info in status.items():
        if info['available']:
            print(f"✅ {provider.upper()}: {info['total_requests']} requests, {info['success_rate']:.2f} success rate")
        else:
            print(f"❌ {provider.upper()}: Not available")


if __name__ == "__main__":
    asyncio.run(main())