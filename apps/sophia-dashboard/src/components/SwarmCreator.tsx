'use client';

import React, { useState } from 'react';

// Mock data for swarms
const mockSwarms = [
  {
    id: 'swarm-1',
    name: 'Research & Development Team',
    description: 'A collaborative swarm for research, code generation, and documentation',
    agents: ['Research Assistant', 'Code Generator', 'Content Writer'],
    coordinationMode: 'Collaborative',
    status: 'Running',
    created: '2024-01-18T10:00:00Z',
    tasks: 15,
    completedTasks: 8,
  },
  {
    id: 'swarm-2',
    name: 'Data Analysis Pipeline',
    description: 'Sequential processing swarm for data extraction and analysis',
    agents: ['Data Analyst', 'Research Assistant'],
    coordinationMode: 'Sequential',
    status: 'Idle',
    created: '2024-01-17T09:00:00Z',
    tasks: 10,
    completedTasks: 10,
  },
  {
    id: 'swarm-3',
    name: 'Customer Support Automation',
    description: 'Routing swarm for handling customer inquiries',
    agents: ['Content Writer', 'Research Assistant'],
    coordinationMode: 'Routing',
    status: 'Running',
    created: '2024-01-16T14:00:00Z',
    tasks: 25,
    completedTasks: 18,
  },
];

// Mock available agents
const mockAvailableAgents = [
  'Research Assistant',
  'Code Generator',
  'Data Analyst',
  'Content Writer',
  'API Integrator',
  'QA Tester',
  'Documentation Writer',
  'Business Analyst',
];

const coordinationModes = [
  {
    value: 'Collaborative',
    label: 'Collaborative',
    description: 'Agents work together simultaneously on tasks',
    icon: '🤝',
  },
  {
    value: 'Sequential',
    label: 'Sequential',
    description: 'Agents process tasks in a predefined order',
    icon: '➡️',
  },
  {
    value: 'Routing',
    label: 'Routing',
    description: 'Tasks are routed to the most suitable agent',
    icon: '🔀',
  },
  {
    value: 'Hierarchical',
    label: 'Hierarchical',
    description: 'Manager agent delegates tasks to worker agents',
    icon: '📊',
  },
];

export default function SwarmCreator() {
  const [swarms, setSwarms] = useState(mockSwarms);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [selectedSwarm, setSelectedSwarm] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    agents: [],
    coordinationMode: 'Collaborative',
  });
  const [searchTerm, setSearchTerm] = useState('');

  const handleCreateSwarm = (event) => {
    event.preventDefault();
    const newSwarm = {
      id: `swarm-${swarms.length + 1}`,
      ...formData,
      status: 'Idle',
      created: new Date().toISOString(),
      tasks: 0,
      completedTasks: 0,
    };
    setSwarms([...swarms, newSwarm]);
    setCreateModalOpen(false);
    resetForm();
  };

  const handleEditSwarm = (event) => {
    event.preventDefault();
    setSwarms(
      swarms.map((swarm) =>
        swarm.id === selectedSwarm.id
          ? { ...swarm, ...formData }
          : swarm
      )
    );
    setEditModalOpen(false);
    resetForm();
  };

  const handleDeleteSwarm = (id) => {
    if (confirm('Are you sure you want to delete this swarm?')) {
      setSwarms(swarms.filter((swarm) => swarm.id !== id));
    }
  };

  const handleToggleStatus = (id) => {
    setSwarms(
      swarms.map((swarm) =>
        swarm.id === id
          ? { ...swarm, status: swarm.status === 'Running' ? 'Idle' : 'Running' }
          : swarm
      )
    );
  };

  const openEditModal = (swarm) => {
    setSelectedSwarm(swarm);
    setFormData({
      name: swarm.name,
      description: swarm.description,
      agents: swarm.agents,
      coordinationMode: swarm.coordinationMode,
    });
    setEditModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      agents: [],
      coordinationMode: 'Collaborative',
    });
    setSelectedSwarm(null);
  };

  const filteredSwarms = swarms.filter((swarm) => {
    return swarm.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           swarm.description.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const SwarmForm = ({ onSubmit, submitText }) => (
    <form onSubmit={onSubmit}>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Swarm Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
          required
        />
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Coordination Mode</label>
        <div className="grid grid-cols-2 gap-2">
          {coordinationModes.map((mode) => (
            <label
              key={mode.value}
              className={`flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                formData.coordinationMode === mode.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="coordinationMode"
                value={mode.value}
                checked={formData.coordinationMode === mode.value}
                onChange={(e) => setFormData({ ...formData, coordinationMode: e.target.value })}
                className="sr-only"
              />
              <span className="mr-2 text-2xl">{mode.icon}</span>
              <div className="flex-1">
                <div className="font-medium">{mode.label}</div>
                <div className="text-xs text-gray-500">{mode.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
      <div className="mb-4">
        <label className="block mb-1 text-sm font-medium">Select Agents</label>
        <div className="space-y-2 max-h-40 overflow-y-auto border rounded-lg p-2">
          {mockAvailableAgents.map((agent) => (
            <label key={agent} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.agents.includes(agent)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setFormData({ ...formData, agents: [...formData.agents, agent] });
                  } else {
                    setFormData({ ...formData, agents: formData.agents.filter((a) => a !== agent) });
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm">{agent}</span>
            </label>
          ))}
        </div>
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
            placeholder="Search swarms..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="ml-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Swarm
        </button>
      </div>

      {/* Swarm Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredSwarms.map((swarm) => (
          <div key={swarm.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold mb-1">{swarm.name}</h3>
                <p className="text-sm text-gray-600">{swarm.description}</p>
              </div>
              <span className={`px-3 py-1 text-xs rounded-full ${
                swarm.status === 'Running'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {swarm.status}
              </span>
            </div>
            
            <div className="mb-4">
              <div className="flex items-center mb-2">
                <span className="text-sm font-medium mr-2">Mode:</span>
                <span className="text-sm text-gray-600">
                  {coordinationModes.find(m => m.value === swarm.coordinationMode)?.icon} {swarm.coordinationMode}
                </span>
              </div>
              <div className="mb-2">
                <span className="text-sm font-medium">Agents ({swarm.agents.length}):</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {swarm.agents.map((agent, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                      {agent}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-500 mb-1">
                <span>Task Progress</span>
                <span>{swarm.completedTasks} / {swarm.tasks}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: swarm.tasks > 0 ? `${(swarm.completedTasks / swarm.tasks) * 100}%` : '0%' }}
                />
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <button
                onClick={() => handleToggleStatus(swarm.id)}
                className="text-sm text-blue-500 hover:text-blue-700"
              >
                {swarm.status === 'Running' ? 'Stop' : 'Start'}
              </button>
              <button
                onClick={() => openEditModal(swarm)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Configure
              </button>
              <button
                onClick={() => handleDeleteSwarm(swarm.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredSwarms.length === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No swarms found</h3>
          <p className="text-gray-500">Create your first swarm to get started with agent coordination.</p>
        </div>
      )}

      {/* Create Swarm Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-6">Create New Swarm</h3>
            <SwarmForm onSubmit={handleCreateSwarm} submitText="Create Swarm" />
          </div>
        </div>
      )}

      {/* Edit Swarm Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-6">Configure Swarm</h3>
            <SwarmForm onSubmit={handleEditSwarm} submitText="Save Changes" />
          </div>
        </div>
      )}
    </div>
  );
}