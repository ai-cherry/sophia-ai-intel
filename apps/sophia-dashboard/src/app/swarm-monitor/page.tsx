'use client';

import { useState, useEffect } from 'react';
import { swarmClient } from '@/lib/swarm-client';
import type { SwarmStatus } from '@/lib/swarm-client';

export default function SwarmMonitorPage() {
  const [activeSwarms, setActiveSwarms] = useState<Map<string, SwarmStatus>>(new Map());
  const [swarmHistory, setSwarmHistory] = useState<SwarmStatus[]>([]);
  const [selectedSwarm, setSelectedSwarm] = useState<SwarmStatus | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSwarms();
    
    if (autoRefresh) {
      const interval = setInterval(loadSwarms, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadSwarms = async () => {
    try {
      const swarms = await swarmClient.listSwarms();
      const swarmMap = new Map<string, SwarmStatus>();
      
      swarms.forEach(swarm => {
        swarmMap.set(swarm.swarm_id, swarm);
        
        // Subscribe to active swarms
        if (swarm.status !== 'completed' && swarm.status !== 'error') {
          swarmClient.subscribeToSwarm(swarm.swarm_id, (status) => {
            setActiveSwarms(prev => {
              const updated = new Map(prev);
              updated.set(swarm.swarm_id, status);
              return updated;
            });
            
            // Add to history when completed
            if (status.status === 'completed' || status.status === 'error') {
              setSwarmHistory(prev => [status, ...prev].slice(0, 50));
            }
          });
        } else {
          // Add completed swarms to history
          setSwarmHistory(prev => {
            if (!prev.find(s => s.swarm_id === swarm.swarm_id)) {
              return [swarm, ...prev].slice(0, 50);
            }
            return prev;
          });
        }
      });
      
      setActiveSwarms(swarmMap);
    } catch (error) {
      console.error('Failed to load swarms:', error);
    }
  };

  const stopSwarm = async (swarmId: string) => {
    const success = await swarmClient.stopSwarm(swarmId);
    if (success) {
      await loadSwarms();
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-900/30';
      case 'error': return 'text-red-400 bg-red-900/30';
      case 'executing': return 'text-yellow-400 bg-yellow-900/30';
      default: return 'text-gray-400 bg-gray-900/30';
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'completed': return 'from-green-600 to-green-400';
      case 'error': return 'from-red-600 to-red-400';
      case 'executing': return 'from-yellow-600 to-yellow-400';
      default: return 'from-purple-600 to-cyan-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Swarm Monitor</h1>
            <p className="text-gray-400 mt-2">Real-time swarm orchestration monitoring</p>
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
              onClick={loadSwarms}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
            >
              Refresh Now
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-black/30 backdrop-blur rounded-xl p-4 border border-purple-500/20">
            <div className="text-2xl font-bold text-white">{activeSwarms.size}</div>
            <div className="text-sm text-gray-400">Active Swarms</div>
          </div>
          <div className="bg-black/30 backdrop-blur rounded-xl p-4 border border-purple-500/20">
            <div className="text-2xl font-bold text-green-400">
              {Array.from(activeSwarms.values()).filter(s => s.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-400">Completed</div>
          </div>
          <div className="bg-black/30 backdrop-blur rounded-xl p-4 border border-purple-500/20">
            <div className="text-2xl font-bold text-yellow-400">
              {Array.from(activeSwarms.values()).filter(s => s.status === 'executing').length}
            </div>
            <div className="text-sm text-gray-400">Executing</div>
          </div>
          <div className="bg-black/30 backdrop-blur rounded-xl p-4 border border-purple-500/20">
            <div className="text-2xl font-bold text-red-400">
              {Array.from(activeSwarms.values()).filter(s => s.status === 'error').length}
            </div>
            <div className="text-sm text-gray-400">Errors</div>
          </div>
        </div>

        {/* Active Swarms */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Active Swarms</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from(activeSwarms.values())
              .filter(s => s.status !== 'completed' && s.status !== 'error')
              .map(swarm => (
                <div 
                  key={swarm.swarm_id} 
                  className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/40 transition cursor-pointer"
                  onClick={() => setSelectedSwarm(swarm)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="text-white font-semibold">{swarm.swarm_type}</div>
                      <div className="text-xs text-gray-500 mt-1">ID: {swarm.swarm_id.slice(0, 12)}...</div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(swarm.status)}`}>
                      {swarm.status}
                    </span>
                  </div>
                  
                  {swarm.current_task && (
                    <p className="text-sm text-gray-400 mb-3 line-clamp-2">{swarm.current_task}</p>
                  )}
                  
                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Progress</span>
                      <span className="text-cyan-400">{Math.round(swarm.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${getProgressColor(swarm.status)} transition-all`}
                        style={{ width: `${swarm.progress * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  {/* Agents */}
                  {swarm.agents && swarm.agents.length > 0 && (
                    <div className="mt-3 flex gap-2 flex-wrap">
                      {swarm.agents.slice(0, 3).map(agent => (
                        <span key={agent.id} className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-300">
                          {agent.role}
                        </span>
                      ))}
                      {swarm.agents.length > 3 && (
                        <span className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400">
                          +{swarm.agents.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                  
                  {/* Actions */}
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        stopSwarm(swarm.swarm_id);
                      }}
                      className="text-xs px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded transition"
                    >
                      Stop
                    </button>
                  </div>
                </div>
              ))}
          </div>
          
          {Array.from(activeSwarms.values()).filter(s => s.status !== 'completed' && s.status !== 'error').length === 0 && (
            <div className="text-center py-12 bg-black/30 backdrop-blur rounded-xl border border-purple-500/20">
              <div className="text-4xl mb-4">🐝</div>
              <p className="text-gray-400">No active swarms</p>
              <p className="text-sm text-gray-500 mt-2">Deploy agents from the Agent Factory to see them here</p>
            </div>
          )}
        </div>

        {/* History */}
        {swarmHistory.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">History</h2>
            <div className="bg-black/30 backdrop-blur rounded-xl border border-purple-500/20 overflow-hidden">
              <table className="w-full">
                <thead className="bg-purple-900/20">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Type</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">ID</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Status</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Task</th>
                  </tr>
                </thead>
                <tbody>
                  {swarmHistory.map((swarm, i) => (
                    <tr 
                      key={i} 
                      className="border-t border-purple-500/10 hover:bg-purple-900/10 cursor-pointer"
                      onClick={() => setSelectedSwarm(swarm)}
                    >
                      <td className="px-4 py-3 text-sm text-white">{swarm.swarm_type}</td>
                      <td className="px-4 py-3 text-xs text-gray-400 font-mono">
                        {swarm.swarm_id.slice(0, 12)}...
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(swarm.status)}`}>
                          {swarm.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400 truncate max-w-xs">
                        {swarm.current_task || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Selected Swarm Details Modal */}
        {selectedSwarm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur flex items-center justify-center p-8 z-50" onClick={() => setSelectedSwarm(null)}>
            <div className="bg-gray-900 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto border border-purple-500/30" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">Swarm Details</h3>
                  <p className="text-sm text-gray-400 mt-1">{selectedSwarm.swarm_type}</p>
                </div>
                <button
                  onClick={() => setSelectedSwarm(null)}
                  className="text-gray-400 hover:text-white transition"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400">ID</label>
                  <p className="text-white font-mono text-sm">{selectedSwarm.swarm_id}</p>
                </div>
                
                <div>
                  <label className="text-sm text-gray-400">Status</label>
                  <p><span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(selectedSwarm.status)}`}>
                    {selectedSwarm.status}
                  </span></p>
                </div>
                
                <div>
                  <label className="text-sm text-gray-400">Progress</label>
                  <div className="mt-1">
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-full bg-gradient-to-r ${getProgressColor(selectedSwarm.status)} transition-all rounded-full`}
                        style={{ width: `${selectedSwarm.progress * 100}%` }}
                      />
                    </div>
                    <p className="text-xs text-cyan-400 mt-1">{Math.round(selectedSwarm.progress * 100)}%</p>
                  </div>
                </div>
                
                {selectedSwarm.current_task && (
                  <div>
                    <label className="text-sm text-gray-400">Current Task</label>
                    <p className="text-white text-sm">{selectedSwarm.current_task}</p>
                  </div>
                )}
                
                {selectedSwarm.agents && selectedSwarm.agents.length > 0 && (
                  <div>
                    <label className="text-sm text-gray-400">Agents</label>
                    <div className="mt-2 space-y-2">
                      {selectedSwarm.agents.map(agent => (
                        <div key={agent.id} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                          <span className="text-white text-sm">{agent.role}</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            agent.status === 'active' ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'
                          }`}>
                            {agent.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {selectedSwarm.results && (
                  <div>
                    <label className="text-sm text-gray-400">Results</label>
                    <pre className="mt-2 p-3 bg-gray-800 rounded text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedSwarm.results, null, 2)}
                    </pre>
                  </div>
                )}
                
                {selectedSwarm.error && (
                  <div>
                    <label className="text-sm text-gray-400">Error</label>
                    <div className="mt-2 p-3 bg-red-900/20 rounded text-sm text-red-400">
                      {selectedSwarm.error}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
