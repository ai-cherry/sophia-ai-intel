#!/usr/bin/env python3
# scripts/neon_passwordless_test.py
"""
Neon Passwordless Connection Test
Tests connection to Neon using their passwordless proxy at pg.neon.tech
"""

import os
import sys
import json
import asyncio
import asyncpg
import subprocess

# Environment configuration
NEON_PROJECT_ID = os.getenv("NEON_PROJECT_ID", "rough-union-72390895")
NEON_BRANCH_ID = os.getenv("NEON_BRANCH_ID", "br-green-firefly-afykrx78")
DEFAULT_USER = os.getenv("NEON_ROLE", "neondb_owner")
DEFAULT_DB = os.getenv("NEON_DB", "neondb")

# Neon passwordless proxy endpoint
NEON_PROXY_HOST = "pg.neon.tech"

async def test_passwordless_connection():
    """Test passwordless connection through Neon proxy"""
    
    print("=" * 60)
    print("Neon Passwordless Connection Test")
    print("=" * 60)
    
    print(f"\n📋 Configuration:")
    print(f"   Project ID: {NEON_PROJECT_ID}")
    print(f"   Branch ID: {NEON_BRANCH_ID}")
    print(f"   User: {DEFAULT_USER}")
    print(f"   Database: {DEFAULT_DB}")
    print(f"   Proxy Host: {NEON_PROXY_HOST}")
    
    # Build passwordless connection string
    # Format: postgresql://[user]@pg.neon.tech/[dbname]?options=project=[project-id]
    options = f"project={NEON_PROJECT_ID}"
    
    # Try different connection string formats
    connection_strings = [
        # Format 1: With project in options
        f"postgresql://{DEFAULT_USER}@{NEON_PROXY_HOST}/{DEFAULT_DB}?options={options}",
        
        # Format 2: With project and endpoint in options
        f"postgresql://{DEFAULT_USER}@{NEON_PROXY_HOST}/{DEFAULT_DB}?options=project={NEON_PROJECT_ID}%20endpoint={NEON_BRANCH_ID}",
        
        # Format 3: Simple format
        f"postgresql://{DEFAULT_USER}@{NEON_PROXY_HOST}/{DEFAULT_DB}",
        
        # Format 4: With SSL mode
        f"postgresql://{DEFAULT_USER}@{NEON_PROXY_HOST}/{DEFAULT_DB}?sslmode=require",
    ]
    
    for idx, dsn in enumerate(connection_strings, 1):
        print(f"\n🔗 Testing connection format {idx}:")
        print(f"   {dsn}")
        
        try:
            conn = await asyncpg.connect(dsn, timeout=10)
            
            # Test basic queries
            version = await conn.fetchval("SELECT version()")
            current_user = await conn.fetchval("SELECT current_user")
            current_db = await conn.fetchval("SELECT current_database()")
            
            await conn.close()
            
            print(f"   ✅ Connection successful!")
            print(f"   User: {current_user}")
            print(f"   Database: {current_db}")
            print(f"   Version: {version[:50]}...")
            
            return True, dsn
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
    
    return False, None

def test_psql_command():
    """Test connection using psql command line tool"""
    
    print("\n" + "=" * 60)
    print("Testing with psql command line tool")
    print("=" * 60)
    
    # Build psql command
    cmd = [
        "psql",
        "-h", NEON_PROXY_HOST,
        "-U", DEFAULT_USER,
        "-d", DEFAULT_DB,
        "--set", f"options=project={NEON_PROJECT_ID}",
        "-c", "SELECT current_user, current_database(), version();"
    ]
    
    print(f"\n🔧 Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"\n✅ psql connection successful!")
            print(f"Output:\n{result.stdout}")
            return True
        else:
            print(f"\n❌ psql connection failed!")
            print(f"Error:\n{result.stderr}")
            return False
            
    except FileNotFoundError:
        print("\n⚠️ psql not found. Install PostgreSQL client tools:")
        print("   macOS: brew install postgresql")
        print("   Linux: sudo apt-get install postgresql-client")
        return False
    except Exception as e:
        print(f"\n❌ Error running psql: {e}")
        return False

async def main():
    """Main entry point"""
    
    # Test asyncpg passwordless connection
    success, working_dsn = await test_passwordless_connection()
    
    if success:
        print(f"\n✅ Passwordless connection successful!")
        print(f"\n📝 Working DSN for asyncpg:")
        print(f"   {working_dsn}")
        print(f"\n📝 Export this environment variable:")
        print(f"   export NEON_DATABASE_URL='{working_dsn}'")
    
    # Test psql command line
    psql_success = test_psql_command()
    
    if not success and not psql_success:
        print("\n❌ All connection attempts failed!")
        print("\n💡 Troubleshooting steps:")
        print("   1. Check if you have access to the Neon project")
        print("   2. Verify project ID and branch ID are correct")
        print("   3. Try connecting through Neon console: https://console.neon.tech")
        print("   4. Check Neon documentation for passwordless auth setup")
        print("\n📚 Neon passwordless docs:")
        print("   https://neon.tech/docs/connect/passwordless-connect")
        sys.exit(1)
    else:
        print("\n✅ At least one connection method works!")
        print("\n📝 Next steps:")
        print("   1. Use passwordless connection for development")
        print("   2. Set up JWT/JWKS for production authentication")
        print("   3. Configure connection pooling for scalability")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())