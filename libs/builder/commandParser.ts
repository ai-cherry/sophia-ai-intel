/**
 * Sophia Builder Command Parser
 * ============================
 * 
 * Parses chat commands for the CEO-gated builder loop:
 * @sophia propose "<change>" paths="..." [options]
 * 
 * Integrates with safe execution, idempotency, and proof generation.
 */

import { safeExecutor, ExecutionContext, generateIdempotencyKey } from '../execution/safeExecutor'
import { validateToolInput } from '../validation/toolSchemas'

/** Supported builder commands */
export enum BuilderCommand {
  PROPOSE = 'propose',
  STATUS = 'status',
  APPROVE = 'approve',
  CANCEL = 'cancel'
}

/** Builder command options */
export interface BuilderOptions {
  priority?: 'low' | 'normal' | 'high' | 'critical'
  branch?: string
  reviewer?: string
  deploy?: boolean
  dryRun?: boolean
  skipTests?: boolean
  skipLint?: boolean
  timeout?: number
}

/** Parsed command structure */
export interface ParsedCommand {
  command: BuilderCommand
  description: string
  paths?: string[]
  options: BuilderOptions
  originalMessage: string
  userId?: string
  sessionId?: string
  timestamp: Date
}

/** Command parsing result */
export interface CommandParseResult {
  success: boolean
  command?: ParsedCommand
  errors: string[]
  suggestions: string[]
  idempotencyKey: string
}

/** Builder proposal structure */
export interface BuilderProposal {
  id: string
  command: ParsedCommand
  status: 'pending' | 'approved' | 'rejected' | 'building' | 'completed' | 'failed'
  createdAt: Date
  updatedAt: Date
  buildDetails?: {
    branch: string
    prUrl?: string
    stagingUrl?: string
    buildLogs: string[]
    testResults?: any
    lintResults?: any
  }
  approvals: Array<{
    userId: string
    decision: 'approve' | 'reject'
    comment?: string
    timestamp: Date
  }>
  metadata: Record<string, any>
}

/** Command parsing patterns */
const COMMAND_PATTERNS = {
  // @sophia propose "description" paths="path1,path2" [options]
  propose: /^@sophia\s+propose\s+"([^"]+)"\s*(?:paths=["']([^"']+)["'])?\s*(.*)$/i,
  
  // @sophia status [proposal-id]
  status: /^@sophia\s+status\s*(.*)$/i,
  
  // @sophia approve proposal-id [comment]
  approve: /^@sophia\s+approve\s+([^\s]+)\s*(.*)$/i,
  
  // @sophia cancel proposal-id [reason]
  cancel: /^@sophia\s+cancel\s+([^\s]+)\s*(.*)$/i
}

/** Options parsing patterns */
const OPTION_PATTERNS = {
  priority: /priority=(\w+)/i,
  branch: /branch=([\w\-\.\/]+)/i,
  reviewer: /reviewer=([\w\-\.@]+)/i,
  deploy: /deploy=(true|false)/i,
  dryRun: /dry[-_]?run=(true|false)/i,
  skipTests: /skip[-_]?tests=(true|false)/i,
  skipLint: /skip[-_]?lint=(true|false)/i,
  timeout: /timeout=(\d+)/i
}

export class SophiaCommandParser {
  private activeProposals: Map<string, BuilderProposal> = new Map()
  private commandHistory: ParsedCommand[] = []
  private stats = {
    totalCommands: 0,
    successfulParses: 0,
    proposalsCreated: 0,
    approvals: 0,
    rejections: 0
  }

  /**
   * Parse a chat message for Sophia builder commands
   */
  async parseCommand(
    message: string,
    userId?: string,
    sessionId?: string
  ): Promise<CommandParseResult> {
    const startTime = Date.now()
    this.stats.totalCommands++
    
    // Generate idempotency key
    const idempotencyKey = generateIdempotencyKey('command_parse', {
      message: message.substring(0, 100), // Limit for key generation
      userId,
      sessionId,
      timestamp: Date.now()
    })

    try {
      // Check if message contains Sophia mention
      if (!this.isSophiaCommand(message)) {
        return {
          success: false,
          errors: [],
          suggestions: [],
          idempotencyKey
        }
      }

      // Parse command type
      const commandType = this.detectCommandType(message)
      if (!commandType) {
        return {
          success: false,
          errors: ['Unrecognized Sophia command'],
          suggestions: [
            'Try: @sophia propose "description" paths="src/"',
            'Try: @sophia status',
            'Try: @sophia approve <proposal-id>'
          ],
          idempotencyKey
        }
      }

      // Parse specific command
      let parsedCommand: ParsedCommand
      switch (commandType) {
        case BuilderCommand.PROPOSE:
          parsedCommand = await this.parsePropose(message, userId, sessionId)
          break
        case BuilderCommand.STATUS:
          parsedCommand = await this.parseStatus(message, userId, sessionId)
          break
        case BuilderCommand.APPROVE:
          parsedCommand = await this.parseApprove(message, userId, sessionId)
          break
        case BuilderCommand.CANCEL:
          parsedCommand = await this.parseCancel(message, userId, sessionId)
          break
        default:
          throw new Error(`Unsupported command type: ${commandType}`)
      }

      // Validate parsed command
      const validation = await this.validateCommand(parsedCommand)
      if (!validation.isValid) {
        return {
          success: false,
          errors: validation.errors,
          suggestions: validation.suggestions,
          idempotencyKey
        }
      }

      // Add to history
      this.commandHistory.push(parsedCommand)
      this.stats.successfulParses++

      // Execute safe parsing with idempotency
      const executionContext: ExecutionContext = {
        sessionId: sessionId || 'builder-session',
        userId,
        toolName: 'command-parser',
        idempotencyKey,
        timeout: 5000
      }

      const result = await safeExecutor.execute(
        async () => parsedCommand,
        { command: parsedCommand },
        executionContext
      )

      if (!result.success) {
        throw result.error || new Error('Safe execution failed')
      }

      return {
        success: true,
        command: parsedCommand,
        errors: [],
        suggestions: [],
        idempotencyKey
      }

    } catch (error) {
      return {
        success: false,
        errors: [(error as Error).message],
        suggestions: ['Check command syntax and try again'],
        idempotencyKey
      }
    }
  }

  /**
   * Create a builder proposal from a parsed command
   */
  async createProposal(
    command: ParsedCommand,
    idempotencyKey: string
  ): Promise<BuilderProposal> {
    if (command.command !== BuilderCommand.PROPOSE) {
      throw new Error('Can only create proposals from PROPOSE commands')
    }

    const proposalId = this.generateProposalId(command, idempotencyKey)
    
    // Check for existing proposal with same idempotency key
    const existing = Array.from(this.activeProposals.values())
      .find(p => p.metadata.idempotencyKey === idempotencyKey)
    
    if (existing) {
      return existing
    }

    const proposal: BuilderProposal = {
      id: proposalId,
      command,
      status: 'pending',
      createdAt: new Date(),
      updatedAt: new Date(),
      approvals: [],
      metadata: {
        idempotencyKey,
        estimatedComplexity: this.estimateComplexity(command),
        requiredApprovals: this.calculateRequiredApprovals(command)
      }
    }

    this.activeProposals.set(proposalId, proposal)
    this.stats.proposalsCreated++

    return proposal
  }

  /**
   * Check if message is a Sophia command
   */
  private isSophiaCommand(message: string): boolean {
    return /^@sophia\s+/i.test(message.trim())
  }

  /**
   * Detect the type of command
   */
  private detectCommandType(message: string): BuilderCommand | null {
    if (COMMAND_PATTERNS.propose.test(message)) return BuilderCommand.PROPOSE
    if (COMMAND_PATTERNS.status.test(message)) return BuilderCommand.STATUS
    if (COMMAND_PATTERNS.approve.test(message)) return BuilderCommand.APPROVE
    if (COMMAND_PATTERNS.cancel.test(message)) return BuilderCommand.CANCEL
    return null
  }

  /**
   * Parse PROPOSE command
   */
  private async parsePropose(
    message: string,
    userId?: string,
    sessionId?: string
  ): Promise<ParsedCommand> {
    const match = message.match(COMMAND_PATTERNS.propose)
    if (!match) {
      throw new Error('Invalid propose command syntax')
    }

    const [, description, pathsStr, optionsStr] = match

    // Parse paths
    const paths = pathsStr ? pathsStr.split(',').map(p => p.trim()) : []

    // Parse options
    const options = this.parseOptions(optionsStr || '')

    return {
      command: BuilderCommand.PROPOSE,
      description: description.trim(),
      paths,
      options,
      originalMessage: message,
      userId,
      sessionId,
      timestamp: new Date()
    }
  }

  /**
   * Parse STATUS command
   */
  private async parseStatus(
    message: string,
    userId?: string,
    sessionId?: string
  ): Promise<ParsedCommand> {
    const match = message.match(COMMAND_PATTERNS.status)
    if (!match) {
      throw new Error('Invalid status command syntax')
    }

    const [, proposalId] = match

    return {
      command: BuilderCommand.STATUS,
      description: proposalId?.trim() || 'all',
      paths: [],
      options: {},
      originalMessage: message,
      userId,
      sessionId,
      timestamp: new Date()
    }
  }

  /**
   * Parse APPROVE command
   */
  private async parseApprove(
    message: string,
    userId?: string,
    sessionId?: string
  ): Promise<ParsedCommand> {
    const match = message.match(COMMAND_PATTERNS.approve)
    if (!match) {
      throw new Error('Invalid approve command syntax')
    }

    const [, proposalId, comment] = match

    return {
      command: BuilderCommand.APPROVE,
      description: proposalId.trim(),
      paths: [],
      options: { reviewer: userId },
      originalMessage: message,
      userId,
      sessionId,
      timestamp: new Date()
    }
  }

  /**
   * Parse CANCEL command
   */
  private async parseCancel(
    message: string,
    userId?: string,
    sessionId?: string
  ): Promise<ParsedCommand> {
    const match = message.match(COMMAND_PATTERNS.cancel)
    if (!match) {
      throw new Error('Invalid cancel command syntax')
    }

    const [, proposalId, reason] = match

    return {
      command: BuilderCommand.CANCEL,
      description: proposalId.trim(),
      paths: [],
      options: {},
      originalMessage: message,
      userId,
      sessionId,
      timestamp: new Date()
    }
  }

  /**
   * Parse command options
   */
  private parseOptions(optionsStr: string): BuilderOptions {
    const options: BuilderOptions = {}

    // Parse each option type
    for (const [key, pattern] of Object.entries(OPTION_PATTERNS)) {
      const match = optionsStr.match(pattern)
      if (match) {
        const value = match[1]
        switch (key) {
          case 'priority':
            options.priority = value as BuilderOptions['priority']
            break
          case 'branch':
            options.branch = value
            break
          case 'reviewer':
            options.reviewer = value
            break
          case 'deploy':
            options.deploy = value === 'true'
            break
          case 'dryRun':
            options.dryRun = value === 'true'
            break
          case 'skipTests':
            options.skipTests = value === 'true'
            break
          case 'skipLint':
            options.skipLint = value === 'true'
            break
          case 'timeout':
            options.timeout = parseInt(value, 10)
            break
        }
      }
    }

    return options
  }

  /**
   * Validate parsed command
   */
  private async validateCommand(command: ParsedCommand): Promise<{
    isValid: boolean
    errors: string[]
    suggestions: string[]
  }> {
    const errors: string[] = []
    const suggestions: string[] = []

    // Validate description
    if (!command.description || command.description.length < 5) {
      errors.push('Description must be at least 5 characters long')
      suggestions.push('Provide a clear description of the proposed change')
    }

    if (command.description.length > 200) {
      errors.push('Description must be less than 200 characters')
      suggestions.push('Keep description concise and focused')
    }

    // Validate paths for PROPOSE command
    if (command.command === BuilderCommand.PROPOSE) {
      if (!command.paths || command.paths.length === 0) {
        errors.push('At least one path must be specified for propose command')
        suggestions.push('Add paths="src/components/" or similar')
      }

      // Validate path format
      if (command.paths) {
        for (const path of command.paths) {
          if (path.includes('..') || path.startsWith('/')) {
            errors.push(`Invalid path: ${path}`)
            suggestions.push('Use relative paths without ".." or leading "/"')
          }
        }
      }
    }

    // Validate options
    if (command.options.priority && 
        !['low', 'normal', 'high', 'critical'].includes(command.options.priority)) {
      errors.push('Priority must be: low, normal, high, or critical')
    }

    if (command.options.timeout && command.options.timeout < 60) {
      errors.push('Timeout must be at least 60 seconds')
    }

    return {
      isValid: errors.length === 0,
      errors,
      suggestions
    }
  }

  /**
   * Generate unique proposal ID
   */
  private generateProposalId(command: ParsedCommand, idempotencyKey: string): string {
    const timestamp = Date.now()
    const hash = idempotencyKey.substring(0, 8)
    return `proposal-${timestamp}-${hash}`
  }

  /**
   * Estimate complexity of the proposed change
   */
  private estimateComplexity(command: ParsedCommand): 'low' | 'medium' | 'high' {
    const pathCount = command.paths?.length || 0
    const hasTests = command.description.toLowerCase().includes('test')
    const hasInfra = command.paths?.some(p => p.includes('infra') || p.includes('deploy')) || false
    
    if (pathCount > 5 || hasInfra) return 'high'
    if (pathCount > 2 || hasTests) return 'medium'
    return 'low'
  }

  /**
   * Calculate required approvals based on complexity and paths
   */
  private calculateRequiredApprovals(command: ParsedCommand): number {
    const complexity = this.estimateComplexity(command)
    const hasInfra = command.paths?.some(p => 
      p.includes('infra') || p.includes('.github') || p.includes('deploy')
    ) || false

    if (hasInfra || complexity === 'high') return 2
    if (complexity === 'medium') return 1
    return 1 // Always require at least one approval
  }

  /**
   * Get proposal by ID
   */
  getProposal(id: string): BuilderProposal | undefined {
    return this.activeProposals.get(id)
  }

  /**
   * Get all active proposals
   */
  getActiveProposals(): BuilderProposal[] {
    return Array.from(this.activeProposals.values())
  }

  /**
   * Get command parsing statistics
   */
  getStats() {
    return {
      ...this.stats,
      successRate: this.stats.totalCommands > 0 
        ? this.stats.successfulParses / this.stats.totalCommands 
        : 0,
      activeProposals: this.activeProposals.size,
      commandHistoryLength: this.commandHistory.length
    }
  }

  /**
   * Clear command history (for testing/cleanup)
   */
  clearHistory(): void {
    this.commandHistory = []
  }
}

// Global instance
export const sophiaCommandParser = new SophiaCommandParser()

/**
 * Convenience function for parsing commands
 */
export async function parseCommand(
  message: string,
  userId?: string,
  sessionId?: string
): Promise<CommandParseResult> {
  return sophiaCommandParser.parseCommand(message, userId, sessionId)
}

/**
 * Example usage patterns
 */
export const EXAMPLE_COMMANDS = {
  basic: '@sophia propose "Add user authentication" paths="src/auth/"',
  withOptions: '@sophia propose "Update dashboard UI" paths="src/components/dashboard/" priority=high deploy=true',
  status: '@sophia status proposal-1724367845231-a3f7k2',
  approve: '@sophia approve proposal-1724367845231-a3f7k2 Looks good to me!'
}