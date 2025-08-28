'use client';

import React, { useState, useEffect } from 'react';

interface Agent {
  id: string;
  name: string;
  status: string;
  uptime: string;
  tasksCompleted: number;
  avgResponseTime: string;
  memoryUsage: number;
  cpuUsage: number;
  lastActivity: string;
  currentTask: string | null;
  errorRate: number;
}

interface SystemMetrics {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  tasksInQueue: number;
  avgSystemLoad: number;
  totalMemory: number;
  usedMemory: number;
  apiCalls: number;
  successRate: number;
}

interface ActivityLogEntry {
  time: string;
  agent: string;
  action: string;
  details: string;
}

// Mock monitoring data
const mockAgentMetrics: Agent[] = [
  {
    id: '1',
    name: 'Research Assistant',
    status: 'Active',
    uptime: '23h 45m',
    tasksCompleted: 127,
    avgResponseTime: '2.3s',
    memoryUsage: 45,
    cpuUsage: 23,
    lastActivity: '2 minutes ago',
    currentTask: 'Analyzing market trends for Q1 report',
    errorRate: 0.2,
  },
  {
    id: '2',
    name: 'Code Generator',
    status: 'Active',
    uptime: '18h 30m',
    tasksCompleted: 89,
    avgResponseTime: '3.1s',
    memoryUsage: 62,
    cpuUsage: 45,
    lastActivity: '5 seconds ago',
    currentTask: 'Generating API endpoint for user service',
    errorRate: 0.5,
  },
  {
    id: '3',
    name: 'Data Analyst',
    status: 'Idle',
    uptime: '12h 15m',
    tasksCompleted: 56,
    avgResponseTime: '4.2s',
    memoryUsage: 30,
    cpuUsage: 10,
    lastActivity: '15 minutes ago',
    currentTask: null,
    errorRate: 0.1,
  },
  {
    id: '4',
    name: 'Content Writer',
    status: 'Active',
    uptime: '6h 20m',
    tasksCompleted: 34,
    avgResponseTime: '5.8s',
    memoryUsage: 38,
    cpuUsage: 18,
    lastActivity: '1 minute ago',
    currentTask: 'Writing blog post on AI trends',
    errorRate: 0.3,
  },
];

const mockSystemMetrics: SystemMetrics = {
  totalAgents: 12,
  activeAgents: 8,
  totalTasks: 512,
  tasksInQueue: 23,
  avgSystemLoad: 42,
  totalMemory: 16384,
  usedMemory: 8765,
  apiCalls: 15234,
  successRate: 99.2,
};

const mockActivityLog: ActivityLogEntry[] = [
  { time: '10:45:23', agent: 'Research Assistant', action: 'Task completed', details: 'Market analysis report generated' },
  { time: '10:44:15', agent: 'Code Generator', action: 'Task started', details: 'Creating REST API endpoints' },
  { time: '10:43:08', agent: 'Content Writer', action: 'Task completed', details: 'Blog post published' },
  { time: '10:42:45', agent: 'Data Analyst', action: 'Error', details: 'Database connection timeout' },
  { time: '10:41:22', agent: 'Research Assistant', action: 'Task started', details: 'Beginning competitive analysis' },
];

export default function AgentMonitoring() {
  const [agentMetrics, setAgentMetrics] = useState<Agent[]>(mockAgentMetrics);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(mockSystemMetrics);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>(mockActivityLog);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(5000);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // Simulate real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Update agent metrics with random changes
      setAgentMetrics(prev => prev.map((agent: Agent) => ({
        ...agent,
        cpuUsage: Math.max(0, Math.min(100, agent.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(0, Math.min(100, agent.memoryUsage + (Math.random() - 0.5) * 5)),
        tasksCompleted: agent.status === 'Active' ? agent.tasksCompleted + Math.floor(Math.random() * 2) : agent.tasksCompleted,
      })));

      // Update system metrics
      setSystemMetrics(prev => ({
        ...prev,
        tasksInQueue: Math.max(0, prev.tasksInQueue + Math.floor((Math.random() - 0.5) * 5)),
        apiCalls: prev.apiCalls + Math.floor(Math.random() * 10),
        avgSystemLoad: Math.max(0, Math.min(100, prev.avgSystemLoad + (Math.random() - 0.5) * 5)),
      }));
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return 'text-green-500';
      case 'Idle': return 'text-yellow-500';
      case 'Error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getProgressBarColor = (value: number) => {
    if (value < 50) return 'bg-green-500';
    if (value < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div>
      {/* System Overview */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">System Overview</h2>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Auto-refresh</span>
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="px-3 py-1 border rounded text-sm"
              disabled={!autoRefresh}
            >
              <option value={1000}>1s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Active Agents</div>
            <div className="text-2xl font-bold">{systemMetrics.activeAgents}/{systemMetrics.totalAgents}</div>
            <div className="text-xs text-gray-400 mt-1">
              {((systemMetrics.activeAgents / systemMetrics.totalAgents) * 100).toFixed(0)}% utilization
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Tasks in Queue</div>
            <div className="text-2xl font-bold">{systemMetrics.tasksInQueue}</div>
            <div className="text-xs text-gray-400 mt-1">
              {systemMetrics.totalTasks} total processed
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">System Load</div>
            <div className="text-2xl font-bold">{systemMetrics.avgSystemLoad}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${getProgressBarColor(systemMetrics.avgSystemLoad)}`}
                style={{ width: `${systemMetrics.avgSystemLoad}%` }}
              />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Success Rate</div>
            <div className="text-2xl font-bold">{systemMetrics.successRate}%</div>
            <div className="text-xs text-gray-400 mt-1">
              {systemMetrics.apiCalls.toLocaleString()} API calls
            </div>
          </div>
        </div>
      </div>

      {/* Agent Metrics */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Agent Performance</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uptime</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tasks</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CPU</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Memory</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Task</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {agentMetrics.map((agent: Agent) => (
                  <tr key={agent.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                      <div className="text-xs text-gray-500">{agent.lastActivity}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        agent.status === 'Active' ? 'bg-green-100 text-green-800' :
                        agent.status === 'Idle' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {agent.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{agent.uptime}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{agent.tasksCompleted}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{agent.avgResponseTime}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">{agent.cpuUsage.toFixed(0)}%</span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getProgressBarColor(agent.cpuUsage)}`}
                            style={{ width: `${agent.cpuUsage}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">{agent.memoryUsage.toFixed(0)}%</span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getProgressBarColor(agent.memoryUsage)}`}
                            style={{ width: `${agent.memoryUsage}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      <div className="max-w-xs truncate">
                        {agent.currentTask || '-'}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedAgent(agent)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Activity Log */}
      <div>
        <h2 className="text-xl font-bold mb-4">Activity Log</h2>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="space-y-2">
            {activityLog.map((log: ActivityLogEntry, index: number) => (
              <div key={index} className="flex items-start space-x-3 py-2 border-b last:border-b-0">
                <div className="text-xs text-gray-400 w-20">{log.time}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-sm">{log.agent}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      log.action === 'Task completed' ? 'bg-green-100 text-green-700' :
                      log.action === 'Task started' ? 'bg-blue-100 text-blue-700' :
                      log.action === 'Error' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {log.action}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">{log.details}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Details Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-2xl w-full">
            <h3 className="text-xl font-bold mb-4">{selectedAgent.name} - Detailed Metrics</h3>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <div className="text-sm text-gray-500">Status</div>
                <div className={`font-medium ${getStatusColor(selectedAgent.status)}`}>{selectedAgent.status}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Uptime</div>
                <div className="font-medium">{selectedAgent.uptime}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Tasks Completed</div>
                <div className="font-medium">{selectedAgent.tasksCompleted}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Average Response Time</div>
                <div className="font-medium">{selectedAgent.avgResponseTime}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Error Rate</div>
                <div className="font-medium">{selectedAgent.errorRate}%</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Last Activity</div>
                <div className="font-medium">{selectedAgent.lastActivity}</div>
              </div>
            </div>
            <div className="mb-6">
              <div className="text-sm text-gray-500 mb-2">Current Task</div>
              <div className="p-3 bg-gray-50 rounded">
                {selectedAgent.currentTask || 'No active task'}
              </div>
            </div>
            <div className="mb-6">
              <div className="text-sm text-gray-500 mb-2">Resource Usage</div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>CPU Usage</span>
                    <span>{selectedAgent.cpuUsage.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getProgressBarColor(selectedAgent.cpuUsage)}`}
                      style={{ width: `${selectedAgent.cpuUsage}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Memory Usage</span>
                    <span>{selectedAgent.memoryUsage.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getProgressBarColor(selectedAgent.memoryUsage)}`}
                      style={{ width: `${selectedAgent.memoryUsage}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setSelectedAgent(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}