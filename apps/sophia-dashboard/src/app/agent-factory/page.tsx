'use client';

import { useState } from 'react';
import { swarmClient } from '@/lib/swarm-client';
import { config } from '@/lib/config';

interface AgentTemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  icon: string;
  config: any;
}

export default function AgentFactoryPage() {
  const [templates] = useState<AgentTemplate[]>([
    {
      id: 'research',
      name: 'Research Agent',
      type: 'research',
      description: 'Deep web research and knowledge synthesis',
      icon: '🔍',
      config: { sources: ['tavily', 'perplexity', 'knowledge_base'] }
    },
    {
      id: 'coding',
      name: 'Coding Agent',
      type: 'coding',
      description: 'Code generation and optimization',
      icon: '💻',
      config: { languages: ['python', 'typescript', 'javascript'] }
    },
    {
      id: 'analysis',
      name: 'Analysis Agent',
      type: 'analysis',
      description: 'Data analysis and insights generation',
      icon: '📊',
      config: { methods: ['statistical', 'machine_learning', 'visualization'] }
    },
    {
      id: 'planning',
      name: 'Planning Agent',
      type: 'planning',
      description: 'Strategic planning with multiple approaches',
      icon: '🎯',
      config: { approaches: ['cutting_edge', 'conservative', 'synthesis'] }
    }
  ]);

  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null);
  const [taskInput, setTaskInput] = useState('');
  const [deployingId, setDeployingId] = useState<string | null>(null);
  const [deployedAgents, setDeployedAgents] = useState<Array<{id: string; type: string; task: string; timestamp: Date}>>([]);

  const deployAgent = async (template: AgentTemplate) => {
    if (!taskInput.trim()) {
      alert('Please enter a task for the agent');
      return;
    }

    setDeployingId(template.id);
    
    try {
      const result = await swarmClient.createSwarm({
        swarm_type: template.type,
        task: taskInput,
        context: { 
          ...template.config,
          source: 'agent-factory'
        }
      });

      if (result.success) {
        // Subscribe to the swarm for live updates
        swarmClient.subscribeToSwarm(result.swarm_id, (status) => {
          console.log('Swarm status update:', status);
        });

        setDeployedAgents(prev => [...prev, {
          id: result.swarm_id,
          type: template.type,
          task: taskInput,
          timestamp: new Date()
        }]);

        setTaskInput('');
        setSelectedTemplate(null);
      }
    } catch (error) {
      console.error('Failed to deploy agent:', error);
      alert('Failed to deploy agent. Check console for details.');
    } finally {
      setDeployingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Agent Factory</h1>
          <p className="text-gray-400 mt-2">Create and deploy specialized AI agents</p>
        </div>

        {/* Agent Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {templates.map((template) => (
            <div
              key={template.id}
              onClick={() => setSelectedTemplate(template)}
              className={`bg-black/30 backdrop-blur rounded-xl p-6 border cursor-pointer transition-all ${
                selectedTemplate?.id === template.id
                  ? 'border-purple-500 shadow-lg shadow-purple-500/20'
                  : 'border-purple-500/20 hover:border-purple-500/40'
              }`}
            >
              <div className="text-4xl mb-4">{template.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-2">{template.name}</h3>
              <p className="text-sm text-gray-400">{template.description}</p>
              {deployingId === template.id && (
                <div className="mt-4 text-xs text-cyan-400 animate-pulse">
                  Deploying...
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Deployment Panel */}
        {selectedTemplate && (
          <div className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">
              Deploy {selectedTemplate.name}
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Task Description</label>
                <textarea
                  value={taskInput}
                  onChange={(e) => setTaskInput(e.target.value)}
                  placeholder={`What should the ${selectedTemplate.name.toLowerCase()} do?`}
                  className="w-full h-32 px-4 py-3 bg-gray-800/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Configuration</label>
                <pre className="p-4 bg-gray-800/30 rounded-lg text-xs text-gray-300 overflow-x-auto">
                  {JSON.stringify(selectedTemplate.config, null, 2)}
                </pre>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => deployAgent(selectedTemplate)}
                  disabled={deployingId !== null || !taskInput.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-600 text-white rounded-lg hover:from-purple-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {deployingId === selectedTemplate.id ? 'Deploying...' : 'Deploy Agent'}
                </button>
                <button
                  onClick={() => {
                    setSelectedTemplate(null);
                    setTaskInput('');
                  }}
                  className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Deployed Agents */}
        {deployedAgents.length > 0 && (
          <div className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20">
            <h2 className="text-xl font-semibold text-white mb-4">Deployed Agents</h2>
            <div className="space-y-3">
              {deployedAgents.map((agent, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg">
                  <div>
                    <div className="text-white font-medium">{agent.type}</div>
                    <div className="text-sm text-gray-400">{agent.task}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      ID: {agent.id} • {agent.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm text-green-400">Active</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
