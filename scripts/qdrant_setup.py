#!/usr/bin/env python3
"""
Qdrant vector database collection setup script
Creates collections with 3072 dimensions for OpenAI embeddings
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, CollectionStatus
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

class QdrantSetup:
    """Setup class for Qdrant vector collections"""
    
    def __init__(self):
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        # Initialize client
        if self.qdrant_api_key:
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
            logger.info(f"Connected to Qdrant at {self.qdrant_url} with API key")
        else:
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info(f"Connected to Qdrant at {self.qdrant_url} without API key")
        
        # Define collections configuration
        self.collections_config = [
            {
                'name': 'slack_messages_vec',
                'description': 'Vector embeddings for Slack messages',
                'vector_size': 3072,  # OpenAI text-embedding-3-large dimension
                'distance': Distance.COSINE,
                'on_disk_payload': False,
                'payload_schema': {
                    'message_id': 'keyword',
                    'channel_id': 'keyword',
                    'user_id': 'keyword',
                    'timestamp': 'datetime',
                    'content': 'text',
                    'thread_ts': 'keyword',
                    'team_id': 'keyword'
                }
            },
            {
                'name': 'gong_transcripts_vec',
                'description': 'Vector embeddings for Gong call transcripts',
                'vector_size': 3072,
                'distance': Distance.COSINE,
                'on_disk_payload': False,
                'payload_schema': {
                    'call_id': 'keyword',
                    'transcript_id': 'keyword',
                    'speaker': 'keyword',
                    'timestamp': 'datetime',
                    'content': 'text',
                    'sentiment': 'float',
                    'keywords': 'keyword[]',
                    'action_items': 'text[]'
                }
            },
            {
                'name': 'notion_pages_vec',
                'description': 'Vector embeddings for Notion pages',
                'vector_size': 3072,
                'distance': Distance.COSINE,
                'on_disk_payload': False,
                'payload_schema': {
                    'page_id': 'keyword',
                    'workspace_id': 'keyword',
                    'title': 'text',
                    'content': 'text',
                    'last_edited': 'datetime',
                    'created_by': 'keyword',
                    'tags': 'keyword[]',
                    'parent_page_id': 'keyword'
                }
            }
        ]
    
    def check_collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        try:
            collections = self.client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {str(e)}")
            return False
    
    def create_collection(self, config: Dict) -> bool:
        """Create a single collection with specified configuration"""
        collection_name = config['name']
        
        try:
            # Check if collection already exists
            if self.check_collection_exists(collection_name):
                logger.warning(f"Collection '{collection_name}' already exists")
                
                # Get collection info
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"  - Status: {collection_info.status}")
                logger.info(f"  - Vectors count: {collection_info.vectors_count}")
                logger.info(f"  - Points count: {collection_info.points_count}")
                
                # Ask if we should recreate
                logger.info(f"Keeping existing collection '{collection_name}'")
                return True
            
            # Create new collection
            logger.info(f"Creating collection '{collection_name}'...")
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config['vector_size'],
                    distance=config['distance']
                ),
                on_disk_payload=config.get('on_disk_payload', False)
            )
            
            logger.info(f"✅ Collection '{collection_name}' created successfully")
            logger.info(f"  - Description: {config['description']}")
            logger.info(f"  - Vector size: {config['vector_size']}")
            logger.info(f"  - Distance metric: {config['distance']}")
            
            # Create indexes for better performance
            self.create_payload_indexes(collection_name, config.get('payload_schema', {}))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{collection_name}': {str(e)}")
            return False
    
    def create_payload_indexes(self, collection_name: str, payload_schema: Dict) -> None:
        """Create payload indexes for efficient filtering"""
        try:
            for field_name, field_type in payload_schema.items():
                if 'keyword' in field_type or field_type == 'float':
                    try:
                        self.client.create_payload_index(
                            collection_name=collection_name,
                            field_name=field_name,
                            field_schema=models.PayloadSchemaType.KEYWORD if 'keyword' in field_type else models.PayloadSchemaType.FLOAT
                        )
                        logger.info(f"  ✓ Created index for field '{field_name}'")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not create index for '{field_name}': {str(e)}")
        except Exception as e:
            logger.warning(f"Could not create payload indexes: {str(e)}")
    
    def test_collection(self, collection_name: str) -> bool:
        """Test a collection with sample data insertion and retrieval"""
        logger.info(f"\nTesting collection '{collection_name}'...")
        
        try:
            # Create test vector
            test_vector = [0.1] * 3072  # Dummy 3072-dimensional vector
            test_id = 999999999  # High ID to avoid conflicts
            
            # Create test payload based on collection type
            test_payloads = {
                'slack_messages_vec': {
                    'message_id': 'test_msg_001',
                    'channel_id': 'test_channel',
                    'user_id': 'test_user',
                    'timestamp': datetime.utcnow().isoformat(),
                    'content': 'This is a test message for Qdrant setup',
                    'team_id': 'test_team'
                },
                'gong_transcripts_vec': {
                    'call_id': 'test_call_001',
                    'transcript_id': 'test_trans_001',
                    'speaker': 'Test Speaker',
                    'timestamp': datetime.utcnow().isoformat(),
                    'content': 'This is a test transcript segment',
                    'sentiment': 0.85,
                    'keywords': ['test', 'qdrant', 'setup']
                },
                'notion_pages_vec': {
                    'page_id': 'test_page_001',
                    'workspace_id': 'test_workspace',
                    'title': 'Test Page',
                    'content': 'This is test content for Notion page',
                    'last_edited': datetime.utcnow().isoformat(),
                    'created_by': 'test_user',
                    'tags': ['test', 'setup']
                }
            }
            
            test_payload = test_payloads.get(collection_name, {
                'test': True,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Insert test point
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=test_id,
                        vector=test_vector,
                        payload=test_payload
                    )
                ]
            )
            logger.info(f"  ✓ Test point inserted (ID: {test_id})")
            
            # Search for similar vectors
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=test_vector,
                limit=1
            )
            
            if search_results:
                logger.info(f"  ✓ Search successful - found {len(search_results)} results")
                logger.info(f"    Score: {search_results[0].score}")
            
            # Clean up test data
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[test_id])
            )
            logger.info(f"  ✓ Test data cleaned up")
            
            logger.info(f"✅ Collection '{collection_name}' test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Collection test failed: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics for all collections"""
        stats = {}
        
        try:
            collections = self.client.get_collections()
            
            for collection in collections.collections:
                try:
                    info = self.client.get_collection(collection.name)
                    stats[collection.name] = {
                        'status': str(info.status),
                        'vectors_count': info.vectors_count,
                        'points_count': info.points_count,
                        'segments_count': info.segments_count,
                        'config': {
                            'vector_size': info.config.params.vectors.size,
                            'distance': str(info.config.params.vectors.distance)
                        }
                    }
                except Exception as e:
                    logger.warning(f"Could not get stats for {collection.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            
        return stats
    
    def run(self) -> bool:
        """Run the complete Qdrant setup"""
        logger.info("=" * 60)
        logger.info("Starting Qdrant Collection Setup")
        logger.info("=" * 60)
        
        success_count = 0
        failed_count = 0
        
        # Create each collection
        for config in self.collections_config:
            if self.create_collection(config):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info("Collection Creation Summary")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {failed_count}")
        
        # Test collections
        logger.info("\n" + "=" * 60)
        logger.info("Testing Collections")
        logger.info("=" * 60)
        
        test_results = []
        for config in self.collections_config:
            test_passed = self.test_collection(config['name'])
            test_results.append(test_passed)
        
        # Display statistics
        logger.info("\n" + "=" * 60)
        logger.info("Collection Statistics")
        logger.info("=" * 60)
        
        stats = self.get_collection_stats()
        for collection_name, collection_stats in stats.items():
            logger.info(f"\n{collection_name}:")
            logger.info(f"  Status: {collection_stats['status']}")
            logger.info(f"  Points: {collection_stats['points_count']}")
            logger.info(f"  Vectors: {collection_stats['vectors_count']}")
            logger.info(f"  Vector size: {collection_stats['config']['vector_size']}")
            logger.info(f"  Distance: {collection_stats['config']['distance']}")
        
        # Overall status
        all_success = failed_count == 0 and all(test_results)
        
        logger.info("\n" + "=" * 60)
        if all_success:
            logger.info("🎉 Qdrant setup completed successfully!")
            logger.info("All collections are ready for use.")
        else:
            logger.warning("⚠️ Qdrant setup completed with some issues.")
            logger.warning("Please check the logs for details.")
        logger.info("=" * 60)
        
        return all_success

def main():
    """Main entry point"""
    try:
        setup = QdrantSetup()
        success = setup.run()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()