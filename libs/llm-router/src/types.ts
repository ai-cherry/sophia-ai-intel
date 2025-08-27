export interface LLMRequest {
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  metadata?: Record<string, any>;
}

export interface MessageContext {
  isError?: boolean;
  isSecurity?: boolean;
  isFinancial?: boolean;
  isInfraOp?: boolean;
  messageType?: 'response' | 'error' | 'info' | 'warning';
  originalPrompt?: string;
}

export interface PersonaAwareRequest extends LLMRequest {
  context?: MessageContext;
  personaOverrides?: {
    humorLevel?: number;
    formality?: number;
    terseness?: number;
  };
}

export interface LLMResponse {
  id: string;
  model: string;
  choices: Array<{
    message: {
      role: 'assistant';
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  metadata?: {
    provider: string;
    latency_ms: number;
    cost_usd?: number;
  };
}

export interface ModelConfig {
  name: string;
  provider: string;
  api_key_env: string;
  weight: number;
  max_tokens: number;
  cost_per_token: number;
  enabled: boolean;
  fallback_order: number;
  type?: string; // e.g., 'completion', 'embedding', 'vision'
  purpose?: string[]; // e.g., 'code_writing', 'general', 'embeddings', 'business_strategy'
}

export interface RouterOptions {
  strategy: 'best_recent' | 'cost_optimized' | 'latency_optimized' | 'round_robin';
  fallback_enabled: boolean;
  timeout_ms: number;
  retry_attempts: number;
  cache_enabled: boolean;
  logging_enabled: boolean;
}

