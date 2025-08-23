// Mock Portkey interface for development
interface Portkey {
  chat: {
    completions: {
      create(params: any): Promise<any>;
    };
  };
}

import { PortkeyConfig } from './config';
import { LLMRequest, LLMResponse, ModelConfig, RouterOptions, PersonaAwareRequest } from './types';

// Local PersonaConfig interface to avoid import issues during compilation
interface PersonaConfig {
  name: string;
  humorLevel: number;
  formality: number;
  terseness: number;
  followUpPolicy: 'always' | 'only-if-ambiguous-or-high-value' | 'never';
  profanity: 'no' | 'mild' | 'unrestricted';
  bragging: 'no' | 'subtle' | 'allowed';
  contextAwareness: {
    disableHumorInErrors: boolean;
    disableHumorInSecurity: boolean;
    disableHumorInFinancial: boolean;
    disableHumorInInfraOps: boolean;
  };
  humorFrequency: {
    maxPerSession: number;
    cooldownMessages: number;
  };
}

export class LLMRouter {
  private portkey: Portkey;
  private config: PortkeyConfig;
  private requestCount: number = 0;
  private lastRequestTime: number = 0;
  private personaConfig?: PersonaConfig;

  constructor(models: ModelConfig[], options: RouterOptions, personaConfig?: PersonaConfig) {
    this.config = new PortkeyConfig(models, options);
    this.personaConfig = personaConfig;
    
    // Mock Portkey for development - in production, use actual Portkey
    this.portkey = {
      chat: {
        completions: {
          create: async (params: any) => {
            // Mock LLM response for development
            return {
              id: `mock_${Date.now()}`,
              model: params.model || 'gpt-4',
              choices: [{
                message: {
                  role: 'assistant' as const,
                  content: `Mock response for: ${params.messages[params.messages.length - 1]?.content || 'No content'}`
                },
                finish_reason: 'stop'
              }],
              usage: {
                prompt_tokens: 100,
                completion_tokens: 50,
                total_tokens: 150
              }
            };
          }
        }
      }
    } as Portkey;
  }

  /**
   * Route LLM request through Portkey with persona-aware routing
   */
  async chat(request: LLMRequest | PersonaAwareRequest): Promise<LLMResponse> {
    const startTime = Date.now();
    this.requestCount++;
    this.lastRequestTime = startTime;

    try {
      // Apply persona configuration to request if available
      const enhancedRequest = this.applyPersonaConfig(request);
      
      // Use primary model (ChatGPT-5) by default
      const model = enhancedRequest.model || this.config.getPrimaryModel().name;
      
      const response = await this.portkey.chat.completions.create({
        model,
        messages: enhancedRequest.messages,
        temperature: enhancedRequest.temperature || 0.7,
        max_tokens: enhancedRequest.max_tokens,
        stream: enhancedRequest.stream || false,
        metadata: {
          ...enhancedRequest.metadata,
          request_id: `sophia_${this.requestCount}_${startTime}`,
          source: 'sophia-ai-intel',
          persona_applied: !!this.personaConfig,
          context_flags: this.extractContextFlags(enhancedRequest)
        }
      });

      const endTime = Date.now();
      const latency = endTime - startTime;

      // Transform Portkey response to our standard format
      return {
        id: response.id,
        model: response.model,
        choices: response.choices.map((choice: any) => ({
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

  /**
   * Apply persona configuration to the request
   */
  private applyPersonaConfig(request: LLMRequest | PersonaAwareRequest): LLMRequest {
    if (!this.personaConfig) return request;

    const toneProfile = this.getPersonaToneProfile();
    const enhancedRequest = { ...request };

    // Adjust temperature based on formality
    if (!enhancedRequest.temperature) {
      // More formal = lower temperature, more casual = higher temperature
      enhancedRequest.temperature = Math.max(0.1, Math.min(0.9,
        0.7 - (this.personaConfig.formality - 0.5) * 0.4
      ));
    }

    // Adjust max_tokens based on terseness
    if (!enhancedRequest.max_tokens) {
      const baseTokens = 800;
      // More terse = fewer tokens, more verbose = more tokens
      enhancedRequest.max_tokens = Math.round(
        baseTokens * (1.5 - this.personaConfig.terseness)
      );
    }

    // Add persona context to system message if applicable
    if (enhancedRequest.messages.length > 0 && enhancedRequest.messages[0].role === 'system') {
      enhancedRequest.messages[0].content = this.enhanceSystemPrompt(
        enhancedRequest.messages[0].content
      );
    }

    return enhancedRequest;
  }

  /**
   * Get persona tone profile for routing decisions
   */
  private getPersonaToneProfile() {
    if (!this.personaConfig) return null;
    
    return {
      formality: this.personaConfig.formality,
      terseness: this.personaConfig.terseness,
      warmth: Math.max(0.2, 1 - this.personaConfig.formality),
    };
  }

  /**
   * Extract context flags for metadata
   */
  private extractContextFlags(request: LLMRequest | PersonaAwareRequest): Record<string, boolean> {
    const contextRequest = request as PersonaAwareRequest;
    return {
      is_error: contextRequest.context?.isError || false,
      is_security: contextRequest.context?.isSecurity || false,
      is_financial: contextRequest.context?.isFinancial || false,
      is_infra_op: contextRequest.context?.isInfraOp || false,
    };
  }

  /**
   * Enhance system prompt with persona guidelines
   */
  private enhanceSystemPrompt(originalPrompt: string): string {
    if (!this.personaConfig) return originalPrompt;

    const personalityGuidelines = this.generatePersonalityGuidelines();
    return `${originalPrompt}\n\n${personalityGuidelines}`;
  }

  /**
   * Generate personality guidelines based on config
   */
  private generatePersonalityGuidelines(): string {
    if (!this.personaConfig) return '';

    const guidelines = [];

    // Formality guidance
    if (this.personaConfig.formality > 0.7) {
      guidelines.push('Maintain professional, formal communication style.');
    } else if (this.personaConfig.formality < 0.3) {
      guidelines.push('Use casual, approachable communication style.');
    }

    // Terseness guidance
    if (this.personaConfig.terseness > 0.7) {
      guidelines.push('Be concise and direct. Avoid unnecessary elaboration.');
    } else if (this.personaConfig.terseness < 0.3) {
      guidelines.push('Provide comprehensive explanations with context.');
    }

    // Humor policy
    if (this.personaConfig.humorLevel > 0) {
      guidelines.push(`Light humor is acceptable (level: ${this.personaConfig.humorLevel}) but avoid in error/security/financial/infrastructure contexts.`);
    }

    // Follow-up policy
    guidelines.push(`Clarification policy: ${this.personaConfig.followUpPolicy}`);

    return `PERSONALITY GUIDELINES:\n${guidelines.map(g => `- ${g}`).join('\n')}`;
  }

  /**
   * Update persona configuration
   */
  updatePersonaConfig(config: PersonaConfig): void {
    this.personaConfig = config;
  }
}

