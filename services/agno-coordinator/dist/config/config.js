"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.configManager = exports.ConfigManager = void 0;
class ConfigManager {
    constructor() {
        this.config = this.loadConfiguration();
    }
    static getInstance() {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }
    loadConfiguration() {
        return {
            routing: {
                enabled: process.env.ENABLE_AGNO_ROUTING === 'true',
                complexityThreshold: parseInt(process.env.AGNO_COMPLEXITY_THRESHOLD || '10', 10),
                confidenceThreshold: parseFloat(process.env.AGNO_CONFIDENCE_THRESHOLD || '0.8')
            },
            fallback: {
                enabled: process.env.ENABLE_AGNO_FALLBACK !== 'false',
                timeoutMs: parseInt(process.env.AGNO_FALLBACK_TIMEOUT || '30000', 10),
                retryAttempts: parseInt(process.env.AGNO_RETRY_ATTEMPTS || '2', 10)
            },
            monitoring: {
                enabled: process.env.ENABLE_AGNO_MONITORING !== 'false',
                metricsInterval: parseInt(process.env.AGNO_METRICS_INTERVAL || '60000', 10)
            },
            services: {
                existingOrchestratorUrl: process.env.EXISTING_ORCHESTRATOR_URL || 'http://sophia-orchestrator:3000',
                redisUrl: process.env.REDIS_URL || 'redis://redis:6379',
                maxRetries: parseInt(process.env.MAX_RETRIES || '3', 10),
                requestTimeout: parseInt(process.env.REQUEST_TIMEOUT || '30000', 10)
            }
        };
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
    }
    validateConfig() {
        const errors = [];
        if (this.config.routing.complexityThreshold < 1) {
            errors.push('Complexity threshold must be at least 1');
        }
        if (this.config.routing.confidenceThreshold < 0 || this.config.routing.confidenceThreshold > 1) {
            errors.push('Confidence threshold must be between 0 and 1');
        }
        if (this.config.fallback.timeoutMs < 1000) {
            errors.push('Fallback timeout must be at least 1000ms');
        }
        if (this.config.fallback.retryAttempts < 0) {
            errors.push('Retry attempts cannot be negative');
        }
        if (!this.config.services.existingOrchestratorUrl) {
            errors.push('Existing orchestrator URL is required');
        }
        if (!this.config.services.redisUrl) {
            errors.push('Redis URL is required');
        }
        if (this.config.services.maxRetries < 0) {
            errors.push('Max retries cannot be negative');
        }
        if (this.config.services.requestTimeout < 1000) {
            errors.push('Request timeout must be at least 1000ms');
        }
        return {
            valid: errors.length === 0,
            errors
        };
    }
    getConfigSummary() {
        return {
            routing: {
                enabled: this.config.routing.enabled,
                complexityThreshold: this.config.routing.complexityThreshold,
                confidenceThreshold: this.config.routing.confidenceThreshold
            },
            fallback: {
                enabled: this.config.fallback.enabled,
                timeoutMs: this.config.fallback.timeoutMs,
                retryAttempts: this.config.fallback.retryAttempts
            },
            monitoring: {
                enabled: this.config.monitoring.enabled,
                metricsInterval: this.config.monitoring.metricsInterval
            },
            services: {
                existingOrchestratorUrl: this.config.services.existingOrchestratorUrl,
                redisUrl: this.config.services.redisUrl ? '[CONFIGURED]' : '[NOT SET]',
                maxRetries: this.config.services.maxRetries,
                requestTimeout: this.config.services.requestTimeout
            }
        };
    }
    isFeatureEnabled(feature) {
        switch (feature) {
            case 'routing':
                return this.config.routing.enabled;
            case 'fallback':
                return this.config.fallback.enabled;
            case 'monitoring':
                return this.config.monitoring.enabled;
            default:
                return false;
        }
    }
    getServiceConfig() {
        return { ...this.config.services };
    }
    getRoutingConfig() {
        return { ...this.config.routing };
    }
    getFallbackConfig() {
        return { ...this.config.fallback };
    }
    getMonitoringConfig() {
        return { ...this.config.monitoring };
    }
}
exports.ConfigManager = ConfigManager;
exports.configManager = ConfigManager.getInstance();
//# sourceMappingURL=config.js.map