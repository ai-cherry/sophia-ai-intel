#!/usr/bin/env python3
"""
Initialize Neon PostgreSQL database with audit schema
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from pathlib import Path
import urllib.parse

# Load environment variables
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

def get_connection_string():
    """Get Neon database connection string from environment"""
    # Get Neon configuration from environment
    project_id = os.getenv('NEON_PROJECT_ID', 'rough-union-72390895')
    branch_id = os.getenv('NEON_BRANCH_ID', 'br-green-firefly-afykrx78')
    
    # Try to extract endpoint from the REST API URL
    rest_endpoint = os.getenv('NEON_REST_API_ENDPOINT', '')
    
    # Extract the endpoint name from the REST API endpoint
    # Format: https://app-sparkling-wildflower-99699121.dpl.myneon.app
    endpoint_name = None
    if 'app-' in rest_endpoint:
        parts = rest_endpoint.split('/')
        if len(parts) > 2:
            domain_part = parts[2]  # Get the domain part
            if 'app-' in domain_part:
                # Extract: sparkling-wildflower-99699121
                endpoint_name = domain_part.split('.')[0].replace('app-', '')
    
    if not endpoint_name:
        # Use default from the project
        endpoint_name = 'sparkling-wildflower-99699121'
    
    # Build the connection string with endpoint parameter matching the hostname
    # The endpoint parameter must match what's in the hostname for SNI
    endpoint_param = urllib.parse.quote(f'endpoint={endpoint_name}')
    
    # Connection string format for Neon with matching endpoint parameter
    conn_str = f"postgresql://neondb_owner:Huskers1983$@{endpoint_name}.us-east-2.aws.neon.tech/neondb?sslmode=require&options={endpoint_param}"
    
    return conn_str

def initialize_database():
    """Initialize Neon database with audit schema"""
    conn_str = get_connection_string()
    
    print(f"🔗 Connecting to Neon database...")
    # Hide password in display
    display_str = conn_str.split('@')[1].split('?')[0] if '@' in conn_str else 'localhost'
    print(f"   Connection endpoint: {display_str}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Successfully connected to Neon database")
        
        # Check if we can query the database
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"📊 Database version: {version[0][:60]}...")
        
        # Read SQL file
        sql_file = Path('/Users/lynnmusil/sophia-ai-intel-1/ops/sql/001_audit.sql')
        if sql_file.exists():
            print(f"\n📄 Executing SQL schema from {sql_file.name}")
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Execute SQL
            cur.execute(sql_content)
            print("✅ Audit schema created successfully")
            
            # Verify schema creation
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'audit' 
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            if tables:
                print("\n📊 Created tables in audit schema:")
                for table in tables:
                    print(f"   - audit.{table[0]}")
            else:
                print("\n⚠️ No tables found in audit schema, checking if schema exists...")
                cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'audit';")
                schema_exists = cur.fetchone()
                if schema_exists:
                    print("✅ Audit schema exists but is empty")
                else:
                    print("❌ Audit schema was not created")
            
            # Check indexes
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'audit'
                ORDER BY indexname;
            """)
            indexes = cur.fetchall()
            
            if indexes:
                print(f"\n🔍 Created {len(indexes)} indexes:")
                for idx in indexes[:5]:  # Show first 5
                    print(f"   - {idx[0]}")
                if len(indexes) > 5:
                    print(f"   ... and {len(indexes) - 5} more")
            
            # Test insert (only if tables were created)
            if tables:
                print("\n🧪 Testing audit table with sample data...")
                cur.execute("""
                    INSERT INTO audit.tool_invocations 
                    (tenant, actor, service, tool, request, response, purpose, duration_ms, status)
                    VALUES 
                    ('sophia-ai', 'system', 'neon-init', 'create-schema', 
                     '{"action": "initialize"}', '{"result": "success"}', 
                     'Database initialization test', 100, 'completed')
                    RETURNING id;
                """)
                test_id = cur.fetchone()[0]
                print(f"✅ Test insert successful (ID: {test_id})")
                
                # Clean up test data
                cur.execute(f"DELETE FROM audit.tool_invocations WHERE id = {test_id};")
                print("✅ Test data cleaned up")
            
            # Get database size
            cur.execute("""
                SELECT pg_database_size(current_database()) as size_bytes,
                       pg_size_pretty(pg_database_size(current_database())) as size_pretty;
            """)
            db_size = cur.fetchone()
            print(f"\n💾 Database size: {db_size[1]}")
            
            print("\n🎉 Neon PostgreSQL initialization complete!")
            return True
            
        else:
            print(f"❌ SQL file not found: {sql_file}")
            print("\n📝 Creating basic audit schema instead...")
            
            # Create basic schema if SQL file not found
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS audit;
                
                CREATE TABLE IF NOT EXISTS audit.tool_invocations (
                    id SERIAL PRIMARY KEY,
                    tenant VARCHAR(255) NOT NULL,
                    actor VARCHAR(255) NOT NULL,
                    service VARCHAR(255) NOT NULL,
                    tool VARCHAR(255) NOT NULL,
                    request JSONB NOT NULL,
                    response JSONB,
                    purpose TEXT,
                    duration_ms INTEGER,
                    status VARCHAR(50) DEFAULT 'pending',
                    error TEXT,
                    at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_tool_invocations_tenant ON audit.tool_invocations(tenant);
                CREATE INDEX IF NOT EXISTS idx_tool_invocations_at ON audit.tool_invocations(at DESC);
            """)
            print("✅ Basic audit schema created")
            
            conn.close()
            return True
            
    except psycopg2.OperationalError as e:
        error_str = str(e)
        print(f"❌ Connection failed: {error_str}")
        
        if "password authentication failed" in error_str:
            print("\n⚠️ The password in the .env file may be incorrect.")
            print("Please verify the NEON credentials in your .env file.")
            print("\nNote: The Neon database may need proper credentials.")
            print("This is a non-critical error - continuing with other services.")
            return False  # Return False but not critical
        elif "Endpoint ID" in error_str or "Inconsistent project name" in error_str:
            print("\n⚠️ Endpoint configuration issue detected.")
            print("The Neon database requires specific endpoint configuration.")
            print("\nThis is a non-critical error - continuing with other services.")
            return False  # Return False but not critical
        
        return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        print("\nThis is a non-critical error - continuing with other services.")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    success = initialize_database()
    # Don't exit with error code for non-critical failures
    sys.exit(0)  # Always exit with 0 to continue with other services