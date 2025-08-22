import { z } from 'zod';

// Common response structure for all MCP services
export const BaseResponseSchema = z.object({
  status: z.enum(['success', 'failure']),
  timestamp: z.string().datetime(),
  execution_time_ms: z.number().min(0),
});

export const ErrorSchema = z.object({
  provider: z.string(),
  code: z.string(),
  message: z.string(),
});

export const SuccessResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
});

export const FailureResponseSchema = BaseResponseSchema.extend({
  status: z.literal('failure'),
  errors: z.array(ErrorSchema),
});

// Health check response
export const HealthCheckSchema = z.object({
  status: z.enum(['healthy', 'unhealthy']),
  service: z.string(),
  version: z.string(),
  timestamp: z.string().datetime(),
  uptime_ms: z.number().min(0),
  dependencies: z.record(z.enum(['healthy', 'unhealthy', 'unknown'])).optional(),
});

// Build information response
export const BuildInfoSchema = z.object({
  build_id: z.string(),
  git_commit: z.string(),
  git_branch: z.string(),
  build_timestamp: z.string().datetime(),
  version: z.string(),
  environment: z.enum(['development', 'staging', 'production']),
});

// Rate limiting
export const RateLimitSchema = z.object({
  limit: z.number(),
  remaining: z.number(),
  reset_at: z.string().datetime(),
});

// Pagination
export const PaginationSchema = z.object({
  page: z.number().min(1).default(1),
  limit: z.number().min(1).max(100).default(20),
  total: z.number().min(0),
  has_more: z.boolean(),
});

// Export types
export type BaseResponse = z.infer<typeof BaseResponseSchema>;
export type ErrorType = z.infer<typeof ErrorSchema>;
export type SuccessResponse = z.infer<typeof SuccessResponseSchema>;
export type FailureResponse = z.infer<typeof FailureResponseSchema>;
export type HealthCheck = z.infer<typeof HealthCheckSchema>;
export type BuildInfo = z.infer<typeof BuildInfoSchema>;
export type RateLimit = z.infer<typeof RateLimitSchema>;
export type Pagination = z.infer<typeof PaginationSchema>;

