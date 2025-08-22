import { z } from 'zod';
import { BaseResponseSchema } from './common';

// LLM Model definitions with ChatGPT-5 as default
export const LLMModelSchema = z.enum([
  'gpt-5',                    // Default primary model
  'gpt-4o',                   // OpenAI fallback
  'gpt-4-turbo',              // OpenAI alternative
  'claude-3-5-sonnet-20241022', // Anthropic primary
  'claude-3-haiku-20240307',  // Anthropic fast
  'deepseek-coder',           // Code assistance
  'groq-llama-3-70b',         // Fast inference
  'groq-llama-3-8b',          // Ultra-fast inference
]);

export const LLMProviderSchema = z.enum([
  'openai',
  'anthropic',
  'deepseek',
  'groq',
  'together',
  'portkey',
]);

// LLM Configuration
export const LLMConfigSchema = z.object({
  model: LLMModelSchema.default('gpt-5'),
  provider: LLMProviderSchema.default('openai'),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(1).max(32000).default(4000),
  top_p: z.number().min(0).max(1).default(1),
  frequency_penalty: z.number().min(-2).max(2).default(0),
  presence_penalty: z.number().min(-2).max(2).default(0),
  stream: z.boolean().default(false),
});

// Chat message structure
export const ChatMessageSchema = z.object({
  role: z.enum(['system', 'user', 'assistant', 'tool']),
  content: z.string(),
  name: z.string().optional(),
  tool_calls: z.array(z.object({
    id: z.string(),
    type: z.literal('function'),
    function: z.object({
      name: z.string(),
      arguments: z.string(),
    }),
  })).optional(),
  tool_call_id: z.string().optional(),
});

// Chat completion request
export const ChatCompletionRequestSchema = z.object({
  messages: z.array(ChatMessageSchema),
  config: LLMConfigSchema.optional(),
  tools: z.array(z.object({
    type: z.literal('function'),
    function: z.object({
      name: z.string(),
      description: z.string(),
      parameters: z.record(z.any()),
    }),
  })).optional(),
  tool_choice: z.union([
    z.literal('auto'),
    z.literal('none'),
    z.object({
      type: z.literal('function'),
      function: z.object({ name: z.string() }),
    }),
  ]).optional(),
});

// Chat completion response
export const ChatCompletionResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  message: ChatMessageSchema,
  usage: z.object({
    prompt_tokens: z.number(),
    completion_tokens: z.number(),
    total_tokens: z.number(),
  }),
  model: LLMModelSchema,
  provider: LLMProviderSchema,
});

// LLM Router configuration for Portkey
export const LLMRouterConfigSchema = z.object({
  strategy: z.enum(['single', 'fallback', 'loadbalance', 'retry']).default('fallback'),
  targets: z.array(z.object({
    provider: LLMProviderSchema,
    model: LLMModelSchema,
    weight: z.number().min(0).max(1).default(1),
    virtual_key: z.string().optional(),
  })),
  retry_settings: z.object({
    attempts: z.number().min(1).max(5).default(3),
    on_status_codes: z.array(z.number()).default([429, 500, 502, 503, 504]),
  }).optional(),
});

// Default router configuration with ChatGPT-5 primary
export const DEFAULT_LLM_ROUTER_CONFIG: z.infer<typeof LLMRouterConfigSchema> = {
  strategy: 'fallback',
  targets: [
    {
      provider: 'openai',
      model: 'gpt-5',
      weight: 1,
    },
    {
      provider: 'anthropic',
      model: 'claude-3-5-sonnet-20241022',
      weight: 0.8,
    },
    {
      provider: 'openai',
      model: 'gpt-4o',
      weight: 0.6,
    },
  ],
  retry_settings: {
    attempts: 3,
    on_status_codes: [429, 500, 502, 503, 504],
  },
};

// Export types
export type LLMModel = z.infer<typeof LLMModelSchema>;
export type LLMProvider = z.infer<typeof LLMProviderSchema>;
export type LLMConfig = z.infer<typeof LLMConfigSchema>;
export type ChatMessage = z.infer<typeof ChatMessageSchema>;
export type ChatCompletionRequest = z.infer<typeof ChatCompletionRequestSchema>;
export type ChatCompletionResponse = z.infer<typeof ChatCompletionResponseSchema>;
export type LLMRouterConfig = z.infer<typeof LLMRouterConfigSchema>;

