"""
Sophia AI Context Service - Real Embeddings Implementation

Replaces placeholder embeddings with functional OpenAI embeddings for semantic search.
Provides high-performance vector operations with proper caching and error handling.

Key Features:
- Real OpenAI text-embedding-3-large model integration
- Redis-based embedding caching for performance
- Batch processing for efficient embedding generation
- Semantic similarity search with Qdrant integration
- Comprehensive error handling and fallback mechanisms

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import openai
import redis
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, Distance, VectorParams
import numpy as np

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL") 
QDRANT_URL = os.getenv("QDRANT_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimensions
CACHE_TTL = 86400  # 24 hours
COLLECTION_NAME = "sophia_code_intelligence"


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    content: str
    embedding: List[float]
    model: str
    cached: bool
    generation_time_ms: int


@dataclass
class SearchResult:
    """Semantic search result with metadata"""
    id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    source: str


class RealEmbeddingEngine:
    """
    Production-ready embedding engine with caching and error handling
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.redis_client = redis.Redis.from_url(REDIS_URL) if REDIS_URL else None
        self.qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY) if QDRANT_URL else None
        
        # Validation
        if not self.openai_client:
            logger.warning("OpenAI client not configured - embeddings will fail")
        if not self.redis_client:
            logger.warning("Redis not configured - no caching available")
        if not self.qdrant_client:
            logger.warning("Qdrant not configured - vector search unavailable")
        
        # Initialize collection
        if self.qdrant_client:
            self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists with proper configuration"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(c.name == COLLECTION_NAME for c in collections.collections)
            
            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfig(
                        default_segment_number=2,
                        max_optimization_threads=2
                    ),
                    hnsw_config=models.HnswConfig(
                        ef_construct=200,
                        m=16,
                        full_scan_threshold=10000
                    )
                )
                logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
            else:
                logger.info(f"Qdrant collection {COLLECTION_NAME} already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")

    def _generate_cache_key(self, content: str) -> str:
        """Generate cache key for content"""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"embedding:v2:{EMBEDDING_MODEL}:{content_hash[:16]}"

    async def generate_embedding(self, content: str) -> EmbeddingResult:
        """
        Generate embedding for content with caching
        
        Args:
            content: Text content to embed
            
        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured")
        
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
                        generation_time_ms=int((time.time() - start_time) * 1000)
                    )
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")
        
        # Generate embedding
        try:
            # Truncate content if too long (OpenAI has token limits)
            truncated_content = content[:8000] if len(content) > 8000 else content
            
            response = await self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=truncated_content,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            if self.redis_client:
                try:
                    cache_data = {
                        'embedding': embedding,
                        'model': EMBEDDING_MODEL,
                        'content_length': len(content),
                        'generated_at': time.time()
                    }
                    self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
            
            return EmbeddingResult(
                content=content,
                embedding=embedding,
                model=EMBEDDING_MODEL,
                cached=False,
                generation_time_ms=int((time.time() - start_time) * 1000)
            )
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise ValueError(f"Failed to generate embedding: {e}")

    async def generate_embeddings_batch(self, contents: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple contents efficiently
        
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
                                generation_time_ms=1
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
        
        # Generate embeddings for uncached contents
        uncached_results = []
        if uncached_contents and self.openai_client:
            try:
                # Batch API call to OpenAI
                truncated_contents = [
                    content[:8000] if len(content) > 8000 else content 
                    for content in uncached_contents
                ]
                
                start_time = time.time()
                response = await self.openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=truncated_contents,
                    encoding_format="float"
                )
                generation_time = int((time.time() - start_time) * 1000)
                
                # Process results and cache
                for i, (content, embedding_data) in enumerate(zip(uncached_contents, response.data)):
                    embedding = embedding_data.embedding
                    
                    # Cache individual result
                    if self.redis_client:
                        try:
                            cache_data = {
                                'embedding': embedding,
                                'model': EMBEDDING_MODEL,
                                'content_length': len(content),
                                'generated_at': time.time()
                            }
                            cache_key = self._generate_cache_key(content)
                            self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
                        except Exception as e:
                            logger.warning(f"Cache storage failed for batch item {i}: {e}")
                    
                    uncached_results.append((uncached_indices[i], EmbeddingResult(
                        content=content,
                        embedding=embedding,
                        model=EMBEDDING_MODEL,
                        cached=False,
                        generation_time_ms=generation_time // len(uncached_contents)
                    )))
                    
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
        Store document with real embedding in Qdrant
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            source: Document source
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not configured")
            return False
        
        try:
            # Generate embedding
            embedding_result = await self.generate_embedding(content)
            
            # Store in Qdrant with metadata
            self.qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                wait=True,
                points=[PointStruct(
                    id=doc_id,
                    vector=embedding_result.embedding,
                    payload={
                        "content": content,
                        "source": source,
                        "metadata": metadata,
                        "embedding_model": embedding_result.model,
                        "content_length": len(content),
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "generation_time_ms": embedding_result.generation_time_ms,
                        "cached": embedding_result.cached
                    }
                )]
            )
            
            logger.info(f"Stored document {doc_id} with embedding (cached: {embedding_result.cached})")
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
        Perform semantic search using real embeddings
        
        Args:
            query: Search query
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects ranked by similarity
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not configured")
            return []
        
        try:
            # Generate query embedding
            query_embedding_result = await self.generate_embedding(query)
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding_result.embedding,
                limit=limit,
                score_threshold=similarity_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Convert to SearchResult objects
            results = []
            for hit in search_results:
                results.append(SearchResult(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    similarity_score=hit.score,
                    metadata=hit.payload.get("metadata", {}),
                    source=hit.payload.get("source", "unknown")
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
                "cache_ttl_hours": CACHE_TTL / 3600
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
            "openai_configured": bool(OPENAI_API_KEY),
            "redis_configured": bool(REDIS_URL),
            "qdrant_configured": bool(QDRANT_URL and QDRANT_API_KEY),
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "cache_ttl_hours": CACHE_TTL / 3600
        }
        
        # Test connections
        try:
            if self.redis_client:
                self.redis_client.ping()
                status["redis_connected"] = True
        except:
            status["redis_connected"] = False
        
        try:
            if self.qdrant_client:
                health = self.qdrant_client.health_check()
                status["qdrant_connected"] = health.status == "ok"
        except:
            status["qdrant_connected"] = False
        
        return status


# Global instance
embedding_engine = RealEmbeddingEngine()


# Utility functions for backward compatibility
async def generate_real_embedding(content: str) -> List[float]:
    """Generate real embedding - replaces placeholder function"""
    try:
        result = await embedding_engine.generate_embedding(content)
        return result.embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return zero vector as fallback (better than random)
        return [0.0] * EMBEDDING_DIMENSION


async def store_with_real_embedding(doc_id: str, content: str, source: str, metadata: Dict[str, Any]) -> bool:
    """Store document with real embedding - replaces placeholder function"""
    return await embedding_engine.store_document_with_embedding(doc_id, content, source, metadata)


async def semantic_search_documents(query: str, limit: int = 10) -> List[SearchResult]:
    """Perform semantic search - replaces placeholder function"""
    return await embedding_engine.semantic_search(query, limit)
