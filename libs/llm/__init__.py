"""
Sophia AI LLM Interface
=======================

Unified interface for all LLM providers with smart routing, caching, and monitoring.

This module provides a single entry point for all LLM operations in the Sophia AI system.

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

from typing import List, Dict, Any, AsyncGenerator, Optional
import asyncio

from libs.llm.base import (
    LLMClient, 
    LLMRouter, 
    LLMConfig, 
    LLMRequest, 
    LLMResponse, 
    LLMProvider, 
    TaskType
)
from libs.llm.router import SmartRouter, router
from libs.llm.cache import LLMCache, cache
from libs.llm.openai_client import OpenAIClient, OpenAIConfig
from libs.llm.anthropic_client import AnthropicClient, AnthropicConfig


class SophiaLLM:
    """Main LLM interface for Sophia AI"""
    
    def __init__(self):
        self.router = router
        self.cache = cache
        self._initialized = False
    
    async def initialize(self):
        """Initialize the LLM system"""
        if not self._initialized:
            # Connect to cache
            await self.cache.connect()
            self._initialized = True
    
    async def generate(self, request: LLMRequest, use_cache: bool = True) -> LLMResponse:
        """Generate a response for a request"""
        if not self._initialized:
            await self.initialize()
        
        # Try cache first
        if use_cache:
            cached_response = await self.cache.get(request)
            if cached_response:
                return cached_response
        
        # Route through smart router
        response = await self.router.route_request(request)
        
        # Cache the response
        if use_cache and response.cost_estimate and response.cost_estimate > 0:
            await self.cache.set(request, response)
        
        return response
    
    async def generate_stream(self, request: LLMRequest, use_cache: bool = True) -> AsyncGenerator[LLMResponse, None]:
        """Generate a streaming response for a request"""
        if not self._initialized:
            await self.initialize()
        
        # For streaming, we don't cache the full response but can cache the final result
        # Route through smart router
        async for response in self.router.route_request(request):
            yield response
    
    async def get_provider_stats(self) -> Dict[str, Any]:
        """Get current provider statistics"""
        return self.router.get_provider_stats()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        return await self.cache.get_stats()
    
    async def clear_cache(self) -> bool:
        """Clear the response cache"""
        return await self.cache.clear()
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health_status = {}
        
        # Check router health
        healthy_providers = await self.router._get_healthy_providers()
        for provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            health_status[provider.value] = provider in healthy_providers
        
        # Check cache health
        health_status['cache'] = self.cache._connected
        
        return health_status


# Global instance
llm = SophiaLLM()


# Convenience functions
async def generate_response(
    messages: List[Dict[str, str]], 
    task_type: TaskType = TaskType.CHAT,
    provider: Optional[LLMProvider] = None,
    model: str = "gpt-4-turbo",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    streaming: bool = False,
    use_cache: bool = True
) -> LLMResponse:
    """Convenience function to generate a response"""
    
    config = LLMConfig(
        provider=provider or LLMProvider.OPENAI,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming
    )
    
    request = LLMRequest(
        messages=messages,
        task_type=task_type,
        config=config
    )
    
    if streaming:
        # For streaming, return the first response
        async for response in llm.generate_stream(request, use_cache):
            return response
    else:
        return await llm.generate(request, use_cache)


# Export main classes and functions
__all__ = [
    'SophiaLLM',
    'llm',
    'generate_response',
    'LLMClient',
    'LLMRouter',
    'LLMConfig',
    'LLMRequest',
    'LLMResponse',
    'LLMProvider',
    'TaskType',
    'OpenAIClient',
    'AnthropicClient',
    'SmartRouter'
]
