"""
OpenAI LLM Client for Sophia AI
===============================

Production-ready OpenAI client with streaming, cost tracking, and error handling.

Supports:
- GPT-4, GPT-4 Turbo, GPT-3.5 Turbo models
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
import openai
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from libs.llm.base import LLMClient, LLMConfig, LLMRequest, LLMResponse, TaskType


@dataclass
class OpenAIConfig(LLMConfig):
    """OpenAI-specific configuration"""
    organization: Optional[str] = None
    project: Optional[str] = None


class OpenAIClient(LLMClient):
    """OpenAI LLM client implementation"""
    
    # Pricing data (per 1M tokens) - updated 2024
    PRICING = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
        "gpt-4-0125-preview": {"input": 10.00, "output": 30.00},
        "gpt-4-1106-preview": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-3.5-turbo-0125": {"input": 0.50, "output": 1.50},
        "gpt-3.5-turbo-1106": {"input": 0.50, "output": 1.50},
    }
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config)
        self.config: OpenAIConfig = config
        
        # Initialize OpenAI client
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=config.organization,
            project=config.project,
            base_url=config.base_url,
            timeout=config.timeout
        )
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response synchronously"""
        start_time = time.time()
        
        try:
            # Format messages for OpenAI
            formatted_messages = self._format_messages(request.messages)
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=request.config.model,
                messages=formatted_messages,
                temperature=request.config.temperature,
                max_tokens=request.config.max_tokens,
                stream=False
            )
            
            # Calculate timing
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract usage and calculate cost
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            cost_estimate = self._calculate_cost(usage, request.config.model)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=request.config.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
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
            raise Exception(f"OpenAI generation failed: {str(e)}")
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """Generate a streaming response"""
        start_time = time.time()
        total_content = ""
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            # Format messages for OpenAI
            formatted_messages = self._format_messages(request.messages)
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(
                model=request.config.model,
                messages=formatted_messages,
                temperature=request.config.temperature,
                max_tokens=request.config.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    total_content += content
                    
                    # Yield partial response
                    yield LLMResponse(
                        content=content,
                        provider="openai",
                        model=request.config.model,
                        usage=None,  # Usage not available in streaming
                        finish_reason=None,
                        latency_ms=(time.time() - start_time) * 1000,
                        cost_estimate=0.0  # Cost calculated at the end
                    )
            
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
                provider="openai",
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
            raise Exception(f"OpenAI streaming generation failed: {str(e)}")
    
    async def get_models(self) -> List[str]:
        """Get available OpenAI models"""
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data if model.id.startswith(("gpt-", "text-"))]
        except Exception as e:
            # Return default models if API call fails
            return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    
    async def health_check(self) -> bool:
        """Check if OpenAI is healthy and accessible"""
        try:
            # Simple model list call to verify connectivity
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate estimated cost based on usage and model"""
        if model not in self.PRICING:
            # Try to find a matching base model
            base_model = next((m for m in self.PRICING.keys() if model.startswith(m)), "gpt-3.5-turbo")
            pricing = self.PRICING[base_model]
        else:
            pricing = self.PRICING[model]
        
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API"""
        # OpenAI expects role and content
        formatted = []
        for msg in messages:
            if "role" in msg and "content" in msg:
                formatted.append({"role": msg["role"], "content": msg["content"]})
            elif "user" in msg:
                formatted.append({"role": "user", "content": msg["user"]})
            elif "assistant" in msg:
                formatted.append({"role": "assistant", "content": msg["assistant"]})
            elif "system" in msg:
                formatted.append({"role": "system", "content": msg["system"]})
        
        return formatted
    
    async def _retry_request(self, request: LLMRequest, attempt: int, max_retries: int = 3) -> LLMResponse:
        """Retry a failed request with exponential backoff"""
        if attempt > max_retries:
            raise Exception("Max retries exceeded for OpenAI request")
        
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
            raise Exception("Max retries exceeded for OpenAI streaming request")
        
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
