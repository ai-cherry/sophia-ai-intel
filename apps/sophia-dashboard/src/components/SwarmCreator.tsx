'use client';

import React, { useState } from 'react';

interface SwarmTemplate {
  id: string;
  name: string;
  description: string;
  agents: string[];
  useCase: string;
}

interface Swarm {
  id: string;
  name: string;
  description: string;
  agents: string[];
  status: 'active' | 'inactive' | 'creating';
  createdAt: string;
  tasksCompleted: number;
}

export default function SwarmCreator() {
  const [swarms, setSwarms] = useState<Swarm[]>([
    {
      id: '1',
      name: 'Research Team',
      description: 'Multi-agent research and analysis team',
      agents: ['Research Assistant', 'Data Analyst', 'Report Writer'],
      status: 'active',
      createdAt: '2024-01-15',
      tasksCompleted: 45
    }
  ]);

  const [templates] = useState<SwarmTemplate[]>([
    {
      id: '1',
      name: 'Research Team',
      description: 'Comprehensive research and analysis swarm',
      agents: ['Research Assistant', 'Data Analyst', 'Report Writer'],
      useCase: 'Market research, competitive analysis, trend analysis'
    },
    {
      id: '2',
      name: 'Development Team',
      description: 'Full-stack development and testing swarm',
      agents: ['Frontend Developer', 'Backend Developer', 'QA Tester'],
      useCase: 'Web development, API creation, testing automation'
    },
    {
      id: '3',
      name: 'Business Intelligence',
      description: 'Business analysis and strategy swarm',
      agents: ['Business Analyst', 'Strategy Consultant', 'Data Scientist'],
      useCase: 'Business process optimization, strategic planning'
    }
  ]);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [customSwarm, setCustomSwarm] = useState({
    name: '',
    description: '',
    agents: [] as string[]
  });

  const handleCreateSwarm = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    let template = templates.find(t => t.id === selectedTemplate);
    let newSwarm: Swarm;
    
    if (template) {
      newSwarm = {
        id: `${swarms.length + 1}`,
        name: template.name,
        description: template.description,
        agents: template.agents,
        status: 'creating',
        createdAt: new Date().toISOString().split('T')[0],
        tasksCompleted: 0
      };
    } else {
      newSwarm = {
        id: `${swarms.length + 1}`,
        name: customSwarm.name,
        description: customSwarm.description,
        agents: customSwarm.agents,
        status: 'creating',
        createdAt: new Date().toISOString().split('T')[0],
        tasksCompleted: 0
      };
    }

    setSwarms([...swarms, newSwarm]);
    setShowCreateForm(false);
    setSelectedTemplate('');
    setCustomSwarm({ name: '', description: '', agents: [] });
  };

  const handleDeleteSwarm = (swarmId: string) => {
    if (window.confirm('Are you sure you want to delete this swarm?')) {
      setSwarms(swarms.filter(swarm => swarm.id !== swarmId));
    }
  };

  const handleToggleSwarm = (swarmId: string) => {
    setSwarms(swarms.map(swarm => 
      swarm.id === swarmId 
        ? { ...swarm, status: swarm.status === 'active' ? 'inactive' : 'active' as Swarm['status'] }
        : swarm
    ));
  };

  const getStatusColor = (status: Swarm['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'creating': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Swarm Creator</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create New Swarm
        </button>
      </div>

      {/* Active Swarms */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Active Swarms</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {swarms.map((swarm) => (
            <div key={swarm.id} className="bg-white rounded-lg shadow-md p-6 border">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold">{swarm.name}</h4>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusColor(swarm.status)}`}>
                    {swarm.status.charAt(0).toUpperCase() + swarm.status.slice(1)}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleSwarm(swarm.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    {swarm.status === 'active' ? 'Pause' : 'Start'}
                  </button>
                  <button
                    onClick={() => handleDeleteSwarm(swarm.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>

              <p className="text-gray-600 text-sm mb-4">{swarm.description}</p>

              <div className="mb-4">
                <h5 className="font-medium text-sm text-gray-700 mb-2">Agents ({swarm.agents.length})</h5>
                <div className="space-y-1">
                  {swarm.agents.map((agent, index) => (
                    <div key={index} className="text-xs text-gray-600 flex items-center">
                      <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                      {agent}
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Tasks Completed:</span>
                  <span className="font-medium">{swarm.tasksCompleted}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-medium">{swarm.createdAt}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Templates Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Swarm Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <div key={template.id} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h4 className="text-lg font-semibold mb-2">{template.name}</h4>
              <p className="text-gray-600 text-sm mb-4">{template.description}</p>
              
              <div className="mb-4">
                <h5 className="font-medium text-sm text-gray-700 mb-2">Included Agents</h5>
                <div className="space-y-1">
                  {template.agents.map((agent, index) => (
                    <div key={index} className="text-xs text-gray-600">
                      • {agent}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-4">
                <h5 className="font-medium text-sm text-gray-700 mb-1">Use Cases</h5>
                <p className="text-xs text-gray-600">{template.useCase}</p>
              </div>

              <button
                onClick={() => {
                  setSelectedTemplate(template.id);
                  setShowCreateForm(true);
                }}
                className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
              >
                Use Template
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Create Swarm Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">
              {selectedTemplate ? 'Create from Template' : 'Create Custom Swarm'}
            </h3>
            
            <form onSubmit={handleCreateSwarm}>
              {selectedTemplate ? (
                <div className="mb-6">
                  {(() => {
                    const template = templates.find(t => t.id === selectedTemplate);
                    return template ? (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold">{template.name}</h4>
                        <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                        <div>
                          <strong className="text-sm">Agents:</strong>
                          <ul className="text-sm text-gray-600">
                            {template.agents.map((agent, index) => (
                              <li key={index}>• {agent}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Swarm Name</label>
                    <input
                      type="text"
                      value={customSwarm.name}
                      onChange={(e) => setCustomSwarm({ ...customSwarm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <textarea
                      value={customSwarm.description}
                      onChange={(e) => setCustomSwarm({ ...customSwarm, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      rows={3}
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Agent Names (comma-separated)
                    </label>
                    <input
                      type="text"
                      onChange={(e) => setCustomSwarm({ 
                        ...customSwarm, 
                        agents: e.target.value.split(',').map(a => a.trim()).filter(a => a) 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="e.g., Research Agent, Analysis Agent"
                      required
                    />
                  </div>
                </>
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setSelectedTemplate('');
                    setCustomSwarm({ name: '', description: '', agents: [] });
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Swarm
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {swarms.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No swarms created</h3>
          <p className="text-gray-500">
            Create your first agent swarm using one of our templates or build a custom one.
          </p>
        </div>
      )}
    </div>
  );
}