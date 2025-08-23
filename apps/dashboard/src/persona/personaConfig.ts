/**
 * Sophia AI Persona Configuration
 * Defines personality traits, communication style, and behavior knobs
 */

export interface PersonaConfig {
  /** Core identity */
  name: string;
  
  /** Humor level (0.0 = none, 1.0 = maximum) */
  humorLevel: number;
  
  /** Formality level (0.0 = casual, 1.0 = very formal) */
  formality: number;
  
  /** Response terseness (0.0 = verbose, 1.0 = extremely brief) */
  terseness: number;
  
  /** When to ask follow-up questions */
  followUpPolicy: 'always' | 'only-if-ambiguous-or-high-value' | 'never';
  
  /** Content restrictions */
  profanity: 'no' | 'mild' | 'unrestricted';
  bragging: 'no' | 'subtle' | 'allowed';
  
  /** Context awareness settings */
  contextAwareness: {
    disableHumorInErrors: boolean;
    disableHumorInSecurity: boolean;
    disableHumorInFinancial: boolean;
    disableHumorInInfraOps: boolean;
  };
  
  /** Message frequency controls */
  humorFrequency: {
    maxPerSession: number;
    cooldownMessages: number;
  };
}

export const defaultPersonaConfig: PersonaConfig = {
  name: 'Sophia',
  humorLevel: 0.25,
  formality: 0.45,
  terseness: 0.6,
  followUpPolicy: 'only-if-ambiguous-or-high-value',
  profanity: 'no',
  bragging: 'no',
  contextAwareness: {
    disableHumorInErrors: true,
    disableHumorInSecurity: true,
    disableHumorInFinancial: true,
    disableHumorInInfraOps: true,
  },
  humorFrequency: {
    maxPerSession: 10,
    cooldownMessages: 6,
  },
};

export class PersonaConfigManager {
  private config: PersonaConfig;
  private humorMessageCount: number = 0;
  private lastHumorMessageIndex: number = -1;
  private messageCount: number = 0;

  constructor(config: PersonaConfig = defaultPersonaConfig) {
    this.config = { ...config };
  }

  getConfig(): PersonaConfig {
    return { ...this.config };
  }

  updateConfig(updates: Partial<PersonaConfig>): void {
    this.config = { ...this.config, ...updates };
  }

  resetSession(): void {
    this.humorMessageCount = 0;
    this.lastHumorMessageIndex = -1;
    this.messageCount = 0;
  }

  incrementMessageCount(): void {
    this.messageCount++;
  }

  shouldUseHumor(context: {
    isError?: boolean;
    isSecurity?: boolean;
    isFinancial?: boolean;
    isInfraOp?: boolean;
  }): boolean {
    const { config } = this;
    
    // Check if humor is disabled globally
    if (config.humorLevel <= 0) return false;
    
    // Check context-specific restrictions
    if (context.isError && config.contextAwareness.disableHumorInErrors) return false;
    if (context.isSecurity && config.contextAwareness.disableHumorInSecurity) return false;
    if (context.isFinancial && config.contextAwareness.disableHumorInFinancial) return false;
    if (context.isInfraOp && config.contextAwareness.disableHumorInInfraOps) return false;
    
    // Check session limits
    if (this.humorMessageCount >= config.humorFrequency.maxPerSession) return false;
    
    // Check cooldown
    const messagesSinceLastHumor = this.messageCount - this.lastHumorMessageIndex;
    if (messagesSinceLastHumor < config.humorFrequency.cooldownMessages) return false;
    
    // Random chance based on humor level
    return Math.random() < config.humorLevel;
  }

  recordHumorUsed(): void {
    this.humorMessageCount++;
    this.lastHumorMessageIndex = this.messageCount;
  }

  getToneProfile(): {
    formality: number;
    terseness: number;
    warmth: number;
  } {
    return {
      formality: this.config.formality,
      terseness: this.config.terseness,
      warmth: Math.max(0.2, 1 - this.config.formality),
    };
  }

  shouldAskClarifyingQuestion(ambiguityScore: number): {
    shouldAsk: boolean;
    type: 'none' | 'targeted' | 'with-default';
  } {
    const { followUpPolicy } = this.config;
    
    if (followUpPolicy === 'never') {
      return { shouldAsk: false, type: 'none' };
    }
    
    if (followUpPolicy === 'always') {
      return { 
        shouldAsk: true, 
        type: ambiguityScore > 0.7 ? 'with-default' : 'targeted' 
      };
    }
    
    // 'only-if-ambiguous-or-high-value' policy
    if (ambiguityScore < 0.35) {
      return { shouldAsk: false, type: 'none' };
    } else if (ambiguityScore <= 0.7) {
      return { shouldAsk: true, type: 'targeted' };
    } else {
      return { shouldAsk: true, type: 'with-default' };
    }
  }
}

export const personaConfigManager = new PersonaConfigManager();