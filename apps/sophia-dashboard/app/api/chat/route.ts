/**
 * SOPHIA COMPLETE - One File, One Truth
 * Everything in one place. No bullshit.
 */

import { NextResponse } from 'next/server';

// Types
interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  metadata?: any;
}

interface ChatRequest {
  message: string;
  sessionId?: string;
  context?: any;
}

// API Provider Configuration
const API_KEYS = {
  perplexity: process.env.PERPLEXITY_API_KEY || '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',
  tavily: process.env.TAVILY_API_KEY || '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',
  openrouter: process.env.OPENROUTER_API_KEY || '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',
  brave: process.env.BRAVE_API_KEY || 'BSApz0194z7SG6DplmVozl7ttFOi0Eo',
  openai: process.env.OPENAI_API_KEY,
  anthropic: process.env.ANTHROPIC_API_KEY,
};

// In-memory session storage (replace with Redis in production)
const sessions = new Map<string, Message[]>();

class SophiaCore {
  /**
   * Classify query intent
   */
  private classifyQuery(query: string): string {
    const q = query.toLowerCase();
    
    if (/\b(code|github|repo|library|npm|pip|framework|api)\b/.test(q)) return 'code';
    if (/\b(search|find|research|latest|news|current)\b/.test(q)) return 'research';
    if (/\b(who|what|when|where|why|how|explain)\b/.test(q)) return 'knowledge';
    if (/\b(build|create|implement|design|plan)\b/.test(q)) return 'planning';
    if (/\b(analyze|compare|evaluate|assess)\b/.test(q)) return 'analysis';
    
    return 'general';
  }

  /**
   * Call Perplexity for research
   */
  private async callPerplexity(query: string): Promise<string | null> {
    if (!API_KEYS.perplexity) return null;
    
    try {
      const response = await fetch('https://api.perplexity.ai/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_KEYS.perplexity}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'sonar-small-chat',
          messages: [{ role: 'user', content: query }]
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.choices?.[0]?.message?.content || null;
      }
    } catch (e) {
      console.error('Perplexity error:', e);
    }
    return null;
  }

  /**
   * Call Tavily for web search
   */
  private async callTavily(query: string): Promise<string | null> {
    if (!API_KEYS.tavily) return null;
    
    try {
      const response = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: API_KEYS.tavily,
          query: query,
          search_depth: 'advanced',
          max_results: 3
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.answer || data.results) {
          let result = data.answer || '';
          if (data.results?.length) {
            result += '\n\nSources:\n' + data.results.slice(0, 3).map((r: any) => 
              `- ${r.title}: ${r.url}`
            ).join('\n');
          }
          return result;
        }
      }
    } catch (e) {
      console.error('Tavily error:', e);
    }
    return null;
  }

  /**
   * Call OpenRouter for LLM access
   */
  private async callOpenRouter(query: string, model = 'anthropic/claude-3-haiku'): Promise<string | null> {
    if (!API_KEYS.openrouter) return null;
    
    try {
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_KEYS.openrouter}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: model,
          messages: [{ role: 'user', content: query }]
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.choices?.[0]?.message?.content || null;
      }
    } catch (e) {
      console.error('OpenRouter error:', e);
    }
    return null;
  }

  /**
   * Call local MCP services
   */
  private async callMCP(query: string, type: string): Promise<string | null> {
    try {
      // Try MCP Research for GitHub/code queries
      if (type === 'code') {
        const response = await fetch(`http://localhost:8085/search/github?q=${encodeURIComponent(query)}&limit=3`);
        if (response.ok) {
          const data = await response.json();
          if (data.results?.length) {
            return data.results.map((r: any) => 
              `📦 ${r.title}\n  ${r.summary}\n  ⭐ ${r.metadata?.stars || 0} | ${r.url}`
            ).join('\n\n');
          }
        }
      }
      
      // Try general research
      const researchResponse = await fetch('http://localhost:8085/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: 3 })
      });
      
      if (researchResponse.ok) {
        const data = await researchResponse.json();
        if (data.results?.length) {
          return data.results.map((r: any) => `- ${r.title}: ${r.summary}`).join('\n');
        }
      }
    } catch (e) {
      // MCP not available
    }
    return null;
  }

  /**
   * Generate response using best available provider
   */
  async generateResponse(query: string, sessionId: string): Promise<{
    response: string;
    provider: string;
    metadata: any;
  }> {
    const queryType = this.classifyQuery(query);
    let response = null;
    let provider = 'none';
    
    // Try providers based on query type
    if (queryType === 'research' || queryType === 'knowledge') {
      // Try Perplexity first for research
      response = await this.callPerplexity(query);
      if (response) provider = 'perplexity';
      
      // Fallback to Tavily
      if (!response) {
        response = await this.callTavily(query);
        if (response) provider = 'tavily';
      }
    }
    
    if (queryType === 'code') {
      // Try MCP for code searches
      response = await this.callMCP(query, 'code');
      if (response) provider = 'mcp-github';
      
      // Fallback to Tavily
      if (!response) {
        response = await this.callTavily(`${query} github repository`);
        if (response) provider = 'tavily';
      }
    }
    
    // For other types or if above failed, try OpenRouter
    if (!response && queryType !== 'code') {
      response = await this.callOpenRouter(query);
      if (response) provider = 'openrouter';
    }
    
    // Final fallback to MCP
    if (!response) {
      response = await this.callMCP(query, 'general');
      if (response) provider = 'mcp-research';
    }
    
    // Ultimate fallback
    if (!response) {
      response = this.getFallbackResponse(query, queryType);
      provider = 'fallback';
    }
    
    return {
      response,
      provider,
      metadata: {
        queryType,
        sessionId,
        timestamp: new Date().toISOString()
      }
    };
  }

  /**
   * Fallback responses when no API available
   */
  private getFallbackResponse(query: string, queryType: string): string {
    const responses: Record<string, string> = {
      code: `I understand you're looking for code related to "${query}". Try searching GitHub directly or check npm/PyPI for packages.`,
      research: `I'd research "${query}" for you, but external services are unavailable. Check recent sources directly.`,
      knowledge: `Regarding "${query}": I can provide general information, though real-time data needs active APIs.`,
      planning: `I'll help you plan "${query}" using architectural best practices and proven patterns.`,
      analysis: `For analyzing "${query}", I'll use my built-in knowledge since external services are unavailable.`,
      general: `Processing your request about "${query}". External services are limited but I'll do my best.`
    };
    
    return responses[queryType] || `I received: "${query}". How can I help you today?`;
  }
}

// Initialize Sophia
const sophia = new SophiaCore();

/**
 * Main chat endpoint
 */
export async function POST(request: Request) {
  try {
    const body: ChatRequest = await request.json();
    const { message, sessionId = 'default', context = {} } = body;
    
    if (!message) {
      return NextResponse.json(
        { error: 'Message required' },
        { status: 400 }
      );
    }
    
    // Get or create session
    if (!sessions.has(sessionId)) {
      sessions.set(sessionId, []);
    }
    const conversation = sessions.get(sessionId)!;
    
    // Add user message
    conversation.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });
    
    // Generate response
    const result = await sophia.generateResponse(message, sessionId);
    
    // Add assistant response
    conversation.push({
      role: 'assistant',
      content: result.response,
      timestamp: new Date().toISOString(),
      metadata: result.metadata
    });
    
    // Keep only last 20 messages per session
    if (conversation.length > 20) {
      conversation.splice(0, conversation.length - 20);
    }
    
    return NextResponse.json({
      message: result.response,
      sessionId,
      provider: result.provider,
      metadata: result.metadata,
      conversationLength: conversation.length
    });
    
  } catch (error) {
    console.error('Chat error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * Get conversation history
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const sessionId = searchParams.get('sessionId') || 'default';
  
  const conversation = sessions.get(sessionId) || [];
  
  return NextResponse.json({
    sessionId,
    messages: conversation,
    total: conversation.length
  });
}

/**
 * Health check
 */
export async function HEAD() {
  return new Response(null, { status: 200 });
}