/**
 * Sophia AI Dashboard - API Client
 * Provides centralized API communication with backend services
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8082';
const GITHUB_MCP_URL = process.env.NEXT_PUBLIC_GITHUB_MCP_URL || 'http://localhost:8092';
const AGNO_COORDINATOR_URL = process.env.NEXT_PUBLIC_AGNO_COORDINATOR_URL || 'http://localhost:8082';

export interface ChatMessage {
  id: string;
  role: 'user' | 'system' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    prompt_enhanced?: boolean;
    processing_time?: number;
    service?: string;
  };
}

export interface ChatSettings {
  verbosity: string;
  askMeThreshold: number;
  riskStance: string;
  enableEnhancement: boolean;
  model: string;
}

export interface APIResponse<T> {
  data?: T;
  error?: string;
  timestamp?: string;
}

class APIClient {
  private async request<T>(url: string, options: RequestInit = {}): Promise<APIResponse<T>> {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('API Request Error:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Chat API - Connect to agno-coordinator
  async sendChatMessage(
    message: string,
    settings: ChatSettings,
    history: ChatMessage[]
  ): Promise<APIResponse<ChatMessage>> {
    const payload = {
      message,
      settings,
      history: history.slice(-10), // Send last 10 messages for context
    };

    const response = await this.request<any>(`${AGNO_COORDINATOR_URL}/chat`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (response.error) {
      return response;
    }

    // Convert timestamp string to Date object
    const messageData = response.data?.data || response.data;
    if (messageData && messageData.timestamp) {
      messageData.timestamp = new Date(messageData.timestamp);
    }

    return { data: messageData };
  }

  // GitHub MCP Service
  async getGitHubHealth(): Promise<APIResponse<any>> {
    return this.request(`${GITHUB_MCP_URL}/healthz`);
  }

  async getGitHubFile(path: string, ref: string = 'main'): Promise<APIResponse<any>> {
    return this.request(`${GITHUB_MCP_URL}/repo/file?path=${encodeURIComponent(path)}&ref=${ref}`);
  }

  async getGitHubTree(path: string = '', ref: string = 'main'): Promise<APIResponse<any>> {
    return this.request(`${GITHUB_MCP_URL}/repo/tree?path=${encodeURIComponent(path)}&ref=${ref}`);
  }

  // Agent Management API
  async getAgents(): Promise<APIResponse<any[]>> {
    return this.request(`${AGNO_COORDINATOR_URL}/agents`);
  }

  async createAgent(config: any): Promise<APIResponse<any>> {
    return this.request(`${AGNO_COORDINATOR_URL}/agents`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSwarms(): Promise<APIResponse<any[]>> {
    return this.request(`${AGNO_COORDINATOR_URL}/swarms`);
  }

  async createSwarm(config: any): Promise<APIResponse<any>> {
    return this.request(`${AGNO_COORDINATOR_URL}/swarms`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Health Check for all services
  async healthCheck(): Promise<APIResponse<any>> {
    const services = [
      { name: 'agno-coordinator', url: `${AGNO_COORDINATOR_URL}/health` },
      { name: 'github-mcp', url: `${GITHUB_MCP_URL}/healthz` },
    ];

    const results = await Promise.allSettled(
      services.map(async (service) => ({
        name: service.name,
        ...(await this.request(service.url)),
      }))
    );

    const healthStatus = results.map((result, index) => ({
      service: services[index].name,
      status: result.status === 'fulfilled' && !result.value.error ? 'healthy' : 'unhealthy',
      details: result.status === 'fulfilled' ? result.value : { error: 'Service unavailable' },
    }));

    return { data: healthStatus };
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;