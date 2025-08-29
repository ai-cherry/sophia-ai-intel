'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Professional color palette
const colors = {
  primary: '#00d4ff',
  secondary: '#7c3aed',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  background: {
    primary: '#0a0a0a',
    secondary: '#141414',
    tertiary: '#1f1f1f',
    card: 'rgba(20, 20, 20, 0.8)'
  },
  text: {
    primary: '#ffffff',
    secondary: '#a3a3a3',
    muted: '#737373'
  }
};

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

export default function ProfessionalDashboard() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '👋 Welcome to Sophia AI Command Center\n\nI\'m your intelligent orchestrator with access to:\n• 🤖 Agent Swarms\n• 💻 Code Generation\n• 🔍 Deep Research\n• 📊 Real-time Analytics',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection with proper error handling
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8096/ws/dashboard');
        
        ws.onopen = () => {
          console.log('✅ WebSocket connected');
          setWsConnected(true);
          ws.send(JSON.stringify({ type: 'subscribe', channels: ['all'] }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          // Reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setWsConnected(false);
        setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: data.message?.content || data.response || 'I\'m processing your request...',
        timestamp: new Date(),
        metadata: data.message?.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: `msg-${Date.now() + 1}`,
        role: 'system',
        content: '⚠️ Connection error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Navigation items
  const navItems = [
    { id: 'chat', icon: '💬', label: 'Chat', shortcut: '⌘1' },
    { id: 'agents', icon: '🤖', label: 'Agents', shortcut: '⌘2' },
    { id: 'code', icon: '💻', label: 'Code', shortcut: '⌘3' },
    { id: 'research', icon: '🔍', label: 'Research', shortcut: '⌘4' },
    { id: 'metrics', icon: '📊', label: 'Metrics', shortcut: '⌘5' }
  ];

  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-950 via-gray-900 to-black">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-pink-500/5 animate-pulse" />
      </div>

      {/* Sidebar */}
      <motion.div
        initial={{ x: 0 }}
        animate={{ width: sidebarOpen ? 280 : 80 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="relative bg-black/40 backdrop-blur-xl border-r border-white/10 flex flex-col z-20"
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <motion.button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center gap-4 group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="relative w-12 h-12 rounded-2xl overflow-hidden flex-shrink-0">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 via-blue-500 to-purple-600 animate-gradient" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-white font-bold text-xl">S</span>
              </div>
            </div>
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex-1 text-left"
              >
                <h1 className="text-white font-bold text-lg">Sophia AI</h1>
                <p className="text-xs text-cyan-400">Neural Command Center</p>
              </motion.div>
            )}
          </motion.button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <motion.button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`
                w-full flex items-center gap-4 px-4 py-3 rounded-xl
                transition-all duration-200 group relative
                ${activeView === item.id 
                  ? 'bg-gradient-to-r from-cyan-600/30 to-purple-600/30 text-white border border-cyan-500/30' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }
              `}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="text-2xl flex-shrink-0">{item.icon}</span>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  className="flex-1 flex items-center justify-between"
                >
                  <span className="font-medium">{item.label}</span>
                  <span className="text-xs text-gray-500">{item.shortcut}</span>
                </motion.div>
              )}
              {activeView === item.id && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 w-1 h-8 bg-gradient-to-b from-cyan-400 to-purple-600 rounded-r"
                />
              )}
            </motion.button>
          ))}
        </nav>

        {/* Status */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            {sidebarOpen && (
              <span className="text-xs text-gray-400">
                {wsConnected ? 'Connected' : 'Connecting...'}
              </span>
            )}
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 px-6 flex items-center justify-between border-b border-white/10 bg-black/20 backdrop-blur-xl">
          <h2 className="text-xl font-semibold text-white capitalize">{activeView}</h2>
          <div className="flex items-center gap-4">
            <button className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all text-sm">
              ⌘K
            </button>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-hidden">
          {activeView === 'chat' && (
            <div className="h-full flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`
                        max-w-3xl mx-auto
                        ${message.role === 'user' ? 'ml-auto' : 'mr-auto'}
                      `}
                    >
                      <div
                        className={`
                          p-4 rounded-2xl backdrop-blur-sm
                          ${message.role === 'user' 
                            ? 'bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border border-cyan-500/30 ml-12' 
                            : message.role === 'assistant'
                            ? 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/30 mr-12'
                            : 'bg-yellow-500/10 border border-yellow-500/30 text-center'
                          }
                        `}
                      >
                        <div className="flex items-start gap-3">
                          {message.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                              <span className="text-white text-sm">S</span>
                            </div>
                          )}
                          <div className="flex-1">
                            <p className="text-white whitespace-pre-wrap">{message.content}</p>
                            <p className="text-xs text-gray-500 mt-2">
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-6 border-t border-white/10 bg-black/20 backdrop-blur-xl">
                <div className="max-w-3xl mx-auto flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask Sophia anything..."
                    disabled={isLoading}
                    className="flex-1 px-6 py-4 bg-white/5 text-white rounded-2xl border border-white/10 focus:border-cyan-500/50 focus:outline-none transition-all placeholder-gray-500"
                  />
                  <motion.button
                    onClick={sendMessage}
                    disabled={isLoading || !input.trim()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-8 py-4 bg-gradient-to-r from-cyan-600 to-purple-600 text-white rounded-2xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isLoading ? '...' : 'Send'}
                  </motion.button>
                </div>
              </div>
            </div>
          )}

          {activeView === 'agents' && (
            <div className="p-6">
              <div className="max-w-6xl mx-auto">
                <h3 className="text-2xl font-bold text-white mb-6">Agent Swarm Control</h3>
                <div className="grid grid-cols-3 gap-6">
                  {['Research Agent', 'Code Agent', 'Analysis Agent'].map((agent) => (
                    <motion.div
                      key={agent}
                      whileHover={{ scale: 1.02, y: -4 }}
                      className="p-6 bg-gradient-to-br from-gray-900/80 to-gray-800/80 backdrop-blur-xl rounded-2xl border border-white/10"
                    >
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center mb-4">
                        <span className="text-2xl">🤖</span>
                      </div>
                      <h4 className="text-lg font-semibold text-white mb-2">{agent}</h4>
                      <p className="text-sm text-gray-400 mb-4">Specialized autonomous agent</p>
                      <button className="w-full py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all">
                        Deploy
                      </button>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeView === 'metrics' && (
            <div className="p-6">
              <div className="max-w-6xl mx-auto">
                <h3 className="text-2xl font-bold text-white mb-6">System Metrics</h3>
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: 'Active Agents', value: '12', trend: '+3' },
                    { label: 'Tasks/min', value: '47', trend: '+12' },
                    { label: 'Success Rate', value: '98.5%', trend: '+0.5%' },
                    { label: 'Latency', value: '127ms', trend: '-23ms' }
                  ].map((metric) => (
                    <motion.div
                      key={metric.label}
                      whileHover={{ scale: 1.05 }}
                      className="p-6 bg-gradient-to-br from-gray-900/80 to-gray-800/80 backdrop-blur-xl rounded-2xl border border-white/10"
                    >
                      <p className="text-sm text-gray-400 mb-2">{metric.label}</p>
                      <p className="text-3xl font-bold text-white mb-1">{metric.value}</p>
                      <p className="text-xs text-green-400">{metric.trend}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Context Panel */}
      <motion.div
        initial={{ x: 400 }}
        animate={{ x: 0 }}
        className="w-96 bg-black/40 backdrop-blur-xl border-l border-white/10 p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Activity Feed</h3>
        <div className="space-y-3">
          {['Agent deployed', 'Research completed', 'Code generated'].map((activity, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="p-3 bg-white/5 rounded-lg border border-white/10"
            >
              <p className="text-sm text-white">{activity}</p>
              <p className="text-xs text-gray-500 mt-1">Just now</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}