# Memory Architecture - Sophia AI Intelligence System

## Overview

The Sophia AI memory system implements a three-layer architecture designed to provide contextual intelligence across session, project, and organizational levels. The system uses PostgreSQL with vector extensions for semantic search capabilities and tree-sitter for reliable code parsing.

## Architecture Layers

### Layer 1: Session Memory
**Purpose**: Short-term conversation and workflow tracking

**Components**:
- **Sessions**: Individual conversation or workflow instances
- **Interactions**: Detailed interaction history with intent analysis
- **Context Packs**: Enriched context used for each interaction

**Schema**: [`sessions`](../libs/memory/schema.sql), [`session_interactions`](../libs/memory/schema.sql)

**Retention**: 30 days for active sessions, 90 days for archived sessions

### Layer 2: Project Memory  
**Purpose**: Medium-term code context and symbol understanding

**Components**:
- **Projects**: Code repositories and their metadata
- **Symbols**: Functions, classes, interfaces, variables with embeddings
- **File Contexts**: File-level summaries and metadata
- **Dependencies**: Symbol relationship graphs

**Schema**: [`projects`](../libs/memory/schema.sql), [`symbols`](../libs/memory/schema.sql), [`file_contexts`](../libs/memory/schema.sql)

**Retention**: Persistent, updated on code changes

### Layer 3: Organizational Memory
**Purpose**: Long-term knowledge base and pattern recognition

**Components**:
- **Organizations**: High-level organizational context and preferences
- **Knowledge Fragments**: Patterns, decisions, best practices
- **Relationships**: Cross-cutting relationships between all memory layers

**Schema**: [`organizations`](../libs/memory/schema.sql), [`knowledge_fragments`](../libs/memory/schema.sql), [`context_relationships`](../libs/memory/schema.sql)

**Retention**: Permanent with confidence-based aging

## Symbol Indexing System

### Tree-Sitter Integration

The system uses tree-sitter parsers for reliable, language-aware code analysis:

```python
# Supported Languages
LANGUAGES = {
    'python': ['.py'],
    'typescript': ['.ts', '.tsx'], 
    'javascript': ['.js', '.jsx']
}

# Symbol Types Extracted
SYMBOL_TYPES = [
    'function', 'class', 'interface', 'method',
    'variable', 'constant', 'type', 'enum'
]
```

### Stable Chunk IDs

Each symbol gets a stable identifier for consistent embedding updates:

```python
def generate_chunk_id(project_id, file_path, symbol_name, start_line):
    content = f"{project_id}|{file_path}|{symbol_name}|{start_line}"
    return hashlib.sha256(content.encode()).hexdigest()
```

### Embedding Generation

Symbols are converted to semantic embeddings using OpenAI's text-embedding-3-small model:

- **Model**: text-embedding-3-small
- **Dimensions**: 1536 (configurable)
- **Input**: Symbol content + documentation
- **Storage**: PostgreSQL with pgvector extension

## Indexing Workflows

### Incremental Indexing (Automated)

Triggered on every merge to main branch:

```yaml
# .github/workflows/index_on_merge.yml
on:
  push:
    branches: [ main ]
    paths: ['**.py', '**.ts', '**.tsx', '**.js', '**.jsx']
```

**Process**:
1. Detect changed files
2. Parse symbols with tree-sitter
3. Generate/update embeddings
4. Update dependency relationships
5. Generate proof artifacts

### Full Indexing (Manual)

Complete reindexing of entire project:

```bash
python symbol_indexer.py \
  --project-root "./" \
  --project-name "sophia-ai-intel" \
  --index-type "full"
```

**Use Cases**:
- Initial project setup
- Major refactoring completion
- Embedding model changes
- Schema migrations

### Nightly Full Index

Automated comprehensive indexing via existing nightly workflow:

```yaml
# .github/workflows/nightly_smoke.yml
- name: Full symbol index
  run: |
    python services/mcp-context/symbol_indexer.py \
      --index-type full
```

## Search Capabilities

### Semantic Search

Vector similarity search across all symbols:

```sql
SELECT s.*, 
       s.embedding_vector <=> $1 as similarity_score
FROM symbols s
WHERE s.project_id = $2
ORDER BY s.embedding_vector <=> $1
LIMIT 10;
```

### Relationship Traversal

Navigate symbol dependencies and usage patterns:

```sql
WITH RECURSIVE dependency_tree AS (
    SELECT chunk_id, dependencies, 1 as depth
    FROM symbols WHERE chunk_id = $1
    UNION ALL
    SELECT s.chunk_id, s.dependencies, dt.depth + 1
    FROM symbols s
    JOIN dependency_tree dt ON s.chunk_id = ANY(dt.dependencies::text[])
    WHERE dt.depth < 5
)
SELECT * FROM dependency_tree;
```

### Context-Aware Retrieval

Combine multiple signals for optimal context selection:

```sql
SELECT 
    s.*,
    fc.summary as file_summary,
    kf.content as related_knowledge
FROM symbols s
LEFT JOIN file_contexts fc ON s.file_path = fc.file_path
LEFT JOIN knowledge_fragments kf ON kf.tags ? s.symbol_type
WHERE s.embedding_vector <=> $1 < 0.8
ORDER BY s.embedding_vector <=> $1;
```

## Integration Points

### Context MCP Service

The Context MCP service provides the primary interface to the memory system:

```python
# Context MCP endpoints
/search    # Semantic search across symbols
/context   # Get enriched context for prompt enhancement
/index     # Trigger indexing operations
/stats     # Get indexing statistics
```

### Prompt Enhancement Pipeline

Memory system integrates with the prompt enhancement pipeline:

```typescript
// Stage 2: Context Enrichment
const context = await contextMcp.search(request);
const codebaseContext = context.symbols;
const historicalContext = context.conversations;
```

### Dashboard Integration

Memory statistics and search capabilities exposed in dashboard:

- Real-time indexing status
- Symbol statistics by language
- Search interface for developers
- Dependency visualization

## Performance Characteristics

### Indexing Performance

| Language | Symbols/sec | Memory Usage | Embedding Rate |
|----------|-------------|--------------|----------------|
| Python   | ~60         | ~50MB        | ~10/sec        |
| TypeScript | ~45       | ~75MB        | ~10/sec        |
| JavaScript | ~55       | ~60MB        | ~10/sec        |

### Search Performance

| Query Type | Response Time | Results | Accuracy |
|------------|---------------|---------|----------|
| Semantic | <200ms | 10-50 | ~85% |
| Keyword | <50ms | 10-100 | ~95% |
| Relationship | <100ms | 5-20 | ~90% |

### Storage Requirements

| Component | Storage/1000 symbols | Growth Rate |
|-----------|---------------------|-------------|
| Symbols | ~15MB | Linear |
| Embeddings | ~6MB | Linear |
| Relationships | ~2MB | Quadratic (bounded) |

## Monitoring & Maintenance

### Health Metrics

Key metrics tracked in `index_statistics` table:

- **Processing Speed**: symbols/second, files/second
- **Error Rates**: parsing errors, embedding failures
- **Coverage**: percentage of files indexed
- **Freshness**: time since last update

### Automated Maintenance

- **Cleanup**: Remove orphaned symbols and outdated embeddings
- **Optimization**: Rebuild vector indexes periodically
- **Archival**: Move old sessions to cold storage
- **Consistency**: Verify symbol-dependency integrity

### Alert Conditions

- Indexing failure rate >5%
- Search response time >500ms
- Storage usage >80% of allocated
- Embedding API rate limiting

## Security Considerations

### Data Protection

- **No Secrets**: Symbol content filtered for sensitive data
- **Access Control**: Project-based permissions
- **Encryption**: Vector embeddings encrypted at rest
- **Audit Trail**: All search operations logged

### Privacy Compliance

- **Anonymization**: Personal identifiers removed from symbols
- **Retention**: Configurable data retention policies
- **Export**: GDPR-compliant data export capabilities
- **Deletion**: Complete removal of user-specific data

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Add support for Go, Rust, Java
2. **Advanced Relationships**: Control flow and data flow analysis
3. **Collaborative Memory**: Multi-user context sharing
4. **Visual Navigation**: Interactive dependency graphs
5. **Performance Optimization**: Batch embedding generation

### Research Areas

- **Adaptive Chunking**: Dynamic symbol boundary detection
- **Contextual Embeddings**: Position-aware code embeddings
- **Cross-project Learning**: Pattern recognition across repositories
- **Natural Language Queries**: Plain English to semantic search

---

**Architecture Version**: 1.0  
**Last Updated**: 2025-08-22T23:18:00Z  
**Implementation Status**: Complete  
**Performance Target**: <200ms semantic search, 95% indexing accuracy