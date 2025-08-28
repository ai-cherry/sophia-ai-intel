'use client';

import React, { useState, useEffect } from 'react';
import { swarmClient, SwarmType, SwarmStatus, AgentInfo, PlansResponse } from '@/lib/swarm-client';

export default function SwarmManager() {
  const [activeSwarms, setActiveSwarms] = useState<SwarmStatus[]>([]);
  const [availableAgents, setAvailableAgents] = useState<AgentInfo[]>([]);
  const [selectedSwarm, setSelectedSwarm] = useState<string | null>(null);
  const [taskInput, setTaskInput] = useState('');
  const [selectedSwarmType, setSelectedSwarmType] = useState<SwarmType>(SwarmType.CODING);
  const [plans, setPlans] = useState<PlansResponse | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isGeneratingPlans, setIsGeneratingPlans] = useState(false);

  useEffect(() => {
    loadSwarms();
    loadAgents();
    const interval = setInterval(loadSwarms, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadSwarms = async () => {
    try {
      const swarms = await swarmClient.listSwarms();
      setActiveSwarms(swarms);
    } catch (error) {
      console.error('Failed to load swarms:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const agents = await swarmClient.listAgents();
      setAvailableAgents(agents);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const createSwarm = async () => {
    if (!taskInput.trim()) return;
    
    setIsCreating(true);
    try {
      const result = await swarmClient.createSwarm({
        swarm_type: selectedSwarmType,
        task: taskInput,
        context: {},
        config: {}
      });
      
      if (result.success) {
        setTaskInput('');
        await loadSwarms();
        setSelectedSwarm(result.swarm_id);
      }
    } catch (error) {
      console.error('Failed to create swarm:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const generatePlans = async () => {
    if (!taskInput.trim()) return;
    
    setIsGeneratingPlans(true);
    try {
      const plansResponse = await swarmClient.generatePlans(taskInput);
      setPlans(plansResponse);
    } catch (error) {
      console.error('Failed to generate plans:', error);
    } finally {
      setIsGeneratingPlans(false);
    }
  };

  const stopSwarm = async (swarmId: string) => {
    try {
      await swarmClient.stopSwarm(swarmId);
      await loadSwarms();
    } catch (error) {
      console.error('Failed to stop swarm:', error);
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Swarm Creation and Control */}
      <div className="w-1/3 p-6 border-r border-gray-700">
        <h2 className="text-2xl font-bold mb-6 text-cyan-400">Swarm Control</h2>
        
        {/* Task Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Task Description</label>
          <textarea
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            className="w-full p-3 rounded-lg bg-gray-800 border border-gray-600 text-white resize-none"
            rows={4}
            placeholder="Describe the task for the swarm..."
          />
        </div>

        {/* Swarm Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Swarm Type</label>
          <select
            value={selectedSwarmType}
            onChange={(e) => setSelectedSwarmType(e.target.value as SwarmType)}
            className="w-full p-3 rounded-lg bg-gray-800 border border-gray-600 text-white"
          >
            <option value={SwarmType.CODING}>Coding Swarm</option>
            <option value={SwarmType.RESEARCH}>Research Swarm</option>
            <option value={SwarmType.ANALYSIS}>Analysis Swarm</option>
            <option value={SwarmType.PLANNING}>Planning Swarm</option>
          </select>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={createSwarm}
            disabled={isCreating || !taskInput.trim()}
            className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 rounded-lg transition-colors"
          >
            {isCreating ? 'Creating...' : 'Deploy Swarm'}
          </button>
          <button
            onClick={generatePlans}
            disabled={isGeneratingPlans || !taskInput.trim()}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg transition-colors"
          >
            {isGeneratingPlans ? 'Planning...' : 'Generate Plans'}
          </button>
        </div>

        {/* Active Swarms List */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Active Swarms</h3>
          <div className="space-y-2">
            {activeSwarms.map((swarm) => (
              <div
                key={swarm.swarm_id}
                onClick={() => setSelectedSwarm(swarm.swarm_id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedSwarm === swarm.swarm_id
                    ? 'border-cyan-500 bg-gray-800'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{swarm.swarm_type}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {swarm.current_task?.substring(0, 50)}...
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded ${
                      swarm.status === 'active' ? 'bg-green-900 text-green-300' :
                      swarm.status === 'completed' ? 'bg-blue-900 text-blue-300' :
                      swarm.status === 'failed' ? 'bg-red-900 text-red-300' :
                      'bg-gray-700 text-gray-300'
                    }`}>
                      {swarm.status}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        stopSwarm(swarm.swarm_id);
                      }}
                      className="text-red-400 hover:text-red-300"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-cyan-500 h-2 rounded-full transition-all"
                      style={{ width: `${swarm.progress * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Middle Panel - Swarm Details */}
      <div className="flex-1 p-6 border-r border-gray-700">
        {selectedSwarm ? (
          <SwarmDetails swarmId={selectedSwarm} />
        ) : plans ? (
          <PlanVisualization plans={plans} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a swarm or generate plans to view details
          </div>
        )}
      </div>

      {/* Right Panel - Available Agents */}
      <div className="w-1/4 p-6">
        <h3 className="text-lg font-semibold mb-4">Available Agents</h3>
        <div className="space-y-2">
          {availableAgents.map((agent) => (
            <div key={agent.id} className="p-3 rounded-lg bg-gray-800 border border-gray-700">
              <div className="font-medium text-sm">{agent.name}</div>
              <div className="text-xs text-gray-400 mt-1">{agent.type}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {agent.capabilities.slice(0, 3).map((cap, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-gray-700 rounded">
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SwarmDetails({ swarmId }: { swarmId: string }) {
  const [swarm, setSwarm] = useState<SwarmStatus | null>(null);

  useEffect(() => {
    const unsubscribe = swarmClient.subscribeToSwarm(swarmId, (status) => {
      setSwarm(status);
    });

    return unsubscribe;
  }, [swarmId]);

  if (!swarm) return <div>Loading swarm details...</div>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Swarm Details</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Task</h3>
        <p className="text-gray-300">{swarm.current_task}</p>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Active Agents</h3>
        <div className="grid grid-cols-2 gap-3">
          {swarm.agents.map((agent) => (
            <div key={agent.id} className="p-3 rounded-lg bg-gray-800 border border-gray-700">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-xs text-gray-400">{agent.type}</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  agent.status === 'active' ? 'bg-green-900 text-green-300' :
                  agent.status === 'idle' ? 'bg-gray-700 text-gray-300' :
                  'bg-yellow-900 text-yellow-300'
                }`}>
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {swarm.results && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Results</h3>
          <pre className="p-4 rounded-lg bg-gray-800 text-sm overflow-auto">
            {JSON.stringify(swarm.results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function PlanVisualization({ plans }: { plans: PlansResponse }) {
  const [selectedPlan, setSelectedPlan] = useState<'cutting_edge' | 'conservative' | 'synthesis'>('synthesis');

  const planTypes = [
    { key: 'cutting_edge', label: 'Cutting-Edge', color: 'text-red-400', bgColor: 'bg-red-900' },
    { key: 'conservative', label: 'Conservative', color: 'text-blue-400', bgColor: 'bg-blue-900' },
    { key: 'synthesis', label: 'Synthesis', color: 'text-green-400', bgColor: 'bg-green-900' }
  ] as const;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Generated Plans</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Task</h3>
        <p className="text-gray-300">{plans.task}</p>
      </div>

      <div className="flex gap-3 mb-6">
        {planTypes.map((type) => (
          <button
            key={type.key}
            onClick={() => setSelectedPlan(type.key)}
            className={`px-4 py-2 rounded-lg transition-all ${
              selectedPlan === type.key
                ? `${type.bgColor} ${type.color}`
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            {type.label}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        <div className="p-4 rounded-lg bg-gray-800 border border-gray-700">
          <h4 className="font-semibold mb-3 text-cyan-400">
            {planTypes.find(t => t.key === selectedPlan)?.label} Plan
          </h4>
          <pre className="whitespace-pre-wrap text-sm text-gray-300">
            {plans.plans[selectedPlan].plan}
          </pre>
          
          {plans.plans[selectedPlan].risk_assessment && (
            <div className="mt-4 p-3 rounded bg-gray-900">
              <h5 className="text-sm font-semibold mb-2">Risk Assessment</h5>
              <pre className="text-xs text-gray-400">
                {JSON.stringify(plans.plans[selectedPlan].risk_assessment, null, 2)}
              </pre>
            </div>
          )}
          
          {plans.plans[selectedPlan].artifacts && plans.plans[selectedPlan].artifacts!.length > 0 && (
            <div className="mt-4">
              <h5 className="text-sm font-semibold mb-2">Artifacts</h5>
              <div className="flex flex-wrap gap-2">
                {plans.plans[selectedPlan].artifacts!.map((artifact, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-gray-700 rounded">
                    {artifact}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 p-4 rounded-lg bg-purple-900 bg-opacity-30 border border-purple-700">
        <h4 className="font-semibold mb-2 text-purple-400">Recommendation</h4>
        <p className="text-sm text-gray-300">{plans.recommendation}</p>
      </div>
    </div>
  );
}