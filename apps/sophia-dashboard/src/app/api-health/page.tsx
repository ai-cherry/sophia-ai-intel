'use client';

import { useState, useEffect } from 'react';
import { config } from '@/lib/config';

interface ServiceHealth {
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy' | 'checking';
  latency: number;
  error?: string;
}

export default function ApiHealthPage() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [overallStatus, setOverallStatus] = useState<'healthy' | 'degraded' | 'unhealthy' | 'checking'>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const checkHealth = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
        setOverallStatus(data.status);
        setLastChecked(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      setOverallStatus('unhealthy');
    }
  };

  useEffect(() => {
    checkHealth();
    
    if (autoRefresh) {
      const interval = setInterval(checkHealth, config.ui.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unhealthy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400 bg-green-900/30';
      case 'unhealthy': return 'text-red-400 bg-red-900/30';
      default: return 'text-gray-400 bg-gray-900/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">API Health Monitor</h1>
            <p className="text-gray-400 mt-2">Real-time service health monitoring</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg transition ${
                autoRefresh 
                  ? 'bg-green-600/20 text-green-400 border border-green-600/50' 
                  : 'bg-gray-700 text-gray-300'
              }`}
            >
              Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
            </button>
            <button
              onClick={checkHealth}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
            >
              Check Now
            </button>
          </div>
        </div>

        {/* Overall Status */}
        <div className="bg-black/30 backdrop-blur rounded-xl p-6 mb-8 border border-purple-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-4 h-4 rounded-full ${getStatusColor(overallStatus)} animate-pulse`}></div>
              <div>
                <h2 className="text-xl font-semibold text-white">System Status</h2>
                <p className="text-gray-400">
                  {overallStatus === 'healthy' && 'All systems operational'}
                  {overallStatus === 'degraded' && 'Some services are experiencing issues'}
                  {overallStatus === 'unhealthy' && 'Major service disruption'}
                  {overallStatus === 'checking' && 'Checking services...'}
                </p>
              </div>
            </div>
            {lastChecked && (
              <div className="text-sm text-gray-400">
                Last checked: {lastChecked.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, i) => (
            <div 
              key={i} 
              className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/40 transition"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">{service.name}</h3>
                  <p className="text-xs text-gray-500 mt-1 break-all">{service.url}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(service.status)}`}>
                  {service.status}
                </span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Latency</span>
                  <span className={service.latency < 200 ? 'text-green-400' : service.latency < 500 ? 'text-yellow-400' : 'text-red-400'}>
                    {service.latency}ms
                  </span>
                </div>
                
                {service.error && (
                  <div className="mt-2 p-2 bg-red-900/20 rounded text-xs text-red-400">
                    {service.error}
                  </div>
                )}
                
                {/* Latency Bar */}
                <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all ${
                      service.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min((200 / service.latency) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {services.length === 0 && overallStatus !== 'checking' && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔍</div>
            <p className="text-gray-400">No services configured</p>
            <p className="text-sm text-gray-500 mt-2">
              Configure HEALTH_TARGETS environment variable
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
