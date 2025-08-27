/**
 * @module @sophia/llm-router
 * @description
 * This module provides a centralized LLM routing mechanism for Sophia AI.
 * It abstracts away direct LLM calls, allowing for dynamic model selection
 * based on predefined strategies, model capabilities (e.g., embeddings, code writing),
 * and fallback mechanisms. This ensures optimal model usage, cost efficiency,
 * and high availability across various tasks within the Sophia AI ecosystem.
 *
 * The model selection strategy prioritizes specific models for key use cases:
 * - Code Planning & Business Strategy: ChatGPT-5
 * - Code Writing: Gemini 2.5 Pro
 * - General-Purpose Backup: Claude Opus 4.1
 * - Embeddings: GPT-Embedding-3-Large
 *
 * All direct LLM calls should be routed through the LLMRouter to leverage
 * this standardized selection and management.
 */
export { LLMRouter } from './router'; // Main router class
export { LLMConfig } from './config'; // Configuration class for LLM router settings
export type {
  LLMRequest,
  LLMResponse,
  ModelConfig,
  RouterOptions,
  PersonaAwareRequest,
  MessageContext
} from './types'; // Type definitions for LLM requests, responses, and router configuration
export { createDefaultConfig } from './defaults'; // Function to create the default model configurations

