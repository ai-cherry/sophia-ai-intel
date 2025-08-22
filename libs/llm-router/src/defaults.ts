import { ModelConfig, RouterOptions } from './types';

export function createDefaultConfig(): {
  models: ModelConfig[];
  options: RouterOptions;
} {
  return {
    models: [
      {
        name: 'gpt-5',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 100,
        max_tokens: 128000,
        cost_per_token: 0.00003, // Estimated
        enabled: true,
        fallback_order: 1
      },
      {
        name: 'claude-3-5-sonnet-20241022',
        provider: 'anthropic',
        api_key_env: 'ANTHROPIC_API_KEY',
        weight: 90,
        max_tokens: 200000,
        cost_per_token: 0.000015,
        enabled: true,
        fallback_order: 2
      },
      {
        name: 'gpt-4o',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 85,
        max_tokens: 128000,
        cost_per_token: 0.0000025,
        enabled: true,
        fallback_order: 3
      },
      {
        name: 'gpt-4o-mini',
        provider: 'openai',
        api_key_env: 'OPENAI_API_KEY',
        weight: 70,
        max_tokens: 128000,
        cost_per_token: 0.00000015,
        enabled: true,
        fallback_order: 4
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

