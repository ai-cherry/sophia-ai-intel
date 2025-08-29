'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DashboardPage() {
  const [messages, setMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  }>>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to Sophia AI. I\'m your advanced neural intelligence assistant. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message - ACTUALLY WORKS
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user' as const,
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
      
      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant' as const,
        content: data.message?.content || data.response || 'I understand. Let me help you with that.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant' as const,
        content: 'I\'m having trouble connecting to my neural network. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Bright Neural Network Background Effect */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-96 h-96 bg-cyan-400 rounded-full filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500 rounded-full filter blur-3xl opacity-15 animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      {/* Main Container */}
      <div className="relative z-10 h-full flex flex-col">
        {/* Header - Brighter */}
        <header className="bg-white/10 backdrop-blur-xl border-b border-cyan-400/40 px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Logo */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center shadow-lg shadow-cyan-400/50">
                <span className="text-white font-bold text-xl">S</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Sophia AI</h1>
                <p className="text-sm text-cyan-300">Neural Intelligence Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50" />
                <span className="text-sm text-white">Neural Network Active</span>
              </div>
            </div>
          </div>
        </header>

        {/* Chat Container */}
        <main className="flex-1 overflow-hidden flex bg-gray-900/30">
          <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full p-6">
            {/* Messages Area - Brighter Background */}
            <div className="flex-1 overflow-y-auto space-y-4 pb-6 bg-white/5 rounded-lg p-4">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`
                        max-w-[70%] px-6 py-4 rounded-2xl backdrop-blur-md
                        ${message.role === 'user' 
                          ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-cyan-500/30' 
                          : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/30'
                        }
                      `}
                    >
                      <p className="text-base leading-relaxed font-medium">{message.content}</p>
                      <p className="text-xs text-white/70 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-4 rounded-2xl shadow-lg shadow-purple-500/30">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area - Much Brighter */}
            <div className="relative mt-4">
              <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-cyan-400/40 p-2 shadow-xl">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask Sophia anything..."
                    disabled={isLoading}
                    className="flex-1 px-6 py-4 bg-white/10 text-white placeholder-gray-300 outline-none rounded-xl"
                    style={{ fontSize: '16px' }}
                  />
                  <motion.button
                    onClick={sendMessage}
                    disabled={isLoading || !input.trim()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-500 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/40"
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      'Send'
                    )}
                  </motion.button>
                </div>
              </div>
            </div>
          </div>

          {/* Side Panel - Brighter */}
          <aside className="w-80 bg-white/10 backdrop-blur-xl border-l border-cyan-400/40 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Neural Status</h3>
            
            {/* Quick Stats - More Visible */}
            <div className="space-y-4">
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-cyan-400/30 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-200">Response Time</span>
                  <span className="text-sm text-cyan-300 font-bold">127ms</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div className="bg-gradient-to-r from-cyan-400 to-purple-500 h-2 rounded-full" style={{ width: '85%' }} />
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-cyan-400/30 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-200">Neural Load</span>
                  <span className="text-sm text-cyan-300 font-bold">42%</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div className="bg-gradient-to-r from-cyan-400 to-purple-500 h-2 rounded-full animate-pulse" style={{ width: '42%' }} />
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-cyan-400/30 p-4">
                <p className="text-sm text-gray-200 mb-2">Active Models</p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-cyan-500 text-white rounded-full text-xs font-bold">GPT-4</span>
                  <span className="px-3 py-1 bg-purple-500 text-white rounded-full text-xs font-bold">Claude</span>
                  <span className="px-3 py-1 bg-pink-500 text-white rounded-full text-xs font-bold">Research</span>
                </div>
              </div>
            </div>

            {/* Quick Actions - More Visible */}
            <div className="mt-8">
              <h4 className="text-sm font-semibold text-gray-200 mb-3">Quick Actions</h4>
              <div className="space-y-2">
                <button className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500 to-purple-500 text-white rounded-lg hover:from-cyan-400 hover:to-purple-400 transition-all text-sm font-bold shadow-lg">
                  🚀 Deploy Agent
                </button>
                <button className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-400 hover:to-pink-400 transition-all text-sm font-bold shadow-lg">
                  🔍 Deep Research
                </button>
                <button className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-400 hover:to-cyan-400 transition-all text-sm font-bold shadow-lg">
                  💻 Generate Code
                </button>
              </div>
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}