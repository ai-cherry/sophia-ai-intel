#!/usr/bin/env python3
"""
Database initialization script for Sophia AI platform
Initializes Neon, Qdrant, and Redis infrastructure
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.http import models
import redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

class DatabaseInitializer:
    """Main class for initializing all database infrastructure"""
    
    def __init__(self):
        self.neon_url = os.getenv('NEON_DATABASE_URL')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Validate required credentials
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL not found in environment")
        
        logger.info("Database credentials loaded successfully")
    
    def init_neon(self) -> bool:
        """Initialize Neon database with audit schema"""
        logger.info("Initializing Neon database...")
        
        try:
            # Connect to Neon
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor()
            
            # Read and execute the audit schema SQL
            sql_file_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'ops', 'sql', '001_audit.sql'
            )
            
            if os.path.exists(sql_file_path):
                with open(sql_file_path, 'r') as f:
                    sql_content = f.read()
                    
                # Execute the SQL statements
                cursor.execute(sql_content)
                conn.commit()
                logger.info("✅ Audit schema created successfully")
            else:
                logger.warning(f"SQL file not found: {sql_file_path}")
                # Create schema directly
                sql_statements = [
                    "CREATE SCHEMA IF NOT EXISTS audit",
                    """
                    CREATE TABLE IF NOT EXISTS audit.tool_invocations (
                        id SERIAL PRIMARY KEY,
                        tenant VARCHAR(255) NOT NULL,
                        actor VARCHAR(255) NOT NULL,
                        service VARCHAR(255) NOT NULL,
                        tool VARCHAR(255) NOT NULL,
                        request JSONB NOT NULL,
                        response JSONB,
                        purpose TEXT,
                        duration_ms INTEGER,
                        status VARCHAR(50) DEFAULT 'pending',
                        error TEXT,
                        at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_tool_invocations_tenant ON audit.tool_invocations(tenant)",
                    "CREATE INDEX IF NOT EXISTS idx_tool_invocations_actor ON audit.tool_invocations(actor)",
                    "CREATE INDEX IF NOT EXISTS idx_tool_invocations_service ON audit.tool_invocations(service)",
                    "CREATE INDEX IF NOT EXISTS idx_tool_invocations_at ON audit.tool_invocations(at DESC)",
                    """
                    CREATE TABLE IF NOT EXISTS audit.service_health (
                        id SERIAL PRIMARY KEY,
                        service VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        latency_ms INTEGER,
                        error TEXT,
                        metadata JSONB,
                        checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_service_health_service ON audit.service_health(service, checked_at DESC)"
                ]
                
                for stmt in sql_statements:
                    cursor.execute(stmt)
                conn.commit()
                logger.info("✅ Audit schema created directly")
            
            # Test insertion to verify connectivity
            test_data = {
                'tenant': 'test',
                'actor': 'init_script',
                'service': 'database_init',
                'tool': 'neon_test',
                'request': json.dumps({'action': 'test_connectivity'}),
                'response': json.dumps({'status': 'success'}),
                'purpose': 'Database initialization test',
                'duration_ms': 100,
                'status': 'completed'
            }
            
            cursor.execute("""
                INSERT INTO audit.tool_invocations 
                (tenant, actor, service, tool, request, response, purpose, duration_ms, status)
                VALUES (%(tenant)s, %(actor)s, %(service)s, %(tool)s, %(request)s::jsonb, 
                        %(response)s::jsonb, %(purpose)s, %(duration_ms)s, %(status)s)
                RETURNING id
            """, test_data)
            
            test_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"✅ Test insertion successful (ID: {test_id})")
            
            # Clean up test data
            cursor.execute("DELETE FROM audit.tool_invocations WHERE id = %s", (test_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Neon database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Neon: {str(e)}")
            return False
    
    def init_qdrant(self) -> bool:
        """Initialize Qdrant vector collections"""
        logger.info("Initializing Qdrant collections...")
        
        try:
            # Connect to Qdrant
            if self.qdrant_api_key:
                client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
            else:
                client = QdrantClient(url=self.qdrant_url)
            
            # Define collections with 3072 dimensions (OpenAI embedding size)
            collections = [
                'slack_messages_vec',
                'gong_transcripts_vec',
                'notion_pages_vec'
            ]
            
            for collection_name in collections:
                try:
                    # Check if collection exists
                    collections_list = client.get_collections()
                    exists = any(c.name == collection_name for c in collections_list.collections)
                    
                    if not exists:
                        # Create collection
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=models.VectorParams(
                                size=3072,  # OpenAI text-embedding-3-large dimension
                                distance=models.Distance.COSINE
                            )
                        )
                        logger.info(f"✅ Created collection: {collection_name}")
                    else:
                        logger.info(f"ℹ️ Collection already exists: {collection_name}")
                    
                    # Test insertion to verify connectivity
                    test_point = models.PointStruct(
                        id=999999,
                        vector=[0.1] * 3072,  # Dummy vector
                        payload={
                            "test": True,
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "init_script"
                        }
                    )
                    
                    client.upsert(
                        collection_name=collection_name,
                        points=[test_point]
                    )
                    logger.info(f"✅ Test insertion successful for {collection_name}")
                    
                    # Clean up test data
                    client.delete(
                        collection_name=collection_name,
                        points_selector=models.PointIdsList(
                            points=[999999]
                        )
                    )
                    logger.info(f"✅ Test data cleaned up for {collection_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to initialize collection {collection_name}: {str(e)}")
                    return False
            
            logger.info("✅ Qdrant collections initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {str(e)}")
            return False
    
    def init_redis(self) -> bool:
        """Test Redis connectivity and basic operations"""
        logger.info("Testing Redis connectivity...")
        
        try:
            # Parse Redis URL
            if self.redis_url.startswith('redis://'):
                redis_client = redis.from_url(self.redis_url)
            else:
                redis_client = redis.Redis(host='localhost', port=6379, db=0)
            
            # Test basic operations
            test_key = 'sophia:test:init'
            test_value = {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'init_script',
                'status': 'testing'
            }
            
            # Set with expiry (60 seconds)
            redis_client.setex(
                test_key, 
                60, 
                json.dumps(test_value)
            )
            logger.info(f"✅ Redis SET operation successful")
            
            # Get operation
            retrieved = redis_client.get(test_key)
            if retrieved:
                retrieved_value = json.loads(retrieved)
                logger.info(f"✅ Redis GET operation successful: {retrieved_value}")
            
            # Test list operations
            list_key = 'sophia:test:list'
            redis_client.lpush(list_key, 'item1', 'item2', 'item3')
            redis_client.expire(list_key, 60)
            
            list_items = redis_client.lrange(list_key, 0, -1)
            logger.info(f"✅ Redis LIST operations successful: {len(list_items)} items")
            
            # Test hash operations
            hash_key = 'sophia:test:hash'
            redis_client.hset(hash_key, mapping={
                'field1': 'value1',
                'field2': 'value2',
                'timestamp': datetime.utcnow().isoformat()
            })
            redis_client.expire(hash_key, 60)
            
            hash_data = redis_client.hgetall(hash_key)
            logger.info(f"✅ Redis HASH operations successful: {len(hash_data)} fields")
            
            # Clean up test data
            redis_client.delete(test_key, list_key, hash_key)
            logger.info("✅ Redis test data cleaned up")
            
            # Get Redis info
            info = redis_client.info()
            logger.info(f"✅ Redis server info - Version: {info.get('redis_version', 'unknown')}, "
                       f"Used memory: {info.get('used_memory_human', 'unknown')}")
            
            logger.info("✅ Redis connectivity test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {str(e)}")
            return False
    
    def run(self) -> Dict[str, bool]:
        """Run all database initializations"""
        results = {}
        
        # Initialize Neon
        results['neon'] = self.init_neon()
        
        # Initialize Qdrant
        results['qdrant'] = self.init_qdrant()
        
        # Initialize Redis
        results['redis'] = self.init_redis()
        
        return results

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Sophia AI Database Initialization")
    logger.info("=" * 60)
    
    try:
        initializer = DatabaseInitializer()
        results = initializer.run()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("INITIALIZATION SUMMARY")
        logger.info("=" * 60)
        
        for service, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{service.upper()}: {status}")
        
        # Overall status
        all_success = all(results.values())
        if all_success:
            logger.info("\n🎉 All databases initialized successfully!")
            sys.exit(0)
        else:
            logger.error("\n⚠️ Some databases failed to initialize. Please check the logs.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()