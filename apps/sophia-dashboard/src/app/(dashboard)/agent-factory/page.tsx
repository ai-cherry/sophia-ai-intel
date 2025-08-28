'use client';

import { useState } from 'react';
import AgentManagement from '../../../components/AgentManagement';
import SwarmCreator from '../../../components/SwarmCreator';
import AgentMonitoring from '../../../components/AgentMonitoring';

export default function AgentFactoryPage() {
  const [activeTab, setActiveTab] = useState('agents');

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Factory</h1>
        <p className="text-gray-600">Create, manage, and monitor your AI agents and swarms</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('agents')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'agents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Agent Management
          </button>
          <button
            onClick={() => setActiveTab('swarms')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'swarms'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Swarm Creator
          </button>
          <button
            onClick={() => setActiveTab('monitoring')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'monitoring'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Monitoring
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'agents' && <AgentManagement />}
        {activeTab === 'swarms' && <SwarmCreator />}
        {activeTab === 'monitoring' && <AgentMonitoring />}
      </div>
    </div>
  );
}