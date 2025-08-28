-- Sophia AI Initial Development Data
-- Seeds file for local development environment

BEGIN;

-- Insert default organization
INSERT INTO organizations (name, slug, description, settings) VALUES 
('Sophia AI Development', 'sophia-dev', 'Default development organization', '{"theme": "dark", "timezone": "UTC"}')
ON CONFLICT (slug) DO NOTHING;

-- Insert default admin user (password: admin123)
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, email_verified) VALUES 
('admin@sophia.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBmdlyDWhzHRru', 'Admin', 'User', 'admin', true, true),
('dev@sophia.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBmdlyDWhzHRru', 'Developer', 'User', 'user', true, true)
ON CONFLICT (email) DO NOTHING;

-- Add users to organization
INSERT INTO organization_members (organization_id, user_id, role, permissions)
SELECT 
    o.id,
    u.id,
    CASE WHEN u.role = 'admin' THEN 'owner' ELSE 'member' END,
    CASE WHEN u.role = 'admin' THEN '["admin", "read", "write", "delete"]'::jsonb ELSE '["read", "write"]'::jsonb END
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' 
AND u.email IN ('admin@sophia.local', 'dev@sophia.local')
ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Insert sample AI agents
INSERT INTO agents (organization_id, name, description, type, config, model, system_prompt, created_by)
SELECT 
    o.id,
    'General Assistant',
    'A helpful AI assistant for general inquiries and tasks',
    'assistant',
    '{"temperature": 0.7, "max_tokens": 2000}'::jsonb,
    'gpt-4',
    'You are a helpful AI assistant. Be concise, accurate, and friendly in your responses.',
    u.id
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' AND u.email = 'admin@sophia.local'
ON CONFLICT DO NOTHING;

INSERT INTO agents (organization_id, name, description, type, config, model, system_prompt, created_by)
SELECT 
    o.id,
    'Code Assistant',
    'Specialized AI assistant for coding and development tasks',
    'assistant',
    '{"temperature": 0.3, "max_tokens": 4000}'::jsonb,
    'gpt-4',
    'You are an expert software developer. Help with coding, debugging, architecture, and best practices. Provide clear, well-commented code examples.',
    u.id
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' AND u.email = 'admin@sophia.local'
ON CONFLICT DO NOTHING;

INSERT INTO agents (organization_id, name, description, type, config, model, system_prompt, created_by)
SELECT 
    o.id,
    'Research Assistant',
    'AI assistant specialized in research and analysis tasks',
    'assistant',
    '{"temperature": 0.5, "max_tokens": 3000}'::jsonb,
    'gpt-4',
    'You are a research assistant. Help with information gathering, analysis, and providing well-sourced insights. Always cite sources when possible.',
    u.id
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' AND u.email = 'admin@sophia.local'
ON CONFLICT DO NOTHING;

-- Insert sample knowledge base
INSERT INTO knowledge_bases (organization_id, name, description, type, config, created_by)
SELECT 
    o.id,
    'Development Documentation',
    'Documentation and guides for Sophia AI development',
    'vector',
    '{"chunk_size": 1000, "overlap": 200, "embedding_model": "text-embedding-ada-002"}'::jsonb,
    u.id
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' AND u.email = 'admin@sophia.local'
ON CONFLICT DO NOTHING;

-- Insert sample documents
INSERT INTO documents (knowledge_base_id, title, content, content_type, metadata, created_by)
SELECT 
    kb.id,
    'Getting Started with Sophia AI',
    'Sophia AI is a comprehensive AI platform that provides intelligent automation and assistance capabilities. This guide covers the basic concepts and how to get started with the platform.

Key Features:
- Multi-agent AI systems
- Knowledge management
- Workflow automation
- Integration capabilities
- Real-time collaboration

To begin using Sophia AI, create an account and set up your organization. Then you can start creating AI agents tailored to your specific needs.',
    'text/markdown',
    '{"category": "documentation", "tags": ["getting-started", "overview"]}'::jsonb,
    u.id
FROM knowledge_bases kb, users u, organizations o
WHERE kb.name = 'Development Documentation' 
AND u.email = 'admin@sophia.local'
AND o.slug = 'sophia-dev'
AND kb.organization_id = o.id
ON CONFLICT DO NOTHING;

INSERT INTO documents (knowledge_base_id, title, content, content_type, metadata, created_by)
SELECT 
    kb.id,
    'API Reference Guide',
    'Sophia AI REST API Reference

Base URL: https://api.sophia.local/v1

Authentication:
All API requests require authentication via API key or JWT token.

Endpoints:
- GET /agents - List all agents
- POST /agents - Create a new agent
- GET /agents/{id} - Get agent details
- PUT /agents/{id} - Update agent
- DELETE /agents/{id} - Delete agent

- GET /conversations - List conversations
- POST /conversations - Create conversation
- POST /conversations/{id}/messages - Send message

Rate Limits:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated requests',
    'text/markdown',
    '{"category": "api", "tags": ["api", "reference", "endpoints"]}'::jsonb,
    u.id
FROM knowledge_bases kb, users u, organizations o
WHERE kb.name = 'Development Documentation' 
AND u.email = 'admin@sophia.local'
AND o.slug = 'sophia-dev'
AND kb.organization_id = o.id
ON CONFLICT DO NOTHING;

-- Insert sample conversation
INSERT INTO conversations (organization_id, agent_id, user_id, title, metadata)
SELECT 
    o.id,
    a.id,
    u.id,
    'Welcome Conversation',
    '{"source": "web", "ip": "127.0.0.1"}'::jsonb
FROM organizations o, agents a, users u 
WHERE o.slug = 'sophia-dev' 
AND a.name = 'General Assistant' 
AND u.email = 'dev@sophia.local'
ON CONFLICT DO NOTHING;

-- Insert sample messages
INSERT INTO messages (conversation_id, role, content, metadata, token_count)
SELECT 
    c.id,
    'user',
    'Hello! Can you help me understand how to use Sophia AI?',
    '{"timestamp": "2024-11-28T12:00:00Z"}'::jsonb,
    15
FROM conversations c
WHERE c.title = 'Welcome Conversation'
ON CONFLICT DO NOTHING;

INSERT INTO messages (conversation_id, role, content, metadata, token_count)
SELECT 
    c.id,
    'assistant',
    'Hello! I''d be happy to help you understand Sophia AI. Sophia AI is a comprehensive platform that provides intelligent automation and AI assistance capabilities. 

Here are the key things you can do:
1. Create and manage AI agents for different tasks
2. Build knowledge bases with your documents and data
3. Set up automated workflows
4. Integrate with various external services
5. Collaborate with team members

What specific aspect would you like to explore first?',
    '{"timestamp": "2024-11-28T12:00:05Z", "model": "gpt-4"}'::jsonb,
    95
FROM conversations c
WHERE c.title = 'Welcome Conversation'
ON CONFLICT DO NOTHING;

-- Insert sample workflow
INSERT INTO workflows (organization_id, name, description, definition, trigger_config, created_by)
SELECT 
    o.id,
    'Welcome New Users',
    'Automatically welcome new users and provide getting started information',
    '{
        "steps": [
            {
                "id": "1",
                "type": "trigger",
                "config": {"event": "user_registered"}
            },
            {
                "id": "2", 
                "type": "send_email",
                "config": {
                    "template": "welcome_email",
                    "to": "{{user.email}}"
                }
            },
            {
                "id": "3",
                "type": "create_conversation", 
                "config": {
                    "agent_id": "{{agents.general_assistant.id}}",
                    "initial_message": "Welcome to Sophia AI! I''m here to help you get started."
                }
            }
        ]
    }'::jsonb,
    '{"events": ["user_registered"], "conditions": []}'::jsonb,
    u.id
FROM organizations o, users u 
WHERE o.slug = 'sophia-dev' AND u.email = 'admin@sophia.local'
ON CONFLICT DO NOTHING;

-- Insert sample API key for development
INSERT INTO api_keys (user_id, key_name, key_hash, permissions, expires_at)
SELECT 
    u.id,
    'Development API Key',
    '$2b$12$dev.api.key.hash.for.local.development.only',
    '["read", "write", "agents", "conversations"]'::jsonb,
    CURRENT_TIMESTAMP + INTERVAL '1 year'
FROM users u 
WHERE u.email = 'dev@sophia.local'
ON CONFLICT (key_hash) DO NOTHING;

COMMIT;

-- Display summary
\echo 'Seed data inserted successfully!'
\echo ''
\echo 'Default users created:'
\echo '- admin@sophia.local (password: admin123) - Admin role'
\echo '- dev@sophia.local (password: admin123) - User role'
\echo ''
\echo 'Sample data includes:'
\echo '- 3 AI agents (General, Code, Research assistants)'
\echo '- 1 knowledge base with 2 sample documents'
\echo '- 1 sample conversation with messages'
\echo '- 1 sample workflow'
\echo '- API keys for development'
\echo ''
\echo 'Organization: Sophia AI Development (sophia-dev)'