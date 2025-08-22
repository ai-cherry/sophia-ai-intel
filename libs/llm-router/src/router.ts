import { Portkey } from 'portkey-ai';
import { PortkeyConfig } from './config';
import { LLMRequest, LLMResponse, ModelConfig, RouterOptions } from './types';

export class LLMRouter {
  private portkey: Portkey;
  private config: PortkeyConfig;
  private requestCount: number = 0;
  private lastRequestTime: number = 0;

  constructor(models: ModelConfig[], options: RouterOptions) {
    this.config = new PortkeyConfig(models, options);
    
    this.portkey = new Portkey({
      apiKey: process.env.PORTKEY_API_KEY,
      config: this.config.generateConfig()
    });
  }

  /**
   * Route LLM request through Portkey with ChatGPT-5 priority
   */
  async chat(request: LLMRequest): Promise<LLMResponse> {
    const startTime = Date.now();
    this.requestCount++;
    this.lastRequestTime = startTime;

    try {
      // Use primary model (ChatGPT-5) by default
      const model = request.model || this.config.getPrimaryModel().name;
      
      const response = await this.portkey.chat.completions.create({
        model,
        messages: request.messages,
        temperature: request.temperature || 0.7,
        max_tokens: request.max_tokens,
        stream: request.stream || false,
        metadata: {
          ...request.metadata,
          request_id: `sophia_${this.requestCount}_${startTime}`,
          source: 'sophia-ai-intel'
        }
      });

      const endTime = Date.now();
      const latency = endTime - startTime;

      // Transform Portkey response to our standard format
      return {
        id: response.id,
        model: response.model,
        choices: response.choices.map(choice => ({
          message: {
            role: 'assistant' as const,
            content: choice.message.content || ''
          },
          finish_reason: choice.finish_reason || 'stop'
        })),
        usage: {
          prompt_tokens: response.usage?.prompt_tokens || 0,
          completion_tokens: response.usage?.completion_tokens || 0,
          total_tokens: response.usage?.total_tokens || 0
        },
        metadata: {
          provider: this.getProviderForModel(response.model),
          latency_ms: latency,
          cost_usd: this.calculateCost(response.model, response.usage?.total_tokens || 0)
        }
      };

    } catch (error) {
      console.error('LLM Router Error:', error);
      throw new Error(`LLM routing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get health status of all configured models
   */
  async getHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    models: Array<{
      name: string;
      provider: string;
      status: 'healthy' | 'unhealthy';
      latency_ms?: number;
    }>;
    primary_model: string;
    fallback_models: string[];
    request_count: number;
    last_request: number;
  }> {
    const primaryModel = this.config.getPrimaryModel();
    const fallbackModels = this.config.getFallbackModels();

    // Simple health check - in production, this would ping each model
    const modelStatuses = [primaryModel, ...fallbackModels].map(model => ({
      name: model.name,
      provider: model.provider,
      status: 'healthy' as const, // Assume healthy for now
      latency_ms: 150 // Mock latency
    }));

    const healthyCount = modelStatuses.filter(m => m.status === 'healthy').length;
    const totalCount = modelStatuses.length;

    let overallStatus: 'healthy' | 'degraded' | 'unhealthy';
    if (healthyCount === totalCount) {
      overallStatus = 'healthy';
    } else if (healthyCount > 0) {
      overallStatus = 'degraded';
    } else {
      overallStatus = 'unhealthy';
    }

    return {
      status: overallStatus,
      models: modelStatuses,
      primary_model: primaryModel.name,
      fallback_models: fallbackModels.map(m => m.name),
      request_count: this.requestCount,
      last_request: this.lastRequestTime
    };
  }

  /**
   * Get current configuration
   */
  getConfig(): {
    primary_model: string;
    fallback_models: string[];
    strategy: string;
    environment: Record<string, string>;
  } {
    return {
      primary_model: this.config.getPrimaryModel().name,
      fallback_models: this.config.getFallbackModels().map(m => m.name),
      strategy: 'best_recent',
      environment: this.config.getEnvironmentConfig()
    };
  }

  private getProviderForModel(modelName: string): string {
    if (modelName.startsWith('gpt')) return 'openai';
    if (modelName.startsWith('claude')) return 'anthropic';
    return 'unknown';
  }

  private calculateCost(modelName: string, totalTokens: number): number {
    // Simple cost calculation - in production, use actual pricing
    const costPerToken = modelName.includes('gpt-5') ? 0.00003 : 0.000015;
    return totalTokens * costPerToken;
  }
}

