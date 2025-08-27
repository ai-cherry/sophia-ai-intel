'use client';

import { useState, useRef, useEffect } from 'react';

// Mock interfaces and API for now
interface ChatMessage {
  id: string;
  role: 'user' | 'system' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    prompt_enhanced?: boolean;
    processing_time?: number;
  };
}

const chatAPI = {
  sendMessage: async (
    message: string,
    settings: any,
    history: ChatMessage[]
  ): Promise<{ message: ChatMessage; error: any }> => {
    console.log('Sending message:', message, settings, history);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      message: {
        id: Date.now().toString(),
        role: 'assistant',
        content: `This is a mocked response to: "${message}"`,
        timestamp: new Date(),
        metadata: {
          model: 'mock-gpt-5',
          prompt_enhanced: settings.enableEnhancement,
        },
      },
      error: null,
    };
  },
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'system',
      content:
        'Sophia AI Intelligence System initialized. Ready for conversation with enhanced prompting pipeline.',
      timestamp: new Date(),
      metadata: {
        model: 'system',
        prompt_enhanced: false,
      },
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    verbosity: 'standard',
    askMeThreshold: 0.7,
    riskStance: 'balanced',
    enableEnhancement: true,
    model: 'gpt-5',
  });
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(
        currentInput,
        settings,
        messages
      );

      if (response.error) {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'system',
          content: `Error: ${response.error}`,
          timestamp: new Date(),
          metadata: {
            model: 'error',
            prompt_enhanced: false,
          },
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        setMessages((prev) => [...prev, response.message]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${
          error instanceof Error ? error.message : 'Failed to generate response'
        }`,
        timestamp: new Date(),
        metadata: {
          model: 'error',
          prompt_enhanced: false,
        },
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: any) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearMessages = () => {
    setMessages([messages[0]]); // Keep system message
  };

  return (
    <div className="flex flex-col h-[600px] border rounded-lg overflow-hidden">
      {/* Header with controls */}
      <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">AI Chat Interface</h3>
          <small className="text-gray-500">
            Model: {settings.model} • Enhancement:{' '}
            {settings.enableEnhancement ? 'ON' : 'OFF'} • Profile:{' '}
            {settings.verbosity}
          </small>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`px-3 py-1 text-sm font-medium text-white rounded-md ${
              showSettings ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            ⚙️ Settings
          </button>
          <button
            onClick={clearMessages}
            className="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded-md"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 border-b bg-yellow-100 text-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block font-semibold mb-1">Verbosity Level</label>
              <select
                value={settings.verbosity}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, verbosity: e.target.value }))
                }
                className="w-full p-1 border rounded-md"
              >
                <option value="minimal">Minimal</option>
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold mb-1">
                Ask-Me Threshold: {settings.askMeThreshold}
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={settings.askMeThreshold}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    askMeThreshold: parseFloat(e.target.value),
                  }))
                }
                className="w-full"
              />
              <small className="text-gray-500">
                Higher = more clarification requests
              </small>
            </div>
            <div>
              <label className="block font-semibold mb-1">Risk Stance</label>
              <select
                value={settings.riskStance}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, riskStance: e.target.value }))
                }
                className="w-full p-1 border rounded-md"
              >
                <option value="conservative">Conservative</option>
                <option value="balanced">Balanced</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex gap-8 items-center">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableEnhancement}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    enableEnhancement: e.target.checked,
                  }))
                }
              />
              Enable Prompt Enhancement Pipeline
            </label>
            <div>
              <label className="mr-2 font-semibold">Model:</label>
              <select
                value={settings.model}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, model: e.target.value }))
                }
                className="p-1 border rounded-md"
              >
                <option value="gpt-5">GPT-5 (Primary)</option>
                <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="deepseek-coder">DeepSeek Coder</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto bg-white">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.role === 'system'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <div className="mb-1">{message.content}</div>
              <div
                className={`text-xs opacity-80 mt-2 ${
                  message.role !== 'user' ? 'border-t border-black/10 pt-1' : ''
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
                {message.metadata && (
                  <>
                    {message.metadata.model && ` • ${message.metadata.model}`}
                    {message.metadata.prompt_enhanced && ` • Enhanced`}
                    {message.metadata.processing_time &&
                      ` • ${message.metadata.processing_time}ms`}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            Generating response...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            className="flex-1 p-2 border rounded-md resize-none min-h-[44px] max-h-[120px] text-sm"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2 text-sm font-semibold text-white bg-blue-600 rounded-md disabled:bg-gray-300"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500 flex justify-between">
          <span>
            Enhancement: {settings.enableEnhancement ? 'ON' : 'OFF'} • Risk:{' '}
            {settings.riskStance} • Verbosity: {settings.verbosity}
          </span>
          <span>{inputValue.length}/2000</span>
        </div>
      </div>
    </div>
  );
}