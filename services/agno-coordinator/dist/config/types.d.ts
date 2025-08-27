export interface PipelineRequest {
    userPrompt: string;
    sessionId: string;
    userId?: string;
    context?: {
        conversationHistory?: Array<{
            role: 'user' | 'assistant' | 'system';
            content: string;
            timestamp: Date;
        }>;
        metadata?: Record<string, any>;
        preferences?: {
            responseLength?: 'brief' | 'moderate' | 'detailed';
            technicalLevel?: 'beginner' | 'intermediate' | 'expert';
            includeReferences?: boolean;
            prioritizeSpeed?: boolean;
        };
    };
    constraints?: {
        maxExecutionTime?: number;
        maxToolCalls?: number;
        allowedTools?: string[];
        requiredSources?: string[];
    };
}
export interface RoutingDecision {
    source: 'existing' | 'agno';
    confidence: number;
    reasoning: string;
    estimatedComplexity: 'low' | 'medium' | 'high';
    recommendedModel?: string | undefined;
    fallbackEnabled: boolean;
}
export interface RoutingResult {
    success: boolean;
    response: string;
    executionId: string;
    routingDecision: RoutingDecision;
    executionTimeMs: number;
    source: 'existing' | 'agno';
    error?: string;
    metadata: Record<string, any>;
}
export interface CoordinatorConfig {
    routing: {
        enabled: boolean;
        complexityThreshold: number;
        confidenceThreshold: number;
    };
    fallback: {
        enabled: boolean;
        timeoutMs: number;
        retryAttempts: number;
    };
    monitoring: {
        enabled: boolean;
        metricsInterval: number;
    };
    services: {
        existingOrchestratorUrl: string;
        redisUrl: string;
        maxRetries: number;
        requestTimeout: number;
    };
}
export interface HealthStatus {
    service: string;
    status: 'healthy' | 'unhealthy' | 'degraded';
    timestamp: string;
    version: string;
    checks: {
        redis: boolean;
        existingOrchestrator: boolean;
        memory: boolean;
        cpu: boolean;
    };
    metrics: {
        activeRequests: number;
        totalRequests: number;
        averageResponseTime: number;
        errorRate: number;
    };
}
export interface FeatureFlags {
    isEnabled(flag: string): boolean;
    setFlag(flag: string, enabled: boolean): void;
    getAllFlags(): Record<string, boolean>;
}
export interface CircuitBreakerState {
    state: 'closed' | 'open' | 'half-open';
    failures: number;
    lastFailureTime: number;
    successCount: number;
}
export interface MonitoringMetrics {
    requestCount: number;
    errorCount: number;
    averageResponseTime: number;
    routingDecisions: {
        existing: number;
        agno: number;
    };
    fallbackActivations: number;
    circuitBreakerState: CircuitBreakerState;
}
//# sourceMappingURL=types.d.ts.map