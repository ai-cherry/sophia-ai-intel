import 'dotenv/config';
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
    this.app.use((_req, res, next) => {
      const start = Date.now();
      res.on('finish', () => {
        const duration = Date.now() - start;
        console.log(`${new Date().toISOString()} - ${_req.method} ${_req.path} - ${res.statusCode} - ${duration}ms`);
      });
      next();
    });
  }

  /**
   * Set up API routes
   */
  private setupRoutes(): void {
    // Health check endpoint
    this.app.get('/healthz', async (_req, res) => {
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
    this.app.get('/health/detailed', async (_req, res) => {
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
        return;

      } catch (error) {
        console.error('Request routing error:', error);
        res.status(500).json({
          error: 'Internal server error',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString()
        });
        return;
      }
    });

    // Feature flag management endpoints
    this.app.get('/flags', (_req, res) => {
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
        return;
      } catch (error) {
        res.status(500).json({
          error: 'Failed to update feature flag',
          timestamp: new Date().toISOString()
        });
        return;
      }
    });

    // Configuration endpoint
    this.app.get('/config', (_req, res) => {
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
    this.app.get('/stats', (_req, res) => {
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
      this.app.get('/debug/config', (_req, res) => {
        res.json({
          config: configManager.getConfig(),
          featureFlags: featureFlags.getAllFlags(),
          timestamp: new Date().toISOString()
        });
      });

      this.app.post('/debug/test', async (_req, res) => {
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

    // Main landing page
    this.app.get('/', (_req, res) => {
      const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sophia AI - Intelligent Enterprise Solutions</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            text-align: center;
        }
        .hero {
            padding: 4rem 0;
        }
        h1 {
            font-size: 3.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        .subtitle {
            font-size: 1.25rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }
        .status {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2rem;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }
        .service-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 2rem;
            border-radius: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .service-card h3 {
            margin-top: 0;
            font-size: 1.5rem;
        }
        .health-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            margin-left: 0.5rem;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            opacity: 0.8;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🧠 Sophia AI</h1>
            <p class="subtitle">Intelligent Enterprise Solutions Platform</p>
            <div class="status">
                System Status: Operational
                <span class="health-indicator"></span>
            </div>
        </div>

        <div class="services">
            <div class="service-card">
                <h3>🤖 AI Coordinator</h3>
                <p>Intelligent request routing and coordination across AI agents</p>
            </div>
            <div class="service-card">
                <h3>📊 Business Intelligence</h3>
                <p>Advanced analytics and insights for sales and client management</p>
            </div>
            <div class="service-card">
                <h3>🔧 MCP Services</h3>
                <p>Multi-Context Protocol integration for external tools and platforms</p>
            </div>
            <div class="service-card">
                <h3>📈 Monitoring</h3>
                <p>Real-time system monitoring and performance analytics</p>
            </div>
        </div>

        <div class="footer">
            <p>© 2025 Sophia AI - Enterprise-grade AI solutions</p>
            <p>Status: <a href="/healthz" style="color: white; text-decoration: none;">Health Check</a> |
               <a href="/api/" style="color: white; text-decoration: none;">API Docs</a> |
               <a href="/grafana/" style="color: white; text-decoration: none;">Monitoring</a></p>
        </div>
    </div>
</body>
</html>`;
      res.setHeader('Content-Type', 'text/html');
      res.send(html);
    });

    // 404 handler
    this.app.use('*', (_req, res) => {
      res.status(404).json({
        error: 'Not found',
        path: _req.originalUrl,
        timestamp: new Date().toISOString()
      });
    });
  }

  /**
   * Set up error handling
   */
  private setupErrorHandling(): void {
    // Global error handler
    this.app.use((error: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
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