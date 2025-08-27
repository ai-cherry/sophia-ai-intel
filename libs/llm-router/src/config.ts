import { ModelConfig, RouterOptions } from './types';

export class LLMConfig {
  private models: ModelConfig[];
  private options: RouterOptions;

  constructor(models: ModelConfig[], options: RouterOptions) {
    this.models = models;
    this.options = options;
  }

  /**
   * Generate standardized LLM configuration for multi-provider routing.
   * This configuration enables dynamic model selection based on predefined strategies,
   * model capabilities (e.g., embeddings, code writing), and robust fallback mechanisms.
   * It also configures providers, targets, caching, logging, and monitoring.
   */
  generateConfig(): any {
    const enabledModels = this.models
      .filter(m => m.enabled)
      .sort((a, b) => a.fallback_order - b.fallback_order);

    return {
      strategy: {
        mode: this.options.strategy === 'best_recent' ? 'fallback' : this.options.strategy,
        // Define an explicit provider fallback order for the router
        primary_provider: 'openai', 
        secondary_provider: 'google', 
        tertiary_provider: 'anthropic',
        quaternary_provider: 'xai', // XAI (Grok)
        quinary_provider: 'deepseek', // DeepSeek
        senary_provider: 'mistral', // Mistral
        septenary_provider: 'cohere', // Cohere
        octonary_provider: 'alibaba', // Alibaba (Qwen)
        nonary_provider: 'meta', // Meta (Llama)
        denary_provider: 'huggingface' // Huggingface (BGE)
      },
      providers: {
        openai: {
          models: enabledModels.filter(m => m.provider === 'openai'),
          base_url: 'https://api.openai.com/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        google: {
          models: enabledModels.filter(m => m.provider === 'google'),
          base_url: 'https://generativelanguage.googleapis.com/v1beta', // Example for Gemini
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        anthropic: {
          models: enabledModels.filter(m => m.provider === 'anthropic'),
          base_url: 'https://api.anthropic.com/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        xai: {
          models: enabledModels.filter(m=>m.provider === 'xai'),
          base_url: 'https://api.x.ai/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        deepseek: {
          models: enabledModels.filter(m => m.provider === 'deepseek'),
          base_url: 'https://api.deepseek.com/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        mistral: {
          models: enabledModels.filter(m => m.provider === 'mistral'),
          base_url: 'https://api.mistral.ai/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        cohere: {
          models: enabledModels.filter(m => m.provider === 'cohere'),
          base_url: 'https://api.cohere.ai/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        alibaba: {
          models: enabledModels.filter(m => m.provider === 'alibaba'),
          base_url: 'https://dashscope.aliyuncs.com/api/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        meta: {
          models: enabledModels.filter(m => m.provider === 'meta'),
          base_url: 'https://llama.meta.com/api/v1',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        },
        huggingface: {
          models: enabledModels.filter(m => m.provider === 'huggingface'),
          base_url: 'https://api-inference.huggingface.co/models',
          timeout: this.options.timeout_ms,
          retry_attempts: this.options.retry_attempts
        }
      },
      targets: enabledModels.map(model => ({
        provider_key: `${model.provider}_${model.name.replace(/[^a-zA-Z0-9]/g, '_')}`,
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
          type: model.type, // Include model type in metadata
          purpose: model.purpose, // Include model purpose in metadata
          // Dynamic tags based on fallback order for easier filtering/analysis
          is_primary: model.fallback_order === 1,
          is_secondary: model.fallback_order === 2,
          is_tertiary: model.fallback_order === 3,
          is_quaternary: model.fallback_order === 4,
          is_quinary: model.fallback_order === 5,
          is_senary: model.fallback_order === 6,
          is_septenary: model.fallback_order === 7,
          is_octonary: model.fallback_order === 8,
          is_nonary: model.fallback_order === 9,
          is_denary: model.fallback_order === 10,
        }
      })),
      cache: {
        mode: this.options.cache_enabled ? 'semantic' : 'off',
        max_age: 3600 // 1 hour
      },
      logging: {
        enabled: this.options.logging_enabled,
        level: 'info'
      },
      monitoring: {
        enabled: true,
        metrics: ['latency', 'cost', 'success_rate', 'fallback_count']
      }
    };
  }

  /**
   * Get the primary model based on purpose.
   * @param purpose The desired purpose of the model (e.g., 'code_planning', 'code_writing', 'embeddings').
   * @returns The ModelConfig for the highest-priority model matching the purpose, or undefined if none found.
   */
  getPrimaryModel(purpose: string[] = ['general']): ModelConfig | undefined {
    // Prioritize models that explicitly match the purpose, then general models
    const orderedModels = this.models
      .filter(m => m.enabled && m.purpose && purpose.some(p => m.purpose?.includes(p)))
      .sort((a, b) => a.fallback_order - b.fallback_order);
    
    if (orderedModels.length > 0) {
      return orderedModels[0];
    }

    // Fallback to the absolute primary model if no purpose-specific model is found (fallback_order 1 for general)
    return this.models.find(m => m.fallback_order === 1 && m.enabled && m.purpose?.includes('general'));
  }

  /**
   * Get fallback models in order of priority, optionally filtered by purpose.
   * @param purpose The desired purpose of the models (e.g., 'code_writing').
   * @returns An array of ModelConfig for fallback models.
   */
  getFallbackModels(purpose: string[] = ['general']): ModelConfig[] {
    return this.models
      .filter(m => m.enabled && m.fallback_order > 1 && m.purpose && purpose.some(p => m.purpose?.includes(p)))
      .sort((a, b) => a.fallback_order - b.fallback_order);
  }

  /**
   * Update model configuration.
   * @param name The name of the model to update.
   * @param updates Partial ModelConfig object with updates.
   */
  updateModel(name: string, updates: Partial<ModelConfig>): void {
    const modelIndex = this.models.findIndex(m => m.name === name);
    if (modelIndex >= 0) {
      this.models[modelIndex] = { ...this.models[modelIndex], ...updates };
    }
  }

  /**
   * Get configuration for environment variables.
   * This includes API keys for each provider and router-specific settings.
   * @returns A record of environment variable names and their values/placeholders.
   */
  getEnvironmentConfig(): Record<string, string> {
    const config: Record<string, string> = {
      PORTKEY_API_KEY: process.env.PORTKEY_API_KEY || '', // Assuming Portkey is used for unified API access
      DEFAULT_LLM_MODEL: this.getPrimaryModel()?.name || '', // Use optional chaining for safety if no primary model is found
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
