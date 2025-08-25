#!/usr/bin/env ts-node
/**
 * Sophia AI Intel - Orchestrator HTTP Server
 * ==========================================
 * 
 * HTTP wrapper for the pipeline orchestrator service
 * Provides REST API endpoints for orchestration functionality
 */

import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import morgan from 'morgan'
import { pipelineOrchestrator, executeOrchestration, PipelineRequest } from './orchestrator'

const app = express()
const PORT = process.env.PORT || 8080

// Middleware
app.use(helmet())
app.use(cors())
app.use(compression())
app.use(morgan('combined'))
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// Health check endpoint
app.get('/healthz', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    service: 'sophia-orchestrator',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    activeExecutions: pipelineOrchestrator.getActiveExecutions().length
  })
})

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Sophia AI Intel - Pipeline Orchestrator',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/healthz',
      orchestrate: 'POST /orchestrate',
      stats: '/stats',
      docs: '/docs'
    },
    activeExecutions: pipelineOrchestrator.getActiveExecutions().length
  })
})

// Main orchestration endpoint
app.post('/orchestrate', async (req, res) => {
  try {
    const request: PipelineRequest = req.body
    
    // Validate required fields
    if (!request.userPrompt || !request.sessionId) {
      return res.status(400).json({
        error: 'Missing required fields: userPrompt and sessionId'
      })
    }

    console.log(`🚀 Starting orchestration for session: ${request.sessionId}`)
    
    // Execute pipeline
    const result = await executeOrchestration(request)
    
    // Return result
    res.json({
      success: result.success,
      response: result.response,
      executionId: result.executionId,
      executionTime: result.totalExecutionTimeMs,
      phases: result.phases.length,
      toolsExecuted: result.toolExecutions.length,
      metadata: {
        timestamp: result.metadata.timestamp,
        proofCount: result.metadata.proofCount
      }
    })

  } catch (error) {
    console.error('Orchestration error:', error)
    res.status(500).json({
      error: 'Internal orchestration error',
      message: (error as Error).message
    })
  }
})

// Get orchestration statistics
app.get('/stats', (req, res) => {
  const stats = pipelineOrchestrator.getStats()
  res.json({
    service: 'sophia-orchestrator',
    statistics: stats,
    timestamp: new Date().toISOString()
  })
})

// Get active executions
app.get('/executions', (req, res) => {
  const activeExecutions = pipelineOrchestrator.getActiveExecutions()
  res.json({
    activeExecutions,
    count: activeExecutions.length,
    timestamp: new Date().toISOString()
  })
})

// Cancel execution
app.delete('/executions/:executionId', async (req, res) => {
  const { executionId } = req.params
  const cancelled = await pipelineOrchestrator.cancelExecution(executionId)
  
  res.json({
    cancelled,
    executionId,
    timestamp: new Date().toISOString()
  })
})

// API Documentation
app.get('/docs', (req, res) => {
  res.json({
    service: 'Sophia AI Intel - Pipeline Orchestrator',
    version: '1.0.0',
    description: 'Coordinates the complete one-chat pipeline: prompt → retrieval → planning → tools → synthesis',
    endpoints: {
      'GET /': 'Service information',
      'GET /healthz': 'Health check',
      'POST /orchestrate': 'Execute pipeline orchestration',
      'GET /stats': 'Get orchestration statistics',
      'GET /executions': 'Get active executions',
      'DELETE /executions/:id': 'Cancel execution',
      'GET /docs': 'This documentation'
    },
    requestFormat: {
      userPrompt: 'string (required)',
      sessionId: 'string (required)', 
      userId: 'string (optional)',
      context: {
        conversationHistory: 'array (optional)',
        metadata: 'object (optional)',
        preferences: 'object (optional)'
      },
      constraints: {
        maxExecutionTime: 'number (optional)',
        maxToolCalls: 'number (optional)',
        allowedTools: 'array (optional)'
      }
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
    available: '/healthz, /orchestrate, /stats, /executions, /docs',
    timestamp: new Date().toISOString()
  })
})

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Sophia Orchestrator Service running on port ${PORT}`)
  console.log(`📊 Health check: http://localhost:${PORT}/healthz`)
  console.log(`📚 Documentation: http://localhost:${PORT}/docs`)
  console.log(`🔧 Environment: ${process.env.NODE_ENV || 'development'}`)
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
