import React, { useState, useEffect } from 'react'

interface SwarmStatus {
  is_initialized: boolean
  total_agents: number
  active_tasks: number
  completed_tasks: number
  failed_tasks: number
  system_status: string
}

interface AgentInfo {
  name: string
  role: string
  is_active: boolean
  current_tasks: number
}

export default function AgentSwarmPanel() {
  const [swarmStatus, setSwarmStatus] = useState<SwarmStatus | null>(null)
  const [agents, setAgents] = useState<Record<string, AgentInfo>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const swarmBaseUrl = 'https://sophiaai-mcp-agents.fly.dev'

  const fetchSwarmStatus = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const statusResponse = await fetch(`${swarmBaseUrl}/agent-swarm/status`)
      const agentsResponse = await fetch(`${swarmBaseUrl}/agent-swarm/agents`)
      
      if (statusResponse.ok) {
        const status = await statusResponse.json()
        setSwarmStatus(status)
      }
      
      if (agentsResponse.ok) {
        const agentData = await agentsResponse.json()
        setAgents(agentData.agents || {})
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch swarm status')
    } finally {
      setLoading(false)
    }
  }

  const testSwarm = async () => {
    try {
      const response = await fetch(`${swarmBaseUrl}/debug/test-swarm`, { method: 'POST' })
      const result = await response.json()
      
      if (response.ok) {
        alert('Swarm test successful! Check console for details.')
        console.log('Swarm test result:', result)
      } else {
        alert('Swarm test failed: ' + (result.detail || 'Unknown error'))
      }
    } catch (err) {
      alert('Swarm test failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  useEffect(() => {
    fetchSwarmStatus()
  }, [])

  return (
    <div style={{ padding: '2rem', background: '#fff', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0 }}>🤖 Sophia Agent Swarm</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={fetchSwarmStatus}
            disabled={loading}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? 'Loading...' : 'Refresh Status'}
          </button>
          <button
            onClick={testSwarm}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🧪 Test Swarm
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {swarmStatus && (
        <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: '1fr 2fr' }}>
          {/* Status Overview */}
          <div style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>System Status</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Initialized:</span>
                <span style={{ 
                  color: swarmStatus.is_initialized ? 'green' : 'red',
                  fontWeight: 'bold'
                }}>
                  {swarmStatus.is_initialized ? '✅ Yes' : '❌ No'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Total Agents:</span>
                <span>{swarmStatus.total_agents}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Active Tasks:</span>
                <span>{swarmStatus.active_tasks}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Completed:</span>
                <span style={{ color: 'green' }}>{swarmStatus.completed_tasks}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Failed:</span>
                <span style={{ color: 'red' }}>{swarmStatus.failed_tasks}</span>
              </div>
            </div>
          </div>

          {/* Agent List */}
          <div style={{ padding: '1.5rem', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>Active Agents</h3>
            {Object.keys(agents).length === 0 ? (
              <p style={{ color: '#666', fontStyle: 'italic' }}>No agents available</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {Object.entries(agents).map(([agentId, agent]) => (
                  <div key={agentId} style={{
                    padding: '1rem',
                    border: '1px solid #eee',
                    borderRadius: '4px',
                    backgroundColor: '#f9f9f9'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <strong>{agent.name}</strong>
                        <br />
                        <small style={{ color: '#666' }}>
                          Role: {agent.role} • Status: {agent.is_active ? 'Active' : 'Inactive'}
                        </small>
                      </div>
                      <div style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: agent.is_active ? '#28a745' : '#6c757d',
                        color: 'white',
                        borderRadius: '12px',
                        fontSize: '0.75rem'
                      }}>
                        {agent.current_tasks} tasks
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Agent Swarm Capabilities */}
      <div style={{
        marginTop: '2rem',
        padding: '1.5rem',
        backgroundColor: '#e7f3ff',
        border: '1px solid #b8daff',
        borderRadius: '8px'
      }}>
        <h3 style={{ margin: '0 0 1rem 0' }}>🚀 Agent Swarm Capabilities</h3>
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
          <div style={{ padding: '1rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ccc' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#007bff' }}>🔍 Repository Analysis</h4>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
              Semantic code analysis, pattern recognition, and quality assessment
            </p>
          </div>
          <div style={{ padding: '1rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ccc' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#28a745' }}>📋 Multi-Agent Planning</h4>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
              Cutting-edge, conservative, and synthesis planning approaches
            </p>
          </div>
          <div style={{ padding: '1rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ccc' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#fd7e14' }}>⚡ Workflow Orchestration</h4>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
              LangGraph-powered stateful workflows with conditional branching
            </p>
          </div>
        </div>
      </div>

      {/* Usage Instructions */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: '#d4edda',
        border: '1px solid #c3e6cb',
        borderRadius: '6px',
        fontSize: '0.9rem',
        color: '#155724'
      }}>
        <strong>💡 How to Use:</strong> Go to the Chat tab and ask questions like:
        <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
          <li>"Analyze this repository and tell me about its structure"</li>
          <li>"Review the code quality and identify issues"</li>
          <li>"Plan implementation for a new authentication service"</li>
          <li>"Generate code for a user management system"</li>
        </ul>
        The agent swarm will automatically activate for code-related requests!
      </div>
    </div>
  )
}
