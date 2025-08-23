/**
 * Sophia AI Tone Middleware
 * Post-processes messages with personality and tone adjustments
 */

import { PersonaConfig, personaConfigManager } from './personaConfig';
import { ContextEnforcer, createContextEnforcer } from '../../../../libs/persona/contextEnforcer';

export interface MessageContext {
  isError?: boolean;
  isSecurity?: boolean;
  isFinancial?: boolean;
  isInfraOp?: boolean;
  messageType?: 'response' | 'error' | 'info' | 'warning';
  originalPrompt?: string;
}

export interface ToneProcessingResult {
  processedMessage: string;
  humorAdded: boolean;
  toneAdjustments: string[];
  metadata: {
    originalLength: number;
    processedLength: number;
    formality: number;
    terseness: number;
  };
}

/**
 * Collection of dry, clever one-liners for appropriate contexts
 */
const CLEVER_QUIPS = [
  "Consider this the plan. It's like a Swiss watch—accurate, tiny moving parts, and mildly expensive if ignored.",
  "This should work nicely. Famous last words, but the math checks out.",
  "The approach is solid. Think of it as defensive coding for your sanity.",
  "Here's the strategy. It's battle-tested, assuming the battle was against predictable problems.",
  "Implementation complete. Now we wait to see what creative ways it finds to surprise us.",
  "The solution is elegant. By elegant, I mean it works and doesn't require a PhD to understand.",
  "Ready to deploy. The servers are standing by, probably wondering what we're up to this time.",
  "Task finished. Filed under 'things that should have been simpler but weren't.'",
  "All systems go. Which is engineer-speak for 'crossing fingers behind back.'",
  "Configuration updated. The infrastructure is now slightly more aware of what it's supposed to do."
];

/**
 * Patterns that indicate sensitive contexts where humor should be avoided
 */
const SENSITIVE_PATTERNS = {
  error: /\b(error|failed|failure|exception|crash|broke|broken|problem|issue)\b/i,
  security: /\b(security|auth|token|key|secret|password|credential|vulnerability|breach)\b/i,
  financial: /\b(payment|billing|cost|charge|money|price|invoice|revenue|finance)\b/i,
  infraOp: /\b(deploy|deployment|infrastructure|server|database|production|outage|downtime)\b/i,
};

export class ToneMiddleware {
  private lastHumorIndex: number = -1;
  private messageCount: number = 0;
  private sessionHumorCount: number = 0;
  private contextEnforcer: ContextEnforcer;

  constructor(private configManager: typeof personaConfigManager) {
    this.contextEnforcer = createContextEnforcer(this.configManager.getConfig());
  }

  /**
   * Main processing function for applying tone adjustments
   */
  async processMessage(
    message: string,
    context: MessageContext = {}
  ): Promise<ToneProcessingResult> {
    this.messageCount++;
    this.configManager.incrementMessageCount();

    // Update context enforcer with latest config
    this.contextEnforcer.updatePersonaConfig(this.configManager.getConfig());

    // Advanced context analysis using the enforcer
    const contextAnalysis = this.contextEnforcer.analyzeContext({
      message,
      prompt: context.originalPrompt,
      metadata: { messageType: context.messageType },
    });

    // Apply humor enforcement if needed
    const enforcement = this.contextEnforcer.shouldEnforceHumorZero(contextAnalysis);
    const enforcedConfig = enforcement.shouldEnforce
      ? this.contextEnforcer.applyEnforcement(contextAnalysis)
      : this.configManager.getConfig();

    // Get tone profile from potentially modified config
    const toneProfile = {
      formality: enforcedConfig.formality,
      terseness: enforcedConfig.terseness,
      warmth: Math.max(0.2, 1 - enforcedConfig.formality),
    };
    
    let processedMessage = message;
    const toneAdjustments: string[] = [];
    let humorAdded = false;

    // Log enforcement if applied
    if (enforcement.shouldEnforce) {
      toneAdjustments.push(`humor-enforcement: ${enforcement.reason}`);
    }

    // Detect context automatically if not provided (legacy detection)
    const detectedContext = this.detectMessageContext(message);
    const finalContext = { ...detectedContext, ...context };

    // Apply formality adjustments
    if (toneProfile.formality !== 0.5) {
      processedMessage = this.adjustFormality(processedMessage, toneProfile.formality);
      toneAdjustments.push(`formality: ${toneProfile.formality}`);
    }

    // Apply terseness adjustments
    if (toneProfile.terseness > 0.5) {
      processedMessage = this.applyTerseness(processedMessage, toneProfile.terseness);
      toneAdjustments.push(`terseness: ${toneProfile.terseness}`);
    }

    // Add humor only if not enforced to zero
    if (!enforcement.shouldEnforce && this.shouldAddHumor(finalContext, enforcedConfig.humorLevel)) {
      const humorResult = this.addCleverHumor(processedMessage);
      if (humorResult.humorAdded) {
        processedMessage = humorResult.message;
        humorAdded = true;
        this.sessionHumorCount++;
        this.configManager.recordHumorUsed();
        toneAdjustments.push('humor: subtle');
      }
    } else if (enforcement.shouldEnforce) {
      toneAdjustments.push('humor: disabled (sensitive context)');
    }

    return {
      processedMessage,
      humorAdded,
      toneAdjustments,
      metadata: {
        originalLength: message.length,
        processedLength: processedMessage.length,
        formality: toneProfile.formality,
        terseness: toneProfile.terseness,
      },
    };
  }

  /**
   * Detect context from message content
   */
  private detectMessageContext(message: string): MessageContext {
    return {
      isError: SENSITIVE_PATTERNS.error.test(message),
      isSecurity: SENSITIVE_PATTERNS.security.test(message),
      isFinancial: SENSITIVE_PATTERNS.financial.test(message),
      isInfraOp: SENSITIVE_PATTERNS.infraOp.test(message),
    };
  }

  /**
   * Determine if humor should be added based on context and config
   * Enhanced with humor level parameter
   */
  private shouldAddHumor(context: MessageContext, humorLevel?: number): boolean {
    const currentHumorLevel = humorLevel ?? this.configManager.getConfig().humorLevel;
    
    // If humor level is 0, never use humor
    if (currentHumorLevel <= 0) return false;
    
    return this.configManager.shouldUseHumor(context);
  }

  /**
   * Adjust message formality level
   */
  private adjustFormality(message: string, formality: number): string {
    if (formality > 0.7) {
      // High formality: add professional language
      return message
        .replace(/\bi think\b/gi, 'I believe')
        .replace(/\bguys\b/gi, 'team members')
        .replace(/\bokay\b/gi, 'very well')
        .replace(/\blet's\b/gi, 'let us')
        .replace(/\bcan't\b/gi, 'cannot')
        .replace(/\bwon't\b/gi, 'will not');
    } else if (formality < 0.3) {
      // Low formality: make more casual
      return message
        .replace(/\bI believe\b/gi, 'I think')
        .replace(/\bvery well\b/gi, 'okay')
        .replace(/\bcannot\b/gi, "can't")
        .replace(/\bwill not\b/gi, "won't");
    }
    return message;
  }

  /**
   * Apply terseness by reducing hedging and unnecessary words
   */
  private applyTerseness(message: string, terseness: number): string {
    if (terseness < 0.5) return message;

    let processed = message;

    // Remove hedging phrases based on terseness level
    const hedgingPhrases = [
      /\b(I think that |I believe that |It seems that |It appears that |I would say that )/gi,
      /\b(sort of |kind of |pretty much |more or less |essentially |basically )/gi,
      /\b(In my opinion, |From my perspective, |I would suggest that |I might recommend )/gi,
    ];

    const intensityThreshold = (1 - terseness) * hedgingPhrases.length;
    hedgingPhrases.slice(0, Math.ceil(intensityThreshold)).forEach(pattern => {
      processed = processed.replace(pattern, '');
    });

    // Remove redundant phrases for high terseness
    if (terseness > 0.7) {
      processed = processed
        .replace(/\b(please note that |it's worth mentioning that |I should point out that )/gi, '')
        .replace(/\b(as you can see |as mentioned |as discussed )/gi, '')
        .replace(/\b(in order to |so as to )/gi, 'to ')
        .replace(/\b(due to the fact that |owing to the fact that )/gi, 'because ');
    }

    // Clean up extra spaces
    return processed.replace(/\s+/g, ' ').trim();
  }

  /**
   * Add subtle, context-appropriate humor
   */
  private addCleverHumor(message: string): { message: string; humorAdded: boolean } {
    // Don't add humor to very short messages
    if (message.length < 50) {
      return { message, humorAdded: false };
    }

    // Select a random quip
    const availableQuips = CLEVER_QUIPS.filter(quip => 
      !message.toLowerCase().includes(quip.toLowerCase().slice(0, 10))
    );

    if (availableQuips.length === 0) {
      return { message, humorAdded: false };
    }

    const quip = availableQuips[Math.floor(Math.random() * availableQuips.length)];
    
    // Add the quip at the end with appropriate spacing
    const enhanced = `${message}\n\n${quip}`;
    
    return { message: enhanced, humorAdded: true };
  }

  /**
   * Reset session state
   */
  resetSession(): void {
    this.lastHumorIndex = -1;
    this.messageCount = 0;
    this.sessionHumorCount = 0;
    this.configManager.resetSession();
  }

  /**
   * Get session statistics
   */
  getSessionStats(): {
    messageCount: number;
    humorCount: number;
    humorRate: number;
    enforcementStats: any;
  } {
    return {
      messageCount: this.messageCount,
      humorCount: this.sessionHumorCount,
      humorRate: this.messageCount > 0 ? this.sessionHumorCount / this.messageCount : 0,
      enforcementStats: this.contextEnforcer.getEnforcementStats(),
    };
  }

  /**
   * Check if a message would trigger humor enforcement
   */
  wouldEnforceHumor(message: string, additionalContext?: Record<string, any>): boolean {
    const analysis = this.contextEnforcer.analyzeContext({
      message,
      ...additionalContext,
    });
    return this.contextEnforcer.shouldEnforceHumorZero(analysis).shouldEnforce;
  }
}

// Export singleton instance
export const toneMiddleware = new ToneMiddleware(personaConfigManager);

/**
 * Convenience function for quick message processing
 */
export async function processMessageTone(
  message: string,
  context?: MessageContext
): Promise<ToneProcessingResult> {
  return toneMiddleware.processMessage(message, context);
}

/**
 * Test if a message context should disable humor
 */
export function shouldDisableHumor(message: string, context: MessageContext = {}): boolean {
  const detectedContext = {
    isError: SENSITIVE_PATTERNS.error.test(message),
    isSecurity: SENSITIVE_PATTERNS.security.test(message),
    isFinancial: SENSITIVE_PATTERNS.financial.test(message),
    isInfraOp: SENSITIVE_PATTERNS.infraOp.test(message),
    ...context,
  };

  return !personaConfigManager.shouldUseHumor(detectedContext);
}
