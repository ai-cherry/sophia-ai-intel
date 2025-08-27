#!/usr/bin/env python3
"""
Test script for Neon audit schema
Performs sample insertions to verify audit functionality
"""

import os
import sys
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

class AuditTester:
    """Test class for audit schema operations"""
    
    def __init__(self):
        self.neon_url = os.getenv('NEON_DATABASE_URL')
        
        if not self.neon_url:
            raise ValueError("NEON_DATABASE_URL not found in environment")
        
        logger.info("Audit tester initialized")
    
    def test_tool_invocation_insert(self) -> bool:
        """Test inserting a tool invocation record"""
        logger.info("Testing tool invocation insertion...")
        
        try:
            # Connect to Neon
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Prepare test data
            test_records = [
                {
                    'tenant': 'acme_corp',
                    'actor': 'user@example.com',
                    'service': 'slack_integration',
                    'tool': 'send_message',
                    'request': {
                        'channel': '#general',
                        'message': 'Hello from audit test',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'response': {
                        'message_id': 'msg_12345',
                        'status': 'delivered',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'purpose': 'Testing audit logging for Slack integration',
                    'duration_ms': 235,
                    'status': 'completed'
                },
                {
                    'tenant': 'techstart_inc',
                    'actor': 'bot@sophia-ai.com',
                    'service': 'gong_analyzer',
                    'tool': 'extract_transcript',
                    'request': {
                        'call_id': 'gong_67890',
                        'filters': ['action_items', 'sentiment'],
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'response': {
                        'transcript_id': 'trans_abc123',
                        'action_items': 3,
                        'sentiment_score': 0.82,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'purpose': 'Extract insights from sales call',
                    'duration_ms': 1542,
                    'status': 'completed'
                },
                {
                    'tenant': 'startup_xyz',
                    'actor': 'scheduler@system',
                    'service': 'notion_sync',
                    'tool': 'update_page',
                    'request': {
                        'page_id': 'notion_page_456',
                        'updates': {
                            'status': 'In Progress',
                            'last_modified': datetime.utcnow().isoformat()
                        }
                    },
                    'response': None,  # Simulating a pending/failed operation
                    'purpose': 'Scheduled page status update',
                    'duration_ms': None,
                    'status': 'failed',
                    'error': 'Connection timeout to Notion API'
                }
            ]
            
            inserted_ids = []
            
            for record in test_records:
                cursor.execute("""
                    INSERT INTO audit.tool_invocations 
                    (tenant, actor, service, tool, request, response, purpose, 
                     duration_ms, status, error)
                    VALUES (%(tenant)s, %(actor)s, %(service)s, %(tool)s, 
                            %(request)s::jsonb, %(response)s::jsonb, %(purpose)s, 
                            %(duration_ms)s, %(status)s, %(error)s)
                    RETURNING id, at
                """, {
                    'tenant': record['tenant'],
                    'actor': record['actor'],
                    'service': record['service'],
                    'tool': record['tool'],
                    'request': json.dumps(record['request']),
                    'response': json.dumps(record['response']) if record['response'] else None,
                    'purpose': record['purpose'],
                    'duration_ms': record['duration_ms'],
                    'status': record['status'],
                    'error': record.get('error')
                })
                
                result = cursor.fetchone()
                inserted_ids.append(result['id'])
                logger.info(f"✅ Inserted tool invocation ID {result['id']} for {record['service']}")
            
            conn.commit()
            
            # Verify insertions
            cursor.execute("""
                SELECT * FROM audit.tool_invocations 
                WHERE id = ANY(%s)
                ORDER BY id
            """, (inserted_ids,))
            
            records = cursor.fetchall()
            
            logger.info(f"\n📊 Verification: Found {len(records)} records")
            for record in records:
                logger.info(f"   ID {record['id']}: {record['service']}.{record['tool']} - {record['status']}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to test tool invocation insertion: {str(e)}")
            return False
    
    def test_service_health_insert(self) -> bool:
        """Test inserting service health records"""
        logger.info("\nTesting service health insertion...")
        
        try:
            # Connect to Neon
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Prepare test data
            health_records = [
                {
                    'service': 'neon_database',
                    'status': 'healthy',
                    'latency_ms': 45,
                    'metadata': {
                        'connections': 12,
                        'queries_per_sec': 150,
                        'cpu_percent': 23.5
                    }
                },
                {
                    'service': 'qdrant_vector_db',
                    'status': 'healthy',
                    'latency_ms': 89,
                    'metadata': {
                        'collections': 3,
                        'total_vectors': 45000,
                        'memory_usage_mb': 512
                    }
                },
                {
                    'service': 'redis_cache',
                    'status': 'degraded',
                    'latency_ms': 250,
                    'error': 'High memory usage detected',
                    'metadata': {
                        'memory_percent': 92,
                        'evicted_keys': 1500,
                        'connected_clients': 45
                    }
                },
                {
                    'service': 'openai_api',
                    'status': 'unhealthy',
                    'latency_ms': None,
                    'error': 'Rate limit exceeded',
                    'metadata': {
                        'error_code': 429,
                        'retry_after_seconds': 60
                    }
                }
            ]
            
            inserted_ids = []
            
            for record in health_records:
                cursor.execute("""
                    INSERT INTO audit.service_health 
                    (service, status, latency_ms, error, metadata)
                    VALUES (%(service)s, %(status)s, %(latency_ms)s, %(error)s, %(metadata)s::jsonb)
                    RETURNING id, checked_at
                """, {
                    'service': record['service'],
                    'status': record['status'],
                    'latency_ms': record.get('latency_ms'),
                    'error': record.get('error'),
                    'metadata': json.dumps(record.get('metadata', {}))
                })
                
                result = cursor.fetchone()
                inserted_ids.append(result['id'])
                
                status_emoji = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'unhealthy': '❌'
                }.get(record['status'], '❓')
                
                logger.info(f"{status_emoji} Inserted health check ID {result['id']} for {record['service']} - {record['status']}")
            
            conn.commit()
            
            # Query and display summary
            cursor.execute("""
                SELECT 
                    service,
                    status,
                    COUNT(*) as check_count,
                    AVG(latency_ms) as avg_latency,
                    MAX(checked_at) as last_check
                FROM audit.service_health
                WHERE id = ANY(%s)
                GROUP BY service, status
                ORDER BY service
            """, (inserted_ids,))
            
            summary = cursor.fetchall()
            
            logger.info("\n📈 Health Check Summary:")
            for row in summary:
                logger.info(f"   {row['service']}: {row['status']} (avg latency: {row['avg_latency']:.0f}ms if row['avg_latency'] else 'N/A')")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to test service health insertion: {str(e)}")
            return False
    
    def test_query_patterns(self) -> bool:
        """Test common query patterns on audit schema"""
        logger.info("\nTesting query patterns...")
        
        try:
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query 1: Recent tool invocations by tenant
            logger.info("\n1️⃣ Recent tool invocations by tenant:")
            cursor.execute("""
                SELECT 
                    tenant,
                    COUNT(*) as invocation_count,
                    COUNT(DISTINCT service) as unique_services,
                    AVG(duration_ms) as avg_duration_ms
                FROM audit.tool_invocations
                WHERE at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                GROUP BY tenant
                ORDER BY invocation_count DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            for row in results:
                logger.info(f"   {row['tenant']}: {row['invocation_count']} calls, "
                          f"{row['unique_services']} services")
            
            # Query 2: Failed operations
            logger.info("\n2️⃣ Recent failed operations:")
            cursor.execute("""
                SELECT 
                    service,
                    tool,
                    error,
                    at
                FROM audit.tool_invocations
                WHERE status = 'failed'
                ORDER BY at DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            for row in results:
                logger.info(f"   {row['service']}.{row['tool']}: {row['error']}")
            
            # Query 3: Service health trends
            logger.info("\n3️⃣ Service health status distribution:")
            cursor.execute("""
                SELECT 
                    service,
                    status,
                    COUNT(*) as count
                FROM audit.service_health
                WHERE checked_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                GROUP BY service, status
                ORDER BY service, status
            """)
            
            results = cursor.fetchall()
            for row in results:
                logger.info(f"   {row['service']} - {row['status']}: {row['count']} checks")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to test query patterns: {str(e)}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data (optional)"""
        logger.info("\nCleaning up test data...")
        
        try:
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor()
            
            # Only clean up data inserted by this test script
            cursor.execute("""
                DELETE FROM audit.tool_invocations 
                WHERE actor IN ('user@example.com', 'bot@sophia-ai.com', 'scheduler@system')
                AND at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            """)
            
            deleted_invocations = cursor.rowcount
            
            cursor.execute("""
                DELETE FROM audit.service_health 
                WHERE checked_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                AND metadata::text LIKE '%test%'
            """)
            
            deleted_health = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Cleaned up {deleted_invocations} tool invocations and {deleted_health} health records")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup test data: {str(e)}")
            return False

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Sophia AI Audit Schema Test")
    logger.info("=" * 60)
    
    try:
        tester = AuditTester()
        
        # Run tests
        results = {
            'tool_invocations': tester.test_tool_invocation_insert(),
            'service_health': tester.test_service_health_insert(),
            'query_patterns': tester.test_query_patterns()
        }
        
        # Optional: cleanup test data
        # Uncomment the next line if you want to clean up test data after running
        # results['cleanup'] = tester.cleanup_test_data()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        # Overall status
        all_success = all(results.values())
        if all_success:
            logger.info("\n🎉 All audit tests passed successfully!")
            sys.exit(0)
        else:
            logger.error("\n⚠️ Some audit tests failed. Please check the logs.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()