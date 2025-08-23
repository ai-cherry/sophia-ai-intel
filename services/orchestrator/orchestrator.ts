/**
 * Orchestrator Service - Sequenced one-chat pipeline execution
 * ===========================================================
 * 
 * Coordinates the complete one-chat pipeline:
 * prompt → retrieval → planning → tools → synthesis
 * 
 * Integrates all Phase A/B components for comprehensive AI orchestration.
 */

import { contextEnforcer, AnalysisResult } from '../../libs/persona/contextEnforcer'
import { safeExecutor, ExecutionContext, ExecutionResult } from '../../libs/execution/safeExecutor'
import { personaRouter, RoutingContext, RoutingDecision } from '../../libs/routing/personaRouter'
import { retrievalRouter, RetrievalQuery, RetrievalResponse } from '../../libs/retrieval/retrievalRouter'
import { validateToolInput, validateToolOutput } from '../../libs/validation/toolSchemas'

/** Pipeline execution phases */
export enum PipelinePhase {
  PROMPT_ANALYSIS = 'prompt_analysis',
  RETRIEVAL = 'retrieval',
  PLANNING = 'planning',
  TOOL_EXECUTION = 'tool_execution',
  SYNTHESIS = 'synthesis',
  VALIDATION = 'validation',
  COMPLETION = 'completion'
}

/** Pipeline execution request */
export interface PipelineRequest {
  userPrompt: string
  sessionId: string
  userId?: string
  context?: {
    conversationHistory?: Array<{
      role: 'user' | 'assistant' | 'system'
      content: string
      timestamp: Date
    }>
    metadata?: Record<string, any>
    preferences?: {
      responseLength?: 'brief' | 'moderate' | 'detailed'
      technicalLevel?: 'beginner' | 'intermediate' | 'expert'
      includeReferences?: boolean
      prioritizeSpeed?: boolean
    }
  }
  constraints?: {
    maxExecutionTime?: number
    maxToolCalls?: number
    allowedTools?: string[]
    requiredSources?: string[]
  }
}

/** Individual phase execution result */
export interface PhaseResult {
  phase: PipelinePhase
  success: boolean
  executionTimeMs: number
  result?: any
  error?: Error
  metadata: Record<string, any>
  proofs: Array<{
    type: string
    data: any
    timestamp: Date
  }>
}

/** Complete pipeline execution result */
export interface PipelineResult {
  success: boolean
  response: string
  executionId: string
  totalExecutionTimeMs: number
  phases: PhaseResult[]
  contextAnalysis: AnalysisResult
  routingDecision: RoutingDecision
  retrievalResponse?: RetrievalResponse
  toolExecutions: Array<{
    tool: string
    input: any
    output: any
    success: boolean
    executionTimeMs: number
  }>
  metadata: {
    request: PipelineRequest
    pipelineVersion: string
    timestamp: Date
    proofCount: number
  }
}

/** Tool execution plan */
interface ToolPlan {
  tools: Array<{
    name: string
    parameters: Record<string, any>
    dependencies: string[]
    priority: number
    rationale: string
  }>
  executionStrategy: 'sequential' | 'parallel' | 'conditional'
  estimatedDuration: number
}

/** Synthesis configuration */
interface SynthesisConfig {
  includeReferences: boolean
  includeMetadata: boolean
  responseStyle: 'conversational' | 'report' | 'bullet-points' | 'structured'
  compressionLevel: 'none' | 'light' | 'aggressive'
}

export class PipelineOrchestrator {
  private activeExecutions: Map<string, PipelineResult> = new Map()
  private executionStats = {
    totalExecutions: 0,
    successfulExecutions: 0,
    averageExecutionTime: 0,
    phaseBreakdown: new Map<PipelinePhase, { count: number; averageTime: number }>()
  }

  constructor() {
    this.initializePhaseStats()
  }

  /**
   * Execute the complete one-chat pipeline
   */
  async execute(request: PipelineRequest): Promise<PipelineResult> {
    const executionId = this.generateExecutionId()
    const startTime = Date.now()
    
    this.executionStats.totalExecutions++

    // Initialize result structure
    const result: PipelineResult = {
      success: false,
      response: '',
      executionId,
      totalExecutionTimeMs: 0,
      phases: [],
      contextAnalysis: {} as AnalysisResult,
      routingDecision: {} as RoutingDecision,
      toolExecutions: [],
      metadata: {
        request,
        pipelineVersion: '1.0.0',
        timestamp: new Date(),
        proofCount: 0
      }
    }

    try {
      // Track active execution
      this.activeExecutions.set(executionId, result)

      // Phase 1: Prompt Analysis
      const promptPhase = await this.executePromptAnalysis(request, executionId)
      result.phases.push(promptPhase)
      
      if (!promptPhase.success) {
        throw new Error(`Prompt analysis failed: ${promptPhase.error?.message}`)
      }

      result.contextAnalysis = promptPhase.result.contextAnalysis
      result.routingDecision = promptPhase.result.routingDecision

      // Phase 2: Retrieval
      const retrievalPhase = await this.executeRetrieval(request, result.contextAnalysis, executionId)
      result.phases.push(retrievalPhase)
      
      if (retrievalPhase.success) {
        result.retrievalResponse = retrievalPhase.result
      }

      // Phase 3: Planning
      const planningPhase = await this.executePlanning(request, result, executionId)
      result.phases.push(planningPhase)

      if (!planningPhase.success) {
        throw new Error(`Planning failed: ${planningPhase.error?.message}`)
      }

      const toolPlan: ToolPlan = planningPhase.result

      // Phase 4: Tool Execution
      const toolPhase = await this.executeTools(toolPlan, request, result, executionId)
      result.phases.push(toolPhase)

      if (toolPhase.success) {
        result.toolExecutions = toolPhase.result
      }

      // Phase 5: Synthesis
      const synthesisPhase = await this.executeSynthesis(request, result, executionId)
      result.phases.push(synthesisPhase)

      if (!synthesisPhase.success) {
        throw new Error(`Synthesis failed: ${synthesisPhase.error?.message}`)
      }

      result.response = synthesisPhase.result.response

      // Phase 6: Validation
      const validationPhase = await this.executeValidation(result, executionId)
      result.phases.push(validationPhase)

      // Phase 7: Completion
      const completionPhase = await this.executeCompletion(result, executionId)
      result.phases.push(completionPhase)

      result.success = true
      this.executionStats.successfulExecutions++

    } catch (error) {
      console.error(`Pipeline execution failed:`, error)
      result.success = false
      
      // Add error phase
      result.phases.push({
        phase: PipelinePhase.COMPLETION,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs: [{
          type: 'pipeline_error',
          data: { error: (error as Error).message, stack: (error as Error).stack },
          timestamp: new Date()
        }]
      })
    } finally {
      result.totalExecutionTimeMs = Date.now() - startTime
      result.metadata.proofCount = this.countTotalProofs(result)

      // Update statistics
      this.updateExecutionStats(result)
      
      // Clean up active execution
      this.activeExecutions.delete(executionId)
    }

    return result
  }

  /**
   * Phase 1: Analyze user prompt and determine context
   */
  private async executePromptAnalysis(
    request: PipelineRequest,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Analyze context using enforcer
      const contextAnalysis = contextEnforcer.analyzeContext({
        message: request.userPrompt,
        metadata: request.context?.metadata
      })

      proofs.push({
        type: 'context_analysis',
        data: contextAnalysis,
        timestamp: new Date()
      })

      // Determine routing strategy
      const routingContext: RoutingContext = {
        prompt: request.userPrompt,
        conversationHistory: request.context?.conversationHistory,
        operationType: this.determineOperationType(request.userPrompt, contextAnalysis),
        userQuery: request.userPrompt,
        metadata: request.context?.metadata
      }

      const routingDecision = await personaRouter.route(routingContext)

      proofs.push({
        type: 'routing_decision',
        data: routingDecision,
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.PROMPT_ANALYSIS,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: { contextAnalysis, routingDecision },
        metadata: { 
          contextType: contextAnalysis.contextType,
          riskLevel: contextAnalysis.riskLevel,
          selectedModel: routingDecision.model
        },
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.PROMPT_ANALYSIS,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 2: Execute retrieval across data sources
   */
  private async executeRetrieval(
    request: PipelineRequest,
    contextAnalysis: AnalysisResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Build retrieval query
      const retrievalQuery: RetrievalQuery = {
        query: request.userPrompt,
        limit: 20,
        compressionLevel: this.determineCompressionLevel(contextAnalysis),
        temporalHints: {
          recency: contextAnalysis.riskLevel === 'high' ? 'recent' : 'all',
          priority: 'comprehensive'
        },
        includeMetadata: true,
        sources: request.constraints?.requiredSources
      }

      proofs.push({
        type: 'retrieval_query',
        data: retrievalQuery,
        timestamp: new Date()
      })

      // Execute retrieval with safe executor
      const executionContext: ExecutionContext = {
        sessionId: request.sessionId,
        userId: request.userId,
        toolName: 'retrieval-router',
        timeout: request.constraints?.maxExecutionTime || 10000
      }

      const retrievalResult = await safeExecutor.execute(
        async () => await retrievalRouter.retrieve(retrievalQuery),
        retrievalQuery,
        executionContext
      )

      if (!retrievalResult.success) {
        throw retrievalResult.error || new Error('Retrieval failed')
      }

      proofs.push({
        type: 'retrieval_response',
        data: retrievalResult.result,
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.RETRIEVAL,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: retrievalResult.result,
        metadata: {
          totalResults: retrievalResult.result?.totalResults || 0,
          sourcesQueried: Object.keys(retrievalResult.result?.sources || {}),
          compressionRatio: retrievalResult.result?.compressionStats?.compressionRatio || 1
        },
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.RETRIEVAL,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 3: Plan tool execution strategy
   */
  private async executePlanning(
    request: PipelineRequest,
    currentResult: PipelineResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Analyze what tools might be needed based on prompt and retrieval
      const toolPlan = this.generateToolPlan(
        request.userPrompt,
        currentResult.retrievalResponse,
        currentResult.contextAnalysis,
        request.constraints
      )

      proofs.push({
        type: 'tool_plan',
        data: toolPlan,
        timestamp: new Date()
      })

      // Validate tool plan against constraints
      const validatedPlan = this.validateToolPlan(toolPlan, request.constraints)

      proofs.push({
        type: 'validated_tool_plan',
        data: validatedPlan,
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.PLANNING,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: validatedPlan,
        metadata: {
          toolCount: validatedPlan.tools.length,
          strategy: validatedPlan.executionStrategy,
          estimatedDuration: validatedPlan.estimatedDuration
        },
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.PLANNING,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 4: Execute planned tools
   */
  private async executeTools(
    toolPlan: ToolPlan,
    request: PipelineRequest,
    currentResult: PipelineResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []
    const toolExecutions: PipelineResult['toolExecutions'] = []

    try {
      // Execute tools based on strategy
      if (toolPlan.executionStrategy === 'sequential') {
        for (const tool of toolPlan.tools) {
          const execution = await this.executeSingleTool(tool, request, executionId)
          toolExecutions.push(execution)
          
          proofs.push({
            type: 'tool_execution',
            data: execution,
            timestamp: new Date()
          })
          
          if (!execution.success && tool.priority > 7) {
            throw new Error(`Critical tool ${tool.name} failed: ${execution.output?.error}`)
          }
        }
      } else if (toolPlan.executionStrategy === 'parallel') {
        const executions = await Promise.allSettled(
          toolPlan.tools.map(tool => this.executeSingleTool(tool, request, executionId))
        )
        
        executions.forEach((result, index) => {
          const tool = toolPlan.tools[index]
          if (result.status === 'fulfilled') {
            toolExecutions.push(result.value)
          } else {
            toolExecutions.push({
              tool: tool.name,
              input: tool.parameters,
              output: { error: result.reason.message },
              success: false,
              executionTimeMs: 0
            })
          }
        })
      }

      proofs.push({
        type: 'tool_execution_summary',
        data: {
          totalTools: toolExecutions.length,
          successful: toolExecutions.filter(e => e.success).length,
          failed: toolExecutions.filter(e => !e.success).length
        },
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.TOOL_EXECUTION,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: toolExecutions,
        metadata: {
          toolsExecuted: toolExecutions.length,
          successfulTools: toolExecutions.filter(e => e.success).length,
          failedTools: toolExecutions.filter(e => !e.success).length
        },
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.TOOL_EXECUTION,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        result: toolExecutions,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 5: Synthesize final response
   */
  private async executeSynthesis(
    request: PipelineRequest,
    currentResult: PipelineResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Determine synthesis configuration
      const synthesisConfig: SynthesisConfig = {
        includeReferences: request.context?.preferences?.includeReferences !== false,
        includeMetadata: currentResult.contextAnalysis.riskLevel === 'high',
        responseStyle: this.determineResponseStyle(request, currentResult.contextAnalysis),
        compressionLevel: currentResult.contextAnalysis.riskLevel === 'high' ? 'none' : 'light'
      }

      proofs.push({
        type: 'synthesis_config',
        data: synthesisConfig,
        timestamp: new Date()
      })

      // Build synthesis context
      const synthesisContext = {
        originalPrompt: request.userPrompt,
        retrievalResults: currentResult.retrievalResponse?.results || [],
        toolResults: currentResult.toolExecutions.filter(e => e.success).map(e => e.output),
        conversationHistory: request.context?.conversationHistory || [],
        preferences: request.context?.preferences
      }

      // Execute synthesis using LLM with optimal routing
      const llmRequest: RoutingContext = {
        prompt: this.buildSynthesisPrompt(synthesisContext, synthesisConfig),
        operationType: 'analytical',
        conversationHistory: request.context?.conversationHistory,
        metadata: { phase: 'synthesis', executionId }
      }

      const routingDecision = await personaRouter.route(llmRequest)
      
      proofs.push({
        type: 'synthesis_routing',
        data: routingDecision,
        timestamp: new Date()
      })

      // Mock LLM call (in real implementation, this would call the actual LLM)
      const response = await this.callLLMForSynthesis(
        llmRequest,
        routingDecision,
        synthesisContext,
        synthesisConfig
      )

      proofs.push({
        type: 'synthesis_response',
        data: { response, config: synthesisConfig },
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.SYNTHESIS,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: { response, config: synthesisConfig },
        metadata: {
          responseLength: response.length,
          style: synthesisConfig.responseStyle,
          referencesIncluded: synthesisConfig.includeReferences
        },
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.SYNTHESIS,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 6: Validate final result
   */
  private async executeValidation(
    result: PipelineResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Validate response quality
      const qualityCheck = this.validateResponseQuality(result.response, result.metadata.request)
      
      proofs.push({
        type: 'quality_validation',
        data: qualityCheck,
        timestamp: new Date()
      })

      // Validate against persona constraints
      const personaCheck = this.validatePersonaCompliance(result)
      
      proofs.push({
        type: 'persona_validation',
        data: personaCheck,
        timestamp: new Date()
      })

      // Validate execution integrity
      const integrityCheck = this.validateExecutionIntegrity(result)
      
      proofs.push({
        type: 'integrity_validation',
        data: integrityCheck,
        timestamp: new Date()
      })

      const validationSummary = {
        quality: qualityCheck.score,
        personaCompliance: personaCheck.compliant,
        executionIntegrity: integrityCheck.valid,
        overallValid: qualityCheck.score > 0.7 && personaCheck.compliant && integrityCheck.valid
      }

      return {
        phase: PipelinePhase.VALIDATION,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: validationSummary,
        metadata: validationSummary,
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.VALIDATION,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  /**
   * Phase 7: Completion and cleanup
   */
  private async executeCompletion(
    result: PipelineResult,
    executionId: string
  ): Promise<PhaseResult> {
    const startTime = Date.now()
    const proofs: PhaseResult['proofs'] = []

    try {
      // Generate execution summary
      const summary = {
        executionId,
        success: result.success,
        totalPhases: result.phases.length,
        totalExecutionTime: result.totalExecutionTimeMs,
        toolsExecuted: result.toolExecutions.length,
        proofsGenerated: this.countTotalProofs(result),
        responseLength: result.response.length
      }

      proofs.push({
        type: 'execution_summary',
        data: summary,
        timestamp: new Date()
      })

      // Log completion metrics
      proofs.push({
        type: 'completion_metrics',
        data: {
          timestamp: new Date(),
          executionId,
          success: result.success,
          duration: result.totalExecutionTimeMs
        },
        timestamp: new Date()
      })

      return {
        phase: PipelinePhase.COMPLETION,
        success: true,
        executionTimeMs: Date.now() - startTime,
        result: summary,
        metadata: summary,
        proofs
      }

    } catch (error) {
      return {
        phase: PipelinePhase.COMPLETION,
        success: false,
        executionTimeMs: Date.now() - startTime,
        error: error as Error,
        metadata: { error: (error as Error).message },
        proofs
      }
    }
  }

  // Helper methods (continued in next part due to length...)

  private generateExecutionId(): string {
    return `pipeline-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`
  }

  private determineOperationType(prompt: string, analysis: AnalysisResult): 'creative' | 'analytical' | 'factual' | 'conversational' {
    if (analysis.contextType === 'creative') return 'creative'
    if (analysis.isSecurity || analysis.isFinancial) return 'analytical'
    if (prompt.includes('?') && prompt.length < 100) return 'factual'
    return 'conversational'
  }

  private determineCompressionLevel(analysis: AnalysisResult): 'none' | 'light' | 'aggressive' {
    if (analysis.riskLevel === 'high') return 'none'
    if (analysis.riskLevel === 'medium') return 'light'
    return 'aggressive'
  }

  private generateToolPlan(
    prompt: string,
    retrievalResponse?: RetrievalResponse,
    contextAnalysis?: AnalysisResult,
    constraints?: PipelineRequest['constraints']
  ): ToolPlan {
    // Simple tool planning logic (would be more sophisticated in real implementation)
    const tools = []
    
    if (prompt.includes('search') || prompt.includes('find')) {
      tools.push({
        name: 'context_search',
        parameters: { query: prompt, limit: 10 },
        dependencies: [],
        priority: 8,
        rationale: 'User requested search functionality'
      })
    }

    if (contextAnalysis?.isFinancial) {
      tools.push({
        name: 'prospects_search',
        parameters: { query: prompt },
        dependencies: [],
        priority: 9,
        rationale: 'Financial context requires business data'
      })
    }

    return {
      tools,
      executionStrategy: tools.length > 2 ? 'parallel' : 'sequential',
      estimatedDuration: tools.length * 2000
    }
  }

  private validateToolPlan(plan: ToolPlan, constraints?: PipelineRequest['constraints']): ToolPlan {
    if (constraints?.allowedTools) {
      plan.tools = plan.tools.filter(tool => constraints.allowedTools!.includes(tool.name))
    }
    
    if (constraints?.maxToolCalls) {
      plan.tools = plan.tools.slice(0, constraints.maxToolCalls)
    }
    
    return plan
  }

  private async executeSingleTool(
    tool: ToolPlan['tools'][0],
    request: PipelineRequest,
    executionId: string
  ): Promise<PipelineResult['toolExecutions'][0]> {
    const startTime = Date.now()
    
    try {
      // Validate input
      const inputValidation = validateToolInput(tool.name, tool.parameters)
      if (!inputValidation.isValid) {
        throw new Error(`Invalid tool input: ${inputValidation.errors.map(e => e.message).join(', ')}`)
      }

      // Execute with safe executor
      const executionContext: ExecutionContext = {
        sessionId: request.sessionId,
        userId: request.userId,
        toolName: tool.name,
        idempotencyKey: `${executionId}-${tool.name}-${Date.now()}`
      }

      const result = await safeExecutor.execute(
        async (input) => {
          // Mock tool execution (in real implementation, would call actual tools)
          return { result: `Mock result for ${tool.name} with input: ${JSON.stringify(input)}` }
        },
        inputValidation.sanitizedValue || tool.parameters,
        executionContext
      )

      // Validate output
      if (result.success && result.result) {
        const outputValidation = validateToolOutput(tool.name, result.result)
        if (!outputValidation.isValid) {
          console.warn(`Tool output validation failed for ${tool.name}:`, outputValidation.errors)
        }
      }

      return {
        tool: tool.name,
        input: tool.parameters,
        output: result.result,
        success: result.success,
        executionTimeMs: Date.now() - startTime
      }

    } catch (error) {
      return {
        tool: tool.name,
        input: tool.parameters,
        output: { error: (error as Error).message },
        success: false,
        executionTimeMs: Date.now() - startTime
      }
    }
  }

  private determineResponseStyle(
    request: PipelineRequest,
    analysis: AnalysisResult
  ): SynthesisConfig['responseStyle'] {
    if (request.context?.preferences?.responseLength === 'brief') return 'bullet-points'
    if (analysis.riskLevel === 'high') return 'structured'
    if (analysis.contextType === 'creative') return 'conversational'
    return 'report'
  }

  private buildSynthesisPrompt(context: any, config: SynthesisConfig): string {
    return `Based on the user's query "${context.originalPrompt}", provide a ${config.responseStyle} response using the retrieved data and tool results.`
  }

  private async callLLMForSynthesis(
    request: RoutingContext,
    routing: RoutingDecision,
    context: any,
    config: SynthesisConfig
  ): Promise<string> {
    // Mock LLM response (in real implementation, would call actual LLM API)
    return `This is a synthesized response based on the analysis. The system processed your request "${context.originalPrompt}" and found relevant information from ${context.retrievalResults.length} sources. Tool execution completed successfully with ${context.toolResults.length} results.`
  }

  private validateResponseQuality(response: string, request: PipelineRequest): { score: number; issues: string[] } {
    const issues: string[] = []
    let score = 1.0

    if (response.length < 50) {
      issues.push('Response too short')
      score -= 0.3
    }

    if (!response.includes(request.userPrompt.split(' ')[0])) {
      issues.push('Response does not address user query')
      score -= 0.5
    }

    return { score: Math.max(0, score), issues }
  }

  private validatePersonaCompliance(result: PipelineResult): { compliant: boolean; violations: string[] } {
    const violations: string[] = []
    
    // Check if persona enforcement was properly applied
    if (!result.routingDecision.personaAdjustments || result.routingDecision.personaAdjustments.length === 0) {
      violations.push('No persona adjustments detected')
    }

    return { compliant: violations.length === 0, violations }
  }

  private validateExecutionIntegrity(result: PipelineResult): { valid: boolean; issues: string[] } {
    const issues: string[] = []

    if (result.phases.length < 5) {
      issues.push('Incomplete pipeline execution')
    }

    if (!result.contextAnalysis.contextType) {
      issues.push('Missing context analysis')
    }

    return { valid: issues.length === 0, issues }
  }

  private countTotalProofs(result: PipelineResult): number {
    return result.phases.reduce((count, phase) => count + phase.proofs.length, 0)
  }

  private initializePhaseStats(): void {
    Object.values(PipelinePhase).forEach(phase => {
      this.executionStats.phaseBreakdown.set(phase, { count: 0, averageTime: 0 })
    })
  }

  private updateExecutionStats(result: PipelineResult): void {
    // Update phase statistics
    result.phases.forEach(phase => {
      const stats = this.executionStats.phaseBreakdown.get(phase.phase)
      if (stats) {
        const newCount = stats.count + 1
        const newAverage = (stats.averageTime * stats.count + phase.executionTimeMs) / newCount
        this.executionStats.phaseBreakdown.set(phase.phase, {
          count: newCount,
          averageTime: newAverage
        })
      }
    })

    // Update overall stats
    const newAvg = (this.executionStats.averageExecutionTime * (this.executionStats.totalExecutions - 1) + result.totalExecutionTimeMs) / this.executionStats.totalExecutions
    this.executionStats.averageExecutionTime = newAvg
  }

  /**
   * Get execution statistics
   */
  getStats() {
    return {
      ...this.executionStats,
      successRate: this.executionStats.totalExecutions > 0 
        ? this.executionStats.successfulExecutions / this.executionStats.totalExecutions 
        : 0,
      activeExecutions: this.activeExecutions.size,
      phaseBreakdown: Object.fromEntries(this.executionStats.phaseBreakdown)
    }
  }

  /**
   * Get active executions
   */
  getActiveExecutions(): string[] {
    return Array.from(this.activeExecutions.keys())
  }

  /**
   * Cancel an active execution
   */
  async cancelExecution(executionId: string): Promise<boolean> {
    if (this.activeExecutions.has(executionId)) {
      this.activeExecutions.delete(executionId)
      return true
    }
    return false
  }
}

// Global instance
export const pipelineOrchestrator = new PipelineOrchestrator()

/**
 * Convenience function for executing pipeline
 */
export async function executeOrchestration(request: PipelineRequest): Promise<PipelineResult> {
  return pipelineOrchestrator.execute(request)
}