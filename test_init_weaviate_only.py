#!/usr/bin/env python3
"""
Test only the Weaviate portion of init_databases.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import weaviate
import weaviate.classes as wvc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Weaviate Cloud connection info
WEAVIATE_URL = "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"

def init_weaviate() -> bool:
    """Initialize Weaviate vector collections using v4 client"""
    logger.info("🚀 Testing Weaviate initialization (from init_databases.py)...")
    
    try:
        # Connect to Weaviate Cloud using v4 client API
        client = weaviate.connect_to_wcs(
            cluster_url=WEAVIATE_URL,
            auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
        )
        
        logger.info("✅ Connected to Weaviate Cloud using v4 client")
        
        # Define collections using v4 API
        collections_config = [
            {
                'name': 'SlackMessages',
                'properties': [
                    wvc.config.Property(name="message_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE)
                ]
            },
            {
                'name': 'GongTranscripts',
                'properties': [
                    wvc.config.Property(name="call_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE)
                ]
            },
            {
                'name': 'NotionPages',
                'properties': [
                    wvc.config.Property(name="page_id", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE)
                ]
            }
        ]
        
        for collection_config in collections_config:
            try:
                collection_name = collection_config['name']
                logger.info(f"🔧 Processing collection: {collection_name}")
                
                # Check if collection exists
                if not client.collections.exists(collection_name):
                    # Create collection
                    client.collections.create(
                        name=collection_name,
                        properties=collection_config['properties'],
                        vectorizer_config=wvc.config.Configure.Vectorizer.none()
                    )
                    logger.info(f"✅ Created collection: {collection_name}")
                else:
                    logger.info(f"ℹ️ Collection already exists: {collection_name}")
                
                # Test insertion to verify connectivity
                collection = client.collections.get(collection_name)
                test_uuid = f"test-{collection_name}-999999"
                
                # Create test properties based on collection type
                if collection_name == "SlackMessages":
                    test_properties = {
                        "message_id": "test-msg-123",
                        "content": f"Test message for {collection_name}",
                        "timestamp": datetime.utcnow()
                    }
                elif collection_name == "GongTranscripts":
                    test_properties = {
                        "call_id": "test-call-123",
                        "content": f"Test transcript for {collection_name}",
                        "timestamp": datetime.utcnow()
                    }
                elif collection_name == "NotionPages":
                    test_properties = {
                        "page_id": "test-page-123",
                        "content": f"Test page for {collection_name}",
                        "timestamp": datetime.utcnow()
                    }
                
                # Insert test data
                collection.data.insert(
                    uuid=test_uuid,
                    properties=test_properties,
                    vector=[0.1] * 1536  # Standard embedding dimension
                )
                logger.info(f"✅ Test insertion successful for {collection_name}")
                
                # Query to verify the data exists
                result = collection.query.fetch_object_by_id(test_uuid)
                if result:
                    logger.info(f"✅ Test data verified for {collection_name}")
                
                # Clean up test data
                collection.data.delete_by_id(test_uuid)
                logger.info(f"✅ Test data cleaned up for {collection_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize collection {collection_name}: {str(e)}")
                return False
        
        # Close connection
        client.close()
        logger.info("✅ Weaviate v4 client closed properly")
        
        logger.info("🎉 Weaviate collections initialized successfully using v4 API!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Weaviate: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("WEAVIATE INITIALIZATION TEST (from init_databases.py)")
    logger.info("=" * 60)
    
    success = init_weaviate()
    
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ Weaviate initialization test PASSED")
        logger.info("🚀 init_databases.py Weaviate component is ready!")
        sys.exit(0)
    else:
        logger.error("❌ Weaviate initialization test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()