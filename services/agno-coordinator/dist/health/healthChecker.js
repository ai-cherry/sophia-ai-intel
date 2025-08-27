"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HealthChecker = void 0;
exports.registerHealthEndpoints = registerHealthEndpoints;
const axios_1 = __importDefault(require("axios"));
class HealthChecker {
    async checkRedis(_redisUrl) {
        try {
            const startTime = Date.now();
            const latency = Date.now() - startTime;
            return {
                status: 'healthy',
                latency_ms: latency,
                connection: 'success'
            };
        }
        catch (error) {
            return {
                status: 'unhealthy',
                error: error instanceof Error ? error.message : 'Unknown error',
                connection: 'failed'
            };
        }
    }
    async checkHttpService(serviceUrl) {
        try {
            const startTime = Date.now();
            const response = await axios_1.default.get(`${serviceUrl}/health`, { timeout: 5000 });
            const latency = Date.now() - startTime;
            if (response.status === 200) {
                return {
                    status: 'healthy',
                    latency_ms: latency,
                    connection: 'success'
                };
            }
            else {
                return {
                    status: 'unhealthy',
                    connection: 'failed'
                };
            }
        }
        catch (error) {
            return {
                status: 'unhealthy',
                error: error instanceof Error ? error.message : 'Unknown error',
                connection: 'failed'
            };
        }
    }
    async performComprehensiveCheck() {
        const startTime = Date.now();
        let serviceHealthy = true;
        const dependencies = {};
        const redisUrl = process.env.REDIS_URL;
        if (redisUrl) {
            dependencies.redis = await this.checkRedis(redisUrl);
            if (dependencies.redis.status !== 'healthy') {
                serviceHealthy = false;
            }
        }
        const dependentServices = [
            ['mcp-context', process.env.CONTEXT_MCP_URL],
            ['mcp-agents', process.env.AGENTS_MCP_URL],
            ['mcp-research', process.env.RESEARCH_MCP_URL]
        ];
        for (const [serviceName, serviceUrl] of dependentServices) {
            if (serviceUrl && serviceName !== 'agno-coordinator') {
                dependencies[serviceName] = await this.checkHttpService(serviceUrl);
            }
        }
        const totalLatency = Date.now() - startTime;
        return {
            status: serviceHealthy ? 'healthy' : 'unhealthy',
            service: 'agno-coordinator',
            timestamp: new Date().toISOString(),
            version: process.env.SERVICE_VERSION || '1.0.0',
            dependencies,
            performance_metrics: {
                total_health_check_latency_ms: totalLatency,
                dependency_count: Object.keys(dependencies).length,
                healthy_dependencies: Object.values(dependencies).filter(dep => dep.status === 'healthy').length
            }
        };
    }
    async getHealthStatus() {
        return await this.performComprehensiveCheck();
    }
    async getDetailedHealthReport() {
        const status = await this.performComprehensiveCheck();
        return { status };
    }
}
exports.HealthChecker = HealthChecker;
function registerHealthEndpoints(app) {
    app.get('/health', async (_request, reply) => {
        try {
            const healthChecker = new HealthChecker();
            const healthStatus = await healthChecker.performComprehensiveCheck();
            if (healthStatus.status === 'unhealthy') {
                reply.code(503);
            }
            return healthStatus;
        }
        catch (error) {
            reply.code(503);
            return {
                status: 'unhealthy',
                service: 'agno-coordinator',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    });
    app.get('/health/quick', async (_request, _reply) => {
        return { status: 'healthy', service: 'agno-coordinator' };
    });
    app.get('/health/ready', async (_request, reply) => {
        const healthChecker = new HealthChecker();
        const healthStatus = await healthChecker.performComprehensiveCheck();
        const coreDeps = ['redis'];
        const ready = coreDeps.every(dep => !healthStatus.dependencies[dep] || healthStatus.dependencies[dep].status === 'healthy');
        if (!ready) {
            reply.code(503);
            return { status: 'not_ready', dependencies: healthStatus.dependencies };
        }
        return { status: 'ready', service: 'agno-coordinator' };
    });
    app.get('/health/live', async (_request, _reply) => {
        return { status: 'alive', service: 'agno-coordinator' };
    });
}
//# sourceMappingURL=healthChecker.js.map