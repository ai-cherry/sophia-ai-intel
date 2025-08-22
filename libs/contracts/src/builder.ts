import { z } from 'zod';
import { BaseResponseSchema } from './common';

// Builder task types
export const BuilderTaskTypeSchema = z.enum([
  'feature_development',
  'bug_fix',
  'refactoring',
  'documentation',
  'deployment',
  'testing',
  'security_update',
]);

// Builder PR request
export const BuilderPRRequestSchema = z.object({
  task: z.string().min(1).max(200),
  summary: z.string().min(1).max(1000),
  type: BuilderTaskTypeSchema,
  paths: z.array(z.string()).optional(),
  branch_name: z.string().optional(),
  assignees: z.array(z.string()).optional(),
  labels: z.array(z.string()).optional(),
  priority: z.enum(['low', 'medium', 'high', 'critical']).default('medium'),
  estimated_effort: z.enum(['xs', 's', 'm', 'l', 'xl']).optional(),
});

// Builder PR response
export const BuilderPRResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  pr_number: z.number(),
  pr_url: z.string().url(),
  branch_name: z.string(),
  commit_sha: z.string(),
  files_changed: z.array(z.string()),
  staging_url: z.string().url().optional(),
  proofs: z.array(z.object({
    type: z.enum(['screenshot', 'healthcheck', 'build_info', 'test_results']),
    url: z.string().url(),
    description: z.string(),
  })),
});

// Builder deployment request
export const BuilderDeployRequestSchema = z.object({
  environment: z.enum(['staging', 'production']),
  pr_number: z.number().optional(),
  commit_sha: z.string().optional(),
  services: z.array(z.string()).optional(), // Specific services to deploy
  rollback_on_failure: z.boolean().default(true),
  run_smoke_tests: z.boolean().default(true),
});

// Builder deployment response
export const BuilderDeployResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  deployment_id: z.string(),
  environment: z.enum(['staging', 'production']),
  deployed_services: z.array(z.object({
    name: z.string(),
    url: z.string().url(),
    version: z.string(),
    health_status: z.enum(['healthy', 'unhealthy', 'unknown']),
  })),
  smoke_test_results: z.array(z.object({
    test_name: z.string(),
    status: z.enum(['passed', 'failed', 'skipped']),
    duration_ms: z.number(),
    error: z.string().optional(),
  })).optional(),
});

// Builder status request
export const BuilderStatusRequestSchema = z.object({
  pr_number: z.number().optional(),
  deployment_id: z.string().optional(),
  include_logs: z.boolean().default(false),
});

// Builder status response
export const BuilderStatusResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  build_status: z.enum(['pending', 'running', 'success', 'failure', 'cancelled']),
  deployment_status: z.enum(['pending', 'running', 'success', 'failure', 'cancelled']).optional(),
  current_step: z.string().optional(),
  progress_percentage: z.number().min(0).max(100).optional(),
  logs: z.array(z.object({
    timestamp: z.string().datetime(),
    level: z.enum(['debug', 'info', 'warn', 'error']),
    message: z.string(),
    service: z.string().optional(),
  })).optional(),
});

// Builder rollback request
export const BuilderRollbackRequestSchema = z.object({
  environment: z.enum(['staging', 'production']),
  target_version: z.string().optional(), // If not provided, rollback to previous
  services: z.array(z.string()).optional(),
  reason: z.string(),
});

// Builder rollback response
export const BuilderRollbackResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  rollback_id: z.string(),
  environment: z.enum(['staging', 'production']),
  rolled_back_services: z.array(z.object({
    name: z.string(),
    from_version: z.string(),
    to_version: z.string(),
    url: z.string().url(),
  })),
});

// Builder workflow configuration
export const BuilderWorkflowConfigSchema = z.object({
  auto_deploy_staging: z.boolean().default(true),
  require_approval_production: z.boolean().default(true),
  run_security_scan: z.boolean().default(true),
  run_performance_tests: z.boolean().default(false),
  notification_channels: z.array(z.object({
    type: z.enum(['slack', 'email', 'webhook']),
    target: z.string(),
    events: z.array(z.enum(['pr_created', 'deployment_success', 'deployment_failure', 'rollback'])),
  })).default([]),
});

// Export types
export type BuilderTaskType = z.infer<typeof BuilderTaskTypeSchema>;
export type BuilderPRRequest = z.infer<typeof BuilderPRRequestSchema>;
export type BuilderPRResponse = z.infer<typeof BuilderPRResponseSchema>;
export type BuilderDeployRequest = z.infer<typeof BuilderDeployRequestSchema>;
export type BuilderDeployResponse = z.infer<typeof BuilderDeployResponseSchema>;
export type BuilderStatusRequest = z.infer<typeof BuilderStatusRequestSchema>;
export type BuilderStatusResponse = z.infer<typeof BuilderStatusResponseSchema>;
export type BuilderRollbackRequest = z.infer<typeof BuilderRollbackRequestSchema>;
export type BuilderRollbackResponse = z.infer<typeof BuilderRollbackResponseSchema>;
export type BuilderWorkflowConfig = z.infer<typeof BuilderWorkflowConfigSchema>;

