/**
 * Context Enforcer - Persona-aware enforcement across all tools
 * ============================================================
 *
 * Centralizes persona-aware enforcement decisions to ensure humor, tone,
 * and other personality attributes are respected across all tool invocations.
 */

import { PersonaConfig, personaConfigManager } from '../../apps/dashboard/src/persona/personaConfig'

/** Context analysis input for the enforcer */
export interface ContextAnalysis {
  message?: string
  prompt?: string
  metadata?: {
    messageType?: string
    [key: string]: any
  }
}

/** Result of context analysis */
export interface AnalysisResult {
  isError: boolean
  isSecurity: boolean
  isFinancial: boolean
  isInfraOp: boolean
  confidenceScore: number
  riskLevel: 'low' | 'medium' | 'high'
  contextType: string
}

/** Enforcement decision result */
export interface EnforcementDecision {
  shouldEnforce: boolean
  reason: string
  severity: 'low' | 'medium' | 'high'
  adjustments: string[]
}

/** Tool classification for enforcement decisions */
export enum ToolCategory {
  SAFE_READ = 'safe_read',
  RISKY_WRITE = 'risky_write',
  FINANCIAL = 'financial',
  INFRASTRUCTURE = 'infrastructure',
  SECURITY = 'security',
  CREATIVE = 'creative',
  ANALYTICAL = 'analytical'
}

/** Context patterns for detection */
const CONTEXT_PATTERNS = {
  error: /\b(error|failed|failure|exception|crash|broke|broken|problem|issue|critical)\b/i,
  security: /\b(security|auth|token|key|secret|password|credential|vulnerability|breach|hack)\b/i,
  financial: /\b(payment|billing|cost|charge|money|price|invoice|revenue|finance|budget)\b/i,
  infraOp: /\b(deploy|deployment|infrastructure|server|database|production|outage|downtime|scaling)\b/i,
}

export class ContextEnforcer {
  private config: PersonaConfig
  private enforcementStats = {
    totalAnalyses: 0,
    enforcementsApplied: 0,
    contextBreakdown: {
      error: 0,
      security: 0,
      financial: 0,
      infraOp: 0,
      normal: 0
    }
  }

  constructor(initialConfig: PersonaConfig) {
    this.config = { ...initialConfig }
  }

  /**
   * Update the persona configuration
   */
  updatePersonaConfig(config: PersonaConfig): void {
    this.config = { ...config }
  }

  /**
   * Analyze context from message content
   */
  analyzeContext(input: ContextAnalysis): AnalysisResult {
    this.enforcementStats.totalAnalyses++
    
    const content = `${input.message || ''} ${input.prompt || ''}`.toLowerCase()
    
    const isError = CONTEXT_PATTERNS.error.test(content)
    const isSecurity = CONTEXT_PATTERNS.security.test(content)
    const isFinancial = CONTEXT_PATTERNS.financial.test(content)
    const isInfraOp = CONTEXT_PATTERNS.infraOp.test(content)
    
    // Update stats
    if (isError) this.enforcementStats.contextBreakdown.error++
    else if (isSecurity) this.enforcementStats.contextBreakdown.security++
    else if (isFinancial) this.enforcementStats.contextBreakdown.financial++
    else if (isInfraOp) this.enforcementStats.contextBreakdown.infraOp++
    else this.enforcementStats.contextBreakdown.normal++
    
    // Calculate confidence score based on pattern matches
    let confidenceScore = 0.5 // Base confidence
    const matches = [isError, isSecurity, isFinancial, isInfraOp].filter(Boolean).length
    confidenceScore += matches * 0.15
    
    // Determine risk level
    let riskLevel: 'low' | 'medium' | 'high' = 'low'
    if (isSecurity || (isError && isInfraOp)) {
      riskLevel = 'high'
    } else if (isError || isFinancial || isInfraOp) {
      riskLevel = 'medium'
    }
    
    // Determine context type
    let contextType = 'normal'
    if (isError) contextType = 'error'
    else if (isSecurity) contextType = 'security'
    else if (isFinancial) contextType = 'financial'
    else if (isInfraOp) contextType = 'infrastructure'
    
    return {
      isError,
      isSecurity,
      isFinancial,
      isInfraOp,
      confidenceScore,
      riskLevel,
      contextType
    }
  }

  /**
   * Determine if humor should be enforced to zero
   */
  shouldEnforceHumorZero(analysis: AnalysisResult): EnforcementDecision {
    const adjustments: string[] = []
    let shouldEnforce = false
    let reason = 'Normal context - no enforcement needed'
    let severity: 'low' | 'medium' | 'high' = 'low'
    
    // Check context-specific enforcement rules
    if (analysis.isError && this.config.contextAwareness.disableHumorInErrors) {
      shouldEnforce = true
      reason = 'Humor disabled for error contexts to maintain professional tone'
      severity = 'medium'
      adjustments.push('humor: disabled (error context)')
    }
    
    if (analysis.isSecurity && this.config.contextAwareness.disableHumorInSecurity) {
      shouldEnforce = true
      reason = 'Humor disabled for security contexts to maintain serious tone'
      severity = 'high'
      adjustments.push('humor: disabled (security context)')
    }
    
    if (analysis.isFinancial && this.config.contextAwareness.disableHumorInFinancial) {
      shouldEnforce = true
      reason = 'Humor disabled for financial contexts to maintain professional tone'
      severity = 'medium'
      adjustments.push('humor: disabled (financial context)')
    }
    
    if (analysis.isInfraOp && this.config.contextAwareness.disableHumorInInfraOps) {
      shouldEnforce = true
      reason = 'Humor disabled for infrastructure operations to maintain focus'
      severity = 'medium'
      adjustments.push('humor: disabled (infrastructure context)')
    }
    
    // Update enforcement stats
    if (shouldEnforce) {
      this.enforcementStats.enforcementsApplied++
    }
    
    return {
      shouldEnforce,
      reason,
      severity,
      adjustments
    }
  }

  /**
   * Apply enforcement by returning modified persona config
   */
  applyEnforcement(analysis: AnalysisResult): PersonaConfig {
    const enforcedConfig = { ...this.config }
    
    // Apply humor suppression
    const enforcement = this.shouldEnforceHumorZero(analysis)
    if (enforcement.shouldEnforce) {
      enforcedConfig.humorLevel = 0
    }
    
    // Adjust formality based on context
    if (analysis.isSecurity || analysis.riskLevel === 'high') {
      enforcedConfig.formality = Math.max(enforcedConfig.formality, 0.8)
    } else if (analysis.isError) {
      enforcedConfig.formality = Math.max(enforcedConfig.formality, 0.6)
    }
    
    // Adjust terseness for critical contexts
    if (analysis.riskLevel === 'high') {
      enforcedConfig.terseness = Math.min(enforcedConfig.terseness, 0.4) // More verbose for critical issues
    }
    
    return enforcedConfig
  }

  /**
   * Get enforcement statistics
   */
  getEnforcementStats() {
    return {
      ...this.enforcementStats,
      enforcementRate: this.enforcementStats.totalAnalyses > 0
        ? this.enforcementStats.enforcementsApplied / this.enforcementStats.totalAnalyses
        : 0
    }
  }

  /**
   * Reset enforcement statistics
   */
  resetStats(): void {
    this.enforcementStats = {
      totalAnalyses: 0,
      enforcementsApplied: 0,
      contextBreakdown: {
        error: 0,
        security: 0,
        financial: 0,
        infraOp: 0,
        normal: 0
      }
    }
  }

  /**
   * Calculate appropriate temperature for LLM calls based on context
   */
  calculateTemperature(analysis: AnalysisResult): number {
    let baseTemperature = 0.7 // Default temperature
    
    // Adjust based on context
    if (analysis.isSecurity || analysis.riskLevel === 'high') {
      baseTemperature = 0.2 // Very low temperature for critical operations
    } else if (analysis.isError || analysis.isInfraOp) {
      baseTemperature = 0.3 // Low temperature for operational contexts
    } else if (analysis.isFinancial) {
      baseTemperature = 0.4 // Moderate low temperature for financial contexts
    }
    
    // Apply persona humor level influence (slight)
    const humorAdjustment = this.config.humorLevel * 0.1
    return Math.max(0.1, Math.min(1.0, baseTemperature + humorAdjustment))
  }
}

/**
 * Factory function to create a new ContextEnforcer instance
 */
export function createContextEnforcer(config: PersonaConfig): ContextEnforcer {
  return new ContextEnforcer(config)
}

// Global instance
export const contextEnforcer = new ContextEnforcer(personaConfigManager.getConfig())