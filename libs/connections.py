#!/usr/bin/env python3
"""
SDK Connection Library - Agent Infrastructure
============================================
Centralized SDK-first connections for all infrastructure components.
"""

import os
import asyncio
import json
import requests
from typing import Dict, Any

class ConnectionTester:
    """Test all infrastructure connections with SDKs"""
    
    def __init__(self):
        self.results = {}
    
    def test_qdrant(self) -> Dict[str, Any]:
        """Test Qdrant connection with qdrant-client"""
        try:
            from qdrant_client import QdrantClient
            
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            
            if not url or not api_key:
                return {"status": "failed", "error": "Missing QDRANT_URL or QDRANT_API_KEY"}
            
            client = QdrantClient(url=url, api_key=api_key)
            collections = client.get_collections()
            
            return {
                "status": "connected",
                "url": url,
                "collections_count": len(collections.collections),
                "test_success": True
            }
            
        except ImportError:
            return {"status": "failed", "error": "qdrant-client not installed"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_redis(self) -> Dict[str, Any]:
        """Test Redis connection with redis-py"""
        try:
            import redis
            
            # Use environment variable for Redis endpoint
            endpoint = os.getenv("REDIS_DATABASE_ENDPOINT", "redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com:15014")
            if ":" in endpoint:
                endpoint, port_str = endpoint.split(":")
                port = int(port_str)
            else:
                port = 15014
            
            # Try multiple password sources
            password = os.getenv("REDIS_PASSWORD") or os.getenv("REDIS_USER_KEY") or os.getenv("REDIS_ACCOUNT_KEY")
            
            if not endpoint or not password:
                return {"status": "failed", "error": "Redis credentials not configured"}
            
            client = redis.Redis(host=endpoint, port=port, password=password, username="default", db=0)
            ping_result = client.ping()
            
            return {
                "status": "connected",
                "endpoint": f"{endpoint}:{port}",
                "ping": ping_result,
                "test_success": True
            }
            
        except ImportError:
            return {"status": "failed", "error": "redis-py not installed"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def test_neon(self) -> Dict[str, Any]:
        """Test Neon connection with asyncpg"""
        try:
            import asyncpg
            
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return {"status": "failed", "error": "Missing DATABASE_URL"}
            
            conn = await asyncpg.connect(database_url)
            result = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return {
                "status": "connected",
                "database_url": database_url.split("@")[1] if "@" in database_url else "masked",
                "postgres_version": result.split()[1] if result else "unknown",
                "test_success": True
            }
            
        except ImportError:
            return {"status": "failed", "error": "asyncpg not installed"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_lambda_labs(self) -> Dict[str, Any]:
        """Test Lambda Labs API connection"""
        try:
            api_key = os.getenv("LAMBDA_CLOUD_API_KEY")
            if not api_key:
                return {"status": "failed", "error": "Missing LAMBDA_CLOUD_API_KEY"}
            
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://cloud.lambdalabs.com/api/v1/instances",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                instances = response.json()
                return {
                    "status": "connected",
                    "instances_count": len(instances.get("data", [])),
                    "test_success": True
                }
            else:
                return {"status": "failed", "error": f"API returned {response.status_code}"}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def test_mem0(self) -> Dict[str, Any]:
        """Test Mem0 API connection"""
        try:
            api_key = os.getenv("MEM0_API_KEY")
            if not api_key:
                return {"status": "failed", "error": "Missing MEM0_API_KEY"}
            
            # Test with requests since mem0 SDK may not be available
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.mem0.ai/v1/memories",
                headers=headers,
                params={"user_id": "test"},
                timeout=10
            )
            
            return {
                "status": "connected" if response.status_code in [200, 404] else "failed",
                "api_response": response.status_code,
                "test_success": response.status_code in [200, 404]
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test all infrastructure connections"""
        print("🔍 Testing all SDK connections...")
        
        results = {
            "qdrant": self.test_qdrant(),
            "redis": self.test_redis(),
            "neon": await self.test_neon(),
            "lambda_labs": self.test_lambda_labs(),
            "mem0": self.test_mem0()
        }
        
        # Summary
        connected = sum(1 for r in results.values() if r.get("test_success", False))
        total = len(results)
        
        summary = {
            "timestamp": "2025-08-24T02:47:00Z",
            "total_connections": total,
            "successful_connections": connected,
            "success_rate": f"{(connected/total)*100:.1f}%",
            "results": results
        }
        
        return summary


async def test_infrastructure_connections():
    """Main function to test all connections"""
    tester = ConnectionTester()
    return await tester.test_all_connections()


if __name__ == "__main__":
    import asyncio
    
    async def main():
        results = await test_infrastructure_connections()
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())
