"""
Sophia AI - OpenRouter Client
Drop-in replacement for OpenAI client with multi-model support
"""

import os
import json
import httpx
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for each model"""
    id: str
    provider: str
    cost_per_million_tokens: float
    max_tokens: int
    supports_functions: bool = True
    supports_vision: bool = False

# Model configurations with OpenRouter model IDs
MODELS = {
    # OpenAI Models
    "gpt-4-turbo": ModelConfig(
        id="openai/gpt-4-turbo",
        provider="openai",
        cost_per_million_tokens=10.0,
        max_tokens=128000,
        supports_vision=True
    ),
    "gpt-4": ModelConfig(
        id="openai/gpt-4",
        provider="openai",
        cost_per_million_tokens=30.0,
        max_tokens=8192
    ),
    "gpt-3.5-turbo": ModelConfig(
        id="openai/gpt-3.5-turbo",
        provider="openai",
        cost_per_million_tokens=0.5,
        max_tokens=16384
    ),
    
    # Anthropic Models
    "claude-3-opus": ModelConfig(
        id="anthropic/claude-3-opus",
        provider="anthropic",
        cost_per_million_tokens=15.0,
        max_tokens=200000,
        supports_vision=True
    ),
    "claude-3-sonnet": ModelConfig(
        id="anthropic/claude-3-sonnet",
        provider="anthropic",
        cost_per_million_tokens=3.0,
        max_tokens=200000,
        supports_vision=True
    ),
    
    # DeepSeek Models
    "deepseek-chat": ModelConfig(
        id="deepseek/deepseek-chat",
        provider="deepseek",
        cost_per_million_tokens=0.14,
        max_tokens=32768
    ),
    "deepseek-coder": ModelConfig(
        id="deepseek/deepseek-coder",
        provider="deepseek",
        cost_per_million_tokens=0.14,
        max_tokens=16384
    ),
    
    # Mistral Models
    "mistral-medium": ModelConfig(
        id="mistral/mistral-medium",
        provider="mistral",
        cost_per_million_tokens=2.7,
        max_tokens=32768
    ),
    "mixtral-8x7b": ModelConfig(
        id="mistralai/mixtral-8x7b-instruct",
        provider="mistral",
        cost_per_million_tokens=0.7,
        max_tokens=32768
    ),
    
    # Meta Models
    "llama-3-70b": ModelConfig(
        id="meta-llama/llama-3-70b-instruct",
        provider="meta",
        cost_per_million_tokens=0.9,
        max_tokens=8192
    ),
    
    # Perplexity Models
    "perplexity-online": ModelConfig(
        id="perplexity/perplexity-online",
        provider="perplexity",
        cost_per_million_tokens=5.0,
        max_tokens=4096,
        supports_functions=False
    ),
    
    # Groq Models (Fast inference)
    "groq-mixtral": ModelConfig(
        id="groq/mixtral-8x7b",
        provider="groq",
        cost_per_million_tokens=0.27,
        max_tokens=32768
    )
}

class OpenRouterClient:
    """
    OpenRouter client with automatic model selection and fallback
    Drop-in replacement for OpenAI client
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "gpt-3.5-turbo",
        max_retries: int = 3
    ):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.default_model = default_model
        self.max_retries = max_retries
        
        if not self.api_key:
            raise ValueError("OpenRouter API key required")
        
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://sophia-intel.ai",
                "X-Title": "Sophia AI Intel"
            },
            timeout=60.0
        )
        
        # Track costs
        self.total_cost = 0.0
        self.request_count = 0
    
    def _select_model(self, 
                     messages: List[Dict], 
                     functions: Optional[List] = None,
                     prefer_cheap: bool = False) -> str:
        """Select optimal model based on request characteristics"""
        
        # Calculate approximate token count
        message_length = sum(len(m.get("content", "")) for m in messages)
        
        # Check if vision is needed
        needs_vision = any(
            isinstance(m.get("content"), list) and 
            any(c.get("type") == "image_url" for c in m.get("content", []))
            for m in messages
        )
        
        # Check if functions are needed
        needs_functions = functions is not None and len(functions) > 0
        
        # Filter compatible models
        compatible_models = []
        for name, config in MODELS.items():
            if needs_vision and not config.supports_vision:
                continue
            if needs_functions and not config.supports_functions:
                continue
            if message_length > config.max_tokens * 0.8:  # 80% safety margin
                continue
            compatible_models.append((name, config))
        
        if not compatible_models:
            # Fallback to most capable model
            return "claude-3-opus" if needs_vision else "gpt-4-turbo"
        
        # Sort by cost (cheapest first)
        compatible_models.sort(key=lambda x: x[1].cost_per_million_tokens)
        
        # Select based on preference
        if prefer_cheap or message_length < 1000:
            # For short messages or when cost is priority
            return compatible_models[0][0]
        else:
            # For complex tasks, use a more capable model
            # Select from top 50% by cost, then most expensive
            mid_point = len(compatible_models) // 2
            return compatible_models[mid_point:][-1][0]
    
    def chat_completions_create(self, **kwargs):
        """Compatible with OpenAI chat.completions.create()"""
        
        # Extract parameters
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self.default_model)
        functions = kwargs.get("functions")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        stream = kwargs.get("stream", False)
        
        # Auto-select model if needed
        if model in ["gpt-4", "gpt-3.5-turbo", "auto"]:
            model = self._select_model(
                messages, 
                functions,
                prefer_cheap=(model == "gpt-3.5-turbo")
            )
            logger.info(f"Selected model: {model}")
        
        # Convert to OpenRouter format
        model_config = MODELS.get(model, MODELS[self.default_model])
        openrouter_model = model_config.id
        
        # Build request
        request_data = {
            "model": openrouter_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, model_config.max_tokens),
            "stream": stream
        }
        
        if functions and model_config.supports_functions:
            request_data["functions"] = functions
            if "function_call" in kwargs:
                request_data["function_call"] = kwargs["function_call"]
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                response = self.client.post(
                    "/chat/completions",
                    json=request_data
                )
                response.raise_for_status()
                
                # Track costs
                result = response.json()
                if "usage" in result:
                    tokens = result["usage"].get("total_tokens", 0)
                    cost = (tokens / 1_000_000) * model_config.cost_per_million_tokens
                    self.total_cost += cost
                    self.request_count += 1
                    logger.debug(f"Request cost: ${cost:.4f} (Total: ${self.total_cost:.4f})")
                
                return OpenRouterResponse(result)
                
            except httpx.HTTPError as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                
                # Try fallback model on error
                if model != "gpt-3.5-turbo":
                    model = "gpt-3.5-turbo"
                    model_config = MODELS[model]
                    openrouter_model = model_config.id
                    request_data["model"] = openrouter_model
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost tracking summary"""
        return {
            "total_cost": self.total_cost,
            "request_count": self.request_count,
            "average_cost_per_request": self.total_cost / max(1, self.request_count)
        }
    
    # Compatibility properties/methods
    @property
    def chat(self):
        """OpenAI-style chat property"""
        return self
    
    @property
    def completions(self):
        """OpenAI-style completions property"""
        return self
    
    def create(self, **kwargs):
        """OpenAI-style create method"""
        return self.chat_completions_create(**kwargs)

class OpenRouterResponse:
    """Wrapper to make response compatible with OpenAI response format"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __getitem__(self, key):
        return self._data[key]
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def to_dict(self):
        return self._data
    
    @property
    def choices(self):
        """Ensure choices are accessible as property"""
        return [OpenRouterChoice(c) for c in self._data.get("choices", [])]

class OpenRouterChoice:
    """Wrapper for choice objects"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    @property
    def message(self):
        """Ensure message is accessible as property"""
        return OpenRouterMessage(self._data.get("message", {}))

class OpenRouterMessage:
    """Wrapper for message objects"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    @property
    def content(self):
        return self._data.get("content")
    
    @property
    def function_call(self):
        return self._data.get("function_call")

# Drop-in replacement function
def create_client(api_key: Optional[str] = None) -> OpenRouterClient:
    """
    Create OpenRouter client as drop-in replacement for OpenAI
    
    Usage:
        # Instead of:
        # from openai import OpenAI
        # client = OpenAI()
        
        # Use:
        from libs.openrouter import create_client
        client = create_client()
        
        # Then use exactly like OpenAI:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    return OpenRouterClient(api_key=api_key)

# For direct import compatibility
OpenAI = OpenRouterClient
