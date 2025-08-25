"""
Sophia AI RAG Pipeline

Retrieval-Augmented Generation pipeline that integrates code embeddings 
with MCP services for intelligent context retrieval and augmentation.

Key Features:
- Semantic code retrieval using embeddings
- Integration with MCP context service  
- Multi-stage retrieval pipeline
- Context ranking and filtering
- Query expansion and refinement
- Integration with LLM routing

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


from .embedding_engine import EmbeddingEngine, CodeChunk, SearchResult, ChunkType
from ..base_agent import AgentMemory

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Strategies for information retrieval"""
    SEMANTIC_SEARCH = "semantic_search"
    HYBRID_SEARCH = "hybrid_search"
    CONTEXTUAL_EXPANSION = "contextual_expansion"
    HIERARCHICAL_SEARCH = "hierarchical_search"
    PATTERN_MATCHING = "pattern_matching"


class ContextType(Enum):
    """Types of context for retrieval"""
    CODE_IMPLEMENTATION = "code_implementation"
    DOCUMENTATION = "documentation"
    API_USAGE = "api_usage"
    DESIGN_PATTERNS = "design_patterns"
    ERROR_HANDLING = "error_handling"
    TEST_CASES = "test_cases"
    CONFIGURATION = "configuration"
    DEPENDENCIES = "dependencies"


@dataclass
class RetrievalQuery:
    """Query for retrieving relevant context"""
    query: str
    context_types: List[ContextType]
    strategy: RetrievalStrategy
    max_results: int = 10
    similarity_threshold: float = 0.6
    include_context: bool = True
    expand_query: bool = True
    filter_languages: Optional[List[str]] = None
    filter_file_patterns: Optional[List[str]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    agent_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.filter_languages is None:
            self.filter_languages = []
        if self.filter_file_patterns is None:
            self.filter_file_patterns = []
        if self.metadata_filters is None:
            self.metadata_filters = {}
        if self.agent_context is None:
            self.agent_context = {}


@dataclass
class RetrievalResult:
    """Result from RAG pipeline retrieval"""
    query: RetrievalQuery
    chunks: List[SearchResult]
    augmented_context: str
    metadata: Dict[str, Any]
    processing_time_ms: float
    total_tokens: int
    confidence_score: float
    retrieval_strategy_used: str
    sources: List[str]


@dataclass
class ContextWindow:
    """Context window for agent interactions"""
    primary_context: str
    supporting_context: List[str]
    code_examples: List[str]
    relevant_files: List[str]
    related_patterns: List[str]
    metadata: Dict[str, Any]
    confidence_scores: Dict[str, float]


class QueryExpander:
    """
    Expands queries with related terms and concepts for better retrieval
    """
    
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedding_engine = embedding_engine
        
        # Common programming concepts and synonyms
        self.concept_mappings = {
            "authentication": ["auth", "login", "security", "credentials", "token"],
            "database": ["db", "storage", "persistence", "data", "query", "sql"],
            "api": ["endpoint", "service", "request", "response", "http", "rest"],
            "error": ["exception", "failure", "bug", "issue", "problem"],
            "test": ["testing", "unit test", "integration", "spec", "assert"],
            "config": ["configuration", "settings", "environment", "setup"],
            "deploy": ["deployment", "release", "production", "build"],
            "cache": ["caching", "redis", "memory", "performance"],
            "async": ["asynchronous", "await", "promise", "concurrent"],
            "validation": ["validate", "check", "verify", "sanitize"]
        }

    async def expand_query(self, query: str, context_types: List[ContextType]) -> List[str]:
        """Expand query with related terms and concepts"""
        expanded_queries = [query]
        
        # Add concept-based expansions
        query_lower = query.lower()
        for concept, synonyms in self.concept_mappings.items():
            if concept in query_lower or any(syn in query_lower for syn in synonyms):
                for synonym in synonyms:
                    if synonym not in query_lower:
                        expanded_queries.append(f"{query} {synonym}")
        
        # Add context-type specific expansions
        for context_type in context_types:
            if context_type == ContextType.CODE_IMPLEMENTATION:
                expanded_queries.append(f"{query} implementation function method")
            elif context_type == ContextType.DOCUMENTATION:
                expanded_queries.append(f"{query} documentation readme comment docstring")
            elif context_type == ContextType.API_USAGE:
                expanded_queries.append(f"{query} api usage example endpoint")
            elif context_type == ContextType.TEST_CASES:
                expanded_queries.append(f"{query} test case unit integration")
        
        # Limit expansion to avoid too many queries
        return expanded_queries[:5]

    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key technical terms from query"""
        # Simple term extraction - could be enhanced with NLP
        import re
        
        # Common technical patterns
        patterns = [
            r'\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*\b',  # CamelCase
            r'\b[a-z]+_[a-z_]+\b',  # snake_case
            r'\b[a-zA-Z]+\.[a-zA-Z]+\b',  # module.function
            r'\b\w+\(\)\b',  # function()
            r'\b[A-Z]{2,}\b'  # CONSTANTS
        ]
        
        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, query)
            terms.extend(matches)
        
        return list(set(terms))


class ContextRanker:
    """
    Ranks and filters retrieved context based on relevance and quality
    """
    
    def __init__(self):
        self.quality_factors = {
            'has_documentation': 1.2,
            'has_tests': 1.1,
            'recent_modification': 1.1,
            'function_over_comment': 1.3,
            'class_over_function': 1.1,
            'complete_implementation': 1.2
        }

    async def rank_results(
        self, 
        results: List[SearchResult], 
        query: RetrievalQuery
    ) -> List[SearchResult]:
        """Rank search results by relevance and quality"""
        scored_results = []
        
        for result in results:
            quality_score = await self._calculate_quality_score(result.chunk)
            relevance_score = result.similarity_score
            context_score = await self._calculate_context_score(result, query)
            
            # Combined score
            final_score = (
                relevance_score * 0.5 +
                quality_score * 0.3 +
                context_score * 0.2
            )
            
            result.similarity_score = final_score
            scored_results.append(result)
        
        # Sort by final score
        scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return scored_results

    async def _calculate_quality_score(self, chunk: CodeChunk) -> float:
        """Calculate quality score for a code chunk"""
        score = 1.0
        
        # Factor in chunk type
        type_scores = {
            ChunkType.FUNCTION: 1.3,
            ChunkType.METHOD: 1.2,
            ChunkType.CLASS: 1.4,
            ChunkType.FILE: 1.0,
            ChunkType.DOCSTRING: 1.1,
            ChunkType.COMMENT: 0.8,
            ChunkType.BLOCK: 0.9
        }
        
        score *= type_scores.get(chunk.chunk_type, 1.0)
        
        # Factor in metadata
        if chunk.metadata:
            if chunk.metadata.get('docstring'):
                score *= self.quality_factors['has_documentation']
            
            if chunk.metadata.get('has_tests', False):
                score *= self.quality_factors['has_tests']
            
            # Prefer functions with clear names
            if chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD]:
                func_name = chunk.metadata.get('function_name', '')
                if any(word in func_name.lower() for word in ['test', 'helper', 'util']):
                    if 'test' in func_name.lower():
                        score *= 1.1  # Tests are good for examples
                    else:
                        score *= 1.05  # Utilities are moderately useful
        
        # Factor in content length (prefer substantial implementations)
        content_length = len(chunk.content)
        if content_length > 500:
            score *= 1.1
        elif content_length < 50:
            score *= 0.9
        
        return min(score, 2.0)  # Cap at 2.0

    async def _calculate_context_score(self, result: SearchResult, query: RetrievalQuery) -> float:
        """Calculate context relevance score"""
        score = 1.0
        
        # Factor in context chunks
        if result.context_chunks:
            score *= 1.1
        
        # Factor in query context
        if query.agent_context:
            # If query is from a specific agent type, prefer relevant content
            agent_role = query.agent_context.get('role')
            if agent_role == 'code_generator' and result.chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD]:
                score *= 1.2
            elif agent_role == 'debugger' and 'error' in result.chunk.content.lower():
                score *= 1.3
        
        # Factor in file relevance
        current_files = query.agent_context.get('current_files', [])
        if current_files and result.chunk.file_path in current_files:
            score *= 1.15
        
        return score

    def filter_duplicates(self, results: List[SearchResult], similarity_threshold: float = 0.95) -> List[SearchResult]:
        """Remove near-duplicate results"""
        filtered_results = []
        seen_content_hashes = set()
        
        for result in results:
            content_hash = hash(result.chunk.content)
            
            # Check for exact duplicates
            if content_hash in seen_content_hashes:
                continue
            
            # Check for semantic duplicates
            is_duplicate = False
            for existing in filtered_results:
                if (result.chunk.file_path == existing.chunk.file_path and 
                    abs(result.chunk.start_line - existing.chunk.start_line) < 5):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_results.append(result)
                seen_content_hashes.add(content_hash)
        
        return filtered_results


class RAGPipeline:
    """
    Main RAG pipeline that orchestrates retrieval and augmentation
    """
    
    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        mcp_clients: Dict[str, Any],
        max_context_tokens: int = 4000
    ):
        self.embedding_engine = embedding_engine
        self.mcp_clients = mcp_clients
        self.max_context_tokens = max_context_tokens
        
        # Initialize components
        self.query_expander = QueryExpander(embedding_engine)
        self.context_ranker = ContextRanker()
        
        # Repository chunks cache
        self.repository_chunks: Dict[str, List[CodeChunk]] = {}
        self.last_update: Dict[str, datetime] = {}
        
        # Context cache for performance
        self.context_cache: Dict[str, RetrievalResult] = {}
        self.cache_ttl = timedelta(hours=1)

    async def retrieve_context(
        self,
        query: RetrievalQuery,
        repository_chunks: Optional[List[CodeChunk]] = None
    ) -> RetrievalResult:
        """Main retrieval method that orchestrates the RAG pipeline"""
        start_time = datetime.now()
        
        # Check cache first
        cache_key = self._generate_cache_key(query)
        if cache_key in self.context_cache:
            cached_result = self.context_cache[cache_key]
            if datetime.now() - datetime.fromisoformat(cached_result.metadata['created_at']) < self.cache_ttl:
                logger.debug(f"Returning cached result for query: {query.query[:50]}...")
                return cached_result

        # Get repository chunks
        if repository_chunks is None:
            repository_chunks = await self._get_repository_chunks()
        
        # Execute retrieval strategy
        if query.strategy == RetrievalStrategy.SEMANTIC_SEARCH:
            raw_results = await self._semantic_search(query, repository_chunks)
        elif query.strategy == RetrievalStrategy.HYBRID_SEARCH:
            raw_results = await self._hybrid_search(query, repository_chunks)
        elif query.strategy == RetrievalStrategy.HIERARCHICAL_SEARCH:
            raw_results = await self._hierarchical_search(query, repository_chunks)
        else:
            # Default to semantic search
            raw_results = await self._semantic_search(query, repository_chunks)
        
        # Rank and filter results
        ranked_results = await self.context_ranker.rank_results(raw_results, query)
        filtered_results = self.context_ranker.filter_duplicates(ranked_results)
        
        # Limit results
        final_results = filtered_results[:query.max_results]
        
        # Generate augmented context
        augmented_context = await self._generate_augmented_context(final_results, query)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        total_tokens = sum(
            self.embedding_engine.chunker.estimate_tokens(result.chunk.content) 
            for result in final_results
        )
        confidence_score = self._calculate_confidence_score(final_results)
        
        # Create result
        result = RetrievalResult(
            query=query,
            chunks=final_results,
            augmented_context=augmented_context,
            metadata={
                'created_at': datetime.now().isoformat(),
                'repository_chunks_count': len(repository_chunks),
                'query_expansion_used': query.expand_query,
                'filters_applied': {
                    'languages': query.filter_languages,
                    'file_patterns': query.filter_file_patterns,
                    'metadata_filters': query.metadata_filters
                }
            },
            processing_time_ms=processing_time,
            total_tokens=total_tokens,
            confidence_score=confidence_score,
            retrieval_strategy_used=query.strategy.value,
            sources=[result.chunk.file_path for result in final_results]
        )
        
        # Cache result
        self.context_cache[cache_key] = result
        
        logger.info(
            f"RAG retrieval completed: {len(final_results)} results, "
            f"{processing_time:.1f}ms, confidence: {confidence_score:.2f}"
        )
        
        return result

    async def _semantic_search(self, query: RetrievalQuery, chunks: List[CodeChunk]) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        results = []
        
        # Expand query if requested
        if query.expand_query:
            expanded_queries = await self.query_expander.expand_query(query.query, query.context_types)
        else:
            expanded_queries = [query.query]
        
        # Search with each expanded query
        all_results = []
        for expanded_query in expanded_queries:
            query_results = await self.embedding_engine.search_similar(
                query=expanded_query,
                chunks=chunks,
                top_k=query.max_results * 2,  # Get more for ranking
                similarity_threshold=query.similarity_threshold,
                filter_by_type=self._get_chunk_type_filters(query.context_types),
                filter_by_language=query.filter_languages or None
            )
            all_results.extend(query_results)
        
        # Remove duplicates and apply additional filters
        seen_ids = set()
        for result in all_results:
            if result.chunk.id not in seen_ids:
                if await self._passes_filters(result.chunk, query):
                    results.append(result)
                    seen_ids.add(result.chunk.id)
        
        return results

    async def _hybrid_search(self, query: RetrievalQuery, chunks: List[CodeChunk]) -> List[SearchResult]:
        """Combine semantic search with keyword matching"""
        # Start with semantic search
        semantic_results = await self._semantic_search(query, chunks)
        
        # Add keyword-based results
        keyword_results = await self._keyword_search(query, chunks)
        
        # Merge results, giving priority to semantic matches
        combined_results = []
        semantic_ids = {result.chunk.id for result in semantic_results}
        
        # Add semantic results first
        combined_results.extend(semantic_results)
        
        # Add keyword results that aren't already included
        for result in keyword_results:
            if result.chunk.id not in semantic_ids:
                combined_results.append(result)
        
        return combined_results

    async def _hierarchical_search(self, query: RetrievalQuery, chunks: List[CodeChunk]) -> List[SearchResult]:
        """Search hierarchically from file -> class -> function level"""
        results = []
        
        # First, find relevant files
        file_chunks = [chunk for chunk in chunks if chunk.chunk_type == ChunkType.FILE]
        file_results = await self.embedding_engine.search_similar(
            query=query.query,
            chunks=file_chunks,
            top_k=5,
            similarity_threshold=query.similarity_threshold * 0.8  # Lower threshold for files
        )
        
        # For each relevant file, search within its contents
        for file_result in file_results:
            file_path = file_result.chunk.file_path
            file_specific_chunks = [chunk for chunk in chunks if chunk.file_path == file_path]
            
            file_specific_results = await self.embedding_engine.search_similar(
                query=query.query,
                chunks=file_specific_chunks,
                top_k=query.max_results // len(file_results) + 1,
                similarity_threshold=query.similarity_threshold,
                filter_by_type=self._get_chunk_type_filters(query.context_types)
            )
            
            results.extend(file_specific_results)
        
        return results

    async def _keyword_search(self, query: RetrievalQuery, chunks: List[CodeChunk]) -> List[SearchResult]:
        """Simple keyword-based search as fallback"""
        results = []
        query_terms = self.query_expander.extract_key_terms(query.query)
        query_words = query.query.lower().split()
        
        for chunk in chunks:
            if not await self._passes_filters(chunk, query):
                continue
            
            content_lower = chunk.content.lower()
            score = 0.0
            
            # Score based on exact matches
            for word in query_words:
                if word in content_lower:
                    score += 0.1
            
            # Score based on technical terms
            for term in query_terms:
                if term.lower() in content_lower:
                    score += 0.2
            
            # Bonus for function/class names
            if chunk.metadata:
                if chunk.metadata.get('function_name', '').lower() in query.query.lower():
                    score += 0.5
                if chunk.metadata.get('class_name', '').lower() in query.query.lower():
                    score += 0.5
            
            if score > 0.3:  # Minimum threshold
                result = SearchResult(
                    chunk=chunk,
                    similarity_score=score,
                    explanation=f"Keyword match score: {score:.2f}"
                )
                results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results

    async def _get_repository_chunks(self) -> List[CodeChunk]:
        """Get all repository chunks from cache or MCP service"""
        # This would integrate with the MCP context service
        # For now, return empty list - would be populated by the repository indexing system
        return []

    async def _generate_augmented_context(self, results: List[SearchResult], query: RetrievalQuery) -> str:
        """Generate augmented context from search results"""
        if not results:
            return "No relevant context found."
        
        context_parts = []
        
        # Add query context
        context_parts.append(f"## Context for: {query.query}\n")
        
        # Group results by type
        by_type = {}
        for result in results:
            chunk_type = result.chunk.chunk_type.value
            if chunk_type not in by_type:
                by_type[chunk_type] = []
            by_type[chunk_type].append(result)
        
        # Add each type section
        for chunk_type, type_results in by_type.items():
            context_parts.append(f"\n### {chunk_type.title()} Examples\n")
            
            for i, result in enumerate(type_results[:3], 1):  # Limit to top 3 per type
                chunk = result.chunk
                context_parts.append(f"\n#### {i}. {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})")
                context_parts.append(f"Similarity: {result.similarity_score:.3f}")
                
                if chunk.metadata:
                    if chunk.metadata.get('function_name'):
                        context_parts.append(f"Function: {chunk.metadata['function_name']}")
                    elif chunk.metadata.get('class_name'):
                        context_parts.append(f"Class: {chunk.metadata['class_name']}")
                
                # Add truncated content
                content = chunk.content
                if len(content) > 500:
                    content = content[:500] + "..."
                
                context_parts.append(f"\n```{chunk.language}\n{content}\n```\n")
        
        # Add summary
        context_parts.append("\n### Summary")
        context_parts.append(f"Found {len(results)} relevant code examples across {len(set(r.chunk.file_path for r in results))} files.")
        
        return '\n'.join(context_parts)

    def _get_chunk_type_filters(self, context_types: List[ContextType]) -> List[ChunkType]:
        """Convert context types to chunk type filters"""
        type_mapping = {
            ContextType.CODE_IMPLEMENTATION: [ChunkType.FUNCTION, ChunkType.METHOD, ChunkType.CLASS],
            ContextType.DOCUMENTATION: [ChunkType.DOCSTRING, ChunkType.COMMENT],
            ContextType.CONFIGURATION: [ChunkType.FILE],  # Config files
            ContextType.TEST_CASES: [ChunkType.FUNCTION, ChunkType.METHOD],  # Test functions
        }
        
        chunk_types = set()
        for context_type in context_types:
            chunk_types.update(type_mapping.get(context_type, []))
        
        return list(chunk_types) if chunk_types else None

    async def _passes_filters(self, chunk: CodeChunk, query: RetrievalQuery) -> bool:
        """Check if chunk passes all query filters"""
        # File pattern filters
        if query.filter_file_patterns:
            import fnmatch
            if not any(fnmatch.fnmatch(chunk.file_path, pattern) for pattern in query.filter_file_patterns):
                return False
        
        # Metadata filters
        if query.metadata_filters:
            for key, value in query.metadata_filters.items():
                if chunk.metadata.get(key) != value:
                    return False
        
        return True

    def _generate_cache_key(self, query: RetrievalQuery) -> str:
        """Generate cache key for query"""
        import hashlib
        
        query_data = {
            'query': query.query,
            'context_types': [ct.value for ct in query.context_types],
            'strategy': query.strategy.value,
            'max_results': query.max_results,
            'similarity_threshold': query.similarity_threshold,
            'filter_languages': query.filter_languages,
            'filter_file_patterns': query.filter_file_patterns
        }
        
        query_str = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()

    def _calculate_confidence_score(self, results: List[SearchResult]) -> float:
        """Calculate overall confidence in retrieval results"""
        if not results:
            return 0.0
        
        # Average similarity score
        avg_similarity = sum(result.similarity_score for result in results) / len(results)
        
        # Factor in result count
        count_factor = min(len(results) / 5, 1.0)  # Optimal around 5 results
        
        # Factor in diversity (different files/types)
        unique_files = len(set(result.chunk.file_path for result in results))
        unique_types = len(set(result.chunk.chunk_type for result in results))
        diversity_factor = min((unique_files + unique_types) / 10, 1.0)
        
        confidence = avg_similarity * 0.6 + count_factor * 0.2 + diversity_factor * 0.2
        
        return min(confidence, 1.0)

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get RAG pipeline statistics"""
        return {
            'cache_size': len(self.context_cache),
            'cache_hit_rate': 0,  # Would track in production
            'avg_processing_time_ms': 0,  # Would track in production
            'total_retrievals': 0,  # Would track in production
            'max_context_tokens': self.max_context_tokens
        }

    def clear_cache(self):
        """Clear the context cache"""
        self.context_cache.clear()
        logger.info("RAG pipeline cache cleared")

    async def create_context_window(
        self,
        retrieval_result: RetrievalResult,
        agent_memory: Optional[AgentMemory] = None
    ) -> ContextWindow:
        """Create a context window for agent consumption"""
        # Extract different types of context
        code_examples = []
        relevant_files = []
        patterns = []
        
        for result in retrieval_result.chunks:
            chunk = result.chunk
            
            if chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD, ChunkType.CLASS]:
                code_examples.append(chunk.content)
            
            if chunk.file_path not in relevant_files:
                relevant_files.append(chunk.file_path)
            
            # Extract patterns from metadata
            if chunk.metadata:
                if 'design_pattern' in chunk.metadata:
                    patterns.append(chunk.metadata['design_pattern'])
        
        # Generate supporting context
        supporting_context = []
        for result in retrieval_result.chunks[3:]:  # Supporting examples
            supporting_context.append(
                f"{result.chunk.file_path}: {result.chunk.content[:200]}..."
            )
        
        # Calculate confidence scores
        confidence_scores = {
            'retrieval_quality': retrieval_result.confidence_score,
            'context_completeness': min(len(code_examples) / 3, 1.0),
            'diversity_score': min(len(relevant_files) / 5, 1.0)
        }
        
        return ContextWindow(
            primary_context=retrieval_result.augmented_context,
            supporting_context=supporting_context,
            code_examples=code_examples,
            relevant_files=relevant_files,
            related_patterns=patterns,
            metadata={
                'query': retrieval_result.query.query,
                'total_results': len(retrieval_result.chunks),
                'processing_time_ms': retrieval_result.processing_time_ms,
                'strategy_used': retrieval_result.retrieval_strategy_used
            },
            confidence_scores=confidence_scores
        )


# Factory function for easy creation
def create_rag_pipeline(
    embedding_model: str = "all-mpnet-base-v2",
    mcp_clients: Optional[Dict[str, Any]] = None,
    max_context_tokens: int = 4000
) -> RAGPipeline:
    """Create a configured RAG pipeline"""
    embedding_engine = EmbeddingEngine(embedding_model=embedding_model)
    
    return RAGPipeline(
        embedding_engine=embedding_engine,
        mcp_clients=mcp_clients or {},
        max_context_tokens=max_context_tokens
    )
