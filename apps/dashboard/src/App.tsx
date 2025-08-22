import { useState, useEffect } from 'react'
import Footer from './components/Footer'
import ChatInterface from './components/ChatInterface'
import { buildGuard } from './lib/buildInfo'

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [gtmData, setGtmData] = useState({ prospects: [], signals: {}, loading: false, error: null })

  const tabs = [
    { id: 'chat', label: 'Chat' },
    { id: 'gtm', label: 'GTM' },
    { id: 'status', label: 'System Status' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'settings', label: 'Settings' }
  ]

  // GTM data fetching function
  const fetchGTMData = async () => {
    setGtmData(prev => ({ ...prev, loading: true, error: null }))
    
    try {
      const businessUrl = 'https://sophiaai-mcp-business-v2.fly.dev'
      
      // Fetch prospects
      const prospectsResponse = await fetch(`${businessUrl}/prospects/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'multifamily AI delinquency prevention',
          k: 10,
          providers: ['apollo', 'hubspot'],
          timeout_s: 15,
          budget_cents: 500
        })
      })
      
      // Fetch signals digest
      const signalsResponse = await fetch(`${businessUrl}/signals/digest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          window: '7d',
          channels: ['telegram']
        })
      })
      
      const prospects = prospectsResponse.ok ? await prospectsResponse.json() : { results: [], error: 'Service unavailable' }
      const signals = signalsResponse.ok ? await signalsResponse.json() : { error: 'Service unavailable' }
      
      setGtmData(prev => ({
        ...prev,
        prospects: prospects.results || [],
        signals: signals,
        loading: false
      }))
    } catch (error) {
      setGtmData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Failed to fetch GTM data'
      }))
    }
  }

  // Auto-fetch GTM data when tab is accessed
  useEffect(() => {
    if (activeTab === 'gtm') {
      fetchGTMData()
    }
  }, [activeTab])

  // Initialize build monitoring
  useEffect(() => {
    buildGuard.init()
  }, [])

  // Generate Sophia Infra workflow link
  const generateInfraLink = (provider, action, payload) => {
    const baseUrl = 'https://github.com/ai-cherry/sophia-ai-intel/actions/workflows/sophia_infra.yml'
    const params = new URLSearchParams({
      provider,
      action,
      payload_json: JSON.stringify(payload)
    })
    return `${baseUrl}?${params.toString()}`
  }

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
            <ChatInterface />
          </div>
        )}

        {activeTab === 'gtm' && (
          <div style={{
            background: '#fff',
            padding: '2rem',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>GTM Intelligence Dashboard</h2>
              <button
                onClick={fetchGTMData}
                disabled={gtmData.loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: gtmData.loading ? 'not-allowed' : 'pointer',
                  opacity: gtmData.loading ? 0.6 : 1
                }}
              >
                {gtmData.loading ? 'Loading...' : 'Refresh Data'}
              </button>
            </div>

            {gtmData.error && (
              <div style={{
                padding: '1rem',
                backgroundColor: '#f8d7da',
                color: '#721c24',
                border: '1px solid #f5c6cb',
                borderRadius: '4px',
                marginBottom: '1rem'
              }}>
                <strong>Error:</strong> {gtmData.error}
              </div>
            )}

            <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: '1fr 1fr' }}>
              {/* Prospects Section */}
              <div style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 1rem 0' }}>Top Prospects</h3>
                
                {gtmData.prospects.length === 0 && !gtmData.loading ? (
                  <p style={{ color: '#666', fontStyle: 'italic' }}>
                    No prospects found. Service may be unavailable or no providers configured.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {gtmData.prospects.slice(0, 5).map((prospect, index) => (
                      <div key={index} style={{
                        padding: '1rem',
                        border: '1px solid #eee',
                        borderRadius: '4px',
                        backgroundColor: '#f9f9f9'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div style={{ flex: 1 }}>
                            <strong>{prospect.company_name || 'Unknown Company'}</strong>
                            <br />
                            <span style={{ color: '#666' }}>
                              {prospect.contact_name} • {prospect.contact_title}
                            </span>
                            <br />
                            <small style={{ color: '#888' }}>
                              {prospect.contact_email} • Score: {prospect.score.toFixed(1)}
                            </small>
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <span style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: prospect.source === 'apollo' ? '#4CAF50' : '#2196F3',
                              color: 'white',
                              borderRadius: '12px',
                              fontSize: '0.75rem',
                              textTransform: 'uppercase'
                            }}>
                              {prospect.source}
                            </span>
                            <a
                              href={generateInfraLink('biz', 'enrich', { emails: [prospect.contact_email] })}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: '#FF9800',
                                color: 'white',
                                textDecoration: 'none',
                                borderRadius: '4px',
                                fontSize: '0.75rem'
                              }}
                            >
                              Enrich
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                  <a
                    href={generateInfraLink('biz', 'search', { query: 'AI PropTech multifamily', k: 20 })}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-block',
                      padding: '0.5rem 1rem',
                      backgroundColor: '#007bff',
                      color: 'white',
                      textDecoration: 'none',
                      borderRadius: '4px',
                      fontSize: '0.9rem'
                    }}
                  >
                    🔍 Run Advanced Search
                  </a>
                </div>
              </div>

              {/* Signals Section */}
              <div style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 1rem 0' }}>Revenue Signals (7d)</h3>
                
                {gtmData.signals.error ? (
                  <p style={{ color: '#666', fontStyle: 'italic' }}>
                    Signals unavailable: {gtmData.signals.error}
                  </p>
                ) : gtmData.signals.digest_results ? (
                  <div>
                    {gtmData.signals.digest_results.slack && (
                      <div style={{ marginBottom: '1rem' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#4A154B' }}>
                          💬 Slack #GTM Activity
                        </h4>
                        <p>Messages: {gtmData.signals.digest_results.slack.messages_found || 0}</p>
                        <p>Channels: {gtmData.signals.digest_results.slack.channels_processed || 0}</p>
                        
                        {gtmData.signals.digest_results.slack.key_topics &&
                         gtmData.signals.digest_results.slack.key_topics.length > 0 ? (
                          <div>
                            <h5>Key Topics:</h5>
                            {gtmData.signals.digest_results.slack.key_topics.slice(0, 3).map((topic, index) => (
                              <div key={index} style={{
                                padding: '0.5rem',
                                backgroundColor: '#f0f0f0',
                                borderRadius: '4px',
                                margin: '0.25rem 0',
                                fontSize: '0.85rem'
                              }}>
                                {topic.text}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: '#666', fontSize: '0.9rem' }}>No key topics detected</p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <p style={{ color: '#666', fontStyle: 'italic' }}>
                    No signals data available. Check Slack integration status.
                  </p>
                )}

                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                  <a
                    href={generateInfraLink('biz', 'digest', { window: '24h', channels: ['slack:#gtm', 'slack:#revenue'] })}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-block',
                      padding: '0.5rem 1rem',
                      backgroundColor: '#28a745',
                      color: 'white',
                      textDecoration: 'none',
                      borderRadius: '4px',
                      fontSize: '0.9rem'
                    }}
                  >
                    📊 Generate Full Digest
                  </a>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div style={{
              marginTop: '2rem',
              padding: '1.5rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              <h3 style={{ margin: '0 0 1rem 0' }}>Quick Actions</h3>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <a
                  href={generateInfraLink('biz', 'sync', { list: 'q1-targets', provider: 'hubspot', mode: 'read' })}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: '#6f42c1',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '0.9rem'
                  }}
                >
                  🔄 Sync HubSpot
                </a>
                <a
                  href={generateInfraLink('biz', 'upload', { provider: 'csv', filename: 'manual_prospects.csv' })}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: '#fd7e14',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '0.9rem'
                  }}
                >
                  📤 Upload CSV
                </a>
                <a
                  href="https://sophiaai-mcp-business-v2.fly.dev/healthz"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: '#20c997',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '0.9rem'
                  }}
                >
                  🏥 Service Health
                </a>
              </div>
            </div>

            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#e7f3ff',
              border: '1px solid #b8daff',
              borderRadius: '6px',
              fontSize: '0.85rem',
              color: '#004085'
            }}>
              <strong>🔒 CEO Notice:</strong> All write operations require manual approval via Sophia Infra workflows.
              Read-only data is refreshed automatically. Provider availability depends on configured secrets.
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
                <h3>MCP Research v2</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-research-v2.fly.dev</p>
              </div>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP Context v2</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-context-v2.fly.dev</p>
              </div>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP GitHub v2</h3>
                <p>Status: <span style={{ color: 'green' }}>●</span> Healthy</p>
                <p>URL: https://sophiaai-mcp-repo-v2.fly.dev</p>
              </div>
              <div style={{ padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                <h3>MCP Business v1</h3>
                <p>Status: <span style={{ color: 'orange' }}>●</span> Deploying</p>
                <p>URL: https://sophiaai-mcp-business-v2.fly.dev</p>
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

