import Redis from 'ioredis';
import pLimit from 'p-limit';
import { WebSocket } from 'ws';
import { HybridVectorStore } from './hybrid-store';
import { logger } from './utils/logger';

interface McpClient {
  name: string;
  url: string;
  timeout: number;
}

interface MemoryContext {
  code: any[];
  research: any[];
  business: any[];
  conversation: any[];
  github?: any[];
}

interface SessionSubscription {
  sessionId: string;
  socket: WebSocket;
  lastActivity: Date;
}

export class MemoryCoordinator {
  private redis: Redis;
  private pubsub: Redis;
  private limit = pLimit(5);
  private clients: Map<string, McpClient>;
  private subscriptions: Map<string, SessionSubscription>;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(private vectorStore: HybridVectorStore) {
    this.redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
    this.pubsub = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
    this.subscriptions = new Map();

    // Initialize MCP clients
    this.clients = new Map([
      ['context', { name: 'context', url: 'http://mcp-context:8081', timeout: 5000 }],
      ['research', { name: 'research', url: 'http://mcp-research:8085', timeout: 10000 }],
      ['business', { name: 'business', url: 'http://mcp-business:8086', timeout: 5000 }],
      ['github', { name: 'github', url: 'http://mcp-github:8082', timeout: 8000 }],
    ]);
  }

  async initialize(): Promise<void> {
    // Subscribe to Redis pub/sub channels
    await this.pubsub.subscribe('memory:invalidate', 'memory:sync');
    
    this.pubsub.on('message', async (channel, message) => {
      try {
        const data = JSON.parse(message);
        await this.handlePubSubMessage(channel, data);
      } catch (error) {
        logger.error({ error, channel, message }, 'Failed to handle pub/sub message');
      }
    });

    // Start cleanup interval for stale subscriptions
    this.cleanupInterval = setInterval(() => {
      this.cleanupStaleSubscriptions();
    }, 60000); // Every minute

    logger.info('MemoryCoordinator initialized');
  }

  async getUnifiedContext(query: string, sessionId: string): Promise<MemoryContext> {
    const cacheKey = this.getCacheKey(query, sessionId);
    
    // Try cache first
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      await this.redis.expire(cacheKey, 600); // Extend TTL
      logger.debug({ sessionId, query }, 'Returning cached context');
      return JSON.parse(cached);
    }

    // Fetch from all sources in parallel with timeout and fallback
    const [code, research, business, github, conversation] = await Promise.all([
      this.fetchWithFallback('context', query),
      this.fetchWithFallback('research', query),
      this.fetchWithFallback('business', query),
      this.fetchWithFallback('github', query),
      this.getConversationHistory(sessionId),
    ]);

    const unified: MemoryContext = {
      code,
      research,
      business,
      conversation,
      github,
    };

    // Store in cache
    await this.redis.setex(cacheKey, 600, JSON.stringify(unified));

    // Store query in vector store for future retrieval
    await this.vectorStore.store(
      query,
      {
        sessionId,
        type: 'query',
        timestamp: new Date().toISOString(),
      },
      'query'
    );

    // Notify subscribers
    this.notifySubscribers(sessionId, {
      type: 'context_updated',
      query,
      timestamp: Date.now(),
    });

    logger.info({ sessionId, query }, 'Unified context generated');
    return unified;
  }

  private async fetchWithFallback(clientName: string, query: string): Promise<any[]> {
    const client = this.clients.get(clientName);
    if (!client) return [];

    try {
      return await this.limit(async () => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), client.timeout);

        try {
          const response = await fetch(`${client.url}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
            signal: controller.signal,
          });

          clearTimeout(timeout);

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();
          return data.results || [];
        } finally {
          clearTimeout(timeout);
        }
      });
    } catch (error) {
      logger.warn({ error, clientName, query }, 'Failed to fetch from MCP client');
      
      // Try to get from cache or vector store as fallback
      const fallbackResults = await this.vectorStore.search(query, { sourceType: clientName }, 5);
      return fallbackResults.map(r => ({
        content: r.content,
        metadata: r.metadata,
        cached: true,
      }));
    }
  }

  async getConversationHistory(sessionId: string): Promise<any[]> {
    const historyKey = `session:${sessionId}:history`;
    const history = await this.redis.lrange(historyKey, 0, 19); // Last 20 messages
    
    return history.map(item => {
      try {
        return JSON.parse(item);
      } catch {
        return { content: item };
      }
    }).reverse(); // Oldest first
  }

  async storeConversation(sessionId: string, data: any): Promise<void> {
    const historyKey = `session:${sessionId}:history`;
    
    // Store in Redis list
    await this.redis.lpush(historyKey, JSON.stringify(data));
    await this.redis.ltrim(historyKey, 0, 99); // Keep last 100 messages
    await this.redis.expire(historyKey, 86400); // 24 hour TTL

    // Store in vector store for long-term retrieval
    await this.vectorStore.store(
      data.message || data.content,
      {
        sessionId,
        type: 'conversation',
        role: data.role || 'user',
        timestamp: data.timestamp || Date.now(),
      },
      'conversation'
    );
  }

  async search(query: string, sessionId?: string): Promise<any> {
    // Search across all memory stores
    const results = await this.vectorStore.search(query, {}, 20);
    
    // If session-specific, boost session-related results
    if (sessionId) {
      const sessionResults = results.filter(r => 
        r.metadata?.sessionId === sessionId
      );
      const otherResults = results.filter(r => 
        r.metadata?.sessionId !== sessionId
      );
      
      return [...sessionResults, ...otherResults].slice(0, 10);
    }
    
    return results;
  }

  subscribe(sessionId: string, socket: WebSocket): void {
    this.subscriptions.set(sessionId, {
      sessionId,
      socket,
      lastActivity: new Date(),
    });
    
    logger.info({ sessionId }, 'Client subscribed to updates');
  }

  unsubscribe(sessionId: string): void {
    this.subscriptions.delete(sessionId);
    logger.info({ sessionId }, 'Client unsubscribed from updates');
  }

  cleanup(socket: WebSocket): void {
    for (const [sessionId, subscription] of this.subscriptions.entries()) {
      if (subscription.socket === socket) {
        this.subscriptions.delete(sessionId);
        logger.info({ sessionId }, 'Cleaned up subscription');
      }
    }
  }

  private notifySubscribers(sessionId: string, data: any): void {
    const subscription = this.subscriptions.get(sessionId);
    if (subscription && subscription.socket.readyState === WebSocket.OPEN) {
      subscription.socket.send(JSON.stringify(data));
      subscription.lastActivity = new Date();
    }
  }

  private cleanupStaleSubscriptions(): void {
    const now = new Date();
    const staleTimeout = 5 * 60 * 1000; // 5 minutes

    for (const [sessionId, subscription] of this.subscriptions.entries()) {
      const timeSinceActivity = now.getTime() - subscription.lastActivity.getTime();
      
      if (timeSinceActivity > staleTimeout || subscription.socket.readyState !== WebSocket.OPEN) {
        this.subscriptions.delete(sessionId);
        logger.info({ sessionId }, 'Removed stale subscription');
      }
    }
  }

  private async handlePubSubMessage(channel: string, data: any): Promise<void> {
    switch (channel) {
      case 'memory:invalidate':
        // Invalidate cache for specific keys
        if (data.keys && Array.isArray(data.keys)) {
          await Promise.all(data.keys.map(key => this.redis.del(key)));
        }
        break;
        
      case 'memory:sync':
        // Sync memory updates to all subscribers
        for (const subscription of this.subscriptions.values()) {
          this.notifySubscribers(subscription.sessionId, {
            type: 'memory_sync',
            data,
          });
        }
        break;
    }
  }

  private getCacheKey(query: string, sessionId: string): string {
    const hash = require('crypto')
      .createHash('md5')
      .update(`${query}:${sessionId}`)
      .digest('hex');
    return `context:${hash}`;
  }

  async shutdown(): Promise<void> {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    
    await this.pubsub.unsubscribe();
    this.pubsub.disconnect();
    this.redis.disconnect();
    
    // Close all WebSocket connections
    for (const subscription of this.subscriptions.values()) {
      if (subscription.socket.readyState === WebSocket.OPEN) {
        subscription.socket.close();
      }
    }
    
    this.subscriptions.clear();
    logger.info('MemoryCoordinator shut down');
  }
}