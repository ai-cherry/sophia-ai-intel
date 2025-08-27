#!/usr/bin/env python3
# scripts/neon_get_dsn.py
"""
Neon DSN Fetcher
Gets the correct connection string from Neon API
"""

import os
import sys
import json
import asyncio
import aiohttp
import asyncpg

# Environment configuration
NEON_API_KEY = os.getenv("NEON_API_KEY", "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby")
NEON_PROJECT_ID = os.getenv("NEON_PROJECT_ID", "rough-union-72390895")
NEON_BRANCH_ID = os.getenv("NEON_BRANCH_ID", "br-green-firefly-afykrx78")
NEON_PASSWORD = os.getenv("NEON_PASSWORD", "Huskers1983$")
DEFAULT_USER = os.getenv("NEON_ROLE", "neondb_owner")
DEFAULT_DB = os.getenv("NEON_DB", "neondb")

BASE_URL = "https://console.neon.tech/api/v2"

async def get_connection_uri():
    """Get the connection URI from Neon API"""
    
    print("🔍 Fetching connection details from Neon API...")
    print(f"   Project: {NEON_PROJECT_ID}")
    print(f"   Branch: {NEON_BRANCH_ID}")
    
    # First, get the project details to find the connection URI
    project_url = f"{BASE_URL}/projects/{NEON_PROJECT_ID}"
    
    headers = {
        "Authorization": f"Bearer {NEON_API_KEY}",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Get project details
        async with session.get(project_url, headers=headers) as resp:
            if resp.status == 200:
                project_data = await resp.json()
                print(f"\n📋 Project Details:")
                print(f"   Name: {project_data['project'].get('name', 'N/A')}")
                print(f"   Region: {project_data['project'].get('region_id', 'N/A')}")
                
                # Get connection URI from project
                connection_uris = project_data['project'].get('connection_uris', [])
                if connection_uris:
                    for uri_info in connection_uris:
                        uri = uri_info.get('connection_uri', '')
                        if uri:
                            print(f"\n🔗 Found Connection URI from project:")
                            # Replace password placeholder
                            if '[YOUR-PASSWORD]' in uri:
                                uri = uri.replace('[YOUR-PASSWORD]', NEON_PASSWORD)
                                print(f"   {uri}")
                                return uri
        
        # Get branch-specific connection details
        branch_url = f"{BASE_URL}/projects/{NEON_PROJECT_ID}/branches/{NEON_BRANCH_ID}"
        async with session.get(branch_url, headers=headers) as resp:
            if resp.status == 200:
                branch_data = await resp.json()
                print(f"\n📋 Branch Details:")
                print(f"   Name: {branch_data['branch'].get('name', 'N/A')}")
                print(f"   Created: {branch_data['branch'].get('created_at', 'N/A')}")
        
        # Get endpoints for more specific connection info
        endpoints_url = f"{BASE_URL}/projects/{NEON_PROJECT_ID}/endpoints"
        async with session.get(endpoints_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                print(f"\n📡 Endpoints found: {len(data.get('endpoints', []))}")
                
                for endpoint in data.get("endpoints", []):
                    if endpoint.get("branch_id") == NEON_BRANCH_ID:
                        host = endpoint.get("host")
                        endpoint_type = endpoint.get("type", "unknown")
                        state = endpoint.get("state", "unknown")
                        
                        print(f"\n✅ Found matching endpoint:")
                        print(f"   Type: {endpoint_type}")
                        print(f"   State: {state}")
                        print(f"   Host: {host}")
                        
                        if host:
                            # Build DSN with correct format
                            dsn = f"postgresql://{DEFAULT_USER}:{NEON_PASSWORD}@{host}:5432/{DEFAULT_DB}?sslmode=require"
                            print(f"\n💾 Built DSN:")
                            print(f"   {dsn}")
                            return dsn
                
                print("\n⚠️ No endpoint found for branch. May need to create one.")
    
    return None

async def test_connection(dsn):
    """Test the database connection"""
    
    print("\n🔗 Testing connection...")
    
    try:
        # Try different SSL modes
        for sslmode in ['require', 'prefer', 'disable']:
            test_dsn = dsn.replace('sslmode=require', f'sslmode={sslmode}')
            print(f"\n   Trying sslmode={sslmode}...")
            
            try:
                conn = await asyncpg.connect(test_dsn, timeout=10)
                
                # Test basic queries
                version = await conn.fetchval("SELECT version()")
                current_user = await conn.fetchval("SELECT current_user")
                current_db = await conn.fetchval("SELECT current_database()")
                
                await conn.close()
                
                print(f"   ✅ Connection successful with sslmode={sslmode}!")
                print(f"   User: {current_user}")
                print(f"   Database: {current_db}")
                print(f"   Version: {version[:50]}...")
                
                return True, test_dsn
                
            except asyncpg.InvalidPasswordError:
                print(f"   ❌ Invalid password with sslmode={sslmode}")
            except Exception as e:
                print(f"   ❌ Failed with sslmode={sslmode}: {str(e)[:100]}")
        
        return False, None
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        return False, None

async def main():
    """Main entry point"""
    
    print("=" * 60)
    print("Neon Connection String Fetcher")
    print("=" * 60)
    
    # Check for API key
    if not NEON_API_KEY:
        print("❌ NEON_API_KEY is required")
        sys.exit(1)
    
    # Get connection URI
    dsn = await get_connection_uri()
    
    if not dsn:
        print("\n❌ Could not fetch connection string")
        print("\n💡 Next steps:")
        print("   1. Check if endpoint exists: python3 scripts/neon_rest.py endpoints")
        print("   2. Create endpoint if needed: python3 scripts/neon_rest.py endpoint-create")
        print("   3. Reset password in Neon console: https://console.neon.tech")
        sys.exit(1)
    
    # Test the connection
    success, working_dsn = await test_connection(dsn)
    
    if success:
        print("\n✅ Connection test successful!")
        print(f"\n📝 Export this environment variable:")
        print(f"export NEON_DATABASE_URL='{working_dsn}'")
        
        # Also show the endpoint host for reference
        host = working_dsn.split('@')[1].split(':')[0]
        print(f"\n📡 Endpoint host for reference:")
        print(f"export NEON_ENDPOINT_HOST='{host}'")
        
        sys.exit(0)
    else:
        print("\n❌ Connection test failed!")
        print("\n💡 Troubleshooting steps:")
        print("   1. The password might be incorrect")
        print("   2. Reset password in Neon console: https://console.neon.tech")
        print("   3. Or try with the console-provided connection string")
        print("   4. Check if the endpoint is in 'active' state")
        print(f"\n📋 Current password being used: {NEON_PASSWORD}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())