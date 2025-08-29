/**
 * API Health Check Route - Real service health monitoring
 * NO MOCK DATA
 */

import { NextResponse } from 'next/server';

// Health check targets from environment or defaults
interface HealthTarget {
  name: string;
  url: string;
}

const HEALTH_TARGETS: HealthTarget[] = process.env.HEALTH_TARGETS ? 
  JSON.parse(process.env.HEALTH_TARGETS) : [
    { name: 'Swarm Orchestrator', url: 'http://localhost:8100/health' },
    { name: 'MCP Context', url: 'http://localhost:8081/health' },
    { name: 'MCP Research', url: 'http://localhost:8085/health' },
    { name: 'Vector Search', url: 'http://localhost:8086/health' }
  ];

async function checkHealth(url: string, timeout: number = 3000): Promise<{
  status: 'healthy' | 'unhealthy';
  latency: number;
  error?: string;
}> {
  const start = Date.now();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store'
    });
    
    clearTimeout(timeoutId);
    const latency = Date.now() - start;
    
    if (response.ok) {
      return { status: 'healthy', latency };
    } else {
      return { 
        status: 'unhealthy', 
        latency,
        error: `HTTP ${response.status}`
      };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      latency: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export async function GET() {
  try {
    // Check all services in parallel
    const healthChecks = await Promise.all(
      HEALTH_TARGETS.map(async (target) => {
        const result = await checkHealth(target.url);
        return {
          name: target.name,
          url: target.url,
          ...result
        };
      })
    );
    
    // Calculate aggregate health
    const healthy = healthChecks.filter(h => h.status === 'healthy').length;
    const total = healthChecks.length;
    const overallStatus = healthy === total ? 'healthy' : 
                          healthy > 0 ? 'degraded' : 'unhealthy';
    
    return NextResponse.json({
      status: overallStatus,
      timestamp: new Date().toISOString(),
      services: healthChecks,
      summary: {
        healthy,
        unhealthy: total - healthy,
        total
      }
    });
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      error: 'Failed to check health',
      message: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}
