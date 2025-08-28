/**
 * Swarm Service API Client
 * Connects to the unified swarm service for all swarm operations
 */

export enum SwarmType {
  CODING = 'coding',
  RESEARCH = 'research',
  ANALYSIS = 'analysis',
  PLANNING = 'planning'
}

export enum PlannerType {
  CUTTING_EDGE = 'cutting_edge',
  CONSERVATIVE = 'conservative',
  SYNTHESIS = 'synthesis'
}

export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  capabilities: string[];
  status: string;
}

export interface SwarmStatus {
  swarm_id: string;
  swarm_type: SwarmType;
  status: string;
  agents: AgentInfo[];
  current_task?: string;
  progress: number;
  results?: any;
}

export interface SwarmRequest {
  swarm_type: SwarmType;
  task: string;
  context?: Record<string, any>;
  config?: Record<string, any>;
}

export interface PlanResponse {
  planner_type: PlannerType;
  plan: string;
  risk_assessment?: Record<string, any>;
  artifacts?: string[];
}

export interface PlansResponse {
  task: string;
  plans: {
    cutting_edge: PlanResponse;
    conservative: PlanResponse;
    synthesis: PlanResponse;
  };
  recommendation: string;
}

class SwarmClient {
  private baseUrl: string;
  private ws: WebSocket | null = null;

  constructor(baseUrl: string = 'http://localhost:8100') {
    this.baseUrl = baseUrl;
  }

  async health(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }

  async listAgents(): Promise<AgentInfo[]> {
    const response = await fetch(`${this.baseUrl}/agents`);
    if (!response.ok) throw new Error('Failed to list agents');
    return response.json();
  }

  async createSwarm(request: SwarmRequest): Promise<{ success: boolean; swarm_id: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/swarms/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) throw new Error('Failed to create swarm');
    return response.json();
  }

  async listSwarms(): Promise<SwarmStatus[]> {
    const response = await fetch(`${this.baseUrl}/swarms`);
    if (!response.ok) throw new Error('Failed to list swarms');
    return response.json();
  }

  async getSwarmStatus(swarmId: string): Promise<SwarmStatus> {
    const response = await fetch(`${this.baseUrl}/swarms/${swarmId}/status`);
    if (!response.ok) throw new Error('Failed to get swarm status');
    return response.json();
  }

  async stopSwarm(swarmId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/swarms/${swarmId}/stop`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to stop swarm');
    return response.json();
  }

  async generatePlans(task: string, context?: Record<string, any>): Promise<PlansResponse> {
    const response = await fetch(`${this.baseUrl}/plans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, context })
    });
    if (!response.ok) throw new Error('Failed to generate plans');
    return response.json();
  }

  subscribeToSwarm(swarmId: string, onMessage: (status: SwarmStatus) => void): () => void {
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(`ws://localhost:8100/ws/swarm/${swarmId}`);
    
    this.ws.onmessage = (event) => {
      const status = JSON.parse(event.data);
      onMessage(status);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
    };
  }
}

export const swarmClient = new SwarmClient();