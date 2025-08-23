/**
 * Sophia AI Context Enforcer
 * Ensures humor=0 in sensitive contexts (error/security/finance/infrastructure)
 */

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

export interface ContextAnalysis {
  isError: boolean;
  isSecurity: boolean;
  isFinancial: boolean;
  isInfraOp: boolean;
  severity: 'low' | 'medium' | 'high';
  detectedKeywords: string[];
  confidence: number; // 0-1
}

export interface EnforcementAction {
  shouldEnforce: boolean;
  originalHumorLevel: number;
  enforcedHumorLevel: number;
  reason: string;
  contextFlags: string[];
}

/**
 * Advanced context detection patterns
 */
const CONTEXT_PATTERNS = {
  error: {
    high: /\b(error|exception|crash|fail|failure|bug|broken|critical|fatal|panic|abort)\b/gi,
    medium: /\b(problem|issue|trouble|wrong|incorrect|invalid|timeout|unavailable)\b/gi,
    low: /\b(warning|notice|alert|unexpected|unusual)\b/gi,
  },
  security: {
    high: /\b(security|breach|hack|exploit|vulnerability|attack|malicious|unauthorized|credential|secret|key|token|password|auth)\b/gi,
    medium: /\b(permission|access|role|policy|firewall|encryption|ssl|tls)\b/gi,
    low: /\b(user|login|session|cookie)\b/gi,
  },
  financial: {
    high: /\b(payment|billing|charge|cost|price|money|revenue|profit|loss|budget|finance|invoice|transaction|bank)\b/gi,
    medium: /\b(subscription|plan|tier|upgrade|downgrade|refund)\b/gi,
    low: /\b(usage|limit|quota|meter)\b/gi,
  },
  infrastructure: {
    high: /\b(deploy|deployment|infrastructure|server|database|production|outage|downtime|maintenance|backup|restore)\b/gi,
    medium: /\b(service|api|endpoint|health|status|monitoring|scaling|load)\b/gi,
    low: /\b(config|configuration|settings|environment|network)\b/gi,
  },
};

/**
 * Context severity weights
 */
const SEVERITY_WEIGHTS = {
  high: 3,
  medium: 2,
  low: 1,
};

export class ContextEnforcer {
  private enforcementLog: EnforcementAction[] = [];
  private maxLogSize = 100;

  constructor(private personaConfig: PersonaConfig) {}

  /**
   * Analyze context from multiple sources
   */
  analyzeContext(sources: {
    message?: string;
    prompt?: string;
    metadata?: Record<string, any>;
    route?: string;
    errorDetails?: string;
  }): ContextAnalysis {
    const allText = [
      sources.message || '',
      sources.prompt || '',
      sources.route || '',
      sources.errorDetails || '',
      JSON.stringify(sources.metadata || {}),
    ].join(' ').toLowerCase();

    const analysis: ContextAnalysis = {
      isError: false,
      isSecurity: false,
      isFinancial: false,
      isInfraOp: false,
      severity: 'low',
      detectedKeywords: [],
      confidence: 0,
    };

    let maxSeverityWeight = 0;
    let totalMatches = 0;

    // Analyze each context type
    Object.entries(CONTEXT_PATTERNS).forEach(([contextType, patterns]) => {
      let contextMatches = 0;
      let contextSeverityWeight = 0;

      Object.entries(patterns).forEach(([severity, pattern]) => {
        const matches = allText.match(pattern) || [];
        if (matches.length > 0) {
          analysis.detectedKeywords.push(...matches);
          contextMatches += matches.length;
          contextSeverityWeight = Math.max(
            contextSeverityWeight,
            SEVERITY_WEIGHTS[severity as keyof typeof SEVERITY_WEIGHTS]
          );
        }
      });

      if (contextMatches > 0) {
        // Explicitly set context flags
        switch (contextType) {
          case 'error':
            analysis.isError = true;
            break;
          case 'security':
            analysis.isSecurity = true;
            break;
          case 'financial':
            analysis.isFinancial = true;
            break;
          case 'infrastructure':
            analysis.isInfraOp = true;
            break;
        }
        totalMatches += contextMatches;
        maxSeverityWeight = Math.max(maxSeverityWeight, contextSeverityWeight);
      }
    });

    // Determine overall severity
    if (maxSeverityWeight >= 3) {
      analysis.severity = 'high';
    } else if (maxSeverityWeight >= 2) {
      analysis.severity = 'medium';
    }

    // Calculate confidence based on number of matches and text length
    const textLength = allText.length;
    const matchDensity = textLength > 0 ? totalMatches / (textLength / 100) : 0;
    analysis.confidence = Math.min(1, Math.max(0, matchDensity / 5 + (totalMatches > 0 ? 0.3 : 0)));

    return analysis;
  }

  /**
   * Determine if humor should be enforced to zero
   */
  shouldEnforceHumorZero(context: ContextAnalysis): EnforcementAction {
    const { contextAwareness } = this.personaConfig;
    const originalHumorLevel = this.personaConfig.humorLevel;

    const contextFlags: string[] = [];
    let shouldEnforce = false;
    let reason = '';

    // Check each context type against persona settings
    if (context.isError && contextAwareness.disableHumorInErrors) {
      shouldEnforce = true;
      contextFlags.push('error');
      reason = 'Error context detected';
    }

    if (context.isSecurity && contextAwareness.disableHumorInSecurity) {
      shouldEnforce = true;
      contextFlags.push('security');
      reason = reason ? `${reason}, security context detected` : 'Security context detected';
    }

    if (context.isFinancial && contextAwareness.disableHumorInFinancial) {
      shouldEnforce = true;
      contextFlags.push('financial');
      reason = reason ? `${reason}, financial context detected` : 'Financial context detected';
    }

    if (context.isInfraOp && contextAwareness.disableHumorInInfraOps) {
      shouldEnforce = true;
      contextFlags.push('infrastructure');
      reason = reason ? `${reason}, infrastructure context detected` : 'Infrastructure context detected';
    }

    // Enhanced enforcement for high-severity contexts
    if (shouldEnforce && context.severity === 'high' && context.confidence > 0.7) {
      reason += ` (high-severity, confidence: ${context.confidence.toFixed(2)})`;
    }

    const action: EnforcementAction = {
      shouldEnforce,
      originalHumorLevel,
      enforcedHumorLevel: shouldEnforce ? 0 : originalHumorLevel,
      reason: reason || 'No sensitive context detected',
      contextFlags,
    };

    // Log the enforcement action
    this.logEnforcement(action);

    return action;
  }

  /**
   * Apply enforcement to persona config (returns modified copy)
   */
  applyEnforcement(context: ContextAnalysis): PersonaConfig {
    const enforcement = this.shouldEnforceHumorZero(context);
    
    if (!enforcement.shouldEnforce) {
      return { ...this.personaConfig };
    }

    return {
      ...this.personaConfig,
      humorLevel: 0,
      // Also increase formality slightly in sensitive contexts
      formality: Math.min(1, this.personaConfig.formality + 0.1),
    };
  }

  /**
   * Quick check for sensitive context from message text only
   */
  isSensitiveContext(message: string): boolean {
    const context = this.analyzeContext({ message });
    const enforcement = this.shouldEnforceHumorZero(context);
    return enforcement.shouldEnforce;
  }

  /**
   * Get enforcement statistics
   */
  getEnforcementStats(): {
    totalEnforcements: number;
    byContext: Record<string, number>;
    recentEnforcements: EnforcementAction[];
  } {
    const byContext: Record<string, number> = {};
    let totalEnforcements = 0;

    this.enforcementLog.forEach(action => {
      if (action.shouldEnforce) {
        totalEnforcements++;
        action.contextFlags.forEach(flag => {
          byContext[flag] = (byContext[flag] || 0) + 1;
        });
      }
    });

    return {
      totalEnforcements,
      byContext,
      recentEnforcements: this.enforcementLog.slice(-10),
    };
  }

  /**
   * Log enforcement action
   */
  private logEnforcement(action: EnforcementAction): void {
    this.enforcementLog.push({
      ...action,
      // Add timestamp for debugging
      ...{ timestamp: new Date().toISOString() },
    });

    // Keep log size manageable
    if (this.enforcementLog.length > this.maxLogSize) {
      this.enforcementLog = this.enforcementLog.slice(-this.maxLogSize);
    }
  }

  /**
   * Update persona configuration
   */
  updatePersonaConfig(config: PersonaConfig): void {
    this.personaConfig = config;
  }

  /**
   * Clear enforcement log
   */
  clearLog(): void {
    this.enforcementLog = [];
  }
}

/**
 * Factory function for creating context enforcer
 */
export function createContextEnforcer(config: PersonaConfig): ContextEnforcer {
  return new ContextEnforcer(config);
}

/**
 * Utility function for quick context checking
 */
export function isHumorSafeContext(
  message: string, 
  config: PersonaConfig,
  additionalSources?: Record<string, any>
): boolean {
  const enforcer = new ContextEnforcer(config);
  const context = enforcer.analyzeContext({ 
    message, 
    ...additionalSources 
  });
  return !enforcer.shouldEnforceHumorZero(context).shouldEnforce;
}