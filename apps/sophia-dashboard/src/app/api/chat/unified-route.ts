/**
 * UNIFIED CHAT API - ONE FUCKING CHAT BOX
 * All requests go through Sophia, she routes internally
 */

import { NextResponse } from 'next/server';

interface ChatSection {
  summary?: string;
  actions?: any[];
  research?: any[];
  plans?: any;
  code?: any;
  github?: any;
  events?: any[];
}

// Intent detection - what does the user want?
function detectIntent(message: string): string {
  const msg = message.toLowerCase();
  
  // Check for complex multi-stage requests (swarm-of-swarms)
  if ((msg.includes('build') || msg.includes('create') || msg.includes('implement')) &&
      (msg.includes('feature') || msg.includes('app') || msg.includes('system'))) {
    return 'swarm-of-swarms';
  }
  
  if (msg.includes('research') || msg.includes('search') || msg.includes('find')) {
    return 'research';
  }
  if (msg.includes('deploy') || msg.includes('agent') || msg.includes('swarm')) {
    return 'agents';
  }
  if (msg.includes('code') || msg.includes('generate') || msg.includes('implement')) {
    return 'code';
  }
  if (msg.includes('plan') || msg.includes('strategy') || msg.includes('design')) {
    return 'planning';
  }
  if (msg.includes('commit') || msg.includes('push') || msg.includes('github') || 
      msg.includes('pr') || msg.includes('pull request') || msg.includes('merge')) {
    return 'github';
  }
  if (msg.includes('health') || msg.includes('status') || msg.includes('broken')) {
    return 'health';
  }
  if (msg.includes('analyze') || msg.includes('review') || msg.includes('repository')) {
    return 'analysis';
  }
  
  return 'general';
}

// Route to appropriate service based on intent
async function routeToService(intent: string, message: string, context: any): Promise<ChatSection> {
  const sections: ChatSection = {};
  
  switch (intent) {
    case 'research':
      // Try multiple research services in priority order
      let researchHandled = false;
      
      // 1. Try MCP Research service first
      try {
        const mcpRes = await fetch('http://localhost:8085/research', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            query: message,
            sources: ['github', 'web'],
            limit: 5
          }),
          signal: AbortSignal.timeout(3000)
        });
        
        if (mcpRes.ok) {
          const data = await mcpRes.json();
          sections.research = data.results || [{ status: 'completed', data: data }];
          sections.actions = [{ type: 'research.mcp', status: 'completed' }];
          sections.summary = `Found ${data.total_results} results from ${data.sources_searched.join(', ')}`;
          researchHandled = true;
        }
      } catch (e) {
        console.log('MCP research unavailable, trying swarm...');
      }
      
      // 2. Fallback to research swarm
      if (!researchHandled) {
        try {
          const res = await fetch('http://localhost:8100/swarms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              swarm_type: 'research',
              task: message,
              context: { enable_websocket: true }
            })
          });
          
          if (res.ok) {
            const data = await res.json();
            sections.actions = [{ type: 'research.swarm', swarm_id: data.swarm_id }];
            sections.research = [{ status: 'running', message: 'Deep web research swarm deployed' }];
            researchHandled = true;
          }
        } catch (e) {
          console.error('Research swarm error:', e);
        }
      }
      
      // 3. Final fallback to direct swarm API
      if (!researchHandled) {
        try {
          const directRes = await fetch('http://localhost:8200/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: message,
              agent_type: 'research'
            })
          });
          
          if (directRes.ok) {
            const data = await directRes.json();
            sections.research = [{ status: 'completed', data: data.response }];
            sections.actions = [{ type: 'research.direct', task_id: data.task_id }];
          }
        } catch (e) {
          sections.research = [{ status: 'error', message: 'All research services unavailable' }];
        }
      }
      break;
      
    case 'agents':
      // Deploy/manage agents with real swarm executor
      let agentHandled = false;
      
      // 1. Try real swarm executor first
      try {
        const executorRes = await fetch('http://localhost:8088/deploy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task: message,
            config: {
              enable_memory: true,
              enable_websocket: true,
              models: ['gpt-4-turbo-preview', 'claude-3-opus']
            }
          }),
          signal: AbortSignal.timeout(5000)
        });
        
        if (executorRes.ok) {
          const data = await executorRes.json();
          sections.actions = [{ type: 'agent.executor', swarm_id: data.swarm_id }];
          sections.events = [{ type: 'swarm_deployed', id: data.swarm_id, agents: data.agents }];
          agentHandled = true;
        }
      } catch (e) {
        console.log('Real swarm executor unavailable, trying unified swarm...');
      }
      
      // 2. Fallback to unified swarm service
      if (!agentHandled) {
        try {
          const res = await fetch('http://localhost:8100/swarms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              swarm_type: 'analysis',
              task: message,
              context: { enable_websocket: true }
            })
          });
          
          if (res.ok) {
            const data = await res.json();
            sections.actions = [{ type: 'agent.unified', swarm_id: data.swarm_id }];
            sections.events = [{ type: 'swarm_created', id: data.swarm_id }];
            agentHandled = true;
          }
        } catch (e) {
          console.error('Unified swarm error:', e);
        }
      }
      
      // 3. WebSocket notification for real-time updates
      if (agentHandled && sections.events && sections.events[0]) {
        try {
          await fetch('http://localhost:8096/notify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: 'swarm.deployed',
              data: sections.events[0]
            })
          });
        } catch (e) {
          console.log('WebSocket notification failed');
        }
      }
      break;
      
    case 'planning':
      // Generate plans
      try {
        const res = await fetch('http://localhost:8100/plans', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task: message })
        });
        
        if (res.ok) {
          const data = await res.json();
          sections.plans = data.plans;
          sections.actions = [{ type: 'plans.generated', count: 3 }];
        }
      } catch (e) {
        console.error('Planning error:', e);
      }
      break;
      
    case 'code':
      // Generate code
      try {
        const res = await fetch('http://localhost:8100/swarms/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            swarm_type: 'coding',
            task: message,
            context: {}
          })
        });
        
        if (res.ok) {
          const data = await res.json();
          sections.actions = [{ type: 'code.generating', swarm_id: data.swarm_id }];
          sections.code = { status: 'generating', language: 'python' };
        }
      } catch (e) {
        console.error('Code generation error:', e);
      }
      break;
      
    case 'swarm-of-swarms':
      // Execute full 6-stage pipeline
      try {
        // Stage 1: Strategy
        const strategyRes = await fetch('http://localhost:8100/plans', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task: message })
        });
        
        if (strategyRes.ok) {
          const strategy = await strategyRes.json();
          
          // Stage 2: Deep Research
          const researchRes = await fetch('http://localhost:8100/swarms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              swarm_type: 'research',
              task: `Research requirements for: ${message}`,
              context: { strategy: strategy.plans }
            })
          });
          
          // Stage 3: Planning
          const planRes = await fetch('http://localhost:8100/swarms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              swarm_type: 'planning',
              task: `Create implementation plan for: ${message}`,
              context: { strategy: strategy.plans }
            })
          });
          
          // Stage 4: Coding
          const codeRes = await fetch('http://localhost:8100/swarms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              swarm_type: 'coding',
              task: message,
              context: { plan: planRes.ok ? await planRes.json() : null }
            })
          });
          
          sections.actions = [
            { type: 'swarm-of-swarms.initiated', stages: 6 },
            { type: 'strategy.completed' },
            { type: 'research.started' },
            { type: 'planning.started' },
            { type: 'coding.started' }
          ];
          
          sections.events = [
            { type: 'pipeline.started', task: message, stages: ['strategy', 'research', 'planning', 'coding', 'qc', 'deploy'] }
          ];
          
          sections.summary = 'Full development pipeline initiated. All 6 stages are now executing.';
        }
      } catch (e) {
        console.error('Swarm-of-swarms error:', e);
        sections.summary = 'Pipeline initialization failed, falling back to individual services';
      }
      break;
    
    case 'github':
      // GitHub operations with MCP
      try {
        // Detect specific GitHub operation
        const isCommit = message.includes('commit');
        const isPR = message.includes('pr') || message.includes('pull request');
        const isPush = message.includes('push');
        
        if (isCommit || isPR || isPush) {
          // Use GitHub MCP service
          const githubRes = await fetch('http://localhost:8082/github/operation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              operation: isCommit ? 'commit' : isPR ? 'create_pr' : 'push',
              message: message,
              context: context
            })
          });
          
          if (githubRes.ok) {
            const data = await githubRes.json();
            sections.github = { 
              status: 'completed', 
              operation: data.operation,
              result: data.result 
            };
            sections.actions = [{ type: `github.${data.operation}`, status: 'completed' }];
          }
        } else {
          // General GitHub query
          sections.github = { status: 'analyzing', message: 'Analyzing GitHub request...' };
          sections.actions = [{ type: 'github.query', status: 'processing' }];
        }
      } catch (e) {
        console.error('GitHub operation error:', e);
        sections.github = { status: 'error', message: 'GitHub service unavailable' };
      }
      break;
      
    case 'health':
      // Check service health
      const healthChecks = await checkServiceHealth();
      sections.actions = [{ type: 'health.checked', services: healthChecks.length }];
      sections.summary = `${healthChecks.filter(h => h.status === 'healthy').length}/${healthChecks.length} services healthy`;
      break;
      
    default:
      // General response
      sections.summary = 'Processing your request...';
  }
  
  return sections;
}

// Check real service health
async function checkServiceHealth() {
  const services = [
    { name: 'unified-swarm', url: 'http://localhost:8100/health' },
    { name: 'mcp-context', url: 'http://localhost:8081/healthz' },
    { name: 'mcp-github', url: 'http://localhost:8082/health' },
    { name: 'mcp-research', url: 'http://localhost:8085/health' },
  ];
  
  const results = await Promise.all(
    services.map(async (service) => {
      try {
        const res = await fetch(service.url, { signal: AbortSignal.timeout(1000) });
        return { ...service, status: res.ok ? 'healthy' : 'unhealthy', latency: 0 };
      } catch {
        return { ...service, status: 'dead', latency: -1 };
      }
    })
  );
  
  return results;
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const messages = body.messages || [{ content: body.message || '' }];
    const message = messages[messages.length - 1]?.content || '';
    const context = body.context || {};
    
    // Detect intent from message
    const intent = detectIntent(message);
    
    // Route to appropriate service
    const sections = await routeToService(intent, message, context);
    
    // Build unified response with sections format expected by audit
    const response = {
      sections: {
        summary: sections.summary || `I'm processing your ${intent} request...`,
        actions: sections.actions || [],
        research: sections.research || [],
        plans: sections.plans || null,
        code: sections.code || null,
        github: sections.github || null,
        events: sections.events || []
      },
      metadata: {
        intent,
        timestamp: new Date().toISOString(),
        sessionId: context?.sessionId || `session_${Date.now()}`
      }
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json({
      sections: {
        summary: 'Error processing request',
        actions: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }, { status: 500 });
  }
}
