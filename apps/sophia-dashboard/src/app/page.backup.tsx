'use client';

import { useState, useEffect } from 'react';
import ChatInterface from '../components/ChatInterface';
import GitHubIntegration from '../components/GitHubIntegration';
import { apiClient } from '../lib/api';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('chat');

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await apiClient.healthCheck();
      if (response.data) {
        setHealthStatus(response.data);
      }
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const tabs = [
    { id: 'chat', name: '💬 Chat', component: <ChatInterface /> },
    { id: 'github', name: '🐙 GitHub', component: <GitHubIntegration /> },
    { id: 'agents', name: '🤖 Agents', component: <div className="p-4 text-gray-500">Agent Management (Coming Soon)</div> },
    { id: 'swarms', name: '🐝 Swarms', component: <div className="p-4 text-gray-500">Swarm Orchestration (Coming Soon)</div> },
  ];

  return (
    <main className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Sophia AI Intelligence Platform</h1>
              <div className="ml-4 text-sm text-gray-500">
                v2.0 - Connected Backend
              </div>
            </div>
            
            {/* System Health Indicator */}
            <div className="flex items-center space-x-3">
              <button
                onClick={checkSystemHealth}
                className="text-sm px-3 py-1 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
              >
                🔄 Refresh Status
              </button>
              <div className="flex items-center space-x-2">
                {healthStatus.map((service, index) => (
                  <div
                    key={index}
                    className={`w-3 h-3 rounded-full ${
                      service.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                    }`}
                    title={`${service.service}: ${service.status}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* System Status Banner */}
        {healthStatus.length > 0 && (
          <div className="mb-8 bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-medium mb-3">System Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {healthStatus.map((service, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <span className="font-medium">{service.service}</span>
                  <span className={`px-2 py-1 text-xs rounded-full text-white ${
                    service.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`}>
                    {service.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {tabs.find(tab => tab.id === activeTab)?.component}
        </div>
      </div>
    </main>
  );
}