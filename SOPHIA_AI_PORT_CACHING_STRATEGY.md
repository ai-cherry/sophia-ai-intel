# Sophia AI Port Allocation & Caching Strategy

## Port Allocation Strategy

### Current Port Conflicts & Resolution

#### 1. Port Allocation Table

| Service | Current Port | Proposed Port | Protocol | Purpose |
|---------|--------------|---------------|----------|---------|
| **Frontend Services** |
| sophia-dashboard | 3000 | 3000 | HTTP | React Dashboard |
| **Core MCP Services** |
| mcp-research | 8081 | 8081 | HTTP | Research API |
| mcp-context | 8082 | 8082 | HTTP | Context/Embeddings API |
| mcp-github | 8083 | 8083 | HTTP | GitHub Integration |
| mcp-business | 8084 | 8084 | HTTP | Business Services |
| mcp-lambda | 8085 | 8085 | HTTP | Lambda Integration |
| mcp-hubspot | 8086 | 8086 | HTTP | HubSpot Integration |
| mcp-agents | 8087 | 8000 → 8087 | HTTP | Agent Swarm (Fix port) |
| **New MCP Services** |
| mcp-gong | - | 8088 | HTTP | Gong Integration |
| mcp-salesforce | - | 8089 | HTTP | Salesforce Integration |
| mcp-slack | - | 8090 | HTTP | Slack Integration |
| mcp-apollo | - | 8091 | HTTP | Apollo.io Integration |
| mcp-intercom | - | 8092 | HTTP | Intercom Integration |
| mcp-linear | - | 8093 | HTTP | Linear Integration |
| mcp-looker | - | 8094 | HTTP | Looker Integration |
| mcp-asana | - | 8095 | HTTP | Asana Integration |
| mcp-notion | - | 8096 | HTTP | Notion Integration |
| mcp-gdrive | - | 8097 | HTTP | Google Drive Integration |
| mcp-costar | - | 8098 | HTTP | CoStar Integration |
| mcp-phantom | - | 8099 | HTTP | PhantomBuster Integration |
| mcp-outlook | - | 8100 | HTTP | Outlook Integration |
| mcp-sharepoint | - | 8101 | HTTP | SharePoint Integration |
| mcp-elevenlabs | - | 8102 | HTTP | 11 Labs Integration |
| **Agno Framework** |
| agno-coordinator | - | 3002 | HTTP | Agno Coordinator |
| agno-teams | - | 8008 | HTTP | Agno Teams |
| **Infrastructure** |
| orchestrator | - | 8080 | HTTP | Service Orchestrator |
| nginx-proxy | 80, 443 | 80, 443 | HTTP/HTTPS | Reverse Proxy |
| redis | 6379 | 6379 | TCP | Cache/Session Store |
| postgresql | 5432 | 5432 | TCP | Primary Database |
| qdrant | 6333 | 6333 | HTTP/gRPC | Vector Database |
| **Monitoring** |
| prometheus | 9090 | 9090 | HTTP | Metrics Collection |
| grafana | 3001 | 3001 | HTTP | Metrics Visualization |
| loki | 3100 | 3100 | HTTP | Log Aggregation |
| promtail | 9080 | 9080 | HTTP | Log Collection |
| cadvisor | 8080 | **8900** | HTTP | Container Metrics (FIXED) |
| node-exporter | 9100 | 9100 | HTTP | Node Metrics |
| dcgm-exporter | 9400 | 9400 | HTTP | GPU Metrics |
| **Development** |
| kubernetes-dashboard | - | 31443 | HTTPS | K8s Dashboard |

### Port Range Allocation Strategy

```yaml
portRanges:
  frontend: 3000-3999
  core-services: 8000-8499
  monitoring: 9000-9999
  infrastructure: 5000-6999
  development: 30000-31999
```

## Caching Strategy

### 1. Multi-Level Cache Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                            │
│                  (Browser Cache)                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                       CDN Layer                              │
│                  (CloudFlare/Fastly)                         │
│  • Static Assets: 1 year                                     │
│  • API Responses: 5-60 minutes                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    Nginx Cache                               │
│                 (Reverse Proxy)                              │
│  • Static: 1 hour                                            │
│  • Dynamic: 1-5 minutes                                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                  Application Cache                           │
│                      (Redis)                                 │
│  • Session Data: 24 hours                                    │
│  • API Results: 5-60 minutes                                 │
│  • Computed Data: 1-6 hours                                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                  Service-Level Cache                         │
│              (In-Memory + Redis)                             │
│  • LLM Responses: 1 hour                                     │
│  • Embeddings: 24 hours                                      │
│  • Search Results: 30 minutes                                │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                   Database Cache                             │
│              (PostgreSQL + Qdrant)                           │
│  • Query Cache: 5-30 minutes                                 │
│  • Vector Cache: Persistent                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Redis Cache Configuration

#### 2.1 Cache Databases Allocation

```yaml
redis-databases:
  0: session-store       # User sessions
  1: api-cache          # API response cache
  2: llm-cache          # LLM response cache
  3: embedding-cache    # Vector embeddings
  4: business-cache     # Business data (CRM, etc.)
  5: rate-limiting      # API rate limit counters
  6: job-queue         # Background job queue
  7: pubsub            # Real-time events
  8: feature-flags     # Feature toggles
  9: metrics           # Temporary metrics storage
  10: search-cache     # Search results
  11: graph-cache      # Relationship data
  12: temp-storage     # Temporary data
  13: locks            # Distributed locks
  14: analytics        # Analytics data
  15: backup           # Cache backup/restore
```

#### 2.2 Cache Key Patterns

```python
# Standard cache key patterns
cache_keys = {
    # Session management
    "session": "session:{user_id}:{session_id}",
    
    # API responses
    "api_response": "api:{service}:{endpoint}:{params_hash}",
    
    # LLM responses
    "llm_response": "llm:{model}:{prompt_hash}:{params_hash}",
    
    # Business data
    "salesforce": "sf:{object_type}:{object_id}:{field}",
    "hubspot": "hs:{object_type}:{object_id}",
    "gong": "gong:{call_id}:{data_type}",
    
    # Embeddings
    "embedding": "emb:{model}:{content_hash}",
    
    # Search results
    "search": "search:{index}:{query_hash}:{filters_hash}",
    
    # Rate limiting
    "rate_limit": "rl:{user_id}:{endpoint}:{window}",
    
    # Feature flags
    "feature": "feature:{flag_name}:{user_segment}"
}
```

### 3. Cache Implementation Strategy

#### 3.1 Service-Level Caching

```python
# Example: MCP Service Cache Decorator
from functools import wraps
import hashlib
import json
import redis
from typing import Any, Optional

class MCPCache:
    def __init__(self, redis_client: redis.Redis, db: int, default_ttl: int = 300):
        self.redis = redis_client
        self.db = db
        self.default_ttl = default_ttl
    
    def cache_result(self, ttl: Optional[int] = None, key_prefix: str = ""):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(func.__name__, key_prefix, args, kwargs)
                
                # Try to get from cache
                cached = await self._get_cached(cache_key)
                if cached is not None:
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self._set_cache(cache_key, result, ttl or self.default_ttl)
                
                return result
            return wrapper
        return decorator
    
    def _generate_key(self, func_name: str, prefix: str, args: tuple, kwargs: dict) -> str:
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"{prefix}:{func_name}:{key_hash}"

# Usage in services
cache = MCPCache(redis_client, db=1)

@cache.cache_result(ttl=3600, key_prefix="gong")
async def get_gong_calls(user_id: str):
    # Expensive API call
    return await gong_api.get_user_calls(user_id)
```

#### 3.2 LLM Response Caching

```python
class LLMCache:
    """Intelligent LLM response caching with semantic similarity"""
    
    def __init__(self, redis_client: redis.Redis, qdrant_client):
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.embedding_model = "text-embedding-ada-002"
    
    async def get_or_compute(self, prompt: str, model: str, **params):
        # Check exact match cache first
        exact_key = self._exact_key(prompt, model, params)
        exact_match = await self.redis.get(exact_key)
        if exact_match:
            return json.loads(exact_match)
        
        # Check semantic similarity cache
        embedding = await self._get_embedding(prompt)
        similar = await self._find_similar_prompts(embedding, model)
        
        if similar and similar["score"] > 0.95:  # 95% similarity threshold
            return similar["response"]
        
        # Compute new response
        response = await self._compute_llm_response(prompt, model, **params)
        
        # Cache both exact and semantic
        await self._cache_response(prompt, model, params, response, embedding)
        
        return response
```

### 4. Cache Warming Strategy

```yaml
cache-warming:
  startup:
    - name: "Load frequently accessed business data"
      targets:
        - salesforce: ["accounts", "contacts", "opportunities"]
        - hubspot: ["companies", "deals", "contacts"]
      schedule: "on_startup"
    
    - name: "Pre-compute embeddings"
      targets:
        - knowledge_base: ["core_documents", "faqs"]
      schedule: "on_startup"
  
  periodic:
    - name: "Refresh user sessions"
      interval: "5m"
      target: "active_sessions"
    
    - name: "Update business metrics"
      interval: "15m"
      targets: ["sales_pipeline", "customer_health"]
    
    - name: "Refresh search indices"
      interval: "1h"
      targets: ["vector_search", "full_text_search"]
```

### 5. Cache Invalidation Strategy

```python
class CacheInvalidator:
    """Intelligent cache invalidation with dependency tracking"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.dependencies = {}
    
    def register_dependency(self, cache_key: str, depends_on: list):
        """Register cache dependencies"""
        for dep in depends_on:
            if dep not in self.dependencies:
                self.dependencies[dep] = set()
            self.dependencies[dep].add(cache_key)
    
    async def invalidate(self, key: str, cascade: bool = True):
        """Invalidate cache with optional cascade"""
        # Delete the key
        await self.redis.delete(key)
        
        if cascade and key in self.dependencies:
            # Invalidate dependent caches
            for dependent in self.dependencies[key]:
                await self.invalidate(dependent, cascade=True)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

### 6. Redis Configuration

```conf
# redis.conf optimizations for Sophia AI

# Memory optimization
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence (for cache warming)
save 900 1
save 300 10
save 60 10000

# Connection optimization
tcp-backlog 511
tcp-keepalive 60
timeout 300

# Performance tuning
hz 100
databases 16

# Cluster configuration (for scaling)
# cluster-enabled yes
# cluster-config-file nodes.conf
# cluster-node-timeout 5000
```

### 7. Monitoring & Metrics

```yaml
cache-metrics:
  prometheus:
    - metric: redis_hit_rate
      type: gauge
      help: "Cache hit rate percentage"
    
    - metric: redis_memory_usage
      type: gauge
      help: "Redis memory usage in bytes"
    
    - metric: cache_latency
      type: histogram
      help: "Cache operation latency"
    
    - metric: eviction_count
      type: counter
      help: "Number of cache evictions"
  
  alerts:
    - name: "Low cache hit rate"
      condition: "redis_hit_rate < 0.7"
      severity: warning
    
    - name: "High memory usage"
      condition: "redis_memory_usage > 0.9 * maxmemory"
      severity: critical
```

## Implementation Priority

### Phase 1: Immediate (Week 1)
1. Fix cAdvisor port conflict (8080 → 8900)
2. Implement Redis multi-database configuration
3. Set up basic API response caching
4. Configure Nginx caching layer

### Phase 2: Short-term (Week 2-3)
1. Implement LLM response caching
2. Set up embedding cache with Qdrant
3. Configure cache warming for business data
4. Implement cache invalidation strategy

### Phase 3: Medium-term (Month 1-2)
1. Add CDN layer for static assets
2. Implement intelligent semantic caching
3. Set up distributed cache with Redis Cluster
4. Add comprehensive cache monitoring

## Best Practices

1. **Cache Key Design**
   - Use consistent naming patterns
   - Include version in keys for easy invalidation
   - Keep keys short but descriptive

2. **TTL Strategy**
   - Static data: 24 hours - 1 year
   - Business data: 5-60 minutes
   - LLM responses: 1-6 hours
   - Session data: 24 hours

3. **Memory Management**
   - Monitor memory usage continuously
   - Set appropriate eviction policies
   - Use compression for large values

4. **Security**
   - Encrypt sensitive cached data
   - Use separate databases for different data types
   - Implement access controls

5. **Performance**
   - Use pipelining for bulk operations
   - Implement connection pooling
   - Monitor and optimize slow queries
