import { EventEmitter } from 'events';
import { PipelineRequest, RoutingResult } from '../config/types';
export declare class AgnosticCoordinator extends EventEmitter {
    private isInitialized;
    private activeRequests;
    private config;
    constructor();
    initialize(): Promise<void>;
    routeRequest(request: PipelineRequest): Promise<RoutingResult>;
    private makeRoutingDecision;
    private analyzeComplexity;
    private calculateConfidence;
    private selectModel;
    private handleWithAGNO;
    private handleWithExisting;
    private setupEventHandlers;
    getHealthStatus(): {
        service: string;
        status: 'healthy' | 'unhealthy';
        initialized: boolean;
        activeRequests: number;
        configValid: boolean;
        timestamp: string;
    };
    getStatistics(): {
        totalRequests: number;
        activeRequests: number;
        averageResponseTime: number;
        errorRate: number;
        routingDistribution: {
            existing: number;
            agno: number;
        };
    };
    shutdown(): Promise<void>;
}
export declare const agnosticCoordinator: AgnosticCoordinator;
//# sourceMappingURL=coordinator.d.ts.map