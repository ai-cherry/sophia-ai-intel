/**
 * Sophia AI Role Mixer - Plan synthesis and conflict resolution
 * Coordinates between PlannerA/B and Mediator for optimal decision making
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

export interface PlanningRequest {
  query: string;
  context: {
    domain: string;
    complexity: 'low' | 'medium' | 'high';
    stakeholders: string[];
    constraints: string[];
    timeline: string;
  };
  ambiguityScore: number;
  requiresConcurrent?: boolean;
}

export interface ModelPlan {
  role: 'PlannerA' | 'PlannerB' | 'Mediator' | 'Coder';
  planId: string;
  approach: string;
  steps: PlanStep[];
  artifacts: ArtifactSpec[];
  riskAssessment: RiskAssessment;
  estimatedEffort: EffortEstimate;
  confidence: number; // 0-1
  reasoning: string;
}

export interface PlanStep {
  id: string;
  description: string;
  dependencies: string[];
  estimatedTime: string;
  riskLevel: 'low' | 'medium' | 'high';
  testable: boolean;
}

export interface ArtifactSpec {
  type: 'file' | 'proof' | 'workflow' | 'test' | 'documentation';
  path: string;
  description: string;
  required: boolean;
}

export interface RiskAssessment {
  technical: { level: 'low' | 'medium' | 'high'; description: string };
  timeline: { level: 'low' | 'medium' | 'high'; description: string };
  complexity: { level: 'low' | 'medium' | 'high'; description: string };
  dependencies: { level: 'low' | 'medium' | 'high'; description: string };
}

export interface EffortEstimate {
  filesModified: number;
  linesOfCode: number;
  timeEstimate: string;
  complexity: 'simple' | 'moderate' | 'complex';
}

export interface SynthesizedPlan extends ModelPlan {
  role: 'Mediator';
  sourcePlans: string[]; // Plan IDs that were synthesized
  conflictResolution: ConflictResolution[];
  finalRecommendation: {
    approach: string;
    reasoning: string;
    tradeOffs: string[];
    nextActions: string[];
  };
}

export interface ConflictResolution {
  aspect: string;
  plannerAView: string;
  plannerBView: string;
  mediatorDecision: string;
  reasoning: string;
}

export class RoleMixer {
  private planHistory: Map<string, ModelPlan> = new Map();

  constructor(private config: PersonaConfig) {}

  /**
   * Generate plans from multiple planners and synthesize via Mediator
   * Now with persona-aware planning integration
   */
  async generateSynthesizedPlan(request: PlanningRequest): Promise<SynthesizedPlan> {
    // Apply persona configuration to planning context
    const personaAwarePlan = this.applyPersonaToPlanning(request);
    
    // Generate plans with persona influence
    const plannerAResult = await this.simulatePlannerA(personaAwarePlan);
    const plannerBResult = await this.simulatePlannerB(personaAwarePlan);
    
    // Store plans in history
    this.planHistory.set(plannerAResult.planId, plannerAResult);
    this.planHistory.set(plannerBResult.planId, plannerBResult);

    // Synthesize via Mediator with persona context
    const synthesizedPlan = await this.synthesizePlans(personaAwarePlan, [plannerAResult, plannerBResult]);
    
    this.planHistory.set(synthesizedPlan.planId, synthesizedPlan);
    
    return synthesizedPlan;
  }

  /**
   * Apply persona configuration to planning request
   */
  private applyPersonaToPlanning(request: PlanningRequest): PlanningRequest {
    const enhancedRequest = { ...request };
    
    // Adjust complexity assessment based on persona terseness
    if (this.config.terseness > 0.7) {
      // High terseness prefers simpler approaches
      if (enhancedRequest.context.complexity === 'high') {
        enhancedRequest.context.complexity = 'medium';
      }
    }
    
    // Adjust timeline expectations based on formality
    if (this.config.formality > 0.7) {
      // High formality prefers thorough, methodical approaches
      enhancedRequest.context.timeline = 'extended for thoroughness';
    }
    
    // Add persona context to constraints
    enhancedRequest.context.constraints.push(
      `Communication style: formality=${this.config.formality}, terseness=${this.config.terseness}`,
      `Humor policy: level=${this.config.humorLevel}, context-aware=${JSON.stringify(this.config.contextAwareness)}`
    );
    
    return enhancedRequest;
  }

  /**
   * Simulate PlannerA (Claude Sonnet) - Strategic, thorough planning
   */
  private async simulatePlannerA(request: PlanningRequest): Promise<ModelPlan> {
    return {
      role: 'PlannerA',
      planId: `planner-a-${Date.now()}`,
      approach: "Comprehensive strategic approach with emphasis on architecture and long-term maintainability",
      steps: [
        {
          id: "analysis",
          description: "Thorough requirements analysis and architecture design",
          dependencies: [],
          estimatedTime: "2-3 hours",
          riskLevel: "low",
          testable: true
        },
        {
          id: "design",
          description: "Detailed technical design with component specifications",
          dependencies: ["analysis"],
          estimatedTime: "3-4 hours", 
          riskLevel: "medium",
          testable: true
        },
        {
          id: "implementation",
          description: "Incremental implementation with comprehensive testing",
          dependencies: ["design"],
          estimatedTime: "6-8 hours",
          riskLevel: "medium",
          testable: true
        }
      ],
      artifacts: [
        { type: 'documentation', path: 'docs/architecture.md', description: 'Architecture specification', required: true },
        { type: 'file', path: 'src/core/', description: 'Core implementation files', required: true },
        { type: 'test', path: 'tests/unit/', description: 'Comprehensive unit tests', required: true },
        { type: 'proof', path: 'proofs/implementation/', description: 'Implementation proofs', required: true }
      ],
      riskAssessment: {
        technical: { level: 'low', description: 'Well-established patterns and practices' },
        timeline: { level: 'medium', description: 'Comprehensive approach takes time' },
        complexity: { level: 'medium', description: 'Complex but well-structured' },
        dependencies: { level: 'low', description: 'Minimal external dependencies' }
      },
      estimatedEffort: {
        filesModified: 8,
        linesOfCode: 500,
        timeEstimate: "11-15 hours",
        complexity: 'moderate'
      },
      confidence: 0.85,
      reasoning: this.generatePersonaAwareReasoning("Strategic approach prioritizes long-term maintainability and robustness over speed", 'PlannerA')
    };
  }

  /**
   * Simulate PlannerB (DeepSeek) - Practical, efficient planning
   */
  private async simulatePlannerB(request: PlanningRequest): Promise<ModelPlan> {
    return {
      role: 'PlannerB',
      planId: `planner-b-${Date.now()}`,
      approach: "Pragmatic implementation-first approach optimizing for rapid delivery",
      steps: [
        {
          id: "prototype",
          description: "Quick prototype to validate core functionality",
          dependencies: [],
          estimatedTime: "1-2 hours",
          riskLevel: "low",
          testable: true
        },
        {
          id: "iterate",
          description: "Iterative implementation with basic testing",
          dependencies: ["prototype"],
          estimatedTime: "3-4 hours",
          riskLevel: "medium",
          testable: true
        },
        {
          id: "polish",
          description: "Polish and document the working solution",
          dependencies: ["iterate"],
          estimatedTime: "1-2 hours",
          riskLevel: "low",
          testable: false
        }
      ],
      artifacts: [
        { type: 'file', path: 'src/implementation.ts', description: 'Core implementation', required: true },
        { type: 'test', path: 'tests/integration.test.ts', description: 'Integration tests', required: true },
        { type: 'proof', path: 'proofs/functional/', description: 'Functional verification', required: true }
      ],
      riskAssessment: {
        technical: { level: 'medium', description: 'Rapid development may introduce technical debt' },
        timeline: { level: 'low', description: 'Fast delivery timeline' },
        complexity: { level: 'low', description: 'Simple, straightforward approach' },
        dependencies: { level: 'low', description: 'Minimal dependencies' }
      },
      estimatedEffort: {
        filesModified: 3,
        linesOfCode: 200,
        timeEstimate: "5-8 hours",
        complexity: 'simple'
      },
      confidence: 0.90,
      reasoning: this.generatePersonaAwareReasoning("Practical approach focuses on rapid delivery and proven patterns", 'PlannerB')
    };
  }

  /**
   * Synthesize plans via Mediator (GPT-4) 
   */
  private async synthesizePlans(
    request: PlanningRequest,
    sourcePlans: ModelPlan[]
  ): Promise<SynthesizedPlan> {
    const conflicts = this.identifyConflicts(sourcePlans);
    const resolutions = this.resolveConflicts(conflicts, request);

    // Hybrid approach combining both planners' strengths
    return {
      role: 'Mediator',
      planId: `mediator-${Date.now()}`,
      sourcePlans: sourcePlans.map(p => p.planId),
      approach: "Hybrid approach balancing strategic depth with practical execution",
      steps: [
        {
          id: "rapid-prototype",
          description: "Quick prototype for early validation (from PlannerB)",
          dependencies: [],
          estimatedTime: "1-2 hours",
          riskLevel: "low",
          testable: true
        },
        {
          id: "strategic-design", 
          description: "Strategic architecture design while prototype validates (from PlannerA)",
          dependencies: ["rapid-prototype"],
          estimatedTime: "2-3 hours",
          riskLevel: "medium",
          testable: true
        },
        {
          id: "structured-implementation",
          description: "Structured implementation incorporating design insights",
          dependencies: ["strategic-design"],
          estimatedTime: "4-5 hours",
          riskLevel: "medium",
          testable: true
        },
        {
          id: "validation-and-docs",
          description: "Comprehensive testing and documentation",
          dependencies: ["structured-implementation"],
          estimatedTime: "2-3 hours",
          riskLevel: "low",
          testable: true
        }
      ],
      artifacts: [
        { type: 'file', path: 'src/prototype.ts', description: 'Initial prototype', required: false },
        { type: 'documentation', path: 'docs/design.md', description: 'Design documentation', required: true },
        { type: 'file', path: 'src/core/', description: 'Core implementation', required: true },
        { type: 'test', path: 'tests/', description: 'Comprehensive test suite', required: true },
        { type: 'proof', path: 'proofs/', description: 'Implementation and functional proofs', required: true }
      ],
      riskAssessment: {
        technical: { level: 'low', description: 'Balanced approach mitigates technical risks' },
        timeline: { level: 'medium', description: 'Moderate timeline with early validation' },
        complexity: { level: 'medium', description: 'Well-structured complexity management' },
        dependencies: { level: 'low', description: 'Minimal external dependencies' }
      },
      estimatedEffort: {
        filesModified: 6,
        linesOfCode: 350,
        timeEstimate: "9-13 hours",
        complexity: 'moderate'
      },
      confidence: 0.92,
      reasoning: "Synthesis leverages PlannerB's rapid validation with PlannerA's strategic depth",
      conflictResolution: resolutions,
      finalRecommendation: {
        approach: "Start with rapid prototype for validation, then implement with strategic architecture",
        reasoning: "Combines speed of delivery with long-term maintainability",
        tradeOffs: [
          "Slightly longer timeline than PlannerB approach",
          "Less comprehensive documentation than pure PlannerA approach",
          "Balanced risk profile with early validation"
        ],
        nextActions: [
          "Begin with prototype implementation",
          "Validate core assumptions early",
          "Proceed with structured implementation based on prototype learnings",
          "Generate comprehensive proof artifacts"
        ]
      }
    };
  }

  /**
   * Identify conflicts between different plans
   */
  private identifyConflicts(plans: ModelPlan[]): ConflictResolution[] {
    if (plans.length < 2) return [];

    const [planA, planB] = plans;
    const conflicts: ConflictResolution[] = [];

    // Timeline conflict
    if (Math.abs(planA.estimatedEffort.filesModified - planB.estimatedEffort.filesModified) > 3) {
      conflicts.push({
        aspect: 'scope',
        plannerAView: `${planA.estimatedEffort.filesModified} files, ${planA.estimatedEffort.timeEstimate}`,
        plannerBView: `${planB.estimatedEffort.filesModified} files, ${planB.estimatedEffort.timeEstimate}`,
        mediatorDecision: 'Hybrid scope with early validation',
        reasoning: 'Balance comprehensive approach with rapid delivery'
      });
    }

    // Approach conflict
    conflicts.push({
      aspect: 'methodology',
      plannerAView: planA.approach,
      plannerBView: planB.approach,
      mediatorDecision: 'Sequential approach: prototype first, then strategic implementation',
      reasoning: 'Leverage early validation while maintaining architectural rigor'
    });

    return conflicts;
  }

  /**
   * Resolve conflicts between plans
   */
  private resolveConflicts(
    conflicts: ConflictResolution[],
    request: PlanningRequest
  ): ConflictResolution[] {
    // Apply request-specific conflict resolution logic
    return conflicts.map(conflict => ({
      ...conflict,
      reasoning: `${conflict.reasoning} (considering ${request.context.complexity} complexity and ${request.context.timeline} timeline)`
    }));
  }

  /**
   * Get plan history
   */
  getPlanHistory(): ModelPlan[] {
    return Array.from(this.planHistory.values());
  }

  /**
   * Get specific plan by ID
   */
  getPlan(planId: string): ModelPlan | undefined {
    return this.planHistory.get(planId);
  }

  /**
   * Generate persona-aware reasoning text
   */
  private generatePersonaAwareReasoning(baseReasoning: string, role: 'PlannerA' | 'PlannerB' | 'Mediator'): string {
    let reasoning = baseReasoning;
    
    // Adjust based on formality
    if (this.config.formality > 0.7) {
      reasoning = reasoning.replace(/\b(quick|fast|rapid)\b/gi, 'efficient and methodical');
      reasoning = reasoning.replace(/\b(simple)\b/gi, 'streamlined yet comprehensive');
    } else if (this.config.formality < 0.3) {
      reasoning = reasoning.replace(/\b(comprehensive|thorough)\b/gi, 'practical');
      reasoning = reasoning.replace(/\b(methodical)\b/gi, 'straightforward');
    }
    
    // Add persona context note based on terseness
    if (this.config.terseness > 0.7) {
      return reasoning; // Keep it brief
    } else {
      const contextNote = this.getPersonaContextNote(role);
      return `${reasoning}. ${contextNote}`;
    }
  }

  /**
   * Get persona context note for reasoning
   */
  private getPersonaContextNote(role: 'PlannerA' | 'PlannerB' | 'Mediator'): string {
    const notes = {
      PlannerA: [
        'This aligns with preference for thorough analysis',
        'Systematic approach matches formal communication style',
        'Comprehensive planning reduces future clarification needs'
      ],
      PlannerB: [
        'Practical execution focus matches efficiency priorities',
        'Direct implementation approach minimizes overhead',
        'Results-oriented strategy with clear deliverables'
      ],
      Mediator: [
        'Balanced synthesis accommodates multiple perspectives',
        'Structured decision-making process ensures clarity',
        'Hybrid approach optimizes for both speed and quality'
      ]
    };
    
    const roleNotes = notes[role];
    return roleNotes[Math.floor(Math.random() * roleNotes.length)];
  }

  /**
   * Update persona configuration
   */
  updatePersonaConfig(config: PersonaConfig): void {
    this.config = config;
  }
}

// Export factory function for integration with persona config
export function createRoleMixer(config: PersonaConfig): RoleMixer {
  return new RoleMixer(config);
}