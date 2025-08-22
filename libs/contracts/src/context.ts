import { z } from 'zod';
import { BaseResponseSchema, PaginationSchema } from './common';

// Context index entry
export const ContextEntrySchema = z.object({
  id: z.string().uuid(),
  type: z.enum(['document', 'conversation', 'code', 'research', 'meeting', 'task']),
  title: z.string(),
  content: z.string(),
  summary: z.string().optional(),
  metadata: z.record(z.any()).optional(),
  tags: z.array(z.string()).default([]),
  source: z.object({
    type: z.enum(['github', 'slack', 'notion', 'salesforce', 'manual', 'research']),
    url: z.string().url().optional(),
    reference_id: z.string().optional(),
  }),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  indexed_at: z.string().datetime(),
  embedding_model: z.string().optional(),
  embedding_dimensions: z.number().optional(),
});

// Context index request
export const ContextIndexRequestSchema = z.object({
  entries: z.array(ContextEntrySchema.omit({ 
    id: true, 
    created_at: true, 
    updated_at: true, 
    indexed_at: true 
  }).extend({
    id: z.string().uuid().optional(),
  })),
  batch_id: z.string().optional(),
  overwrite_existing: z.boolean().default(false),
});

// Context index response
export const ContextIndexResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  indexed_count: z.number().min(0),
  skipped_count: z.number().min(0),
  failed_count: z.number().min(0),
  batch_id: z.string().optional(),
  entries: z.array(z.object({
    id: z.string().uuid(),
    status: z.enum(['indexed', 'skipped', 'failed']),
    error: z.string().optional(),
  })),
});

// Context search request
export const ContextSearchRequestSchema = z.object({
  query: z.string().min(1).max(500),
  types: z.array(z.enum(['document', 'conversation', 'code', 'research', 'meeting', 'task'])).optional(),
  sources: z.array(z.enum(['github', 'slack', 'notion', 'salesforce', 'manual', 'research'])).optional(),
  tags: z.array(z.string()).optional(),
  limit: z.number().min(1).max(100).default(20),
  similarity_threshold: z.number().min(0).max(1).default(0.7),
  include_content: z.boolean().default(true),
  date_range: z.object({
    start: z.string().datetime().optional(),
    end: z.string().datetime().optional(),
  }).optional(),
});

// Context search result
export const ContextSearchResultSchema = z.object({
  entry: ContextEntrySchema,
  similarity_score: z.number().min(0).max(1),
  matched_snippets: z.array(z.string()).optional(),
});

// Context search response
export const ContextSearchResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  query: z.string(),
  results: z.array(ContextSearchResultSchema),
  total_results: z.number().min(0),
  search_time_ms: z.number().min(0),
  pagination: PaginationSchema.optional(),
});

// Context statistics
export const ContextStatsSchema = z.object({
  total_entries: z.number().min(0),
  entries_by_type: z.record(z.number().min(0)),
  entries_by_source: z.record(z.number().min(0)),
  last_indexed: z.string().datetime().optional(),
  index_size_mb: z.number().min(0),
  embedding_model: z.string().optional(),
});

// Context stats response
export const ContextStatsResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  stats: ContextStatsSchema,
});

// Context deletion request
export const ContextDeleteRequestSchema = z.object({
  ids: z.array(z.string().uuid()).optional(),
  filters: z.object({
    types: z.array(z.enum(['document', 'conversation', 'code', 'research', 'meeting', 'task'])).optional(),
    sources: z.array(z.enum(['github', 'slack', 'notion', 'salesforce', 'manual', 'research'])).optional(),
    tags: z.array(z.string()).optional(),
    before_date: z.string().datetime().optional(),
  }).optional(),
});

// Context deletion response
export const ContextDeleteResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  deleted_count: z.number().min(0),
});

// Export types
export type ContextEntry = z.infer<typeof ContextEntrySchema>;
export type ContextIndexRequest = z.infer<typeof ContextIndexRequestSchema>;
export type ContextIndexResponse = z.infer<typeof ContextIndexResponseSchema>;
export type ContextSearchRequest = z.infer<typeof ContextSearchRequestSchema>;
export type ContextSearchResult = z.infer<typeof ContextSearchResultSchema>;
export type ContextSearchResponse = z.infer<typeof ContextSearchResponseSchema>;
export type ContextStats = z.infer<typeof ContextStatsSchema>;
export type ContextStatsResponse = z.infer<typeof ContextStatsResponseSchema>;
export type ContextDeleteRequest = z.infer<typeof ContextDeleteRequestSchema>;
export type ContextDeleteResponse = z.infer<typeof ContextDeleteResponseSchema>;

