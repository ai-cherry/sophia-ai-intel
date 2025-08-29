'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type Tab = 'chat' | 'api_health' | 'agent_factory' | 'swarm_monitor' | 'code' | 'analytics';

interface ChatSections {
  summary?: string;
  actions?: Array<{ type: string; id?: string; status?: string; meta?: any }>;
  research?: Array<{ title: string; url: string; source: string; date?: string }>;
  plans?: {
    cutting_edge?: any;
    conservative?: any;
    synthesis?: any;
    recommendation?: "cutting_edge" | "conservative" | "synthesis";
  };
  code?: { language: string; files: Array<{ path: string; diff: string }> };
  github?: { pr_url?: string; branch?: string };
  events?: Array<{ swarm_id: string; type: string; data?: any }>;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sections?: ChatSections;
  timestamp: string;
}

export default function AGNODashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`agno_${Date.now()}`);
  
  // Real-time data
  const [healthData, setHealthData] = useState<any[]>([]);
  const [swarmActivity, setSwarmActivity] = useState<any[]>([]);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8096/ws/dashboard');
    
    wsRef.current.onopen = () => {
      console.log('AGNO WebSocket connected');
      wsRef.current?.send(JSON.stringify({ type: 'subscribe', session_id: sessionId }));
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'swarm.update' || data.type === 'pipeline.progress') {
        setSwarmActivity(prev => [...prev.slice(-19), data]);
      }
      
      if (data.type === 'health.update') {
        setHealthData(data.services);
      }
      
      if (data.type === 'analytics.update') {
        setAnalyticsData(data);
      }
    };
    
    return () => {
      wsRef.current?.close();
    };
  }, [sessionId]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Health polling
  useEffect(() => {
    if (activeTab === 'api_health') {
      const interval = setInterval(async () => {
        try {
          const res = await fetch('http://localhost:8400/health');
          if (res.ok) {
            const data = await res.json();
            setHealthData(data);
          }
        } catch (error) {
          console.error('Health check failed:', error);
        }
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8400/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          context: { tab: activeTab }
        })
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.sections.summary || 'Processing...',
          sections: data.sections,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Service temporarily unavailable. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, sessionId, activeTab]);

  const deploySwarm = async (swarmType: string, task: string) => {
    try {
      const res = await fetch('http://localhost:8400/swarm/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ swarm_type: swarmType, task })
      });
      
      if (res.ok) {
        const data = await res.json();
        setSwarmActivity(prev => [...prev, {
          type: 'swarm.created',
          swarm_id: data.swarm_id,
          swarm_type: swarmType,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Swarm deployment failed:', error);
    }
  };

  const tabs = [
    { id: 'chat' as Tab, label: 'Chat', icon: '💬' },
    { id: 'api_health' as Tab, label: 'API Health', icon: '🔧' },
    { id: 'agent_factory' as Tab, label: 'Agent Factory', icon: '🤖' },
    { id: 'swarm_monitor' as Tab, label: 'Swarm Monitor', icon: '🐝' },
    { id: 'code' as Tab, label: 'Code', icon: '📝' },
    { id: 'analytics' as Tab, label: 'Analytics', icon: '📊' }
  ];

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-950 via-purple-950/20 to-slate-950">
      {/* Left Sidebar */}
      <motion.div 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 bg-slate-900/50 backdrop-blur-xl border-r border-cyan-500/20 p-4"
      >
        <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-8">
          AGNO SOPHIA
        </h1>
        
        <nav className="space-y-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white border-l-4 border-cyan-400'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="text-xl">{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-8">
          <div className="text-xs text-gray-500">
            <div>Session: {sessionId.slice(0, 12)}...</div>
            <div>Models: Together AI + OpenRouter</div>
            <div>Pipeline: 6-stage AGNO</div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col"
            >
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-3xl rounded-2xl p-4 backdrop-blur-md ${
                      msg.role === 'user' 
                        ? 'bg-gradient-to-br from-cyan-600/20 to-cyan-600/10 text-cyan-100 border border-cyan-500/20' 
                        : 'bg-gradient-to-br from-purple-600/20 to-purple-600/10 text-purple-100 border border-purple-500/20'
                    }`}>
                      <div className="text-xs text-gray-400 mb-2">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                      {msg.sections && <SectionsRenderer sections={msg.sections} />}
                    </div>
                  </motion.div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-white/10 p-4 bg-slate-900/50 backdrop-blur-xl">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask Sophia anything... (try: 'build a feature for user auth')"
                    className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/40"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={loading}
                    className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-purple-600 hover:from-cyan-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 rounded-xl text-white font-medium transition-all transform hover:scale-105"
                  >
                    {loading ? '...' : 'Send'}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'api_health' && (
            <motion.div
              key="health"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6 overflow-y-auto"
            >
              <h2 className="text-2xl font-bold text-white mb-6">API Health Status</h2>
              <div className="grid grid-cols-2 gap-4">
                {healthData.map((service, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className={`p-4 rounded-xl backdrop-blur-md border ${
                      service.status === 'healthy' 
                        ? 'bg-green-900/20 border-green-500/30' 
                        : service.status === 'unhealthy'
                        ? 'bg-yellow-900/20 border-yellow-500/30'
                        : 'bg-red-900/20 border-red-500/30'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">{service.service}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        service.status === 'healthy' 
                          ? 'bg-green-500/20 text-green-400' 
                          : service.status === 'unhealthy'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {service.status}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'agent_factory' && (
            <motion.div
              key="factory"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6"
            >
              <h2 className="text-2xl font-bold text-white mb-6">Agent Factory</h2>
              <div className="grid grid-cols-2 gap-6">
                {['strategy', 'research', 'planning', 'coding', 'qc_ux', 'commit_deploy'].map(swarmType => (
                  <div key={swarmType} className="bg-white/5 backdrop-blur-md rounded-xl p-6 border border-white/10">
                    <h3 className="text-lg font-semibold text-cyan-400 mb-4 capitalize">
                      {swarmType.replace('_', ' ')} Swarm
                    </h3>
                    <textarea
                      placeholder={`Task for ${swarmType} swarm...`}
                      className="w-full h-24 bg-white/5 border border-white/10 rounded-lg p-3 text-white resize-none mb-4"
                      id={`task-${swarmType}`}
                    />
                    <button
                      onClick={() => {
                        const textarea = document.getElementById(`task-${swarmType}`) as HTMLTextAreaElement;
                        if (textarea?.value) {
                          deploySwarm(swarmType, textarea.value);
                          textarea.value = '';
                        }
                      }}
                      className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg text-white font-medium transition-all"
                    >
                      Deploy {swarmType} Swarm
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'swarm_monitor' && (
            <motion.div
              key="monitor"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6"
            >
              <h2 className="text-2xl font-bold text-white mb-6">Swarm Activity Monitor</h2>
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {swarmActivity.map((activity, i) => (
                  <motion.div
                    key={i}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    className="bg-white/5 backdrop-blur-md rounded-xl p-4 border border-white/10"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-cyan-400 font-medium">
                          {activity.swarm_id || activity.pipeline_id || 'Unknown'}
                        </span>
                        <div className="text-sm text-gray-400 mt-1">
                          Type: {activity.type} | Stage: {activity.stage || activity.swarm_type || 'N/A'}
                        </div>
                      </div>
                      <span className="text-xs text-gray-500">
                        {activity.timestamp ? new Date(activity.timestamp).toLocaleTimeString() : 'Live'}
                      </span>
                    </div>
                    {activity.data && (
                      <div className="mt-2 text-xs text-gray-300 font-mono">
                        {JSON.stringify(activity.data, null, 2)}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'code' && (
            <motion.div
              key="code"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6"
            >
              <h2 className="text-2xl font-bold text-white mb-6">Code Viewer</h2>
              <div className="bg-gray-900 rounded-xl p-6 font-mono text-sm">
                <div className="text-gray-400">No active code changes</div>
                <div className="mt-4 text-xs text-gray-500">
                  Code generation outputs will appear here after running coding swarms
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'analytics' && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6"
            >
              <h2 className="text-2xl font-bold text-white mb-6">Analytics & Evals</h2>
              <div className="grid grid-cols-3 gap-6">
                <MetricCard 
                  label="Token Cost (24h)" 
                  value={analyticsData?.token_cost_24h || '$0.00'} 
                  trend={analyticsData?.cost_trend || 'stable'} 
                />
                <MetricCard 
                  label="Model Win Rate" 
                  value={analyticsData?.win_rate || '0%'} 
                  trend={analyticsData?.win_trend || 'up'} 
                />
                <MetricCard 
                  label="Pipeline Success" 
                  value={analyticsData?.pipeline_success || '0%'} 
                  trend={analyticsData?.pipeline_trend || 'stable'} 
                />
                <MetricCard 
                  label="Scout Agreement" 
                  value={analyticsData?.scout_agreement || '0%'} 
                  trend="stable" 
                />
                <MetricCard 
                  label="Judge Confidence" 
                  value={analyticsData?.judge_confidence || '0%'} 
                  trend="up" 
                />
                <MetricCard 
                  label="Active Swarms" 
                  value={swarmActivity.length.toString()} 
                  trend="stable" 
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SectionsRenderer({ sections }: { sections: ChatSections }) {
  return (
    <div className="mt-4 space-y-3">
      {sections.actions && sections.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sections.actions.map((action, i) => (
            <span key={i} className="px-3 py-1 bg-cyan-600/30 backdrop-blur-sm rounded-full text-xs text-cyan-300 border border-cyan-500/30">
              {action.type} {action.status && `(${action.status})`}
            </span>
          ))}
        </div>
      )}
      
      {sections.research && sections.research.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-gray-400 uppercase tracking-wider">Research Results</div>
          {sections.research.map((item, i) => (
            <div key={i} className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-white/10">
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
                {item.title}
              </a>
              <div className="text-xs text-gray-400 mt-1">{item.source} • {item.date}</div>
            </div>
          ))}
        </div>
      )}

      {sections.code && (
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg p-4 border border-white/10">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Generated Code</div>
          <div className="font-mono text-sm text-green-400">
            {sections.code.files.length} file(s) • {sections.code.language}
          </div>
        </div>
      )}

      {sections.github && (
        <div className="bg-green-600/20 backdrop-blur-sm rounded-lg p-3 border border-green-500/30">
          {sections.github.pr_url && (
            <a href={sections.github.pr_url} target="_blank" rel="noopener noreferrer" className="text-green-400 hover:underline">
              View Pull Request →
            </a>
          )}
          {sections.github.branch && (
            <div className="text-xs text-gray-400 mt-1">Branch: {sections.github.branch}</div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, trend }: { label: string; value: string; trend: 'up' | 'down' | 'stable' }) {
  return (
    <motion.div 
      whileHover={{ scale: 1.02 }}
      className="bg-white/5 backdrop-blur-md rounded-xl p-6 border border-white/10"
    >
      <div className="text-gray-400 text-sm mb-2">{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
      <div className={`text-sm mt-2 ${
        trend === 'up' ? 'text-green-400' :
        trend === 'down' ? 'text-red-400' :
        'text-gray-400'
      }`}>
        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
      </div>
    </motion.div>
  );
}