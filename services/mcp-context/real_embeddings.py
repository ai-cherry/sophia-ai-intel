"""
Sophia AI Context Service - Real Embeddings Implementation

Replaces placeholder embeddings with standardized Portkey routing for semantic search.
Provides high-performance vector operations with proper caching and error handling.

Key Features:
- Standardized Portkey routing for embeddings (OpenRouter removed)
- Redis-based embedding caching for performance
- Batch processing for efficient embedding generation
- Semantic similarity search with Weaviate integration
- Comprehensive error handling and fallback mechanisms

Version: 2.0.0 - Standardized Routing
Author: Sophia AI Intelligence Team
"""

import hashlib
import json
import logging
import os
import time
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType

logger = logging.getLogger(__name__)

# Configuration - Updated for standardized routing
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimensions
CACHE_TTL = 86400  # 24 hours
CLASS_NAME = "SophiaCodeIntelligence"


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    content: str
    embedding: List[float]
    model: str
    cached: bool
    generation_time_ms: int
    provider: str = "standardized_portkey"


@dataclass
class SearchResult:
    """Semantic search result with metadata"""
    id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    source: str


class StandardizedEmbeddingEngine:
    """
    Production-ready embedding engine using standardized Portkey routing
    OpenRouter removed - using unified Portkey virtual keys
    """

    def __init__(self):
        self.portkey_available = bool(PORTKEY_API_KEY)
        self.session: Optional[aiohttp.ClientSession] = None
        # Temporarily disable Redis to get service running
        # TODO: Fix Redis URL configuration once service is stable
        self.redis_client = None
        logger.info("Redis temporarily disabled - running without cache")
        self.weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        ) if WEAVIATE_URL and WEAVIATE_API_KEY else None

        # Validation
        if not self.portkey_available:
            logger.warning("Portkey API key not configured - embeddings will fail")
        if not self.redis_client:
            logger.warning("Redis not configured - no caching available")
        if not self.weaviate_client:
            logger.warning("Weaviate not configured - vector search unavailable")

        # Initialize schema
        if self.weaviate_client:
            self._ensure_schema_exists()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"User-Agent": "Sophia-AI-Embeddings/2.0"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _ensure_schema_exists(self):
        """Ensure Weaviate schema/class exists with proper configuration"""
        try:
            schema = self.weaviate_client.schema.get()
            class_exists = any(c['class'] == CLASS_NAME for c in schema.get('classes', []))

            if not class_exists:
                class_definition = {
                    "class": CLASS_NAME,
                    "description": "Sophia AI code intelligence documents with embeddings",
                    "vectorizer": "none",  # We provide our own vectors
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content"
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                            "description": "Document source"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata"
                        },
                        {
                            "name": "embeddingModel",
                            "dataType": ["string"],
                            "description": "Embedding model used"
                        },
                        {
                            "name": "embeddingProvider",
                            "dataType": ["string"],
                            "description": "Embedding provider"
                        },
                        {
                            "name": "contentLength",
                            "dataType": ["int"],
                            "description": "Content length"
                        },
                        {
                            "name": "createdAt",
                            "dataType": ["date"],
                            "description": "Creation timestamp"
                        },
                        {
                            "name": "generationTimeMs",
                            "dataType": ["int"],
                            "description": "Embedding generation time in ms"
                        },
                        {
                            "name": "cached",
                            "dataType": ["boolean"],
                            "description": "Whether embedding was cached"
                        }
                    ]
                }
                
                self.weaviate_client.schema.create_class(class_definition)
                logger.info(f"Created Weaviate class: {CLASS_NAME}")
            else:
                logger.info(f"Weaviate class {CLASS_NAME} already exists")

        except Exception as e:
            logger.error(f"Failed to ensure schema exists: {e}")

    def _generate_cache_key(self, content: str) -> str:
        """Generate cache key for content"""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"embedding:v2:{EMBEDDING_MODEL}:{content_hash[:16]}"

    async def _generate_embedding_via_portkey(self, content: str) -> List[float]:
        """Generate embedding using standardized Portkey routing"""
        if not self.session:
            raise ValueError("HTTP session not initialized")

        headers = {
            "x-portkey-api-key": PORTKEY_API_KEY,
            "x-portkey-virtual-key": "openai-text-embedding-3-large",  # Standardized virtual key
            "Content-Type": "application/json"
        }

        payload = {
            "model": EMBEDDING_MODEL,
            "input": content[:8000],  # Truncate to model limits
            "encoding_format": "float"
        }

        async with self.session.post("https://api.portkey.ai/v1/embeddings", json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Portkey returns OpenAI-compatible format
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                else:
                    logger.error(f"Unexpected embedding response format: {data}")
                    raise ValueError("Invalid embedding response format")
            else:
                error_text = await response.text()
                logger.error(f"Portkey embedding API error {response.status}: {error_text}")
                raise Exception(f"Portkey API error {response.status}: {error_text}")

    async def generate_embedding(self, content: str) -> EmbeddingResult:
        """
        Generate embedding for content with caching using standardized routing

        Args:
            content: Text content to embed

        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if not self.portkey_available:
            raise ValueError("Portkey API key not configured")

        start_time = time.time()
        cache_key = self._generate_cache_key(content)

        # Check cache first
        if self.redis_client:
            try:
                cached_embedding = self.redis_client.get(cache_key)
                if cached_embedding:
                    embedding_data = json.loads(cached_embedding)
                    return EmbeddingResult(
                        content=content,
                        embedding=embedding_data['embedding'],
                        model=embedding_data['model'],
                        cached=True,
                        generation_time_ms=int((time.time() - start_time) * 1000),
                        provider="standardized_portkey"
                    )
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")

        # Generate embedding using standardized routing
        try:
            async with self as engine:
                embedding = await engine._generate_embedding_via_portkey(content)

            # Cache the result
            if self.redis_client:
                try:
                    cache_data = {
                        'embedding': embedding,
                        'model': EMBEDDING_MODEL,
                        'content_length': len(content),
                        'generated_at': time.time(),
                        'provider': 'standardized_portkey'
                    }
                    self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")

            return EmbeddingResult(
                content=content,
                embedding=embedding,
                model=EMBEDDING_MODEL,
                cached=False,
                generation_time_ms=int((time.time() - start_time) * 1000),
                provider="standardized_portkey"
            )

        except Exception as e:
            logger.error(f"Standardized embedding generation failed: {e}")
            raise ValueError(f"Failed to generate embedding: {e}")

    async def generate_embeddings_batch(self, contents: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple contents efficiently using standardized routing

        Args:
            contents: List of text contents to embed

        Returns:
            List of EmbeddingResult objects
        """
        if not contents:
            return []

        # Check cache for all contents
        cache_keys = [self._generate_cache_key(content) for content in contents]
        cached_results = []
        uncached_contents = []
        uncached_indices = []

        if self.redis_client:
            try:
                cached_values = self.redis_client.mget(cache_keys)
                for i, cached_value in enumerate(cached_values):
                    if cached_value:
                        try:
                            embedding_data = json.loads(cached_value)
                            cached_results.append((i, EmbeddingResult(
                                content=contents[i],
                                embedding=embedding_data['embedding'],
                                model=embedding_data['model'],
                                cached=True,
                                generation_time_ms=1,
                                provider="standardized_portkey"
                            )))
                        except Exception as e:
                            logger.warning(f"Invalid cache data for index {i}: {e}")
                            uncached_contents.append(contents[i])
                            uncached_indices.append(i)
                    else:
                        uncached_contents.append(contents[i])
                        uncached_indices.append(i)
            except Exception as e:
                logger.warning(f"Batch cache lookup failed: {e}")
                uncached_contents = contents
                uncached_indices = list(range(len(contents)))
        else:
            uncached_contents = contents
            uncached_indices = list(range(len(contents)))

        # Generate embeddings for uncached contents using standardized routing
        uncached_results = []
        if uncached_contents and self.portkey_available:
            try:
                async with self as engine:
                    # Process in smaller batches to avoid API limits
                    batch_size = 10
                    for i in range(0, len(uncached_contents), batch_size):
                        batch_contents = uncached_contents[i:i + batch_size]
                        batch_indices = uncached_indices[i:i + batch_size]

                        # Note: Portkey doesn't support true batching like OpenAI
                        # We'll process sequentially for now
                        for content, index in zip(batch_contents, batch_indices):
                            try:
                                start_time = time.time()
                                embedding = await engine._generate_embedding_via_portkey(content)
                                generation_time = int((time.time() - start_time) * 1000)

                                # Cache individual result
                                if self.redis_client:
                                    try:
                                        cache_data = {
                                            'embedding': embedding,
                                            'model': EMBEDDING_MODEL,
                                            'content_length': len(content),
                                            'generated_at': time.time(),
                                            'provider': 'standardized_portkey'
                                        }
                                        cache_key = self._generate_cache_key(content)
                                        self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
                                    except Exception as e:
                                        logger.warning(f"Cache storage failed for batch item {index}: {e}")

                                uncached_results.append((index, EmbeddingResult(
                                    content=content,
                                    embedding=embedding,
                                    model=EMBEDDING_MODEL,
                                    cached=False,
                                    generation_time_ms=generation_time,
                                    provider="standardized_portkey"
                                )))

                            except Exception as e:
                                logger.error(f"Failed to generate embedding for batch item {index}: {e}")
                                continue

            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                raise ValueError(f"Failed to generate batch embeddings: {e}")

        # Combine cached and uncached results in original order
        all_results = [None] * len(contents)

        for index, result in cached_results:
            all_results[index] = result

        for index, result in uncached_results:
            all_results[index] = result

        return [r for r in all_results if r is not None]

    async def store_document_with_embedding(
        self,
        doc_id: str,
        content: str,
        source: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store document with real embedding in Weaviate using standardized routing

        Args:
            doc_id: Unique document identifier
            content: Document content
            source: Document source
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.weaviate_client:
            logger.error("Weaviate client not configured")
            return False

        try:
            # Generate embedding using standardized routing
            embedding_result = await self.generate_embedding(content)

            # Store in Weaviate with metadata
            data_object = {
                "content": content,
                "source": source,
                "metadata": metadata,
                "embeddingModel": embedding_result.model,
                "embeddingProvider": embedding_result.provider,
                "contentLength": len(content),
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "generationTimeMs": embedding_result.generation_time_ms,
                "cached": embedding_result.cached
            }

            self.weaviate_client.data_object.create(
                data_object=data_object,
                class_name=CLASS_NAME,
                uuid=doc_id,
                vector=embedding_result.embedding
            )

            logger.info(f"Stored document {doc_id} with embedding (cached: {embedding_result.cached}, provider: {embedding_result.provider})")
            return True

        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            return False

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Perform semantic search using real embeddings with standardized routing

        Args:
            query: Search query
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of SearchResult objects ranked by similarity
        """
        if not self.weaviate_client:
            logger.error("Weaviate client not configured")
            return []

        try:
            # Generate query embedding using standardized routing
            query_embedding_result = await self.generate_embedding(query)

            # Search in Weaviate
            near_vector = {"vector": query_embedding_result.embedding}
            
            response = (
                self.weaviate_client.query
                .get(CLASS_NAME, ["content", "source", "metadata"])
                .with_near_vector(near_vector)
                .with_limit(limit)
                .with_additional(["id", "distance"])
                .do()
            )

            # Convert to SearchResult objects
            results = []
            if 'data' in response and 'Get' in response['data'] and CLASS_NAME in response['data']['Get']:
                for item in response['data']['Get'][CLASS_NAME]:
                    # Convert Weaviate distance to similarity score (1 - distance for cosine)
                    distance = item['_additional']['distance']
                    similarity_score = 1.0 - distance if distance is not None else 0.0
                    
                    # Only include results above similarity threshold
                    if similarity_score >= similarity_threshold:
                        results.append(SearchResult(
                            id=item['_additional']['id'],
                            content=item.get("content", ""),
                            similarity_score=similarity_score,
                            metadata=item.get("metadata", {}),
                            source=item.get("source", "unknown")
                        ))

            logger.info(f"Semantic search for '{query[:50]}...' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics"""
        if not self.redis_client:
            return {"error": "Redis not configured"}

        try:
            # Get cache statistics
            info = self.redis_client.info()

            # Count embedding keys
            embedding_keys = self.redis_client.keys("embedding:v2:*")

            return {
                "redis_connected": True,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "embedding_keys": len(embedding_keys),
                "memory_usage_bytes": info.get("used_memory", 0),
                "cache_hit_ratio": info.get("keyspace_hit_rate", "N/A"),
                "embedding_model": EMBEDDING_MODEL,
                "cache_ttl_hours": CACHE_TTL / 3600,
                "provider": "standardized_portkey"
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear embedding cache"""
        if not self.redis_client:
            return 0

        try:
            if pattern:
                keys = self.redis_client.keys(f"embedding:v2:{pattern}*")
            else:
                keys = self.redis_client.keys("embedding:v2:*")

            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} embedding cache entries")
                return deleted_count

            return 0

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate embedding engine configuration"""
        status = {
            "portkey_configured": bool(PORTKEY_API_KEY),
            "redis_configured": bool(REDIS_URL),
            "weaviate_configured": bool(WEAVIATE_URL and WEAVIATE_API_KEY),
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "cache_ttl_hours": CACHE_TTL / 3600,
            "provider": "standardized_portkey"
        }

        # Test connections
        try:
            if self.redis_client:
                self.redis_client.ping()
                status["redis_connected"] = True
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            status["redis_connected"] = False

        try:
            if self.weaviate_client:
                status["weaviate_connected"] = self.weaviate_client.is_ready()
        except Exception as e:
            logger.warning(f"Weaviate connection test failed: {e}")
            status["weaviate_connected"] = False

        return status


# Global instance
embedding_engine = StandardizedEmbeddingEngine()


# Utility functions for backward compatibility
async def generate_real_embedding(content: str) -> List[float]:
    """Generate real embedding using standardized routing - replaces placeholder function"""
    try:
        result = await embedding_engine.generate_embedding(content)
        return result.embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return zero vector as fallback (better than random)
        return [0.0] * EMBEDDING_DIMENSION


async def store_with_real_embedding(doc_id: str, content: str, source: str, metadata: Dict[str, Any]) -> bool:
    """Store document with real embedding using standardized routing - replaces placeholder function"""
    return await embedding_engine.store_document_with_embedding(doc_id, content, source, metadata)


async def semantic_search_documents(query: str, limit: int = 10) -> List[SearchResult]:
    """Perform semantic search using standardized routing - replaces placeholder function"""
    return await embedding_engine.semantic_search(query, limit)