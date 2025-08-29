import { NextResponse } from 'next/server';

// Map agent types to swarm types
const agentToSwarmTypeMap: Record<string, string> = {
  'Research Agent': 'research',
  'Code Agent': 'coding',
  'Analysis Agent': 'analysis',
  'Planning Agent': 'planning'
};

export async function POST(request: Request) {
  try {
    const { action, agentType, task } = await request.json();

    if (action === 'deploy') {
      // Convert agent type to swarm type
      const swarmType = agentToSwarmTypeMap[agentType] || 'research';
      
      // Actually create a swarm using the unified swarm service
      try {
        const swarmResponse = await fetch('http://localhost:8100/swarms/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            swarm_type: swarmType,
            task: task || `Execute ${agentType} operations`,
            context: {
              source: 'dashboard',
              agentType: agentType,
              timestamp: new Date().toISOString()
            }
          })
        });

        if (swarmResponse.ok) {
          const swarmData = await swarmResponse.json();
          
          return NextResponse.json({
            success: true,
            agentId: swarmData.swarm_id,
            agentType,
            status: 'deployed',
            message: `${agentType} deployed successfully! Swarm ID: ${swarmData.swarm_id}`,
            task,
            swarmId: swarmData.swarm_id,
            swarmType: swarmType,
            viewUrl: `/swarms/${swarmData.swarm_id}`
          });
        }
      } catch (error) {
        console.error('Failed to create swarm:', error);
      }

      // Fallback to mock if swarm service is unavailable
      return NextResponse.json({
        success: true,
        agentId: `agent-${Date.now()}`,
        agentType,
        status: 'deployed',
        message: `${agentType} deployed (mock mode)`,
        task
      });
    }

    if (action === 'list') {
      // Get real swarms from the unified service
      try {
        const swarmsResponse = await fetch('http://localhost:8100/swarms');
        if (swarmsResponse.ok) {
          const swarms = await swarmsResponse.json();
          
          // Transform swarms to agent format
          const agents = swarms.map((swarm: any) => ({
            id: swarm.swarm_id,
            type: swarm.swarm_type,
            status: swarm.status,
            progress: swarm.progress,
            task: swarm.current_task,
            lastActive: new Date().toISOString()
          }));
          
          return NextResponse.json({ agents });
        }
      } catch (error) {
        console.error('Failed to list swarms:', error);
      }

      // Fallback to mock agents
      return NextResponse.json({
        agents: [
          { id: 'agent-1', type: 'Research Agent', status: 'idle', lastActive: new Date().toISOString() },
          { id: 'agent-2', type: 'Code Agent', status: 'idle', lastActive: new Date().toISOString() }
        ]
      });
    }

    if (action === 'status') {
      const { swarmId } = await request.json();
      
      try {
        const statusResponse = await fetch(`http://localhost:8100/swarms/${swarmId}/status`);
        if (statusResponse.ok) {
          const status = await statusResponse.json();
          return NextResponse.json(status);
        }
      } catch (error) {
        console.error('Failed to get swarm status:', error);
      }
      
      return NextResponse.json({ error: 'Swarm not found' }, { status: 404 });
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to process agent request' }, { status: 500 });
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');
  
  // Handle activity feed request
  if (action === 'activity') {
    try {
      // Get recent activities from WebSocket hub or swarm service
      const activities = [];
      
      // Try to get swarm activities
      try {
        const swarmsResponse = await fetch('http://localhost:8100/swarms');
        if (swarmsResponse.ok) {
          const swarms = await swarmsResponse.json();
          swarms.forEach((swarm: any) => {
            activities.push({
              id: `swarm-${swarm.swarm_id}`,
              timestamp: new Date().toISOString(),
              type: 'agent',
              agent_id: swarm.swarm_id,
              agent_type: swarm.swarm_type,
              action: swarm.current_task || 'Processing',
              status: swarm.status,
              progress: swarm.progress
            });
          });
        }
      } catch (error) {
        console.error('Failed to get swarm activities:', error);
      }
      
      return NextResponse.json({ activities });
    } catch (error) {
      return NextResponse.json({ activities: [] });
    }
  }
  
  // Default: Get available agents from the unified swarm service
  try {
    const agentsResponse = await fetch('http://localhost:8100/agents');
    if (agentsResponse.ok) {
      const agents = await agentsResponse.json();
      
      // Group by type and return in dashboard format
      const agentTypes = new Map();
      agents.forEach((agent: any) => {
        if (!agentTypes.has(agent.type)) {
          agentTypes.set(agent.type, {
            type: agent.name,
            icon: getIconForType(agent.type),
            description: agent.capabilities.join(', '),
            capabilities: agent.capabilities
          });
        }
      });
      
      return NextResponse.json({
        availableAgents: Array.from(agentTypes.values())
      });
    }
  } catch (error) {
    console.error('Failed to get available agents:', error);
  }

  // Fallback to default agents
  return NextResponse.json({
    availableAgents: [
      {
        type: 'Research Agent',
        icon: '🔍',
        description: 'Autonomous web research and data gathering',
        capabilities: ['Web search', 'Data extraction', 'Report generation']
      },
      {
        type: 'Code Agent',
        icon: '💻',
        description: 'Automated code generation and debugging',
        capabilities: ['Code generation', 'Bug fixing', 'Code review']
      },
      {
        type: 'Analysis Agent',
        icon: '📊',
        description: 'Data analysis and insights generation',
        capabilities: ['Data processing', 'Statistical analysis', 'Visualization']
      },
      {
        type: 'Planning Agent',
        icon: '📋',
        description: 'Strategic planning with multiple perspectives',
        capabilities: ['Cutting-edge solutions', 'Conservative approaches', 'Synthesis']
      }
    ]
  });
}

function getIconForType(type: string): string {
  const iconMap: Record<string, string> = {
    'orchestrator': '🎯',
    'developer': '💻',
    'researcher': '🔍',
    'analyzer': '📊',
    'planner': '📋',
    'quality': '✅',
    'infrastructure': '🔧',
    'mediator': '🤝'
  };
  return iconMap[type] || '🤖';
}