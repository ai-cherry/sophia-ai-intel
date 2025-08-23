/**
 * Sophia AI Builder Service
 *
 * Core service that orchestrates the CEO-gated builder loop:
 * 1. Parse chat commands (@sophia propose)
 * 2. Dispatch GitHub workflows
 * 3. Generate proof artifacts
 * 4. Handle idempotency and safe execution
 */

import { SafeExecutor, type SafeExecutionConfig, type ExecutionContext, type ExecutionResult } from '../execution/safeExecutor';
import { SophiaCommandParser, BuilderCommand, type ParsedCommand, type CommandParseResult } from './commandParser';

// GitHub API types
interface GitHubWorkflowDispatch {
  workflow_id: string;
  ref: string;
  inputs: Record<string, string | boolean>;
}

interface GitHubAPIResponse {
  status: number;
  message?: string;
  run_id?: number;
  html_url?: string;
}

interface BuilderProposal {
  id: string;
  status: 'pending' | 'validating' | 'building' | 'testing' | 'staging' | 'approved' | 'merged' | 'failed' | 'cancelled';
  description: string;
  paths: string[];
  priority: 'low' | 'normal' | 'high' | 'critical';
  branch_name?: string;
  pr_url?: string;
  staging_url?: string;
  workflow_run_id?: string;
  idempotency_key: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  approvals_required: number;
  approvals_received: number;
  error_message?: string;
  proof_artifacts: string[];
}

interface BuilderConfig {
  github: {
    token: string;
    owner: string;
    repo: string;
    workflow_file: string;
  };
  limits: {
    max_concurrent_proposals: number;
    max_daily_proposals_per_user: number;
    max_file_changes_per_proposal: number;
  };
  approval: {
    required_approvers: string[];
    auto_merge_enabled: boolean;
  };
}

export class BuilderService {
  private safeExecutor: SafeExecutor;
  private commandParser: SophiaCommandParser;
  private config: BuilderConfig;
  private proposals: Map<string, BuilderProposal> = new Map();

  constructor(config: BuilderConfig) {
    this.config = config;
    this.safeExecutor = new SafeExecutor({
      maxCallsPerSession: config.limits.max_concurrent_proposals,
      maxCallsPerTool: 10,
      maxCallsPerMinute: 30,
      maxRetryAttempts: 2,
      circuitBreakerThreshold: 5
    } as Partial<SafeExecutionConfig>);
    this.commandParser = new SophiaCommandParser();
  }

  /**
   * Process a chat message and handle builder commands
   */
  async processChatMessage(
    message: string,
    userId: string,
    context: {
      conversationId?: string;
      sessionId?: string;
      timestamp?: string;
    } = {}
  ): Promise<{
    handled: boolean;
    response?: string;
    proposal?: BuilderProposal;
    suggestions?: string[];
    error?: string;
  }> {
    try {
      // Parse command from message
      const parseResult = await this.commandParser.parseCommand(message, userId, context.sessionId);
      
      if (!parseResult.success) {
        if (parseResult.errors.length === 0) {
          // Not a sophia command
          return { handled: false };
        }
        
        return {
          handled: true,
          error: parseResult.errors.join(', '),
          suggestions: parseResult.suggestions
        };
      }

      if (!parseResult.command) {
        return { handled: false };
      }

      // Handle different command types
      switch (parseResult.command.command) {
        case BuilderCommand.PROPOSE:
          return await this.handleProposeCommand(parseResult.command, userId, context);
        
        case BuilderCommand.STATUS:
          return await this.handleStatusCommand(parseResult.command, userId);
        
        case BuilderCommand.APPROVE:
          return await this.handleApproveCommand(parseResult.command, userId);
        
        case BuilderCommand.CANCEL:
          return await this.handleCancelCommand(parseResult.command, userId);
        
        default:
          return {
            handled: true,
            error: `Unknown builder command type: ${parseResult.command.command}`,
            suggestions: [
              '@sophia propose "description" paths="src/app.ts"',
              '@sophia status proposal-id',
              '@sophia approve proposal-id'
            ]
          };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      return {
        handled: true,
        error: `Builder service error: ${errorMessage}`,
        suggestions: [
          'Try rephrasing your command',
          'Use @sophia help for available commands',
          'Check command syntax and try again'
        ]
      };
    }
  }

  /**
   * Handle proposal commands - the core builder functionality
   */
  private async handleProposeCommand(
    command: ParsedCommand,
    userId: string,
    context: any
  ): Promise<{
    handled: boolean;
    response?: string;
    proposal?: BuilderProposal;
    error?: string;
  }> {
    if (command.command !== BuilderCommand.PROPOSE) {
      throw new Error('Invalid command type for proposal handler');
    }

    // Generate unique identifiers
    const proposalId = `proposal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const idempotencyKey = `${userId}-${Date.now()}-${this.hashString(command.description + (command.paths || []).join(','))}`;

    // Check for duplicate proposals
    const existingProposal = Array.from(this.proposals.values()).find(
      p => p.idempotency_key === idempotencyKey
    );

    if (existingProposal) {
      return {
        handled: true,
        response: `Duplicate proposal detected. Existing proposal: ${existingProposal.id} (Status: ${existingProposal.status})`,
        proposal: existingProposal
      };
    }

    // Validate rate limits
    const rateLimitCheck = await this.checkRateLimit(userId);
    if (!rateLimitCheck.allowed) {
      return {
        handled: true,
        error: `Rate limit exceeded: ${rateLimitCheck.reason}`
      };
    }

    // Create proposal record
    const proposal: BuilderProposal = {
      id: proposalId,
      status: 'pending',
      description: command.description,
      paths: command.paths || [],
      priority: (command.options.priority as 'low' | 'normal' | 'high' | 'critical') || 'normal',
      idempotency_key: idempotencyKey,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: userId,
      approvals_required: this.calculateRequiredApprovals(command),
      approvals_received: 0,
      proof_artifacts: []
    };

    this.proposals.set(proposalId, proposal);

    // Execute the proposal workflow
    try {
      const executionContext: ExecutionContext = {
        sessionId: context.sessionId || 'builder-session',
        userId,
        toolName: 'github-workflow-dispatch',
        idempotencyKey
      };

      const workflowResult = await this.safeExecutor.execute(
        async (input: any, ctx: ExecutionContext) => await this.dispatchProposalWorkflow(proposal),
        {},
        executionContext
      );

      // Update proposal with workflow results
      proposal.status = 'validating';
      if (workflowResult.success && workflowResult.result) {
        const result = workflowResult.result as GitHubAPIResponse;
        proposal.workflow_run_id = result.run_id?.toString();
      }
      proposal.updated_at = new Date().toISOString();

      // Generate proof artifact
      await this.generateProposalProof(proposal, 'initiated');

      return {
        handled: true,
        response: this.formatProposalResponse(proposal, workflowResult.result as GitHubAPIResponse),
        proposal
      };

    } catch (error) {
      proposal.status = 'failed';
      proposal.error_message = error instanceof Error ? error.message : 'Unknown error';
      proposal.updated_at = new Date().toISOString();

      await this.generateProposalProof(proposal, 'failed');

      return {
        handled: true,
        error: `Failed to initiate proposal: ${proposal.error_message}`,
        proposal
      };
    }
  }

  /**
   * Dispatch GitHub workflow for proposal
   */
  private async dispatchProposalWorkflow(proposal: BuilderProposal): Promise<GitHubAPIResponse> {
    const workflowInputs = {
      proposal_id: proposal.id,
      description: proposal.description,
      paths: proposal.paths.join(','),
      priority: proposal.priority,
      deploy_staging: 'true',
      dry_run: 'false',
      skip_tests: 'false',
      skip_lint: 'false',
      idempotency_key: proposal.idempotency_key
    };

    // GitHub API call to dispatch workflow
    const response = await fetch(
      `https://api.github.com/repos/${this.config.github.owner}/${this.config.github.repo}/actions/workflows/${this.config.github.workflow_file}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.github.token}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ref: 'main',
          inputs: workflowInputs
        })
      }
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`GitHub API error: ${response.status} - ${error}`);
    }

    // Note: GitHub workflow dispatch doesn't return run_id immediately
    // We would need to query the runs API to get the actual run_id
    return {
      status: response.status,
      message: 'Workflow dispatched successfully'
    };
  }

  /**
   * Handle status command
   */
  private async handleStatusCommand(
    command: ParsedCommand,
    userId: string
  ): Promise<{
    handled: boolean;
    response?: string;
    error?: string;
  }> {
    const proposalId = command.description === 'all' ? undefined : command.description;
    
    if (!proposalId) {
      // Return status of all user's proposals
      const userProposals = Array.from(this.proposals.values())
        .filter(p => p.created_by === userId)
        .slice(0, 5); // Limit to recent 5

      if (userProposals.length === 0) {
        return {
          handled: true,
          response: "No active proposals found. Use `@sophia propose \"description\" paths=\"...\"` to create one."
        };
      }

      const statusSummary = userProposals
        .map(p => `• ${p.id}: ${p.status} - "${p.description}"`)
        .join('\n');

      return {
        handled: true,
        response: `Your recent proposals:\n${statusSummary}`
      };
    }

    // Get specific proposal status
    const proposal = this.proposals.get(proposalId);
    if (!proposal) {
      return {
        handled: true,
        error: `Proposal not found: ${proposalId}`
      };
    }

    // Check permissions
    if (proposal.created_by !== userId && !this.isApprover(userId)) {
      return {
        handled: true,
        error: 'You can only view status of your own proposals'
      };
    }

    return {
      handled: true,
      response: this.formatDetailedProposalStatus(proposal)
    };
  }

  /**
   * Handle approve command (for authorized users)
   */
  private async handleApproveCommand(
    command: ParsedCommand,
    userId: string
  ): Promise<{
    handled: boolean;
    response?: string;
    error?: string;
  }> {
    if (!this.isApprover(userId)) {
      return {
        handled: true,
        error: 'You are not authorized to approve proposals'
      };
    }

    const proposalId = command.description;
    if (!proposalId) {
      return {
        handled: true,
        error: 'Please specify proposal ID: @sophia approve <proposal-id>'
      };
    }

    const proposal = this.proposals.get(proposalId);
    if (!proposal) {
      return {
        handled: true,
        error: `Proposal not found: ${proposalId}`
      };
    }

    if (proposal.status !== 'staging') {
      return {
        handled: true,
        error: `Cannot approve proposal in status: ${proposal.status}. Proposal must be in 'staging' status.`
      };
    }

    // Record approval
    proposal.approvals_received++;
    proposal.updated_at = new Date().toISOString();

    if (proposal.approvals_received >= proposal.approvals_required) {
      proposal.status = 'approved';
      await this.generateProposalProof(proposal, 'approved');
    }

    return {
      handled: true,
      response: `Proposal ${proposalId} approved by ${userId}. ${proposal.approvals_received}/${proposal.approvals_required} approvals received.`
    };
  }

  /**
   * Handle cancel command
   */
  private async handleCancelCommand(
    command: ParsedCommand,
    userId: string
  ): Promise<{
    handled: boolean;
    response?: string;
    error?: string;
  }> {
    const proposalId = command.description;
    if (!proposalId) {
      return {
        handled: true,
        error: 'Please specify proposal ID: @sophia cancel <proposal-id>'
      };
    }

    const proposal = this.proposals.get(proposalId);
    if (!proposal) {
      return {
        handled: true,
        error: `Proposal not found: ${proposalId}`
      };
    }

    // Check permissions
    if (proposal.created_by !== userId && !this.isApprover(userId)) {
      return {
        handled: true,
        error: 'You can only cancel your own proposals'
      };
    }

    if (['approved', 'merged'].includes(proposal.status)) {
      return {
        handled: true,
        error: `Cannot cancel proposal in status: ${proposal.status}`
      };
    }

    proposal.status = 'cancelled';
    proposal.updated_at = new Date().toISOString();

    await this.generateProposalProof(proposal, 'cancelled');

    return {
      handled: true,
      response: `Proposal ${proposalId} has been cancelled.`
    };
  }

  /**
   * Generate proof artifacts for proposals
   */
  private async generateProposalProof(
    proposal: BuilderProposal,
    stage: 'initiated' | 'approved' | 'cancelled' | 'failed'
  ): Promise<void> {
    const timestamp = new Date().toISOString();
    const proofData = {
      builder_proposal_proof: {
        proposal_id: proposal.id,
        stage,
        timestamp,
        proposal_state: {
          ...proposal,
          // Remove sensitive data
          proof_artifacts: proposal.proof_artifacts.length
        },
        workflow_context: {
          idempotency_key: proposal.idempotency_key,
          safe_executor_used: true,
          rate_limits_enforced: true
        },
        compliance: {
          ceo_gated: true,
          approval_required: proposal.approvals_required > 0,
          github_workflow_dispatched: !!proposal.workflow_run_id
        }
      }
    };

    // In a real implementation, this would write to a proof storage system
    const proofArtifact = `proofs/builder/${proposal.id}-${stage}-${Date.now()}.json`;
    proposal.proof_artifacts.push(proofArtifact);

    console.log(`Generated proof artifact: ${proofArtifact}`, proofData);
  }

  /**
   * Utility methods
   */
  private calculateRequiredApprovals(command: ParsedCommand): number {
    if (command.options?.priority === 'critical') return 2;
    if (command.paths && command.paths.some((path: string) => path.includes('infra') || path.includes('.github'))) return 2;
    return 1;
  }

  private async checkRateLimit(userId: string): Promise<{ allowed: boolean; reason?: string }> {
    const userProposals = Array.from(this.proposals.values())
      .filter(p => p.created_by === userId);

    const todayProposals = userProposals.filter(p => {
      const createdDate = new Date(p.created_at);
      const today = new Date();
      return createdDate.toDateString() === today.toDateString();
    });

    if (todayProposals.length >= this.config.limits.max_daily_proposals_per_user) {
      return {
        allowed: false,
        reason: `Daily limit exceeded (${this.config.limits.max_daily_proposals_per_user})`
      };
    }

    const activeProposals = userProposals.filter(p => 
      !['merged', 'cancelled', 'failed'].includes(p.status)
    );

    if (activeProposals.length >= this.config.limits.max_concurrent_proposals) {
      return {
        allowed: false,
        reason: `Too many active proposals (max: ${this.config.limits.max_concurrent_proposals})`
      };
    }

    return { allowed: true };
  }

  private isApprover(userId: string): boolean {
    return this.config.approval.required_approvers.includes(userId);
  }

  private hashString(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(36);
  }

  private formatProposalResponse(proposal: BuilderProposal, workflowResult: GitHubAPIResponse): string {
    return `🤖 **Proposal Initiated**

**ID**: \`${proposal.id}\`
**Description**: ${proposal.description}
**Paths**: ${proposal.paths.join(', ')}
**Priority**: ${proposal.priority}
**Status**: ${proposal.status}

**Next Steps**:
1. Validation and branch creation
2. Automated code changes
3. Linting and testing
4. Staging deployment
5. CEO approval required (${proposal.approvals_required} approval(s) needed)

Use \`@sophia status ${proposal.id}\` to track progress.`;
  }

  private formatDetailedProposalStatus(proposal: BuilderProposal): string {
    const statusEmojis = {
      pending: '⏳',
      validating: '🔍',
      building: '🔨',
      testing: '🧪',
      staging: '🚀',
      approved: '✅',
      merged: '🎉',
      failed: '❌',
      cancelled: '🚫'
    };

    const emoji = statusEmojis[proposal.status] || '❓';
    
    return `${emoji} **Proposal Status**

**ID**: \`${proposal.id}\`
**Status**: ${proposal.status}
**Description**: ${proposal.description}
**Paths**: ${proposal.paths.join(', ')}
**Priority**: ${proposal.priority}

**Approvals**: ${proposal.approvals_received}/${proposal.approvals_required}
**Created**: ${new Date(proposal.created_at).toLocaleString()}
**Updated**: ${new Date(proposal.updated_at).toLocaleString()}
**Created By**: ${proposal.created_by}

${proposal.pr_url ? `**PR**: ${proposal.pr_url}` : ''}
${proposal.staging_url ? `**Staging**: ${proposal.staging_url}` : ''}
${proposal.error_message ? `**Error**: ${proposal.error_message}` : ''}

**Proof Artifacts**: ${proposal.proof_artifacts.length} generated`;
  }

  /**
   * Get proposal by ID (for external integrations)
   */
  getProposal(proposalId: string): BuilderProposal | undefined {
    return this.proposals.get(proposalId);
  }

  /**
   * Get all proposals (for admin/monitoring)
   */
  getAllProposals(): BuilderProposal[] {
    return Array.from(this.proposals.values());
  }

  /**
   * Update proposal status (for webhook integration)
   */
  updateProposalStatus(
    proposalId: string,
    status: BuilderProposal['status'],
    metadata?: Partial<BuilderProposal>
  ): boolean {
    const proposal = this.proposals.get(proposalId);
    if (!proposal) return false;

    proposal.status = status;
    proposal.updated_at = new Date().toISOString();
    
    if (metadata) {
      Object.assign(proposal, metadata);
    }

    return true;
  }
}

// Export singleton instance factory
export function createBuilderService(config: BuilderConfig): BuilderService {
  return new BuilderService(config);
}

// Default configuration
// Helper function to get environment variables safely
function getEnvVar(name: string, fallback: string = ''): string {
  if (typeof globalThis !== 'undefined' && (globalThis as any).process?.env) {
    return (globalThis as any).process.env[name] || fallback;
  }
  return fallback;
}

export const defaultBuilderConfig: BuilderConfig = {
  github: {
    token: getEnvVar('SOPHIA_GITHUB_TOKEN', ''),
    owner: getEnvVar('GITHUB_REPOSITORY', 'sophiaai-dev/sophia-ai-intel').split('/')[0] || 'sophiaai-dev',
    repo: getEnvVar('GITHUB_REPOSITORY', 'sophiaai-dev/sophia-ai-intel').split('/')[1] || 'sophia-ai-intel',
    workflow_file: 'sophia-builder.yml'
  },
  limits: {
    max_concurrent_proposals: 3,
    max_daily_proposals_per_user: 10,
    max_file_changes_per_proposal: 50
  },
  approval: {
    required_approvers: ['ceo', 'admin', 'lead-developer'],
    auto_merge_enabled: false
  }
};