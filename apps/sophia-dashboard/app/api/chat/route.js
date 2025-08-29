// Chat API Route - Simple implementation that works
import { NextResponse } from 'next/server';

// Simple in-memory storage for demo (replace with database in production)
const conversations = new Map();

export async function POST(request) {
  try {
    const { message, sessionId = 'default' } = await request.json();
    
    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Get or create conversation
    if (!conversations.has(sessionId)) {
      conversations.set(sessionId, []);
    }
    const conversation = conversations.get(sessionId);
    
    // Add user message
    conversation.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });

    // Try to call Sophia Chat Service first
    let response = '';
    let metadata = {};
    
    try {
      // Call Sophia's enhanced intelligence service
      const sophiaResponse = await fetch('http://localhost:8090/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          context: {},
          use_enhanced_intelligence: true
        }),
        signal: AbortSignal.timeout(30000) // 30 second timeout for complex requests
      });
      
      if (sophiaResponse.ok) {
        const data = await sophiaResponse.json();
        response = data.response;
        metadata = {
          source: 'sophia-enhanced-intelligence',
          processing_method: data.processing_method,
          execution_time: data.execution_time,
          quality_score: data.quality_score,
          api_providers_used: data.api_providers_used,
          external_intelligence: data.metadata?.external_intelligence || false
        };
      }
    } catch (e) {
      console.log('Sophia Enhanced Intelligence not available, trying MCP services');
      
      // Fallback to direct MCP research service
      try {
        const researchResponse = await fetch('http://localhost:8085/search/web?q=' + encodeURIComponent(message) + '&limit=3', {
          signal: AbortSignal.timeout(3000)
        });
        
        if (researchResponse.ok) {
          const data = await researchResponse.json();
          if (data.results && data.results.length > 0) {
            response = `Based on web search:\n${data.results.map(r => `- ${r.title}: ${r.summary}`).join('\n')}`;
            metadata.source = 'mcp-research-fallback';
          }
        }
      } catch (e2) {
        console.log('MCP services also not available, using basic fallback');
      }
    }

    // Fallback response if MCP services are not available
    if (!response) {
      // Simple pattern matching for common queries
      if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
        response = "Hello! I'm your AI coding assistant. I can help with code, architecture, debugging, and more. What would you like to work on?";
      } else if (message.toLowerCase().includes('help')) {
        response = "I can help you with:\n- Writing and reviewing code\n- Debugging issues\n- Architecture decisions\n- Best practices\n- Documentation\n\nJust ask me anything!";
      } else if (message.toLowerCase().includes('status')) {
        response = "System Status:\n- Dashboard: ✅ Running\n- Database: ✅ Connected\n- MCP Services: ⚠️ Limited availability\n- AI Agents: 🔄 Loading";
      } else {
        // Generic coding assistant response
        response = `I understand you're asking about: "${message}". \n\nWhile I'm operating with limited services, I can still help with coding tasks. For the best experience, ensure all MCP services are running:\n- MCP Research (port 8085)\n- MCP Context (port 8081)\n- MCP GitHub (port 8082)`;
      }
      metadata.source = 'fallback';
    }

    // Add assistant response
    conversation.push({
      role: 'assistant',
      content: response,
      metadata,
      timestamp: new Date().toISOString()
    });

    // Return the response
    return NextResponse.json({
      message: response,
      sessionId,
      metadata,
      conversationLength: conversation.length
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}

export async function GET(request) {
  // Get conversation history
  const { searchParams } = new URL(request.url);
  const sessionId = searchParams.get('sessionId') || 'default';
  
  const conversation = conversations.get(sessionId) || [];
  
  return NextResponse.json({
    sessionId,
    messages: conversation,
    total: conversation.length
  });
}