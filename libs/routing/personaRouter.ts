/**
 * Persona Router - Temperature adjustment based on context and persona
 * ===================================================================
 * 
 * Integrates persona configuration with LLM routing to dynamically adjust
 * temperature, model selection, and other parameters based on context analysis.
 */

import { PersonaConfig, personaConfigManager } from '../../apps/dashboard/src/persona/personaConfig'
import { contextEnforcer, AnalysisResult } from '../persona/contextEnforcer'

/** LLM routing configuration */
export interface LLMRouterConfig {
  temperature: number
  model: string
  maxTokens?: number
  topP?: number
  frequencyPenalty?: number
  presencePenalty?: number
  timeout?: number
}

/** Context for routing decisions */
export interface RoutingContext {
  prompt: string
  conversationHistory?: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
  }>
  toolName?: string
  operationType?: 'creative' | 'analytical' | 'factual' | 'conversational'
  userQuery?: string
  metadata?: Record<string, any>
}

/** Routing decision result */
export interface RoutingDecision {
  config: LLMRouterConfig
  rationale: string
  contextAnalysis: AnalysisResult
  personaAdjustments: string[]
  model: string
  estimatedCost?: number
}

/** Model definitions with capabilities */
interface ModelDefinition {
  name: string
  baseTemperature: number
  maxTokens: number
  costPerToken: number
  strengths: string[]
  weaknesses: string[]
  bestFor: string[]
}

/** Available models */
const AVAILABLE_MODELS: Record<string, ModelDefinition> = {
  'gpt-4': {
    name: 'gpt-4',
    baseTemperature: 0.7,
    maxTokens: 8192,
    costPerToken: 0.00003,
    strengths: ['reasoning', 'complex-analysis', 'code-generation'],
    weaknesses: ['speed', 'cost'],
    bestFor: ['analytical', 'complex-reasoning', 'code-review']
  },
  'gpt-4-turbo': {
    name: 'gpt-4-turbo',
    baseTemperature: 0.7,
    maxTokens: 4096,
    costPerToken: 0.00001,
    strengths: ['speed', 'reasoning', 'cost-effective'],
    weaknesses: ['context-length'],
    bestFor: ['conversational', 'quick-analysis', 'factual']
  },
  'gpt-3.5-turbo': {
    name: 'gpt-3.5-turbo',
    baseTemperature: 0.9,
    maxTokens: 4096,
    costPerToken: 0.0000015,
    strengths: ['speed', 'cost', 'conversational'],
    weaknesses: ['reasoning', 'complex-tasks'],
    bestFor: ['creative', 'conversational', 'simple-tasks']
  },
  'claude-3-sonnet': {
    name: 'claude-3-sonnet',
    baseTemperature: 0.7,
    maxTokens: 4096,
    costPerToken: 0.00003,
    strengths: ['reasoning', 'safety', 'nuanced-analysis'],
    weaknesses: ['cost', 'availability'],
    bestFor: ['analytical', 'safety-critical', 'nuanced-tasks']
  }
}

export class PersonaRouter {
  constructor(
    private personaManager = personaConfigManager,
    private enforcer = contextEnforcer
  ) {}

  /**
   * Main routing function - determines optimal LLM configuration
   */
  async route(context: RoutingContext): Promise<RoutingDecision> {
    const persona = this.personaManager.getConfig()
    
    // Analyze context using enforcer
    const contextAnalysis = this.enforcer.analyzeContext({
      message: context.prompt,
      prompt: context.userQuery,
      metadata: { ...context.metadata, toolName: context.toolName }
    })

    // Apply persona enforcement if needed
    const enforcement = this.enforcer.shouldEnforceHumorZero(contextAnalysis)
    const adjustedPersona = enforcement.shouldEnforce
      ? this.enforcer.applyEnforcement(contextAnalysis)
      : persona

    // Select optimal model
    const selectedModel = this.selectModel(context, contextAnalysis, adjustedPersona)
    
    // Calculate temperature
    const temperature = this.calculateTemperature(
      context,
      contextAnalysis,
      adjustedPersona,
      selectedModel
    )

    // Build final configuration
    const config: LLMRouterConfig = {
      temperature,
      model: selectedModel.name,
      maxTokens: this.calculateMaxTokens(context, selectedModel),
      topP: this.calculateTopP(contextAnalysis, adjustedPersona),
      frequencyPenalty: this.calculateFrequencyPenalty(contextAnalysis),
      presencePenalty: this.calculatePresencePenalty(contextAnalysis),
      timeout: this.calculateTimeout(context, contextAnalysis)
    }

    // Generate rationale
    const rationale = this.generateRationale(
      context,
      contextAnalysis,
      selectedModel,
      config,
      enforcement
    )

    // Track persona adjustments
    const personaAdjustments = this.trackPersonaAdjustments(
      persona,
      adjustedPersona,
      enforcement
    )

    return {
      config,
      rationale,
      contextAnalysis,
      personaAdjustments,
      model: selectedModel.name,
      estimatedCost: this.estimateCost(config, selectedModel)
    }
  }

  /**
   * Select the most appropriate model based on context
   */
  private selectModel(
    context: RoutingContext,
    analysis: AnalysisResult,
    persona: PersonaConfig
  ): ModelDefinition {
    const models = Object.values(AVAILABLE_MODELS)
    let scores = models.map(model => ({
      model,
      score: this.scoreModel(model, context, analysis, persona)
    }))

    // Sort by score and return best match
    scores.sort((a, b) => b.score - a.score)
    return scores[0].model
  }

  /**
   * Score a model based on context requirements
   */
  private scoreModel(
    model: ModelDefinition,
    context: RoutingContext,
    analysis: AnalysisResult,
    persona: PersonaConfig
  ): number {
    let score = 0

    // Base suitability for operation type
    if (context.operationType && model.bestFor.includes(context.operationType)) {
      score += 3
    }

    // Context-specific adjustments
    if (analysis.riskLevel === 'high' && model.strengths.includes('safety')) {
      score += 2
    }

    if (analysis.isSecurity && model.strengths.includes('reasoning')) {
      score += 2
    }

    if (analysis.isFinancial && model.strengths.includes('complex-analysis')) {
      score += 1
    }

    // Persona-based preferences
    if (persona.formality > 0.7 && model.strengths.includes('reasoning')) {
      score += 1
    }

    if (persona.terseness > 0.7 && model.strengths.includes('speed')) {
      score += 1
    }

    // Penalize weaknesses in high-risk contexts
    if (analysis.riskLevel === 'high' && model.weaknesses.includes('reasoning')) {
      score -= 2
    }

    // Cost considerations (lower cost = higher score for non-critical tasks)
    if (analysis.riskLevel === 'low') {
      score += (0.00003 - model.costPerToken) * 100000 // Normalize cost impact
    }

    return score
  }

  /**
   * Calculate optimal temperature based on all factors
   */
  private calculateTemperature(
    context: RoutingContext,
    analysis: AnalysisResult,
    persona: PersonaConfig,
    model: ModelDefinition
  ): number {
    let baseTemp = model.baseTemperature

    // Context adjustments
    if (analysis.isSecurity || analysis.isFinancial || analysis.riskLevel === 'high') {
      baseTemp = Math.min(baseTemp, 0.3) // Very low for critical contexts
    } else if (analysis.isError) {
      baseTemp = Math.min(baseTemp, 0.4) // Low for error contexts
    }

    // Operation type adjustments
    switch (context.operationType) {
      case 'creative':
        baseTemp = Math.max(baseTemp, 0.8)
        break
      case 'analytical':
        baseTemp = Math.min(baseTemp, 0.4)
        break
      case 'factual':
        baseTemp = Math.min(baseTemp, 0.2)
        break
      case 'conversational':
        baseTemp = Math.max(baseTemp, 0.6)
        break
    }

    // Tool-specific adjustments
    if (context.toolName) {
      const toolTemp = this.getToolTemperature(context.toolName)
      if (toolTemp !== null) {
        baseTemp = Math.min(baseTemp, toolTemp)
      }
    }

    // Persona influence
    const humorAdjustment = persona.humorLevel * 0.15
    const formalityAdjustment = (1 - persona.formality) * 0.1

    baseTemp += humorAdjustment + formalityAdjustment

    // Clamp to valid range
    return Math.max(0.0, Math.min(1.0, baseTemp))
  }

  /**
   * Get recommended temperature for specific tools
   */
  private getToolTemperature(toolName: string): number | null {
    const toolTemperatures: Record<string, number> = {
      'prospects_search': 0.2,
      'arxiv_search': 0.1,
      'context_search': 0.3,
      'code_review': 0.2,
      'financial_analysis': 0.1,
      'creative_writing': 0.9,
      'casual_chat': 0.7,
      'technical_docs': 0.3
    }

    return toolTemperatures[toolName] || null
  }

  /**
   * Calculate max tokens based on context
   */
  private calculateMaxTokens(context: RoutingContext, model: ModelDefinition): number {
    let maxTokens = model.maxTokens

    // Adjust based on conversation length
    if (context.conversationHistory && context.conversationHistory.length > 10) {
      maxTokens = Math.min(maxTokens, 2048) // Reduce for long conversations
    }

    // Adjust based on prompt length
    const promptLength = context.prompt.length
    if (promptLength > 2000) {
      maxTokens = Math.max(maxTokens, 4096) // Increase for complex prompts
    }

    return maxTokens
  }

  /**
   * Calculate TopP (nucleus sampling)
   */
  private calculateTopP(analysis: AnalysisResult, persona: PersonaConfig): number {
    let topP = 0.9 // Default

    if (analysis.riskLevel === 'high' || analysis.isSecurity) {
      topP = 0.1 // Very focused sampling
    } else if (analysis.isFinancial || analysis.isError) {
      topP = 0.3 // Focused sampling
    }

    // Persona adjustments
    if (persona.humorLevel > 0.5) {
      topP += 0.1 // More diverse for humor
    }

    return Math.max(0.1, Math.min(1.0, topP))
  }

  /**
   * Calculate frequency penalty
   */
  private calculateFrequencyPenalty(analysis: AnalysisResult): number {
    if (analysis.contextType === 'creative') {
      return 0.3 // Reduce repetition in creative contexts
    }
    
    if (analysis.riskLevel === 'high') {
      return 0.0 // No penalty for critical contexts
    }

    return 0.1 // Light penalty
  }

  /**
   * Calculate presence penalty
   */
  private calculatePresencePenalty(analysis: AnalysisResult): number {
    if (analysis.contextType === 'creative') {
      return 0.6 // Encourage topic diversity
    }

    return 0.0 // No penalty for most contexts
  }

  /**
   * Calculate timeout based on context complexity
   */
  private calculateTimeout(context: RoutingContext, analysis: AnalysisResult): number {
    let timeout = 30000 // 30 seconds default

    if (analysis.riskLevel === 'high') {
      timeout = 60000 // 60 seconds for critical contexts
    }

    if (context.prompt.length > 1000) {
      timeout = 45000 // 45 seconds for complex prompts
    }

    return timeout
  }

  /**
   * Generate human-readable rationale
   */
  private generateRationale(
    context: RoutingContext,
    analysis: AnalysisResult,
    model: ModelDefinition,
    config: LLMRouterConfig,
    enforcement: any
  ): string {
    const parts: string[] = []

    parts.push(`Selected ${model.name} for ${context.operationType || 'general'} task`)
    
    if (analysis.riskLevel === 'high') {
      parts.push(`High risk context detected - using conservative settings`)
    }

    if (enforcement.shouldEnforce) {
      parts.push(`Persona enforcement applied: ${enforcement.reason}`)
    }

    parts.push(`Temperature ${config.temperature.toFixed(2)} for ${analysis.contextType} context`)

    if (config.temperature < 0.3) {
      parts.push('Low temperature for precision and consistency')
    } else if (config.temperature > 0.7) {
      parts.push('High temperature for creativity and diversity')
    }

    return parts.join('. ')
  }

  /**
   * Track what persona adjustments were made
   */
  private trackPersonaAdjustments(
    original: PersonaConfig,
    adjusted: PersonaConfig,
    enforcement: any
  ): string[] {
    const adjustments: string[] = []

    if (original.humorLevel !== adjusted.humorLevel) {
      adjustments.push(`Humor level: ${original.humorLevel} → ${adjusted.humorLevel}`)
    }

    if (original.formality !== adjusted.formality) {
      adjustments.push(`Formality: ${original.formality} → ${adjusted.formality}`)
    }

    if (original.terseness !== adjusted.terseness) {
      adjustments.push(`Terseness: ${original.terseness} → ${adjusted.terseness}`)
    }

    if (enforcement.shouldEnforce) {
      adjustments.push(`Context enforcement: ${enforcement.reason}`)
    }

    return adjustments
  }

  /**
   * Estimate cost for the request
   */
  private estimateCost(config: LLMRouterConfig, model: ModelDefinition): number {
    // Rough estimation based on max tokens and model cost
    return (config.maxTokens || model.maxTokens) * model.costPerToken
  }

  /**
   * Get routing statistics
   */
  getStats(): {
    totalRoutings: number
    modelUsage: Record<string, number>
    averageTemperature: number
    contextBreakdown: Record<string, number>
  } {
    // This would be implemented with actual tracking in a real system
    return {
      totalRoutings: 0,
      modelUsage: {},
      averageTemperature: 0.7,
      contextBreakdown: {}
    }
  }
}

// Global instance
export const personaRouter = new PersonaRouter()

/**
 * Convenience function for quick routing decisions
 */
export async function routeForContext(context: RoutingContext): Promise<RoutingDecision> {
  return personaRouter.route(context)
}

/**
 * Helper to create routing context from common parameters
 */
export function createRoutingContext(
  prompt: string,
  options: Partial<RoutingContext> = {}
): RoutingContext {
  return {
    prompt,
    operationType: 'conversational',
    ...options
  }
}