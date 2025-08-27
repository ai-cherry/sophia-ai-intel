#!/usr/bin/env python3
"""
Test Weaviate Cloud connection for mcp-research service
"""

import os
import sys
import asyncio
import weaviate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Weaviate Cloud credentials
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

async def test_weaviate_connection():
    """Test connection to Weaviate Cloud"""
    
    print("🔍 Testing Weaviate Cloud connection for mcp-research service...")
    print(f"URL: {WEAVIATE_URL}")
    print(f"API Key configured: {'Yes' if WEAVIATE_API_KEY else 'No'}")
    
    if not WEAVIATE_URL or not WEAVIATE_API_KEY:
        print("❌ Missing Weaviate Cloud credentials!")
        print("Required environment variables:")
        print("- WEAVIATE_URL")
        print("- WEAVIATE_API_KEY")
        return False
    
    try:
        # Create Weaviate client following mcp-context pattern
        client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY)
        )
        
        # Test connection
        print("📡 Testing connection...")
        if client.is_ready():
            print("✅ Weaviate Cloud connection successful!")
            
            # Get cluster info
            meta = client.get_meta()
            print(f"📊 Cluster info:")
            print(f"   Version: {meta.get('version', 'Unknown')}")
            print(f"   Hostname: {meta.get('hostname', 'Unknown')}")
            
            # Test schema operations
            print("🔧 Testing schema operations...")
            schema = client.schema.get()
            existing_classes = [cls["class"] for cls in schema.get("classes", [])]
            print(f"   Existing classes: {existing_classes}")
            
            # Test if ResearchResult class exists or can be created
            research_class_name = "ResearchResult"
            if research_class_name in existing_classes:
                print(f"✅ {research_class_name} class already exists")
            else:
                print(f"ℹ️  {research_class_name} class will be created on first use")
            
            print("🎉 All Weaviate tests passed! mcp-research is ready for deployment.")
            return True
            
        else:
            print("❌ Weaviate Cloud is not ready!")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    finally:
        try:
            if 'client' in locals():
                client.close()
        except Exception as e:
            print(f"Warning: Error closing client: {e}")

if __name__ == "__main__":
    success = asyncio.run(test_weaviate_connection())
    sys.exit(0 if success else 1)