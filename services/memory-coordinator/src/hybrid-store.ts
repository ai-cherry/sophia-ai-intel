import { QdrantClient } from '@qdrant/js-client-rest';
import { Pool } from 'pg';
import Redis from 'ioredis';
import weaviate, { WeaviateClient } from 'weaviate-ts-client';
import { pipeline } from '@xenova/transformers';
import crypto from 'crypto';
import { logger } from './utils/logger';

export interface MemoryChunk {
  id: string;
  content: string;
  embedding: number[];
  metadata: Record<string, any>;
  sourceType: string;
  timestamp: Date;
}

export interface SearchResult {
  id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  source: string;
}

export class HybridVectorStore {
  private qdrant: QdrantClient;
  private weaviate: WeaviateClient;
  private postgres: Pool;
  private redis: Redis;
  private embedder: any;
  private initialized = false;

  constructor() {
    // Initialize Qdrant
    this.qdrant = new QdrantClient({
      url: process.env.QDRANT_URL || 'http://localhost:6333',
      apiKey: process.env.QDRANT_API_KEY,
    });

    // Initialize Weaviate
    this.weaviate = weaviate.client({
      scheme: process.env.WEAVIATE_SCHEME || 'http',
      host: process.env.WEAVIATE_HOST || 'localhost:8080',
      apiKey: process.env.WEAVIATE_API_KEY ? 
        new weaviate.ApiKey(process.env.WEAVIATE_API_KEY) : undefined,
    });

    // Initialize PostgreSQL
    this.postgres = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Initialize Redis
    this.redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379', {
      maxRetriesPerRequest: 3,
      retryStrategy: (times) => Math.min(times * 50, 2000),
    });
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Initialize embedding model
      this.embedder = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');

      // Create PostgreSQL tables
      await this.createPostgresTables();

      // Create Qdrant collection
      await this.createQdrantCollection();

      // Create Weaviate schema
      await this.createWeaviateSchema();

      this.initialized = true;
      logger.info('HybridVectorStore initialized successfully');
    } catch (error) {
      logger.error({ error }, 'Failed to initialize HybridVectorStore');
      throw error;
    }
  }

  private async createPostgresTables(): Promise<void> {
    const client = await this.postgres.connect();
    try {
      await client.query(`
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS memory_chunks (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          content TEXT NOT NULL,
          content_hash VARCHAR(64) NOT NULL,
          embedding vector(384),
          metadata JSONB DEFAULT '{}',
          source_type VARCHAR(50) DEFAULT 'general',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          access_count INTEGER DEFAULT 0,
          last_accessed TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_memory_hash ON memory_chunks(content_hash);
        CREATE INDEX IF NOT EXISTS idx_memory_source ON memory_chunks(source_type);
        CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_chunks(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_memory_metadata ON memory_chunks USING gin(metadata);
        CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_chunks USING ivfflat (embedding vector_cosine_ops);
      `);
      
      logger.info('PostgreSQL tables created successfully');
    } finally {
      client.release();
    }
  }

  private async createQdrantCollection(): Promise<void> {
    const collections = await this.qdrant.getCollections();
    const collectionExists = collections.collections.some(c => c.name === 'sophia_memory');

    if (!collectionExists) {
      await this.qdrant.createCollection('sophia_memory', {
        vectors: {
          size: 384,
          distance: 'Cosine',
        },
        optimizers_config: {
          default_segment_number: 2,
        },
        replication_factor: 2,
      });
      
      logger.info('Qdrant collection created successfully');
    }
  }

  private async createWeaviateSchema(): Promise<void> {
    try {
      const schema = await this.weaviate.schema.getter().do();
      const classExists = schema.classes?.some(c => c.class === 'MemoryChunk');

      if (!classExists) {
        await this.weaviate.schema.classCreator().withClass({
          class: 'MemoryChunk',
          description: 'Sophia AI memory chunks',
          vectorizer: 'text2vec-transformers',
          properties: [
            {
              name: 'content',
              dataType: ['text'],
              description: 'The content of the memory chunk',
            },
            {
              name: 'sourceType',
              dataType: ['string'],
              description: 'The source type of the memory',
            },
            {
              name: 'metadata',
              dataType: ['string'],
              description: 'JSON metadata',
            },
            {
              name: 'timestamp',
              dataType: ['date'],
              description: 'Creation timestamp',
            },
          ],
        }).do();
        
        logger.info('Weaviate schema created successfully');
      }
    } catch (error) {
      logger.warn({ error }, 'Weaviate schema creation failed (may not be available)');
    }
  }

  async store(content: string, metadata: Record<string, any> = {}, sourceType: string = 'general'): Promise<string> {
    await this.initialize();

    // Generate content hash for deduplication
    const contentHash = crypto.createHash('sha256').update(content).digest('hex');

    // Check for duplicates
    const existing = await this.checkDuplicate(contentHash);
    if (existing) {
      logger.debug({ id: existing }, 'Duplicate content detected, returning existing ID');
      await this.updateAccessCount(existing);
      return existing;
    }

    // Generate embedding
    const output = await this.embedder(content, { pooling: 'mean', normalize: true });
    const embedding = Array.from(output.data);

    // Generate ID
    const id = crypto.randomUUID();
    const timestamp = new Date();

    // Store in all systems in parallel
    await Promise.allSettled([
      this.storeInPostgres(id, content, contentHash, embedding, metadata, sourceType, timestamp),
      this.storeInQdrant(id, content, embedding, metadata, sourceType, timestamp),
      this.storeInWeaviate(id, content, metadata, sourceType, timestamp),
      this.cacheInRedis(id, content, metadata),
    ]);

    logger.info({ id, sourceType }, 'Memory chunk stored successfully');
    return id;
  }

  private async checkDuplicate(contentHash: string): Promise<string | null> {
    const client = await this.postgres.connect();
    try {
      const result = await client.query(
        'SELECT id FROM memory_chunks WHERE content_hash = $1 LIMIT 1',
        [contentHash]
      );
      return result.rows[0]?.id || null;
    } finally {
      client.release();
    }
  }

  private async updateAccessCount(id: string): Promise<void> {
    const client = await this.postgres.connect();
    try {
      await client.query(
        'UPDATE memory_chunks SET access_count = access_count + 1, last_accessed = NOW() WHERE id = $1',
        [id]
      );
    } finally {
      client.release();
    }
  }

  private async storeInPostgres(
    id: string,
    content: string,
    contentHash: string,
    embedding: number[],
    metadata: Record<string, any>,
    sourceType: string,
    timestamp: Date
  ): Promise<void> {
    const client = await this.postgres.connect();
    try {
      await client.query(
        `INSERT INTO memory_chunks (id, content, content_hash, embedding, metadata, source_type, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [id, content, contentHash, JSON.stringify(embedding), metadata, sourceType, timestamp]
      );
    } catch (error) {
      logger.error({ error, id }, 'Failed to store in PostgreSQL');
    } finally {
      client.release();
    }
  }

  private async storeInQdrant(
    id: string,
    content: string,
    embedding: number[],
    metadata: Record<string, any>,
    sourceType: string,
    timestamp: Date
  ): Promise<void> {
    try {
      await this.qdrant.upsert('sophia_memory', {
        points: [
          {
            id,
            vector: embedding,
            payload: {
              content,
              metadata,
              sourceType,
              timestamp: timestamp.toISOString(),
            },
          },
        ],
      });
    } catch (error) {
      logger.error({ error, id }, 'Failed to store in Qdrant');
    }
  }

  private async storeInWeaviate(
    id: string,
    content: string,
    metadata: Record<string, any>,
    sourceType: string,
    timestamp: Date
  ): Promise<void> {
    try {
      await this.weaviate.data
        .creator()
        .withClassName('MemoryChunk')
        .withId(id)
        .withProperties({
          content,
          sourceType,
          metadata: JSON.stringify(metadata),
          timestamp: timestamp.toISOString(),
        })
        .do();
    } catch (error) {
      logger.warn({ error, id }, 'Failed to store in Weaviate');
    }
  }

  private async cacheInRedis(
    id: string,
    content: string,
    metadata: Record<string, any>
  ): Promise<void> {
    try {
      const cacheData = JSON.stringify({ id, content, metadata });
      await this.redis.setex(`memory:${id}`, 3600, cacheData); // 1 hour TTL
    } catch (error) {
      logger.warn({ error, id }, 'Failed to cache in Redis');
    }
  }

  async search(
    query: string,
    filters: Record<string, any> = {},
    limit: number = 10
  ): Promise<SearchResult[]> {
    await this.initialize();

    // Generate query embedding
    const output = await this.embedder(query, { pooling: 'mean', normalize: true });
    const embedding = Array.from(output.data);

    // Search in parallel
    const [qdrantResults, postgresResults, weaviateResults] = await Promise.allSettled([
      this.searchQdrant(embedding, filters, limit * 2),
      this.searchPostgres(embedding, filters, limit * 2),
      this.searchWeaviate(query, filters, limit * 2),
    ]);

    // Merge and deduplicate results
    const allResults: SearchResult[] = [];
    
    if (qdrantResults.status === 'fulfilled') {
      allResults.push(...qdrantResults.value);
    }
    
    if (postgresResults.status === 'fulfilled') {
      allResults.push(...postgresResults.value);
    }
    
    if (weaviateResults.status === 'fulfilled') {
      allResults.push(...weaviateResults.value);
    }

    // Deduplicate by ID and sort by score
    const uniqueResults = this.deduplicateResults(allResults);
    const sortedResults = uniqueResults.sort((a, b) => b.score - a.score);

    // Cache results
    const cacheKey = `search:${crypto.createHash('md5').update(query + JSON.stringify(filters)).digest('hex')}`;
    await this.redis.setex(cacheKey, 300, JSON.stringify(sortedResults.slice(0, limit)));

    return sortedResults.slice(0, limit);
  }

  private async searchQdrant(
    embedding: number[],
    filters: Record<string, any>,
    limit: number
  ): Promise<SearchResult[]> {
    try {
      const searchResult = await this.qdrant.search('sophia_memory', {
        vector: embedding,
        limit,
        filter: filters.sourceType ? {
          must: [{ key: 'sourceType', match: { value: filters.sourceType } }],
        } : undefined,
      });

      return searchResult.map(result => ({
        id: result.id as string,
        content: result.payload?.content as string,
        score: result.score || 0,
        metadata: result.payload?.metadata as Record<string, any>,
        source: 'qdrant',
      }));
    } catch (error) {
      logger.error({ error }, 'Qdrant search failed');
      return [];
    }
  }

  private async searchPostgres(
    embedding: number[],
    filters: Record<string, any>,
    limit: number
  ): Promise<SearchResult[]> {
    const client = await this.postgres.connect();
    try {
      let query = `
        SELECT id, content, metadata,
               1 - (embedding <=> $1::vector) as score
        FROM memory_chunks
        WHERE 1=1
      `;
      
      const params: any[] = [JSON.stringify(embedding)];
      let paramIndex = 2;

      if (filters.sourceType) {
        query += ` AND source_type = $${paramIndex}`;
        params.push(filters.sourceType);
        paramIndex++;
      }

      query += ` ORDER BY score DESC LIMIT $${paramIndex}`;
      params.push(limit);

      const result = await client.query(query, params);

      return result.rows.map(row => ({
        id: row.id,
        content: row.content,
        score: row.score,
        metadata: row.metadata,
        source: 'postgres',
      }));
    } catch (error) {
      logger.error({ error }, 'PostgreSQL search failed');
      return [];
    } finally {
      client.release();
    }
  }

  private async searchWeaviate(
    query: string,
    filters: Record<string, any>,
    limit: number
  ): Promise<SearchResult[]> {
    try {
      const result = await this.weaviate.graphql
        .get()
        .withClassName('MemoryChunk')
        .withFields('content sourceType metadata _additional { id distance }')
        .withNearText({ concepts: [query] })
        .withLimit(limit)
        .do();

      if (!result.data?.Get?.MemoryChunk) {
        return [];
      }

      return result.data.Get.MemoryChunk.map((chunk: any) => ({
        id: chunk._additional.id,
        content: chunk.content,
        score: 1 - (chunk._additional.distance || 0),
        metadata: JSON.parse(chunk.metadata || '{}'),
        source: 'weaviate',
      }));
    } catch (error) {
      logger.warn({ error }, 'Weaviate search failed');
      return [];
    }
  }

  private deduplicateResults(results: SearchResult[]): SearchResult[] {
    const seen = new Map<string, SearchResult>();
    
    for (const result of results) {
      const existing = seen.get(result.id);
      if (!existing || result.score > existing.score) {
        seen.set(result.id, result);
      }
    }
    
    return Array.from(seen.values());
  }

  async shutdown(): Promise<void> {
    await this.postgres.end();
    this.redis.disconnect();
    logger.info('HybridVectorStore shut down');
  }
}