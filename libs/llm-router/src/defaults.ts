import { ModelConfig, RouterOptions } from './types';

export function createDefaultConfig(): {
  models: ModelConfig[];
  options: RouterOptions;
} {
  return {
    models: [
      // --- Embeddings Models ---
      {
        name: 'gpt-embedding-3-large',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 100,
        max_tokens: 8192, // Max input tokens for embedding
        cost_per_token: 0.0000002, // Estimate, actual needs verification
        enabled: true,
        fallback_order: 1,
        type: 'embedding',
        purpose: ['embeddings']
      },
      {
        name: 'gemini-embed',
        provider: 'google',
        api_key_env: 'GOOGLE_API_KEY',
        weight: 90,
        max_tokens: 3072, // Estimate
        cost_per_token: 0.0000001, // Estimate
        enabled: true,
        fallback_order: 2,
        type: 'embedding',
        purpose: ['embeddings']
      },
      {
        name: 'cohere-embed',
        provider: 'cohere',
        api_key_env: 'COHERE_API_KEY',
        weight: 85,
        max_tokens: 512, // Estimate
        cost_per_token: 0.00000015, // Estimate
        enabled: true,
        fallback_order: 3,
        type: 'embedding',
        purpose: ['embeddings']
      },
      {
        name: 'mistral-embed',
        provider: 'mistral',
        api_key_env: 'MISTRAL_API_KEY',
        weight: 80,
        max_tokens: 8192, // Estimate
        cost_per_token: 0.0000001, // Estimate
        enabled: true,
        fallback_order: 4,
        type: 'embedding',
        purpose: ['embeddings']
      },
      {
        name: 'bge-large-en', // Generic BGE
        provider: 'huggingface',
        api_key_env: 'HUGGINGFACE_API_KEY', // New env var
        weight: 70,
        max_tokens: 512, // Estimate
        cost_per_token: 0.00000008, // Estimate
        enabled: true,
        fallback_order: 5,
        type: 'embedding',
        purpose: ['embeddings']
      },

      // --- Code Planning & Business Strategy (GPT-5 Primary) ---
      {
        name: 'gpt-5',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 100,
        max_tokens: 128000,
        cost_per_token: 0.00003,
        enabled: true,
        fallback_order: 1,
        type: 'completion',
        purpose: ['code_planning', 'business_strategy', 'general']
      },
      {
        name: 'claude-opus-4.1', // High-tier backup for general, structured outputs, deep reasoning
        provider: 'anthropic',
        api_key_env: 'ANTHROPIC_API_KEY',
        weight: 98,
        max_tokens: 200000,
        cost_per_token: 0.000015,
        enabled: true,
        fallback_order: 2,
        type: 'completion',
        purpose: ['general', 'code_planning', 'business_strategy', 'chat', 'deep_research', 'structured_output', 'safety']
      },
      {
        name: 'o1-preview',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 95,
        max_tokens: 128000,
        cost_per_token: 0.00003,
        enabled: true,
        fallback_order: 3,
        type: 'completion',
        purpose: ['general', 'code_planning', 'business_strategy']
      },
      {
        name: 'gemini-2.5-deep-think', // Strong for deep reasoning, good for planning/strategy
        provider: 'google',
        api_key_env: 'GOOGLE_API_KEY',
        weight: 92,
        max_tokens: 32768, // Estimate
        cost_per_token: 0.00001, // Estimate
        enabled: true,
        fallback_order: 4,
        type: 'completion',
        purpose: ['deep_research', 'general', 'chat', 'code_planning', 'business_strategy']
      },
      {
        name: 'grok-4',
        provider: 'xai',
        api_key_env: 'XAI_API_KEY',
        weight: 90,
        max_tokens: 128000,
        cost_per_token: 0.000025,
        enabled: true,
        fallback_order: 5,
        type: 'completion',
        purpose: ['general', 'chat']
      },

      // --- Code Writing (Gemini 2.5 Pro Primary) ---
      {
        name: 'gemini-2.5-pro',
        provider: 'google',
        api_key_env: 'GOOGLE_API_KEY',
        weight: 100,
        max_tokens: 32768,
        cost_per_token: 0.000005, // Estimate
        enabled: true,
        fallback_order: 1,
        type: 'completion',
        purpose: ['code_writing', 'general']
      },
      {
        name: 'deepseek-coder',
        provider: 'deepseek',
        api_key_env: 'DEEPSEEK_API_KEY',
        weight: 95,
        max_tokens: 16384, // Estimate
        cost_per_token: 0.000001, // Estimate
        enabled: true,
        fallback_order: 2,
        type: 'completion',
        purpose: ['code_writing']
      },
      {
        name: 'qwen3-coder-480b',
        provider: 'alibaba',
        api_key_env: 'ALIBABA_API_KEY',
        weight: 90,
        max_tokens: 128000, // Estimate
        cost_per_token: 0.000002, // Estimate
        enabled: true,
        fallback_order: 3,
        type: 'completion',
        purpose: ['code_writing']
      },
      {
        name: 'gpt-4o-mini',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 85,
        max_tokens: 128000,
        cost_per_token: 0.00000015,
        enabled: true,
        fallback_order: 4,
        type: 'completion',
        purpose: ['code_writing', 'chat', 'general']
      },
      {
        name: 'grok-1-beta',
        provider: 'xai',
        api_key_env: 'XAI_API_KEY',
        weight: 80,
        max_tokens: 128000,
        cost_per_token: 0.00002,
        enabled: true,
        fallback_order: 5,
        type: 'completion',
        purpose: ['general', 'chat']
      },

      // --- General Purpose / Other Specialized Models ---
      {
        name: 'deepseek-v3.1',
        provider: 'deepseek',
        api_key_env: 'DEEPSEEK_API_KEY',
        weight: 88,
        max_tokens: 128000, // Estimate
        cost_per_token: 0.0000015, // Estimate
        enabled: true,
        fallback_order: 6,
        type: 'completion',
        purpose: ['general', 'chat']
      },
      {
        name: 'deepseek-r1',
        provider: 'deepseek',
        api_key_env: 'DEEPSEEK_API_KEY',
        weight: 87,
        max_tokens: 128000, // Estimate
        cost_per_token: 0.0000015, // Estimate
        enabled: true,
        fallback_order: 7,
        type: 'completion',
        purpose: ['general', 'chat']
      },
      {
        name: 'command-a-reasoning',
        provider: 'cohere',
        api_key_env: 'COHERE_API_KEY',
        weight: 86,
        max_tokens: 4096, // Estimate
        cost_per_token: 0.000006, // Estimate
        enabled: true,
        fallback_order: 8,
        type: 'completion',
        purpose: ['deep_research', 'general']
      },
      {
        name: 'command-a-vision',
        provider: 'cohere',
        api_key_env: 'COHERE_API_KEY',
        weight: 85,
        max_tokens: 4096, // Estimate
        cost_per_token: 0.000007, // Estimate
        enabled: true,
        fallback_order: 9,
        type: 'vision',
        purpose: ['vision', 'general']
      },
      {
        name: 'qwen3-235b',
        provider: 'alibaba',
        api_key_env: 'ALIBABA_API_KEY',
        weight: 84,
        max_tokens: 65536, // Estimate
        cost_per_token: 0.0000018, // Estimate
        enabled: true,
        fallback_order: 10,
        type: 'completion',
        purpose: ['general', 'chat']
      },
      {
        name: 'qwen-mt',
        provider: 'alibaba',
        api_key_env: 'ALIBABA_API_KEY',
        weight: 83,
        max_tokens: 32768, // Estimate
        cost_per_token: 0.0000015, // Estimate
        enabled: true,
        fallback_order: 11,
        type: 'completion',
        purpose: ['translation', 'general']
      },
      {
        name: 'gemini-2.5-flash-lite', // Cost-effective and fast for simple tasks
        provider: 'google',
        api_key_env: 'GOOGLE_API_KEY',
        weight: 82,
        max_tokens: 16384, // Estimate
        cost_per_token: 0.0000005, // Estimate
        enabled: true,
        fallback_order: 12,
        type: 'completion',
        purpose: ['chat', 'general']
      },
      {
        name: 'llama-3-70b-instruct',
        provider: 'meta',
        api_key_env: 'META_API_KEY',
        weight: 70,
        max_tokens: 8192, // Estimate
        cost_per_token: 0.0000008, // Estimate
        enabled: true,
        fallback_order: 13,
        type: 'completion',
        purpose: ['general', 'chat']
      },
      {
        name: 'llama-3-8b-instruct', // Smaller Llama model for efficiency
        provider: 'meta',
        api_key_env: 'META_API_KEY',
        weight: 65,
        max_tokens: 8192, // Estimate
        cost_per_token: 0.0000002, // Estimate
        enabled: true,
        fallback_order: 14,
        type: 'completion',
        purpose: ['general', 'chat', 'summarization']
      }
    ],
    options: {
      strategy: 'best_recent',
      fallback_enabled: true,
      timeout_ms: 30000,
      retry_attempts: 3,
      cache_enabled: true,
      logging_enabled: true
    }
  };
}
