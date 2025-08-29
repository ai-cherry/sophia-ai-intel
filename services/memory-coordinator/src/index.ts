import Fastify from 'fastify';
import cors from '@fastify/cors';
import websocket from '@fastify/websocket';
import { MemoryCoordinator } from './coordinator';
import { HybridVectorStore } from './hybrid-store';
import { healthRoutes } from './routes/health';
import { memoryRoutes } from './routes/memory';
import { searchRoutes } from './routes/search';
import { logger } from './utils/logger';

const PORT = parseInt(process.env.PORT || '8090', 10);
const HOST = process.env.HOST || '0.0.0.0';

async function start() {
  const fastify = Fastify({
    logger: logger,
    requestIdHeader: 'x-request-id',
    requestIdLogLabel: 'requestId',
  });

  // Register plugins
  await fastify.register(cors, {
    origin: process.env.CORS_ORIGIN || true,
    credentials: true,
  });
  
  await fastify.register(websocket);

  // Initialize services
  const vectorStore = new HybridVectorStore();
  await vectorStore.initialize();
  
  const coordinator = new MemoryCoordinator(vectorStore);
  await coordinator.initialize();

  // Decorate fastify with services
  fastify.decorate('memory', coordinator);
  fastify.decorate('vectorStore', vectorStore);

  // Register routes
  await fastify.register(healthRoutes);
  await fastify.register(memoryRoutes);
  await fastify.register(searchRoutes);

  // WebSocket handler for real-time updates
  fastify.register(async function (fastify) {
    fastify.get('/ws', { websocket: true }, (connection, req) => {
      connection.socket.on('message', async (message) => {
        try {
          const data = JSON.parse(message.toString());
          
          switch (data.type) {
            case 'subscribe':
              coordinator.subscribe(data.sessionId, connection.socket);
              break;
            case 'unsubscribe':
              coordinator.unsubscribe(data.sessionId);
              break;
            case 'search':
              const results = await coordinator.search(data.query, data.sessionId);
              connection.socket.send(JSON.stringify({
                type: 'search_results',
                results,
              }));
              break;
          }
        } catch (error) {
          logger.error({ error }, 'WebSocket message error');
          connection.socket.send(JSON.stringify({
            type: 'error',
            message: 'Invalid message format',
          }));
        }
      });

      connection.socket.on('close', () => {
        coordinator.cleanup(connection.socket);
      });
    });
  });

  // Graceful shutdown
  const gracefulShutdown = async (signal: string) => {
    logger.info({ signal }, 'Shutting down gracefully');
    await fastify.close();
    await coordinator.shutdown();
    await vectorStore.shutdown();
    process.exit(0);
  };

  process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
  process.on('SIGINT', () => gracefulShutdown('SIGINT'));

  // Start server
  try {
    await fastify.listen({ port: PORT, host: HOST });
    logger.info(`Memory Coordinator running on http://${HOST}:${PORT}`);
  } catch (err) {
    logger.error(err, 'Failed to start server');
    process.exit(1);
  }
}

start().catch((error) => {
  logger.error(error, 'Startup error');
  process.exit(1);
});