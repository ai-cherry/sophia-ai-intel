import { z } from 'zod';
import { BaseResponseSchema } from './common';

// GitHub repository reference
export const GitHubRepoRefSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  ref: z.string().default('main'),
});

// GitHub file request
export const GitHubFileRequestSchema = GitHubRepoRefSchema.extend({
  path: z.string(),
});

// GitHub file content
export const GitHubFileContentSchema = z.object({
  name: z.string(),
  path: z.string(),
  sha: z.string(),
  size: z.number(),
  url: z.string().url(),
  html_url: z.string().url(),
  git_url: z.string().url(),
  download_url: z.string().url().nullable(),
  type: z.literal('file'),
  content: z.string(),
  encoding: z.enum(['base64', 'utf-8']),
});

// GitHub file response
export const GitHubFileResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  file: GitHubFileContentSchema,
  repository: GitHubRepoRefSchema,
});

// GitHub directory tree request
export const GitHubTreeRequestSchema = GitHubRepoRefSchema.extend({
  path: z.string().default(''),
  recursive: z.boolean().default(false),
});

// GitHub tree item
export const GitHubTreeItemSchema = z.object({
  path: z.string(),
  mode: z.string(),
  type: z.enum(['blob', 'tree', 'commit']),
  sha: z.string(),
  size: z.number().optional(),
  url: z.string().url(),
});

// GitHub tree response
export const GitHubTreeResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  tree: z.array(GitHubTreeItemSchema),
  repository: GitHubRepoRefSchema,
  truncated: z.boolean(),
});

// GitHub repository info
export const GitHubRepositorySchema = z.object({
  id: z.number(),
  name: z.string(),
  full_name: z.string(),
  owner: z.object({
    login: z.string(),
    id: z.number(),
    type: z.enum(['User', 'Organization']),
  }),
  private: z.boolean(),
  html_url: z.string().url(),
  description: z.string().nullable(),
  fork: z.boolean(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  pushed_at: z.string().datetime(),
  size: z.number(),
  stargazers_count: z.number(),
  watchers_count: z.number(),
  language: z.string().nullable(),
  forks_count: z.number(),
  archived: z.boolean(),
  disabled: z.boolean(),
  open_issues_count: z.number(),
  license: z.object({
    key: z.string(),
    name: z.string(),
    spdx_id: z.string(),
  }).nullable(),
  default_branch: z.string(),
});

// GitHub repository response
export const GitHubRepositoryResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  repository: GitHubRepositorySchema,
});

// GitHub commit info
export const GitHubCommitSchema = z.object({
  sha: z.string(),
  commit: z.object({
    author: z.object({
      name: z.string(),
      email: z.string().email(),
      date: z.string().datetime(),
    }),
    committer: z.object({
      name: z.string(),
      email: z.string().email(),
      date: z.string().datetime(),
    }),
    message: z.string(),
  }),
  author: z.object({
    login: z.string(),
    id: z.number(),
  }).nullable(),
  committer: z.object({
    login: z.string(),
    id: z.number(),
  }).nullable(),
  html_url: z.string().url(),
});

// GitHub commits request
export const GitHubCommitsRequestSchema = GitHubRepoRefSchema.extend({
  path: z.string().optional(),
  since: z.string().datetime().optional(),
  until: z.string().datetime().optional(),
  per_page: z.number().min(1).max(100).default(30),
  page: z.number().min(1).default(1),
});

// GitHub commits response
export const GitHubCommitsResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  commits: z.array(GitHubCommitSchema),
  repository: GitHubRepoRefSchema,
  total_count: z.number().optional(),
});

// GitHub search request
export const GitHubSearchRequestSchema = z.object({
  query: z.string(),
  type: z.enum(['repositories', 'code', 'commits', 'issues', 'users']),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).default('desc'),
  per_page: z.number().min(1).max(100).default(30),
  page: z.number().min(1).default(1),
});

// GitHub search response
export const GitHubSearchResponseSchema = BaseResponseSchema.extend({
  status: z.literal('success'),
  total_count: z.number(),
  incomplete_results: z.boolean(),
  items: z.array(z.any()), // Type varies by search type
});

// GitHub webhook event
export const GitHubWebhookEventSchema = z.object({
  action: z.string(),
  repository: GitHubRepositorySchema.optional(),
  sender: z.object({
    login: z.string(),
    id: z.number(),
  }),
  installation: z.object({
    id: z.number(),
  }).optional(),
});

// Export types
export type GitHubRepoRef = z.infer<typeof GitHubRepoRefSchema>;
export type GitHubFileRequest = z.infer<typeof GitHubFileRequestSchema>;
export type GitHubFileContent = z.infer<typeof GitHubFileContentSchema>;
export type GitHubFileResponse = z.infer<typeof GitHubFileResponseSchema>;
export type GitHubTreeRequest = z.infer<typeof GitHubTreeRequestSchema>;
export type GitHubTreeItem = z.infer<typeof GitHubTreeItemSchema>;
export type GitHubTreeResponse = z.infer<typeof GitHubTreeResponseSchema>;
export type GitHubRepository = z.infer<typeof GitHubRepositorySchema>;
export type GitHubRepositoryResponse = z.infer<typeof GitHubRepositoryResponseSchema>;
export type GitHubCommit = z.infer<typeof GitHubCommitSchema>;
export type GitHubCommitsRequest = z.infer<typeof GitHubCommitsRequestSchema>;
export type GitHubCommitsResponse = z.infer<typeof GitHubCommitsResponseSchema>;
export type GitHubSearchRequest = z.infer<typeof GitHubSearchRequestSchema>;
export type GitHubSearchResponse = z.infer<typeof GitHubSearchResponseSchema>;
export type GitHubWebhookEvent = z.infer<typeof GitHubWebhookEventSchema>;

