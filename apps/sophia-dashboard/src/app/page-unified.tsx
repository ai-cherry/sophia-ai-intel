'use client';

import { useState, useEffect, useRef } from 'react';
import { swarmClient } from '@/lib/swarm-client';
import type { SwarmStatus, SwarmEvent } from '@/lib/swarm-client';
import MessageRenderer from '@/components/MessageRenderer';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
  sections?: {
    summary?: string;
    actions?: Array<{type: string; status: string}>;
    research?: Array<{source: string; url: string}>;
    plans?: any;
    code?: Array<{task: string; language: string; code: string}>;
    github?: {pr_url?: string};
    events?: Array<SwarmEvent>;
  };
}

export default function UnifiedSophiaApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'I\'m Sophia, your unified AI orchestrator. I can research, deploy agents, analyze code, create PRs - all through this single chat. What would you like to accomplish?',
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [activeSwarms, setActiveSwarms] = useState<Map<string, SwarmStatus>>(new Map());
  const [swarmEvents, setSwarmEvents] = useState<SwarmEvent[]>([]);
  const [selectedView, setSelectedView] = useState('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const subscriptionsRef = useRef<Map<string, () => void>>(new Map());

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load active swarms on mount
  useEffect(() => {
    loadActiveSwarms();
    return () => {
      // Cleanup all subscriptions on unmount
      subscriptionsRef.current.forEach(unsubscribe => unsubscribe());
      swarmClient.disconnect();
    };
  }, []);

  const loadActiveSwarms = async () => {
    const swarms = await swarmClient.listSwarms();
    const swarmMap = new Map<string, SwarmStatus>();
    swarms.forEach(swarm => {
      swarmMap.set(swarm.swarm_id, swarm);
      // Subscribe to active swarms
      if (swarm.status !== 'completed' && swarm.status !== 'error') {
        subscribeToSwarm(swarm.swarm_id);
      }
    });
    setActiveSwarms(swarmMap);
  };

  const subscribeToSwarm = (swarmId: string) => {
    // Avoid duplicate subscriptions
    if (subscriptionsRef.current.has(swarmId)) return;
    
    const unsubscribe = swarmClient.subscribeToSwarm(swarmId, (status: SwarmStatus) => {
      // Update swarm status
      setActiveSwarms(prev => {
        const updated = new Map(prev);
        updated.set(swarmId, status);
        return updated;
      });
      
      // Add to event feed
      const event: SwarmEvent = {
        type: 'status',
        swarm_id: swarmId,
        data: status,
        timestamp: new Date().toISOString()
      };
      setSwarmEvents(prev => [event, ...prev].slice(0, 100)); // Keep last 100 events
      
      // If completed, unsubscribe
      if (status.status === 'completed' || status.status === 'error') {
        const unsub = subscriptionsRef.current.get(swarmId);
        if (unsub) {
          unsub();
          subscriptionsRef.current.delete(swarmId);
        }
      }
    });
    
    subscriptionsRef.current.set(swarmId, unsubscribe);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setConnectionStatus('processing');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          context: messages.slice(-5),
          activeSwarms: Array.from(activeSwarms.values())
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Handle structured response
        if (data.sections) {
          // If swarm was created, subscribe to it
          if (data.sections.actions) {
            data.sections.actions.forEach((action: any) => {
              if (action.type === 'swarm.created' && action.swarm_id) {
                subscribeToSwarm(action.swarm_id);
              }
            });
          }
          
          // Create message with sections
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.sections.summary || data.response || 'Processing...',
            timestamp: new Date(),
            sections: data.sections,
            metadata: data
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          // Fallback to simple response
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.response,
            timestamp: new Date(),
            metadata: data
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      } else {
        throw new Error('API request failed');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Connection issue. Retrying...',
        timestamp: new Date()
      }]);
      setConnectionStatus('disconnected');
      setTimeout(() => setConnectionStatus('connected'), 3000);
    } finally {
      setIsLoading(false);
      setConnectionStatus('connected');
    }
  };

  const renderMessage = (msg: Message) => {
    if (msg.sections) {
      return (
        <div className="space-y-3">
          {/* Summary */}
          {msg.sections.summary && (
            <div className="text-white">{msg.sections.summary}</div>
          )}
          
          {/* Actions */}
          {msg.sections.actions && msg.sections.actions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {msg.sections.actions.map((action, i) => (
                <span key={i} className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-xs">
                  {action.type}: {action.status}
                </span>
              ))}
            </div>
          )}
          
          {/* Research Citations */}
          {msg.sections.research && msg.sections.research.length > 0 && (
            <div className="border-l-2 border-cyan-500 pl-3 space-y-1">
              <div className="text-xs text-gray-400">Research Sources:</div>
              {msg.sections.research.map((cite, i) => (
                <div key={i} className="text-sm">
                  <a href={cite.url} className="text-cyan-400 hover:underline">
                    {cite.source}
                  </a>
                </div>
              ))}
            </div>
          )}
          
          {/* Code */}
          {msg.sections.code && msg.sections.code.length > 0 && (
            <div className="space-y-2">
              {msg.sections.code.map((code, i) => (
                <div key={i} className="bg-gray-900 rounded-lg p-3">
                  <div className="text-xs text-gray-400 mb-2">{code.task}</div>
                  <pre className="text-xs text-green-400 overflow-x-auto">
                    <code>{code.code}</code>
                  </pre>
                </div>
              ))}
            </div>
          )}
          
          {/* GitHub PR */}
          {msg.sections.github?.pr_url && (
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-600/20 rounded-lg">
              <span className="text-green-400">✓ PR Created:</span>
              <a href={msg.sections.github.pr_url} className="text-cyan-400 hover:underline">
                {msg.sections.github.pr_url.split('/').pop()}
              </a>
            </div>
          )}
        </div>
      );
    }
    
    return <MessageRenderer content={msg.content} role={msg.role} />;
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      {/* Left Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} transition-all duration-300 bg-black/40 backdrop-blur border-r border-purple-500/20 flex flex-col`}>
        <div className="p-4 border-b border-purple-500/20">
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-lg flex items-center justify-center text-white font-bold">
              S
            </div>
            {!sidebarCollapsed && (
              <div>
                <div className="text-white font-bold">Sophia AI</div>
                <div className="text-xs text-gray-400">Unified Interface</div>
              </div>
            )}
          </button>
        </div>
        
        <nav className="flex-1 p-2">
          <button
            onClick={() => setSelectedView('chat')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'chat' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>💬</span>
            {!sidebarCollapsed && <span>Chat</span>}
          </button>
          
          <button
            onClick={() => setSelectedView('api-health')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'api-health' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>💚</span>
            {!sidebarCollapsed && <span>API Health</span>}
          </button>
          
          <button
            onClick={() => setSelectedView('agent-factory')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'agent-factory' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>🏭</span>
            {!sidebarCollapsed && <span>Agent Factory</span>}
          </button>
          
          <button
            onClick={() => setSelectedView('swarm-monitor')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'swarm-monitor' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>🐝</span>
            {!sidebarCollapsed && <span>Swarm Monitor</span>}
          </button>
          
          <button
            onClick={() => setSelectedView('code')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'code' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>📝</span>
            {!sidebarCollapsed && <span>Code</span>}
          </button>
          
          <button
            onClick={() => setSelectedView('metrics')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
              selectedView === 'metrics' ? 'bg-purple-600/30 text-white' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <span>📊</span>
            {!sidebarCollapsed && <span>Metrics</span>}
          </button>
        </nav>
        
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-purple-500/20">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Status</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : connectionStatus === 'processing' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'}`}></div>
                <span className={connectionStatus === 'connected' ? 'text-green-400' : connectionStatus === 'processing' ? 'text-yellow-400' : 'text-red-400'}>
                  {connectionStatus}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedView === 'chat' && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-2xl px-4 py-3 rounded-lg ${
                    msg.role === 'user' 
                      ? 'bg-purple-600/30 text-white' 
                      : msg.role === 'system'
                      ? 'bg-yellow-600/20 text-yellow-200'
                      : 'bg-gray-800/50 text-gray-100'
                  }`}>
                    <div className="text-xs text-gray-400 mb-1">
                      {msg.timestamp.toLocaleTimeString()}
                    </div>
                    {renderMessage(msg)}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-800/50 px-4 py-3 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-75"></div>
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-150"></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Activity Feed */}
            {swarmEvents.length > 0 && (
              <div className="border-t border-purple-500/20 p-4 max-h-48 overflow-y-auto bg-black/20">
                <div className="text-xs text-gray-400 mb-2">Live Activity ({activeSwarms.size} active swarms)</div>
                <div className="space-y-1">
                  {swarmEvents.slice(0, 5).map((event, i) => (
                    <div key={`${event.swarm_id}-${i}`} className="flex items-center gap-2 text-xs">
                      <span className="text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      <span className="px-2 py-0.5 bg-purple-600/20 text-purple-400 rounded">
                        {event.data.swarm_type || 'swarm'}
                      </span>
                      <span className={`text-${event.data.status === 'completed' ? 'green' : event.data.status === 'error' ? 'red' : 'yellow'}-400`}>
                        {event.data.status}
                      </span>
                      {event.data.current_task && (
                        <span className="text-gray-400 truncate">{event.data.current_task}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="border-t border-purple-500/20 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Ask me to research, deploy agents, analyze code, or anything else..."
                  className="flex-1 px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-cyan-600 text-white rounded-lg hover:from-purple-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}

        {/* Other views would go here */}
        {selectedView === 'api-health' && (
          <div className="flex-1 p-6">
            <h2 className="text-2xl font-bold text-white mb-4">API Health</h2>
            <p className="text-gray-400">Real API health monitoring will be displayed here</p>
          </div>
        )}

        {selectedView === 'agent-factory' && (
          <div className="flex-1 p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Agent Factory</h2>
            <p className="text-gray-400">Create and deploy agents through the chat interface</p>
          </div>
        )}

        {selectedView === 'swarm-monitor' && (
          <div className="flex-1 p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Swarm Monitor</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from(activeSwarms.values()).map(swarm => (
                <div key={swarm.swarm_id} className="bg-gray-800/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-semibold">{swarm.swarm_type}</span>
                    <span className={`px-2 py-1 text-xs rounded ${
                      swarm.status === 'completed' ? 'bg-green-600/30 text-green-400' :
                      swarm.status === 'error' ? 'bg-red-600/30 text-red-400' :
                      'bg-yellow-600/30 text-yellow-400'
                    }`}>
                      {swarm.status}
                    </span>
                  </div>
                  {swarm.current_task && (
                    <p className="text-sm text-gray-400 mb-2">{swarm.current_task}</p>
                  )}
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-purple-600 to-cyan-600 h-2 rounded-full transition-all"
                      style={{ width: `${swarm.progress * 100}%` }}
                    ></div>
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
