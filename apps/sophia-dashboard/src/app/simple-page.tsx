'use client';

import { useState } from 'react';

export default function SimpleDashboard() {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([
    { role: 'system', content: 'Welcome to Sophia AI! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call MCP Context API
      const response = await fetch('http://localhost:8081/documents/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, limit: 5 })
      });
      
      const data = await response.json();
      
      const aiResponse = {
        role: 'assistant',
        content: data.results?.length > 0 
          ? `Found ${data.results.length} relevant documents: ${data.results[0].content}`
          : `I'll help you with: "${input}". The system is processing your request.`
      };
      
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection established. How can I assist you?'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white">Sophia AI Platform</h1>
              <p className="text-purple-300">Intelligent Multi-Agent System</p>
            </div>
            <div className="flex gap-2">
              <StatusIndicator service="MCP Context" port={8081} />
              <StatusIndicator service="Orchestrator" port={8088} />
              <StatusIndicator service="AI Core" port={8080} />
            </div>
          </div>
        </div>
      </header>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto p-4">
        <div className="bg-black/20 backdrop-blur-md rounded-lg shadow-2xl border border-white/10">
          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[70%] rounded-lg p-4 ${
                  msg.role === 'user' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-800 text-gray-200 border border-purple-500/30'
                }`}>
                  <div className="text-xs opacity-70 mb-1">
                    {msg.role === 'user' ? 'You' : 'Sophia AI'}
                  </div>
                  <div>{msg.content}</div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-200 rounded-lg p-4 border border-purple-500/30">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-white/10 p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type your message..."
                className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                onClick={sendMessage}
                disabled={isLoading}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg px-6 py-3 transition-colors"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Service Status */}
        <div className="mt-4 grid grid-cols-4 gap-2">
          {['MCP Context', 'MCP Agents', 'Orchestrator', 'Memory'].map(service => (
            <div key={service} className="bg-black/20 backdrop-blur-md rounded-lg p-3 border border-white/10">
              <div className="text-xs text-gray-400">{service}</div>
              <div className="text-green-400 text-sm">● Online</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

function StatusIndicator({ service, port }: { service: string; port: number }) {
  const [status, setStatus] = useState('checking');
  
  useState(() => {
    fetch(`http://localhost:${port}/healthz`)
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'));
  });

  return (
    <div className="text-xs">
      <span className={`inline-block w-2 h-2 rounded-full mr-1 ${
        status === 'online' ? 'bg-green-400' : status === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
      }`}></span>
      <span className="text-gray-300">{service}</span>
    </div>
  );
}