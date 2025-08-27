#!/usr/bin/env python3
"""
Test script for Weaviate Cloud connection validation using v4 client
"""
import weaviate
import weaviate.classes as wvc
import json
import sys

def test_weaviate_connection():
    """Test Weaviate connection with provided credentials using v4 client."""
    print("Testing Weaviate Cloud Connection...")
    print("=" * 50)
    
    # Connection configuration
    url = "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
    api_key = "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"
    
    try:
        # Initialize client using v4 syntax
        print(f"Connecting to: {url}")
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=wvc.init.Auth.api_key(api_key)
        )
        
        # Test connection readiness
        print("\n1. Testing connection readiness...")
        is_ready = client.is_ready()
        print(f"   Connection ready: {is_ready}")
        
        if not is_ready:
            print("   ❌ Client not ready - connection failed")
            return False
            
        # Test cluster metadata
        print("\n2. Getting cluster metadata...")
        meta = client.get_meta()
        print(f"   Weaviate version: {meta.get('version', 'Unknown')}")
        print(f"   Hostname: {meta.get('hostname', 'Unknown')}")
        
        # List available modules
        modules = meta.get('modules', {})
        print(f"   Available modules: {len(modules)}")
        embedding_modules = [k for k in modules.keys() if 'text2vec' in k]
        print(f"   Text embedding modules: {len(embedding_modules)}")
        if embedding_modules:
            print("   Available embedding modules:")
            for module in embedding_modules[:5]:  # Show first 5
                print(f"     - {module}")
        
        # Test collections (schema) retrieval
        print("\n3. Retrieving current collections...")
        try:
            collections = client.collections.list_all()
            print(f"   Collections found: {len(collections)}")
            
            if collections:
                print("   Existing collections:")
                for collection_name in collections:
                    print(f"     - {collection_name}")
            else:
                print("   No existing collections found (empty schema)")
        except Exception as schema_e:
            print(f"   Warning: Could not retrieve collections: {str(schema_e)}")
            
        print("\n✅ All connection tests passed!")
        
        # Close the connection
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_weaviate_connection()
    sys.exit(0 if success else 1)