'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatSections } from '../api/chat/sophia-supreme';

type Tab = 'chat' | 'api_health' | 'agent_factory' | 'swarm_monitor' | 'code' | 'metrics';

export default function SophiaSupreme() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [messages, setMessages] = useState<Array<{ role: string; content: string; sections?: ChatSections }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);
  const [healthData, setHealthData] = useState<any>(null);
  const [swarmData, setSwarmData] = useState<any>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect WebSocket
    wsRef.current = new WebSocket('ws://localhost:8096/ws/dashboard');
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'swarm.update') {
        setSwarmData((prev: any) => [...prev, data]);
      }
    };
    
    // Poll health
    const healthInterval = setInterval(async () => {
      if (activeTab === 'api_health') {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: [{ role: 'user', content: 'check health status' }], session_id: sessionId })
        });
        if (res.ok) {
          const data = await res.json();
          setHealthData(data.sections);
        }
      }
    }, 5000);

    return () => {
      wsRef.current?.close();
      clearInterval(healthInterval);
    };
  }, [activeTab, sessionId]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          session_id: sessionId,
          tenant: 'default'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.sections.summary || 'Processing...',
          sections: data.sections
        }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'api_health', label: 'API Health', icon: '🔧' },
    { id: 'agent_factory', label: 'Agent Factory', icon: '🤖' },
    { id: 'swarm_monitor', label: 'Swarm Monitor', icon: '🐝' },
    { id: 'code', label: 'Code', icon: '📝' },
    { id: 'metrics', label: 'Metrics', icon: '📊' }
  ];

  return (
    <div className="flex h-screen bg-slate-950">
      {/* Left Sidebar */}
      <div className="w-64 bg-slate-900 border-r border-cyan-500/20 p-4">
        <h1 className="text-2xl font-bold text-cyan-400 mb-8">SOPHIA SUPREME</h1>
        <nav className="space-y-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab === tab.id
                  ? 'bg-cyan-500/20 text-cyan-400 border-l-4 border-cyan-400'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="text-xl">{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {activeTab === 'chat' && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-3xl rounded-2xl p-4 ${
                    msg.role === 'user' 
                      ? 'bg-cyan-600/20 text-cyan-100' 
                      : 'bg-purple-600/20 text-purple-100'
                  }`}>
                    <div className="mb-2">{msg.content}</div>
                    {msg.sections && <ChatRenderer sections={msg.sections} />}
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="border-t border-white/10 p-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask Sophia anything..."
                  className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
                />
                <button
                  onClick={sendMessage}
                  disabled={loading}
                  className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 rounded-xl text-white font-medium transition-colors"
                >
                  {loading ? '...' : 'Send'}
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'api_health' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">API Health Status</h2>
            {healthData?.actions?.map((action: any, i: number) => (
              <div key={i} className={`p-4 mb-3 rounded-xl border ${
                action.status === 'healthy' ? 'bg-green-900/20 border-green-500/30' :
                action.status === 'unhealthy' ? 'bg-yellow-900/20 border-yellow-500/30' :
                'bg-red-900/20 border-red-500/30'
              }`}>
                <div className="flex justify-between">
                  <span className="text-white">{action.id}</span>
                  <span className={`font-medium ${
                    action.status === 'healthy' ? 'text-green-400' :
                    action.status === 'unhealthy' ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>{action.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'agent_factory' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Agent Factory</h2>
            <div className="bg-white/5 rounded-xl p-6 border border-white/10">
              <textarea
                placeholder="Describe the task for your agents..."
                className="w-full h-32 bg-white/5 border border-white/10 rounded-xl p-4 text-white resize-none"
              />
              <button className="mt-4 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-xl text-white font-medium">
                Deploy Swarm
              </button>
            </div>
          </div>
        )}

        {activeTab === 'swarm_monitor' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Swarm Monitor</h2>
            <div className="space-y-3">
              {swarmData.map((swarm: any, i: number) => (
                <div key={i} className="bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex justify-between mb-2">
                    <span className="text-cyan-400 font-medium">{swarm.swarm_id}</span>
                    <span className="text-gray-400">{swarm.type}</span>
                  </div>
                  {swarm.data && (
                    <div className="text-sm text-gray-300">
                      {JSON.stringify(swarm.data)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Code Viewer</h2>
            <div className="bg-gray-900 rounded-xl p-6 font-mono text-sm text-gray-300">
              <div>No active code changes</div>
            </div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">System Metrics</h2>
            <div className="grid grid-cols-3 gap-6">
              <MetricCard label="Chat Latency p95" value="1.8s" trend="down" />
              <MetricCard label="Error Rate" value="0.2%" trend="stable" />
              <MetricCard label="Active Swarms" value="4" trend="up" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ChatRenderer({ sections }: { sections: ChatSections }) {
  return (
    <div className="space-y-3 mt-3">
      {sections.actions && sections.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sections.actions.map((action, i) => (
            <span key={i} className="px-3 py-1 bg-cyan-600/30 rounded-full text-xs text-cyan-300">
              {action.type} {action.status && `(${action.status})`}
            </span>
          ))}
        </div>
      )}
      
      {sections.research && sections.research.length > 0 && (
        <div className="space-y-2">
          {sections.research.map((item, i) => (
            <div key={i} className="bg-white/5 rounded-lg p-3">
              <a href={item.url} className="text-cyan-400 hover:underline">{item.title}</a>
              <div className="text-xs text-gray-400 mt-1">{item.source}</div>
            </div>
          ))}
        </div>
      )}

      {sections.github && (
        <div className="bg-green-600/20 rounded-lg p-3">
          {sections.github.pr_url && (
            <a href={sections.github.pr_url} className="text-green-400 hover:underline">
              View Pull Request →
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, trend }: { label: string; value: string; trend: 'up' | 'down' | 'stable' }) {
  return (
    <div className="bg-white/5 rounded-xl p-6 border border-white/10">
      <div className="text-gray-400 text-sm mb-2">{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
      <div className={`text-sm mt-2 ${
        trend === 'up' ? 'text-green-400' :
        trend === 'down' ? 'text-red-400' :
        'text-gray-400'
      }`}>
        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
      </div>
    </div>
  );
}