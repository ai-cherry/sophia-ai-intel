import { FeatureFlags } from './types';
export declare class FeatureFlagManager implements FeatureFlags {
    private flags;
    private defaultFlags;
    constructor();
    private initializeFlags;
    isEnabled(flag: string): boolean;
    setFlag(flag: string, enabled: boolean): void;
    getAllFlags(): Record<string, boolean>;
    getFlagsByCategory(category: string): Record<string, boolean>;
    enableFlags(flags: string[]): void;
    disableFlags(flags: string[]): void;
    resetToDefaults(): void;
    getModifiedFlags(): Record<string, boolean>;
    validateConfiguration(): {
        valid: boolean;
        issues: string[];
    };
    getConfigurationSummary(): {
        totalFlags: number;
        enabledFlags: number;
        disabledFlags: number;
        modifiedFlags: number;
        validation: {
            valid: boolean;
            issues: string[];
        };
    };
}
export declare const featureFlags: FeatureFlagManager;
//# sourceMappingURL=featureFlags.d.ts.map