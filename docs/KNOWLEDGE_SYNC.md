# Knowledge Sync Documentation

## Overview

The Sophia AI Intelligence System maintains a comprehensive knowledge sync pipeline that integrates external knowledge sources into the semantic search infrastructure. This system enables the AI to access and reason over organizational knowledge, OKRs, and domain expertise in real-time.

## Architecture

### Core Components

1. **Notion Integration**: Primary knowledge source via Notion API
2. **Database Storage**: PostgreSQL with vector embeddings via [`libs/memory/schema.sql`](../libs/memory/schema.sql)
3. **Embedding Pipeline**: OpenAI text-embedding-3-small (1536 dimensions)
4. **Qdrant Sync**: Vector database for semantic search
5. **Context MCP Integration**: Real-time knowledge access via [`services/mcp-context`](../services/mcp-context/)

### Workflow Trigger

```yaml
# Automated: Nightly at 2 AM UTC
schedule:
  - cron: '0 2 * * *'

# Manual: On-demand sync with options
workflow_dispatch:
  inputs:
    sync_type: [incremental, full]
    force_embed: [true, false]
```

## Database Schema

### Knowledge Tables

#### `knowledge_fragments` Table
Primary storage for knowledge content with vector embeddings:

```sql
CREATE TABLE knowledge_fragments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    fragment_type knowledge_fragment_type NOT NULL,  -- 'knowledge', 'okr', 'process'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags JSONB DEFAULT '[]',
    confidence_score FLOAT DEFAULT 0.0,
    source_type TEXT NOT NULL,  -- 'notion', 'manual', 'imported'
    source_reference TEXT,     -- URL or identifier
    embedding_vector vector(1536),
    created_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, title)
);
```

#### Supporting Indexes
```sql
-- Semantic search optimization
CREATE INDEX idx_knowledge_fragments_embedding_vector 
ON knowledge_fragments USING ivfflat (embedding_vector vector_cosine_ops);

-- Text search optimization
CREATE INDEX idx_knowledge_fragments_content_fts 
ON knowledge_fragments USING gin(to_tsvector('english', content));

-- Type and source filtering
CREATE INDEX idx_knowledge_fragments_type_source 
ON knowledge_fragments(fragment_type, source_type);
```

### OKR-Specific Storage

#### Fragment Type: `'okr'`
OKRs are stored as specialized knowledge fragments with structured tags:

```json
{
  "type": "okr",
  "quarter": "2024-Q4",
  "objective_id": "obj-1",
  "key_result_id": "kr-1.2",
  "status": "on_track",
  "completion": 0.75,
  "department": "engineering"
}
```

## Sync Process

### Notion API Integration

#### Authentication
```bash
# Required GitHub Secrets
NOTION_API_KEY=secret_xxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Optional
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Page Extraction Pipeline
1. **Discovery**: Query Notion database or search for "knowledge" pages
2. **Content Extraction**: Parse blocks (paragraphs, headings, lists, code)
3. **Metadata Extraction**: Title, last_edited_time, properties
4. **Embedding Generation**: OpenAI text-embedding-3-small
5. **Storage**: Upsert to `knowledge_fragments` table

### Content Processing

#### Supported Notion Block Types
- `paragraph`: Plain text content
- `heading_1/2/3`: Structured headings
- `bulleted_list_item`: Bullet point lists
- `numbered_list_item`: Numbered lists  
- `quote`: Blockquote content
- `code`: Code blocks with language detection

#### Content Chunking Strategy
```python
# Maximum content length for embeddings
max_length = 8000  # characters

# Truncation strategy
if len(text) > max_length:
    text = text[:max_length] + "..."
```

### Error Handling

#### Normalized Error Format
All sync failures generate standardized proof files:

```json
{
  "status": "failure",
  "query": "Notion knowledge sync integration",
  "results": [],
  "summary": {
    "text": "Notion API key not configured - knowledge sync cannot proceed",
    "confidence": 1.0,
    "model": "n/a",
    "sources": []
  },
  "timestamp": "2024-08-22T23:30:00Z",
  "execution_time_ms": 0,
  "errors": [
    {
      "provider": "notion_api",
      "code": "MISSING_API_KEY",
      "message": "NOTION_API_KEY secret not configured in GitHub Actions"
    }
  ]
}
```

## Integration Points

### Context MCP Service

After successful sync, the Context MCP is notified to refresh its knowledge cache:

```bash
curl -X POST "http://localhost:{port}/internal/refresh-knowledge" \
  -H "Content-Type: application/json" \
  -d '{"source": "notion_sync", "timestamp": "2024-08-22T23:30:00Z"}'
```

### Qdrant Vector Database

Knowledge fragments are automatically synced to Qdrant collections:

```python
# Collection configuration
collection_name = "knowledge_fragments"
vector_size = 1536
distance = "Cosine"

# Metadata payload
{
  "fragment_id": "uuid",
  "title": "Page Title",
  "fragment_type": "knowledge",
  "source_type": "notion",
  "tags": ["ai", "documentation"],
  "organization_id": "org-uuid"
}
```

## Quality Assurance

### Validation Pipeline

The workflow includes comprehensive validation:

1. **Configuration Check**: Verify all required secrets are present
2. **Sync Execution**: Process pages with error tracking
3. **Results Validation**: Confirm embeddings and storage success
4. **Proof Generation**: Create audit trail for monitoring

### Monitoring Metrics

```json
{
  "pages_processed": 42,
  "pages_stored": 40,
  "errors": 2,
  "execution_time_ms": 15000,
  "embedding_success_rate": 0.95
}
```

## Usage Examples

### Manual Sync Trigger

```bash
# Full re-sync of all knowledge
gh workflow run notion_sync.yml -f sync_type=full -f force_embed=true

# Incremental sync (default)
gh workflow run notion_sync.yml
```

### Query Knowledge via Context MCP

```python
# Search for specific knowledge
response = await context_mcp.search_knowledge(
    query="deployment procedures",
    limit=5,
    filter={"fragment_type": "knowledge"}
)

# OKR-specific search
okrs = await context_mcp.search_knowledge(
    query="Q4 engineering objectives",
    filter={"fragment_type": "okr", "tags": ["2024-Q4", "engineering"]}
)
```

## Configuration

### Environment Variables

```bash
# Required
NOTION_API_KEY=secret_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SYNC_TYPE=incremental  # or 'full'
```

### Notion Database Setup

#### Required Permissions
- Read content and comments
- Read database content
- Search workspace

#### Recommended Page Properties
- **Title**: Title (required)
- **Tags**: Multi-select (optional)
- **Department**: Select (optional)  
- **Status**: Select (optional)
- **Last Updated**: Last edited time (auto)

## Performance Characteristics

### Sync Performance
- **Typical Runtime**: 30-60 seconds for incremental sync
- **Full Sync**: 2-5 minutes for 100-500 pages
- **Rate Limits**: Notion API (3 requests/second), OpenAI (500 requests/minute)

### Storage Efficiency
- **Embedding Size**: 1536 dimensions × 4 bytes = 6.1KB per fragment
- **Content Compression**: Full-text search indexes with PostgreSQL
- **Deduplication**: Upsert strategy based on organization + title

## Troubleshooting

### Common Issues

#### Missing API Keys
```bash
# Error: NOTION_API_KEY not configured
# Solution: Add to GitHub repository secrets
```

#### Notion API Rate Limiting
```bash
# Error: Too many requests
# Solution: Automatic backoff with exponential retry
```

#### Embedding Generation Failures
```bash
# Error: OpenAI API quota exceeded
# Solution: Cost monitoring and graceful degradation
```

### Debug Commands

```bash
# Check sync artifacts
ls -la proofs/knowledge/

# Validate last sync
jq '.summary' proofs/knowledge/notion_sync_scaffold.json

# Monitor workflow status
gh run list --workflow=notion_sync.yml
```

## Security Considerations

### API Key Management
- Store all keys as GitHub encrypted secrets
- Use environment-specific keys (dev/prod separation)
- Regular key rotation (quarterly recommended)

### Data Privacy
- Knowledge fragments stored in encrypted PostgreSQL
- No PII in embedding vectors
- Organization-level access control

### Access Control
- Workflow restricted to main repository
- Production environment gating
- CEO approval for infrastructure changes

## Roadmap

### Phase 2 Enhancements
- [ ] Multi-source knowledge sync (Confluence, SharePoint)
- [ ] Real-time webhook integration
- [ ] Knowledge graph relationships
- [ ] Automated content classification
- [ ] Usage analytics and optimization

### Performance Optimizations
- [ ] Incremental embedding updates
- [ ] Parallel processing for large syncs  
- [ ] Smart content chunking strategies
- [ ] Embedding model fine-tuning

---

**Related Documentation:**
- [`docs/MEMORY_ARCHITECTURE.md`](./MEMORY_ARCHITECTURE.md) - Memory system overview
- [`docs/SWARM_CHARTER.md`](./SWARM_CHARTER.md) - Distributed intelligence procedures
- [`libs/memory/schema.sql`](../libs/memory/schema.sql) - Database schema
- [`.github/workflows/notion_sync.yml`](../.github/workflows/notion_sync.yml) - Sync workflow implementation