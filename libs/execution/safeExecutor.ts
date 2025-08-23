/**
 * Safe Executor - Tool call caps, idempotency, and bounded retry logic
 * ===================================================================
 * 
 * Provides safe execution environment for tool calls with:
 * - Rate limiting and caps per session/user/tool
 * - Idempotency keys to prevent duplicate operations
 * - Bounded retry logic with exponential backoff
 * - Circuit breaker pattern for failing services
 * - Execution context isolation and cleanup
 */

// Simple UUID generator for browser/Node compatibility
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/** Configuration for safe execution limits */
export interface SafeExecutionConfig {
  /** Maximum tool calls per session */
  maxCallsPerSession: number
  /** Maximum calls per tool per session */
  maxCallsPerTool: number
  /** Maximum calls per minute (rate limiting) */
  maxCallsPerMinute: number
  /** Default retry attempts */
  maxRetryAttempts: number
  /** Base delay for exponential backoff (ms) */
  baseRetryDelay: number
  /** Maximum retry delay (ms) */
  maxRetryDelay: number
  /** Circuit breaker failure threshold */
  circuitBreakerThreshold: number
  /** Circuit breaker timeout (ms) */
  circuitBreakerTimeout: number
  /** Idempotency key expiration (ms) */
  idempotencyKeyTTL: number
}

/** Default configuration */
export const defaultSafeConfig: SafeExecutionConfig = {
  maxCallsPerSession: 100,
  maxCallsPerTool: 20,
  maxCallsPerMinute: 30,
  maxRetryAttempts: 3,
  baseRetryDelay: 1000,
  maxRetryDelay: 30000,
  circuitBreakerThreshold: 5,
  circuitBreakerTimeout: 60000,
  idempotencyKeyTTL: 600000, // 10 minutes
}

/** Tool execution context */
export interface ExecutionContext {
  sessionId: string
  userId?: string
  toolName: string
  idempotencyKey?: string
  maxRetries?: number
  timeout?: number
  metadata?: Record<string, any>
}

/** Tool execution result */
export interface ExecutionResult<T = any> {
  success: boolean
  result?: T
  error?: Error
  executionId: string
  attemptCount: number
  executionTimeMs: number
  fromCache: boolean
  idempotencyKey?: string
}

/** Tool function signature */
export type ToolFunction<TInput = any, TOutput = any> = (
  input: TInput, 
  context: ExecutionContext
) => Promise<TOutput>

/** Rate limiting bucket for tracking calls */
interface RateLimitBucket {
  calls: number[]
  lastReset: number
}

/** Circuit breaker state */
interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half-open'
  failureCount: number
  lastFailureTime: number
  nextAttemptTime: number
}

/** Cached execution result for idempotency */
interface CachedResult {
  result: ExecutionResult
  timestamp: number
  ttl: number
}

export class SafeExecutor {
  private config: SafeExecutionConfig
  private sessionCalls: Map<string, number> = new Map()
  private toolCalls: Map<string, number> = new Map() // key: sessionId:toolName
  private rateLimitBuckets: Map<string, RateLimitBucket> = new Map()
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map()
  private idempotencyCache: Map<string, CachedResult> = new Map()
  private activeExecutions: Map<string, Promise<ExecutionResult>> = new Map()

  constructor(config: Partial<SafeExecutionConfig> = {}) {
    this.config = { ...defaultSafeConfig, ...config }
    
    // Start cleanup interval
    this.startCleanupInterval()
  }

  /**
   * Execute a tool function safely with all protections applied
   */
  async execute<TInput, TOutput>(
    toolFunction: ToolFunction<TInput, TOutput>,
    input: TInput,
    context: ExecutionContext
  ): Promise<ExecutionResult<TOutput>> {
    const executionId = generateUUID()
    const startTime = Date.now()

    try {
      // Check idempotency first
      if (context.idempotencyKey) {
        const cached = this.checkIdempotencyCache(context.idempotencyKey)
        if (cached) {
          return {
            ...cached,
            executionId,
            fromCache: true
          }
        }

        // Check if this operation is already in progress
        const activeKey = `${context.sessionId}:${context.idempotencyKey}`
        if (this.activeExecutions.has(activeKey)) {
          return await this.activeExecutions.get(activeKey)!
        }
      }

      // Create execution promise
      const executionPromise = this.executeWithProtections(
        toolFunction,
        input,
        context,
        executionId,
        startTime
      )

      // Track active execution for idempotency
      if (context.idempotencyKey) {
        const activeKey = `${context.sessionId}:${context.idempotencyKey}`
        this.activeExecutions.set(activeKey, executionPromise)
        
        // Clean up after execution
        executionPromise.finally(() => {
          this.activeExecutions.delete(activeKey)
        })
      }

      return await executionPromise

    } catch (error) {
      return {
        success: false,
        error: error as Error,
        executionId,
        attemptCount: 0,
        executionTimeMs: Date.now() - startTime,
        fromCache: false,
        idempotencyKey: context.idempotencyKey
      }
    }
  }

  /**
   * Execute with all safety protections
   */
  private async executeWithProtections<TInput, TOutput>(
    toolFunction: ToolFunction<TInput, TOutput>,
    input: TInput,
    context: ExecutionContext,
    executionId: string,
    startTime: number
  ): Promise<ExecutionResult<TOutput>> {
    // Check rate limits and caps
    this.checkExecutionLimits(context)

    // Check circuit breaker
    this.checkCircuitBreaker(context.toolName)

    // Track the call
    this.trackCall(context)

    // Execute with retry logic
    const result = await this.executeWithRetry(
      toolFunction,
      input,
      context,
      executionId
    )

    // Update circuit breaker state
    this.updateCircuitBreaker(context.toolName, result.success)

    // Cache result for idempotency
    if (context.idempotencyKey && result.success) {
      this.cacheResult(context.idempotencyKey, {
        ...result,
        executionId,
        executionTimeMs: Date.now() - startTime,
        fromCache: false
      })
    }

    return {
      ...result,
      executionId,
      executionTimeMs: Date.now() - startTime,
      fromCache: false,
      idempotencyKey: context.idempotencyKey
    }
  }

  /**
   * Check execution limits (rate limiting, caps)
   */
  private checkExecutionLimits(context: ExecutionContext): void {
    // Check session limits
    const sessionCalls = this.sessionCalls.get(context.sessionId) || 0
    if (sessionCalls >= this.config.maxCallsPerSession) {
      throw new Error(`Session ${context.sessionId} exceeded max calls (${this.config.maxCallsPerSession})`)
    }

    // Check per-tool limits
    const toolKey = `${context.sessionId}:${context.toolName}`
    const toolCalls = this.toolCalls.get(toolKey) || 0
    if (toolCalls >= this.config.maxCallsPerTool) {
      throw new Error(`Tool ${context.toolName} exceeded max calls (${this.config.maxCallsPerTool}) for session`)
    }

    // Check rate limiting
    const rateLimitKey = context.userId || context.sessionId
    const bucket = this.getRateLimitBucket(rateLimitKey)
    const now = Date.now()
    const oneMinuteAgo = now - 60000

    // Remove calls older than 1 minute
    bucket.calls = bucket.calls.filter(time => time > oneMinuteAgo)

    if (bucket.calls.length >= this.config.maxCallsPerMinute) {
      throw new Error(`Rate limit exceeded: ${this.config.maxCallsPerMinute} calls per minute`)
    }
  }

  /**
   * Check circuit breaker state
   */
  private checkCircuitBreaker(toolName: string): void {
    const breaker = this.getCircuitBreaker(toolName)
    const now = Date.now()

    switch (breaker.state) {
      case 'open':
        if (now < breaker.nextAttemptTime) {
          throw new Error(`Circuit breaker OPEN for ${toolName}. Next attempt at ${new Date(breaker.nextAttemptTime)}`)
        }
        // Transition to half-open
        breaker.state = 'half-open'
        break

      case 'half-open':
        // Allow one request through
        break

      case 'closed':
        // Normal operation
        break
    }
  }

  /**
   * Execute function with retry logic
   */
  private async executeWithRetry<TInput, TOutput>(
    toolFunction: ToolFunction<TInput, TOutput>,
    input: TInput,
    context: ExecutionContext,
    executionId: string
  ): Promise<Omit<ExecutionResult<TOutput>, 'executionId' | 'executionTimeMs' | 'fromCache'>> {
    const maxRetries = context.maxRetries ?? this.config.maxRetryAttempts
    let lastError: Error | undefined

    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      try {
        // Apply timeout if specified
        const result = context.timeout
          ? await this.withTimeout(toolFunction(input, context), context.timeout)
          : await toolFunction(input, context)

        return {
          success: true,
          result,
          attemptCount: attempt,
          idempotencyKey: context.idempotencyKey
        }

      } catch (error) {
        lastError = error as Error
        
        // Don't retry on certain types of errors
        if (this.isNonRetryableError(error)) {
          break
        }

        // Don't retry if this was the last attempt
        if (attempt > maxRetries) {
          break
        }

        // Calculate backoff delay
        const delay = this.calculateBackoffDelay(attempt)
        await this.sleep(delay)
      }
    }

    return {
      success: false,
      error: lastError,
      attemptCount: maxRetries + 1,
      idempotencyKey: context.idempotencyKey
    }
  }

  /**
   * Track a successful call
   */
  private trackCall(context: ExecutionContext): void {
    // Increment session counter
    const sessionCalls = this.sessionCalls.get(context.sessionId) || 0
    this.sessionCalls.set(context.sessionId, sessionCalls + 1)

    // Increment tool counter
    const toolKey = `${context.sessionId}:${context.toolName}`
    const toolCalls = this.toolCalls.get(toolKey) || 0
    this.toolCalls.set(toolKey, toolCalls + 1)

    // Track rate limiting
    const rateLimitKey = context.userId || context.sessionId
    const bucket = this.getRateLimitBucket(rateLimitKey)
    bucket.calls.push(Date.now())
  }

  /**
   * Get or create rate limit bucket
   */
  private getRateLimitBucket(key: string): RateLimitBucket {
    if (!this.rateLimitBuckets.has(key)) {
      this.rateLimitBuckets.set(key, {
        calls: [],
        lastReset: Date.now()
      })
    }
    return this.rateLimitBuckets.get(key)!
  }

  /**
   * Get or create circuit breaker
   */
  private getCircuitBreaker(toolName: string): CircuitBreakerState {
    if (!this.circuitBreakers.has(toolName)) {
      this.circuitBreakers.set(toolName, {
        state: 'closed',
        failureCount: 0,
        lastFailureTime: 0,
        nextAttemptTime: 0
      })
    }
    return this.circuitBreakers.get(toolName)!
  }

  /**
   * Update circuit breaker state based on execution result
   */
  private updateCircuitBreaker(toolName: string, success: boolean): void {
    const breaker = this.getCircuitBreaker(toolName)
    const now = Date.now()

    if (success) {
      if (breaker.state === 'half-open') {
        // Success in half-open state - close the circuit
        breaker.state = 'closed'
        breaker.failureCount = 0
      } else if (breaker.state === 'closed') {
        // Reset failure count on success
        breaker.failureCount = 0
      }
    } else {
      breaker.failureCount++
      breaker.lastFailureTime = now

      if (breaker.failureCount >= this.config.circuitBreakerThreshold) {
        breaker.state = 'open'
        breaker.nextAttemptTime = now + this.config.circuitBreakerTimeout
      }
    }
  }

  /**
   * Check idempotency cache
   */
  private checkIdempotencyCache(idempotencyKey: string): ExecutionResult | null {
    const cached = this.idempotencyCache.get(idempotencyKey)
    if (!cached) return null

    const now = Date.now()
    if (now > cached.timestamp + cached.ttl) {
      this.idempotencyCache.delete(idempotencyKey)
      return null
    }

    return cached.result
  }

  /**
   * Cache execution result for idempotency
   */
  private cacheResult(idempotencyKey: string, result: ExecutionResult): void {
    this.idempotencyCache.set(idempotencyKey, {
      result,
      timestamp: Date.now(),
      ttl: this.config.idempotencyKeyTTL
    })
  }

  /**
   * Execute with timeout
   */
  private async withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
      )
    ])
  }

  /**
   * Check if error should not be retried
   */
  private isNonRetryableError(error: any): boolean {
    const message = error?.message?.toLowerCase() || ''
    return (
      message.includes('unauthorized') ||
      message.includes('forbidden') ||
      message.includes('bad request') ||
      message.includes('not found') ||
      message.includes('validation') ||
      message.includes('schema')
    )
  }

  /**
   * Calculate exponential backoff delay
   */
  private calculateBackoffDelay(attempt: number): number {
    const delay = Math.min(
      this.config.baseRetryDelay * Math.pow(2, attempt - 1),
      this.config.maxRetryDelay
    )
    
    // Add jitter (±25%)
    const jitter = delay * 0.25 * (Math.random() - 0.5)
    return Math.max(100, delay + jitter)
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Reset session limits (call when session ends)
   */
  resetSession(sessionId: string): void {
    this.sessionCalls.delete(sessionId)
    
    // Remove tool counters for this session
    const keysToDelete = Array.from(this.toolCalls.keys())
      .filter(key => key.startsWith(`${sessionId}:`))
    keysToDelete.forEach(key => this.toolCalls.delete(key))
  }

  /**
   * Get execution statistics
   */
  getStats(): {
    activeSessions: number
    totalCalls: number
    circuitBreakerStates: Record<string, string>
    cachedResults: number
    activeExecutions: number
  } {
    const totalCalls = Array.from(this.sessionCalls.values())
      .reduce((sum, calls) => sum + calls, 0)

    const circuitBreakerStates: Record<string, string> = {}
    this.circuitBreakers.forEach((breaker, toolName) => {
      circuitBreakerStates[toolName] = breaker.state
    })

    return {
      activeSessions: this.sessionCalls.size,
      totalCalls,
      circuitBreakerStates,
      cachedResults: this.idempotencyCache.size,
      activeExecutions: this.activeExecutions.size
    }
  }

  /**
   * Start periodic cleanup of expired data
   */
  private startCleanupInterval(): void {
    setInterval(() => {
      const now = Date.now()
      const oneHourAgo = now - 3600000

      // Clean up old rate limit data
      this.rateLimitBuckets.forEach((bucket, key) => {
        bucket.calls = bucket.calls.filter(time => time > oneHourAgo)
        if (bucket.calls.length === 0 && bucket.lastReset < oneHourAgo) {
          this.rateLimitBuckets.delete(key)
        }
      })

      // Clean up expired idempotency cache
      this.idempotencyCache.forEach((cached, key) => {
        if (now > cached.timestamp + cached.ttl) {
          this.idempotencyCache.delete(key)
        }
      })
    }, 300000) // Run every 5 minutes
  }
}

// Global instance
export const safeExecutor = new SafeExecutor()

/**
 * Convenience wrapper for safe execution
 */
export async function executeSafely<TInput, TOutput>(
  toolName: string,
  toolFunction: ToolFunction<TInput, TOutput>,
  input: TInput,
  options: Partial<ExecutionContext> = {}
): Promise<ExecutionResult<TOutput>> {
  const context: ExecutionContext = {
    sessionId: 'default',
    toolName,
    ...options
  }

  return safeExecutor.execute(toolFunction, input, context)
}

/**
 * Generate a unique idempotency key
 */
export function generateIdempotencyKey(operation: string, inputs: any): string {
  // Simple hash function for browser compatibility
  const data = `${operation}:${JSON.stringify(inputs)}`;
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  const hashStr = Math.abs(hash).toString(16).padStart(8, '0').substring(0, 8);
  return `${operation}-${hashStr}`;
}