import { ModelConfig, RouterOptions } from './types';

export class PortkeyConfig {
  private models: ModelConfig[];
  private options: RouterOptions;

  constructor(models: ModelConfig[], options: RouterOptions) {
    this.models = models;
    this.options = options;
  }

  /**
   * Generate Portkey configuration for best-recent models policy
   * Prioritizes ChatGPT-5 with intelligent fallbacks
   */
  generateConfig(): any {
    const enabledModels = this.models
      .filter(m => m.enabled)
      .sort((a, b) => a.fallback_order - b.fallback_order);

    return {
      strategy: {
        mode: this.options.strategy === 'best_recent' ? 'fallback' : this.options.strategy
      },
      targets: enabledModels.map((model, index) => ({
        virtual_key: `${model.provider}_${model.name.replace(/[^a-zA-Z0-9]/g, '_')}`,
        provider: model.provider,
        model: model.name,
        weight: model.weight,
        retry: {
          attempts: this.options.retry_attempts,
          on_status_codes: [429, 500, 502, 503, 504]
        },
        timeout: this.options.timeout_ms,
        override_params: {
          max_tokens: model.max_tokens
        },
        metadata: {
          cost_per_token: model.cost_per_token,
          fallback_order: model.fallback_order,
          is_primary: index === 0 // ChatGPT-5 is primary
        }
      })),
      cache: {
        mode: this.options.cache_enabled ? 'semantic' : 'off',
        max_age: 3600 // 1 hour
      },
      logging: {
        enabled: this.options.logging_enabled,
        level: 'info'
      }
    };
  }

  /**
   * Get the primary model (ChatGPT-5)
   */
  getPrimaryModel(): ModelConfig {
    return this.models.find(m => m.fallback_order === 1) || this.models[0];
  }

  /**
   * Get fallback models in order
   */
  getFallbackModels(): ModelConfig[] {
    return this.models
      .filter(m => m.enabled && m.fallback_order > 1)
      .sort((a, b) => a.fallback_order - b.fallback_order);
  }

  /**
   * Update model configuration
   */
  updateModel(name: string, updates: Partial<ModelConfig>): void {
    const modelIndex = this.models.findIndex(m => m.name === name);
    if (modelIndex >= 0) {
      this.models[modelIndex] = { ...this.models[modelIndex], ...updates };
    }
  }

  /**
   * Get configuration for environment variables
   */
  getEnvironmentConfig(): Record<string, string> {
    const config: Record<string, string> = {
      PORTKEY_API_KEY: process.env.PORTKEY_API_KEY || '',
      DEFAULT_LLM_MODEL: this.getPrimaryModel().name,
      LLM_STRATEGY: this.options.strategy,
      LLM_FALLBACK_ENABLED: this.options.fallback_enabled.toString(),
      LLM_TIMEOUT_MS: this.options.timeout_ms.toString(),
      LLM_RETRY_ATTEMPTS: this.options.retry_attempts.toString()
    };

    // Add API keys for each provider
    const providers = [...new Set(this.models.map(m => m.provider))];
    providers.forEach(provider => {
      const envKey = this.models.find(m => m.provider === provider)?.api_key_env;
      if (envKey) {
        config[envKey] = process.env[envKey] || '';
      }
    });

    return config;
  }
}

