import { useState } from 'react'
import Footer from './components/Footer'

function App() {
  const [activeTab, setActiveTab] = useState('chat')

  const tabs = [
    { id: 'chat', label: 'Chat' },
    { id: 'status', label: 'System Status' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'settings', label: 'Settings' }
  ]

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <header style={{ 
        padding: '1rem 2rem', 
        borderBottom: '1px solid #eee',
        background: '#f8f9fa'
      }}>
        <h1 style={{ margin: 0, color: '#333' }}>Sophia AI Intel</h1>
        <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>
          Autonomous AI Intelligence Platform • Default LLM: ChatGPT-5
        </p>
      </header>

      <nav style={{ 
        padding: '0 2rem', 
        borderBottom: '1px solid #eee',
        background: '#fff'
      }}>
        <div style={{ display: 'flex', gap: '2rem' }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '1rem 0',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                borderBottom: activeTab === tab.id ? '2px solid #007bff' : '2px solid transparent',
                color: activeTab === tab.id ? '#007bff' : '#666',
                fontWeight: activeTab === tab.id ? '600' : '400'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <main style={{ 
        flex: 1, 
        padding: '2rem',
        background: '#f8f9fa'
      }}>
        {activeTab === 'chat' && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2>AI Chat Interface</h2>
            <p>ChatGPT-5 powered conversation interface coming soon...</p>
            <div style={{ 
              padding: '1rem', 
              background: '#f8f9fa', 
              borderRadius: '4px',
              marginTop: '1rem'
            }}>
              <strong>Default Model:</strong> ChatGPT-5 (GPT-5)<br />
              <strong>Fallback:</strong> Claude 3.5 Sonnet, GPT-4o<br />
              <strong>Router:</strong> Portkey with best-recent models policy
            </div>
          </div>
        )}

        {activeTab === 'status' && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2>System Status</h2>
            <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP Research</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-research.fly.dev</p>
              </div>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP Context</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-context.fly.dev</p>
              </div>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP GitHub</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-repo.fly.dev</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'integrations' && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2>Integrations</h2>
            <p>Business system integrations and MCP services configuration.</p>
          </div>
        )}

        {activeTab === 'settings' && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2>Settings</h2>
            <p>System configuration and preferences.</p>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}

export default App

