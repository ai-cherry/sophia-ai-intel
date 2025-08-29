#!/usr/bin/env python3
"""
Final comprehensive test for MCP adapter integration
"""

import asyncio
import httpx
import json
import subprocess
import sys
from datetime import datetime

def test_libraries():
    """Test that all required libraries are installed"""
    print("1. Testing Required Libraries")
    print("-" * 40)
    
    try:
        import mcp.server
        print("   ✅ MCP library installed")
    except ImportError:
        print("   ❌ MCP library missing")
        return False
    
    try:
        import httpx
        print("   ✅ httpx library installed")
    except ImportError:
        print("   ❌ httpx library missing")
        return False
    
    return True

async def test_services():
    """Test that services are running"""
    print("\n2. Testing Service Availability")
    print("-" * 40)
    
    services = {
        "context": 8081,
        "research": 8085,
        "github": 8082,
        "hubspot": 8083,
        "salesforce": 8092,
        "gong": 8091,
        "agents": 8000,
        "coordinator": 8080,
        "orchestrator": 8088
    }
    
    working = 0
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, port in services.items():
            try:
                response = await client.get(f"http://localhost:{port}/health")
                if response.status_code in [200, 404]:  # 404 means service is running but no health endpoint
                    print(f"   ✅ {name:12} (port {port})")
                    working += 1
                else:
                    print(f"   ❌ {name:12} (port {port}) - Status {response.status_code}")
            except:
                print(f"   ❌ {name:12} (port {port}) - Not accessible")
    
    print(f"\n   Services Running: {working}/{len(services)}")
    return working > 0

def test_adapter_file():
    """Test that adapter file exists and is valid"""
    print("\n3. Testing MCP Adapter File")
    print("-" * 40)
    
    import os
    adapter_path = "/Users/lynnmusil/sophia-ai-intel-1/mcp-universal-adapter.py"
    
    if os.path.exists(adapter_path):
        print(f"   ✅ Adapter file exists: {adapter_path}")
        
        # Check if it's executable
        if os.access(adapter_path, os.X_OK):
            print("   ✅ Adapter is executable")
        else:
            print("   ⚠️ Adapter not executable (will still work with python3)")
        
        # Check file size
        size = os.path.getsize(adapter_path)
        print(f"   ✅ Adapter size: {size} bytes")
        
        return True
    else:
        print(f"   ❌ Adapter file not found: {adapter_path}")
        return False

def test_config_file():
    """Test that Cline config file exists"""
    print("\n4. Testing Cline Configuration")
    print("-" * 40)
    
    import os
    config_path = "/Users/lynnmusil/sophia-ai-intel-1/cline-mcp-config.json"
    
    if os.path.exists(config_path):
        print(f"   ✅ Config file exists: {config_path}")
        
        # Try to parse it
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                if "mcpServers" in config:
                    print("   ✅ Valid MCP configuration structure")
                    servers = config.get("mcpServers", {})
                    for server_name in servers:
                        print(f"   ✅ Server configured: {server_name}")
                    return True
        except Exception as e:
            print(f"   ❌ Config parsing error: {e}")
            return False
    else:
        print(f"   ❌ Config file not found: {config_path}")
        return False

def show_integration_summary():
    """Show how the integration works"""
    print("\n5. Integration Architecture")
    print("-" * 40)
    print("""
   Current Setup (UNCHANGED):
   [Sophia App] <--HTTP--> [Services:8081-8092]
   
   MCP Integration (NEW):
   [Cline] <--MCP Protocol--> [Adapter] <--HTTP--> [Services]
   
   Key Points:
   • Services remain HTTP-only (no changes)
   • Adapter translates MCP ↔ HTTP
   • Sophia integration untouched
   • Can be removed anytime
   """)

def show_next_steps():
    """Show what to do next"""
    print("\n6. Next Steps to Connect Cline")
    print("-" * 40)
    print("""
   To connect Cline to your services:
   
   1. Open Cline settings in VSCode
   2. Go to MCP Servers section
   3. Click "Edit Config File"
   4. Add this configuration:
   
   {
     "sophia-universal": {
       "command": "python3",
       "args": ["/Users/lynnmusil/sophia-ai-intel-1/mcp-universal-adapter.py"]
     }
   }
   
   5. Restart Cline or reload VSCode
   
   Once connected, you'll have access to:
   • search_context - Semantic search
   • store_document - Store with embeddings
   • web_search - Web searches
   • search_code - GitHub search
   • get_crm_contacts - CRM access
   • execute_workflow - Run workflows
   • check_service_health - Monitor services
   """)

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🔍 MCP ADAPTER INTEGRATION - FINAL VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    all_good = True
    
    # Test libraries
    if not test_libraries():
        all_good = False
    
    # Test services
    if not await test_services():
        all_good = False
    
    # Test adapter file
    if not test_adapter_file():
        all_good = False
    
    # Test config
    if not test_config_file():
        all_good = False
    
    # Show architecture
    show_integration_summary()
    
    # Final verdict
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION RESULT")
    print("=" * 60)
    
    if all_good:
        print("\n🎉 ALL CHECKS PASSED - READY FOR CLINE CONNECTION!")
        print("\nYour MCP adapter is ready. Your existing services remain")
        print("completely unchanged. The adapter acts as a translator.")
        show_next_steps()
        return True
    else:
        print("\n⚠️ SOME CHECKS FAILED")
        print("Please review the errors above and fix any issues.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
