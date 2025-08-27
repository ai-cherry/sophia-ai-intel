#!/usr/bin/env python3
# scripts/neon_fix_conn.py
"""
Neon Connection Troubleshooting Tool
Diagnoses connection issues and provides detailed error analysis
"""

import os
import sys
import json
import asyncio
import asyncpg
import aiohttp
from urllib.parse import urljoin

# Environment configuration with defaults
NEON_API_KEY            = os.getenv("NEON_API_KEY", "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby")
NEON_REST_API_ENDPOINT  = os.getenv("NEON_REST_API_ENDPOINT", "https://console.neon.tech/api/v2")
NEON_PROJECT_ID         = os.getenv("NEON_PROJECT_ID", "rough-union-72390895")
NEON_BRANCH_ID          = os.getenv("NEON_BRANCH_ID", "br-green-firefly-afykrx78")
NEON_PASSWORD           = os.getenv("NEON_PASSWORD", "Huskers1983$")
DEFAULT_USER            = os.getenv("NEON_ROLE", "neondb_owner")
DEFAULT_DB              = os.getenv("NEON_DB", "neondb")
DEFAULT_PORT            = int(os.getenv("NEON_PORT", "5432"))

def _normalize_base(base: str) -> str:
    """Normalize the REST API base URL"""
    b = base.strip().rstrip("/")
    if "/api/" not in b:
        if "console.neon.tech" not in b:
            return "https://console.neon.tech/api/v2"
        return b + "/api/v2"
    return b

BASE = _normalize_base(NEON_REST_API_ENDPOINT)

def dsn_from(host: str, user: str = DEFAULT_USER, db: str = DEFAULT_DB, password: str = NEON_PASSWORD) -> str:
    """Build PostgreSQL DSN from components"""
    return f"postgresql://{user}:{password}@{host}:{DEFAULT_PORT}/{db}"

async def _req(path: str):
    """Make authenticated request to Neon REST API"""
    if not NEON_API_KEY:
        raise RuntimeError("NEON_API_KEY is required to query REST")
    url = urljoin(BASE + "/", path.lstrip("/"))
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers={"Authorization": f"Bearer {NEON_API_KEY}", "Accept":"application/json"}) as r:
            txt = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"GET {url} -> {r.status} {txt[:240]}")
            return json.loads(txt) if txt else {}

async def fetch_readwrite_host():
    """Fetch the read-write endpoint host for the branch"""
    print(f"🔍 Fetching endpoints for project {NEON_PROJECT_ID}...")
    eps = await _req(f"projects/{NEON_PROJECT_ID}/endpoints")
    
    for ep in eps.get("endpoints", []):
        if ep.get("type") == "read_write" and ep.get("branch_id") == NEON_BRANCH_ID:
            host = ep.get("host")
            print(f"✅ Found read-write endpoint: {host}")
            return host
    
    print(f"❌ No read-write endpoint found for branch {NEON_BRANCH_ID}")
    return None

async def try_connect(dsn: str):
    """Try to connect to database and diagnose any issues"""
    print(f"🔗 Attempting connection...")
    print(f"   DSN: postgresql://{DEFAULT_USER}:***@{dsn.split('@')[1] if '@' in dsn else 'unknown'}")
    
    try:
        conn = await asyncpg.connect(dsn)
        who = await conn.fetchval("select current_user")
        host = await conn.fetchval("select inet_server_addr()::text")
        dbn = await conn.fetchval("select current_database()")
        await conn.close()
        
        result = {"ok": True, "user": who, "db": dbn, "host": host}
        print(f"✅ Connection successful!")
        print(f"   User: {who}")
        print(f"   Database: {dbn}")
        print(f"   Host: {host}")
        return result
        
    except asyncpg.InvalidPasswordError as e:
        print(f"❌ Password authentication failed")
        print(f"   Error: {e}")
        print(f"\n💡 Solution: Verify NEON_PASSWORD is correct")
        print(f"   Current password: {'*' * (len(NEON_PASSWORD) - 4)}{NEON_PASSWORD[-4:]}")
        return {"ok": False, "reason": "password", "detail": str(e)}
        
    except asyncpg.InvalidAuthorizationSpecificationError as e:
        print(f"❌ Role/authorization error")
        print(f"   Error: {e}")
        print(f"\n💡 Solution: Check if role '{DEFAULT_USER}' exists")
        return {"ok": False, "reason": "role", "detail": str(e)}
        
    except (asyncpg.InvalidCatalogNameError, asyncpg.UndefinedTableError) as e:
        print(f"❌ Database error")
        print(f"   Error: {e}")
        print(f"\n💡 Solution: Verify database '{DEFAULT_DB}' exists")
        return {"ok": False, "reason": "database", "detail": str(e)}
        
    except Exception as e:
        print(f"❌ Connection failed (network/host issue)")
        print(f"   Error: {e}")
        print(f"\n💡 Solution: Check if endpoint host is correct and accessible")
        return {"ok": False, "reason": "network/host", "detail": str(e)}

async def diagnose_full():
    """Run full diagnosis including fetching correct host"""
    print("=" * 60)
    print("Neon PostgreSQL Connection Diagnostics")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Configuration:")
    print(f"   NEON_PROJECT_ID: {NEON_PROJECT_ID}")
    print(f"   NEON_BRANCH_ID: {NEON_BRANCH_ID}")
    print(f"   NEON_ROLE: {DEFAULT_USER}")
    print(f"   NEON_DB: {DEFAULT_DB}")
    print(f"   REST API: {BASE}")
    
    # Try to fetch the correct host
    print("\n🌐 Fetching correct endpoint from Neon REST API...")
    try:
        host = await fetch_readwrite_host()
        if not host:
            print("\n⚠️ Could not find endpoint. You may need to create one:")
            print(f"   python scripts/neon_rest.py endpoint-create")
            return {"ok": False, "reason": "no_endpoint"}
    except Exception as e:
        print(f"\n❌ Failed to fetch endpoint: {e}")
        print("\n💡 Check:")
        print("   1. NEON_API_KEY is valid")
        print("   2. NEON_PROJECT_ID is correct")
        print("   3. Network connectivity to console.neon.tech")
        return {"ok": False, "reason": "api_error", "detail": str(e)}
    
    # Build DSN and test connection
    dsn = dsn_from(host)
    print(f"\n📝 Built DSN from fetched host")
    
    result = await try_connect(dsn)
    
    # Save working DSN if successful
    if result["ok"]:
        print(f"\n💾 Working DSN (save this to NEON_DATABASE_URL):")
        print(f"   {dsn}")
    
    return result

async def main():
    """Main entry point"""
    dsn = os.getenv("NEON_DATABASE_URL", "")
    
    if dsn:
        # If DSN is provided, test it directly
        print("🔍 Testing provided NEON_DATABASE_URL...")
        result = await try_connect(dsn)
    else:
        # Run full diagnosis
        result = await diagnose_full()
    
    # Output JSON result for scripting
    print("\n📊 JSON Result:")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("ok") else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(2)