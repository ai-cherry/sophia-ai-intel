#!/usr/bin/env python3
"""
Basic Weaviate Cloud connectivity test
Tests the core connectivity to our Weaviate Cloud instance
"""

import weaviate
import os
import sys
from typing import Dict, Any

# Weaviate Cloud connection info
WEAVIATE_URL = "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"

def test_basic_connectivity():
    """Test basic connectivity to Weaviate Cloud"""
    print("🔗 Testing basic Weaviate Cloud connectivity...")
    
    try:
        # Create client
        client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
            timeout_config=(5, 15)
        )
        
        # Test connectivity
        if client.is_ready():
            print("✅ Weaviate Cloud is ready and responsive")
            return client
        else:
            print("❌ Weaviate Cloud is not ready")
            return None
            
    except Exception as e:
        print(f"❌ Failed to connect to Weaviate Cloud: {e}")
        return None

def test_cluster_health(client):
    """Test cluster health and metadata"""
    print("\n🏥 Testing cluster health...")
    
    try:
        # Get cluster metadata
        metadata = client.cluster.get_nodes_status()
        print(f"✅ Cluster nodes status: {len(metadata)} nodes")
        
        for i, node in enumerate(metadata):
            print(f"   Node {i+1}: {node.get('name', 'Unknown')} - Status: {node.get('status', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get cluster health: {e}")
        return False

def test_schema_access(client):
    """Test schema access and list existing classes"""
    print("\n📋 Testing schema access...")
    
    try:
        # Get schema
        schema = client.schema.get()
        classes = schema.get('classes', [])
        
        print(f"✅ Schema accessible - Found {len(classes)} classes:")
        for class_info in classes:
            class_name = class_info.get('class', 'Unknown')
            properties = class_info.get('properties', [])
            print(f"   - {class_name} ({len(properties)} properties)")
        
        return True, classes
        
    except Exception as e:
        print(f"❌ Failed to access schema: {e}")
        return False, []

def test_basic_operations(client, classes):
    """Test basic vector operations if we have classes"""
    print("\n🔧 Testing basic operations...")
    
    if not classes:
        print("⚠️  No classes found - skipping operations test")
        return True
    
    try:
        # Try to query an existing class (just check if query works)
        test_class = classes[0]['class']
        print(f"   Testing query on class: {test_class}")
        
        result = client.query.get(test_class).with_limit(1).do()
        print(f"✅ Query successful - class {test_class} is accessible")
        
        # Test aggregation
        agg_result = client.query.aggregate(test_class).with_meta_count().do()
        count = agg_result.get('data', {}).get('Aggregate', {}).get(test_class, [{}])[0].get('meta', {}).get('count', 0)
        print(f"✅ Aggregation successful - {test_class} has {count} objects")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Basic operations test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Weaviate Cloud Integration Validation")
    print("=" * 50)
    
    # Test basic connectivity
    client = test_basic_connectivity()
    if not client:
        print("\n❌ CRITICAL: Cannot connect to Weaviate Cloud!")
        sys.exit(1)
    
    # Test cluster health
    health_ok = test_cluster_health(client)
    
    # Test schema access
    schema_ok, classes = test_schema_access(client)
    
    # Test basic operations
    ops_ok = test_basic_operations(client, classes)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 WEAVIATE CLOUD VALIDATION SUMMARY:")
    print(f"   Connectivity: {'✅ PASS' if client else '❌ FAIL'}")
    print(f"   Cluster Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Schema Access: {'✅ PASS' if schema_ok else '❌ FAIL'}")
    print(f"   Basic Operations: {'✅ PASS' if ops_ok else '⚠️  PARTIAL'}")
    
    if client and health_ok and schema_ok:
        print("\n🎉 Weaviate Cloud is ready for service testing!")
        return True
    else:
        print("\n🚨 Weaviate Cloud has issues that need attention!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)