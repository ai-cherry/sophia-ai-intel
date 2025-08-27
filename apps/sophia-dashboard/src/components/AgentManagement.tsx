'use client';

import React, { useState } from 'react';

// Mock data for agents
const mockAgents = [
  {
    id: '1',
    name: 'Research Assistant',
    role: 'Gathers and summarizes information from the web, analyzes data trends, and provides comprehensive research reports.',
    model: 'Claude 3 Opus',
    status: 'Active',
    tools: ['Web Search', 'Calculator', 'File Reader', 'Code Interpreter'],
    memory: 'Redis',
    created: '2024-01-15T10:00:00Z',
    lastActive: '2024-01-20T15:30:00Z',
  },
  {
    id: '2',
    name: 'Code Generator',
    role: 'Generates code snippets in various languages, reviews code quality, and suggests optimizations.',
    model: 'GPT-4 Turbo',
    status: 'Active',
    tools: ['File I/O', 'Code Interpreter', 'Git', 'Terminal'],
    memory: 'Qdrant',
    created: '2024-01-10T08:00:00Z',
    lastActive: '2024-01-20T14:00:00Z',
  },
  {
    id: '3',
    name: 'Data Analyst',
    role: 'Performs data analysis, creates visualizations, and generates insights from datasets.',
    model: 'Claude 3 Sonnet',
    status: 'Paused',
    tools: ['SQL Query', 'Python', 'Data Visualizer', 'Statistics'],
    memory: 'Redis',
    created: '2024-01-12T09:00:00Z',
    lastActive: '2024-01-18T11:00:00Z',
  },
  {
    id: '4',
    name: 'Content Writer',
    role: 'Creates engaging content, blog posts, and documentation with SEO optimization.',
    model: 'Mistral Large',
    status: 'Active',
    tools: ['Web Search', 'Grammar Check', 'SEO Analyzer'],
    memory: 'Qdrant',
    created: '2024-01-08T07:00:00Z',
    lastActive: '2024-01-20T16:00:00Z',
  },
];

const availableTools = [
  'Web Search',
  'Calculator',
  'File Reader',
  'File I/O',
  'Code Interpreter',
  'Git',
  'Terminal',
  'SQL Query',
  'Python',
  'Data Visualizer',
  'Statistics',
  'Grammar Check',
  'SEO Analyzer',
  'Email',
  'Calendar',
  'Slack',
];

const availableModels = [
  'Claude 3 Opus',
  'Claude 3 Sonnet',
  'GPT-4 Turbo',
  'GPT-4',
  'Mistral Large',
  'Mistral Medium',
  'Llama 2 70B',
  'Gemini Pro',
];

export default function AgentManagement() {
  const [agents, setAgents] = useState(mockAgents);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    model: 'Claude 3 Opus',
    tools: [],
    memory: 'Redis',
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  const handleCreateAgent = (event) => {
    event.preventDefault();
    const newAgent = {
      id: `${agents.length + 1}`,
      ...formData,
      status: 'Active',
      created: new Date().toISOString(),
      lastActive: new Date().toISOString(),
    };
    setAgents([...agents, newAgent]);
    setCreateModalOpen(false);
    resetForm();
  };

  const handleEditAgent = (event) => {
    event.preventDefault();
    setAgents(
      agents.map((agent) =>
        agent.id === selectedAgent.id
          ? { ...agent, ...formData }
          : agent
      )
    );
    setEditModalOpen(false);
    resetForm();
  };

  const handleDeleteAgent = (id) => {
    if (confirm('Are you sure you want to delete this agent?')) {
      setAgents(agents.filter((agent) => agent.id !== id));
    }
  };

  const handleToggleStatus = (id) => {
    setAgents(
      agents.map((agent) =>
        agent.id === id
          ? { ...agent, status: agent.status === 'Active' ? 'Paused' : 'Active' }
          : agent
      )
    );
  };

  const openEditModal = (agent) => {
    setSelectedAgent(agent);
    setFormData({
      name: agent.name,
      role: agent.role,
      model: agent.model,
      tools: agent.tools,
      memory: agent.memory,
    });
    setEditModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      role: '',
      model: 'Claude 3 Opus',
      tools: [],
      memory: 'Redis',
    });
    setSelectedAgent(null);
  };

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          agent.role.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || agent.status.toLowerCase() === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const AgentForm = ({ onSubmit, submitText }) => (
    <form onSubmit={onSubmit}>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Agent Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Agent Role & Description</label>
        <textarea
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
          required
        />
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Model</label>
        <select
          value={formData.model}
          onChange={(e) => setFormData({ ...formData, model: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {availableModels.map((model) => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Tools</label>
        <div className="space-y-2 max-h-40 overflow-y-auto border rounded-lg p-2">
          {availableTools.map((tool) => (
            <label key={tool} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.tools.includes(tool)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setFormData({ ...formData, tools: [...formData.tools, tool] });
                  } else {
                    setFormData({ ...formData, tools: formData.tools.filter((t) => t !== tool) });
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm">{tool}</span>
            </label>
          ))}
        </div>
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Memory Persistence</label>
        <select
          value={formData.memory}
          onChange={(e) => setFormData({ ...formData, memory: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="Redis">Redis</option>
          <option value="Qdrant">Qdrant</option>
          <option value="Pinecone">Pinecone</option>
          <option value="Weaviate">Weaviate</option>
        </select>
      </div>
      <div className="flex justify-end space-x-2">
        <button
          type="button"
          onClick={() => {
            setCreateModalOpen(false);
            setEditModalOpen(false);
            resetForm();
          }}
          className="px-4 py-2 text-gray-600 bg-gray-200 rounded-lg hover:bg-gray-300"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-white bg-blue-500 rounded-lg hover:bg-blue-600"
        >
          {submitText}
        </button>
      </div>
    </form>
  );

  return (
    <div>
      {/* Header and Controls */}
      <div className="mb-6 flex justify-between items-center">
        <div className="flex-1 max-w-lg">
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex items-center space-x-4 ml-4">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
          </select>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Agent
          </button>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((agent) => (
          <div key={agent.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">{agent.name}</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${
                agent.status === 'Active' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {agent.status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-4">{agent.role}</p>
            <div className="mb-4">
              <div className="flex items-center text-sm text-gray-500 mb-1">
                <span className="font-medium mr-2">Model:</span> {agent.model}
              </div>
              <div className="flex items-center text-sm text-gray-500 mb-1">
                <span className="font-medium mr-2">Memory:</span> {agent.memory}
              </div>
              <div className="flex items-center text-sm text-gray-500">
                <span className="font-medium mr-2">Tools:</span> {agent.tools.length} enabled
              </div>
            </div>
            <div className="flex justify-between pt-4 border-t">
              <button
                onClick={() => handleToggleStatus(agent.id)}
                className="text-sm text-blue-500 hover:text-blue-700"
              >
                {agent.status === 'Active' ? 'Pause' : 'Resume'}
              </button>
              <button
                onClick={() => openEditModal(agent)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Edit
              </button>
              <button
                onClick={() => handleDeleteAgent(agent.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create Agent Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-6">Create New Agent</h3>
            <AgentForm onSubmit={handleCreateAgent} submitText="Create Agent" />
          </div>
        </div>
      )}

      {/* Edit Agent Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-6">Edit Agent</h3>
            <AgentForm onSubmit={handleEditAgent} submitText="Save Changes" />
          </div>
        </div>
      )}
    </div>
  );
}