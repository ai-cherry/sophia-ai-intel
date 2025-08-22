import { useState, useRef, useEffect } from 'react'
import { chatAPI, ChatMessage, ChatSettings, ChatResponse } from '../lib/chatApi'

const defaultSettings: ChatSettings = {
  verbosity: 'standard',
  askMeThreshold: 0.7,
  riskStance: 'balanced',
  enableEnhancement: true,
  model: 'gpt-5'
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'system',
      content: 'Sophia AI Intelligence System initialized. Ready for conversation with enhanced prompting pipeline.',
      timestamp: new Date(),
      metadata: {
        model: 'system',
        prompt_enhanced: false
      }
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [settings, setSettings] = useState<ChatSettings>(defaultSettings)
  const [showSettings, setShowSettings] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = inputValue
    setInputValue('')
    setIsLoading(true)

    try {
      const response: ChatResponse = await chatAPI.sendMessage(
        currentInput,
        settings,
        messages
      )

      if (response.error) {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'system',
          content: `Error: ${response.error}`,
          timestamp: new Date(),
          metadata: {
            model: 'error',
            prompt_enhanced: false
          }
        }
        setMessages(prev => [...prev, errorMessage])
      } else {
        setMessages(prev => [...prev, response.message])
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to generate response'}`,
        timestamp: new Date(),
        metadata: {
          model: 'error',
          prompt_enhanced: false
        }
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: any) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearMessages = () => {
    setMessages([messages[0]]) // Keep system message
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '600px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header with controls */}
      <div style={{ 
        padding: '1rem', 
        borderBottom: '1px solid #eee',
        background: '#f8f9fa',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>AI Chat Interface</h3>
          <small style={{ color: '#666' }}>
            Model: {settings.model} • Enhancement: {settings.enableEnhancement ? 'ON' : 'OFF'} • 
            Profile: {settings.verbosity}
          </small>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            style={{
              padding: '0.4rem 0.8rem',
              backgroundColor: showSettings ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            ⚙️ Settings
          </button>
          <button
            onClick={clearMessages}
            style={{
              padding: '0.4rem 0.8rem',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div style={{ 
          padding: '1rem', 
          borderBottom: '1px solid #eee',
          background: '#fff3cd',
          fontSize: '0.9rem'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.3rem' }}>
                Verbosity Level
              </label>
              <select
                value={settings.verbosity}
                onChange={(e) => setSettings(prev => ({ ...prev, verbosity: e.target.value as any }))}
                style={{ width: '100%', padding: '0.3rem', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="minimal">Minimal</option>
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
            
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.3rem' }}>
                Ask-Me Threshold: {settings.askMeThreshold}
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={settings.askMeThreshold}
                onChange={(e) => setSettings(prev => ({ ...prev, askMeThreshold: parseFloat(e.target.value) }))}
                style={{ width: '100%' }}
              />
              <small style={{ color: '#666' }}>Higher = more clarification requests</small>
            </div>
            
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.3rem' }}>
                Risk Stance
              </label>
              <select
                value={settings.riskStance}
                onChange={(e) => setSettings(prev => ({ ...prev, riskStance: e.target.value as any }))}
                style={{ width: '100%', padding: '0.3rem', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="conservative">Conservative</option>
                <option value="balanced">Balanced</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
          </div>
          
          <div style={{ marginTop: '1rem', display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={settings.enableEnhancement}
                onChange={(e) => setSettings(prev => ({ ...prev, enableEnhancement: e.target.checked }))}
              />
              Enable Prompt Enhancement Pipeline
            </label>
            
            <div>
              <label style={{ marginRight: '0.5rem', fontWeight: '600' }}>Model:</label>
              <select
                value={settings.model}
                onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
                style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid #ccc' }}
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
      <div style={{ 
        flex: 1, 
        padding: '1rem', 
        overflowY: 'auto',
        background: '#fff'
      }}>
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              marginBottom: '1rem',
              display: 'flex',
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row'
            }}
          >
            <div
              style={{
                maxWidth: '70%',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                backgroundColor: 
                  message.role === 'user' ? '#007bff' : 
                  message.role === 'system' ? '#6c757d' : '#f1f3f4',
                color: 
                  message.role === 'user' ? 'white' : 
                  message.role === 'system' ? 'white' : '#333'
              }}
            >
              <div style={{ marginBottom: '0.25rem' }}>
                {message.content}
              </div>
              
              <div style={{ 
                fontSize: '0.7rem', 
                opacity: 0.8,
                marginTop: '0.5rem',
                borderTop: message.role !== 'user' ? '1px solid rgba(0,0,0,0.1)' : 'none',
                paddingTop: message.role !== 'user' ? '0.25rem' : '0'
              }}>
                {message.timestamp.toLocaleTimeString()}
                {message.metadata && (
                  <>
                    {message.metadata.model && ` • ${message.metadata.model}`}
                    {message.metadata.prompt_enhanced && ` • Enhanced`}
                    {message.metadata.processing_time && ` • ${message.metadata.processing_time}ms`}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            color: '#666'
          }}>
            <div style={{ 
              width: '12px', 
              height: '12px', 
              border: '2px solid #007bff', 
              borderTop: '2px solid transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            Generating response...
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ 
        padding: '1rem', 
        borderTop: '1px solid #eee',
        background: '#f8f9fa'
      }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            style={{
              flex: 1,
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '6px',
              resize: 'none',
              minHeight: '44px',
              maxHeight: '120px',
              fontSize: '0.9rem'
            }}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: isLoading || !inputValue.trim() ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isLoading || !inputValue.trim() ? 'not-allowed' : 'pointer',
              fontSize: '0.9rem',
              whiteSpace: 'nowrap'
            }}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
        
        <div style={{ 
          marginTop: '0.5rem', 
          fontSize: '0.75rem', 
          color: '#666',
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span>
            Enhancement: {settings.enableEnhancement ? 'ON' : 'OFF'} • 
            Risk: {settings.riskStance} • 
            Verbosity: {settings.verbosity}
          </span>
          <span>
            {inputValue.length}/2000
          </span>
        </div>
      </div>

      {/* CSS for spinning animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}