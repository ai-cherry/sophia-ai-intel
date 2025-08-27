import { CoordinatorConfig } from './types';
export declare class ConfigManager {
    private static instance;
    private config;
    private constructor();
    static getInstance(): ConfigManager;
    private loadConfiguration;
    getConfig(): CoordinatorConfig;
    updateConfig(updates: Partial<CoordinatorConfig>): void;
    validateConfig(): {
        valid: boolean;
        errors: string[];
    };
    getConfigSummary(): Record<string, any>;
    isFeatureEnabled(feature: keyof CoordinatorConfig): boolean;
    getServiceConfig(): CoordinatorConfig['services'];
    getRoutingConfig(): CoordinatorConfig['routing'];
    getFallbackConfig(): CoordinatorConfig['fallback'];
    getMonitoringConfig(): CoordinatorConfig['monitoring'];
}
export declare const configManager: ConfigManager;
//# sourceMappingURL=config.d.ts.map