import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { agnosticCoordinator } from './coordinator/coordinator';
import { healthChecker } from './health/healthChecker';
import { configManager } from './config/config';
import { featureFlags } from './config/featureFlags';
import { PipelineRequest } from './config/types';

/**
 * Main server for AGNO Coordinator Service
 */
class Server {
  private app: express.Application;
  private port: number;

  constructor(port: number = 3001) {
    this.port = port;
    this.app = express();
    this.configureMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  /**
   * Configure Express middleware
   */
  private configureMiddleware(): void {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: false, // Disable CSP for API
      crossOriginEmbedderPolicy: false
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
    }));

    // Compression
    this.app.use(compression());

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging
    this.app.use((req, res, next) => {
      const start = Date.now();
      res.on('finish', () => {
        const duration = Date.now() - start;
        console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
      });
      next();
    });
  }

  /**
   * Set up API routes
   */
  private setupRoutes(): void {
    // Health check endpoint
    this.app.get('/healthz', async (req, res) => {
      try {
        const health = await healthChecker.getHealthStatus();
        const statusCode = health.status === 'healthy' ? 200 : 503;
        res.status(statusCode).json(health);
      } catch (error) {
        res.status(503).json({
          service: 'agno-coordinator',
          status: 'unhealthy',
          error: error instanceof Error ? error.message : 'Health check failed',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Detailed health check
    this.app.get('/health/detailed', async (req, res) => {
      try {
        const report = await healthChecker.getDetailedHealthReport();
        const statusCode = report.status.status === 'healthy' ? 200 : 503;
        res.status(statusCode).json(report);
      } catch (error) {
        res.status(503).json({
          error: error instanceof Error ? error.message : 'Detailed health check failed',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Main routing endpoint
    this.app.post('/route', async (req, res) => {
      try {
        const request: PipelineRequest = req.body;

        // Validate request
        if (!request || !request.userPrompt) {
          return res.status(400).json({
            error: 'Invalid request: userPrompt is required',
            timestamp: new Date().toISOString()
          });
        }

        // Route the request
        const result = await agnosticCoordinator.routeRequest(request);
        res.json(result);

      } catch (error) {
        console.error('Request routing error:', error);
        res.status(500).json({
          error: 'Internal server error',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Feature flag management endpoints
    this.app.get('/flags', (req, res) => {
      try {
        const flags = featureFlags.getAllFlags();
        res.json({
          flags,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to get feature flags',
          timestamp: new Date().toISOString()
        });
      }
    });

    this.app.put('/flags/:flag', (req, res) => {
      try {
        const { flag } = req.params;
        const { enabled } = req.body;

        if (typeof enabled !== 'boolean') {
          return res.status(400).json({
            error: 'Invalid request: enabled must be a boolean',
            timestamp: new Date().toISOString()
          });
        }

        featureFlags.setFlag(flag, enabled);
        res.json({
          flag,
          enabled,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to update feature flag',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Configuration endpoint
    this.app.get('/config', (req, res) => {
      try {
        const config = configManager.getConfigSummary();
        res.json({
          config,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to get configuration',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Statistics endpoint
    this.app.get('/stats', (req, res) => {
      try {
        const stats = agnosticCoordinator.getStatistics();
        res.json({
          stats,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to get statistics',
          timestamp: new Date().toISOString()
        });
      }
    });

    // Debug endpoints (only in development)
    if (process.env.NODE_ENV !== 'production') {
      this.app.get('/debug/config', (req, res) => {
        res.json({
          config: configManager.getConfig(),
          featureFlags: featureFlags.getAllFlags(),
          timestamp: new Date().toISOString()
        });
      });

      this.app.post('/debug/test', async (req, res) => {
        try {
          const testRequest: PipelineRequest = {
            userPrompt: 'This is a test request for debugging',
            sessionId: 'test-session',
            userId: 'test-user'
          };

          const result = await agnosticCoordinator.routeRequest(testRequest);
          res.json({
            test: 'successful',
            result,
            timestamp: new Date().toISOString()
          });
        } catch (error) {
          res.status(500).json({
            test: 'failed',
            error: error instanceof Error ? error.message : 'Unknown error',
            timestamp: new Date().toISOString()
          });
        }
      });
    }

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not found',
        path: req.originalUrl,
        timestamp: new Date().toISOString()
      });
    });
  }

  /**
   * Set up error handling
   */
  private setupErrorHandling(): void {
    // Global error handler
    this.app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      console.error('Unhandled error:', error);

      res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
        timestamp: new Date().toISOString()
      });
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
      process.exit(1);
    });
  }

  /**
   * Start the server
   */
  async start(): Promise<void> {
    try {
      // Initialize the coordinator
      await agnosticCoordinator.initialize();

      // Start the HTTP server
      this.app.listen(this.port, () => {
        console.log(`🚀 AGNO Coordinator Service listening on port ${this.port}`);
        console.log(`📊 Health check available at: http://localhost:${this.port}/healthz`);
        console.log(`🔧 Configuration:`, configManager.getConfigSummary());
        console.log(`🏷️  Feature flags:`, featureFlags.getAllFlags());
      });

    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  /**
   * Stop the server
   */
  async stop(): Promise<void> {
    console.log('Stopping AGNO Coordinator Service...');

    try {
      await agnosticCoordinator.shutdown();
      console.log('✅ Server stopped successfully');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }

  /**
   * Get the Express app (for testing)
   */
  getApp(): express.Application {
    return this.app;
  }
}

// Create and start server
const server = new Server();

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, shutting down gracefully...');
  await server.stop();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('Received SIGINT, shutting down gracefully...');
  await server.stop();
  process.exit(0);
});

// Start the server
server.start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

export default server;