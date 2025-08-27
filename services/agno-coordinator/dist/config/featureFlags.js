"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.featureFlags = exports.FeatureFlagManager = void 0;
class FeatureFlagManager {
    constructor() {
        this.flags = new Map();
        this.defaultFlags = {
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
        this.initializeFlags();
    }
    initializeFlags() {
        Object.entries(this.defaultFlags).forEach(([flag, defaultValue]) => {
            this.flags.set(flag, defaultValue);
        });
        Object.keys(this.defaultFlags).forEach(flagKey => {
            const envKey = `ENABLE_${flagKey.toUpperCase().replace(/-/g, '_')}`;
            const envValue = process.env[envKey];
            if (envValue !== undefined) {
                const enabled = envValue === 'true' || envValue === '1';
                this.flags.set(flagKey, enabled);
            }
        });
    }
    isEnabled(flag) {
        return this.flags.get(flag) || false;
    }
    setFlag(flag, enabled) {
        this.flags.set(flag, enabled);
        console.log(`Feature flag '${flag}' set to ${enabled}`);
    }
    getAllFlags() {
        const result = {};
        this.flags.forEach((value, key) => {
            result[key] = value;
        });
        return result;
    }
    getFlagsByCategory(category) {
        const result = {};
        const prefix = `${category}_`;
        this.flags.forEach((value, key) => {
            if (key.startsWith(prefix)) {
                result[key] = value;
            }
        });
        return result;
    }
    enableFlags(flags) {
        flags.forEach(flag => this.setFlag(flag, true));
    }
    disableFlags(flags) {
        flags.forEach(flag => this.setFlag(flag, false));
    }
    resetToDefaults() {
        this.flags.clear();
        this.initializeFlags();
    }
    getModifiedFlags() {
        const result = {};
        this.flags.forEach((value, key) => {
            const defaultValue = this.defaultFlags[key];
            if (defaultValue !== undefined && value !== defaultValue) {
                result[key] = value;
            }
        });
        return result;
    }
    validateConfiguration() {
        const issues = [];
        if (this.isEnabled('agno_routing') && !this.isEnabled('agno_fallback')) {
            issues.push("AGNO routing enabled but fallback disabled - this may cause service disruption");
        }
        if (this.isEnabled('agno_monitoring') && !this.isEnabled('agno_metrics')) {
            issues.push("Monitoring enabled but metrics disabled - monitoring will be incomplete");
        }
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
    getConfigurationSummary() {
        const totalFlags = this.flags.size;
        let enabledFlags = 0;
        this.flags.forEach(value => {
            if (value)
                enabledFlags++;
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
exports.FeatureFlagManager = FeatureFlagManager;
exports.featureFlags = new FeatureFlagManager();
//# sourceMappingURL=featureFlags.js.map