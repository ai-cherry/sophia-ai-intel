'use client';

import { useState, useEffect } from 'react';

interface Activity {
  id: string;
  timestamp: Date;
  type: 'agent' | 'system' | 'error' | 'success';
  agentId?: string;
  agentType?: string;
  action: string;
  details?: string;
  status?: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
}

export default function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'agent' | 'system' | 'error'>('all');

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8096/ws/dashboard');
      
      ws.onopen = () => {
        console.log('ActivityFeed connected to WebSocket');
        setIsConnected(true);
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'activity' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different message types
          if (data.type === 'agent_update') {
            const activity: Activity = {
              id: `activity-${Date.now()}-${Math.random()}`,
              timestamp: new Date(),
              type: 'agent',
              agentId: data.agent_id,
              agentType: data.agent_type,
              action: data.action || 'Processing',
              details: data.details || data.message,
              status: data.status || 'in_progress',
              progress: data.progress
            };
            setActivities(prev => [activity, ...prev].slice(0, 100)); // Keep last 100
          } else if (data.type === 'system') {
            const activity: Activity = {
              id: `system-${Date.now()}`,
              timestamp: new Date(),
              type: 'system',
              action: data.message || 'System update',
              status: 'completed'
            };
            setActivities(prev => [activity, ...prev].slice(0, 100));
          } else if (data.type === 'error') {
            const activity: Activity = {
              id: `error-${Date.now()}`,
              timestamp: new Date(),
              type: 'error',
              action: 'Error occurred',
              details: data.error || data.message,
              status: 'failed'
            };
            setActivities(prev => [activity, ...prev].slice(0, 100));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      return ws;
    };

    const ws = connectWebSocket();

    // Also poll REST API for initial data and fallback
    const pollActivities = async () => {
      try {
        const response = await fetch('/api/agents?action=activity');
        if (response.ok) {
          const data = await response.json();
          if (data.activities) {
            const formattedActivities = data.activities.map((a: any) => ({
              id: a.id || `activity-${Date.now()}-${Math.random()}`,
              timestamp: new Date(a.timestamp || Date.now()),
              type: a.type || 'agent',
              agentId: a.agent_id,
              agentType: a.agent_type,
              action: a.action || a.message || 'Activity',
              details: a.details,
              status: a.status || 'in_progress',
              progress: a.progress
            }));
            setActivities(prev => {
              // Merge with existing, avoiding duplicates
              const existingIds = new Set(prev.map(p => p.id));
              const newActivities = formattedActivities.filter((a: Activity) => !existingIds.has(a.id));
              return [...newActivities, ...prev].slice(0, 100);
            });
          }
        }
      } catch (error) {
        console.error('Failed to fetch activities:', error);
      }
    };

    // Initial poll
    pollActivities();
    
    // Poll every 5 seconds as fallback
    const pollInterval = setInterval(pollActivities, 5000);

    return () => {
      clearInterval(pollInterval);
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const toggleExpanded = (id: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      case 'in_progress': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'agent': return '🤖';
      case 'system': return '⚙️';
      case 'error': return '⚠️';
      case 'success': return '✅';
      default: return '📌';
    }
  };

  const filteredActivities = activities.filter(a => 
    filter === 'all' || a.type === filter
  );

  return (
    <div className="h-full flex flex-col bg-gray-900/50 backdrop-blur-lg border border-cyan-500/20 rounded-lg">
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/20">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-white">Activity Feed</h3>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-xs text-gray-400">
                {isConnected ? 'Live' : 'Reconnecting...'}
              </span>
            </div>
          </div>
          <span className="text-xs text-gray-400">
            {filteredActivities.length} activities
          </span>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2">
          {(['all', 'agent', 'system', 'error'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded transition-all ${
                filter === f
                  ? 'bg-cyan-600/30 text-cyan-400 border border-cyan-600/50'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== 'all' && (
                <span className="ml-1 opacity-60">
                  ({activities.filter(a => a.type === f).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredActivities.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3 opacity-20">🔍</div>
            <p className="text-gray-500 text-sm">No activities yet</p>
            <p className="text-gray-600 text-xs mt-1">Deploy agents to see activity</p>
          </div>
        ) : (
          filteredActivities.map(activity => (
            <div
              key={activity.id}
              className="bg-gray-800/30 rounded-lg p-3 hover:bg-gray-800/50 transition-all cursor-pointer"
              onClick={() => toggleExpanded(activity.id)}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl mt-0.5">{getTypeIcon(activity.type)}</span>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {activity.agentType && (
                      <span className="text-xs px-2 py-0.5 bg-cyan-600/20 text-cyan-400 rounded">
                        {activity.agentType}
                      </span>
                    )}
                    {activity.agentId && (
                      <span className="text-xs text-gray-500">
                        {activity.agentId.slice(0, 8)}...
                      </span>
                    )}
                    <span className={`text-xs ${getStatusColor(activity.status)}`}>
                      {activity.status?.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <p className="text-sm text-white mb-1">{activity.action}</p>
                  
                  {activity.progress !== undefined && (
                    <div className="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-purple-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${activity.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {expandedItems.has(activity.id) && activity.details && (
                    <p className="text-xs text-gray-400 mt-2 p-2 bg-gray-900/50 rounded">
                      {activity.details}
                    </p>
                  )}
                  
                  <span className="text-xs text-gray-500">
                    {activity.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="p-3 border-t border-cyan-500/20 bg-gray-900/70">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="text-cyan-400 font-semibold">
              {activities.filter(a => a.status === 'in_progress').length}
            </div>
            <div className="text-gray-500">Active</div>
          </div>
          <div className="text-center">
            <div className="text-green-400 font-semibold">
              {activities.filter(a => a.status === 'completed').length}
            </div>
            <div className="text-gray-500">Complete</div>
          </div>
          <div className="text-center">
            <div className="text-red-400 font-semibold">
              {activities.filter(a => a.status === 'failed').length}
            </div>
            <div className="text-gray-500">Failed</div>
          </div>
        </div>
      </div>
    </div>
  );
}