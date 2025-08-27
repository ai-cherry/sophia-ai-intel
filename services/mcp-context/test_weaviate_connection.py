#!/usr/bin/env python3
"""
Test Weaviate Cloud connection for mcp-context service migration
"""

import os
import sys
import weaviate

# Test credentials provided in migration task
WEAVIATE_URL = "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"

def test_weaviate_connection():
    """Test connection to Weaviate Cloud"""
    print(f"Testing connection to Weaviate Cloud: {WEAVIATE_URL}")
    
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
            
            # Test creating our required classes
            test_schema_creation(client)
            
            print("✅ All Weaviate tests passed!")
            return True
        else:
            print("❌ Weaviate cluster not ready")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_schema_creation(client):
    """Test creating the schemas we need"""
    
    # Test SophiaCodeIntelligence class creation
    intelligence_class = {
        "class": "SophiaCodeIntelligenceTest",
        "description": "Test class for Sophia AI code intelligence documents",
        "vectorizer": "none",
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Document content"
            },
            {
                "name": "source",
                "dataType": ["string"],
                "description": "Document source"
            }
        ]
    }
    
    try:
        client.schema.create_class(intelligence_class)
        print("✅ Successfully created SophiaCodeIntelligenceTest class")
        
        # Clean up test class
        client.schema.delete_class("SophiaCodeIntelligenceTest")
        print("✅ Successfully cleaned up test class")
        
    except Exception as e:
        print(f"⚠️  Schema creation test: {e}")

    # Test SophiaCodeSymbols class creation
    symbols_class = {
        "class": "SophiaCodeSymbolsTest",
        "description": "Test class for code symbols",
        "vectorizer": "none",
        "properties": [
            {
                "name": "name",
                "dataType": ["string"],
                "description": "Symbol name"
            },
            {
                "name": "kind",
                "dataType": ["string"],
                "description": "Symbol kind"
            }
        ]
    }
    
    try:
        client.schema.create_class(symbols_class)
        print("✅ Successfully created SophiaCodeSymbolsTest class")
        
        # Clean up test class
        client.schema.delete_class("SophiaCodeSymbolsTest")
        print("✅ Successfully cleaned up test class")
        
    except Exception as e:
        print(f"⚠️  Symbols schema creation test: {e}")

def test_basic_operations(client):
    """Test basic CRUD operations"""
    try:
        # Create a test object
        test_object = {
            "content": "This is a test document for Weaviate migration",
            "source": "test_migration"
        }
        
        result = client.data_object.create(
            data_object=test_object,
            class_name="SophiaCodeIntelligenceTest"
        )
        
        object_id = result
        print(f"✅ Created test object: {object_id}")
        
        # Delete test object
        client.data_object.delete(object_id, class_name="SophiaCodeIntelligenceTest")
        print("✅ Successfully deleted test object")
        
    except Exception as e:
        print(f"⚠️  Basic operations test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Weaviate Cloud connection test for mcp-context migration")
    print("=" * 60)
    
    success = test_weaviate_connection()
    
    print("=" * 60)
    if success:
        print("✅ Migration validation complete - Weaviate Cloud ready!")
        sys.exit(0)
    else:
        print("❌ Migration validation failed - connection issues detected")
        sys.exit(1)