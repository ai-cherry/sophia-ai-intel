'use client';

import { useState } from 'react';

export default function Home() {
  const [message, setMessage] = useState('');
  const [chat, setChat] = useState<Array<{role: string, content: string}>>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    const userMsg = { role: 'user', content: message };
    setChat(prev => [...prev, userMsg]);
    setMessage('');
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content })
      });
      
      const data = await response.json();
      console.log('Response:', data);
      
      // Extract the actual message from the response structure
      let aiMessage = '';
      if (data.sections?.summary) {
        aiMessage = data.sections.summary;
        if (data.sections.research?.length > 0) {
          aiMessage += '\n\nResearch Results:\n';
          data.sections.research.forEach((r: any) => {
            aiMessage += `• ${r.title}: ${r.summary}\n`;
          });
        }
      } else if (data.message) {
        aiMessage = data.message;
      } else {
        aiMessage = JSON.stringify(data);
      }
      
      setChat(prev => [...prev, { role: 'assistant', content: aiMessage }]);
    } catch (error) {
      setChat(prev => [...prev, { 
        role: 'error', 
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto', fontFamily: 'system-ui' }}>
      <h1 style={{ color: '#333' }}>🤖 Sophia AI - Local Development Chat</h1>
      
      <div style={{ 
        backgroundColor: '#e8f5e9', 
        padding: '15px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>✅ Active Services</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <div>• MCP Research (8085)</div>
          <div>• PostgreSQL (5432)</div>
          <div>• Qdrant (6333)</div>
        </div>
      </div>
      
      <div style={{ 
        height: '400px', 
        overflowY: 'auto', 
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '15px',
        backgroundColor: '#fff'
      }}>
        {chat.length === 0 ? (
          <div style={{ color: '#666', textAlign: 'center', paddingTop: '150px' }}>
            <p>👋 Welcome! Try asking me to:</p>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li>• "research langchain agent patterns"</li>
              <li>• "find github repos for AI orchestration"</li>
              <li>• "search documentation for MCP protocol"</li>
            </ul>
          </div>
        ) : (
          chat.map((msg, i) => (
            <div key={i} style={{ 
              marginBottom: '15px',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: msg.role === 'user' ? '#e3f2fd' : 
                             msg.role === 'error' ? '#ffebee' : '#f5f5f5',
              maxWidth: msg.role === 'user' ? '70%' : '100%',
              marginLeft: msg.role === 'user' ? 'auto' : '0'
            }}>
              <strong style={{ 
                color: msg.role === 'user' ? '#1976d2' : 
                       msg.role === 'error' ? '#d32f2f' : '#388e3c'
              }}>
                {msg.role === 'user' ? '👤 You' : 
                 msg.role === 'error' ? '⚠️ Error' : '🤖 Sophia'}:
              </strong>
              <div style={{ marginTop: '5px', whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </div>
            </div>
          ))
        )}
      </div>
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
          placeholder="Ask me anything about code, research, or documentation..."
          disabled={loading}
          style={{ 
            flex: 1,
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #ddd',
            fontSize: '14px'
          }}
        />
        <button 
          onClick={sendMessage}
          disabled={loading || !message.trim()}
          style={{
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: loading || !message.trim() ? '#ccc' : '#2196F3',
            color: 'white',
            cursor: loading || !message.trim() ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 'bold'
          }}
        >
          {loading ? '⏳ Sending...' : '📤 Send'}
        </button>
      </div>
      
      <div style={{ 
        marginTop: '20px', 
        padding: '15px',
        backgroundColor: '#fff3e0',
        borderRadius: '8px',
        fontSize: '13px'
      }}>
        <strong>💡 Pro Tips:</strong>
        <ul style={{ margin: '5px 0 0 20px' }}>
          <li>Research queries trigger real GitHub and web searches</li>
          <li>The MCP Research service can search code, documentation, and academic papers</li>
          <li>Claude can connect directly to these services for enhanced capabilities</li>
        </ul>
      </div>
    </div>
  );
}