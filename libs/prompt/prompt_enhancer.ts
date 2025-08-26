/**
 * Prompt Enhancement Library
 * 
 * Implements the 5-stage prompt pipeline:
 * 1. Intent Analysis
 * 2. Context Enrichment  
 * 3. Constraint Integration
 * 4. Ambiguity Resolution
 * 5. Plan Generation
 */

export interface IntentAnalysis {
  primary_goal: string;
  task_type: 'code' | 'architecture' | 'debug' | 'research' | 'orchestration';
  urgency_level: 'low' | 'medium' | 'high' | 'critical';
  scope: 'local' | 'system' | 'enterprise';
  stakeholders: string[];
  confidence: number;
}

export interface ContextPack {
  codebase_context: SearchResult[];
  infrastructure_state: SystemStatus;
  previous_conversations: ConversationHistory[];
  external_knowledge: KnowledgeFragment[];
  constraints: BusinessRule[];
}

export interface SearchResult {
  content: string;
  relevance_score: number;
  source: string;
  timestamp: string;
}

export interface SystemStatus {
  services: ServiceHealth[];
  infrastructure: InfrastructureState;
  last_updated: string;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'failed';
  url?: string;
}

export interface InfrastructureState {
  qdrant_collections: string[];
  redis_status: 'connected' | 'disconnected';
  neon_status: 'connected' | 'disconnected';
}

export interface ConversationHistory {
  id: string;
  summary: string;
  outcome: string;
  timestamp: string;
}

export interface KnowledgeFragment {
  content: string;
  source: string;
  confidence: number;
}

export interface BusinessRule {
  rule: string;
  scope: string;
  enforcement: 'required' | 'recommended' | 'optional';
}

export interface ConstraintSet {
  technical: TechnicalConstraint[];
  business: BusinessRule[];
  security: SecurityPolicy[];
  resource: ResourceLimit[];
  timeline: TimeConstraint[];
}

export interface TechnicalConstraint {
  type: string;
  description: string;
  impact: 'blocking' | 'limiting' | 'advisory';
}

export interface SecurityPolicy {
  policy: string;
  scope: string;
  enforcement: 'strict' | 'standard' | 'advisory';
}

export interface ResourceLimit {
  resource: 'tokens' | 'compute' | 'storage' | 'api_calls';
  limit: number;
  current_usage: number;
}

export interface TimeConstraint {
  deadline: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
}

export interface AmbiguityAssessment {
  unclear_requirements: string[];
  missing_information: InfoGap[];
  assumption_risks: RiskFactor[];
  clarification_needed: Question[];
  confidence_score: number;
}

export interface InfoGap {
  category: string;
  description: string;
  impact: 'critical' | 'moderate' | 'minor';
}

export interface RiskFactor {
  risk: string;
  probability: number;
  impact: 'high' | 'medium' | 'low';
  mitigation?: string;
}

export interface Question {
  question: string;
  urgency: 'blocking' | 'important' | 'clarifying';
  default_assumption?: string;
}

export interface EnhancementConfig {
  context_depth: 'minimal' | 'standard' | 'comprehensive';
  ambiguity_tolerance: number; // 0-1
  plan_granularity: 'high-level' | 'detailed' | 'micro-tasks';
  proof_generation: 'minimal' | 'standard' | 'comprehensive';
  constraint_strictness: 'permissive' | 'standard' | 'strict';
}

export interface EnhancedPrompt {
  original_request: string;
  intent: IntentAnalysis;
  context: ContextPack;
  constraints: ConstraintSet;
  ambiguities: AmbiguityAssessment;
  enhanced_prompt: string;
  metadata: {
    processing_time_ms: number;
    confidence_score: number;
    warnings: string[];
  };
}

export class PromptEnhancer {
  private config: EnhancementConfig;
  private contextMcpClient: ContextMcpClient | null = null;
  private qdrantClient: QdrantClient | null = null;

  constructor(config: Partial<EnhancementConfig> = {}) {
    this.config = {
      context_depth: 'standard',
      ambiguity_tolerance: 0.3,
      plan_granularity: 'detailed',
      proof_generation: 'standard',
      constraint_strictness: 'standard',
      ...config
    };
  }

  async enhance(request: string): Promise<EnhancedPrompt> {
    const startTime = Date.now();
    const warnings: string[] = [];

    try {
      // Stage 1: Intent Analysis
      const intent = await this.analyzeIntent(request);
      
      // Stage 2: Context Enrichment
      const context = await this.enrichContext(request, intent);
      
      // Stage 3: Constraint Integration
      const constraints = await this.integrateConstraints(intent, context);
      
      // Stage 4: Ambiguity Resolution
      const ambiguities = await this.resolveAmbiguities(request, intent, context, constraints);
      
      // Stage 5: Enhanced Prompt Generation
      const enhanced_prompt = await this.generateEnhancedPrompt(
        request, intent, context, constraints, ambiguities
      );

      return {
        original_request: request,
        intent,
        context,
        constraints,
        ambiguities,
        enhanced_prompt,
        metadata: {
          processing_time_ms: Date.now() - startTime,
          confidence_score: this.calculateOverallConfidence(intent, context, ambiguities),
          warnings
        }
      };
    } catch (error) {
      warnings.push(`Enhancement failed: ${error instanceof Error ? error.message : String(error)}`);
      
      // Fallback to basic enhancement
      return {
        original_request: request,
        intent: await this.analyzeIntent(request),
        context: this.getEmptyContext(),
        constraints: this.getEmptyConstraints(),
        ambiguities: this.getEmptyAmbiguities(),
        enhanced_prompt: request, // Fallback to original
        metadata: {
          processing_time_ms: Date.now() - startTime,
          confidence_score: 0.5,
          warnings
        }
      };
    }
  }

  private async analyzeIntent(request: string): Promise<IntentAnalysis> {
    // Intent classification logic
    const task_type = this.classifyTaskType(request);
    const urgency_level = this.assessUrgency(request);
    const scope = this.determineScope(request);
    const stakeholders = this.identifyStakeholders(request);
    const primary_goal = this.extractPrimaryGoal(request);
    
    return {
      primary_goal,
      task_type,
      urgency_level,
      scope,
      stakeholders,
      confidence: this.calculateIntentConfidence(request)
    };
  }

  private async enrichContext(request: string, intent: IntentAnalysis): Promise<ContextPack> {
    const context: ContextPack = {
      codebase_context: [],
      infrastructure_state: await this.getInfrastructureState(),
      previous_conversations: await this.getPreviousConversations(intent),
      external_knowledge: await this.getExternalKnowledge(request),
      constraints: []
    };

    // Get codebase context if Context MCP is available
    if (this.contextMcpClient) {
      try {
        const searchResults = await this.contextMcpClient.search(request);
        context.codebase_context = searchResults;
      } catch (error) {
        // Context MCP unavailable - continue without codebase context
      }
    }

    return context;
  }

  private async integrateConstraints(intent: IntentAnalysis, context: ContextPack): Promise<ConstraintSet> {
    return {
      technical: await this.getTechnicalConstraints(intent),
      business: this.getBusinessConstraints(intent),
      security: this.getSecurityPolicies(intent),
      resource: this.getResourceLimits(intent),
      timeline: this.getTimeConstraints(intent)
    };
  }

  private async resolveAmbiguities(
    request: string, 
    intent: IntentAnalysis, 
    context: ContextPack,
    constraints: ConstraintSet
  ): Promise<AmbiguityAssessment> {
    const unclear_requirements = this.identifyUnclearRequirements(request);
    const missing_information = this.identifyMissingInformation(intent, context);
    const assumption_risks = this.assessAssumptionRisks(request, context);
    const clarification_needed = this.generateClarificationQuestions(unclear_requirements, missing_information);
    
    return {
      unclear_requirements,
      missing_information,
      assumption_risks,
      clarification_needed,
      confidence_score: this.calculateAmbiguityConfidence(unclear_requirements, missing_information)
    };
  }

  private async generateEnhancedPrompt(
    request: string,
    intent: IntentAnalysis,
    context: ContextPack,
    constraints: ConstraintSet,
    ambiguities: AmbiguityAssessment
  ): Promise<string> {
    let enhanced = `Original Request: ${request}\n\n`;
    
    enhanced += `## Intent Analysis\n`;
    enhanced += `Primary Goal: ${intent.primary_goal}\n`;
    enhanced += `Task Type: ${intent.task_type}\n`;
    enhanced += `Scope: ${intent.scope}\n`;
    enhanced += `Urgency: ${intent.urgency_level}\n\n`;
    
    if (context.codebase_context.length > 0) {
      enhanced += `## Relevant Context\n`;
      context.codebase_context.slice(0, 3).forEach((result, i) => {
        enhanced += `${i + 1}. ${result.content} (relevance: ${result.relevance_score})\n`;
      });
      enhanced += `\n`;
    }
    
    if (constraints.technical.length > 0 || constraints.business.length > 0) {
      enhanced += `## Key Constraints\n`;
      constraints.technical.filter(c => c.impact === 'blocking').forEach(constraint => {
        enhanced += `- Technical: ${constraint.description}\n`;
      });
      constraints.business.filter(c => c.enforcement === 'required').forEach(rule => {
        enhanced += `- Business: ${rule.rule}\n`;
      });
      enhanced += `\n`;
    }
    
    if (ambiguities.clarification_needed.length > 0 && ambiguities.confidence_score < this.config.ambiguity_tolerance) {
      enhanced += `## Clarifications Needed\n`;
      ambiguities.clarification_needed.forEach((q, i) => {
        enhanced += `${i + 1}. ${q.question}\n`;
        if (q.default_assumption) {
          enhanced += `   Default assumption: ${q.default_assumption}\n`;
        }
      });
      enhanced += `\n`;
    }
    
    enhanced += `## Enhanced Request\n`;
    enhanced += `Please ${intent.primary_goal} following these specifications:\n\n`;
    enhanced += `${request}\n\n`;
    
    if (this.config.proof_generation !== 'minimal') {
      enhanced += `## Proof Requirements\n`;
      enhanced += `- Generate verification artifacts for all major components\n`;
      enhanced += `- Follow NO MOCKS protocol - create normalized error JSON if blocked\n`;
      enhanced += `- Commit all proofs under proofs/* directory\n\n`;
    }
    
    return enhanced;
  }

  // Helper methods for classification and analysis
  private classifyTaskType(request: string): IntentAnalysis['task_type'] {
    const codeKeywords = ['implement', 'write', 'code', 'function', 'class', 'api'];
    const architectureKeywords = ['design', 'architect', 'system', 'structure', 'plan'];
    const debugKeywords = ['debug', 'fix', 'error', 'issue', 'problem', 'bug'];
    const researchKeywords = ['research', 'investigate', 'analyze', 'explore', 'find'];
    const orchestrationKeywords = ['deploy', 'orchestrate', 'coordinate', 'manage', 'workflow'];
    
    const lowerRequest = request.toLowerCase();
    
    if (codeKeywords.some(keyword => lowerRequest.includes(keyword))) return 'code';
    if (architectureKeywords.some(keyword => lowerRequest.includes(keyword))) return 'architecture';
    if (debugKeywords.some(keyword => lowerRequest.includes(keyword))) return 'debug';
    if (researchKeywords.some(keyword => lowerRequest.includes(keyword))) return 'research';
    if (orchestrationKeywords.some(keyword => lowerRequest.includes(keyword))) return 'orchestration';
    
    return 'code'; // Default
  }

  private assessUrgency(request: string): IntentAnalysis['urgency_level'] {
    const criticalKeywords = ['urgent', 'critical', 'emergency', 'asap', 'immediately'];
    const highKeywords = ['important', 'priority', 'soon', 'needed'];
    
    const lowerRequest = request.toLowerCase();
    
    if (criticalKeywords.some(keyword => lowerRequest.includes(keyword))) return 'critical';
    if (highKeywords.some(keyword => lowerRequest.includes(keyword))) return 'high';
    
    return 'medium'; // Default
  }

  private determineScope(request: string): IntentAnalysis['scope'] {
    const enterpriseKeywords = ['enterprise', 'organization', 'company', 'all services'];
    const systemKeywords = ['system', 'infrastructure', 'deployment', 'workflow'];
    
    const lowerRequest = request.toLowerCase();
    
    if (enterpriseKeywords.some(keyword => lowerRequest.includes(keyword))) return 'enterprise';
    if (systemKeywords.some(keyword => lowerRequest.includes(keyword))) return 'system';
    
    return 'local'; // Default
  }

  private identifyStakeholders(request: string): string[] {
    const stakeholders: string[] = [];
    const lowerRequest = request.toLowerCase();
    
    if (lowerRequest.includes('ceo') || lowerRequest.includes('executive')) stakeholders.push('CEO');
    if (lowerRequest.includes('user') || lowerRequest.includes('customer')) stakeholders.push('Users');
    if (lowerRequest.includes('team') || lowerRequest.includes('developer')) stakeholders.push('Development Team');
    if (lowerRequest.includes('compliance') || lowerRequest.includes('security')) stakeholders.push('Compliance Team');
    
    return stakeholders;
  }

  private extractPrimaryGoal(request: string): string {
    // Simple extraction - in production this would use NLP
    const sentences = request.split(/[.!?]+/);
    return sentences[0]?.trim() || request.substring(0, 100);
  }

  private calculateIntentConfidence(request: string): number {
    // Simple confidence calculation based on clarity and specificity
    const words = request.split(' ').length;
    const hasSpecificTerms = /\b(create|implement|fix|deploy|analyze)\b/i.test(request);
    
    let confidence = 0.5; // Base confidence
    
    if (hasSpecificTerms) confidence += 0.2;
    if (words > 10) confidence += 0.2;
    if (words > 20) confidence += 0.1;
    
    return Math.min(confidence, 1.0);
  }

  // Placeholder implementations for context gathering
  private async getInfrastructureState(): Promise<SystemStatus> {
    return {
      services: [
        { name: 'sophiaai-mcp-repo-v2', status: 'healthy', url: 'http://localhost:{port}' }
      ],
      infrastructure: {
        qdrant_collections: [],
        redis_status: 'disconnected',
        neon_status: 'disconnected'
      },
      last_updated: new Date().toISOString()
    };
  }

  private async getPreviousConversations(intent: IntentAnalysis): Promise<ConversationHistory[]> {
    // Would integrate with conversation history system
    return [];
  }

  private async getExternalKnowledge(request: string): Promise<KnowledgeFragment[]> {
    // Would integrate with Research MCP
    return [];
  }

  private async getTechnicalConstraints(intent: IntentAnalysis): Promise<TechnicalConstraint[]> {
    const constraints: TechnicalConstraint[] = [];
    
    if (intent.task_type === 'code') {
      constraints.push({
        type: 'language',
        description: 'Must use TypeScript for frontend, Python for services',
        impact: 'limiting'
      });
    }
    
    return constraints;
  }

  private getBusinessConstraints(intent: IntentAnalysis): BusinessRule[] {
    const rules: BusinessRule[] = [
      {
        rule: 'All infrastructure changes require CEO approval',
        scope: 'enterprise',
        enforcement: 'required'
      }
    ];
    
    if (intent.scope === 'enterprise') {
      rules.push({
        rule: 'Follow NO MOCKS protocol for all operations',
        scope: 'enterprise',
        enforcement: 'required'
      });
    }
    
    return rules;
  }

  private getSecurityPolicies(intent: IntentAnalysis): SecurityPolicy[] {
    return [
      {
        policy: 'No secret values in proofs or logs',
        scope: 'all',
        enforcement: 'strict'
      }
    ];
  }

  private getResourceLimits(intent: IntentAnalysis): ResourceLimit[] {
    return [
      {
        resource: 'tokens',
        limit: 100000,
        current_usage: 25000
      }
    ];
  }

  private getTimeConstraints(intent: IntentAnalysis): TimeConstraint[] {
    if (intent.urgency_level === 'critical') {
      return [{
        deadline: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        priority: 'critical'
      }];
    }
    return [];
  }

  private identifyUnclearRequirements(request: string): string[] {
    const unclear: string[] = [];
    
    if (!/\b(specific|exactly|precisely)\b/i.test(request)) {
      unclear.push('Specific implementation details not provided');
    }
    
    if (!/\b(test|testing|verify)\b/i.test(request)) {
      unclear.push('Testing requirements not specified');
    }
    
    return unclear;
  }

  private identifyMissingInformation(intent: IntentAnalysis, context: ContextPack): InfoGap[] {
    const gaps: InfoGap[] = [];
    
    if (intent.task_type === 'code' && context.codebase_context.length === 0) {
      gaps.push({
        category: 'context',
        description: 'No existing codebase context available',
        impact: 'moderate'
      });
    }
    
    return gaps;
  }

  private assessAssumptionRisks(request: string, context: ContextPack): RiskFactor[] {
    const risks: RiskFactor[] = [];
    
    if (context.infrastructure_state.services.length < 2) {
      risks.push({
        risk: 'Limited infrastructure visibility may affect deployment decisions',
        probability: 0.7,
        impact: 'medium',
        mitigation: 'Verify service status before making changes'
      });
    }
    
    return risks;
  }

  private generateClarificationQuestions(
    unclear: string[], 
    missing: InfoGap[]
  ): Question[] {
    const questions: Question[] = [];
    
    if (unclear.includes('Specific implementation details not provided')) {
      questions.push({
        question: 'What specific implementation approach do you prefer?',
        urgency: 'clarifying',
        default_assumption: 'Use established patterns from existing codebase'
      });
    }
    
    missing.forEach(gap => {
      if (gap.impact === 'critical') {
        questions.push({
          question: `How should we handle: ${gap.description}?`,
          urgency: 'blocking'
        });
      }
    });
    
    return questions;
  }

  private calculateAmbiguityConfidence(unclear: string[], missing: InfoGap[]): number {
    const unclearCount = unclear.length;
    const criticalMissing = missing.filter(g => g.impact === 'critical').length;
    
    let confidence = 1.0;
    confidence -= (unclearCount * 0.1);
    confidence -= (criticalMissing * 0.3);
    
    return Math.max(confidence, 0.0);
  }

  private calculateOverallConfidence(
    intent: IntentAnalysis, 
    context: ContextPack, 
    ambiguities: AmbiguityAssessment
  ): number {
    return (intent.confidence + ambiguities.confidence_score) / 2;
  }

  private getEmptyContext(): ContextPack {
    return {
      codebase_context: [],
      infrastructure_state: {
        services: [],
        infrastructure: {
          qdrant_collections: [],
          redis_status: 'disconnected',
          neon_status: 'disconnected'
        },
        last_updated: new Date().toISOString()
      },
      previous_conversations: [],
      external_knowledge: [],
      constraints: []
    };
  }

  private getEmptyConstraints(): ConstraintSet {
    return {
      technical: [],
      business: [],
      security: [],
      resource: [],
      timeline: []
    };
  }

  private getEmptyAmbiguities(): AmbiguityAssessment {
    return {
      unclear_requirements: [],
      missing_information: [],
      assumption_risks: [],
      clarification_needed: [],
      confidence_score: 0.5
    };
  }
}

// Mock client interfaces for type safety
interface ContextMcpClient {
  search(query: string): Promise<SearchResult[]>;
}

interface QdrantClient {
  search(vector: number[], collection: string): Promise<SearchResult[]>;
}

// Default configuration profiles
export const DEVELOPMENT_CONFIG: EnhancementConfig = {
  context_depth: 'comprehensive',
  ambiguity_tolerance: 0.5,
  plan_granularity: 'detailed',
  proof_generation: 'comprehensive',
  constraint_strictness: 'permissive'
};

export const PRODUCTION_CONFIG: EnhancementConfig = {
  context_depth: 'standard',
  ambiguity_tolerance: 0.2,
  plan_granularity: 'detailed',
  proof_generation: 'standard',
  constraint_strictness: 'strict'
};

export const EMERGENCY_CONFIG: EnhancementConfig = {
  context_depth: 'minimal',
  ambiguity_tolerance: 0.7,
  plan_granularity: 'high-level',
  proof_generation: 'minimal',
  constraint_strictness: 'permissive'
};