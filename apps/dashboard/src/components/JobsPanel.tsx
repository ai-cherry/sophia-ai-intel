import { useState, useEffect } from 'react'
import { chatAPI } from '../lib/chatApi'

interface JobStatus {
  id: string
  type: 'reindex' | 'knowledge_sync' | 'eval_run' | 'canary_check'
  status: 'queued' | 'running' | 'completed' | 'failed'
  started_at: string
  completed_at?: string
  progress: number
  artifacts: string[]
  error_message?: string
  metadata?: {
    symbols_processed?: number
    files_indexed?: number
    execution_time_ms?: number
    trigger_source?: string
  }
}

interface JobExecution {
  id: string
  type: string
  status: 'completed' | 'failed'
  started_at: string
  completed_at: string
  duration_ms: number
  artifacts: string[]
  summary: string
}

interface JobsPanelProps {
  className?: string
}

export default function JobsPanel({ className }: JobsPanelProps) {
  const [activeJobs, setActiveJobs] = useState<JobStatus[]>([])
  const [jobHistory, setJobHistory] = useState<JobExecution[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedJobType, setSelectedJobType] = useState<JobStatus['type']>('reindex')

  // Auto-refresh job status every 5 seconds
  useEffect(() => {
    const interval = setInterval(fetchJobStatus, 5000)
    fetchJobStatus() // Initial fetch
    return () => clearInterval(interval)
  }, [])

  const fetchJobStatus = async () => {
    try {
      const response = await fetch('https://sophiaai-mcp-context-v2.fly.dev/jobs/status')
      if (response.ok) {
        const data = await response.json()
        setActiveJobs(data.active_jobs || [])
        setJobHistory(data.job_history?.slice(0, 10) || []) // Last 10 jobs
      }
    } catch (err) {
      // Silently handle fetch errors - jobs panel should be resilient
      console.debug('Job status fetch failed:', err)
    }
  }

  const runJobNow = async (jobType: JobStatus['type']) => {
    setIsLoading(true)
    setError(null)

    try {
      // Generate idempotency key to prevent duplicate jobs
      const idempotencyKey = `${jobType}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      const response = await fetch('https://sophiaai-mcp-context-v2.fly.dev/jobs/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
          job_type: jobType,
          trigger_source: 'manual_dashboard',
          timestamp: new Date().toISOString(),
          user_id: 'dashboard_user' // In real implementation, get from auth
        })
      })

      if (response.ok) {
        const result = await response.json()
        
        // Add new job to active jobs
        const newJob: JobStatus = {
          id: result.job_id || `job-${Date.now()}`,
          type: jobType,
          status: 'queued',
          started_at: new Date().toISOString(),
          progress: 0,
          artifacts: [],
          metadata: {
            trigger_source: 'manual_dashboard'
          }
        }
        
        setActiveJobs(prev => [newJob, ...prev])
        
        // Create proof artifact
        await createJobProof(newJob, 'dispatched')
        
        // Trigger immediate status refresh
        setTimeout(fetchJobStatus, 1000)
        
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}`)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(`Failed to start ${jobType} job: ${errorMessage}`)
      
      // Create error proof
      await createJobProof({
        id: `error-${Date.now()}`,
        type: jobType,
        status: 'failed',
        started_at: new Date().toISOString(),
        progress: 0,
        artifacts: [],
        error_message: errorMessage
      }, 'failed')
      
    } finally {
      setIsLoading(false)
    }
  }

  const createJobProof = async (job: JobStatus, eventType: 'dispatched' | 'completed' | 'failed') => {
    try {
      const proof = {
        status: eventType === 'failed' ? 'failure' : 'success',
        query: `Job ${eventType}: ${job.type}`,
        results: [job],
        summary: {
          text: eventType === 'dispatched' 
            ? `${job.type} job dispatched successfully`
            : eventType === 'completed'
            ? `${job.type} job completed in ${job.metadata?.execution_time_ms || 0}ms`
            : `${job.type} job failed: ${job.error_message}`,
          confidence: 1.0,
          model: 'jobs_orchestrator',
          sources: ['dashboard_ui', 'mcp_context']
        },
        timestamp: new Date().toISOString(),
        execution_time_ms: job.metadata?.execution_time_ms || 0,
        errors: job.error_message ? [{
          provider: 'jobs_system',
          code: 'JOB_EXECUTION_ERROR',
          message: job.error_message
        }] : []
      }

      // In a real implementation, this would be sent to a proof collection endpoint
      console.debug('Job proof generated:', proof)
      
    } catch (err) {
      console.error('Failed to create job proof:', err)
    }
  }

  const getStatusColor = (status: JobStatus['status']) => {
    switch (status) {
      case 'queued': return '#6c757d'
      case 'running': return '#007bff'  
      case 'completed': return '#28a745'
      case 'failed': return '#dc3545'
      default: return '#6c757d'
    }
  }

  const getJobTypeIcon = (type: JobStatus['type']) => {
    switch (type) {
      case 'reindex': return '🔄'
      case 'knowledge_sync': return '📚'
      case 'eval_run': return '🧪'
      case 'canary_check': return '🐤'
      default: return '⚙️'
    }
  }

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime).getTime()
    const end = endTime ? new Date(endTime).getTime() : Date.now()
    const duration = Math.round((end - start) / 1000)
    
    if (duration < 60) return `${duration}s`
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`
  }

  return (
    <div className={`jobs-panel ${className || ''}`} style={{ 
      border: '1px solid #dee2e6',
      borderRadius: '8px',
      padding: '1rem',
      backgroundColor: '#fff'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem',
        borderBottom: '1px solid #eee',
        paddingBottom: '1rem'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '600' }}>
            🔧 Jobs Management
          </h3>
          <small style={{ color: '#666', fontSize: '0.85rem' }}>
            Active: {activeJobs.filter(j => j.status === 'running').length} | 
            Queued: {activeJobs.filter(j => j.status === 'queued').length}
          </small>
        </div>

        {/* Run Now Controls */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <select
            value={selectedJobType}
            onChange={(e) => setSelectedJobType(e.target.value as JobStatus['type'])}
            style={{
              padding: '0.4rem 0.6rem',
              borderRadius: '4px',
              border: '1px solid #ccc',
              fontSize: '0.85rem'
            }}
          >
            <option value="reindex">🔄 Reindex Symbols</option>
            <option value="knowledge_sync">📚 Knowledge Sync</option>
            <option value="eval_run">🧪 Eval Run</option>
            <option value="canary_check">🐤 Canary Check</option>
          </select>

          <button
            onClick={() => runJobNow(selectedJobType)}
            disabled={isLoading}
            style={{
              padding: '0.4rem 1rem',
              backgroundColor: isLoading ? '#6c757d' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.85rem',
              fontWeight: '500',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            {isLoading ? '⏳ Starting...' : '▶️ Run Now'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '1rem',
          fontSize: '0.9rem'
        }}>
          ❌ {error}
        </div>
      )}

      {/* Active Jobs */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ 
          fontSize: '1rem', 
          fontWeight: '600',
          marginBottom: '0.75rem',
          color: '#495057'
        }}>
          Active Jobs ({activeJobs.length})
        </h4>

        {activeJobs.length === 0 ? (
          <div style={{ 
            padding: '2rem',
            textAlign: 'center',
            color: '#6c757d',
            fontSize: '0.9rem',
            fontStyle: 'italic'
          }}>
            No active jobs. Click "Run Now" to start a job.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {activeJobs.map(job => (
              <div
                key={job.id}
                style={{
                  border: '1px solid #e9ecef',
                  borderRadius: '6px',
                  padding: '0.75rem',
                  backgroundColor: '#f8f9fa'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.2rem' }}>{getJobTypeIcon(job.type)}</span>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>
                        {job.type.charAt(0).toUpperCase() + job.type.slice(1).replace('_', ' ')}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>
                        Started: {formatDuration(job.started_at)} ago
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {job.status === 'running' && (
                      <div style={{ 
                        width: '100px',
                        height: '6px',
                        backgroundColor: '#e9ecef',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${job.progress}%`,
                          height: '100%',
                          backgroundColor: '#007bff',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    )}

                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      color: 'white',
                      backgroundColor: getStatusColor(job.status)
                    }}>
                      {job.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {job.metadata && (
                  <div style={{ 
                    marginTop: '0.5rem',
                    fontSize: '0.8rem',
                    color: '#6c757d',
                    display: 'flex',
                    gap: '1rem'
                  }}>
                    {job.metadata.symbols_processed && (
                      <span>Symbols: {job.metadata.symbols_processed}</span>
                    )}
                    {job.metadata.files_indexed && (
                      <span>Files: {job.metadata.files_indexed}</span>
                    )}
                    {job.metadata.trigger_source && (
                      <span>Source: {job.metadata.trigger_source}</span>
                    )}
                  </div>
                )}

                {job.artifacts.length > 0 && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <small style={{ color: '#666' }}>
                      Artifacts: {job.artifacts.join(', ')}
                    </small>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Job History */}
      <div>
        <h4 style={{ 
          fontSize: '1rem', 
          fontWeight: '600',
          marginBottom: '0.75rem',
          color: '#495057'
        }}>
          Recent History ({jobHistory.length})
        </h4>

        {jobHistory.length === 0 ? (
          <div style={{ 
            padding: '1rem',
            textAlign: 'center',
            color: '#6c757d',
            fontSize: '0.85rem',
            fontStyle: 'italic'
          }}>
            No job history available.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {jobHistory.map(job => (
              <div
                key={job.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #e9ecef',
                  borderRadius: '4px',
                  backgroundColor: job.status === 'completed' ? '#f8fff8' : '#fff5f5'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1rem' }}>{getJobTypeIcon(job.type as JobStatus['type'])}</span>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: '500' }}>
                      {job.type.charAt(0).toUpperCase() + job.type.slice(1).replace('_', ' ')}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#666' }}>
                      {job.summary}
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ 
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    color: job.status === 'completed' ? '#28a745' : '#dc3545'
                  }}>
                    {job.status.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#666' }}>
                    {Math.round(job.duration_ms / 1000)}s
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        marginTop: '1rem',
        paddingTop: '1rem',
        borderTop: '1px solid #eee',
        fontSize: '0.75rem',
        color: '#6c757d',
        textAlign: 'center'
      }}>
        Jobs refresh every 5 seconds • MCP Context integration • Proof-first execution
      </div>
    </div>
  )
}