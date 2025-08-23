/**
 * Retrieval Router - Unified retrieval from Neon/Qdrant/Redis with compression
 * ===========================================================================
 * 
 * Orchestrates retrieval across multiple data sources with intelligent routing,
 * result merging, compression, temporal filtering, and payload optimization.
 */

import { safeExecutor, ExecutionContext } from '../execution/safeExecutor'
import { validateToolInput } from '../validation/toolSchemas'

/** Retrieval source configuration */
export interface RetrievalSource {
  name: string
  type: 'neon' | 'qdrant' | 'redis' | 'memory'
  endpoint: string
  priority: number
  timeout: number
  maxResults: number
  enabled: boolean
  metadata?: Record<string, any>
}

/** Enhanced retrieval query parameters */
export interface RetrievalQuery {
  query: string
  limit?: number
  offset?: number
  filters?: Record<string, any>
  temporalHints?: {
    timeRange?: { start: Date; end: Date }
    recency?: 'recent' | 'archive' | 'all'
    priority?: 'fresh' | 'comprehensive' | 'balanced'
    temporalWeight?: number // How much to weight recency (0.0 to 1.0)
  }
  compressionLevel?: 'none' | 'light' | 'aggressive' | 'adaptive'
  includeMetadata?: boolean
  sources?: string[] // Specific sources to query
  tenant?: string
  visibility?: 'public' | 'private' | 'team'
  
  // Enhanced filtering capabilities
  qualityThreshold?: number // Minimum quality score (0.0 to 1.0)
  accessLevel?: 'public' | 'tenant' | 'private'
  contentTypes?: string[] // Filter by content types
  
  // Payload filtering options
  payloadFiltering?: {
    includeMetadata?: boolean
    metadataFilter?: string[] // Specific metadata fields to include
    contentSummary?: boolean // Include content summaries
    relationshipDepth?: number // How deep to fetch relationships
  }
  
  // Conversation context for adaptive responses
  conversationContext?: {
    sessionId: string
    previousQueries: string[]
    userPreferences: Record<string, any>
    conversationIntent?: string
  }
}

/** Enhanced retrieval query interface */
export interface EnhancedRetrievalQuery extends RetrievalQuery {
  // Additional enhanced features
  semanticRouting?: boolean // Use semantic analysis for source selection
  qualityBoost?: number // Boost factor for high-quality content
  diversityMode?: 'focused' | 'diverse' | 'balanced' // Result diversity strategy
}

/** Individual retrieval result */
export interface RetrievalResult {
  id: string
  content: string
  source: string
  relevanceScore: number
  timestamp: Date
  metadata: Record<string, any>
  compressed?: boolean
  originalSize?: number
  compressedSize?: number
}

/** Aggregated retrieval response */
export interface RetrievalResponse {
  results: RetrievalResult[]
  totalResults: number
  sources: Record<string, {
    count: number
    avgRelevance: number
    errors: string[]
  }>
  executionTimeMs: number
  compressionStats?: {
    originalSize: number
    compressedSize: number
    compressionRatio: number
  }
  metadata: {
    query: string
    queryId: string
    cached: boolean
    mergeStrategy: string
  }
}

/** Source-specific query configuration */
interface SourceQuery {
  source: RetrievalSource
  query: string
  params: Record<string, any>
}

/** Cache entry for retrieval results */
interface CacheEntry {
  response: RetrievalResponse
  timestamp: Date
  ttl: number
  queryHash: string
}

/** Enhanced compression utilities with adaptive compression */
class CompressionUtils {
  /**
   * Compress content based on level setting
   */
  static compress(content: string, level: 'none' | 'light' | 'aggressive' | 'adaptive', userPreferences?: Record<string, any>): {
    compressed: string
    originalSize: number
    compressedSize: number
    compressionLevel: string
  } {
    const originalSize = content.length

    switch (level) {
      case 'none':
        return {
          compressed: content,
          originalSize,
          compressedSize: originalSize,
          compressionLevel: 'none'
        }

      case 'light':
        // Remove extra whitespace and normalize
        const lightCompressed = content
          .replace(/\s+/g, ' ')
          .replace(/\n\s*\n/g, '\n')
          .trim()
        
        return {
          compressed: lightCompressed,
          originalSize,
          compressedSize: lightCompressed.length,
          compressionLevel: 'light'
        }

      case 'aggressive':
        // More aggressive compression: remove redundant phrases, etc.
        const aggressiveCompressed = content
          .replace(/\s+/g, ' ')
          .replace(/\b(the|a|an|and|or|but|in|on|at|to|for|of|with|by)\b\s*/gi, '')
          .replace(/[.,;:!?]+/g, '.')
          .replace(/\.+/g, '.')
          .trim()

        return {
          compressed: aggressiveCompressed,
          originalSize,
          compressedSize: aggressiveCompressed.length,
          compressionLevel: 'aggressive'
        }

      case 'adaptive':
        // Determine optimal compression based on content size and user preferences
        const verbosityPreference = userPreferences?.verbosity || 0.7
        let adaptiveLevel: 'none' | 'light' | 'aggressive'
        
        if (originalSize < 500) {
          adaptiveLevel = 'none'
        } else if (originalSize < 2000 && verbosityPreference > 0.8) {
          adaptiveLevel = 'light'
        } else if (verbosityPreference < 0.4 || originalSize > 5000) {
          adaptiveLevel = 'aggressive'
        } else {
          adaptiveLevel = 'light'
        }
        
        // Recursively call with determined level
        const adaptiveResult = this.compress(content, adaptiveLevel, userPreferences)
        return {
          ...adaptiveResult,
          compressionLevel: `adaptive(${adaptiveLevel})`
        }

      default:
        return {
          compressed: content,
          originalSize,
          compressedSize: originalSize,
          compressionLevel: 'none'
        }
    }
  }

  /**
   * Calculate optimal compression level based on content size
   */
  static getOptimalCompressionLevel(contentSize: number, targetRatio: number = 0.7): 'none' | 'light' | 'aggressive' {
    if (contentSize < 1000) return 'none'
    if (contentSize < 5000) return 'light'
    return 'aggressive'
  }
}

export class RetrievalRouter {
  private sources: Map<string, RetrievalSource> = new Map()
  private cache: Map<string, CacheEntry> = new Map()
  private stats = {
    totalQueries: 0,
    cacheHits: 0,
    sourceCalls: 0,
    averageLatency: 0,
    compressionSavings: 0
  }

  constructor() {
    this.initializeDefaultSources()
    this.startCacheCleanup()
  }

  /**
   * Initialize default retrieval sources
   */
  private initializeDefaultSources(): void {
    // Neon PostgreSQL for structured data
    this.registerSource({
      name: 'neon-primary',
      type: 'neon',
      endpoint: (globalThis as any).process?.env?.NEON_DATABASE_URL || 'postgresql://localhost:5432/sophia',
      priority: 1,
      timeout: 5000,
      maxResults: 100,
      enabled: true,
      metadata: { description: 'Primary structured data store' }
    })

    // Qdrant for vector similarity search
    this.registerSource({
      name: 'qdrant-vectors',
      type: 'qdrant',
      endpoint: (globalThis as any).process?.env?.QDRANT_URL || 'http://localhost:6333',
      priority: 2,
      timeout: 3000,
      maxResults: 50,
      enabled: true,
      metadata: { description: 'Vector similarity search' }
    })

    // Redis for fast cached lookups
    this.registerSource({
      name: 'redis-cache',
      type: 'redis',
      endpoint: (globalThis as any).process?.env?.REDIS_URL || 'redis://localhost:6379',
      priority: 3,
      timeout: 1000,
      maxResults: 20,
      enabled: true,
      metadata: { description: 'Fast cached data' }
    })

    // In-memory for session data
    this.registerSource({
      name: 'memory-session',
      type: 'memory',
      endpoint: 'internal://memory',
      priority: 4,
      timeout: 100,
      maxResults: 10,
      enabled: true,
      metadata: { description: 'Session-specific data' }
    })
  }

  /**
   * Register a new retrieval source
   */
  registerSource(source: RetrievalSource): void {
    this.sources.set(source.name, source)
  }

  /**
   * Main retrieval function - coordinates across all sources
   */
  async retrieve(query: RetrievalQuery, context?: ExecutionContext): Promise<RetrievalResponse> {
    const startTime = Date.now()
    const queryId = this.generateQueryId(query)

    this.stats.totalQueries++

    // Check cache first
    const cached = this.checkCache(query)
    if (cached) {
      this.stats.cacheHits++
      return {
        ...cached,
        metadata: {
          ...cached.metadata,
          cached: true,
          queryId
        }
      }
    }

    // Determine which sources to query
    const activeSources = this.selectSources(query)
    
    // Prepare source-specific queries
    const sourceQueries = this.prepareSourceQueries(query, activeSources)

    // Execute queries in parallel with safe execution
    const sourceResults = await Promise.allSettled(
      sourceQueries.map(sq => this.executeSourceQuery(sq, context))
    )

    // Process and merge results
    const mergedResults = await this.mergeResults(sourceResults, query)

    // Apply compression if requested with user preferences
    const compressedResults = this.applyCompression(
      mergedResults.results,
      query.compressionLevel || 'none',
      query.conversationContext?.userPreferences
    )

    // Calculate compression stats
    const compressionStats = this.calculateCompressionStats(mergedResults.results, compressedResults)

    const response: RetrievalResponse = {
      results: compressedResults,
      totalResults: compressedResults.length,
      sources: mergedResults.sourcesStats,
      executionTimeMs: Date.now() - startTime,
      compressionStats,
      metadata: {
        query: query.query,
        queryId,
        cached: false,
        mergeStrategy: 'relevance-weighted'
      }
    }

    // Cache the response
    this.cacheResponse(query, response)

    // Update stats
    this.updateStats(response)

    return response
  }

  /**
   * Select which sources to query based on query parameters
   */
  private selectSources(query: RetrievalQuery): RetrievalSource[] {
    let sources = Array.from(this.sources.values())
      .filter(s => s.enabled)
      .sort((a, b) => a.priority - b.priority)

    // Filter by explicitly requested sources
    if (query.sources && query.sources.length > 0) {
      sources = sources.filter(s => query.sources!.includes(s.name))
    }

    // Apply temporal hints for source selection
    if (query.temporalHints) {
      sources = this.applyTemporalSourceSelection(sources, query.temporalHints)
    }

    return sources
  }

  /**
   * Apply temporal hints to source selection
   */
  private applyTemporalSourceSelection(
    sources: RetrievalSource[],
    hints: NonNullable<RetrievalQuery['temporalHints']>
  ): RetrievalSource[] {
    if (hints.priority === 'fresh') {
      // Prioritize Redis cache and memory for fresh data
      return sources.filter(s => ['redis', 'memory'].includes(s.type))
    }

    if (hints.priority === 'comprehensive') {
      // Use all sources for comprehensive search
      return sources
    }

    if (hints.recency === 'recent') {
      // Favor faster sources for recent data
      return sources.slice(0, 2)
    }

    return sources
  }

  /**
   * Prepare source-specific query parameters
   */
  private prepareSourceQueries(query: RetrievalQuery, sources: RetrievalSource[]): SourceQuery[] {
    return sources.map(source => {
      const params = this.buildSourceParams(query, source)
      return {
        source,
        query: query.query,
        params
      }
    })
  }

  /**
   * Build source-specific parameters
   */
  private buildSourceParams(query: RetrievalQuery, source: RetrievalSource): Record<string, any> {
    const baseParams = {
      limit: Math.min(query.limit || 20, source.maxResults),
      offset: query.offset || 0
    }

    switch (source.type) {
      case 'neon':
        return {
          ...baseParams,
          filters: query.filters,
          tenant: query.tenant,
          visibility: query.visibility,
          timeRange: query.temporalHints?.timeRange
        }

      case 'qdrant':
        return {
          ...baseParams,
          vector_search: true,
          score_threshold: 0.7,
          with_payload: query.includeMetadata !== false
        }

      case 'redis':
        return {
          ...baseParams,
          pattern_match: true,
          ttl_filter: query.temporalHints?.recency === 'recent'
        }

      case 'memory':
        return {
          ...baseParams,
          session_only: true
        }

      default:
        return baseParams
    }
  }

  /**
   * Execute query against a specific source
   */
  private async executeSourceQuery(
    sourceQuery: SourceQuery,
    context?: ExecutionContext
  ): Promise<RetrievalResult[]> {
    const { source, query, params } = sourceQuery

    this.stats.sourceCalls++

    // Use safe executor for resilient execution
    const executionContext: ExecutionContext = {
      sessionId: context?.sessionId || 'retrieval',
      toolName: `retrieval-${source.name}`,
      timeout: source.timeout,
      ...context
    }

    const result = await safeExecutor.execute(
      async (input) => {
        return this.callSource(source, input.query, input.params)
      },
      { query, params },
      executionContext
    )

    if (!result.success) {
      console.warn(`Source ${source.name} failed:`, result.error?.message)
      return []
    }

    return result.result || []
  }

  /**
   * Make actual API call to a source
   */
  private async callSource(
    source: RetrievalSource,
    query: string,
    params: Record<string, any>
  ): Promise<RetrievalResult[]> {
    switch (source.type) {
      case 'neon':
        return this.queryNeon(source, query, params)
      case 'qdrant':
        return this.queryQdrant(source, query, params)
      case 'redis':
        return this.queryRedis(source, query, params)
      case 'memory':
        return this.queryMemory(source, query, params)
      default:
        throw new Error(`Unsupported source type: ${source.type}`)
    }
  }

  /**
   * Query Neon PostgreSQL
   */
  private async queryNeon(
    source: RetrievalSource,
    query: string,
    params: Record<string, any>
  ): Promise<RetrievalResult[]> {
    // This would integrate with actual Neon client
    // For now, return mock data
    return [{
      id: `neon-${Date.now()}`,
      content: `Neon result for: ${query}`,
      source: source.name,
      relevanceScore: 0.8,
      timestamp: new Date(),
      metadata: { source_type: 'neon', ...params }
    }]
  }

  /**
   * Query Qdrant vector database
   */
  private async queryQdrant(
    source: RetrievalSource,
    query: string,
    params: Record<string, any>
  ): Promise<RetrievalResult[]> {
    // This would integrate with actual Qdrant client
    // For now, return mock data
    return [{
      id: `qdrant-${Date.now()}`,
      content: `Qdrant vector result for: ${query}`,
      source: source.name,
      relevanceScore: 0.9,
      timestamp: new Date(),
      metadata: { source_type: 'qdrant', ...params }
    }]
  }

  /**
   * Query Redis cache
   */
  private async queryRedis(
    source: RetrievalSource,
    query: string,
    params: Record<string, any>
  ): Promise<RetrievalResult[]> {
    // This would integrate with actual Redis client
    // For now, return mock data
    return [{
      id: `redis-${Date.now()}`,
      content: `Redis cached result for: ${query}`,
      source: source.name,
      relevanceScore: 0.7,
      timestamp: new Date(),
      metadata: { source_type: 'redis', ...params }
    }]
  }

  /**
   * Query in-memory data
   */
  private async queryMemory(
    source: RetrievalSource,
    query: string,
    params: Record<string, any>
  ): Promise<RetrievalResult[]> {
    // This would query in-memory session data
    return [{
      id: `memory-${Date.now()}`,
      content: `Memory result for: ${query}`,
      source: source.name,
      relevanceScore: 0.6,
      timestamp: new Date(),
      metadata: { source_type: 'memory', ...params }
    }]
  }

  /**
   * Merge results from multiple sources
   */
  private async mergeResults(
    sourceResults: PromiseSettledResult<RetrievalResult[]>[],
    query: RetrievalQuery
  ): Promise<{
    results: RetrievalResult[]
    sourcesStats: Record<string, { count: number; avgRelevance: number; errors: string[] }>
  }> {
    const allResults: RetrievalResult[] = []
    const sourcesStats: Record<string, { count: number; avgRelevance: number; errors: string[] }> = {}

    sourceResults.forEach((result, index) => {
      const sourceName = Array.from(this.sources.values())[index]?.name || `source-${index}`
      
      if (result.status === 'fulfilled') {
        allResults.push(...result.value)
        const relevanceSum = result.value.reduce((sum, r) => sum + r.relevanceScore, 0)
        sourcesStats[sourceName] = {
          count: result.value.length,
          avgRelevance: result.value.length > 0 ? relevanceSum / result.value.length : 0,
          errors: []
        }
      } else {
        sourcesStats[sourceName] = {
          count: 0,
          avgRelevance: 0,
          errors: [result.reason?.message || 'Unknown error']
        }
      }
    })

    // Sort by relevance score and apply limit
    const sortedResults = allResults
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, query.limit || 50)

    // Remove duplicates based on content similarity
    const deduplicatedResults = this.deduplicateResults(sortedResults)

    return {
      results: deduplicatedResults,
      sourcesStats
    }
  }

  /**
   * Remove duplicate results based on content similarity
   */
  private deduplicateResults(results: RetrievalResult[]): RetrievalResult[] {
    const deduped: RetrievalResult[] = []
    const seenContent = new Set<string>()

    for (const result of results) {
      const contentHash = this.hashContent(result.content)
      if (!seenContent.has(contentHash)) {
        seenContent.add(contentHash)
        deduped.push(result)
      }
    }

    return deduped
  }

  /**
   * Apply compression to results
   */
  private applyCompression(
    results: RetrievalResult[],
    compressionLevel: 'none' | 'light' | 'aggressive'
  ): RetrievalResult[] {
    if (compressionLevel === 'none') {
      return results
    }

    return results.map(result => {
      const compression = CompressionUtils.compress(result.content, compressionLevel)
      return {
        ...result,
        content: compression.compressed,
        compressed: true,
        originalSize: compression.originalSize,
        compressedSize: compression.compressedSize,
        metadata: {
          ...result.metadata,
          compressionLevel: compression.compressionLevel
        }
      }
    })
  }

  /**
   * Calculate compression statistics
   */
  private calculateCompressionStats(
    original: RetrievalResult[],
    compressed: RetrievalResult[]
  ): { originalSize: number; compressedSize: number; compressionRatio: number } {
    const originalSize = original.reduce((sum, r) => sum + r.content.length, 0)
    const compressedSize = compressed.reduce((sum, r) => sum + r.content.length, 0)
    
    return {
      originalSize,
      compressedSize,
      compressionRatio: originalSize > 0 ? compressedSize / originalSize : 1
    }
  }

  /**
   * Generate unique query ID
   */
  private generateQueryId(query: RetrievalQuery): string {
    const hash = this.hashContent(JSON.stringify(query))
    return `query-${hash}-${Date.now()}`
  }

  /**
   * Simple content hashing
   */
  private hashContent(content: string): string {
    let hash = 0
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16).substring(0, 8)
  }

  /**
   * Check cache for existing result
   */
  private checkCache(query: RetrievalQuery): RetrievalResponse | null {
    const queryHash = this.hashContent(JSON.stringify(query))
    const cached = this.cache.get(queryHash)
    
    if (!cached) return null
    
    const now = Date.now()
    if (now > cached.timestamp.getTime() + cached.ttl) {
      this.cache.delete(queryHash)
      return null
    }
    
    return cached.response
  }

  /**
   * Cache response
   */
  private cacheResponse(query: RetrievalQuery, response: RetrievalResponse): void {
    const queryHash = this.hashContent(JSON.stringify(query))
    const ttl = this.calculateCacheTTL(query)
    
    this.cache.set(queryHash, {
      response,
      timestamp: new Date(),
      ttl,
      queryHash
    })
  }

  /**
   * Calculate appropriate cache TTL
   */
  private calculateCacheTTL(query: RetrievalQuery): number {
    if (query.temporalHints?.recency === 'recent') {
      return 60 * 1000 // 1 minute for recent data
    }
    
    if (query.temporalHints?.recency === 'archive') {
      return 24 * 60 * 60 * 1000 // 24 hours for archive data
    }
    
    return 10 * 60 * 1000 // 10 minutes default
  }

  /**
   * Update performance statistics
   */
  private updateStats(response: RetrievalResponse): void {
    const latencies: number[] = []
    if (this.stats.totalQueries > 0) {
      latencies.push(this.stats.averageLatency)
    }
    latencies.push(response.executionTimeMs)
    
    this.stats.averageLatency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length
    
    if (response.compressionStats) {
      const savings = response.compressionStats.originalSize - response.compressionStats.compressedSize
      this.stats.compressionSavings += savings
    }
  }

  /**
   * Start periodic cache cleanup
   */
  private startCacheCleanup(): void {
    setInterval(() => {
      const now = Date.now()
      for (const [key, entry] of this.cache.entries()) {
        if (now > entry.timestamp.getTime() + entry.ttl) {
          this.cache.delete(key)
        }
      }
    }, 5 * 60 * 1000) // Clean up every 5 minutes
  }

  /**
   * Get performance statistics
   */
  getStats() {
    return {
      ...this.stats,
      cacheHitRate: this.stats.totalQueries > 0 ? this.stats.cacheHits / this.stats.totalQueries : 0,
      activeSources: this.sources.size,
      cacheSize: this.cache.size
    }
  }

  /**
   * Health check for all sources
   */
  async healthCheck(): Promise<Record<string, boolean>> {
    const health: Record<string, boolean> = {}
    
    for (const source of this.sources.values()) {
      try {
        await this.callSource(source, 'health-check', { limit: 1 })
        health[source.name] = true
      } catch (error) {
        health[source.name] = false
      }
    }
    
    return health
  }
}

// Global instance
export const retrievalRouter = new RetrievalRouter()

/**
 * Convenience function for simple retrieval
 */
export async function retrieve(query: string, options: Partial<RetrievalQuery> = {}): Promise<RetrievalResponse> {
  return retrievalRouter.retrieve({ query, ...options })
}