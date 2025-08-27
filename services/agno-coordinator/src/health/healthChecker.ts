// Health Check Implementation for agno-coordinator
// Comprehensive health monitoring with dependency validation

import { FastifyInstance } from 'fastify';
import axios from 'axios';

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

class HealthChecker {
  
  static async checkRedis(redisUrl: string): Promise<DependencyResult> {
    try {
      const startTime = Date.now();
      // TODO: Implement Redis client check
      const latency = Date.now() - startTime;
      
      return {
        status: 'healthy',
        latency_ms: latency,
        connection: 'success'
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        connection: 'failed'
      };
    }
  }
  
  static async checkHttpService(serviceUrl: string): Promise<DependencyResult> {
    try {
      const startTime = Date.now();
      const response = await axios.get(`${serviceUrl}/health`, { timeout: 5000 });
      const latency = Date.now() - startTime;
      
      if (response.status === 200) {
        return {
          status: 'healthy',
          latency_ms: latency,
          connection: 'success'
        };
      } else {
        return {
          status: 'unhealthy',
          connection: 'failed'
        };
      }
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        connection: 'failed'
      };
    }
  }
  
  static async performComprehensiveCheck(): Promise<HealthStatus> {
    const startTime = Date.now();
    let serviceHealthy = true;
    const dependencies: Record<string, any> = {};
    
    // Check Redis if configured
    const redisUrl = process.env.REDIS_URL;
    if (redisUrl) {
      dependencies.redis = await this.checkRedis(redisUrl);
      if (dependencies.redis.status !== 'healthy') {
        serviceHealthy = false;
      }
    }
    
    // Check dependent services
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
}

export function registerHealthEndpoints(app: FastifyInstance) {
  
  // Comprehensive health check
  app.get('/health', async (request, reply) => {
    try {
      const healthStatus = await HealthChecker.performComprehensiveCheck();
      
      if (healthStatus.status === 'unhealthy') {
        reply.code(503);
      }
      
      return healthStatus;
    } catch (error) {
      reply.code(503);
      return {
        status: 'unhealthy',
        service: 'agno-coordinator',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  });
  
  // Quick health check for load balancers
  app.get('/health/quick', async (request, reply) => {
    return { status: 'healthy', service: 'agno-coordinator' };
  });
  
  // Readiness probe for Kubernetes
  app.get('/health/ready', async (request, reply) => {
    const healthStatus = await HealthChecker.performComprehensiveCheck();
    
    // Check if core dependencies are ready
    const coreDeps = ['redis'];
    const ready = coreDeps.every(dep => 
      !healthStatus.dependencies[dep] || healthStatus.dependencies[dep].status === 'healthy'
    );
    
    if (!ready) {
      reply.code(503);
      return { status: 'not_ready', dependencies: healthStatus.dependencies };
    }
    
    return { status: 'ready', service: 'agno-coordinator' };
  });
  
  // Liveness probe for Kubernetes
  app.get('/health/live', async (request, reply) => {
    return { status: 'alive', service: 'agno-coordinator' };
  });
}
