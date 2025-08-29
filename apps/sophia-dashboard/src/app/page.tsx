'use client';

import { useState, useEffect, useRef } from 'react';
import SwarmManager from '@/components/SwarmManager';
import ActivityFeed from '@/components/ActivityFeed';
import ViewModeSwitcher from '@/components/ViewModeSwitcher';
import QuickActions from '@/components/QuickActions';
import MessageRenderer from '@/components/MessageRenderer';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

interface Agent {
  id: string;
  type: string;
  status: string;
  icon: string;
  description: string;
}

interface MetricCard {
  title: string;
  value: string | number;
  status: 'good' | 'warning' | 'error';
  change?: string;
}

export default function SophiaApp() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'VERSION 3.0 NEURAL - Welcome! I\'m Sophia AI, your intelligent neural companion. I can help with research, agent orchestration, code generation, and deep analysis. What would you like to explore today?',
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState('chat');
  const [showActivityFeed, setShowActivityFeed] = useState(true);
  const [selectedDashboard, setSelectedDashboard] = useState('neural');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [deployedAgents, setDeployedAgents] = useState<any[]>([]);
  const [agentStatus, setAgentStatus] = useState<Record<string, any>>({});
  const [researchQuery, setResearchQuery] = useState('');
  const [codePrompt, setCodePrompt] = useState('');
  const [projectName, setProjectName] = useState('AI Research Platform');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (activeView === 'agents') {
      loadAgents();
    }
  }, [activeView]);

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents');
      if (response.ok) {
        const data = await response.json();
        setAgents(data.availableAgents || []);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input;
    if (!text || !text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageText) setInput(''); // Only clear input if not passed as parameter
    setIsLoading(true);
    setConnectionStatus('processing');
    
    // Check for agent-related commands
    const lowerInput = text.toLowerCase();
    if (lowerInput.includes('agent status') || lowerInput.includes('show agents') || lowerInput.includes('list agents')) {
      const statusMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: deployedAgents.length > 0 
          ? `📊 **Active Agents:**\n\n${deployedAgents.map(a => 
              `🤖 **${a.type}**\n   ID: ${a.id}\n   Status: ${a.status}\n   Task: ${a.task}\n   Deployed: ${new Date(a.timestamp).toLocaleTimeString()}`
            ).join('\n\n')}\n\n💡 Tip: You can give them new tasks or ask about specific agent IDs.`
          : '📭 No agents currently deployed.\n\nTo deploy an agent:\n1. Switch to the **Agents** tab\n2. Choose an agent type\n3. Click **Deploy Agent**\n\nOr go to **Agent Factory** in the sidebar for advanced swarm management.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, statusMessage]);
      setIsLoading(false);
      setConnectionStatus('connected');
      return;
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          context: messages.slice(-5),
          activeAgents: deployedAgents,
          activeTab: activeView
        })
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          metadata: data
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('API request failed');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I\'m having trouble connecting to my neural networks. Let me try to reconnect...',
        timestamp: new Date()
      }]);
      setConnectionStatus('disconnected');
      setTimeout(() => setConnectionStatus('connected'), 3000);
    } finally {
      setIsLoading(false);
      setConnectionStatus('connected');
    }
  };

  const deployAgent = async (agentType: string) => {
    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'deploy',
          agentType,
          task: `Deploy ${agentType} for autonomous operations`
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Add to deployed agents list
        const newAgent = {
          id: data.swarmId || data.agentId,
          type: agentType,
          status: 'active',
          task: data.task,
          timestamp: new Date().toISOString()
        };
        setDeployedAgents(prev => [...prev, newAgent]);
        
        // Add a system message in chat
        const systemMessage: Message = {
          id: `msg-${Date.now()}`,
          role: 'system',
          content: `🤖 ${agentType} deployed!\n\nSwarm ID: ${data.swarmId || data.agentId}\nStatus: Active\n\nYou can now:\n• Give it tasks by typing in chat\n• Ask "What is my agent doing?"\n• Navigate to Agent Factory tab for monitoring`,
          timestamp: new Date(),
          metadata: { agentId: data.swarmId || data.agentId }
        };
        setMessages(prev => [...prev, systemMessage]);
        
        // Switch to chat to show the deployment
        setActiveView('chat');
        
        loadAgents();
      }
    } catch (error) {
      alert('Failed to deploy agent');
    }
  };

  const apiMetrics: MetricCard[] = [
    { title: 'Response Time', value: '127ms', status: 'good', change: '-12%' },
    { title: 'Success Rate', value: '99.8%', status: 'good', change: '+0.3%' },
    { title: 'Active Connections', value: '1,247', status: 'warning', change: '+18%' },
    { title: 'Error Rate', value: '0.2%', status: 'good', change: '-0.1%' }
  ];

  const quickActions = [
    { icon: '🔬', text: 'Research AI Papers', command: 'Search for the latest AI research papers' },
    { icon: '🤖', text: 'Deploy Agent', command: 'Create a new AI agent for data analysis' },
    { icon: '⚡', text: 'Generate Code', command: 'Generate a Python function to process data' },
    { icon: '🌐', text: 'Swarm Intelligence', command: 'Deploy an agent swarm for web scraping' }
  ];

  return (
    <div className="flex h-screen">
      {/* Left Sidebar Navigation */}
      <div className={`${sidebarCollapsed ? 'w-20' : 'w-72'} transition-all duration-300 bg-gradient-to-b from-[#0f1b3c] via-[#1e293b] to-[#4c1d95]/70 backdrop-blur-xl border-r border-cyan-500/10 flex flex-col`}>
        {/* Sidebar Header */}
        <div className="p-6 border-b border-cyan-500/20">
          <div className="flex items-center gap-4">
            <div className="logo-container">
              <img 
                src="/sophia-logo.jpg" 
                alt="Sophia AI" 
                className="w-10 h-10 rounded-xl object-cover shadow-2xl cursor-pointer"
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              />
            </div>
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-white font-bold text-lg">Sophia AI</h1>
                <p className="text-xs text-cyan-400/80">Platform Control</p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          {/* Platform Section */}
          {!sidebarCollapsed && <div className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase">Platform</div>}
          
          <button
            onClick={() => setSelectedDashboard('neural')}
            className={`w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg transition-all ${
              selectedDashboard === 'neural' 
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                : 'text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1'
            }`}
          >
            <span className="text-xl w-6 text-center">🏠</span>
            {!sidebarCollapsed && <span>Neural Interface</span>}
          </button>

          <button
            onClick={() => setSelectedDashboard('api-health')}
            className={`w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg transition-all ${
              selectedDashboard === 'api-health' 
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                : 'text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1'
            }`}
          >
            <span className="text-xl w-6 text-center">📊</span>
            {!sidebarCollapsed && <span>API Health</span>}
          </button>

          <button
            onClick={() => setSelectedDashboard('agent-factory')}
            className={`w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg transition-all ${
              selectedDashboard === 'agent-factory' 
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                : 'text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1'
            }`}
          >
            <span className="text-xl w-6 text-center">🏭</span>
            {!sidebarCollapsed && <span>Agent Factory</span>}
          </button>

          <button
            onClick={() => setSelectedDashboard('project-mgmt')}
            className={`w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg transition-all ${
              selectedDashboard === 'project-mgmt' 
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                : 'text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1'
            }`}
          >
            <span className="text-xl w-6 text-center">📋</span>
            {!sidebarCollapsed && <span>Project Management</span>}
          </button>

          {/* System Section */}
          {!sidebarCollapsed && <div className="px-4 mt-6 mb-2 text-xs font-semibold text-gray-400 uppercase">System</div>}
          
          <button className="w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1 transition-all">
            <span className="text-xl w-6 text-center">⚙️</span>
            {!sidebarCollapsed && <span>Settings</span>}
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1 transition-all">
            <span className="text-xl w-6 text-center">📈</span>
            {!sidebarCollapsed && <span>Analytics</span>}
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 mx-2 mb-1 rounded-lg text-gray-300 hover:bg-white/5 hover:text-cyan-400 hover:translate-x-1 transition-all">
            <span className="text-xl w-6 text-center">🔒</span>
            {!sidebarCollapsed && <span>Security</span>}
          </button>
        </nav>

        {/* Sidebar Footer */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-cyan-500/20">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Connection</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className={connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400'}>
                  {connectionStatus === 'connected' ? 'Active' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Neural Interface Dashboard */}
        {selectedDashboard === 'neural' && (
          <>
            {/* Top Navigation for Neural Interface */}
            <header className="compact-header p-4 border-b border-cyan-500/20">
              <div className="flex items-center justify-between">
                <ViewModeSwitcher currentView={activeView} onViewChange={setActiveView} />
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowActivityFeed(!showActivityFeed)}
                    className="px-3 py-2 bg-gray-800/50 hover:bg-gray-800 text-gray-400 hover:text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    <span className="text-sm">Activity Feed</span>
                    <span className="text-xs px-1.5 py-0.5 bg-cyan-600/30 text-cyan-400 rounded">
                      {showActivityFeed ? 'Hide' : 'Show'}
                    </span>
                  </button>
                </div>
              </div>
            </header>

            <main className="flex-1 relative overflow-hidden flex">
              {/* Main Content Area */}
              <div className="flex-1 flex flex-col">
                {/* Quick Actions Bar */}
                <div className="p-4 border-b border-cyan-500/20">
                  <QuickActions 
                    onAction={(command) => {
                      setInput(command);
                      sendMessage();
                    }}
                    isLoading={isLoading}
                  />
                </div>

                {/* Chat View */}
                {activeView === 'chat' && (
                <>
                  {/* Active Agents Bar */}
                  {deployedAgents.length > 0 && (
                    <div className="absolute top-0 left-0 right-0 z-10 p-3">
                      <div className="glass-card p-2 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-sm text-gray-300">
                            {deployedAgents.length} agent{deployedAgents.length !== 1 ? 's' : ''} active
                          </span>
                          <div className="flex gap-2">
                            {deployedAgents.map(agent => (
                              <span key={agent.id} className="text-xs px-2 py-1 bg-gray-800 rounded text-cyan-400">
                                {agent.type.replace(' Agent', '')} • {agent.id.slice(0, 8)}
                              </span>
                            ))}
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            const statusMsg = `Active agents:\n${deployedAgents.map(a => `• ${a.type}: ${a.task}`).join('\n')}`;
                            setInput('show agent status');
                            sendMessage();
                          }}
                          className="text-xs px-3 py-1 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-600/50 rounded transition-all"
                        >
                          View Status
                        </button>
                      </div>
                    </div>
                  )}
                  <div className="chat-container" style={{ paddingTop: deployedAgents.length > 0 ? '60px' : '0' }}>
                    {messages.map((msg) => (
                      <div key={msg.id} className={`mb-4 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                        <div className={`inline-block max-w-[70%] px-4 py-3 ${
                          msg.role === 'user' 
                            ? 'user-message' 
                            : msg.role === 'system'
                            ? 'system-message'
                            : 'ai-message'
                        }`}>
                          <div className="message-time">
                            {msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                          <MessageRenderer content={msg.content} role={msg.role} />
                        </div>
                      </div>
                    ))}
                    
                    {isLoading && (
                      <div className="mb-4">
                        <div className="inline-block ai-message px-4 py-3">
                          <div className="text-cyan-400 text-sm">Sophia is thinking...</div>
                          <div className="loading-dots">
                            <div className="loading-dot"></div>
                            <div className="loading-dot"></div>
                            <div className="loading-dot"></div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </div>

                  {messages.length <= 2 && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                      <div className="grid grid-cols-2 gap-4 max-w-md">
                        {quickActions.map((action, idx) => (
                          <button
                            key={idx}
                            onClick={() => setInput(action.command)}
                            className="quick-action flex items-center gap-3 px-4 py-3 rounded-xl text-left"
                          >
                            <span className="text-2xl">{action.icon}</span>
                            <span className="text-sm text-white/80">{action.text}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Swarm View - Visual Agent Network */}
              {activeView === 'swarm' && (
                <div className="p-8 h-full">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-white mb-2">Agent Swarm Visualization</h2>
                    <p className="text-gray-400">Real-time view of active agent networks and their interactions</p>
                  </div>
                  <div className="glass-card p-6 h-[500px] flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-6xl mb-4 animate-pulse">🐝</div>
                      <p className="text-white text-lg mb-2">Swarm Network View</p>
                      <p className="text-gray-400 text-sm mb-4">Deploy agents to see live network visualization</p>
                      {deployedAgents.length > 0 && (
                        <div className="mt-6">
                          <p className="text-cyan-400 mb-3">Active Swarms: {deployedAgents.length}</p>
                          <div className="flex justify-center gap-4">
                            {deployedAgents.map(agent => (
                              <div key={agent.id} className="p-3 bg-gray-800 rounded-lg">
                                <div className="text-2xl mb-1">🤖</div>
                                <div className="text-xs text-white">{agent.type}</div>
                                <div className="text-xs text-gray-400">{agent.status}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Code View - Live Code Generation */}
              {activeView === 'code' && (
                <div className="p-8 h-full">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-white mb-2">Code Generation Studio</h2>
                    <p className="text-gray-400">Generate, review, and optimize code with AI assistance</p>
                  </div>
                  <div className="glass-card p-6">
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">Code Request</label>
                      <textarea
                        value={codePrompt}
                        onChange={(e) => setCodePrompt(e.target.value)}
                        placeholder="Describe what code you need..."
                        className="w-full h-32 p-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-cyan-500 focus:outline-none"
                      />
                    </div>
                    <button
                      onClick={() => {
                        if (codePrompt) {
                          setInput(`Generate code: ${codePrompt}`);
                          sendMessage();
                          setActiveView('chat');
                        }
                      }}
                      className="neural-button"
                      disabled={!codePrompt || isLoading}
                    >
                      Generate Code
                    </button>
                  </div>
                </div>
              )}

              {/* Research View - Knowledge Exploration */}
              {activeView === 'research' && (
                <div className="p-8 h-full">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-white mb-2">Research Center</h2>
                    <p className="text-gray-400">Deep dive into topics with comprehensive research and citations</p>
                  </div>
                  <div className="glass-card p-6">
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">Research Query</label>
                      <input
                        type="text"
                        value={researchQuery}
                        onChange={(e) => setResearchQuery(e.target.value)}
                        placeholder="What would you like to research?"
                        className="w-full p-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-cyan-500 focus:outline-none"
                      />
                    </div>
                    <button
                      onClick={() => {
                        if (researchQuery) {
                          setInput(`Research: ${researchQuery}`);
                          sendMessage();
                          setActiveView('chat');
                        }
                      }}
                      className="neural-button"
                      disabled={!researchQuery || isLoading}
                    >
                      Start Research
                    </button>
                  </div>
                </div>
              )}

              {/* Metrics View - Performance Analytics */}
              {activeView === 'metrics' && (
                <div className="p-8 h-full overflow-y-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-white mb-2">Performance Metrics</h2>
                    <p className="text-gray-400">Monitor system performance and agent efficiency</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    {apiMetrics.map((metric) => (
                      <div key={metric.title} className="glass-card p-4">
                        <h3 className="text-sm text-gray-400 mb-2">{metric.title}</h3>
                        <div className="text-2xl font-bold text-white mb-1">{metric.value}</div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          metric.status === 'good' ? 'bg-green-500/20 text-green-400' :
                          metric.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {metric.change}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Agent Performance</h3>
                    <div className="space-y-3">
                      {deployedAgents.map(agent => (
                        <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <span className="text-xl">🤖</span>
                            <div>
                              <div className="text-white text-sm">{agent.type}</div>
                              <div className="text-gray-400 text-xs">{agent.id}</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-green-400 text-sm">Active</span>
                            <div className="w-32 bg-gray-700 rounded-full h-2">
                              <div className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Agents View */}
              {activeView === 'agents' && (
                <div className="p-8 max-w-6xl mx-auto">
                  <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white mb-2">AI Agent Deployment Center</h2>
                    <p className="text-gray-400">Deploy specialized AI agents for autonomous tasks</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {[
                      { type: 'Research Agent', icon: '🔍', desc: 'Autonomous web research and data gathering' },
                      { type: 'Code Agent', icon: '💻', desc: 'Automated code generation and debugging' },
                      { type: 'Analysis Agent', icon: '📊', desc: 'Data analysis and insights generation' }
                    ].map((agent) => (
                      <div key={agent.type} className="glass-card p-6">
                        <div className="text-4xl mb-4">{agent.icon}</div>
                        <h3 className="text-lg font-semibold text-white mb-2">{agent.type}</h3>
                        <p className="text-gray-400 text-sm mb-4">{agent.desc}</p>
                        <button
                          onClick={() => deployAgent(agent.type)}
                          className="neural-button w-full"
                          disabled={isLoading}
                        >
                          Deploy Agent
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              </div>

              {/* Activity Feed Sidebar */}
              {showActivityFeed && (
                <div className="w-96 border-l border-cyan-500/20 bg-gray-900/30">
                  <ActivityFeed />
                </div>
              )}
            </main>

            {/* Floating Input (only for chat view) */}
            {activeView === 'chat' && (
              <div className="message-input-container">
                <div className="relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    placeholder="Ask Sophia anything..."
                    className="message-input"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={isLoading || !input.trim()}
                    className="send-button"
                  >
                    ➤
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* API Health Dashboard */}
        {selectedDashboard === 'api-health' && (
          <div className="flex-1 p-8 overflow-y-auto">
            <div className="max-w-7xl mx-auto">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h1 className="text-3xl font-bold text-white">API Health Monitor</h1>
                  <p className="text-gray-400 mt-2">Real-time system performance and health metrics</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/50 rounded-lg">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-400 font-semibold">All Systems Operational</span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {apiMetrics.map((metric) => (
                  <div key={metric.title} className="glass-card p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-gray-400 text-sm">{metric.title}</h3>
                      <span className={`text-xs px-2 py-1 rounded ${
                        metric.status === 'good' ? 'bg-green-500/20 text-green-400' :
                        metric.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {metric.change}
                      </span>
                    </div>
                    <div className="text-3xl font-bold text-white mb-2">{metric.value}</div>
                    <div className="h-16 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded"></div>
                  </div>
                ))}
              </div>

              {/* Service Status */}
              <div className="glass-card p-6 mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">Service Status</h2>
                <div className="space-y-3">
                  {['Neural Chat API', 'Agent Orchestration', 'Research Engine', 'Code Generation'].map((service) => (
                    <div key={service} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                        <span className="text-white">{service}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-400 text-sm">Uptime: 99.9%</span>
                        <span className="text-green-400 text-sm">Healthy</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Agent Factory Dashboard */}
        {selectedDashboard === 'agent-factory' && (
          <div className="flex-1 overflow-hidden">
            <SwarmManager />
          </div>
        )}

        {/* Project Management Dashboard */}
        {selectedDashboard === 'project-mgmt' && (
          <div className="flex-1 p-8 overflow-y-auto">
            <div className="max-w-7xl mx-auto">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h1 className="text-3xl font-bold text-white">Project Command Center</h1>
                  <p className="text-gray-400 mt-2">Manage projects, tasks, and team coordination</p>
                </div>
                <select className="neural-input" value={projectName} onChange={(e) => setProjectName(e.target.value)}>
                  <option>AI Research Platform</option>
                  <option>Neural Interface v2.0</option>
                  <option>Agent Swarm System</option>
                </select>
              </div>

              {/* Project Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="glass-card p-6">
                  <h3 className="text-gray-400 text-sm mb-4">Progress</h3>
                  <div className="text-3xl font-bold text-white mb-4">73%</div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full" style={{ width: '73%' }}></div>
                  </div>
                </div>

                <div className="glass-card p-6">
                  <h3 className="text-gray-400 text-sm mb-4">Active Tasks</h3>
                  <div className="text-3xl font-bold text-white mb-4">12</div>
                  <div className="flex gap-2 text-xs">
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded">4 In Progress</span>
                    <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded">6 Review</span>
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded">2 Testing</span>
                  </div>
                </div>

                <div className="glass-card p-6">
                  <h3 className="text-gray-400 text-sm mb-4">Team Capacity</h3>
                  <div className="text-3xl font-bold text-white mb-4">85%</div>
                  <p className="text-sm text-gray-400">3 agents + 2 humans</p>
                </div>
              </div>

              {/* Task Board */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {['Backlog', 'In Progress', 'Review', 'Done'].map((column) => (
                  <div key={column} className="glass-card p-4">
                    <h3 className="text-white font-semibold mb-4">{column}</h3>
                    <div className="space-y-3">
                      {column === 'In Progress' && (
                        <div className="p-3 bg-gray-800/50 rounded-lg border-l-4 border-yellow-500">
                          <h4 className="text-white text-sm font-medium mb-2">API health monitoring system</h4>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded">Critical</span>
                            <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded">DevOps</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-gray-400">Agent-Code-01</span>
                            <span className="text-xs text-cyan-400">60%</span>
                          </div>
                        </div>
                      )}
                      {column === 'Backlog' && (
                        <>
                          <div className="p-3 bg-gray-800/50 rounded-lg">
                            <h4 className="text-white text-sm font-medium mb-2">Implement neural network optimization</h4>
                            <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-400 rounded">AI/ML</span>
                          </div>
                          <div className="p-3 bg-gray-800/50 rounded-lg">
                            <h4 className="text-white text-sm font-medium mb-2">Design swarm coordination protocol</h4>
                            <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">Architecture</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}