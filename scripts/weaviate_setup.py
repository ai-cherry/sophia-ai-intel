#!/usr/bin/env python3
"""
Weaviate vector database collection setup script
Creates collections for document embeddings and vector search
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes as wvc
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

class WeaviateSetup:
    """Setup class for Weaviate vector collections"""
    
    def __init__(self):
        self.weaviate_url = os.getenv('WEAVIATE_URL', '')
        self.weaviate_api_key = os.getenv('WEAVIATE_API_KEY', '')
        
        if not self.weaviate_url or not self.weaviate_api_key:
            raise ValueError("WEAVIATE_URL and WEAVIATE_API_KEY must be set in environment")
        
        # Initialize client
        self.client = weaviate.connect_to_wcs(
            cluster_url=self.weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(self.weaviate_api_key)
        )
        logger.info(f"Connected to Weaviate at {self.weaviate_url}")
        
        # Define collections configuration
        self.collections_config = [
            {
                'name': 'SlackMessages',
                'description': 'Vector embeddings for Slack messages',
                'properties': [
                    wvc.config.Property(name="message_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="channel_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="user_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="thread_ts", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="team_id", data_type=wvc.config.DataType.TEXT)
                ]
            },
            {
                'name': 'GongTranscripts', 
                'description': 'Vector embeddings for Gong call transcripts',
                'properties': [
                    wvc.config.Property(name="call_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="transcript_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="speaker", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="sentiment", data_type=wvc.config.DataType.NUMBER),
                    wvc.config.Property(name="keywords", data_type=wvc.config.DataType.TEXT_ARRAY),
                    wvc.config.Property(name="action_items", data_type=wvc.config.DataType.TEXT_ARRAY)
                ]
            },
            {
                'name': 'NotionPages',
                'description': 'Vector embeddings for Notion pages',
                'properties': [
                    wvc.config.Property(name="page_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="workspace_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="last_edited", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="created_by", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="tags", data_type=wvc.config.DataType.TEXT_ARRAY),
                    wvc.config.Property(name="parent_page_id", data_type=wvc.config.DataType.TEXT)
                ]
            },
            {
                'name': 'SophiaKnowledgeBase',
                'description': 'Main knowledge base for Sophia AI platform',
                'properties': [
                    wvc.config.Property(name="doc_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="filename", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="doc_type", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="tenant", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="chunk_index", data_type=wvc.config.DataType.INT),
                    wvc.config.Property(name="created_at", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="metadata", data_type=wvc.config.DataType.OBJECT)
                ]
            }
        ]
    
    def check_collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        try:
            return self.client.collections.exists(collection_name)
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
                collection = self.client.collections.get(collection_name)
                logger.info(f"  - Collection: {collection_name}")
                logger.info(f"  - Description: {config['description']}")
                
                # Ask if we should keep existing
                logger.info(f"Keeping existing collection '{collection_name}'")
                return True
            
            # Create new collection
            logger.info(f"Creating collection '{collection_name}'...")
            
            self.client.collections.create(
                name=collection_name,
                description=config['description'],
                properties=config.get('properties', []),
                vectorizer_config=wvc.config.Configure.Vectorizer.none()  # We'll provide our own vectors
            )
            
            logger.info(f"✅ Collection '{collection_name}' created successfully")
            logger.info(f"  - Description: {config['description']}")
            logger.info(f"  - Properties: {len(config.get('properties', []))}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{collection_name}': {str(e)}")
            return False
    
    def test_collection(self, collection_name: str) -> bool:
        """Test a collection with sample data insertion and retrieval"""
        logger.info(f"\nTesting collection '{collection_name}'...")
        
        try:
            # Get collection
            collection = self.client.collections.get(collection_name)
            
            # Create test vector
            test_vector = [0.1] * 1536  # Standard embedding dimension
            test_uuid = "test-uuid-12345"
            
            # Create test properties based on collection type
            test_properties = {
                'SlackMessages': {
                    'message_id': 'test_msg_001',
                    'channel_id': 'test_channel',
                    'user_id': 'test_user',
                    'timestamp': datetime.utcnow(),
                    'content': 'This is a test message for Weaviate setup',
                    'team_id': 'test_team'
                },
                'GongTranscripts': {
                    'call_id': 'test_call_001',
                    'transcript_id': 'test_trans_001',
                    'speaker': 'Test Speaker',
                    'timestamp': datetime.utcnow(),
                    'content': 'This is a test transcript segment',
                    'sentiment': 0.85,
                    'keywords': ['test', 'weaviate', 'setup']
                },
                'NotionPages': {
                    'page_id': 'test_page_001',
                    'workspace_id': 'test_workspace',
                    'title': 'Test Page',
                    'content': 'This is test content for Notion page',
                    'last_edited': datetime.utcnow(),
                    'created_by': 'test_user',
                    'tags': ['test', 'setup']
                },
                'SophiaKnowledgeBase': {
                    'doc_id': 'test_doc_001',
                    'filename': 'test.md',
                    'content': 'This is test knowledge content',
                    'doc_type': 'documentation',
                    'tenant': 'test',
                    'chunk_index': 0,
                    'created_at': datetime.utcnow(),
                    'metadata': {'test': True}
                }
            }
            
            test_props = test_properties.get(collection_name, {
                'test': True,
                'timestamp': datetime.utcnow()
            })
            
            # Insert test object
            collection.data.insert(
                uuid=test_uuid,
                properties=test_props,
                vector=test_vector
            )
            logger.info(f"  ✓ Test object inserted (UUID: {test_uuid})")
            
            # Search for similar vectors
            search_results = collection.query.near_vector(
                near_vector=test_vector,
                limit=1
            )
            
            if search_results.objects:
                logger.info(f"  ✓ Search successful - found {len(search_results.objects)} results")
                logger.info(f"    UUID: {search_results.objects[0].uuid}")
            
            # Clean up test data
            collection.data.delete_by_id(test_uuid)
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
            # Get all collections
            all_collections = self.client.collections.list_all()
            
            for collection_name in all_collections:
                try:
                    collection = self.client.collections.get(collection_name)
                    # Get basic stats - note: Weaviate doesn't have direct count methods
                    # We'd need to use aggregate queries for precise counts
                    stats[collection_name] = {
                        'name': collection_name,
                        'exists': True,
                        'description': 'Vector collection for embeddings'
                    }
                except Exception as e:
                    logger.warning(f"Could not get stats for {collection_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            
        return stats
    
    def run(self) -> bool:
        """Run the complete Weaviate setup"""
        logger.info("=" * 60)
        logger.info("Starting Weaviate Collection Setup")
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
            logger.info(f"  Name: {collection_stats['name']}")
            logger.info(f"  Exists: {collection_stats['exists']}")
            logger.info(f"  Description: {collection_stats['description']}")
        
        # Overall status
        all_success = failed_count == 0 and all(test_results)
        
        logger.info("\n" + "=" * 60)
        if all_success:
            logger.info("🎉 Weaviate setup completed successfully!")
            logger.info("All collections are ready for use.")
        else:
            logger.warning("⚠️ Weaviate setup completed with some issues.")
            logger.warning("Please check the logs for details.")
        logger.info("=" * 60)
        
        return all_success

def main():
    """Main entry point"""
    try:
        setup = WeaviateSetup()
        success = setup.run()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()