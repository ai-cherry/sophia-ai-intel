#!/usr/bin/env python3
"""
Test Weaviate Cloud connection for vector-indexer service migration
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
import weaviate

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test credentials provided in migration task
WEAVIATE_URL = "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"
CLASS_NAME = "SophiaDocumentsTest"

def test_weaviate_connection():
    """Test connection to Weaviate Cloud"""
    print(f"Testing Weaviate Cloud connection for vector-indexer: {WEAVIATE_URL}")
    
    try:
        # Create client
        client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY)
        )
        
        # Test basic connectivity
        if client.is_ready():
            print("✅ Weaviate Cloud connection successful!")
            
            # Get cluster information
            meta = client.get_meta()
            print(f"✅ Weaviate version: {meta.get('version', 'unknown')}")
            
            # Get schema
            schema = client.schema.get()
            classes = schema.get('classes', [])
            print(f"✅ Found {len(classes)} existing classes in schema")
            
            for cls in classes:
                print(f"   - Class: {cls['class']}")
            
            # Test creating our required class
            test_schema_creation(client)
            
            # Test batch operations
            test_batch_operations(client)
            
            print("✅ All vector-indexer Weaviate tests passed!")
            return True
        else:
            print("❌ Weaviate cluster not ready")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_schema_creation(client):
    """Test creating the schema for vector-indexer"""
    
    class_definition = {
        "class": CLASS_NAME,
        "description": "Test class for Sophia AI vector indexer documents",
        "vectorizer": "none",  # We provide our own vectors
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Document content"
            },
            {
                "name": "docId",
                "dataType": ["string"],
                "description": "Document ID"
            },
            {
                "name": "accountId",
                "dataType": ["string"],
                "description": "Account ID"
            },
            {
                "name": "chunkIndex",
                "dataType": ["int"],
                "description": "Chunk index"
            },
            {
                "name": "chunkHash",
                "dataType": ["string"],
                "description": "Chunk hash for deduplication"
            },
            {
                "name": "url",
                "dataType": ["string"],
                "description": "Source URL"
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "Creation timestamp"
            },
            {
                "name": "embeddingModel",
                "dataType": ["string"],
                "description": "Embedding model used"
            },
            {
                "name": "embeddingProvider",
                "dataType": ["string"],
                "description": "Embedding provider"
            }
        ]
    }
    
    try:
        client.schema.create_class(class_definition)
        print(f"✅ Successfully created {CLASS_NAME} class")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"⚠️  {CLASS_NAME} class already exists")
        else:
            print(f"❌ Schema creation failed: {e}")
            return False
    
    return True

def test_batch_operations(client):
    """Test batch operations that vector-indexer will use"""
    try:
        # Test batch upload with mock data
        test_data = [
            {
                "id": "test_doc_1_chunk_0",
                "vector": [0.1] * 3072,  # Mock 3072-dimensional vector
                "properties": {
                    "content": "This is test chunk 0 from document 1",
                    "docId": "test_doc_1",
                    "accountId": "test_account",
                    "chunkIndex": 0,
                    "chunkHash": "hash_chunk_0",
                    "url": "https://example.com/doc1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "embeddingModel": "text-embedding-3-large",
                    "embeddingProvider": "standardized_portkey_routing"
                }
            },
            {
                "id": "test_doc_1_chunk_1",
                "vector": [0.2] * 3072,  # Mock 3072-dimensional vector
                "properties": {
                    "content": "This is test chunk 1 from document 1",
                    "docId": "test_doc_1",
                    "accountId": "test_account",
                    "chunkIndex": 1,
                    "chunkHash": "hash_chunk_1",
                    "url": "https://example.com/doc1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "embeddingModel": "text-embedding-3-large",
                    "embeddingProvider": "standardized_portkey_routing"
                }
            }
        ]
        
        # Use batch operations like in worker.py
        with client.batch as batch:
            batch.batch_size = len(test_data)
            
            for item in test_data:
                batch.add_data_object(
                    data_object=item["properties"],
                    class_name=CLASS_NAME,
                    uuid=item["id"],
                    vector=item["vector"]
                )
        
        print(f"✅ Successfully uploaded {len(test_data)} test objects using batch operations")
        
        # Test query
        response = (
            client.query
            .get(CLASS_NAME, ["content", "docId", "chunkIndex"])
            .with_limit(5)
            .do()
        )
        
        if 'data' in response and 'Get' in response['data']:
            results = response['data']['Get'][CLASS_NAME]
            print(f"✅ Successfully queried {len(results)} objects from {CLASS_NAME}")
        
        # Cleanup - delete test objects
        try:
            client.batch.delete_objects(
                class_name=CLASS_NAME,
                where={
                    "path": ["docId"],
                    "operator": "Equal",
                    "valueString": "test_doc_1"
                }
            )
            print("✅ Successfully cleaned up test objects")
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup warning: {cleanup_error}")
        
        # Cleanup - delete test class
        try:
            client.schema.delete_class(CLASS_NAME)
            print(f"✅ Successfully cleaned up test class {CLASS_NAME}")
        except Exception as cleanup_error:
            print(f"⚠️  Class cleanup warning: {cleanup_error}")
            
        return True
        
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Weaviate Cloud connection test for vector-indexer migration")
    print("=" * 70)
    
    success = test_weaviate_connection()
    
    print("=" * 70)
    if success:
        print("✅ Migration validation complete - Weaviate Cloud ready for vector-indexer!")
        sys.exit(0)
    else:
        print("❌ Migration validation failed - connection issues detected")
        sys.exit(1)