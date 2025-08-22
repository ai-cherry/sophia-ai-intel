-- Business MCP v1 Database Schema for Neon PostgreSQL
-- Created: 2025-08-22
-- Purpose: GTM/RevOps data storage for companies, contacts, prospects, signals, and uploads

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Companies table - Master company records
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    source VARCHAR(100) NOT NULL, -- apollo, hubspot, salesforce, csv, etc.
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_source ON companies(source);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at);
CREATE INDEX IF NOT EXISTS idx_companies_meta_json ON companies USING GIN(meta_json);

-- Contacts table - Individual contacts within companies
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    source VARCHAR(100) NOT NULL, -- apollo, hubspot, salesforce, usergems, csv, etc.
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for contacts
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_source ON contacts(source);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_meta_json ON contacts USING GIN(meta_json);

-- Prospects table - Qualified leads and prospects with scoring
CREATE TABLE IF NOT EXISTS prospects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    list VARCHAR(100) NOT NULL, -- target list name (e.g., 'q1-multifamily', 'ai-proptech')
    tags TEXT[] DEFAULT '{}', -- prospect tags/categories
    score DECIMAL(5,2) DEFAULT 0.0, -- prospect score (0.00 to 100.00)
    source VARCHAR(100) NOT NULL, -- apollo, hubspot, usergems, manual, etc.
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for prospects
CREATE INDEX IF NOT EXISTS idx_prospects_company_id ON prospects(company_id);
CREATE INDEX IF NOT EXISTS idx_prospects_contact_id ON prospects(contact_id);
CREATE INDEX IF NOT EXISTS idx_prospects_list ON prospects(list);
CREATE INDEX IF NOT EXISTS idx_prospects_score ON prospects(score);
CREATE INDEX IF NOT EXISTS idx_prospects_source ON prospects(source);
CREATE INDEX IF NOT EXISTS idx_prospects_tags ON prospects USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_prospects_created_at ON prospects(created_at);
CREATE INDEX IF NOT EXISTS idx_prospects_meta_json ON prospects USING GIN(meta_json);

-- Signals table - Business intelligence signals and events
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kind VARCHAR(100) NOT NULL, -- job_change, funding_round, tech_stack, hiring, etc.
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for signals
CREATE INDEX IF NOT EXISTS idx_signals_kind ON signals(kind);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_payload_json ON signals USING GIN(payload_json);

-- Uploads table - Track CSV and manual data uploads
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(100) NOT NULL, -- linkedin, costar, nmhc, csv, apollo, hubspot, etc.
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing', -- processing, completed, failed
    row_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create indexes for uploads
CREATE INDEX IF NOT EXISTS idx_uploads_provider ON uploads(provider);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers to tables that need them
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_contacts_updated_at ON contacts;
CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_prospects_updated_at ON prospects;
CREATE TRIGGER update_prospects_updated_at
    BEFORE UPDATE ON prospects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW prospect_summary AS
SELECT 
    p.id,
    p.list,
    p.tags,
    p.score,
    p.source,
    c.name as company_name,
    c.domain as company_domain,
    ct.name as contact_name,
    ct.title as contact_title,
    ct.email as contact_email,
    p.created_at,
    p.updated_at
FROM prospects p
LEFT JOIN companies c ON p.company_id = c.id
LEFT JOIN contacts ct ON p.contact_id = ct.id;

-- Insert sample data for testing (optional)
INSERT INTO companies (name, domain, source, meta_json) VALUES
('Sophia AI', 'sophia-ai.com', 'manual', '{"industry": "AI/ML", "size": "startup", "funding": "seed"}'),
('Example Corp', 'example.com', 'apollo', '{"industry": "PropTech", "size": "mid-market"}')
ON CONFLICT (domain) DO NOTHING;

-- Grant permissions for the application user (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Database schema migration completed successfully