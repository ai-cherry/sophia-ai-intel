/**
 * Sophia AI Safe Execution Orchestrator
 * Provides execution rails with max steps/retries, idempotency, and strict schemas
 */

export interface ExecutionContext {
  sessionId: string;
  userId?: string;
  requestId: string;
  timestamp: string;
  maxSteps?: number;
  maxRetries?: number;
  timeoutMs?: number;
  enableIdempotency?: boolean;
}

export interface ExecutionStep {
  id: string;
  type: 'retrieval' | 'planning' | 'mcp_call' | 'web_research' | 'synthesis';
  action: string;
  input: any;
  idempotencyKey?: string;
  retryCount: number;
  maxRetries: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output?: any;
  error?: string;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
}

export interface ExecutionPlan {
  id: string;
  sessionId: string;
  steps: ExecutionStep[];
  totalSteps: number;
  currentStep: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt?: string;
  completedAt?: string;
  totalDurationMs?: number;
  metadata: {
    persona: any;
    originalQuery: string;
    safetyChecks: string[];
  };
}

export interface SafetyRails {
  maxStepsPerPlan: number;
  maxRetriesPerStep: number;
  stepTimeoutMs: number;
  totalTimeoutMs: number;
  enableCircuitBreaker: boolean;
  circuitBreakerFailureThreshold: number;
  idempotencyTtlMs: number;
  rateLimitPerUser: number;
  rateLimitWindowMs: number;
}

export interface ExecutionResult {
  planId: string;
  success: boolean;
  output?: any;
  error?: string;
  executedSteps: number;
  totalDurationMs: number;
  safetyViolations: string[];
  idempotencyHits: number;
}

const DEFAULT_SAFETY_RAILS: SafetyRails = {
  maxStepsPerPlan: 10,
  maxRetriesPerStep: 3,
  stepTimeoutMs: 30000, // 30 seconds
  totalTimeoutMs: 300000, // 5 minutes
  enableCircuitBreaker: true,
  circuitBreakerFailureThreshold: 5,
  idempotencyTtlMs: 3600000, // 1 hour
  rateLimitPerUser: 20,
  rateLimitWindowMs: 60000, // 1 minute
};

export class SafeExecutor {
  private plans: Map<string, ExecutionPlan> = new Map();
  private idempotencyStore: Map<string, { result: any; timestamp: number }> = new Map();
  private circuitBreakerFailures: Map<string, number> = new Map();
  private userRateLimits: Map<string, { count: number; resetAt: number }> = new Map();
  private activeExecutions: Set<string> = new Set();

  constructor(private safetyRails: SafetyRails = DEFAULT_SAFETY_RAILS) {
    // Clean up old idempotency entries periodically
    setInterval(() => this.cleanupIdempotencyStore(), 60000);
  }

  /**
   * Create and validate execution plan
   */
  async createPlan(
    context: ExecutionContext,
    steps: Omit<ExecutionStep, 'retryCount' | 'status'>[]
  ): Promise<ExecutionPlan> {
    // Validate context
    this.validateContext(context);
    
    // Check rate limits
    await this.checkRateLimit(context.userId);
    
    // Apply safety rails
    if (steps.length > this.safetyRails.maxStepsPerPlan) {
      throw new Error(`Plan exceeds maximum steps (${this.safetyRails.maxStepsPerPlan})`);
    }

    const planId = `plan_${context.sessionId}_${Date.now()}`;
    
    const plan: ExecutionPlan = {
      id: planId,
      sessionId: context.sessionId,
      steps: steps.map((step, index) => ({
        ...step,
        id: `${planId}_step_${index}`,
        retryCount: 0,
        maxRetries: step.maxRetries || this.safetyRails.maxRetriesPerStep,
        status: 'pending' as const,
        idempotencyKey: step.idempotencyKey || this.generateIdempotencyKey(step),
      })),
      totalSteps: steps.length,
      currentStep: 0,
      status: 'pending',
      metadata: {
        persona: context,
        originalQuery: context.requestId,
        safetyChecks: [],
      },
    };

    this.plans.set(planId, plan);
    return plan;
  }

  /**
   * Execute plan with full safety rails
   */
  async executePlan(planId: string): Promise<ExecutionResult> {
    const plan = this.plans.get(planId);
    if (!plan) {
      throw new Error(`Plan not found: ${planId}`);
    }

    if (this.activeExecutions.has(planId)) {
      throw new Error(`Plan already executing: ${planId}`);
    }

    this.activeExecutions.add(planId);
    const startTime = Date.now();
    
    try {
      plan.status = 'running';
      plan.startedAt = new Date().toISOString();

      const result: ExecutionResult = {
        planId,
        success: false,
        executedSteps: 0,
        totalDurationMs: 0,
        safetyViolations: [],
        idempotencyHits: 0,
      };

      // Execute steps sequentially with safety checks
      for (let i = 0; i < plan.steps.length; i++) {
        const step = plan.steps[i];
        plan.currentStep = i;

        // Check overall timeout
        if (Date.now() - startTime > this.safetyRails.totalTimeoutMs) {
          result.safetyViolations.push('Total execution timeout exceeded');
          plan.status = 'failed';
          break;
        }

        // Execute step with retries
        const stepResult = await this.executeStepWithRetries(step);
        result.executedSteps++;

        if (stepResult.fromCache) {
          result.idempotencyHits++;
        }

        if (step.status === 'failed') {
          plan.status = 'failed';
          result.error = step.error;
          break;
        }

        // Check circuit breaker
        if (this.isCircuitBreakerOpen(step.type)) {
          result.safetyViolations.push(`Circuit breaker open for ${step.type}`);
          plan.status = 'failed';
          break;
        }
      }

      if (plan.status === 'running') {
        plan.status = 'completed';
        result.success = true;
        result.output = this.synthesizeResults(plan);
      }

      plan.completedAt = new Date().toISOString();
      plan.totalDurationMs = Date.now() - startTime;
      result.totalDurationMs = plan.totalDurationMs;

      return result;

    } catch (error) {
      plan.status = 'failed';
      plan.completedAt = new Date().toISOString();
      plan.totalDurationMs = Date.now() - startTime;
      
      throw new Error(`Plan execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      this.activeExecutions.delete(planId);
    }
  }

  /**
   * Execute single step with retries and idempotency
   */
  private async executeStepWithRetries(step: ExecutionStep): Promise<{ result: any; fromCache: boolean }> {
    const stepStartTime = Date.now();
    step.startedAt = new Date().toISOString();
    step.status = 'running';

    // Check idempotency cache
    if (step.idempotencyKey) {
      const cached = this.getFromIdempotencyStore(step.idempotencyKey);
      if (cached) {
        step.output = cached.result;
        step.status = 'completed';
        step.completedAt = new Date().toISOString();
        step.durationMs = Date.now() - stepStartTime;
        return { result: cached.result, fromCache: true };
      }
    }

    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= step.maxRetries; attempt++) {
      step.retryCount = attempt;

      try {
        // Execute the actual step
        const result = await this.executeStepAction(step);
        
        // Success - cache result if idempotency enabled
        step.output = result;
        step.status = 'completed';
        step.completedAt = new Date().toISOString();
        step.durationMs = Date.now() - stepStartTime;

        if (step.idempotencyKey) {
          this.storeInIdempotencyCache(step.idempotencyKey, result);
        }

        return { result, fromCache: false };

      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Record circuit breaker failure
        this.recordCircuitBreakerFailure(step.type);
        
        // If we've exhausted retries, fail the step
        if (attempt === step.maxRetries) {
          step.status = 'failed';
          step.error = lastError.message;
          step.completedAt = new Date().toISOString();
          step.durationMs = Date.now() - stepStartTime;
          break;
        }

        // Wait before retry (exponential backoff)
        const backoffMs = Math.min(1000 * Math.pow(2, attempt), 10000);
        await new Promise(resolve => setTimeout(resolve, backoffMs));
      }
    }

    if (lastError) {
      throw lastError;
    }

    return { result: null, fromCache: false };
  }

  /**
   * Execute individual step action based on type
   */
  private async executeStepAction(step: ExecutionStep): Promise<any> {
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Step timeout')), this.safetyRails.stepTimeoutMs);
    });

    // Execute based on step type
    const executionPromise = this.performStepByType(step);

    // Race between execution and timeout
    return Promise.race([executionPromise, timeoutPromise]);
  }

  /**
   * Perform step based on type
   */
  private async performStepByType(step: ExecutionStep): Promise<any> {
    switch (step.type) {
      case 'retrieval':
        return this.performRetrieval(step);
      case 'planning':
        return this.performPlanning(step);
      case 'mcp_call':
        return this.performMcpCall(step);
      case 'web_research':
        return this.performWebResearch(step);
      case 'synthesis':
        return this.performSynthesis(step);
      default:
        throw new Error(`Unknown step type: ${step.type}`);
    }
  }

  /**
   * Mock implementations for different step types
   */
  private async performRetrieval(step: ExecutionStep): Promise<any> {
    // Mock retrieval - in production would call actual services
    return {
      type: 'retrieval',
      query: step.input.query,
      results: ['mock result 1', 'mock result 2'],
      timestamp: new Date().toISOString(),
    };
  }

  private async performPlanning(step: ExecutionStep): Promise<any> {
    // Mock planning - in production would use RoleMixer
    return {
      type: 'planning',
      plan: 'Generated execution plan',
      confidence: 0.85,
      timestamp: new Date().toISOString(),
    };
  }

  private async performMcpCall(step: ExecutionStep): Promise<any> {
    // Mock MCP call - in production would call actual MCP services
    return {
      type: 'mcp_call',
      service: step.input.service,
      response: 'Mock MCP response',
      timestamp: new Date().toISOString(),
    };
  }

  private async performWebResearch(step: ExecutionStep): Promise<any> {
    // Mock web research
    return {
      type: 'web_research',
      query: step.input.query,
      findings: ['Finding 1', 'Finding 2'],
      timestamp: new Date().toISOString(),
    };
  }

  private async performSynthesis(step: ExecutionStep): Promise<any> {
    // Mock synthesis
    return {
      type: 'synthesis',
      summary: 'Synthesized results',
      confidence: 0.9,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Synthesize results from all completed steps
   */
  private synthesizeResults(plan: ExecutionPlan): any {
    const completedSteps = plan.steps.filter(s => s.status === 'completed');
    return {
      planId: plan.id,
      totalSteps: plan.totalSteps,
      completedSteps: completedSteps.length,
      results: completedSteps.map(s => s.output),
      summary: 'Plan execution completed successfully',
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Utility methods for safety rails
   */
  private validateContext(context: ExecutionContext): void {
    if (!context.sessionId || !context.requestId) {
      throw new Error('Invalid execution context');
    }
  }

  private async checkRateLimit(userId?: string): Promise<void> {
    if (!userId) return;

    const now = Date.now();
    const limit = this.userRateLimits.get(userId);

    if (limit) {
      if (now < limit.resetAt) {
        if (limit.count >= this.safetyRails.rateLimitPerUser) {
          throw new Error('Rate limit exceeded');
        }
        limit.count++;
      } else {
        // Reset window
        this.userRateLimits.set(userId, {
          count: 1,
          resetAt: now + this.safetyRails.rateLimitWindowMs,
        });
      }
    } else {
      this.userRateLimits.set(userId, {
        count: 1,
        resetAt: now + this.safetyRails.rateLimitWindowMs,
      });
    }
  }

  private generateIdempotencyKey(step: Omit<ExecutionStep, 'retryCount' | 'status'>): string {
    const content = JSON.stringify({
      type: step.type,
      action: step.action,
      input: step.input,
    });
    return `${step.type}_${this.simpleHash(content)}`;
  }

  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  private getFromIdempotencyStore(key: string): { result: any } | null {
    const entry = this.idempotencyStore.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > this.safetyRails.idempotencyTtlMs;
    if (isExpired) {
      this.idempotencyStore.delete(key);
      return null;
    }

    return { result: entry.result };
  }

  private storeInIdempotencyCache(key: string, result: any): void {
    this.idempotencyStore.set(key, {
      result,
      timestamp: Date.now(),
    });
  }

  private recordCircuitBreakerFailure(stepType: string): void {
    if (!this.safetyRails.enableCircuitBreaker) return;

    const current = this.circuitBreakerFailures.get(stepType) || 0;
    this.circuitBreakerFailures.set(stepType, current + 1);
  }

  private isCircuitBreakerOpen(stepType: string): boolean {
    if (!this.safetyRails.enableCircuitBreaker) return false;

    const failures = this.circuitBreakerFailures.get(stepType) || 0;
    return failures >= this.safetyRails.circuitBreakerFailureThreshold;
  }

  private cleanupIdempotencyStore(): void {
    const now = Date.now();
    for (const [key, entry] of this.idempotencyStore.entries()) {
      if (now - entry.timestamp > this.safetyRails.idempotencyTtlMs) {
        this.idempotencyStore.delete(key);
      }
    }
  }

  /**
   * Management methods
   */
  getPlan(planId: string): ExecutionPlan | undefined {
    return this.plans.get(planId);
  }

  cancelPlan(planId: string): boolean {
    const plan = this.plans.get(planId);
    if (plan && plan.status === 'running') {
      plan.status = 'cancelled';
      this.activeExecutions.delete(planId);
      return true;
    }
    return false;
  }

  getStats(): {
    activePlans: number;
    totalPlans: number;
    circuitBreakerFailures: Record<string, number>;
    idempotencyCacheSize: number;
  } {
    return {
      activePlans: this.activeExecutions.size,
      totalPlans: this.plans.size,
      circuitBreakerFailures: Object.fromEntries(this.circuitBreakerFailures),
      idempotencyCacheSize: this.idempotencyStore.size,
    };
  }
}

/**
 * Factory function for creating safe executor
 */
export function createSafeExecutor(safetyRails?: Partial<SafetyRails>): SafeExecutor {
  const mergedRails = { ...DEFAULT_SAFETY_RAILS, ...safetyRails };
  return new SafeExecutor(mergedRails);
}