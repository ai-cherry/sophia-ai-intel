/**
 * Sophia Dashboard Configuration
 * NO MOCK DATA - Real service endpoints
 */

export const config = {
  // API Base URLs
  api: {
    dashboard: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
    swarmOrchestrator: process.env.NEXT_PUBLIC_SWARM_URL || 'http://localhost:8100',
    mcpContext: process.env.NEXT_PUBLIC_MCP_CONTEXT_URL || 'http://localhost:8081',
    mcpResearch: process.env.NEXT_PUBLIC_MCP_RESEARCH_URL || 'http://localhost:8085',
    vectorSearch: process.env.NEXT_PUBLIC_VECTOR_SEARCH_URL || 'http://localhost:8086',
  },
  
  // WebSocket URLs
  ws: {
    swarm: process.env.NEXT_PUBLIC_SWARM_WS_URL || 'ws://localhost:8100',
    debate: process.env.NEXT_PUBLIC_DEBATE_WS_URL || 'ws://localhost:8100',
  },
  
  // Prometheus/Grafana
  monitoring: {
    prometheusUrl: process.env.NEXT_PUBLIC_PROM_URL || 'http://localhost:9090',
    grafanaUrl: process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3001',
    grafanaDashboardId: process.env.NEXT_PUBLIC_GRAFANA_DASHBOARD_ID || 'sophia-metrics',
  },
  
  // Health Check Targets
  healthTargets: [
    { name: 'Swarm Orchestrator', url: 'http://localhost:8100/health' },
    { name: 'MCP Context', url: 'http://localhost:8081/health' },
    { name: 'MCP Research', url: 'http://localhost:8085/health' },
    { name: 'Vector Search', url: 'http://localhost:8086/health' },
  ],
  
  // Portkey Virtual Keys (presence check only, not actual secrets)
  portkey: {
    enabled: !!process.env.NEXT_PUBLIC_PORTKEY_API_KEY,
    virtualKeysConfigured: [
      'OPENAI',
      'ANTHROPIC',
      'DEEPSEEK',
      'QWEN',
      'GROK',
      'GROQ',
      'PERPLEXITY',
      'MISTRAL',
      'HUGGINGFACE',
    ].filter(key => !!process.env[`PORTKEY_VK_${key}`]),
  },
  
  // Feature Flags
  features: {
    enableWebSocket: true,
    enableDebateMode: true,
    enableMetrics: true,
    enableAgentFactory: true,
    enableSwarmMonitor: true,
    autoSubscribeToSwarms: true,
  },
  
  // UI Configuration
  ui: {
    maxActivityFeedItems: 100,
    maxDebateOutcomes: 10,
    defaultChatMessages: 50,
    refreshInterval: 5000, // ms
  },
};

// Type exports
export type Config = typeof config;
export type ApiConfig = typeof config.api;
export type WsConfig = typeof config.ws;
export type MonitoringConfig = typeof config.monitoring;
export type FeatureFlags = typeof config.features;
