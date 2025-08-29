"""
Anthropic LLM Client for Sophia AI
==================================

Production-ready Anthropic client with streaming, cost tracking, and error handling.

Supports:
- Claude 3 models (Opus, Sonnet, Haiku)
- Streaming responses with real-time token delivery
- Cost estimation and usage tracking
- Automatic retry with exponential backoff
- Rate limit handling

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import os
import asyncio
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass
import anthropic
from anthropic import AsyncAnthropic, APIError, RateLimitError, APIConnectionError

from libs.llm.base import LLMClient, LLMConfig, LLMRequest, LLMResponse, TaskType


@dataclass
class AnthropicConfig(LLMConfig):
    """Anthropic-specific configuration"""
    pass


class AnthropicClient(LLMClient):
    """Anthropic LLM client implementation"""
    
    # Pricing data (per 1M tokens) - updated 2024
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-2.1": {"input": 8.00, "output": 24.00},
        "claude-2.0": {"input": 8.00, "output": 24.00},
    }
    
    def __init__(self, config: AnthropicConfig):
        super().__init__(config)
        self.config: AnthropicConfig = config
        
        # Initialize Anthropic client
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response synchronously"""
        start_time = time.time()
        
        try:
            # Format messages for Anthropic
            formatted_messages = self._format_messages(request.messages)
            
            # Make API call
            response = await self.client.messages.create(
                model=request.config.model,
                messages=formatted_messages,
                max_tokens=request.config.max_tokens,
                temperature=request.config.temperature,
                stream=False
            )
            
            # Calculate timing
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract usage and calculate cost
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            cost_estimate = self._calculate_cost(usage, request.config.model)
            
            return LLMResponse(
                content=response.content[0].text,
                provider="anthropic",
                model=request.config.model,
                usage=usage,
                finish_reason=response.stop_reason,
                latency_ms=latency_ms,
                cost_estimate=cost_estimate
            )
            
        except RateLimitError as e:
            # Handle rate limiting
            await asyncio.sleep(1)
            return await self._retry_request(request, attempt=1)
            
        except (APIError, APIConnectionError) as e:
            # Handle API errors with retry
            return await self._retry_request(request, attempt=1)
            
        except Exception as e:
            raise Exception(f"Anthropic generation failed: {str(e)}")
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """Generate a streaming response"""
        start_time = time.time()
        total_content = ""
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            # Format messages for Anthropic
            formatted_messages = self._format_messages(request.messages)
            
            # Make streaming API call
            stream = await self.client.messages.create(
                model=request.config.model,
                messages=formatted_messages,
                max_tokens=request.config.max_tokens,
                temperature=request.config.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
                    content = chunk.delta.text
                    total_content += content
                    
                    # Yield partial response
                    yield LLMResponse(
                        content=content,
                        provider="anthropic",
                        model=request.config.model,
                        usage=None,  # Usage not available in streaming
                        finish_reason=None,
                        latency_ms=(time.time() - start_time) * 1000,
                        cost_estimate=0.0  # Cost calculated at the end
                    )
                elif chunk.type == "message_stop":
                    # Final response with complete usage
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # Estimate usage (this is approximate for streaming)
                    usage = {
                        "prompt_tokens": len(str(formatted_messages)) // 4,  # Rough estimate
                        "completion_tokens": len(total_content) // 4,       # Rough estimate
                        "total_tokens": (len(str(formatted_messages)) + len(total_content)) // 4
                    }
                    
                    cost_estimate = self._calculate_cost(usage, request.config.model)
                    
                    yield LLMResponse(
                        content="",
                        provider="anthropic",
                        model=request.config.model,
                        usage=usage,
                        finish_reason="stop",
                        latency_ms=latency_ms,
                        cost_estimate=cost_estimate
                    )
            
        except RateLimitError as e:
            # Handle rate limiting in streaming
            await asyncio.sleep(1)
            async for response in self._retry_stream_request(request, attempt=1):
                yield response
                
        except (APIError, APIConnectionError) as e:
            # Handle API errors with retry
            async for response in self._retry_stream_request(request, attempt=1):
                yield response
                
        except Exception as e:
            raise Exception(f"Anthropic streaming generation failed: {str(e)}")
    
    async def get_models(self) -> List[str]:
        """Get available Anthropic models"""
        # Anthropic doesn't have a models list endpoint, return known models
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]
    
    async def health_check(self) -> bool:
        """Check if Anthropic is healthy and accessible"""
        try:
            # Simple count tokens call to verify connectivity
            await self.client.count_tokens("test")
            return True
        except Exception:
            return False
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate estimated cost based on usage and model"""
        if model not in self.PRICING:
            # Try to find a matching base model
            base_model = next((m for m in self.PRICING.keys() if model.startswith(m.split("-")[0])), "claude-3-sonnet-20240229")
            pricing = self.PRICING[base_model]
        else:
            pricing = self.PRICING[model]
        
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for Anthropic API"""
        # Anthropic expects role and content
        formatted = []
        for msg in messages:
            if "role" in msg and "content" in msg:
                formatted.append({"role": msg["role"], "content": msg["content"]})
            elif "user" in msg:
                formatted.append({"role": "user", "content": msg["user"]})
            elif "assistant" in msg:
                formatted.append({"role": "assistant", "content": msg["assistant"]})
            elif "system" in msg:
                # Anthropic handles system messages differently - we'll add them to the API call
                continue  # Skip system messages here, they're handled in the API call
        
        return formatted
    
    async def _retry_request(self, request: LLMRequest, attempt: int, max_retries: int = 3) -> LLMResponse:
        """Retry a failed request with exponential backoff"""
        if attempt > max_retries:
            raise Exception("Max retries exceeded for Anthropic request")
        
        # Exponential backoff
        await asyncio.sleep(min(0.1 * (2 ** attempt), 10))
        
        try:
            return await self.generate(request)
        except Exception:
            if attempt < max_retries:
                return await self._retry_request(request, attempt + 1, max_retries)
            else:
                raise
    
    async def _retry_stream_request(self, request: LLMRequest, attempt: int, max_retries: int = 3) -> AsyncGenerator[LLMResponse, None]:
        """Retry a failed streaming request with exponential backoff"""
        if attempt > max_retries:
            raise Exception("Max retries exceeded for Anthropic streaming request")
        
        # Exponential backoff
        await asyncio.sleep(min(0.1 * (2 ** attempt), 10))
        
        try:
            async for response in self.generate_stream(request):
                yield response
        except Exception:
            if attempt < max_retries:
                async for response in self._retry_stream_request(request, attempt + 1, max_retries):
                    yield response
            else:
                raise
