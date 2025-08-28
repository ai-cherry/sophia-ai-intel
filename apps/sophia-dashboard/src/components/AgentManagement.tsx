'use client';

import React, { useState, useEffect } from 'react';

// Types for agent management
interface Agent {
  id: string;
  name: string;
  type: 'research' | 'coding' | 'business' | 'communication';
  status: 'active' | 'inactive' | 'training';
  description: string;
  createdAt: string;
  lastActive: string;
  capabilities: string[];
  metrics: {
    tasksCompleted: number;
    successRate: number;
    avgResponseTime: string;
  };
}

interface NewAgentForm {
  name: string;
  type: 'research' | 'coding' | 'business' | 'communication';
  description: string;
  capabilities: string[];
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: '1',
      name: 'Research Assistant',
      type: 'research',
      status: 'active',
      description: 'Conducts market analysis and competitive research',
      createdAt: '2024-01-15',
      lastActive: '5 minutes ago',
      capabilities: ['Web Research', 'Data Analysis', 'Report Generation'],
      metrics: {
        tasksCompleted: 127,
        successRate: 94.5,
        avgResponseTime: '2.3s'
      }
    },
    {
      id: '2',
      name: 'Code Generator',
      type: 'coding',
      status: 'active',
      description: 'Generates and reviews code across multiple languages',
      createdAt: '2024-01-10',
      lastActive: '2 minutes ago',
      capabilities: ['Code Generation', 'Code Review', 'Testing', 'Documentation'],
      metrics: {
        tasksCompleted: 89,
        successRate: 97.2,
        avgResponseTime: '3.1s'
      }
    },
    {
      id: '3',
      name: 'Business Analyst',
      type: 'business',
      status: 'inactive',
      description: 'Analyzes business processes and suggests improvements',
      createdAt: '2024-01-05',
      lastActive: '2 hours ago',
      capabilities: ['Process Analysis', 'KPI Tracking', 'Strategy Planning'],
      metrics: {
        tasksCompleted: 56,
        successRate: 91.8,
        avgResponseTime: '4.2s'
      }
    }
  ]);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAgent, setNewAgent] = useState<NewAgentForm>({
    name: '',
    type: 'research',
    description: '',
    capabilities: []
  });
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const handleCreateAgent = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const agent: Agent = {
      id: `${agents.length + 1}`,
      name: newAgent.name,
      type: newAgent.type,
      status: 'training',
      description: newAgent.description,
      createdAt: new Date().toISOString().split('T')[0],
      lastActive: 'Just created',
      capabilities: newAgent.capabilities,
      metrics: {
        tasksCompleted: 0,
        successRate: 0,
        avgResponseTime: 'N/A'
      }
    };

    setAgents([...agents, agent]);
    setNewAgent({ name: '', type: 'research', description: '', capabilities: [] });
    setShowCreateForm(false);
  };

  const handleDeleteAgent = (agentId: string) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      setAgents(agents.filter(agent => agent.id !== agentId));
    }
  };

  const handleToggleStatus = (agentId: string) => {
    setAgents(agents.map(agent => 
      agent.id === agentId 
        ? { ...agent, status: agent.status === 'active' ? 'inactive' : 'active' as Agent['status'] }
        : agent
    ));
  };

  const filteredAgents = agents.filter(agent => {
    const typeMatch = filterType === 'all' || agent.type === filterType;
    const statusMatch = filterStatus === 'all' || agent.status === filterStatus;
    return typeMatch && statusMatch;
  });

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'training': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: Agent['type']) => {
    switch (type) {
      case 'research': return '🔍';
      case 'coding': return '💻';
      case 'business': return '📊';
      case 'communication': return '💬';
      default: return '🤖';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Agent Management</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create New Agent
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Type</label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="all">All Types</option>
            <option value="research">Research</option>
            <option value="coding">Coding</option>
            <option value="business">Business</option>
            <option value="communication">Communication</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Status</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="training">Training</option>
          </select>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <div key={agent.id} className="bg-white rounded-lg shadow-md p-6 border">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center">
                <span className="text-2xl mr-3">{getTypeIcon(agent.type)}</span>
                <div>
                  <h3 className="text-lg font-semibold">{agent.name}</h3>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                    {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleToggleStatus(agent.id)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  {agent.status === 'active' ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  onClick={() => handleDeleteAgent(agent.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </div>
            </div>

            <p className="text-gray-600 text-sm mb-4">{agent.description}</p>

            <div className="mb-4">
              <h4 className="font-medium text-sm text-gray-700 mb-2">Capabilities</h4>
              <div className="flex flex-wrap gap-1">
                {agent.capabilities.map((capability, index) => (
                  <span key={index} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                    {capability}
                  </span>
                ))}
              </div>
            </div>

            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex justify-between">
                <span>Tasks Completed:</span>
                <span className="font-medium">{agent.metrics.tasksCompleted}</span>
              </div>
              <div className="flex justify-between">
                <span>Success Rate:</span>
                <span className="font-medium">{agent.metrics.successRate}%</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Response:</span>
                <span className="font-medium">{agent.metrics.avgResponseTime}</span>
              </div>
              <div className="flex justify-between">
                <span>Last Active:</span>
                <span className="font-medium">{agent.lastActive}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Agent Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Create New Agent</h3>
            <form onSubmit={handleCreateAgent}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                <select
                  value={newAgent.type}
                  onChange={(e) => setNewAgent({ ...newAgent, type: e.target.value as Agent['type'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="research">Research</option>
                  <option value="coding">Coding</option>
                  <option value="business">Business</option>
                  <option value="communication">Communication</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={newAgent.description}
                  onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Capabilities (comma-separated)
                </label>
                <input
                  type="text"
                  onChange={(e) => setNewAgent({ 
                    ...newAgent, 
                    capabilities: e.target.value.split(',').map(c => c.trim()).filter(c => c) 
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Data Analysis, Report Generation"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents found</h3>
          <p className="text-gray-500">
            {filterType !== 'all' || filterStatus !== 'all'
              ? 'Try adjusting your filters or create a new agent.'
              : 'Get started by creating your first agent.'}
          </p>
        </div>
      )}
    </div>
  );
}