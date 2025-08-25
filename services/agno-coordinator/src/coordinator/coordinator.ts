import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import {
  PipelineRequest,
  RoutingDecision,
  RoutingResult,
  CoordinatorConfig
} from '../config/types';
import { featureFlags } from '../config/featureFlags';
import { configManager } from '../config/config';

/**
 * AGNO Coordinator Service
 * Routes requests between existing orchestrator and AGNO capabilities
 */
export class AgnosticCoordinator extends EventEmitter {
  private isInitialized = false;
  private activeRequests = new Map<string, RoutingResult>();
  private config: CoordinatorConfig;

  constructor() {
    super();
    this.config = configManager.getConfig();
    this.setupEventHandlers();
  }

  /**
   * Initialize the coordinator service
   */
  async initialize(): Promise<void> {
    try {
      console.log('Initializing AGNO Coordinator Service...');

      // Validate configuration
      const configValidation = configManager.validateConfig();
      if (!configValidation.valid) {
        throw new Error(`Configuration validation failed: ${configValidation.errors.join(', ')}`);
      }

      // Validate feature flags
      const flagValidation = featureFlags.validateConfiguration();
      if (!flagValidation.valid) {
        console.warn('Feature flag validation issues:', flagValidation.issues);
      }

      this.isInitialized = true;
      console.log('AGNO Coordinator Service initialized successfully');

      this.emit('initialized');

    } catch (error) {
      console.error('Failed to initialize AGNO Coordinator:', error);
      throw error;
    }
  }

  /**
   * Route a request to the appropriate handler
   */
  async routeRequest(request: PipelineRequest): Promise<RoutingResult> {
    const executionId = uuidv4();
    const startTime = Date.now();

    // Initialize result structure
    const result: RoutingResult = {
      success: false,
      response: '',
      executionId,
      routingDecision: {} as RoutingDecision,
      executionTimeMs: 0,
      source: 'existing',
      metadata: {
        requestId: executionId,
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      }
    };

    try {
      // Track active request
      this.activeRequests.set(executionId, result);

      // Make routing decision
      const routingDecision = await this.makeRoutingDecision(request);
      result.routingDecision = routingDecision;

      // Route to appropriate handler
      if (routingDecision.source === 'agno') {
        result.source = 'agno';
        const agnoResult = await this.handleWithAGNO(request, routingDecision);
        result.response = agnoResult.response;
        result.success = agnoResult.success;
        result.metadata = { ...result.metadata, ...agnoResult.metadata };
      } else {
        result.source = 'existing';
        const existingResult = await this.handleWithExisting(request, routingDecision);
        result.response = existingResult.response;
        result.success = existingResult.success;
        result.metadata = { ...result.metadata, ...existingResult.metadata };
      }

      result.executionTimeMs = Date.now() - startTime;

      // Emit success event
      this.emit('requestCompleted', result);

      return result;

    } catch (error) {
      result.success = false;
      result.executionTimeMs = Date.now() - startTime;
      result.error = error instanceof Error ? error.message : 'Unknown error';
      result.metadata.error = result.error;

      console.error(`Request routing failed for ${executionId}:`, error);

      // Emit error event
      this.emit('requestFailed', result);

      return result;

    } finally {
      // Clean up active request
      this.activeRequests.delete(executionId);
    }
  }

  /**
   * Make routing decision based on request analysis
   */
  private async makeRoutingDecision(request: PipelineRequest): Promise<RoutingDecision> {
    const routingConfig = this.config.routing;

    // Check if routing is enabled
    if (!routingConfig.enabled) {
      return {
        source: 'existing',
        confidence: 1.0,
        reasoning: 'AGNO routing disabled by configuration',
        estimatedComplexity: 'low',
        fallbackEnabled: true
      };
    }

    // Analyze request complexity
    const complexity = this.analyzeComplexity(request);
    const confidence = this.calculateConfidence(request, complexity);

    // Determine routing based on complexity and confidence
    const shouldUseAGNO = complexity.estimatedComplexity !== 'low' &&
                         confidence >= routingConfig.confidenceThreshold;

    return {
      source: shouldUseAGNO ? 'agno' : 'existing',
      confidence,
      reasoning: shouldUseAGNO
        ? `Request complexity (${complexity.estimatedComplexity}) meets threshold`
        : `Request complexity (${complexity.estimatedComplexity}) below threshold`,
      estimatedComplexity: complexity.estimatedComplexity,
      fallbackEnabled: featureFlags.isEnabled('agno_fallback'),
      recommendedModel: shouldUseAGNO ? this.selectModel(complexity) : undefined
    };
  }

  /**
   * Analyze request complexity
   */
  private analyzeComplexity(request: PipelineRequest): {
    estimatedComplexity: 'low' | 'medium' | 'high';
    wordCount: number;
    hasConstraints: boolean;
    hasContext: boolean;
  } {
    const wordCount = request.userPrompt.split(' ').length;
    const hasConstraints = !!(request.constraints?.maxExecutionTime ||
                             request.constraints?.maxToolCalls ||
                             request.constraints?.allowedTools);
    const hasContext = !!(request.context?.conversationHistory?.length ||
                         request.context?.metadata);

    let estimatedComplexity: 'low' | 'medium' | 'high' = 'low';

    if (wordCount > 50 || hasConstraints || hasContext) {
      estimatedComplexity = 'high';
    } else if (wordCount > 20) {
      estimatedComplexity = 'medium';
    }

    return {
      estimatedComplexity,
      wordCount,
      hasConstraints,
      hasContext
    };
  }

  /**
   * Calculate confidence score for routing decision
   */
  private calculateConfidence(request: PipelineRequest, complexity: any): number {
    let confidence = 0.5; // Base confidence

    // Increase confidence based on complexity
    if (complexity.estimatedComplexity === 'high') {
      confidence += 0.3;
    } else if (complexity.estimatedComplexity === 'medium') {
      confidence += 0.1;
    }

    // Increase confidence for requests with constraints
    if (complexity.hasConstraints) {
      confidence += 0.1;
    }

    // Increase confidence for requests with context
    if (complexity.hasContext) {
      confidence += 0.1;
    }

    return Math.min(confidence, 1.0);
  }

  /**
   * Select appropriate model for AGNO processing
   */
  private selectModel(complexity: any): string {
    switch (complexity.estimatedComplexity) {
      case 'high':
        return 'gpt-4o';
      case 'medium':
        return 'claude-3-sonnet';
      default:
        return 'gpt-4o-mini';
    }
  }

  /**
   * Handle request with AGNO (placeholder for Phase 2A)
   */
  private async handleWithAGNO(
    request: PipelineRequest,
    routingDecision: RoutingDecision
  ): Promise<{ success: boolean; response: string; metadata: any }> {
    // This is a placeholder for Phase 2A implementation
    // In Phase 1A, we always fall back to existing orchestrator

    console.log(`AGNO routing requested for request ${request.sessionId}, but falling back to existing orchestrator`);

    return this.handleWithExisting(request, routingDecision);
  }

  /**
   * Handle request with existing orchestrator
   */
  private async handleWithExisting(
    _request: PipelineRequest,
    routingDecision: RoutingDecision
  ): Promise<{ success: boolean; response: string; metadata: any }> {
    try {
      // This would make an HTTP call to the existing orchestrator
      // For now, return a mock response

      const response = `Processed via existing orchestrator: ${routingDecision.reasoning}`;
      const metadata = {
        handler: 'existing-orchestrator',
        routingReason: routingDecision.reasoning,
        complexity: routingDecision.estimatedComplexity
      };

      return {
        success: true,
        response,
        metadata
      };

    } catch (error) {
      console.error('Existing orchestrator call failed:', error);
      throw error;
    }
  }

  /**
   * Set up event handlers
   */
  private setupEventHandlers(): void {
    this.on('initialized', () => {
      console.log('AGNO Coordinator initialized');
    });

    this.on('requestCompleted', (result: RoutingResult) => {
      console.log(`Request ${result.executionId} completed in ${result.executionTimeMs}ms`);
    });

    this.on('requestFailed', (result: RoutingResult) => {
      console.error(`Request ${result.executionId} failed: ${result.error}`);
    });
  }

  /**
   * Get service health status
   */
  getHealthStatus(): {
    service: string;
    status: 'healthy' | 'unhealthy';
    initialized: boolean;
    activeRequests: number;
    configValid: boolean;
    timestamp: string;
  } {
    const configValidation = configManager.validateConfig();

    return {
      service: 'agno-coordinator',
      status: this.isInitialized && configValidation.valid ? 'healthy' : 'unhealthy',
      initialized: this.isInitialized,
      activeRequests: this.activeRequests.size,
      configValid: configValidation.valid,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get service statistics
   */
  getStatistics(): {
    totalRequests: number;
    activeRequests: number;
    averageResponseTime: number;
    errorRate: number;
    routingDistribution: { existing: number; agno: number };
  } {
    // This would track real statistics in a production implementation
    return {
      totalRequests: 0,
      activeRequests: this.activeRequests.size,
      averageResponseTime: 0,
      errorRate: 0,
      routingDistribution: { existing: 100, agno: 0 }
    };
  }

  /**
   * Gracefully shutdown the service
   */
  async shutdown(): Promise<void> {
    console.log('Shutting down AGNO Coordinator Service...');

    // Wait for active requests to complete
    if (this.activeRequests.size > 0) {
      console.log(`Waiting for ${this.activeRequests.size} active requests to complete...`);
      // In a real implementation, you'd wait with a timeout
    }

    this.isInitialized = false;
    this.removeAllListeners();

    console.log('AGNO Coordinator Service shutdown complete');
  }
}

// Export singleton instance
export const agnosticCoordinator = new AgnosticCoordinator();