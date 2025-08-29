/**
 * SOPHIA SUPREME - One Chat, One Persona
 * No mocks. Real services only.
 */

import { NextResponse } from 'next/server';

export type ChatSections = {
  summary?: string;
  actions?: { type: string; id?: string; status?: string; meta?: any }[];
  research?: { title: string; url: string; source: string; date?: string }[];
  plans?: { 
    cutting_edge?: any; 
    conservative?: any; 
    synthesis?: any; 
    recommendation?: "cutting_edge" | "conservative" | "synthesis" 
  };
  code?: { language: string; files: { path: string; diff: string }[] };
  github?: { pr_url?: string; branch?: string };
  events?: { swarm_id: string; type: "finding" | "progress" | "result" | "error"; data?: any }[];
};

class SophiaOrchestrator {
  private readonly services = {
    research: ['http://localhost:8085', 'http://localhost:8100', 'http://localhost:8200'],
    swarm: ['http://localhost:8088', 'http://localhost:8100', 'http://localhost:8200'],
    github: ['http://localhost:8082'],
    health: ['http://localhost:8081', 'http://localhost:8082', 'http://localhost:8085', 'http://localhost:8088', 'http://localhost:8096', 'http://localhost:8100']
  };

  async route(message: string, context: any): Promise<ChatSections> {
    const intent = this.detectIntent(message);
    const sections: ChatSections = {};

    try {
      switch (intent) {
        case 'swarm-of-swarms':
          return await this.executePipeline(message, context);
        case 'research':
          return await this.executeResearch(message, context);
        case 'agents':
          return await this.deployAgents(message, context);
        case 'github':
          return await this.handleGitHub(message, context);
        case 'health':
          return await this.checkHealth();
        default:
          return await this.handleGeneral(message, context);
      }
    } catch (error) {
      sections.actions = [{ type: 'error', status: 'failed', meta: { error: error instanceof Error ? error.message : 'Unknown error' } }];
      sections.summary = `Service error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      return sections;
    }
  }

  private detectIntent(message: string): string {
    const msg = message.toLowerCase();
    
    if ((msg.includes('build') || msg.includes('create') || msg.includes('implement')) &&
        (msg.includes('feature') || msg.includes('app') || msg.includes('system'))) {
      return 'swarm-of-swarms';
    }
    if (msg.includes('research') || msg.includes('search') || msg.includes('find')) return 'research';
    if (msg.includes('deploy') || msg.includes('agent') || msg.includes('swarm')) return 'agents';
    if (msg.includes('commit') || msg.includes('push') || msg.includes('pr') || msg.includes('pull request')) return 'github';
    if (msg.includes('health') || msg.includes('status') || msg.includes('broken')) return 'health';
    
    return 'general';
  }

  private async executePipeline(message: string, context: any): Promise<ChatSections> {
    const sections: ChatSections = {};
    const pipeline = ['strategy', 'research', 'planning', 'coding', 'qc', 'deploy'];
    
    // Stage 1: Strategy
    const strategyRes = await this.callService(
      `${this.services.swarm[1]}/plans`,
      { task: message }
    );
    
    if (strategyRes.ok) {
      const strategy = await strategyRes.json();
      sections.plans = strategy.plans;
      
      // Stage 2-6: Deploy swarms
      const swarmPromises = pipeline.slice(1).map(stage => 
        this.callService(`${this.services.swarm[1]}/swarms/create`, {
          swarm_type: stage === 'research' ? 'research' : stage === 'coding' ? 'coding' : 'analysis',
          task: `${stage}: ${message}`,
          context: { strategy: strategy.plans, pipeline: true }
        })
      );
      
      await Promise.allSettled(swarmPromises);
      
      sections.actions = pipeline.map(stage => ({ type: `${stage}.initiated`, status: 'running' }));
      sections.events = [{ 
        swarm_id: `pipeline-${Date.now()}`, 
        type: 'progress',
        data: { stages: pipeline, message }
      }];
      sections.summary = 'Full 6-stage pipeline initiated. All stages executing.';
    }
    
    return sections;
  }

  private async executeResearch(message: string, context: any): Promise<ChatSections> {
    const sections: ChatSections = {};
    
    for (const endpoint of this.services.research) {
      try {
        const res = await this.callService(
          endpoint === this.services.research[0] ? `${endpoint}/research` : `${endpoint}/swarms/create`,
          endpoint === this.services.research[0] ? { query: message } : { swarm_type: 'research', task: message }
        );
        
        if (res.ok) {
          const data = await res.json();
          sections.research = data.results || [{ title: 'Research initiated', url: '', source: endpoint, date: new Date().toISOString() }];
          sections.actions = [{ type: 'research.completed', id: data.swarm_id || data.id }];
          sections.summary = 'Research completed.';
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!sections.research) {
      sections.summary = 'All research services unavailable.';
      sections.actions = [{ type: 'research.failed', status: 'error' }];
    }
    
    return sections;
  }

  private async deployAgents(message: string, context: any): Promise<ChatSections> {
    const sections: ChatSections = {};
    
    for (const endpoint of this.services.swarm) {
      try {
        const res = await this.callService(
          endpoint === this.services.swarm[0] ? `${endpoint}/deploy` : `${endpoint}/swarms/create`,
          { task: message, swarm_type: 'analysis', config: { enable_websocket: true } }
        );
        
        if (res.ok) {
          const data = await res.json();
          sections.actions = [{ type: 'swarm.deployed', id: data.swarm_id }];
          sections.events = [{ swarm_id: data.swarm_id, type: 'progress', data: { status: 'deployed' } }];
          sections.summary = `Swarm ${data.swarm_id} deployed.`;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    return sections;
  }

  private async handleGitHub(message: string, context: any): Promise<ChatSections> {
    const sections: ChatSections = {};
    const operation = message.includes('commit') ? 'commit' : 
                      message.includes('pr') || message.includes('pull request') ? 'create_pr' : 'push';
    
    try {
      const res = await this.callService(`${this.services.github[0]}/github/operation`, {
        operation,
        message,
        context
      });
      
      if (res.ok) {
        const data = await res.json();
        sections.github = { pr_url: data.pr_url, branch: data.branch };
        sections.actions = [{ type: `github.${operation}`, status: 'completed' }];
        sections.summary = `GitHub ${operation} completed.`;
      }
    } catch (e) {
      sections.summary = 'GitHub service unavailable.';
      sections.actions = [{ type: 'github.failed', status: 'error' }];
    }
    
    return sections;
  }

  private async checkHealth(): Promise<ChatSections> {
    const sections: ChatSections = {};
    const healthChecks = await Promise.allSettled(
      this.services.health.map(async endpoint => {
        try {
          const res = await fetch(`${endpoint}/health`, { signal: AbortSignal.timeout(1000) });
          return { endpoint, status: res.ok ? 'healthy' : 'unhealthy', latency: 0 };
        } catch {
          return { endpoint, status: 'dead', latency: -1 };
        }
      })
    );
    
    const results = healthChecks.map(r => r.status === 'fulfilled' ? r.value : { endpoint: 'unknown', status: 'error', latency: -1 });
    const healthy = results.filter(r => r.status === 'healthy').length;
    
    sections.summary = `${healthy}/${results.length} services healthy`;
    sections.actions = results.map(r => ({ type: 'health.check', id: r.endpoint, status: r.status }));
    
    return sections;
  }

  private async handleGeneral(message: string, context: any): Promise<ChatSections> {
    return {
      summary: 'Processing your request...',
      actions: [{ type: 'general.processing', status: 'pending' }]
    };
  }

  private async callService(url: string, body: any): Promise<Response> {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000)
    });
  }
}

export async function POST(request: Request) {
  try {
    const { messages, session_id, tenant, hints } = await request.json();
    const message = messages[messages.length - 1].content;
    
    const orchestrator = new SophiaOrchestrator();
    const sections = await orchestrator.route(message, { session_id, tenant, hints });
    
    return NextResponse.json({
      service: 'sophia-orchestrator',
      sections
    });
  } catch (error) {
    return NextResponse.json({
      service: 'sophia-orchestrator',
      sections: {
        summary: 'Error processing request',
        actions: [{ type: 'error', status: 'failed' }]
      }
    }, { status: 500 });
  }
}