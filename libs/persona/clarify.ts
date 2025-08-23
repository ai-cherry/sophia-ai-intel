/**
 * Sophia AI Clarifying Question Policy
 * Determines when and how to ask clarifying questions based on ambiguity analysis
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

export interface AmbiguityAnalysis {
  intentClarity: number; // 0-1, higher = clearer intent
  constraintCompleteness: number; // 0-1, higher = more complete constraints
  contextSufficiency: number; // 0-1, higher = sufficient context
  overallScore: number; // 0-1, higher = less ambiguous
  ambiguityFactors: AmbiguityFactor[];
}

export interface AmbiguityFactor {
  type: 'missing_context' | 'unclear_intent' | 'incomplete_constraints' | 'conflicting_requirements' | 'scope_undefined';
  description: string;
  severity: 'low' | 'medium' | 'high';
  suggestion: string;
}

export interface ClarificationDecision {
  shouldAsk: boolean;
  type: 'none' | 'targeted' | 'with-default';
  question?: string;
  suggestedAnswers?: string[];
  defaultAssumption?: string;
  reasoning: string;
}

export interface ClarificationContext {
  domain: string;
  userExpertise: 'beginner' | 'intermediate' | 'expert';
  urgency: 'low' | 'medium' | 'high';
  previousInteractions: number;
  hasTimeConstraints: boolean;
}

/**
 * Analyzes message ambiguity using enhanced prompt pipeline outputs
 */
export class AmbiguityAnalyzer {
  constructor(private config: PersonaConfig) {}

  /**
   * Analyze ambiguity from prompt enhancer outputs
   */
  analyzeAmbiguity(
    intent: string,
    context: string,
    constraints: string[],
    originalPrompt: string
  ): AmbiguityAnalysis {
    const factors: AmbiguityFactor[] = [];
    
    // Analyze intent clarity
    const intentClarity = this.analyzeIntentClarity(intent, factors);
    
    // Analyze constraint completeness
    const constraintCompleteness = this.analyzeConstraintCompleteness(constraints, factors);
    
    // Analyze context sufficiency
    const contextSufficiency = this.analyzeContextSufficiency(context, originalPrompt, factors);
    
    // Calculate overall ambiguity score
    const overallScore = this.calculateOverallScore(intentClarity, constraintCompleteness, contextSufficiency);

    return {
      intentClarity,
      constraintCompleteness,
      contextSufficiency,
      overallScore,
      ambiguityFactors: factors,
    };
  }

  /**
   * Analyze how clear the user's intent is
   */
  private analyzeIntentClarity(intent: string, factors: AmbiguityFactor[]): number {
    let clarity = 0.8; // Start with reasonable baseline

    // Check for vague language
    const vaguePatterns = [
      /\b(maybe|perhaps|might|could|sort of|kind of|somewhat)\b/i,
      /\b(better|improve|fix|enhance|optimize)\b/i, // without specificity
      /\b(something|anything|whatever)\b/i,
    ];

    vaguePatterns.forEach(pattern => {
      if (pattern.test(intent)) {
        clarity -= 0.15;
        factors.push({
          type: 'unclear_intent',
          description: 'Intent contains vague or non-specific language',
          severity: 'medium',
          suggestion: 'Ask for specific goals or outcomes'
        });
      }
    });

    // Check for action words (good for clarity)
    const actionPatterns = [
      /\b(create|build|implement|deploy|configure|setup|add|remove|update|modify)\b/i,
    ];

    let hasActionWords = false;
    actionPatterns.forEach(pattern => {
      if (pattern.test(intent)) {
        hasActionWords = true;
        clarity += 0.1;
      }
    });

    if (!hasActionWords && intent.length > 20) {
      factors.push({
        type: 'unclear_intent',
        description: 'Intent lacks clear action words',
        severity: 'medium',
        suggestion: 'Clarify what specific action should be taken'
      });
    }

    return Math.max(0, Math.min(1, clarity));
  }

  /**
   * Analyze completeness of constraints
   */
  private analyzeConstraintCompleteness(constraints: string[], factors: AmbiguityFactor[]): number {
    let completeness = 0.6; // Start with moderate baseline

    // More constraints generally indicate better specification
    if (constraints.length >= 3) {
      completeness += 0.2;
    } else if (constraints.length === 0) {
      completeness -= 0.3;
      factors.push({
        type: 'incomplete_constraints',
        description: 'No constraints specified',
        severity: 'high',
        suggestion: 'Clarify requirements, timeline, or technical constraints'
      });
    }

    // Check for important constraint types
    const constraintTypes = {
      timeline: /\b(deadline|timeline|urgent|asap|quickly|time)\b/i,
      technical: /\b(technology|framework|language|platform|version)\b/i,
      scope: /\b(scope|feature|functionality|requirement)\b/i,
      quality: /\b(quality|performance|security|scalability)\b/i,
    };

    const foundTypes = Object.entries(constraintTypes).filter(([, pattern]) =>
      constraints.some(constraint => pattern.test(constraint))
    ).map(([type]) => type);

    if (foundTypes.length >= 2) {
      completeness += 0.2;
    } else if (foundTypes.length === 0) {
      factors.push({
        type: 'incomplete_constraints',
        description: 'Missing key constraint types (timeline, technical, scope)',
        severity: 'medium',
        suggestion: 'Specify timeline, technical requirements, or scope boundaries'
      });
    }

    return Math.max(0, Math.min(1, completeness));
  }

  /**
   * Analyze sufficiency of context
   */
  private analyzeContextSufficiency(context: string, originalPrompt: string, factors: AmbiguityFactor[]): number {
    let sufficiency = 0.7; // Start with reasonable baseline

    // Length-based heuristics
    if (context.length < 50) {
      sufficiency -= 0.3;
      factors.push({
        type: 'missing_context',
        description: 'Minimal context provided',
        severity: 'high',
        suggestion: 'Provide more background or context about the situation'
      });
    } else if (context.length > 200) {
      sufficiency += 0.1;
    }

    // Check for domain-specific context
    const domainPatterns = {
      technical: /\b(code|system|architecture|database|api|service)\b/i,
      business: /\b(customer|user|business|revenue|strategy|goal)\b/i,
      process: /\b(workflow|process|step|procedure|method)\b/i,
    };

    const foundDomains = Object.entries(domainPatterns).filter(([, pattern]) =>
      pattern.test(context) || pattern.test(originalPrompt)
    ).length;

    if (foundDomains >= 1) {
      sufficiency += 0.1;
    }

    // Check for references to existing systems/files
    if (/\b(current|existing|we have|already)\b/i.test(context) && 
        !/\b(file|system|implementation|version)\b/i.test(context)) {
      factors.push({
        type: 'missing_context',
        description: 'References existing systems without sufficient detail',
        severity: 'medium',
        suggestion: 'Provide details about existing systems or implementations'
      });
      sufficiency -= 0.2;
    }

    return Math.max(0, Math.min(1, sufficiency));
  }

  /**
   * Calculate overall ambiguity score
   */
  private calculateOverallScore(
    intentClarity: number,
    constraintCompleteness: number,
    contextSufficiency: number
  ): number {
    // Weighted average - intent is most important
    return (intentClarity * 0.5) + (constraintCompleteness * 0.3) + (contextSufficiency * 0.2);
  }
}

/**
 * Determines clarification strategy based on ambiguity analysis
 */
export class ClarificationPolicy {
  constructor(
    private config: PersonaConfig,
    private analyzer: AmbiguityAnalyzer
  ) {}

  /**
   * Make clarification decision based on analysis and context
   */
  makeClarificationDecision(
    analysis: AmbiguityAnalysis,
    context: ClarificationContext
  ): ClarificationDecision {
    const { overallScore, ambiguityFactors } = analysis;
    const { followUpPolicy } = this.config;

    // Apply persona-aware humor constraints to clarification context
    const humorDisallowedContext = this.isHumorDisallowed(context, ambiguityFactors);
    
    // Never ask if policy is set to never
    if (followUpPolicy === 'never') {
      return {
        shouldAsk: false,
        type: 'none',
        reasoning: 'Follow-up policy set to never ask clarifying questions',
        defaultAssumption: this.generatePersonaAwareAssumption(analysis, context)
      };
    }

    // Always ask if policy is set to always
    if (followUpPolicy === 'always') {
      return this.generatePersonaAwareClarificationQuestion(analysis, context,
        overallScore > 0.7 ? 'targeted' : 'with-default', humorDisallowedContext);
    }

    // Apply persona-adjusted ambiguity thresholds
    const adjustedThresholds = this.getPersonaAdjustedThresholds();
    
    if (overallScore >= adjustedThresholds.high) {
      // Low ambiguity - proceed with assumption
      return {
        shouldAsk: false,
        type: 'none',
        reasoning: `Low ambiguity (score: ${overallScore.toFixed(2)}) - proceeding with persona-informed assumption`,
        defaultAssumption: this.generatePersonaAwareAssumption(analysis, context)
      };
    } else if (overallScore >= adjustedThresholds.medium) {
      // Medium ambiguity - ask targeted question
      return this.generatePersonaAwareClarificationQuestion(analysis, context, 'targeted', humorDisallowedContext);
    } else {
      // High ambiguity - ask question with default
      return this.generatePersonaAwareClarificationQuestion(analysis, context, 'with-default', humorDisallowedContext);
    }
  }

  /**
   * Generate appropriate clarification question
   */
  private generateClarificationQuestion(
    analysis: AmbiguityAnalysis,
    context: ClarificationContext,
    type: 'targeted' | 'with-default'
  ): ClarificationDecision {
    const { ambiguityFactors } = analysis;
    
    // Find the most severe ambiguity factor
    const primaryFactor = ambiguityFactors
      .sort((a, b) => this.getSeverityWeight(b.severity) - this.getSeverityWeight(a.severity))[0];

    if (!primaryFactor) {
      return {
        shouldAsk: false,
        type: 'none',
        reasoning: 'No significant ambiguity factors identified'
      };
    }

    const question = this.generateQuestionFromFactor(primaryFactor, context);
    const suggestedAnswers = this.generateSuggestedAnswers(primaryFactor, context);
    const defaultAssumption = type === 'with-default' 
      ? this.generateDefaultAssumption(analysis, context)
      : undefined;

    return {
      shouldAsk: true,
      type,
      question,
      suggestedAnswers,
      defaultAssumption,
      reasoning: `${primaryFactor.severity} ambiguity in ${primaryFactor.type}: ${primaryFactor.description}`
    };
  }

  /**
   * Generate question based on ambiguity factor
   */
  private generateQuestionFromFactor(
    factor: AmbiguityFactor,
    context: ClarificationContext
  ): string {
    const templates = {
      missing_context: [
        "What's the current state of the system or project?",
        "Can you provide more details about the existing setup?",
        "What context should I know about your environment?"
      ],
      unclear_intent: [
        "What specific outcome are you looking for?",
        "What exactly should be accomplished?",
        "What's the primary goal here?"
      ],
      incomplete_constraints: [
        "Are there any timeline or technical constraints I should know about?",
        "What are the key requirements or limitations?",
        "Do you have preferences for technology or approach?"
      ],
      conflicting_requirements: [
        "I see some conflicting requirements - which takes priority?",
        "How should I handle the trade-off between these requirements?",
        "Which requirement is most critical?"
      ],
      scope_undefined: [
        "What's the scope of this work?",
        "How comprehensive should this solution be?",
        "What are the boundaries of what needs to be done?"
      ]
    };

    const options = templates[factor.type] || templates.unclear_intent;
    return options[0]; // Use first option for consistency
  }

  /**
   * Generate suggested answers
   */
  private generateSuggestedAnswers(
    factor: AmbiguityFactor,
    context: ClarificationContext
  ): string[] {
    // Generate context-appropriate suggested answers
    switch (factor.type) {
      case 'unclear_intent':
        return [
          "Build a complete solution",
          "Make minimal changes to existing system"
        ];
      case 'incomplete_constraints':
        return [
          "No timeline constraints - focus on quality",
          "Need it done quickly with basic functionality"
        ];
      case 'missing_context':
        return [
          "This is a new project/greenfield",
          "Working with existing system that needs modification"
        ];
      default:
        return [
          "Option A (recommended)",
          "Option B (alternative approach)"
        ];
    }
  }

  /**
   * Generate default assumption when not asking questions
   */
  private generateDefaultAssumption(
    analysis: AmbiguityAnalysis,
    context: ClarificationContext
  ): string {
    const assumptions = [
      "Assuming standard best practices apply",
      "Proceeding with moderate scope and timeline",
      "Using established patterns and technologies"
    ];

    // Customize based on domain
    if (context.domain === 'technical') {
      assumptions.push("Following existing architectural patterns");
    } else if (context.domain === 'business') {
      assumptions.push("Prioritizing user value and business impact");
    }

    return assumptions[0];
  }

  /**
   * Get numeric weight for severity levels
   */
  private getSeverityWeight(severity: 'low' | 'medium' | 'high'): number {
    switch (severity) {
      case 'high': return 3;
      case 'medium': return 2;
      case 'low': return 1;
      default: return 0;
    }
  }
}

/**
 * Main clarification service
 */
export class ClarificationService {
  private analyzer: AmbiguityAnalyzer;
  private policy: ClarificationPolicy;

  constructor(config: PersonaConfig) {
    this.analyzer = new AmbiguityAnalyzer(config);
    this.policy = new ClarificationPolicy(config, this.analyzer);
  }

  /**
   * Analyze and decide on clarification for a given prompt
   */
  processClarificationRequest(
    intent: string,
    context: string,
    constraints: string[],
    originalPrompt: string,
    clarificationContext: ClarificationContext
  ): ClarificationDecision {
    const analysis = this.analyzer.analyzeAmbiguity(intent, context, constraints, originalPrompt);
    return this.policy.makeClarificationDecision(analysis, clarificationContext);
  }

  /**
   * Update configuration
   */
  updateConfig(config: PersonaConfig): void {
    this.analyzer = new AmbiguityAnalyzer(config);
    this.policy = new ClarificationPolicy(config, this.analyzer);
  }

  /**
   * Get current persona configuration
   */
  getPersonaConfig(): PersonaConfig {
    return this.analyzer['config']; // Access private config
  }
}

/**
 * Extended ClarificationPolicy with persona integration methods
 */
declare module './clarify' {
  interface ClarificationPolicy {
    isHumorDisallowed(context: ClarificationContext, factors: AmbiguityFactor[]): boolean;
    getPersonaAdjustedThresholds(): { high: number; medium: number };
    generatePersonaAwareAssumption(analysis: AmbiguityAnalysis, context: ClarificationContext): string;
    generatePersonaAwareClarificationQuestion(
      analysis: AmbiguityAnalysis,
      context: ClarificationContext,
      type: 'targeted' | 'with-default',
      humorDisallowed: boolean
    ): ClarificationDecision;
  }
}

// Add methods to ClarificationPolicy prototype
Object.assign(ClarificationPolicy.prototype, {
  /**
   * Check if humor should be disallowed based on context and factors
   */
  isHumorDisallowed(context: ClarificationContext, factors: AmbiguityFactor[]): boolean {
    // Check for sensitive context types
    const sensitiveTypes = ['error', 'security', 'financial', 'infrastructure'];
    const hasSensitiveContext = sensitiveTypes.some(type =>
      context.domain?.toLowerCase().includes(type) ||
      factors.some(f => f.description.toLowerCase().includes(type))
    );

    // Apply persona's contextAwareness settings
    return hasSensitiveContext && (
      (context.domain?.includes('error') && this.config.contextAwareness.disableHumorInErrors) ||
      (context.domain?.includes('security') && this.config.contextAwareness.disableHumorInSecurity) ||
      (context.domain?.includes('financial') && this.config.contextAwareness.disableHumorInFinancial) ||
      (context.domain?.includes('infrastructure') && this.config.contextAwareness.disableHumorInInfraOps)
    );
  },

  /**
   * Get persona-adjusted ambiguity thresholds
   */
  getPersonaAdjustedThresholds(): { high: number; medium: number } {
    // Base thresholds
    let highThreshold = 0.65;
    let mediumThreshold = 0.35;

    // Adjust based on formality (more formal = ask fewer questions)
    if (this.config.formality > 0.7) {
      highThreshold += 0.1;
      mediumThreshold += 0.1;
    } else if (this.config.formality < 0.3) {
      highThreshold -= 0.1;
      mediumThreshold -= 0.05;
    }

    // Adjust based on terseness (more terse = higher bar for questions)
    if (this.config.terseness > 0.7) {
      highThreshold += 0.15;
      mediumThreshold += 0.1;
    }

    return {
      high: Math.min(0.9, Math.max(0.3, highThreshold)),
      medium: Math.min(0.7, Math.max(0.1, mediumThreshold))
    };
  },

  /**
   * Generate persona-aware default assumption
   */
  generatePersonaAwareAssumption(analysis: AmbiguityAnalysis, context: ClarificationContext): string {
    const baseAssumption = this.generateDefaultAssumption(analysis, context);
    
    // Adjust assumption tone based on persona
    if (this.config.formality > 0.7) {
      return `Based on analysis: ${baseAssumption}`;
    } else if (this.config.formality < 0.3) {
      return `Going with: ${baseAssumption}`;
    }
    
    return baseAssumption;
  },

  /**
   * Generate persona-aware clarification question
   */
  generatePersonaAwareClarificationQuestion(
    analysis: AmbiguityAnalysis,
    context: ClarificationContext,
    type: 'targeted' | 'with-default',
    humorDisallowed: boolean
  ): ClarificationDecision {
    const baseDecision = this.generateClarificationQuestion(analysis, context, type);
    
    if (!baseDecision.question) return baseDecision;

    // Adjust question tone based on persona
    let adjustedQuestion = baseDecision.question;
    
    if (this.config.formality > 0.7) {
      adjustedQuestion = adjustedQuestion
        .replace(/^What's/, 'What is')
        .replace(/Can you/, 'Could you please')
        .replace(/\?$/, ', if you would?');
    } else if (this.config.formality < 0.3) {
      adjustedQuestion = adjustedQuestion
        .replace(/Could you please/, 'Can you')
        .replace(/What is/, "What's");
    }

    // Apply terseness
    if (this.config.terseness > 0.7) {
      adjustedQuestion = adjustedQuestion
        .replace(/\b(please|if you would|kindly)\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
    }

    // Remove any humor if context disallows it
    if (humorDisallowed && this.config.humorLevel > 0) {
      // Strip casual language that might be perceived as humorous
      adjustedQuestion = adjustedQuestion
        .replace(/\b(just|simply|basically)\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
    }

    return {
      ...baseDecision,
      question: adjustedQuestion,
      reasoning: `${baseDecision.reasoning} (persona-adjusted: formality=${this.config.formality}, terseness=${this.config.terseness}, humor=${humorDisallowed ? 'disabled' : 'enabled'})`
    };
  }
});

// Export factory function
export function createClarificationService(config: PersonaConfig): ClarificationService {
  return new ClarificationService(config);
}