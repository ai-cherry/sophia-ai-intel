"""
Base LLM Client Interface for Sophia AI
======================================

Abstract base classes and common utilities for LLM provider integration.

This module defines the core interfaces that all LLM providers must implement,
ensuring consistent behavior across different models and services.

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    PORTKEY = "portkey"
    GROQ = "groq"
    MISTRAL = "mistral"


class TaskType(str, Enum):
    """Task classification for routing decisions"""
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    CHAT = "chat"
    REASONING = "reasoning"


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    streaming: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None


@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    latency_ms: Optional[float] = None
    cost_estimate: Optional[float] = None


@dataclass
class LLMRequest:
    """Standardized LLM request format"""
    messages: List[Dict[str, str]]
    task_type: TaskType
    config: LLMConfig
    context: Optional[Dict[str, Any]] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response synchronously"""
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """Generate a streaming response"""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[str]:
        """Get available models for this provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible"""
        pass
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate estimated cost based on usage and model"""
        # This would be implemented with actual pricing data
        return 0.0
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for the specific provider"""
        # Default implementation - providers can override
        return messages


class LLMRouter(ABC):
    """Abstract base class for LLM routing logic"""
    
    @abstractmethod
    async def select_provider(self, request: LLMRequest) -> LLMProvider:
        """Select the best provider for a given request"""
        pass
    
    @abstractmethod
    async def route_request(self, request: LLMRequest) -> LLMResponse:
        """Route and execute the request with the selected provider"""
        pass
