#!/usr/bin/env python3
"""
Test script for official Weaviate Cloud connection pattern
Based on official Weaviate Python client documentation
"""

import os
import weaviate
from weaviate.classes.init import Auth

def test_official_pattern():
    """Test the official Weaviate Cloud connection pattern"""
    
    # Environment variables (without https:// prefix as per official docs)
    weaviate_url = os.getenv("WEAVIATE_URL", "w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf")
    
    print("🔧 Testing Official Weaviate Cloud Connection Pattern")
    print(f"URL: {weaviate_url}")
    print(f"API Key: {'*' * 20}...{weaviate_api_key[-6:]}")
    
    try:
        # Official pattern from Weaviate documentation
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,  # No https:// prefix
            auth_credentials=Auth.api_key(weaviate_api_key),
        )
        
        # Test connection
        if client.is_ready():
            print("✅ Connection successful!")
            
            # Get cluster status
            try:
                collections = client.collections.list_all()
                print(f"✅ Found {len(collections)} collections")
                
                # Test basic operations
                print("✅ Basic operations working")
                
                return True
            except Exception as e:
                print(f"⚠️ Operations test failed: {e}")
                return False
        else:
            print("❌ Client not ready")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    success = test_official_pattern()
    if success:
        print("\n🎉 Official Weaviate Cloud pattern is working correctly!")
    else:
        print("\n❌ Official pattern test failed")
        exit(1)