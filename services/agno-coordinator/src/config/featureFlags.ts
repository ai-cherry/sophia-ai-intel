import { FeatureFlags } from './types';

/**
 * Feature Flag System for AGNO Coordinator
 * Manages gradual rollout and A/B testing capabilities
 */
export class FeatureFlagManager implements FeatureFlags {
  private flags: Map<string, boolean> = new Map();
  private defaultFlags: Record<string, boolean> = {
    'agno_routing': false,
    'agno_logging': true,
    'agno_monitoring': true,
    'agno_fallback': true,
    'agno_circuit_breaker': true,
    'agno_metrics': true,
    'agno_health_checks': true,
    'agno_complexity_analysis': false,
    'agno_performance_tracking': true,
    'agno_error_reporting': true
  };

  constructor() {
    this.initializeFlags();
  }

  /**
   * Initialize feature flags from environment variables and defaults
   */
  private initializeFlags(): void {
    // Set default flags
    Object.entries(this.defaultFlags).forEach(([flag, defaultValue]) => {
      this.flags.set(flag, defaultValue);
    });

    // Override with environment variables
    Object.keys(this.defaultFlags).forEach(flagKey => {
      const envKey = `ENABLE_${flagKey.toUpperCase().replace(/-/g, '_')}`;
      const envValue = process.env[envKey];

      if (envValue !== undefined) {
        const enabled = envValue === 'true' || envValue === '1';
        this.flags.set(flagKey, enabled);
      }
    });
  }

  /**
   * Check if a feature flag is enabled
   */
  isEnabled(flag: string): boolean {
    return this.flags.get(flag) || false;
  }

  /**
   * Set a feature flag value
   */
  setFlag(flag: string, enabled: boolean): void {
    this.flags.set(flag, enabled);

    // In a real implementation, this would persist to a database
    // or configuration service for distributed systems
    console.log(`Feature flag '${flag}' set to ${enabled}`);
  }

  /**
   * Get all feature flags
   */
  getAllFlags(): Record<string, boolean> {
    const result: Record<string, boolean> = {};
    this.flags.forEach((value, key) => {
      result[key] = value;
    });
    return result;
  }

  /**
   * Get feature flags for a specific category
   */
  getFlagsByCategory(category: string): Record<string, boolean> {
    const result: Record<string, boolean> = {};
    const prefix = `${category}_`;

    this.flags.forEach((value, key) => {
      if (key.startsWith(prefix)) {
        result[key] = value;
      }
    });

    return result;
  }

  /**
   * Enable multiple flags at once
   */
  enableFlags(flags: string[]): void {
    flags.forEach(flag => this.setFlag(flag, true));
  }

  /**
   * Disable multiple flags at once
   */
  disableFlags(flags: string[]): void {
    flags.forEach(flag => this.setFlag(flag, false));
  }

  /**
   * Reset flags to default values
   */
  resetToDefaults(): void {
    this.flags.clear();
    this.initializeFlags();
  }

  /**
   * Get flags that are different from defaults
   */
  getModifiedFlags(): Record<string, boolean> {
    const result: Record<string, boolean> = {};

    this.flags.forEach((value, key) => {
      const defaultValue = this.defaultFlags[key];
      if (defaultValue !== undefined && value !== defaultValue) {
        result[key] = value;
      }
    });

    return result;
  }

  /**
   * Validate that required flags are properly configured
   */
  validateConfiguration(): { valid: boolean; issues: string[] } {
    const issues: string[] = [];

    // Check for conflicting configurations
    if (this.isEnabled('agno_routing') && !this.isEnabled('agno_fallback')) {
      issues.push("AGNO routing enabled but fallback disabled - this may cause service disruption");
    }

    if (this.isEnabled('agno_monitoring') && !this.isEnabled('agno_metrics')) {
      issues.push("Monitoring enabled but metrics disabled - monitoring will be incomplete");
    }

    // Check for required flags
    const requiredFlags = ['agno_health_checks'];
    requiredFlags.forEach(flag => {
      if (!this.isEnabled(flag)) {
        issues.push(`Required flag '${flag}' is disabled`);
      }
    });

    return {
      valid: issues.length === 0,
      issues
    };
  }

  /**
   * Get configuration summary for logging/debugging
   */
  getConfigurationSummary(): {
    totalFlags: number;
    enabledFlags: number;
    disabledFlags: number;
    modifiedFlags: number;
    validation: { valid: boolean; issues: string[] };
  } {
    const totalFlags = this.flags.size;
    let enabledFlags = 0;
    this.flags.forEach(value => {
      if (value) enabledFlags++;
    });

    const modifiedFlags = Object.keys(this.getModifiedFlags()).length;
    const validation = this.validateConfiguration();

    return {
      totalFlags,
      enabledFlags,
      disabledFlags: totalFlags - enabledFlags,
      modifiedFlags,
      validation
    };
  }
}

// Global instance
export const featureFlags = new FeatureFlagManager();