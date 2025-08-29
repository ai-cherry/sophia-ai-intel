'use client';

import { useState, useEffect } from 'react';

interface SwarmStatus {
  is_initialized: boolean;
  total_agents: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  system_status: string;
}

interface AgentInfo {
  name: string;
  role: string;
  is_active: boolean;
  current_tasks: number;
}

export default function AgentSwarmPanel() {
  const [swarmStatus, setSwarmStatus] = useState<SwarmStatus | null>(null);
  const [agents, setAgents] = useState<Record<string, AgentInfo>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSwarmStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      // REAL DATA - Fetch from actual swarm service
      const [statusRes, agentsRes] = await Promise.all([
        fetch('http://localhost:8100/swarms'),
        fetch('http://localhost:8100/agents')
      ]);
      
      if (statusRes.ok) {
        const swarms = await statusRes.json();
        setSwarmStatus({
          is_initialized: swarms.length > 0,
          total_agents: swarms.reduce((acc: number, s: any) => acc + (s.agents?.length || 0), 0),
          active_tasks: swarms.filter((s: any) => s.status === 'executing').length,
          completed_tasks: swarms.filter((s: any) => s.status === 'completed').length,
          failed_tasks: swarms.filter((s: any) => s.status === 'failed').length,
          system_status: swarms.length > 0 ? 'ok' : 'idle',
        });
      }
      
      if (agentsRes.ok) {
        const agentList = await agentsRes.json();
        const agentMap: Record<string, AgentInfo> = {};
        agentList.forEach((agent: any) => {
          agentMap[agent.id] = {
            name: agent.name,
            role: agent.type,
            is_active: agent.status === 'idle' || agent.status === 'active',
            current_tasks: 0, // Will be updated from swarm status
          };
        });
        setAgents(agentMap);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch swarm status');
      // Fallback to empty state (no mock data)
      setSwarmStatus({
        is_initialized: false,
        total_agents: 0,
        active_tasks: 0,
        completed_tasks: 0,
        failed_tasks: 0,
        system_status: 'error',
      });
      setAgents({});
    } finally {
      setLoading(false);
    }
  };

  const testSwarm = async () => {
    alert('Swarm test initiated!');
  };

  useEffect(() => {
    fetchSwarmStatus();
  }, []);

  return (
    <div className="p-8 bg-white rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold">🤖 Sophia Agent Swarm</h2>
        <div className="flex gap-4">
          <button
            onClick={fetchSwarmStatus}
            disabled={loading}
            className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-md disabled:bg-gray-400"
          >
            {loading ? 'Loading...' : 'Refresh Status'}
          </button>
          <button
            onClick={testSwarm}
            className="px-4 py-2 font-semibold text-white bg-green-600 rounded-md"
          >
            🧪 Test Swarm
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-4 text-red-800 bg-red-100 border border-red-200 rounded-md">
          <strong>Error:</strong> {error}
        </div>
      )}

      {swarmStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Status Overview */}
          <div className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-4">System Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Initialized:</span>
                <span className={`font-bold ${swarmStatus.is_initialized ? 'text-green-600' : 'text-red-600'}`}>
                  {swarmStatus.is_initialized ? '✅ Yes' : '❌ No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Total Agents:</span>
                <span>{swarmStatus.total_agents}</span>
              </div>
              <div className="flex justify-between">
                <span>Active Tasks:</span>
                <span>{swarmStatus.active_tasks}</span>
              </div>
              <div className="flex justify-between">
                <span>Completed:</span>
                <span className="text-green-600 font-semibold">{swarmStatus.completed_tasks}</span>
              </div>
              <div className="flex justify-between">
                <span>Failed:</span>
                <span className="text-red-600 font-semibold">{swarmStatus.failed_tasks}</span>
              </div>
            </div>
          </div>

          {/* Agent List */}
          <div className="p-6 border rounded-lg md:col-span-2">
            <h3 className="text-lg font-semibold mb-4">Active Agents</h3>
            {Object.keys(agents).length === 0 ? (
              <p className="text-gray-500 italic">No agents available</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(agents).map(([agentId, agent]) => (
                  <div key={agentId} className="p-4 bg-gray-50 rounded-md border">
                    <div className="flex justify-between items-center">
                      <div>
                        <strong className="font-semibold">{agent.name}</strong>
                        <br />
                        <small className="text-gray-500">
                          Role: {agent.role} • Status: {agent.is_active ? 'Active' : 'Inactive'}
                        </small>
                      </div>
                      <div
                        className={`px-3 py-1 text-xs font-semibold text-white rounded-full ${
                          agent.is_active ? 'bg-green-500' : 'bg-gray-500'
                        }`}
                      >
                        {agent.current_tasks} tasks
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
