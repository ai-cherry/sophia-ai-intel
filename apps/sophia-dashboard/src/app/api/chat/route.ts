import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { message, context, sessionId, activeTab, enableWebSocket } = await request.json();

    // Enhanced context for Sophia Brain
    const enhancedContext = {
      ...context,
      dashboard: {
        activeTab: activeTab || 'chat',
        sessionId: sessionId || `session_${Date.now()}`,
        timestamp: new Date().toISOString()
      },
      services: {
        unified_swarm: 'http://localhost:8100',
        mcp_context: 'http://localhost:8081',
        github: 'http://localhost:8082'
      }
    };

    // SOPHIA SUPREME - The One True Orchestrator
    try {
      const sophiaSupremeResponse = await fetch('http://localhost:8300/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          context: enhancedContext
        })
      });

      if (sophiaSupremeResponse.ok) {
        const data = await sophiaSupremeResponse.json();
        
        // Return structured response for new dashboard
        return NextResponse.json({
          message: {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: data.response || data.message || 'Processing your request...',
            metadata: {
              actions: data.actions_taken || [],
              services: data.services_used || [],
              research: data.research_results || [],
              code: data.code_artifacts || [],
              plans: data.planning_output || null,
              agents: data.agent_activities || [],
              github_pr: data.github_pr || null
            },
            timestamp: new Date().toISOString()
          },
          orchestrator: 'Sophia Supreme',
          sessionId: enhancedContext.dashboard.sessionId
        });
      }
    } catch (error) {
      console.log('Connecting to Sophia Supreme...');
    }
    
    // Fallback to Direct Swarm API
    try {
      const directResponse = await fetch('http://localhost:8200/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          agent_type: activeTab || 'research'
        })
      });

      if (directResponse.ok) {
        const data = await directResponse.json();
        
        return NextResponse.json({
          message: {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: data.response,
            metadata: {
              actions: ['Swarm deployed'],
              services: ['direct-swarm'],
              agents: [{ type: data.swarm_type, id: data.task_id }]
            },
            timestamp: new Date().toISOString()
          },
          orchestrator: 'Direct Swarm',
          sessionId: enhancedContext.dashboard.sessionId
        });
      }
    } catch (error) {
      console.log('Direct swarm not available, trying Sophia Brain...');
    }
    
    // Try Sophia Brain as fallback
    try {
      const sophiaResponse = await fetch('http://localhost:8099/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: message }],
          context: enhancedContext,
          capabilities: ['research', 'code', 'agents', 'github', 'analysis']
        })
      });

      if (sophiaResponse.ok) {
        const data = await sophiaResponse.json();
        
        // Process Sophia's response with full context awareness
        return NextResponse.json({
          message: {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: data.response || data.message || 'Processing your request with full neural context...',
            metadata: {
              actions: data.actions_taken || [],
              services: data.services_used || []
            },
            timestamp: new Date().toISOString()
          },
          orchestrator: 'Sophia Brain',
          sessionId: enhancedContext.dashboard.sessionId
        });
      }
    } catch (error) {
      console.log('Sophia Brain initializing, trying fallback...');
    }

    // Fallback to chat coordinator
    try {
      const coordinatorResponse = await fetch('http://localhost:8095/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: message }]
        })
      });

      if (coordinatorResponse.ok) {
        const data = await coordinatorResponse.json();
        return NextResponse.json({
          response: data.response || 'Let me process that for you.',
          timestamp: new Date().toISOString(),
          service: 'chat-coordinator'
        });
      }
    } catch (error) {
      console.log('Chat coordinator not available');
    }

    // If no services available, provide intelligent fallback responses
    const fallbackResponses: Record<string, string> = {
      'hello': 'Hello! I\'m Sophia AI. How can I assist you today?',
      'help': 'I can help you with:\n• Research and analysis\n• Code generation and debugging\n• Agent deployment for autonomous tasks\n• Deep web research\n• GitHub integration',
      'agents': 'You can deploy various AI agents:\n• Research Agent - for autonomous web research\n• Code Agent - for code generation and debugging\n• Analysis Agent - for data analysis',
      'research': 'I can conduct comprehensive research with source citations. Just tell me what topic you\'d like me to investigate.',
      'code': 'I can help generate, debug, and optimize code in any language. What would you like to build?',
      'default': `I received your message: "${message}". While my neural networks are initializing, I can still help you with basic queries. Try asking about agents, research, or code generation.`
    };

    const lowercaseMessage = message.toLowerCase();
    let response = fallbackResponses.default;
    
    for (const [key, value] of Object.entries(fallbackResponses)) {
      if (lowercaseMessage.includes(key)) {
        response = value;
        break;
      }
    }

    return NextResponse.json({
      message: {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: response,
        metadata: {},
        timestamp: new Date().toISOString()
      },
      orchestrator: 'Fallback',
      sessionId: sessionId || `session_${Date.now()}`
    });

  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { error: 'Failed to process message' },
      { status: 500 }
    );
  }
}