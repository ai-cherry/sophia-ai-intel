#!/usr/bin/env python3
# scripts/neon_reset_password.py
"""
Neon Password Reset Tool
Resets database role passwords using Neon SQL API
"""

import os
import sys
import json
import asyncio
import aiohttp

# Environment configuration
NEON_API_KEY = os.getenv("NEON_API_KEY", "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby")
NEON_PROJECT_ID = os.getenv("NEON_PROJECT_ID", "rough-union-72390895")
NEON_BRANCH_ID = os.getenv("NEON_BRANCH_ID", "br-green-firefly-afykrx78")
NEON_PASSWORD = os.getenv("NEON_PASSWORD", "Huskers1983$")
DEFAULT_USER = os.getenv("NEON_ROLE", "neondb_owner")
DEFAULT_DB = os.getenv("NEON_DB", "neondb")

BASE_URL = "https://console.neon.tech/api/v2"

async def reset_password(role: str, password: str, branch_id: str = NEON_BRANCH_ID):
    """Reset password for a database role using Neon SQL API"""
    
    print(f"🔑 Resetting password for role '{role}'...")
    print(f"   Project: {NEON_PROJECT_ID}")
    print(f"   Branch: {branch_id}")
    
    # SQL endpoint for executing queries
    sql_endpoint = f"{BASE_URL}/projects/{NEON_PROJECT_ID}/branches/{branch_id}/sql"
    
    # SQL query to reset password
    sql_query = f"ALTER ROLE {role} WITH PASSWORD '{password}'"
    
    headers = {
        "Authorization": f"Bearer {NEON_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": sql_query,
        "db_name": DEFAULT_DB
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(sql_endpoint, headers=headers, json=payload) as resp:
                text = await resp.text()
                
                if resp.status == 200 or resp.status == 201:
                    print(f"✅ Password reset successfully!")
                    print(f"   Role: {role}")
                    print(f"   New Password: {password}")
                    
                    # Also try to verify the role exists
                    verify_query = f"SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = '{role}'"
                    verify_payload = {"query": verify_query, "db_name": DEFAULT_DB}
                    
                    async with session.post(sql_endpoint, headers=headers, json=verify_payload) as verify_resp:
                        if verify_resp.status == 200:
                            verify_data = await verify_resp.json()
                            if verify_data.get("rows"):
                                print(f"   Role verified: {verify_data['rows'][0]}")
                    
                    return True
                else:
                    print(f"❌ Failed to reset password: HTTP {resp.status}")
                    print(f"   Response: {text[:500]}")
                    
                    # Try to parse error details
                    try:
                        error_data = json.loads(text)
                        if "message" in error_data:
                            print(f"   Error: {error_data['message']}")
                    except:
                        pass
                    
                    return False
                    
        except Exception as e:
            print(f"❌ Exception during password reset: {e}")
            return False

async def fetch_connection_string():
    """Fetch the complete connection string after password reset"""
    
    endpoints_url = f"{BASE_URL}/projects/{NEON_PROJECT_ID}/endpoints"
    
    headers = {
        "Authorization": f"Bearer {NEON_API_KEY}",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoints_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                for endpoint in data.get("endpoints", []):
                    if endpoint.get("branch_id") == NEON_BRANCH_ID:
                        host = endpoint.get("host")
                        if host:
                            dsn = f"postgresql://{DEFAULT_USER}:{NEON_PASSWORD}@{host}:5432/{DEFAULT_DB}"
                            print(f"\n💾 Connection string after password reset:")
                            print(f"   {dsn}")
                            print(f"\n📝 Export this to use:")
                            print(f"   export NEON_DATABASE_URL='{dsn}'")
                            return dsn
    
    return None

async def main():
    """Main entry point"""
    
    print("=" * 60)
    print("Neon Password Reset Tool")
    print("=" * 60)
    
    # Check for API key
    if not NEON_API_KEY:
        print("❌ NEON_API_KEY is required")
        sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Reset Neon database role password")
    parser.add_argument("--role", default=DEFAULT_USER, help="Database role to reset")
    parser.add_argument("--password", default=NEON_PASSWORD, help="New password")
    parser.add_argument("--branch", default=NEON_BRANCH_ID, help="Branch ID")
    
    args = parser.parse_args()
    
    # Reset the password
    success = await reset_password(args.role, args.password, args.branch)
    
    if success:
        # Fetch and display connection string
        await fetch_connection_string()
        print("\n✅ Password reset complete!")
        sys.exit(0)
    else:
        print("\n❌ Password reset failed!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify NEON_API_KEY is correct")
        print("   2. Check if the role exists in the database")
        print("   3. Ensure you have permission to alter roles")
        print("   4. Try resetting through Neon console UI")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())