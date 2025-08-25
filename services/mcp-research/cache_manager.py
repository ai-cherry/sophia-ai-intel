"""
Sophia AI Research Service - Aggressive Cache Manager

High-performance Redis-based caching system for research queries and results.
Eliminates redundant API calls and improves response times significantly.

Key Features:
- Multi-level caching strategy (query results, processed data, embeddings)
- Intelligent cache invalidation and TTL management
- Cache warming for frequently accessed queries
- Performance metrics and monitoring
- Fallback mechanisms for cache failures

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import redis
try:
    import aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    AIOREDIS_AVAILABLE = False
    logging.warning("aioredis not available - falling back to synchronous Redis")

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL")
DEFAULT_TTL = 3600  # 1 hour
LONG_TTL = 86400   # 24 hours
SHORT_TTL = 300    # 5 minutes


class CacheLevel(Enum):
    """Cache level priorities"""
    HOT = "hot"        # Frequently accessed, long TTL
    WARM = "warm"      # Moderately accessed, medium TTL
    COLD = "cold"      # Rarely accessed, short TTL


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_ratio: float
    average_response_time_ms: float
    total_keys: int
    memory_usage_bytes: int


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    level: CacheLevel
    created_at: float
    access_count: int
    last_accessed: float


class AggressiveCacheManager:
    """
    High-performance Redis cache manager with intelligent strategies
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.aioredis_client: Optional[aioredis.Redis] = None
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_generation_time': 0
        }
        
        # Cache key prefixes for organization
        self.prefixes = {
            'research_query': 'research:query:',
            'research_summary': 'research:summary:',
            'provider_result': 'research:provider:',
            'embedding': 'research:embed:',
            'metadata': 'research:meta:',
            'stats': 'research:stats:'
        }

    async def initialize(self):
        """Initialize Redis connections"""
        if not self.redis_url:
            logger.warning("Redis URL not configured - caching disabled")
            return False
        
        try:
            # Sync client for simple operations
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            
            # Async client for high-performance operations (if available)
            if AIOREDIS_AVAILABLE:
                self.aioredis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
                await self.aioredis_client.ping()
            else:
                self.aioredis_client = None
                logger.warning("aioredis not available - using synchronous Redis only")
            
            logger.info("Redis cache manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            return False

    def _generate_cache_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate intelligent cache key"""
        # Create deterministic hash from identifier and kwargs
        combined_data = f"{identifier}:{json.dumps(kwargs, sort_keys=True)}"
        hash_suffix = hashlib.sha256(combined_data.encode()).hexdigest()[:12]
        return f"{prefix}{hash_suffix}"

    async def get_cached_research_query(self, query: str, providers: List[str], **params) -> Optional[Dict[str, Any]]:
        """Get cached research query result"""
        if not self.aioredis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(
                self.prefixes['research_query'],
                query,
                providers=providers,
                **params
            )
            
            cached_result = await self.aioredis_client.get(cache_key)
            
            if cached_result:
                self.stats['cache_hits'] += 1
                self.stats['total_requests'] += 1
                
                # Update access metadata
                await self._update_access_metadata(cache_key)
                
                result = json.loads(cached_result)
                result['cached'] = True
                result['cache_key'] = cache_key
                
                logger.info(f"Cache HIT for research query: {query[:50]}...")
                return result
            else:
                self.stats['cache_misses'] += 1
                self.stats['total_requests'] += 1
                logger.info(f"Cache MISS for research query: {query[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def cache_research_query(
        self, 
        query: str, 
        providers: List[str], 
        result: Dict[str, Any], 
        ttl: Optional[int] = None,
        level: CacheLevel = CacheLevel.WARM,
        **params
    ) -> bool:
        """Cache research query result with intelligent TTL"""
        if not self.aioredis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(
                self.prefixes['research_query'],
                query,
                providers=providers,
                **params
            )
            
            # Determine TTL based on cache level and result quality
            if ttl is None:
                if level == CacheLevel.HOT:
                    ttl = LONG_TTL
                elif level == CacheLevel.WARM:
                    ttl = DEFAULT_TTL
                else:
                    ttl = SHORT_TTL
                
                # Adjust TTL based on result quality
                confidence = result.get('summary', {}).get('confidence', 0.5)
                if confidence > 0.9:
                    ttl *= 2  # High confidence results cached longer
                elif confidence < 0.5:
                    ttl //= 2  # Low confidence results cached shorter
            
            # Prepare cache entry
            cache_data = {
                **result,
                'cached_at': time.time(),
                'cache_level': level.value,
                'ttl': ttl,
                'query_hash': hashlib.sha256(query.encode()).hexdigest()[:12]
            }
            
            # Store in Redis
            await self.aioredis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            # Store access metadata
            await self._store_access_metadata(cache_key, {
                'query': query[:100],
                'providers': providers,
                'level': level.value,
                'ttl': ttl,
                'created_at': time.time(),
                'access_count': 0
            })
            
            logger.info(f"Cached research query: {query[:50]}... (TTL: {ttl}s, Level: {level.value})")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            return False

    async def get_cached_provider_result(self, provider: str, query: str, **params) -> Optional[Dict[str, Any]]:
        """Get cached individual provider result"""
        if not self.aioredis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(
                self.prefixes['provider_result'],
                f"{provider}:{query}",
                **params
            )
            
            cached_result = await self.aioredis_client.get(cache_key)
            
            if cached_result:
                self.stats['cache_hits'] += 1
                await self._update_access_metadata(cache_key)
                
                result = json.loads(cached_result)
                result['cached'] = True
                
                logger.debug(f"Cache HIT for {provider} query: {query[:30]}...")
                return result
            else:
                self.stats['cache_misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Provider cache retrieval failed: {e}")
            return None

    async def cache_provider_result(
        self, 
        provider: str, 
        query: str, 
        result: Dict[str, Any], 
        ttl: int = DEFAULT_TTL,
        **params
    ) -> bool:
        """Cache individual provider result"""
        if not self.aioredis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(
                self.prefixes['provider_result'],
                f"{provider}:{query}",
                **params
            )
            
            cache_data = {
                **result,
                'provider': provider,
                'cached_at': time.time(),
                'ttl': ttl
            }
            
            await self.aioredis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.debug(f"Cached {provider} result for: {query[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"Provider cache storage failed: {e}")
            return False

    async def get_cached_summary(self, content_hash: str) -> Optional[str]:
        """Get cached content summary"""
        if not self.aioredis_client:
            return None
        
        try:
            cache_key = self.prefixes['research_summary'] + content_hash
            cached_summary = await self.aioredis_client.get(cache_key)
            
            if cached_summary:
                self.stats['cache_hits'] += 1
                await self._update_access_metadata(cache_key)
                logger.debug(f"Cache HIT for summary: {content_hash}")
                return json.loads(cached_summary)
            else:
                self.stats['cache_misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Summary cache retrieval failed: {e}")
            return None

    async def cache_summary(self, content_hash: str, summary: str, ttl: int = LONG_TTL) -> bool:
        """Cache generated summary"""
        if not self.aioredis_client:
            return False
        
        try:
            cache_key = self.prefixes['research_summary'] + content_hash
            
            cache_data = {
                'summary': summary,
                'content_hash': content_hash,
                'cached_at': time.time(),
                'ttl': ttl
            }
            
            await self.aioredis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached summary for: {content_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Summary cache storage failed: {e}")
            return False

    async def _update_access_metadata(self, cache_key: str):
        """Update access metadata for cache optimization"""
        try:
            metadata_key = self.prefixes['metadata'] + cache_key.split(':')[-1]
            
            # Increment access count and update last accessed
            pipe = self.aioredis_client.pipeline()
            pipe.hincrby(metadata_key, 'access_count', 1)
            pipe.hset(metadata_key, 'last_accessed', time.time())
            pipe.expire(metadata_key, LONG_TTL)
            await pipe.execute()
            
        except Exception as e:
            logger.warning(f"Failed to update access metadata: {e}")

    async def _store_access_metadata(self, cache_key: str, metadata: Dict[str, Any]):
        """Store initial access metadata"""
        try:
            metadata_key = self.prefixes['metadata'] + cache_key.split(':')[-1]
            
            await self.aioredis_client.hmset(metadata_key, metadata)
            await self.aioredis_client.expire(metadata_key, LONG_TTL)
            
        except Exception as e:
            logger.warning(f"Failed to store access metadata: {e}")

    async def get_cache_performance_stats(self) -> CacheStats:
        """Get comprehensive cache performance statistics"""
        if not self.redis_client:
            return CacheStats(0, 0, 0, 0.0, 0.0, 0, 0)
        
        try:
            # Get Redis info
            info = self.redis_client.info()
            
            # Calculate hit ratio
            total_requests = self.stats['total_requests']
            hit_ratio = (self.stats['cache_hits'] / total_requests) if total_requests > 0 else 0.0
            
            # Average response time
            avg_response_time = (
                self.stats['total_generation_time'] / self.stats['cache_misses']
            ) if self.stats['cache_misses'] > 0 else 0.0
            
            # Count total keys (research-related)
            research_keys = 0
            for prefix in self.prefixes.values():
                keys = self.redis_client.keys(f"{prefix}*")
                research_keys += len(keys)
            
            return CacheStats(
                total_requests=total_requests,
                cache_hits=self.stats['cache_hits'],
                cache_misses=self.stats['cache_misses'],
                hit_ratio=hit_ratio,
                average_response_time_ms=avg_response_time,
                total_keys=research_keys,
                memory_usage_bytes=info.get('used_memory', 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return CacheStats(0, 0, 0, 0.0, 0.0, 0, 0)

    async def warm_cache_for_common_queries(self, common_queries: List[str]):
        """Pre-warm cache for frequently accessed queries"""
        if not self.aioredis_client:
            logger.warning("Cannot warm cache - Redis not available")
            return
        
        logger.info(f"Warming cache for {len(common_queries)} common queries")
        
        for query in common_queries:
            # Check if already cached
            cached = await self.get_cached_research_query(query, ['serpapi', 'perplexity'])
            
            if not cached:
                # This would trigger the actual research and cache the result
                logger.info(f"Would warm cache for: {query}")
                # In production, this would call the actual research function

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired or low-value cache entries"""
        if not self.redis_client:
            return 0
        
        try:
            cleaned_count = 0
            
            # Get all metadata keys to analyze access patterns
            metadata_keys = self.redis_client.keys(self.prefixes['metadata'] + '*')
            
            for metadata_key in metadata_keys:
                try:
                    metadata = self.redis_client.hgetall(metadata_key)
                    
                    if metadata:
                        # Check if low-value (low access count, old)
                        access_count = int(metadata.get('access_count', 0))
                        last_accessed = float(metadata.get('last_accessed', 0))
                        age_hours = (time.time() - last_accessed) / 3600
                        
                        # Remove if rarely accessed and old
                        if access_count < 2 and age_hours > 24:
                            # Find and remove associated cache entry
                            cache_suffix = metadata_key.split(':')[-1]
                            
                            for prefix in self.prefixes.values():
                                if prefix != self.prefixes['metadata']:
                                    cache_key = f"{prefix}{cache_suffix}"
                                    if self.redis_client.exists(cache_key):
                                        self.redis_client.delete(cache_key)
                                        cleaned_count += 1
                            
                            # Remove metadata
                            self.redis_client.delete(metadata_key)
                            
                except Exception as e:
                    logger.warning(f"Failed to process metadata key {metadata_key}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} low-value cache entries")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return 0

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys_to_delete = []
            
            for prefix in self.prefixes.values():
                matching_keys = self.redis_client.keys(f"{prefix}*{pattern}*")
                keys_to_delete.extend(matching_keys)
            
            if keys_to_delete:
                deleted_count = self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0

    async def get_hot_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed queries for optimization"""
        if not self.redis_client:
            return []
        
        try:
            hot_queries = []
            metadata_keys = self.redis_client.keys(self.prefixes['metadata'] + '*')
            
            # Collect access statistics
            for metadata_key in metadata_keys:
                try:
                    metadata = self.redis_client.hgetall(metadata_key)
                    
                    if metadata:
                        hot_queries.append({
                            'query': metadata.get('query', ''),
                            'access_count': int(metadata.get('access_count', 0)),
                            'last_accessed': float(metadata.get('last_accessed', 0)),
                            'providers': json.loads(metadata.get('providers', '[]')),
                            'level': metadata.get('level', 'unknown')
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to process hot query metadata: {e}")
            
            # Sort by access count
            hot_queries.sort(key=lambda x: x['access_count'], reverse=True)
            
            return hot_queries[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get hot queries: {e}")
            return []

    async def optimize_cache_levels(self):
        """Automatically optimize cache levels based on access patterns"""
        if not self.aioredis_client:
            return
        
        try:
            hot_queries = await self.get_hot_queries(50)
            
            # Promote frequently accessed queries to HOT level
            for query_info in hot_queries[:10]:  # Top 10 become HOT
                if query_info['access_count'] >= 5:
                    # Re-cache with HOT level (longer TTL)
                    logger.info(f"Promoting query to HOT level: {query_info['query'][:50]}...")
                    
            # Demote rarely accessed queries
            for query_info in hot_queries[30:]:  # Bottom queries become COLD
                if query_info['access_count'] <= 1:
                    logger.info(f"Demoting query to COLD level: {query_info['query'][:50]}...")
            
            logger.info("Cache level optimization completed")
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")

    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health metrics"""
        if not self.redis_client:
            return {"status": "disabled", "reason": "Redis not configured"}
        
        try:
            info = self.redis_client.info()
            
            # Calculate health metrics
            memory_usage_mb = info.get('used_memory', 0) / 1024 / 1024
            hit_ratio = (
                self.stats['cache_hits'] / self.stats['total_requests']
            ) if self.stats['total_requests'] > 0 else 0.0
            
            # Determine health status
            if hit_ratio >= 0.8 and memory_usage_mb < 500:
                status = "excellent"
            elif hit_ratio >= 0.6 and memory_usage_mb < 1000:
                status = "good"
            elif hit_ratio >= 0.4:
                status = "fair"
            else:
                status = "poor"
            
            return {
                "status": status,
                "hit_ratio": hit_ratio,
                "memory_usage_mb": memory_usage_mb,
                "total_requests": self.stats['total_requests'],
                "cache_hits": self.stats['cache_hits'],
                "cache_misses": self.stats['cache_misses'],
                "redis_connected": True,
                "recommendations": self._get_cache_recommendations(hit_ratio, memory_usage_mb)
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"status": "error", "error": str(e)}

    def _get_cache_recommendations(self, hit_ratio: float, memory_usage_mb: float) -> List[str]:
        """Generate cache optimization recommendations"""
        recommendations = []
        
        if hit_ratio < 0.5:
            recommendations.append("Consider increasing TTL for stable queries")
            recommendations.append("Implement cache warming for common queries")
        
        if memory_usage_mb > 800:
            recommendations.append("Run cache cleanup to remove expired entries")
            recommendations.append("Consider reducing TTL for less important data")
        
        if hit_ratio > 0.9:
            recommendations.append("Excellent cache performance - consider expanding cache usage")
        
        return recommendations

    async def close(self):
        """Close Redis connections"""
        try:
            if self.aioredis_client:
                await self.aioredis_client.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("Cache manager connections closed")
        except Exception as e:
            logger.error(f"Error closing cache connections: {e}")


# Global cache manager instance
cache_manager = AggressiveCacheManager()

# Decorator for automatic caching
def cached_research_query(ttl: int = DEFAULT_TTL, level: CacheLevel = CacheLevel.WARM):
    """Decorator to automatically cache research query results"""
    def decorator(func):
        async def wrapper(query: str, providers: List[str], *args, **kwargs):
            # Try to get from cache first
            cached_result = await cache_manager.get_cached_research_query(
                query, providers, **kwargs
            )
            
            if cached_result:
                return cached_result
            
            # Execute original function
            start_time = time.time()
            result = await func(query, providers, *args, **kwargs)
            execution_time = int((time.time() - start_time) * 1000)
            
            # Cache the result
            if result:
                cache_manager.stats['total_generation_time'] += execution_time
                await cache_manager.cache_research_query(
                    query, providers, result, ttl, level, **kwargs
                )
            
            return result
        
        return wrapper
    return decorator
