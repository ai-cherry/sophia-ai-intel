'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import NavigationRail from '@/components/NavigationRail';
import ResizablePanel from '@/components/ResizablePanel';
import ContextPanel from '@/components/ContextPanel';
import RichMessageCard from '@/components/RichMessageCard';
import CommandPalette from '@/components/CommandPalette';
import QuickActions from '@/components/QuickActions';
import ViewModeSwitcher from '@/components/ViewModeSwitcher';
import SwarmManager from '@/components/SwarmManager';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'agent' | 'system';
  content: string;
  metadata?: {
    actions?: string[];
    services?: string[];
    research?: any[];
    code?: any[];
    plans?: any;
    agents?: any[];
    github_pr?: any;
  };
  timestamp: Date;
  status?: 'pending' | 'streaming' | 'complete' | 'error';
}

export default function DashboardPage() {
  // State Management
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [activeView, setActiveView] = useState('chat');
  const [contextMode, setContextMode] = useState<'activity' | 'agents' | 'code' | 'research'>('activity');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `# Welcome to Sophia AI Command Center

I'm your intelligent AI orchestrator with full access to:
- 🤖 **Agent Swarms** for parallel task execution
- 💻 **Code Generation** with full-stack capabilities
- 🔍 **Research** using multiple search engines
- 📋 **Strategic Planning** with three perspectives
- 🔌 **GitHub Integration** for code management

Use **Cmd+K** to open the command palette or type your request below.`,
      timestamp: new Date(),
      status: 'complete'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket Connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8096/ws/dashboard');
      
      ws.onopen = () => {
        console.log('Dashboard connected to WebSocket hub');
        ws.send(JSON.stringify({ 
          type: 'subscribe', 
          channels: ['chat', 'agents', 'research', 'code'] 
        }));
        setWsConnection(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...');
        setWsConnection(null);
        setTimeout(connectWebSocket, 3000);
      };

      return ws;
    };

    const ws = connectWebSocket();

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Handle WebSocket Messages
  const handleWebSocketMessage = useCallback((data: any) => {
    if (data.type === 'stream_chunk' && streamingMessageId) {
      setMessages(prev => prev.map(msg => 
        msg.id === streamingMessageId 
          ? { ...msg, content: msg.content + data.chunk }
          : msg
      ));
    }

    if (data.type === 'metadata_update' && data.message_id) {
      setMessages(prev => prev.map(msg => 
        msg.id === data.message_id 
          ? { ...msg, metadata: { ...msg.metadata, ...data.metadata } }
          : msg
      ));
    }

    if (data.type === 'agent_update') {
      // Context panel will handle this
      console.log('Agent update:', data);
    }

    if (data.type === 'research_result' || data.type === 'code_generated') {
      // Update context mode to show new content
      setContextMode(data.type === 'research_result' ? 'research' : 'code');
    }
  }, [streamingMessageId]);

  // Send Message
  const sendMessage = async (messageText?: string) => {
    const text = messageText || input;
    if (!text.trim()) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
      status: 'complete'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Create assistant message for streaming
    const assistantMessageId = `msg-${Date.now() + 1}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'streaming'
    };
    setMessages(prev => [...prev, assistantMessage]);
    setStreamingMessageId(assistantMessageId);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          context: messages.slice(-10),
          sessionId: 'dashboard-session',
          enableWebSocket: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId 
            ? { 
                ...msg, 
                content: data.message.content,
                metadata: data.message.metadata,
                status: 'complete'
              }
            : msg
        ));
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { 
              ...msg, 
              content: 'I encountered an error processing your request. Please try again.',
              status: 'error'
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette(prev => !prev);
      }

      // View switching
      if (e.metaKey || e.ctrlKey) {
        switch(e.key) {
          case '1': setActiveView('chat'); break;
          case '2': setActiveView('agents'); break;
          case '3': setActiveView('code'); break;
          case '4': setActiveView('research'); break;
          case '5': setActiveView('swarm'); break;
        }
      }

      // Focus input
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        document.querySelector<HTMLInputElement>('.chat-input')?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Render different views
  const renderView = () => {
    switch(activeView) {
      case 'chat':
        return (
          <div className="flex flex-col h-full">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <AnimatePresence initial={false}>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  >
                    <RichMessageCard 
                      message={message} 
                      isStreaming={message.status === 'streaming'}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-6 border-t border-white/10">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Ask Sophia anything... (Cmd+K for commands)"
                  className="chat-input flex-1 px-6 py-4 bg-gray-800/50 text-white rounded-xl border border-white/10 focus:border-cyan-500/50 focus:outline-none transition-all"
                  disabled={isLoading}
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={isLoading || !input.trim()}
                  className="px-8 py-4 bg-gradient-to-r from-cyan-600 to-purple-600 text-white rounded-xl font-medium hover:from-cyan-500 hover:to-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'agents':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Agent Management</h2>
            <SwarmManager />
          </div>
        );

      case 'swarm':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Swarm Visualization</h2>
            <div className="glass-card p-8 h-[600px] flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🐝</div>
                <p className="text-white text-lg">Agent Network Visualization</p>
                <p className="text-gray-400 text-sm mt-2">Real-time swarm monitoring coming soon</p>
              </div>
            </div>
          </div>
        );

      case 'code':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Code Generation Studio</h2>
            <div className="glass-card p-6">
              <textarea
                placeholder="Describe the code you need..."
                className="w-full h-40 p-4 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-cyan-500 focus:outline-none"
              />
              <button className="mt-4 neural-button">Generate Code</button>
            </div>
          </div>
        );

      case 'research':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Research Center</h2>
            <div className="glass-card p-6">
              <input
                type="text"
                placeholder="What would you like to research?"
                className="w-full p-4 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-cyan-500 focus:outline-none"
              />
              <button className="mt-4 neural-button">Start Research</button>
            </div>
          </div>
        );

      case 'metrics':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">System Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Active Agents', value: '12', change: '+3' },
                { label: 'Tasks/min', value: '47', change: '+12' },
                { label: 'Success Rate', value: '98.5%', change: '+0.5%' },
                { label: 'Latency', value: '127ms', change: '-23ms' }
              ].map(metric => (
                <div key={metric.label} className="glass-card p-6">
                  <h3 className="text-sm text-gray-400 mb-2">{metric.label}</h3>
                  <div className="text-3xl font-bold text-white mb-1">{metric.value}</div>
                  <span className="text-xs text-green-400">{metric.change}</span>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Navigation Rail */}
      <NavigationRail
        collapsed={navCollapsed}
        onToggle={() => setNavCollapsed(!navCollapsed)}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b border-white/10 bg-gray-900/50 backdrop-blur-lg">
          <div className="flex items-center justify-between">
            <ViewModeSwitcher currentView={activeView} onViewChange={setActiveView} />
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">
                {wsConnection ? '🟢 Connected' : '🔴 Disconnected'}
              </span>
              <button
                onClick={() => setShowCommandPalette(true)}
                className="px-3 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white transition-all text-sm"
              >
                Cmd+K
              </button>
            </div>
          </div>
        </header>

        {/* Quick Actions */}
        {activeView === 'chat' && (
          <div className="p-4 border-b border-white/10">
            <QuickActions onAction={sendMessage} isLoading={isLoading} />
          </div>
        )}

        {/* Main View */}
        <main className="flex-1 overflow-hidden">
          {renderView()}
        </main>
      </div>

      {/* Context Panel */}
      <ResizablePanel defaultWidth={400} minWidth={300} maxWidth={600}>
        <ContextPanel mode={contextMode} />
      </ResizablePanel>

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onCommand={sendMessage}
      />
    </div>
  );
}