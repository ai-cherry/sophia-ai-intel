import { HealthStatus } from '../config/types';
import { agnosticCoordinator } from '../coordinator/coordinator';
import { configManager } from '../config/config';
import { featureFlags } from '../config/featureFlags';

/**
 * Health check service for AGNO Coordinator
 */
export class HealthChecker {
  private lastHealthCheck = 0;
  private healthCache: HealthStatus | null = null;
  private readonly CACHE_DURATION = 30000; // 30 seconds

  /**
   * Get comprehensive health status
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const now = Date.now();

    // Return cached result if still valid
    if (this.healthCache && (now - this.lastHealthCheck) < this.CACHE_DURATION) {
      return this.healthCache;
    }

    const coordinatorHealth = agnosticCoordinator.getHealthStatus();
    const configValidation = configManager.validateConfig();
    const flagValidation = featureFlags.validateConfiguration();

    // Perform additional health checks
    const redisHealth = await this.checkRedisHealth();
    const memoryHealth = this.checkMemoryHealth();
    const overallHealth = this.determineOverallHealth({
      coordinatorHealth,
      configValidation,
      flagValidation,
      redisHealth,
      memoryHealth
    });

    const healthStatus: HealthStatus = {
      service: 'agno-coordinator',
      status: overallHealth.status,
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      checks: {
        redis: redisHealth.healthy,
        existingOrchestrator: coordinatorHealth.status === 'healthy',
        memory: memoryHealth.healthy,
        cpu: true // Placeholder - would check actual CPU usage
      },
      metrics: {
        activeRequests: coordinatorHealth.activeRequests,
        totalRequests: 0, // Would track in production
        averageResponseTime: 0, // Would track in production
        errorRate: 0 // Would track in production
      }
    };

    // Cache the result
    this.healthCache = healthStatus;
    this.lastHealthCheck = now;

    return healthStatus;
  }

  /**
   * Check Redis connectivity
   */
  private async checkRedisHealth(): Promise<{ healthy: boolean; error?: string }> {
    try {
      // This would check actual Redis connectivity
      // For now, return healthy since Redis check would be implemented
      return { healthy: true };
    } catch (error) {
      return {
        healthy: false,
        error: error instanceof Error ? error.message : 'Redis check failed'
      };
    }
  }

  /**
   * Check memory usage
   */
  private checkMemoryHealth(): { healthy: boolean; usage?: number } {
    try {
      // In Node.js, check memory usage
      const memUsage = process.memoryUsage();
      const usedMemoryMB = memUsage.heapUsed / 1024 / 1024;
      const totalMemoryMB = memUsage.heapTotal / 1024 / 1024;
      const usagePercentage = (usedMemoryMB / totalMemoryMB) * 100;

      // Consider unhealthy if using more than 90% of heap
      const healthy = usagePercentage < 90;

      return { healthy, usage: usagePercentage };
    } catch (error) {
      return { healthy: false };
    }
  }

  /**
   * Determine overall health status
   */
  private determineOverallHealth(checks: {
    coordinatorHealth: any;
    configValidation: any;
    flagValidation: any;
    redisHealth: any;
    memoryHealth: any;
  }): { status: 'healthy' | 'unhealthy' | 'degraded' } {
    const criticalFailures = [];
    const warnings = [];

    // Check critical components
    if (!checks.coordinatorHealth.initialized) {
      criticalFailures.push('Coordinator not initialized');
    }

    if (!checks.configValidation.valid) {
      criticalFailures.push('Configuration invalid');
    }

    if (!checks.redisHealth.healthy) {
      criticalFailures.push('Redis unhealthy');
    }

    if (!checks.memoryHealth.healthy) {
      warnings.push('High memory usage');
    }

    if (!checks.flagValidation.valid) {
      warnings.push('Feature flag configuration issues');
    }

    // Determine overall status
    if (criticalFailures.length > 0) {
      return { status: 'unhealthy' };
    } else if (warnings.length > 0) {
      return { status: 'degraded' };
    } else {
      return { status: 'healthy' };
    }
  }

  /**
   * Get detailed health report
   */
  async getDetailedHealthReport(): Promise<{
    status: HealthStatus;
    checks: Array<{
      name: string;
      status: 'healthy' | 'unhealthy' | 'degraded';
      message: string;
      details?: any;
    }>;
    recommendations: string[];
  }> {
    const status = await this.getHealthStatus();
    const checks = [];
    const recommendations = [];

    // Coordinator check
    const coordinatorHealth = agnosticCoordinator.getHealthStatus();
    checks.push({
      name: 'Coordinator Service',
      status: coordinatorHealth.status,
      message: coordinatorHealth.initialized ? 'Service initialized' : 'Service not initialized',
      details: {
        activeRequests: coordinatorHealth.activeRequests,
        configValid: coordinatorHealth.configValid
      }
    });

    if (!coordinatorHealth.initialized) {
      recommendations.push('Initialize the coordinator service');
    }

    // Configuration check
    const configValidation = configManager.validateConfig();
    checks.push({
      name: 'Configuration',
      status: (configValidation.valid ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'degraded',
      message: configValidation.valid ? 'Configuration valid' : 'Configuration invalid',
      details: configValidation.errors
    });

    if (!configValidation.valid) {
      recommendations.push('Fix configuration issues: ' + configValidation.errors.join(', '));
    }

    // Feature flags check
    const flagValidation = featureFlags.validateConfiguration();
    checks.push({
      name: 'Feature Flags',
      status: (flagValidation.valid ? 'healthy' : 'degraded') as 'healthy' | 'unhealthy' | 'degraded',
      message: flagValidation.valid ? 'Feature flags valid' : 'Feature flag issues detected',
      details: flagValidation.issues
    });

    if (!flagValidation.valid) {
      recommendations.push('Review feature flag configuration');
    }

    // Redis check
    const redisHealth = await this.checkRedisHealth();
    checks.push({
      name: 'Redis',
      status: (redisHealth.healthy ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'degraded',
      message: redisHealth.healthy ? 'Redis connected' : 'Redis connection failed',
      details: redisHealth.error
    });

    if (!redisHealth.healthy) {
      recommendations.push('Check Redis connectivity and configuration');
    }

    // Memory check
    const memoryHealth = this.checkMemoryHealth();
    checks.push({
      name: 'Memory Usage',
      status: (memoryHealth.healthy ? 'healthy' : 'degraded') as 'healthy' | 'unhealthy' | 'degraded',
      message: memoryHealth.healthy ? 'Memory usage normal' : 'High memory usage detected',
      details: { usage: memoryHealth.usage }
    });

    if (!memoryHealth.healthy) {
      recommendations.push('Monitor memory usage and consider scaling');
    }

    return {
      status,
      checks,
      recommendations
    };
  }

  /**
   * Clear health cache (useful for testing)
   */
  clearCache(): void {
    this.healthCache = null;
    this.lastHealthCheck = 0;
  }
}

// Global instance
export const healthChecker = new HealthChecker();