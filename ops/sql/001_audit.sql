-- Create audit schema for tracking tool invocations and system events
CREATE SCHEMA IF NOT EXISTS audit;

-- Tool invocations table
CREATE TABLE IF NOT EXISTS audit.tool_invocations (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(255) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    service VARCHAR(255) NOT NULL,
    tool VARCHAR(255) NOT NULL,
    request JSONB NOT NULL,
    response JSONB,
    purpose TEXT,
    duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_tool_invocations_tenant ON audit.tool_invocations(tenant);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_actor ON audit.tool_invocations(actor);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_service ON audit.tool_invocations(service);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_at ON audit.tool_invocations(at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_request ON audit.tool_invocations USING gin(request);

-- Service health events
CREATE TABLE IF NOT EXISTS audit.service_health (
    id SERIAL PRIMARY KEY,
    service VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    error TEXT,
    metadata JSONB,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_health_service ON audit.service_health(service, checked_at DESC);