#!/usr/bin/env ts-node
/**
 * Agno Coordinator Service - AI Agent Coordination Platform
 * =========================================================
 * 
 * HTTP server for coordinating AI agents and managing distributed workflows
 * Provides REST API endpoints for agent orchestration and coordination
 */

import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import morgan from 'morgan'

const app = express()
const PORT = process.env.PORT || 8080

// Middleware
app.use(helmet())
app.use(cors())
app.use(compression())
app.use(morgan('combined'))
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// Mock agent coordination functionality
class AgentCoordinator {
  private agents: Map<string, any> = new Map()
  private activeJobs: Map<string, any> = new Map()

  getAgentCount(): number {
    return this.agents.size
  }

  getActiveJobCount(): number {
    return this.activeJobs.size
  }

  getStats() {
    return {
      totalAgents: this.getAgentCount(),
      activeJobs: this.getActiveJobCount(),
      successRate: 0.95,
      averageResponseTime: 125
    }
  }

  registerAgent(agentId: string, capabilities: string[]) {
    this.agents.set(agentId, {
      id: agentId,
      capabilities,
      status: 'online',
      registeredAt: new Date()
    })
  }

  async coordinateJob(jobRequest: any) {
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    this.activeJobs.set(jobId, {
      ...jobRequest,
      id: jobId,
      status: 'processing',
      startedAt: new Date()
    })

    // Simulate job processing
    setTimeout(() => {
      this.activeJobs.delete(jobId)
    }, 5000)

    return {
      jobId,
      status: 'accepted',
      estimatedCompletion: new Date(Date.now() + 5000)
    }
  }
}

const coordinator = new AgentCoordinator()

// Initialize some mock agents
coordinator.registerAgent('agent_001', ['nlp', 'summarization'])
coordinator.registerAgent('agent_002', ['vision', 'classification']) 
coordinator.registerAgent('agent_003', ['reasoning', 'planning'])

// Health check endpoint
app.get('/healthz', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    service: 'agno-coordinator',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    agents: coordinator.getAgentCount(),
    activeJobs: coordinator.getActiveJobCount()
  })
})

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Agno Coordinator - AI Agent Coordination Platform',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/healthz',
      agents: 'GET /agents',
      jobs: 'POST /jobs',
      stats: '/stats',
      docs: '/docs'
    },
    agents: coordinator.getAgentCount(),
    activeJobs: coordinator.getActiveJobCount()
  })
})

// Get agent statistics
app.get('/stats', (req, res) => {
  const stats = coordinator.getStats()
  res.json({
    service: 'agno-coordinator',
    statistics: stats,
    timestamp: new Date().toISOString()
  })
})

// Get registered agents
app.get('/agents', (req, res) => {
  res.json({
    agents: Array.from(coordinator['agents'].values()),
    count: coordinator.getAgentCount(),
    timestamp: new Date().toISOString()
  })
})

// Coordinate new job
app.post('/jobs', async (req, res) => {
  try {
    const jobRequest = req.body
    
    if (!jobRequest.type || !jobRequest.requirements) {
      return res.status(400).json({
        error: 'Missing required fields: type and requirements'
      })
    }

    const result = await coordinator.coordinateJob(jobRequest)
    
    res.json({
      success: true,
      job: result,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Job coordination error:', error)
    res.status(500).json({
      error: 'Internal coordination error',
      message: (error as Error).message
    })
  }
})

// Get active jobs
app.get('/jobs', (req, res) => {
  const activeJobs = Array.from(coordinator['activeJobs'].values())
  res.json({
    jobs: activeJobs,
    count: activeJobs.length,
    timestamp: new Date().toISOString()
  })
})

// API Documentation
app.get('/docs', (req, res) => {
  res.json({
    service: 'Agno Coordinator - AI Agent Coordination Platform',
    version: '1.0.0',
    description: 'Coordinates AI agents and manages distributed workflows across the Sophia AI platform',
    endpoints: {
      'GET /': 'Service information',
      'GET /healthz': 'Health check',
      'GET /agents': 'Get registered agents',
      'POST /jobs': 'Submit new coordination job',
      'GET /jobs': 'Get active jobs',
      'GET /stats': 'Get coordination statistics',
      'GET /docs': 'This documentation'
    },
    jobRequestFormat: {
      type: 'string (required) - Job type: nlp, vision, reasoning, etc.',
      requirements: 'array (required) - Required capabilities',
      priority: 'number (optional) - Job priority 1-10',
      timeout: 'number (optional) - Max execution time in ms',
      context: 'object (optional) - Additional context data'
    }
  })
})

// Error handling middleware
app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Express error:', error)
  res.status(500).json({
    error: 'Internal server error',
    message: error.message,
    timestamp: new Date().toISOString()
  })
})

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    available: '/healthz, /agents, /jobs, /stats, /docs',
    timestamp: new Date().toISOString()
  })
})

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Agno Coordinator Service running on port ${PORT}`)
  console.log(`📊 Health check: http://localhost:${PORT}/healthz`)
  console.log(`📚 Documentation: http://localhost:${PORT}/docs`)
  console.log(`🔧 Environment: ${process.env.NODE_ENV || 'development'}`)
  console.log(`🤖 Registered agents: ${coordinator.getAgentCount()}`)
})

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('⏹️ Received SIGTERM, shutting down gracefully')
  server.close(() => {
    console.log('✅ Server closed')
    process.exit(0)
  })
})

process.on('SIGINT', () => {
  console.log('⏹️ Received SIGINT, shutting down gracefully')
  server.close(() => {
    console.log('✅ Server closed')
    process.exit(0)
  })
})

export default app