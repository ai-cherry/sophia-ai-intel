# Sophia AI Phase 1A: Foundation - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks  
**Priority**: IMMEDIATE EXECUTION  
**Goal**: Establish AGNO Coordinator foundation with zero disruption to existing services

## Executive Summary

Phase 1A establishes the foundational AGNO Coordinator service that will enable gradual migration from the existing PipelineOrchestrator to an AGNO-based architecture. This phase focuses on:

1. Creating the AGNO Coordinator service in TypeScript
2. Implementing a feature flag system for controlled rollout
3. Building integration layers with existing services
4. Setting up comprehensive monitoring and health checks

## Week 1: Core Implementation

### Day 1-2: Project Setup & Architecture

#### 1.1 AGNO Coordinator Service Structure
```
services/agno-coordinator/
├── src/
│   ├── index.ts                 # Main entry point
│   ├── coordinator.ts           # AgnosticCoordinator class
│   ├── routing/
│   │   ├── router.ts           # Request routing logic
│   │   ├── strategies/         # Routing strategies
│   │   │   ├── agno.ts        # AGNO routing strategy
│   │   │   └── legacy.ts      # Legacy routing strategy
│   │   └── analyzer.ts         # Request complexity analyzer
│   ├── integration/
│   │   ├── pipeline.ts         # PipelineOrchestrator integration
│   │   └── mcp-bridge.ts       # MCP service bridge
│   ├── monitoring/
│   │   ├── health.ts           # Health check endpoints
│   │   ├── metrics.ts          # Prometheus metrics
│   │   └── tracing.ts          # OpenTelemetry tracing
│   └── config/
│       ├── index.ts            # Configuration loader
│       └── validation.ts       # Config validation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Dockerfile
├── package.json
├── tsconfig.json
└── README.md
```

#### 1.2 Initial TypeScript Configuration
```typescript
// services/agno-coordinator/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

#### 1.3 Package Dependencies
```json
// services/agno-coordinator/package.json
{
  "name": "@sophia-ai/agno-coordinator",
  "version": "0.1.0",
  "description": "AGNO Coordinator Service for Sophia AI",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node-dev --respawn --transpile-only src/index.ts",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src --ext .ts",
    "lint:fix": "eslint src --ext .ts --fix"
  },
  "dependencies": {
    "@opentelemetry/api": "^1.9.0",
    "@opentelemetry/instrumentation-express": "^0.38.0",
    "@opentelemetry/instrumentation-http": "^0.51.1",
    "@opentelemetry/sdk-node": "^0.51.1",
    "express": "^4.19.2",
    "prom-client": "^15.1.2",
    "winston": "^3.13.0",
    "axios": "^1.6.8",
    "joi": "^17.13.1",
    "dotenv": "^16.4.5",
    "bullmq": "^5.7.8",
    "ioredis": "^5.3.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.12.7",
    "@typescript-eslint/eslint-plugin": "^7.7.0",
    "@typescript-eslint/parser": "^7.7.0",
    "eslint": "^8.57.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.2",
    "ts-node-dev": "^2.0.0",
    "typescript": "^5.4.5"
  }
}
```

### Day 3-4: Core Coordinator Implementation

#### 1.4 AgnosticCoordinator Class
```typescript
// services/agno-coordinator/src/coordinator.ts
import { EventEmitter } from 'events';
import { PipelineOrchestrator } from './integration/pipeline';
import { FeatureFlags } from '../../libs/feature-flags';
import { RequestAnalyzer } from './routing/analyzer';
import { Router } from './routing/router';
import { MetricsCollector } from './monitoring/metrics';
import { Logger } from './utils/logger';

export interface CoordinatorConfig {
  pipelineOrchestratorUrl: string;
  featureFlags: FeatureFlags;
  enableMetrics: boolean;
  enableTracing: boolean;
  maxRetries: number;
  timeoutMs: number;
}

export class AgnosticCoordinator extends EventEmitter {
  private pipeline: PipelineOrchestrator;
  private featureFlags: FeatureFlags;
  private router: Router;
  private analyzer: RequestAnalyzer;
  private metrics: MetricsCollector;
  private logger: Logger;

  constructor(config: CoordinatorConfig) {
    super();
    this.featureFlags = config.featureFlags;
    this.pipeline = new PipelineOrchestrator(config.pipelineOrchestratorUrl);
    this.analyzer = new RequestAnalyzer();
    this.router = new Router(config);
    this.metrics = new MetricsCollector(config.enableMetrics);
    this.logger = new Logger('AgnosticCoordinator');
  }

  async routeRequest(request: PipelineRequest): Promise<RoutingResult> {
    const startTime = Date.now();
    const requestId = this.generateRequestId();
    
    try {
      // Analyze request complexity and characteristics
      const analysis = await this.analyzer.analyze(request);
      this.logger.info('Request analyzed', { requestId, analysis });
      
      // Check feature flags for routing decision
      const useAGNO = this.shouldUseAGNO(request, analysis);
      
      // Route request based on decision
      let result: RoutingResult;
      if (useAGNO) {
        this.metrics.incrementCounter('agno_requests_total');
        result = await this.handleWithAGNO(request, analysis);
      } else {
        this.metrics.incrementCounter('legacy_requests_total');
        result = await this.handleWithExisting(request);
      }
      
      // Record metrics
      const duration = Date.now() - startTime;
      this.metrics.recordHistogram('request_duration_ms', duration, {
        routing: useAGNO ? 'agno' : 'legacy',
        success: result.success.toString()
      });
      
      return result;
    } catch (error) {
      this.logger.error('Request routing failed', { requestId, error });
      this.metrics.incrementCounter('routing_errors_total');
      throw error;
    }
  }

  private shouldUseAGNO(request: PipelineRequest, analysis: RequestAnalysis): boolean {
    // Check global AGNO routing flag
    if (!this.featureFlags.isEnabled('agno_routing')) {
      return false;
    }
    
    // Check request-specific criteria
    if (analysis.complexity === 'high' && this.featureFlags.isEnabled('agno_complex_requests')) {
      return true;
    }
    
    // Check user-specific rollout
    if (request.userId && this.featureFlags.isEnabledForUser('agno_routing', request.userId)) {
      return true;
    }
    
    // Check percentage-based rollout
    return this.featureFlags.isInRolloutPercentage('agno_routing', request.requestId);
  }

  private async handleWithAGNO(request: PipelineRequest, analysis: RequestAnalysis): Promise<RoutingResult> {
    // Implementation will be added in Week 2
    this.logger.info('Routing to AGNO', { requestId: request.requestId });
    
    // For now, fallback to existing pipeline
    return this.handleWithExisting(request);
  }

  private async handleWithExisting(request: PipelineRequest): Promise<RoutingResult> {
    return await this.pipeline.execute(request);
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

### Day 5: Feature Flag System

#### 1.5 Feature Flag Implementation
```typescript
// libs/feature-flags/src/index.ts
import { Redis } from 'ioredis';
import { createHash } from 'crypto';

export interface FeatureFlagConfig {
  redisUrl: string;
  refreshIntervalMs: number;
  defaultFlags: Record<string, boolean>;
}

export class FeatureFlags {
  private redis: Redis;
  private cache: Map<string, FeatureFlagValue> = new Map();
  private refreshInterval: NodeJS.Timer;

  constructor(config: FeatureFlagConfig) {
    this.redis = new Redis(config.redisUrl);
    this.initializeDefaults(config.defaultFlags);
    this.startRefreshInterval(config.refreshIntervalMs);
  }

  async isEnabled(flagName: string): Promise<boolean> {
    const flag = await this.getFlag(flagName);
    return flag?.enabled || false;
  }

  async isEnabledForUser(flagName: string, userId: string): Promise<boolean> {
    const flag = await this.getFlag(flagName);
    if (!flag || !flag.enabled) return false;
    
    // Check user-specific overrides
    if (flag.enabledUsers?.includes(userId)) return true;
    if (flag.disabledUsers?.includes(userId)) return false;
    
    // Check percentage rollout
    if (flag.rolloutPercentage !== undefined) {
      return this.isInPercentage(userId, flag.rolloutPercentage);
    }
    
    return flag.enabled;
  }

  async isInRolloutPercentage(flagName: string, identifier: string): Promise<boolean> {
    const flag = await this.getFlag(flagName);
    if (!flag || !flag.enabled || flag.rolloutPercentage === undefined) {
      return false;
    }
    
    return this.isInPercentage(identifier, flag.rolloutPercentage);
  }

  private isInPercentage(identifier: string, percentage: number): boolean {
    const hash = createHash('md5').update(identifier).digest('hex');
    const hashInt = parseInt(hash.substring(0, 8), 16);
    return (hashInt % 100) < percentage;
  }

  private async getFlag(flagName: string): Promise<FeatureFlagValue | null> {
    // Check cache first
    if (this.cache.has(flagName)) {
      return this.cache.get(flagName)!;
    }
    
    // Fetch from Redis
    const flagData = await this.redis.get(`feature_flag:${flagName}`);
    if (flagData) {
      const flag = JSON.parse(flagData) as FeatureFlagValue;
      this.cache.set(flagName, flag);
      return flag;
    }
    
    return null;
  }

  private initializeDefaults(defaultFlags: Record<string, boolean>) {
    Object.entries(defaultFlags).forEach(([name, enabled]) => {
      this.cache.set(name, { name, enabled });
    });
  }

  private startRefreshInterval(intervalMs: number) {
    this.refreshInterval = setInterval(async () => {
      await this.refreshFlags();
    }, intervalMs);
  }

  private async refreshFlags() {
    try {
      const keys = await this.redis.keys('feature_flag:*');
      for (const key of keys) {
        const flagData = await this.redis.get(key);
        if (flagData) {
          const flag = JSON.parse(flagData) as FeatureFlagValue;
          this.cache.set(flag.name, flag);
        }
      }
    } catch (error) {
      console.error('Failed to refresh feature flags:', error);
    }
  }

  async close() {
    clearInterval(this.refreshInterval);
    await this.redis.quit();
  }
}

interface FeatureFlagValue {
  name: string;
  enabled: boolean;
  description?: string;
  rolloutPercentage?: number;
  enabledUsers?: string[];
  disabledUsers?: string[];
  metadata?: Record<string, any>;
}
```

#### 1.6 Feature Flag Configuration UI
```typescript
// services/agno-coordinator/src/api/feature-flags.ts
import { Router } from 'express';
import { FeatureFlags } from '../../../libs/feature-flags';

export function createFeatureFlagRouter(featureFlags: FeatureFlags): Router {
  const router = Router();

  // Get all feature flags
  router.get('/flags', async (req, res) => {
    try {
      const flags = await featureFlags.getAllFlags();
      res.json(flags);
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch feature flags' });
    }
  });

  // Update a feature flag
  router.put('/flags/:flagName', async (req, res) => {
    try {
      const { flagName } = req.params;
      const updates = req.body;
      await featureFlags.updateFlag(flagName, updates);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: 'Failed to update feature flag' });
    }
  });

  // Check if flag is enabled for user
  router.get('/flags/:flagName/check', async (req, res) => {
    try {
      const { flagName } = req.params;
      const { userId } = req.query;
      const enabled = userId 
        ? await featureFlags.isEnabledForUser(flagName, userId as string)
        : await featureFlags.isEnabled(flagName);
      res.json({ enabled });
    } catch (error) {
      res.status(500).json({ error: 'Failed to check feature flag' });
    }
  });

  return router;
}
```

## Week 2: Integration & Monitoring

### Day 6-7: Integration Layer

#### 2.1 Pipeline Orchestrator Integration
```typescript
// services/agno-coordinator/src/integration/pipeline.ts
import axios, { AxiosInstance } from 'axios';
import { CircuitBreaker } from '../utils/circuit-breaker';
import { RetryPolicy } from '../utils/retry-policy';

export class PipelineOrchestrator {
  private client: AxiosInstance;
  private circuitBreaker: CircuitBreaker;
  private retryPolicy: RetryPolicy;

  constructor(baseUrl: string) {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000,
      monitoringPeriod: 60000
    });

    this.retryPolicy = new RetryPolicy({
      maxRetries: 3,
      initialDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2
    });
  }

  async execute(request: PipelineRequest): Promise<RoutingResult> {
    return await this.circuitBreaker.execute(async () => {
      return await this.retryPolicy.execute(async () => {
        const response = await this.client.post('/pipeline/execute', request);
        return this.transformResponse(response.data);
      });
    });
  }

  private transformResponse(pipelineResponse: any): RoutingResult {
    return {
      success: pipelineResponse.status === 'completed',
      requestId: pipelineResponse.requestId,
      result: pipelineResponse.result,
      metadata: {
        duration: pipelineResponse.duration,
        phases: pipelineResponse.phases,
        model: pipelineResponse.model
      }
    };
  }
}
```

#### 2.2 MCP Service Bridge
```typescript
// services/agno-coordinator/src/integration/mcp-bridge.ts
export class MCPServiceBridge {
  private services: Map<string, MCPServiceClient> = new Map();

  constructor(serviceConfigs: MCPServiceConfig[]) {
    serviceConfigs.forEach(config => {
      this.services.set(config.name, new MCPServiceClient(config));
    });
  }

  async callService(serviceName: string, method: string, params: any): Promise<any> {
    const client = this.services.get(serviceName);
    if (!client) {
      throw new Error(`MCP service '${serviceName}' not found`);
    }

    return await client.call(method, params);
  }

  getAvailableServices(): string[] {
    return Array.from(this.services.keys());
  }
}

class MCPServiceClient {
  private config: MCPServiceConfig;
  private client: AxiosInstance;

  constructor(config: MCPServiceConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.url,
      timeout: config.timeout || 30000
    });
  }

  async call(method: string, params: any): Promise<any> {
    const response = await this.client.post('/rpc', {
      jsonrpc: '2.0',
      method,
      params,
      id: Date.now()
    });

    if (response.data.error) {
      throw new Error(response.data.error.message);
    }

    return response.data.result;
  }
}

interface MCPServiceConfig {
  name: string;
  url: string;
  timeout?: number;
  auth?: {
    type: 'bearer' | 'basic';
    credentials: string;
  };
}
```

### Day 8-9: Monitoring & Health Checks

#### 2.3 Health Check Implementation
```typescript
// services/agno-coordinator/src/monitoring/health.ts
import { Router } from 'express';
import { PipelineOrchestrator } from '../integration/pipeline';
import { MCPServiceBridge } from '../integration/mcp-bridge';
import { FeatureFlags } from '../../../libs/feature-flags';

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  checks: {
    [key: string]: {
      status: 'pass' | 'fail';
      message?: string;
      duration?: number;
    };
  };
}

export class HealthChecker {
  constructor(
    private pipeline: PipelineOrchestrator,
    private mcpBridge: MCPServiceBridge,
    private featureFlags: FeatureFlags
  ) {}

  async performHealthCheck(): Promise<HealthCheckResult> {
    const checks: HealthCheckResult['checks'] = {};
    
    // Check Pipeline Orchestrator
    checks.pipeline = await this.checkPipeline();
    
    // Check MCP Services
    const mcpServices = this.mcpBridge.getAvailableServices();
    for (const service of mcpServices) {
      checks[`mcp_${service}`] = await this.checkMCPService(service);
    }
    
    // Check Feature Flags
    checks.featureFlags = await this.checkFeatureFlags();
    
    // Check Redis
    checks.redis = await this.checkRedis();
    
    // Determine overall status
    const failedChecks = Object.values(checks).filter(check => check.status === 'fail');
    const status = failedChecks.length === 0 ? 'healthy' : 
                   failedChecks.length < Object.keys(checks).length / 2 ? 'degraded' : 'unhealthy';
    
    return {
      status,
      timestamp: new Date().toISOString(),
      version: process.env.APP_VERSION || '0.1.0',
      checks
    };
  }

  private async checkPipeline(): Promise<HealthCheckResult['checks'][string]> {
    const start = Date.now();
    try {
      // Send a health check request to pipeline
      await this.pipeline.execute({
        type: 'health_check',
        requestId: 'health_' + Date.now(),
        userId: 'system',
        content: 'ping'
      });
      
      return {
        status: 'pass',
        duration: Date.now() - start
      };
    } catch (error) {
      return {
        status: 'fail',
        message: error.message,
        duration: Date.now() - start
      };
    }
  }

  private async checkMCPService(serviceName: string): Promise<HealthCheckResult['checks'][string]> {
    const start = Date.now();
    try {
      await this.mcpBridge.callService(serviceName, 'health', {});
      return {
        status: 'pass',
        duration: Date.now() - start
      };
    } catch (error) {
      return {
        status: 'fail',
        message: error.message,
        duration: Date.now() - start
      };
    }
  }

  private async checkFeatureFlags(): Promise<HealthCheckResult['checks'][string]> {
    try {
      // Test a known feature flag
      await this.featureFlags.isEnabled('health_check_flag');
      return { status: 'pass' };
    } catch (error) {
      return {
        status: 'fail',
        message: error.message
      };
    }
  }

  private async checkRedis(): Promise<HealthCheckResult['checks'][string]> {
    // Implementation depends on Redis client setup
    return { status: 'pass' };
  }
}

export function createHealthRouter(healthChecker: HealthChecker): Router {
  const router = Router();

  router.get('/health', async (req, res) => {
    const result = await healthChecker.performHealthCheck();
    const statusCode = result.status === 'healthy' ? 200 : 
                      result.status === 'degraded' ? 503 : 503;
    res.status(statusCode).json(result);
  });

  router.get('/health/live', (req, res) => {
    res.status(200).json({ status: 'alive' });
  });

  router.get('/health/ready', async (req, res) => {
    const result = await healthChecker.performHealthCheck();
    if (result.status === 'healthy') {
      res.status(200).json({ ready: true });
    } else {
      res.status(503).json({ ready: false, reason: result });
    }
  });

  return router;
}
```

#### 2.4 Prometheus Metrics
```typescript
// services/agno-coordinator/src/monitoring/metrics.ts
import { Registry, Counter, Histogram, Gauge, Summary } from 'prom-client';

export class MetricsCollector {
  private registry: Registry;
  private counters: Map<string, Counter> = new Map();
  private histograms: Map<string, Histogram> = new Map();
  private gauges: Map<string, Gauge> = new Map();
  private summaries: Map<string, Summary> = new Map();

  constructor(enabled: boolean = true) {
    this.registry = new Registry();
    
    if (enabled) {
      this.initializeMetrics();
    }
  }

  private initializeMetrics() {
    // Request counters
    this.counters.set('agno_requests_total', new Counter({
      name: 'agno_requests_total',
      help: 'Total number of requests routed through AGNO',
      labelNames: ['status', 'route'],
      registers: [this.registry]
    }));

    this.counters.set('legacy_requests_total', new Counter({
      name: 'legacy_requests_total',
      help: 'Total number of requests routed through legacy pipeline',
      labelNames: ['status'],
      registers: [this.registry]
    }));

    this.counters.set('routing_errors_total', new Counter({
      name: 'routing_errors_total',
      help: 'Total number of routing errors',
      labelNames: ['type'],
      registers: [this.registry]
    }));

    // Duration histograms
    this.histograms.set('request_duration_ms', new Histogram({
      name: 'request_duration_ms',
      help: 'Request duration in milliseconds',
      labelNames: ['routing', 'success'],
      buckets: [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
      registers: [this.registry]
    }));

    // Active requests gauge
    this.gauges.set('active_requests', new Gauge({
      name: 'active_requests',
      help: 'Number of active requests',
      labelNames: ['routing'],
      registers: [this.registry]
    }));

    // Feature flag metrics
    this.gauges.set('feature_flag_enabled', new Gauge({
      name: 'feature_flag_enabled',
      help: 'Feature flag status (1 = enabled, 0 = disabled)',
      labelNames: ['flag_name'],
      registers: [this.registry]
    }));

    // Circuit breaker metrics
    this.gauges.set('circuit_breaker_state', new Gauge({
      name: 'circuit_breaker_state',
      help: 'Circuit breaker state (0 = closed, 1 = open, 2 = half-open)',
      labelNames: ['service'],
      registers: [this.registry]
    }));
  }

  incrementCounter(name: string, labels?: Record<string, string>) {
    const counter = this.counters.get(name);
    if (counter) {
      counter.inc(labels);
    }
  }

  recordHistogram(name: string, value: number, labels?: Record<string, string>) {
    const histogram = this.histograms.get(name);
    if (histogram) {
      histogram.observe(labels, value);
    }
  }

  setGauge(name: string, value: number, labels?: Record<string, string>) {
    const gauge = this.gauges.get(name);
    if (gauge) {
      gauge.set(labels, value);
    }
  }

  getMetrics(): Promise<string> {
    return this.registry.metrics();
  }

  getContentType(): string {
    return this.registry.contentType;
  }
}
```

### Day 10: Testing & Documentation

#### 2.5 Integration Tests
```typescript
// services/agno-coordinator/tests/integration/coordinator.test.ts
import { AgnosticCoordinator } from '../../src/coordinator';
import { FeatureFlags } from '../../../../libs/feature-flags';
import { MockPipelineOrchestrator } from '../mocks/pipeline';

describe('AgnosticCoordinator Integration Tests', () => {
  let coordinator: AgnosticCoordinator;
  let featureFlags: FeatureFlags;
  let mockPipeline: MockPipelineOrchestrator;

  beforeEach(() => {
    featureFlags = new FeatureFlags({
      redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
      refreshIntervalMs: 1000,
      defaultFlags: {
        agno_routing: false,
        agno_complex_requests: false
      }
    });

    mockPipeline = new MockPipelineOrchestrator();
    
    coordinator = new AgnosticCoordinator({
      pipelineOrchestratorUrl: 'http://localhost:3000',
      featureFlags,
      enableMetrics: true,
      enableTracing: false,
      maxRetries: 3,
      timeoutMs: 30000
    });
  });

  afterEach(async () => {
    await featureFlags.close();
  });

  describe('Request Routing', () => {
    test('should route to legacy pipeline when AGNO is disabled', async () => {
      const request = {
        type: 'chat',
        requestId: 'test_123',
        userId: 'user_123',
        content: 'Hello'
      };

      const result = await coordinator.routeRequest(request);
      
      expect(result.success).toBe(true);
      expect(mockPipeline.executeCalled).toBe(true);
    });

    test('should route to AGNO when feature flag is enabled', async () => {
      await featureFlags.updateFlag('agno_routing', { enabled: true });
      
      const request = {
        type: 'chat',
        requestId: 'test_456',
        userId: 'user_456',
        content: 'Complex query about quantum computing'
      };

      const result = await coordinator.routeRequest(request);
      
      // Since AGNO is not yet implemented, it should fallback
      expect(result.success).toBe(true);
    });

    test('should handle
