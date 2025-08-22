-- Memory Architecture Schema for Sophia AI
-- Supports session, project, and organizational memory layers

-- Session-level memory for conversation tracking
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_type VARCHAR(50) NOT NULL DEFAULT 'chat', -- 'chat', 'workflow', 'debug'
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'completed', 'archived'
    context_summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexing for fast lookups
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_status (status),
    INDEX idx_sessions_created_at (created_at),
    INDEX idx_sessions_type_status (session_type, status)
);

-- Session interactions for detailed conversation history
CREATE TABLE IF NOT EXISTS session_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- 'user_message', 'assistant_response', 'system_event'
    content TEXT NOT NULL,
    intent_analysis JSONB, -- Structured intent data from prompt enhancer
    context_used JSONB, -- Context that was used for this interaction
    metadata JSONB DEFAULT '{}',
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    INDEX idx_interactions_session_id (session_id),
    INDEX idx_interactions_created_at (created_at),
    INDEX idx_interactions_type (interaction_type)
);

-- Project-level memory for code and task context
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    repository_url VARCHAR(500),
    main_branch VARCHAR(100) DEFAULT 'main',
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'archived', 'deprecated'
    tech_stack JSONB DEFAULT '[]', -- Technologies used
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_projects_name (name),
    INDEX idx_projects_status (status)
);

-- Symbol index for code entities across projects
CREATE TABLE IF NOT EXISTS symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    symbol_type VARCHAR(50) NOT NULL, -- 'function', 'class', 'interface', 'variable', 'constant'
    name VARCHAR(255) NOT NULL,
    qualified_name VARCHAR(1000), -- Full namespace path
    file_path VARCHAR(1000) NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    language VARCHAR(50) NOT NULL,
    content TEXT, -- Symbol content/signature
    documentation TEXT, -- Extracted docstrings/comments
    chunk_id VARCHAR(100) NOT NULL, -- Stable identifier for embeddings
    embedding_vector VECTOR(1536), -- OpenAI embedding dimension
    dependencies JSONB DEFAULT '[]', -- List of other symbols this depends on
    dependents JSONB DEFAULT '[]', -- List of symbols that depend on this
    complexity_score FLOAT DEFAULT 0.0,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(project_id, chunk_id),
    
    -- Indexing
    INDEX idx_symbols_project_id (project_id),
    INDEX idx_symbols_name (name),
    INDEX idx_symbols_type (symbol_type),
    INDEX idx_symbols_file_path (file_path),
    INDEX idx_symbols_chunk_id (chunk_id),
    INDEX idx_symbols_qualified_name (qualified_name)
);

-- Create vector similarity search index for embeddings
CREATE INDEX idx_symbols_embedding_vector ON symbols 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- File-level context for broader code understanding
CREATE TABLE IF NOT EXISTS file_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'source', 'config', 'documentation', 'test'
    language VARCHAR(50),
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 of content
    line_count INTEGER DEFAULT 0,
    size_bytes INTEGER DEFAULT 0,
    summary TEXT, -- AI-generated summary of file purpose
    key_symbols JSONB DEFAULT '[]', -- Important symbols in this file
    imports JSONB DEFAULT '[]', -- Import/require statements
    exports JSONB DEFAULT '[]', -- Export statements
    last_indexed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(project_id, file_path),
    
    -- Indexing
    INDEX idx_file_contexts_project_id (project_id),
    INDEX idx_file_contexts_file_path (file_path),
    INDEX idx_file_contexts_file_type (file_type),
    INDEX idx_file_contexts_content_hash (content_hash),
    INDEX idx_file_contexts_last_indexed (last_indexed)
);

-- Organization-level memory for high-level knowledge and patterns
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255), -- Primary domain/industry
    size VARCHAR(50), -- 'startup', 'small', 'medium', 'large', 'enterprise'
    preferences JSONB DEFAULT '{}', -- Coding standards, preferences, etc.
    knowledge_base JSONB DEFAULT '{}', -- Organizational knowledge and patterns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_organizations_name (name),
    INDEX idx_organizations_domain (domain)
);

-- Knowledge fragments for organizational learning
CREATE TABLE IF NOT EXISTS knowledge_fragments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    fragment_type VARCHAR(50) NOT NULL, -- 'pattern', 'best_practice', 'solution', 'decision', 'lesson_learned'
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    tags JSONB DEFAULT '[]',
    confidence_score FLOAT DEFAULT 0.0, -- How reliable this knowledge is
    usage_count INTEGER DEFAULT 0, -- How often this knowledge has been referenced
    source_type VARCHAR(50), -- 'conversation', 'code_analysis', 'documentation', 'manual'
    source_reference VARCHAR(1000), -- Link back to source
    embedding_vector VECTOR(1536), -- For semantic search
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    INDEX idx_knowledge_org_id (organization_id),
    INDEX idx_knowledge_project_id (project_id),
    INDEX idx_knowledge_type (fragment_type),
    INDEX idx_knowledge_tags USING GIN (tags),
    INDEX idx_knowledge_confidence (confidence_score),
    INDEX idx_knowledge_created_at (created_at)
);

-- Vector search index for knowledge fragments
CREATE INDEX idx_knowledge_embedding_vector ON knowledge_fragments 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- Context relationships for tracking how different pieces relate
CREATE TABLE IF NOT EXISTS context_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_type VARCHAR(50) NOT NULL, -- 'symbol', 'file', 'knowledge', 'session'
    from_id UUID NOT NULL,
    to_type VARCHAR(50) NOT NULL,
    to_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'depends_on', 'similar_to', 'references', 'implements', 'extends'
    strength FLOAT DEFAULT 1.0, -- Relationship strength (0.0 to 1.0)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate relationships
    UNIQUE(from_type, from_id, to_type, to_id, relationship_type),
    
    -- Indexing
    INDEX idx_relationships_from (from_type, from_id),
    INDEX idx_relationships_to (to_type, to_id),
    INDEX idx_relationships_type (relationship_type),
    INDEX idx_relationships_strength (strength)
);

-- Index statistics for monitoring and optimization
CREATE TABLE IF NOT EXISTS index_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    index_type VARCHAR(50) NOT NULL, -- 'full', 'incremental', 'selective'
    symbols_processed INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]',
    git_commit_hash VARCHAR(40),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    
    -- Indexing
    INDEX idx_index_stats_project_id (project_id),
    INDEX idx_index_stats_started_at (started_at),
    INDEX idx_index_stats_status (status)
);

-- Views for common queries
CREATE OR REPLACE VIEW recent_sessions AS
SELECT 
    s.*,
    COUNT(si.id) as interaction_count,
    MAX(si.created_at) as last_interaction
FROM sessions s
LEFT JOIN session_interactions si ON s.id = si.session_id
WHERE s.created_at > NOW() - INTERVAL '30 days'
GROUP BY s.id
ORDER BY s.updated_at DESC;

CREATE OR REPLACE VIEW project_symbol_summary AS
SELECT 
    p.name as project_name,
    p.id as project_id,
    COUNT(s.id) as total_symbols,
    COUNT(DISTINCT s.file_path) as files_with_symbols,
    COUNT(DISTINCT s.language) as languages_used,
    MAX(s.last_modified) as last_symbol_update
FROM projects p
LEFT JOIN symbols s ON p.id = s.project_id
WHERE p.status = 'active'
GROUP BY p.id, p.name
ORDER BY total_symbols DESC;

-- Functions for common operations
CREATE OR REPLACE FUNCTION generate_chunk_id(
    p_project_id UUID,
    p_file_path VARCHAR,
    p_symbol_name VARCHAR,
    p_start_line INTEGER
) RETURNS VARCHAR AS $$
BEGIN
    -- Generate stable chunk ID based on project, file, symbol, and position
    RETURN encode(
        digest(
            p_project_id::text || '|' || 
            p_file_path || '|' || 
            p_symbol_name || '|' || 
            p_start_line::text, 
            'sha256'
        ), 
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION update_symbol_dependencies(
    p_symbol_id UUID,
    p_dependencies JSONB
) RETURNS VOID AS $$
DECLARE
    dep_chunk_id VARCHAR;
    dep_symbol_id UUID;
BEGIN
    -- Update the symbol's dependencies
    UPDATE symbols SET dependencies = p_dependencies WHERE id = p_symbol_id;
    
    -- Update reverse dependencies for all referenced symbols
    FOR dep_chunk_id IN SELECT jsonb_array_elements_text(p_dependencies)
    LOOP
        SELECT id INTO dep_symbol_id FROM symbols WHERE chunk_id = dep_chunk_id;
        
        IF dep_symbol_id IS NOT NULL THEN
            UPDATE symbols 
            SET dependents = COALESCE(dependents, '[]'::jsonb) || jsonb_build_array(
                (SELECT chunk_id FROM symbols WHERE id = p_symbol_id)
            )
            WHERE id = dep_symbol_id
            AND NOT dependents ? (SELECT chunk_id FROM symbols WHERE id = p_symbol_id);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining data consistency
CREATE OR REPLACE FUNCTION update_modified_time() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER trigger_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER trigger_knowledge_fragments_updated_at
    BEFORE UPDATE ON knowledge_fragments
    FOR EACH ROW EXECUTE FUNCTION update_modified_time();

-- Initial data
INSERT INTO organizations (name, domain, size, preferences) VALUES 
('Sophia AI Intelligence', 'artificial_intelligence', 'startup', '{
    "coding_standards": {
        "typescript": {"style": "standard", "strict": true},
        "python": {"style": "pep8", "type_hints": true},
        "documentation": {"required": true, "format": "markdown"}
    },
    "architecture": {
        "microservices": true,
        "event_driven": true,
        "proof_first": true
    }
}') ON CONFLICT (name) DO NOTHING;

-- Insert default project
INSERT INTO projects (name, description, repository_url, tech_stack) VALUES 
('sophia-ai-intel', 'Sophia AI Intelligence System', 'https://github.com/ai-cherry/sophia-ai-intel', '[
    "typescript", "python", "react", "postgresql", "qdrant", "redis", "fly.io"
]') ON CONFLICT (name) DO NOTHING;

-- Performance optimization: Create partial indexes for active records
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_sessions 
ON sessions (user_id, created_at) WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_projects_symbols 
ON symbols (project_id, name) WHERE project_id IN (
    SELECT id FROM projects WHERE status = 'active'
);

-- Enable row level security (optional, for multi-tenant scenarios)
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE symbols ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE sessions IS 'Session-level memory for conversation and workflow tracking';
COMMENT ON TABLE symbols IS 'Code symbol index with embeddings for semantic search';
COMMENT ON TABLE knowledge_fragments IS 'Organizational knowledge base with semantic search capabilities';
COMMENT ON TABLE context_relationships IS 'Graph relationships between different context entities';