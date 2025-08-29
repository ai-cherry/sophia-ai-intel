"""
LLM Response Caching for Sophia AI
==================================

Redis-based caching system for LLM responses to reduce costs and improve performance.

Features:
- Semantic cache key generation
- TTL-based expiration
- Cost tracking and savings
- Cache warming strategies

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import os
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from datetime import datetime, timedelta

from libs.llm.base import LLMResponse, LLMRequest


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    savings_usd: float = 0.0
    total_requests: int = 0


@dataclass
class CachedResponse:
    """Cached response with metadata"""
    response: LLMResponse
    created_at: datetime
    expires_at: datetime
    cost_saved: float = 0.0


class LLMCache:
    """LLM response caching system"""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self.stats = CacheStats()
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis"""
        if not self._connected:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                self._connected = True
            except Exception as e:
                print(f"Warning: Could not connect to Redis cache: {e}")
                self._connected = False
    
    async def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response for a request"""
        if not self._connected or not self.redis_client:
            return None
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Try to get from cache
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                # Cache hit
                self.stats.hits += 1
                self.stats.total_requests += 1
                
                # Deserialize cached response
                cached_dict = json.loads(cached_data)
                cached_response = CachedResponse(
                    response=LLMResponse(**cached_dict['response']),
                    created_at=datetime.fromisoformat(cached_dict['created_at']),
                    expires_at=datetime.fromisoformat(cached_dict['expires_at']),
                    cost_saved=cached_dict.get('cost_saved', 0.0)
                )
                
                # Update stats
                self.stats.savings_usd += cached_response.cost_saved
                
                return cached_response.response
            else:
                # Cache miss
                self.stats.misses += 1
                self.stats.total_requests += 1
                return None
                
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, request: LLMRequest, response: LLMResponse, ttl: int = None) -> bool:
        """Cache a response"""
        if not self._connected or not self.redis_client:
            return False
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Create cached response
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl or self.default_ttl)
            
            cached_response = CachedResponse(
                response=response,
                created_at=now,
                expires_at=expires_at,
                cost_saved=response.cost_estimate or 0.0
            )
            
            # Serialize and store
            cached_dict = {
                'response': asdict(response),
                'created_at': cached_response.created_at.isoformat(),
                'expires_at': cached_response.expires_at.isoformat(),
                'cost_saved': cached_response.cost_saved
            }
            
            await self.redis_client.setex(
                cache_key,
                ttl or self.default_ttl,
                json.dumps(cached_dict, default=str)
            )
            
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Generate a cache key based on request content"""
        # Create a hash of the request content for the cache key
        request_data = {
            'messages': request.messages,
            'task_type': request.task_type.value,
            'model': request.config.model,
            'temperature': request.config.temperature
        }
        
        # Sort the data to ensure consistent hashing
        request_str = json.dumps(request_data, sort_keys=True, default=str)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()
        
        return f"llm_cache:{request_hash}"
    
    async def warm_cache(self, requests: List[LLMRequest], responses: List[LLMResponse]) -> int:
        """Warm the cache with pre-computed responses"""
        if len(requests) != len(responses):
            raise ValueError("Requests and responses lists must have the same length")
        
        warmed_count = 0
        for request, response in zip(requests, responses):
            if await self.set(request, response):
                warmed_count += 1
        
        return warmed_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.stats.total_requests > 0:
            hit_rate = self.stats.hits / self.stats.total_requests
        else:
            hit_rate = 0.0
        
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'hit_rate': hit_rate,
            'total_requests': self.stats.total_requests,
            'savings_usd': self.stats.savings_usd,
            'connected': self._connected
        }
    
    async def clear(self) -> bool:
        """Clear all cached responses"""
        if not self._connected or not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            self.stats = CacheStats()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._connected and self.redis_client:
            await self.redis_client.close()
            self._connected = False


# Global cache instance
cache = LLMCache()
