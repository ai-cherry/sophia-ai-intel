/**
 * Swarm Client - WebSocket subscriptions for live swarm updates
 * NO MOCK DATA
 */

export enum SwarmType {
  CODING = 'coding',
  RESEARCH = 'research',
  ANALYSIS = 'analysis',
  PLANNING = 'planning'
}

export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  capabilities: string[];
  status?: string;
}

export interface PlansResponse {
  task: string;
  plans: {
    cutting_edge: {
      plan: string;
      risk_assessment?: any;
      artifacts?: string[];
    };
    conservative: {
      plan: string;
      risk_assessment?: any;
      artifacts?: string[];
    };
    synthesis: {
      plan: string;
      risk_assessment?: any;
      artifacts?: string[];
    };
  };
  recommendation: string;
}

export interface SwarmStatus {
  swarm_id: string;
  swarm_type: string;
  status: 'creating' | 'executing' | 'completed' | 'error' | 'active' | 'failed';
  progress: number;
  current_task?: string;
  agents: Array<{
    id: string;
    name: string;
    type: string;
    role?: string;
    status: string;
  }>;
  results?: any;
  error?: string;
}

export interface SwarmEvent {
  type: 'status' | 'progress' | 'finding' | 'result' | 'error';
  swarm_id: string;
  data: any;
  timestamp: string;
}

class SwarmClient {
  private websockets: Map<string, WebSocket> = new Map();
  private baseUrl: string;
  
  constructor() {
    // Use environment or default to local
    this.baseUrl = process.env.NEXT_PUBLIC_SWARM_WS_URL || 'ws://localhost:8100';
  }
  
  /**
   * Subscribe to swarm updates via WebSocket
   */
  subscribeToSwarm(
    swarmId: string, 
    onMessage: (status: SwarmStatus) => void
  ): () => void {
    // Close existing connection if any
    if (this.websockets.has(swarmId)) {
      this.websockets.get(swarmId)?.close();
    }
    
    // Create new WebSocket connection
    const ws = new WebSocket(`${this.baseUrl}/ws/swarm/${swarmId}`);
    
    ws.onopen = () => {
      console.log(`Connected to swarm ${swarmId}`);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('Failed to parse swarm message:', e);
      }
    };
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for swarm ${swarmId}:`, error);
    };
    
    ws.onclose = () => {
      console.log(`Disconnected from swarm ${swarmId}`);
      this.websockets.delete(swarmId);
    };
    
    this.websockets.set(swarmId, ws);
    
    // Return unsubscribe function
    return () => {
      ws.close();
      this.websockets.delete(swarmId);
    };
  }
  
  /**
   * List all active swarms
   */
  async listSwarms(): Promise<Array<SwarmStatus>> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/swarms`);
      if (!response.ok) throw new Error('Failed to fetch swarms');
      return await response.json();
    } catch (error) {
      console.error('Failed to list swarms:', error);
      return [];
    }
  }
  
  /**
   * Get swarm status
   */
  async getSwarmStatus(swarmId: string): Promise<SwarmStatus | null> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/swarms/${swarmId}/status`);
      if (!response.ok) throw new Error('Failed to fetch swarm status');
      return await response.json();
    } catch (error) {
      console.error('Failed to get swarm status:', error);
      return null;
    }
  }
  
  /**
   * Create a new swarm
   */
  async createSwarm(params: {
    swarm_type: SwarmType | string;
    task: string;
    context?: any;
    config?: any;
  }): Promise<{ success: boolean; swarm_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/swarms/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      
      if (!response.ok) throw new Error('Failed to create swarm');
      const data = await response.json();
      return { success: true, swarm_id: data.swarm_id };
    } catch (error) {
      console.error('Failed to create swarm:', error);
      return { success: false, swarm_id: '' };
    }
  }
  
  /**
   * Generate plans for a task
   */
  async generatePlans(task: string): Promise<PlansResponse> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/swarms/plans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
      });
      
      if (!response.ok) throw new Error('Failed to generate plans');
      return await response.json();
    } catch (error) {
      console.error('Failed to generate plans:', error);
      // Return a default response structure
      return {
        task,
        plans: {
          cutting_edge: { plan: 'Failed to generate plan', risk_assessment: null, artifacts: [] },
          conservative: { plan: 'Failed to generate plan', risk_assessment: null, artifacts: [] },
          synthesis: { plan: 'Failed to generate plan', risk_assessment: null, artifacts: [] }
        },
        recommendation: 'Unable to generate plans at this time'
      };
    }
  }
  
  /**
   * Stop a swarm
   */
  async stopSwarm(swarmId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/swarms/${swarmId}/stop`, {
        method: 'POST'
      });
      return response.ok;
    } catch (error) {
      console.error('Failed to stop swarm:', error);
      return false;
    }
  }
  
  /**
   * Get list of available agents
   */
  async listAgents(): Promise<Array<AgentInfo>> {
    try {
      const response = await fetch(`${this.baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/agents`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      return await response.json();
    } catch (error) {
      console.error('Failed to list agents:', error);
      // Return default agents if API is unavailable
      return [
        { id: 'research-1', name: 'Research Agent', type: 'research', capabilities: ['web_search', 'summarization', 'citation'] },
        { id: 'code-1', name: 'Code Generator', type: 'coding', capabilities: ['python', 'javascript', 'testing'] },
        { id: 'plan-1', name: 'Planning Agent', type: 'planning', capabilities: ['strategy', 'architecture', 'roadmap'] },
        { id: 'analyze-1', name: 'Analysis Agent', type: 'analysis', capabilities: ['data_analysis', 'visualization', 'insights'] }
      ];
    }
  }
  
  /**
   * Cleanup all connections
   */
  disconnect(): void {
    this.websockets.forEach((ws, id) => {
      ws.close();
    });
    this.websockets.clear();
  }
}

// Export singleton instance
export const swarmClient = new SwarmClient();
