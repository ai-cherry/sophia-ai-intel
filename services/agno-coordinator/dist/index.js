"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
require('dotenv').config();
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const helmet_1 = __importDefault(require("helmet"));
const compression_1 = __importDefault(require("compression"));
const codingSwarm = __importStar(require("./swarms/coding_swarm"));
const researchSwarm = __importStar(require("./swarms/research_swarm"));
const biSwarm = __importStar(require("./swarms/bi_swarm"));
const coordinator_1 = require("./coordinator/coordinator");
const healthChecker_1 = require("./health/healthChecker");
const config_1 = require("./config/config");
const featureFlags_1 = require("./config/featureFlags");
class Server {
    constructor(port = 3001) {
        this.port = port;
        this.app = (0, express_1.default)();
        this.configureMiddleware();
        this.setupRoutes();
        this.setupErrorHandling();
    }
    configureMiddleware() {
        this.app.use((0, helmet_1.default)({
            contentSecurityPolicy: false,
            crossOriginEmbedderPolicy: false
        }));
        this.app.use((0, cors_1.default)({
            origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
            credentials: true,
            methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
        }));
        this.app.use((0, compression_1.default)());
        this.app.use(express_1.default.json({ limit: '10mb' }));
        this.app.use(express_1.default.urlencoded({ extended: true, limit: '10mb' }));
        this.app.use((_req, res, next) => {
            const start = Date.now();
            res.on('finish', () => {
                const duration = Date.now() - start;
                console.log(`${new Date().toISOString()} - ${_req.method} ${_req.path} - ${res.statusCode} - ${duration}ms`);
            });
            next();
        });
    }
    setupRoutes() {
        this.app.get('/healthz', async (_req, res) => {
            try {
                const healthChecker = new healthChecker_1.HealthChecker();
                const health = await healthChecker.getHealthStatus();
                const statusCode = health.status === 'healthy' ? 200 : 503;
                res.status(statusCode).json(health);
            }
            catch (error) {
                res.status(503).json({
                    service: 'agno-coordinator',
                    status: 'unhealthy',
                    error: error instanceof Error ? error.message : 'Health check failed',
                    timestamp: new Date().toISOString()
                });
            }
        });
        this.app.get('/health/detailed', async (_req, res) => {
            try {
                const healthChecker = new healthChecker_1.HealthChecker();
                const report = await healthChecker.getDetailedHealthReport();
                const statusCode = report.status.status === 'healthy' ? 200 : 503;
                res.status(statusCode).json(report);
            }
            catch (error) {
                res.status(503).json({
                    error: error instanceof Error ? error.message : 'Detailed health check failed',
                    timestamp: new Date().toISOString()
                });
            }
        });
        this.app.post('/route', async (req, res) => {
            try {
                const request = req.body;
                if (!request || !request.userPrompt) {
                    return res.status(400).json({
                        error: 'Invalid request: userPrompt is required',
                        timestamp: new Date().toISOString()
                    });
                }
                const result = await coordinator_1.agnosticCoordinator.routeRequest(request);
                res.json(result);
                return;
            }
            catch (error) {
                console.error('Request routing error:', error);
                res.status(500).json({
                    error: 'Internal server error',
                    message: error instanceof Error ? error.message : 'Unknown error',
                    timestamp: new Date().toISOString()
                });
                return;
            }
        });
        this.app.get('/flags', (_req, res) => {
            try {
                const flags = featureFlags_1.featureFlags.getAllFlags();
                res.json({
                    flags,
                    timestamp: new Date().toISOString()
                });
            }
            catch (error) {
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
                featureFlags_1.featureFlags.setFlag(flag, enabled);
                res.json({
                    flag,
                    enabled,
                    timestamp: new Date().toISOString()
                });
                return;
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to update feature flag',
                    timestamp: new Date().toISOString()
                });
                return;
            }
        });
        this.app.get('/config', (_req, res) => {
            try {
                const config = config_1.configManager.getConfigSummary();
                res.json({
                    config,
                    timestamp: new Date().toISOString()
                });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to get configuration',
                    timestamp: new Date().toISOString()
                });
            }
        });
        this.app.get('/stats', (_req, res) => {
            try {
                const stats = coordinator_1.agnosticCoordinator.getStatistics();
                res.json({
                    stats,
                    timestamp: new Date().toISOString()
                });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to get statistics',
                    timestamp: new Date().toISOString()
                });
            }
        });
        this.app.post('/api/v1/swarms/invoke', async (req, res) => {
            try {
                const { swarm, task } = req.body;
                if (!swarm || !task) {
                    return res.status(400).json({
                        error: 'Invalid request: swarm and task are required',
                        timestamp: new Date().toISOString()
                    });
                }
                let result;
                switch (swarm) {
                    case 'coding':
                        result = await codingSwarm.run(task);
                        break;
                    case 'research':
                        result = await researchSwarm.run(task);
                        break;
                    case 'bi':
                        result = await biSwarm.run(task);
                        break;
                    default:
                        return res.status(400).json({
                            error: `Invalid swarm: ${swarm}`,
                            timestamp: new Date().toISOString()
                        });
                }
                res.json({
                    swarm,
                    task,
                    result,
                    timestamp: new Date().toISOString()
                });
                return;
            }
            catch (error) {
                console.error('Swarm invocation error:', error);
                res.status(500).json({
                    error: 'Internal server error during swarm invocation',
                    message: error instanceof Error ? error.message : 'Unknown error',
                    timestamp: new Date().toISOString()
                });
                return;
            }
        });
        if (process.env.NODE_ENV !== 'production') {
            this.app.get('/debug/config', (_req, res) => {
                res.json({
                    config: config_1.configManager.getConfig(),
                    featureFlags: featureFlags_1.featureFlags.getAllFlags(),
                    timestamp: new Date().toISOString()
                });
            });
            this.app.post('/debug/test', async (_req, res) => {
                try {
                    const testRequest = {
                        userPrompt: 'This is a test request for debugging',
                        sessionId: 'test-session',
                        userId: 'test-user'
                    };
                    const result = await coordinator_1.agnosticCoordinator.routeRequest(testRequest);
                    res.json({
                        test: 'successful',
                        result,
                        timestamp: new Date().toISOString()
                    });
                }
                catch (error) {
                    res.status(500).json({
                        test: 'failed',
                        error: error instanceof Error ? error.message : 'Unknown error',
                        timestamp: new Date().toISOString()
                    });
                }
            });
        }
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
        this.app.use('*', (_req, res) => {
            res.status(404).json({
                error: 'Not found',
                path: _req.originalUrl,
                timestamp: new Date().toISOString()
            });
        });
    }
    setupErrorHandling() {
        this.app.use((error, _req, res, _next) => {
            console.error('Unhandled error:', error);
            res.status(500).json({
                error: 'Internal server error',
                message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
                timestamp: new Date().toISOString()
            });
        });
        process.on('uncaughtException', (error) => {
            console.error('Uncaught Exception:', error);
            process.exit(1);
        });
        process.on('unhandledRejection', (reason, promise) => {
            console.error('Unhandled Rejection at:', promise, 'reason:', reason);
            process.exit(1);
        });
    }
    async start() {
        try {
            await coordinator_1.agnosticCoordinator.initialize();
            this.app.listen(this.port, () => {
                console.log(`🚀 AGNO Coordinator Service listening on port ${this.port}`);
                console.log(`📊 Health check available at: http://localhost:${this.port}/healthz`);
                console.log(`🔧 Configuration:`, config_1.configManager.getConfigSummary());
                console.log(`🏷️  Feature flags:`, featureFlags_1.featureFlags.getAllFlags());
            });
        }
        catch (error) {
            console.error('Failed to start server:', error);
            process.exit(1);
        }
    }
    async stop() {
        console.log('Stopping AGNO Coordinator Service...');
        try {
            await coordinator_1.agnosticCoordinator.shutdown();
            console.log('✅ Server stopped successfully');
        }
        catch (error) {
            console.error('Error during shutdown:', error);
        }
    }
    getApp() {
        return this.app;
    }
}
const server = new Server();
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
server.start().catch((error) => {
    console.error('Failed to start server:', error);
    process.exit(1);
});
exports.default = server;
//# sourceMappingURL=index.js.map