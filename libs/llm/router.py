"""
LLM Router for Sophia AI
========================

Intelligent routing system that selects the best LLM provider based on:
- Task type and requirements
- Model quality and capabilities
- Latency and performance
- Cost optimization
- Provider health and availability

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import os
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from libs.llm.base import LLMRouter, LLMRequest, LLMResponse, LLMProvider, TaskType
from libs.llm.openai_client import OpenAIClient, OpenAIConfig
from libs.llm.anthropic_client import AnthropicClient, AnthropicConfig


@dataclass
class ProviderStats:
    """Statistics for provider performance tracking"""
    latency_avg: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    total_requests: int = 0
    last_error_time: Optional[float] = None


@dataclass
class RoutingConfig:
    """Configuration for routing decisions"""
    # Provider priorities by task type (higher = better)
    provider_priorities: Dict[TaskType, Dict[LLMProvider, int]] = field(default_factory=lambda: {
        TaskType.CODING: {LLMProvider.OPENAI: 3, LLMProvider.ANTHROPIC: 2},
        TaskType.RESEARCH: {LLMProvider.ANTHROPIC: 3, LLMProvider.OPENAI: 2},
        TaskType.ANALYSIS: {LLMProvider.OPENAI: 3, LLMProvider.ANTHROPIC: 2},
        TaskType.CREATIVE: {LLMProvider.ANTHROPIC: 3, LLMProvider.OPENAI: 2},
        TaskType.CHAT: {LLMProvider.OPENAI: 2, LLMProvider.ANTHROPIC: 2},
        TaskType.REASONING: {LLMProvider.ANTHROPIC: 3, LLMProvider.OPENAI: 2},
    })
    
    # Cost thresholds (USD)
    max_cost_threshold: float = 0.10  # Max cost per request
    
    # Latency thresholds (ms)
    max_latency_threshold: float = 5000.0  # Max acceptable latency
    
    # Fallback providers
    fallback_providers: List[LLMProvider] = field(default_factory=lambda: [
        LLMProvider.OPENAI, LLMProvider.ANTHROPIC
    ])


class SmartRouter(LLMRouter):
    """Intelligent LLM routing system"""
    
    def __init__(self, config: RoutingConfig = None):
        self.config = config or RoutingConfig()
        self.provider_stats: Dict[LLMProvider, ProviderStats] = {}
        self._initialize_providers()
        self._load_provider_configs()
    
    def _initialize_providers(self):
        """Initialize all supported providers"""
        for provider in LLMProvider:
            self.provider_stats[provider] = ProviderStats()
    
    def _load_provider_configs(self):
        """Load provider configurations from environment"""
        # OpenAI configuration
        self.openai_config = OpenAIConfig(
            provider=LLMProvider.OPENAI,
            model=os.getenv("LLM_OPENAI_MODEL", "gpt-4-turbo"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_OPENAI_MAX_TOKENS", "2048"))
        )
        
        # Anthropic configuration
        self.anthropic_config = AnthropicConfig(
            provider=LLMProvider.ANTHROPIC,
            model=os.getenv("LLM_ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=float(os.getenv("LLM_ANTHROPIC_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_ANTHROPIC_MAX_TOKENS", "2048"))
        )
    
    async def select_provider(self, request: LLMRequest) -> LLMProvider:
        """Select the best provider for a given request"""
        
        # 1. Check user override
        if hasattr(request.config, 'provider') and request.config.provider:
            return request.config.provider
        
        # 2. Get provider priorities for task type
        priorities = self.config.provider_priorities.get(request.task_type, {})
        
        # 3. Filter by health and performance
        healthy_providers = await self._get_healthy_providers()
        
        # 4. Score providers based on multiple factors
        provider_scores = {}
        
        for provider in healthy_providers:
            if provider not in priorities:
                continue
            
            # Base priority score
            priority_score = priorities.get(provider, 0)
            
            # Performance score (latency and success rate)
            stats = self.provider_stats.get(provider, ProviderStats())
            performance_score = stats.success_rate * (1.0 / max(stats.latency_avg, 1.0))
            
            # Cost consideration (if context provides cost info)
            cost_score = 1.0  # Default - can be enhanced with cost estimation
            
            # Combine scores
            provider_scores[provider] = priority_score * performance_score * cost_score
        
        # 5. Select highest scoring provider
        if provider_scores:
            return max(provider_scores.items(), key=lambda x: x[1])[0]
        
        # 6. Fallback to default providers
        for provider in self.config.fallback_providers:
            if provider in healthy_providers:
                return provider
        
        # 7. Last resort - first available
        return next(iter(healthy_providers)) if healthy_providers else LLMProvider.OPENAI
    
    async def route_request(self, request: LLMRequest) -> LLMResponse:
        """Route and execute the request with the selected provider"""
        start_time = time.time()
        
        # Select provider
        provider = await self.select_provider(request)
        
        # Initialize client
        client = await self._get_client(provider)
        if not client:
            raise Exception(f"No client available for provider: {provider}")
        
        try:
            # Execute request
            if request.config.streaming:
                # For streaming, return the first response from stream
                async for response in client.generate_stream(request):
                    if response.content:  # Return first content chunk
                        return response
                # If no content chunks, return final response
                async for response in client.generate_stream(request):
                    pass
                return response
            else:
                response = await client.generate(request)
                
                # Update provider stats
                await self._update_provider_stats(provider, True, response.latency_ms or 0)
                
                return response
                
        except Exception as e:
            # Update provider stats with error
            await self._update_provider_stats(provider, False, time.time() - start_time)
            
            # Try fallback provider
            return await self._try_fallback_provider(request, provider, str(e))
    
    async def _get_healthy_providers(self) -> List[LLMProvider]:
        """Get list of currently healthy providers"""
        healthy_providers = []
        
        # Check OpenAI health
        try:
            openai_client = OpenAIClient(self.openai_config)
            if await openai_client.health_check():
                healthy_providers.append(LLMProvider.OPENAI)
        except Exception:
            pass
        
        # Check Anthropic health
        try:
            anthropic_client = AnthropicClient(self.anthropic_config)
            if await anthropic_client.health_check():
                healthy_providers.append(LLMProvider.ANTHROPIC)
        except Exception:
            pass
        
        return healthy_providers
    
    async def _get_client(self, provider: LLMProvider):
        """Get client for specified provider"""
        if provider == LLMProvider.OPENAI:
            return OpenAIClient(self.openai_config)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(self.anthropic_config)
        else:
            # For other providers, you would add their clients here
            return None
    
    async def _update_provider_stats(self, provider: LLMProvider, success: bool, latency: float):
        """Update provider statistics"""
        if provider not in self.provider_stats:
            self.provider_stats[provider] = ProviderStats()
        
        stats = self.provider_stats[provider]
        stats.total_requests += 1
        
        if success:
            # Update latency average
            if stats.latency_avg == 0:
                stats.latency_avg = latency
            else:
                stats.latency_avg = (stats.latency_avg * 0.9) + (latency * 0.1)
        else:
            stats.error_count += 1
            stats.last_error_time = time.time()
        
        # Update success rate
        stats.success_rate = (stats.total_requests - stats.error_count) / stats.total_requests
    
    async def _try_fallback_provider(self, request: LLMRequest, failed_provider: LLMProvider, error: str) -> LLMResponse:
        """Try fallback providers when primary fails"""
        fallback_providers = [p for p in self.config.fallback_providers if p != failed_provider]
        
        for provider in fallback_providers:
            try:
                client = await self._get_client(provider)
                if client:
                    if request.config.streaming:
                        async for response in client.generate_stream(request):
                            if response.content:
                                return response
                    else:
                        return await client.generate(request)
            except Exception:
                continue  # Try next fallback provider
        
        # If all fallbacks fail, re-raise original error
        raise Exception(f"All providers failed. Original error: {error}")
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get current provider statistics"""
        stats = {}
        for provider, provider_stats in self.provider_stats.items():
            stats[provider.value] = {
                "latency_avg": provider_stats.latency_avg,
                "success_rate": provider_stats.success_rate,
                "error_count": provider_stats.error_count,
                "total_requests": provider_stats.total_requests,
                "last_error_time": provider_stats.last_error_time
            }
        return stats


# Singleton instance for easy access
router = SmartRouter()
