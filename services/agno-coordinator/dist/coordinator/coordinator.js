"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.agnosticCoordinator = exports.AgnosticCoordinator = void 0;
const events_1 = require("events");
const uuid_1 = require("uuid");
const featureFlags_1 = require("../config/featureFlags");
const config_1 = require("../config/config");
class AgnosticCoordinator extends events_1.EventEmitter {
    constructor() {
        super();
        this.isInitialized = false;
        this.activeRequests = new Map();
        this.config = config_1.configManager.getConfig();
        this.setupEventHandlers();
    }
    async initialize() {
        try {
            console.log('Initializing AGNO Coordinator Service...');
            const configValidation = config_1.configManager.validateConfig();
            if (!configValidation.valid) {
                throw new Error(`Configuration validation failed: ${configValidation.errors.join(', ')}`);
            }
            const flagValidation = featureFlags_1.featureFlags.validateConfiguration();
            if (!flagValidation.valid) {
                console.warn('Feature flag validation issues:', flagValidation.issues);
            }
            this.isInitialized = true;
            console.log('AGNO Coordinator Service initialized successfully');
            this.emit('initialized');
        }
        catch (error) {
            console.error('Failed to initialize AGNO Coordinator:', error);
            throw error;
        }
    }
    async routeRequest(request) {
        const executionId = (0, uuid_1.v4)();
        const startTime = Date.now();
        const result = {
            success: false,
            response: '',
            executionId,
            routingDecision: {},
            executionTimeMs: 0,
            source: 'existing',
            metadata: {
                requestId: executionId,
                timestamp: new Date().toISOString(),
                version: '1.0.0'
            }
        };
        try {
            this.activeRequests.set(executionId, result);
            const routingDecision = await this.makeRoutingDecision(request);
            result.routingDecision = routingDecision;
            if (routingDecision.source === 'agno') {
                result.source = 'agno';
                const agnoResult = await this.handleWithAGNO(request, routingDecision);
                result.response = agnoResult.response;
                result.success = agnoResult.success;
                result.metadata = { ...result.metadata, ...agnoResult.metadata };
            }
            else {
                result.source = 'existing';
                const existingResult = await this.handleWithExisting(request, routingDecision);
                result.response = existingResult.response;
                result.success = existingResult.success;
                result.metadata = { ...result.metadata, ...existingResult.metadata };
            }
            result.executionTimeMs = Date.now() - startTime;
            this.emit('requestCompleted', result);
            return result;
        }
        catch (error) {
            result.success = false;
            result.executionTimeMs = Date.now() - startTime;
            result.error = error instanceof Error ? error.message : 'Unknown error';
            result.metadata.error = result.error;
            console.error(`Request routing failed for ${executionId}:`, error);
            this.emit('requestFailed', result);
            return result;
        }
        finally {
            this.activeRequests.delete(executionId);
        }
    }
    async makeRoutingDecision(request) {
        const routingConfig = this.config.routing;
        if (!routingConfig.enabled) {
            return {
                source: 'existing',
                confidence: 1.0,
                reasoning: 'AGNO routing disabled by configuration',
                estimatedComplexity: 'low',
                fallbackEnabled: true
            };
        }
        const complexity = this.analyzeComplexity(request);
        const confidence = this.calculateConfidence(complexity);
        const shouldUseAGNO = complexity.estimatedComplexity !== 'low' &&
            confidence >= routingConfig.confidenceThreshold;
        return {
            source: shouldUseAGNO ? 'agno' : 'existing',
            confidence,
            reasoning: shouldUseAGNO
                ? `Request complexity (${complexity.estimatedComplexity}) meets threshold`
                : `Request complexity (${complexity.estimatedComplexity}) below threshold`,
            estimatedComplexity: complexity.estimatedComplexity,
            fallbackEnabled: featureFlags_1.featureFlags.isEnabled('agno_fallback'),
            recommendedModel: shouldUseAGNO ? this.selectModel(complexity) : undefined
        };
    }
    analyzeComplexity(request) {
        const wordCount = request.userPrompt.split(' ').length;
        const hasConstraints = !!(request.constraints?.maxExecutionTime ||
            request.constraints?.maxToolCalls ||
            request.constraints?.allowedTools);
        const hasContext = !!(request.context?.conversationHistory?.length ||
            request.context?.metadata);
        let estimatedComplexity = 'low';
        if (wordCount > 50 || hasConstraints || hasContext) {
            estimatedComplexity = 'high';
        }
        else if (wordCount > 20) {
            estimatedComplexity = 'medium';
        }
        return {
            estimatedComplexity,
            wordCount,
            hasConstraints,
            hasContext
        };
    }
    calculateConfidence(complexity) {
        let confidence = 0.5;
        if (complexity.estimatedComplexity === 'high') {
            confidence += 0.3;
        }
        else if (complexity.estimatedComplexity === 'medium') {
            confidence += 0.1;
        }
        if (complexity.hasConstraints) {
            confidence += 0.1;
        }
        if (complexity.hasContext) {
            confidence += 0.1;
        }
        return Math.min(confidence, 1.0);
    }
    selectModel(complexity) {
        switch (complexity.estimatedComplexity) {
            case 'high':
                return 'gpt-4o';
            case 'medium':
                return 'claude-3-sonnet';
            default:
                return 'gpt-4o-mini';
        }
    }
    async handleWithAGNO(request, routingDecision) {
        console.log(`AGNO routing requested for request ${request.sessionId}, but falling back to existing orchestrator`);
        return this.handleWithExisting(request, routingDecision);
    }
    async handleWithExisting(_request, routingDecision) {
        try {
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
        }
        catch (error) {
            console.error('Existing orchestrator call failed:', error);
            throw error;
        }
    }
    setupEventHandlers() {
        this.on('initialized', () => {
            console.log('AGNO Coordinator initialized');
        });
        this.on('requestCompleted', (result) => {
            console.log(`Request ${result.executionId} completed in ${result.executionTimeMs}ms`);
        });
        this.on('requestFailed', (result) => {
            console.error(`Request ${result.executionId} failed: ${result.error}`);
        });
    }
    getHealthStatus() {
        const configValidation = config_1.configManager.validateConfig();
        return {
            service: 'agno-coordinator',
            status: this.isInitialized && configValidation.valid ? 'healthy' : 'unhealthy',
            initialized: this.isInitialized,
            activeRequests: this.activeRequests.size,
            configValid: configValidation.valid,
            timestamp: new Date().toISOString()
        };
    }
    getStatistics() {
        return {
            totalRequests: 0,
            activeRequests: this.activeRequests.size,
            averageResponseTime: 0,
            errorRate: 0,
            routingDistribution: { existing: 100, agno: 0 }
        };
    }
    async shutdown() {
        console.log('Shutting down AGNO Coordinator Service...');
        if (this.activeRequests.size > 0) {
            console.log(`Waiting for ${this.activeRequests.size} active requests to complete...`);
        }
        this.isInitialized = false;
        this.removeAllListeners();
        console.log('AGNO Coordinator Service shutdown complete');
    }
}
exports.AgnosticCoordinator = AgnosticCoordinator;
exports.agnosticCoordinator = new AgnosticCoordinator();
//# sourceMappingURL=coordinator.js.map