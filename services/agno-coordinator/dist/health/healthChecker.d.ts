import { FastifyInstance } from 'fastify';
interface HealthStatus {
    status: string;
    service: string;
    timestamp: string;
    version: string;
    dependencies: Record<string, any>;
    performance_metrics: Record<string, any>;
}
interface DependencyResult {
    status: string;
    latency_ms?: number;
    connection: string;
    error?: string;
}
export declare class HealthChecker {
    checkRedis(_redisUrl: string): Promise<DependencyResult>;
    checkHttpService(serviceUrl: string): Promise<DependencyResult>;
    performComprehensiveCheck(): Promise<HealthStatus>;
    getHealthStatus(): Promise<HealthStatus>;
    getDetailedHealthReport(): Promise<{
        status: HealthStatus;
    }>;
}
export declare function registerHealthEndpoints(app: FastifyInstance): void;
export {};
//# sourceMappingURL=healthChecker.d.ts.map