import { z } from 'zod';
import { BaseResponseSchema, PaginationSchema } from './common';

// Research query schema
export const ResearchQuerySchema = z.object({
  query: z.string().min(1).max(500),
  sources: z.array(z.enum(['tavily', 'serper', 'exa', 'perplexity'])).default(['tavily', 'serper']),
  max_results: z.number().min(1).max(50).default(10),
  include_images: z.boolean().default(false),
  include_raw_content: z.boolean().default(false),
  date_range: z.enum(['any', 'day', 'week', 'month', 'year']).default('any'),
  language: z.string().length(2).default('en'),
  region: z.string().length(2).optional(),
});

// Research result item
export const ResearchResultSchema = z.object({
  title: z.string(),
  url: z.string().url(),
  snippet: z.string(),
  content: z.string().optional(),
  published_date: z.string().datetime().optional(),
  source: z.enum(['tavily', 'serper', 'exa', 'perplexity']),
  score: z.number().min(0).max(1),
  images: z.array(z.object({
    url: z.string().url(),
    alt: z.string().optional(),
    width: z.number().optional(),
    height: z.number().optional(),
  })).optional(),
});

// Research summary
export const ResearchSummarySchema = z.object({
  text: z.string(),
  confidence: z.number().min(0).max(1),
  model: z.string(),
  sources: z.array(z.string().url()),
  key_points: z.array(z.string()).optional(),
  related_queries: z.array(z.string()).optional(),
});

// Research response
export const ResearchResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  query: z.string(),
  results: z.array(ResearchResultSchema),
  summary: ResearchSummarySchema,
  pagination: PaginationSchema.optional(),
});

// Research failure response
export const ResearchFailureResponseSchema = BaseResponseSchema.extend({
  status: z.literal('failure'),
  query: z.string(),
  results: z.array(z.never()).default([]),
  summary: ResearchSummarySchema.partial().extend({
    text: z.string().default(''),
    confidence: z.literal(0),
    model: z.string().default('n/a'),
    sources: z.array(z.string()).default([]),
  }),
  errors: z.array(z.object({
    provider: z.string(),
    code: z.string(),
    message: z.string(),
  })),
});

// Scraping request (for deep content extraction)
export const ScrapingRequestSchema = z.object({
  url: z.string().url(),
  extract_content: z.boolean().default(true),
  extract_images: z.boolean().default(false),
  extract_links: z.boolean().default(false),
  wait_for: z.string().optional(), // CSS selector to wait for
  timeout_ms: z.number().min(1000).max(30000).default(10000),
});

// Scraping response
export const ScrapingResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  url: z.string().url(),
  title: z.string().optional(),
  content: z.string().optional(),
  images: z.array(z.object({
    url: z.string().url(),
    alt: z.string().optional(),
  })).optional(),
  links: z.array(z.object({
    url: z.string().url(),
    text: z.string(),
  })).optional(),
  metadata: z.object({
    description: z.string().optional(),
    keywords: z.array(z.string()).optional(),
    author: z.string().optional(),
    published_date: z.string().datetime().optional(),
  }).optional(),
});

// Export types
export type ResearchQuery = z.infer<typeof ResearchQuerySchema>;
export type ResearchResult = z.infer<typeof ResearchResultSchema>;
export type ResearchSummary = z.infer<typeof ResearchSummarySchema>;
export type ResearchResponse = z.infer<typeof ResearchResponseSchema>;
export type ResearchFailureResponse = z.infer<typeof ResearchFailureResponseSchema>;
export type ScrapingRequest = z.infer<typeof ScrapingRequestSchema>;
export type ScrapingResponse = z.infer<typeof ScrapingResponseSchema>;

