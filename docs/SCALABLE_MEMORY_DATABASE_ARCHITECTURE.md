# 🧠 Sophia AI - Scalable Memory & Database Architecture Plan

**Date**: August 25, 2025  
**Status**: 📋 Implementation Ready  
**Scope**: Enhanced Memory Architecture for Complete Codebase Visibility  

---

## 🎯 Executive Summary

Based on comprehensive analysis of Sophia AI's current memory architecture, this plan upgrades the system to provide the orchestrator and dashboard with complete codebase visibility and contextualized insights. The enhanced architecture addresses current gaps while maintaining scalability for enterprise deployment.

## 📊 Current Architecture Analysis

### **✅ Existing Strengths:**
- **Sophisticated 3-layer memory**: Session → Project → Organization
- **Advanced database schema**: PostgreSQL with pgvector + quality assessment
- **Multi-language code chunking**: AST-based parsing for Python/TypeScript
- **RAG pipeline framework**: Multiple retrieval strategies implemented
- **Quality assessment system**: Confidence scoring and knowledge promotion

### **🔧 Critical Gaps Identified:**
- **Incomplete vector integration**: Qdrant using placeholder embeddings
- **Missing Mem0 integration**: Referenced but not implemented
- **No LlamaIndex support**: Advanced document management missing
- **Basic orchestrator**: Simple HTTP wrapper without memory coordination
- **No real-time context sharing**: Microservices operate in isolation
- **Limited semantic boundaries**: Chunking not optimized for retrieval

---

## 🏗️ Enhanced Scalable Architecture

### **1. Hybrid Vector Database System**

#### **Current State**:
```python
# services/mcp-context/app.py - Line 167
embedding_vector = [0.0] * 1536  # Placeholder implementation
```

#### **Enhanced Implementation**:
```python
class HybridVectorStore:
    """Dual vector database system for optimal performance"""
    
    def __init__(self):
        # Primary: Qdrant for fast semantic search
        self.qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Secondary: PostgreSQL pgvector for complex queries
        self.postgres = asyncpg.create_pool(NEON_DATABASE_URL)
        
        # Mem0 integration for enhanced memory patterns
        self.mem0 = Mem0Client(api_key=MEM0_API_KEY)
        
        # LlamaIndex for document management
        self.llama_index = VectorStoreIndex.from_vector_store(
            QdrantVectorStore(client=self.qdrant, collection_name="sophia_knowledge")
        )
    
    async def store_with_enhancement(self, chunk: CodeChunk):
        """Store in both databases with Mem0 enhancement"""
        # Generate real embeddings
        embedding = await self.embedding_model.encode(chunk.content)
        
        # Store in Qdrant for fast retrieval
        await self.qdrant.upsert(
            collection_name="code_chunks",
            points=[PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "language": chunk.language,
                    "chunk_type": chunk.chunk_type.value
                }
            )]
        )
        
        # Store in PostgreSQL for complex queries
        await self.postgres.execute("""
            INSERT INTO symbols (id, content, embedding_vector, metadata)
            VALUES ($1, $2, $3, $4)
        """, chunk.id, chunk.content, embedding, chunk.metadata)
        
        # Enhance with Mem0 memory patterns
        await self.mem0.add_memory(
            content=chunk.content,
            metadata={
                "chunk_id": chunk.id,
                "memory_type": "code_pattern",
                "context": chunk.metadata
            }
        )
        
        # Index in LlamaIndex for advanced querying
        document = Document(text=chunk.content, metadata=chunk.metadata)
        self.llama_index.insert(document)
```

### **2. Real-Time Memory Coordination**

#### **Enhanced Orchestrator Service**:
```typescript
// services/orchestrator/memory-coordinator.ts
class MemoryCoordinator {
    private redisClient: Redis;
    private mcpClients: Map<string, McpClient>;
    private contextCache: LRUCache<string, ContextWindow>;
    
    constructor() {
        this.redisClient = new Redis(process.env.REDIS_URL);
        this.mcpClients = new Map([
            ['context', new McpClient('http://sophia-context:8080')],
            ['research', new McpClient('http://sophia-research:8080')],
            ['business', new McpClient('http://sophia-business:8080')]
        ]);
        
        // Distributed context cache
        this.contextCache = new LRUCache({ max: 1000, ttl: 1000 * 60 * 10 });
    }
    
    async getEnhancedContext(query: string, sessionId: string): Promise<EnhancedContext> {
        const cacheKey = `context:${sessionId}:${hashQuery(query)}`;
        
        // Check distributed cache
        let context = await this.redisClient.get(cacheKey);
        if (context) {
            return JSON.parse(context);
        }
        
        // Parallel context retrieval from all services
        const [codeContext, researchContext, businessContext] = await Promise.all([
            this.mcpClients.get('context')?.searchContext(query),
            this.mcpClients.get('research')?.getResearchContext(query),
            this.mcpClients.get('business')?.getBusinessContext(query)
        ]);
        
        // Combine and rank contexts
        const enhancedContext = await this.combineContexts({
            code: codeContext,
            research: researchContext,
            business: businessContext,
            session_history: await this.getSessionHistory(sessionId)
        });
        
        // Cache for future use
        await this.redisClient.setex(cacheKey, 600, JSON.stringify(enhancedContext));
        
        return enhancedContext;
    }
}
```

### **3. Semantic Chunking Optimization**

#### **Enhanced Code Chunker**:
```python
class SemanticCodeChunker:
    """Advanced semantic chunking with Tree-sitter integration"""
    
    def __init__(self):
        self.tree_sitter_languages = {
            'python': Language(tree_sitter_python.language(), 'python'),
            'typescript': Language(tree_sitter_typescript.language(), 'typescript'),
            'javascript': Language(tree_sitter_javascript.language(), 'javascript')
        }
        
        # Semantic boundary detection
        self.boundary_patterns = {
            'function_start': ['def ', 'function ', 'const ', 'async '],
            'class_start': ['class ', 'interface ', 'type '],
            'logical_break': ['# ---', '// ---', '"""', "'''"],
            'dependency_import': ['import ', 'from ', 'require(']
        }
    
    async def chunk_with_semantic_boundaries(self, content: str, language: str) -> List[CodeChunk]:
        """Chunk code respecting semantic boundaries"""
        tree = self.tree_sitter_languages[language].parse(bytes(content, 'utf8'))
        
        chunks = []
        semantic_units = self._extract_semantic_units(tree, content)
        
        for unit in semantic_units:
            # Create chunk with enhanced metadata
            chunk = CodeChunk(
                id=self._generate_semantic_id(unit),
                content=unit.content,
                chunk_type=self._determine_semantic_type(unit),
                language=language,
                file_path=unit.file_path,
                start_line=unit.start_line,
                end_line=unit.end_line,
                metadata={
                    **unit.metadata,
                    'semantic_context': await self._analyze_semantic_context(unit),
                    'dependency_graph': await self._build_dependency_graph(unit),
                    'complexity_metrics': await self._calculate_complexity(unit)
                }
            )
            
            chunks.append(chunk)
        
        return chunks
```

### **4. Enhanced Dashboard Integration**

#### **Real-Time Memory Dashboard**:
```typescript
// apps/dashboard/src/components/MemoryInsights.tsx
interface MemoryInsightsProps {
    sessionId: string;
    currentQuery: string;
}

export const MemoryInsights: React.FC<MemoryInsightsProps> = ({ sessionId, currentQuery }) => {
    const [contextData, setContextData] = useState<EnhancedContext | null>(null);
    const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
    
    // Real-time context updates via WebSocket
    useEffect(() => {
        const ws = new WebSocket(`ws://sophia-orchestrator:8080/memory-stream/${sessionId}`);
        
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            if (update.type === 'context_update') {
                setContextData(update.context);
            } else if (update.type === 'memory_stats') {
                setMemoryStats(update.stats);
            }
        };
        
        return () => ws.close();
    }, [sessionId]);
    
    return (
        <div className="memory-insights">
            <ContextVisualization context={contextData} />
            <CodebaseMap symbols={contextData?.relevant_symbols} />
            <MemoryHealth stats={memoryStats} />
            <SemanticSimilarity query={currentQuery} results={contextData?.similar_chunks} />
        </div>
    );
};
```

### **5. Distributed Context Synchronization**

#### **Redis-Based Context Coordination**:
```python
class DistributedContextManager:
    """Manages context sharing across microservices"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.context_ttl = 3600  # 1 hour
        
    async def sync_context_across_services(self, session_id: str, context: Dict[str, Any]):
        """Synchronize context updates across all microservices"""
        context_key = f"session_context:{session_id}"
        
        # Store in Redis with structured format
        await self.redis.hset(context_key, mapping={
            'code_context': json.dumps(context.get('code', {})),
            'research_context': json.dumps(context.get('research', {})),
            'business_context': json.dumps(context.get('business', {})),
            'agent_memory': json.dumps(context.get('agent_memory', {})),
            'last_updated': time.time()
        })
        
        await self.redis.expire(context_key, self.context_ttl)
        
        # Notify all services of context update
        await self.redis.publish(f"context_updates:{session_id}", json.dumps({
            'type': 'context_sync',
            'session_id': session_id,
            'timestamp': time.time()
        }))
```

---

## 🎯 Implementation Roadmap

### **Phase 1: Vector Database Completion (1-2 weeks)**
1. **Replace Qdrant placeholders** with real OpenAI embeddings
2. **Integrate Mem0** for enhanced memory management
3. **Add LlamaIndex** for document processing and querying
4. **Implement semantic chunking** with Tree-sitter

### **Phase 2: Memory Coordination (1-2 weeks)**
1. **Upgrade orchestrator** to memory coordinator
2. **Implement Redis context sharing** between microservices
3. **Add real-time WebSocket** updates to dashboard
4. **Create context visualization** components

### **Phase 3: Advanced Features (2-3 weeks)**
1. **Cross-service memory queries** and aggregation
2. **Intelligent context pre-loading** and prediction
3. **Advanced dependency tracking** and relationship mapping
4. **Performance optimization** and caching strategies

---

## 📋 Specific Implementation Tasks

### **Immediate Actions (Week 1):**
- Fix Qdrant placeholder embeddings in mcp-context service
- Implement real OpenAI embedding generation
- Add Mem0 client integration for memory management
- Create semantic chunking with Tree-sitter parsers

### **Integration Tasks (Week 2):**
- Enhance orchestrator with memory coordination capabilities
- Implement Redis-based context sharing
- Create dashboard memory insights components
- Add real-time context streaming

### **Advanced Features (Week 3):**
- Cross-service memory aggregation
- Intelligent context prediction
- Performance monitoring and optimization
- Advanced relationship mapping

---

**This architecture will transform Sophia AI into a truly intelligent system with complete codebase visibility and contextualized insights across all microservices and the dashboard.**
