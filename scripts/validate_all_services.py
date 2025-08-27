#!/usr/bin/env python3
"""
Comprehensive External Services Validation Script
Tests all external service integrations for the Sophia AI platform.
"""

import os
import sys
import json
import asyncio
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add color support
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    # Fallback if colorama is not installed
    class Fore:
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        RESET_ALL = '\033[0m'

# Try importing required libraries
try:
    import aiohttp
    import requests
    import psycopg2
    import redis
    from dotenv import load_dotenv
except ImportError as e:
    print(f"{Fore.RED}❌ Missing required library: {e}")
    print(f"{Fore.YELLOW}Please install: pip install aiohttp requests psycopg2-binary redis python-dotenv")
    sys.exit(1)

# Try importing Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.exceptions import UnexpectedResponse
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print(f"{Fore.YELLOW}⚠️  Qdrant client not available. Install with: pip install qdrant-client")


@dataclass
class ServiceTest:
    """Result of a service test"""
    category: str
    service: str
    success: bool
    message: str
    response_time: float
    details: Optional[Dict] = None


class ComprehensiveValidator:
    """Validates all external service integrations"""
    
    def __init__(self):
        """Initialize the validator with environment variables"""
        # Load environment variables
        env_path = Path("/Users/lynnmusil/sophia-ai-intel-1/.env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Database configurations
        self.neon_url = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # LLM configurations
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        
        # Lambda Labs configuration
        self.lambda_key = os.getenv("LAMBDA_API_KEY")
        self.lambda_endpoint = os.getenv("LAMBDA_CLOUD_ENDPOINT", "https://cloud.lambdalabs.com/api/v1")
        
        # Test results storage
        self.results: List[ServiceTest] = []
    
    def print_header(self):
        """Print validation header"""
        print(f"\n{Style.BRIGHT}{'='*70}")
        print(f"{Style.BRIGHT}SOPHIA AI - Comprehensive Service Validation")
        print(f"{Style.BRIGHT}{'='*70}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"{'='*70}\n")
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'─'*60}")
        print(f"{Style.BRIGHT}{Fore.CYAN}{title}")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'─'*60}")
    
    def print_result(self, result: ServiceTest):
        """Print a single test result"""
        status = f"{Fore.GREEN}✅" if result.success else f"{Fore.RED}❌"
        print(f"{status} {result.service}: {result.message} ({result.response_time:.3f}s)")
        if result.details and not result.success:
            print(f"   Details: {json.dumps(result.details, indent=2)}")
    
    # ========== DATABASE TESTS ==========
    
    async def test_neon_database(self) -> ServiceTest:
        """Test Neon PostgreSQL database connectivity"""
        start_time = time.time()
        
        if not self.neon_url:
            return ServiceTest(
                category="Database",
                service="Neon PostgreSQL",
                success=False,
                message="DATABASE_URL not found in environment",
                response_time=0.0
            )
        
        try:
            # Connect to database
            conn = psycopg2.connect(self.neon_url)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return ServiceTest(
                category="Database",
                service="Neon PostgreSQL",
                success=True,
                message=f"Connected successfully, {table_count} tables found",
                response_time=time.time() - start_time,
                details={"version": version.split("\n")[0], "tables": table_count}
            )
            
        except Exception as e:
            return ServiceTest(
                category="Database",
                service="Neon PostgreSQL",
                success=False,
                message=f"Connection failed: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    async def test_qdrant_vector_db(self) -> ServiceTest:
        """Test Qdrant vector database connectivity"""
        start_time = time.time()
        
        if not QDRANT_AVAILABLE:
            return ServiceTest(
                category="Database",
                service="Qdrant Vector DB",
                success=False,
                message="Qdrant client library not installed",
                response_time=0.0
            )
        
        try:
            # Initialize client
            client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                timeout=10
            )
            
            # Get collections
            collections = client.get_collections()
            collection_count = len(collections.collections)
            
            # Get cluster info
            info = client.get_cluster_info()
            
            return ServiceTest(
                category="Database",
                service="Qdrant Vector DB",
                success=True,
                message=f"Connected successfully, {collection_count} collections found",
                response_time=time.time() - start_time,
                details={
                    "collections": collection_count,
                    "status": "healthy"
                }
            )
            
        except Exception as e:
            return ServiceTest(
                category="Database",
                service="Qdrant Vector DB",
                success=False,
                message=f"Connection failed: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    async def test_redis_cache(self) -> ServiceTest:
        """Test Redis cache connectivity"""
        start_time = time.time()
        
        try:
            # Parse Redis URL
            if self.redis_url.startswith("redis://"):
                url_parts = self.redis_url.replace("redis://", "").split(":")
                host = url_parts[0]
                port = int(url_parts[1].split("/")[0]) if len(url_parts) > 1 else 6379
            else:
                host = "localhost"
                port = 6379
            
            # Connect to Redis
            r = redis.Redis(host=host, port=port, decode_responses=True, socket_timeout=5)
            
            # Ping test
            r.ping()
            
            # Get info
            info = r.info()
            version = info.get("redis_version", "unknown")
            used_memory = info.get("used_memory_human", "unknown")
            
            # Test set/get
            test_key = "sophia_test_key"
            test_value = f"test_{int(time.time())}"
            r.set(test_key, test_value, ex=10)  # Expire in 10 seconds
            retrieved = r.get(test_key)
            
            if retrieved != test_value:
                raise ValueError("Set/Get test failed")
            
            return ServiceTest(
                category="Database",
                service="Redis Cache",
                success=True,
                message=f"Connected successfully (v{version}, memory: {used_memory})",
                response_time=time.time() - start_time,
                details={
                    "version": version,
                    "memory_usage": used_memory,
                    "connected_clients": info.get("connected_clients", 0)
                }
            )
            
        except Exception as e:
            return ServiceTest(
                category="Database",
                service="Redis Cache",
                success=False,
                message=f"Connection failed: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    # ========== LLM SERVICE TESTS ==========
    
    async def test_openrouter_llm(self) -> ServiceTest:
        """Test OpenRouter LLM service"""
        start_time = time.time()
        
        if not self.openrouter_key:
            return ServiceTest(
                category="LLM",
                service="OpenRouter",
                success=False,
                message="OPENROUTER_API_KEY not found",
                response_time=0.0
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                # Test with a simple embeddings request
                url = "https://openrouter.ai/api/v1/embeddings"
                payload = {
                    "model": "openai/text-embedding-3-small",
                    "input": "Test connection"
                }
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ServiceTest(
                            category="LLM",
                            service="OpenRouter",
                            success=True,
                            message="API responding correctly",
                            response_time=time.time() - start_time,
                            details={"model": "text-embedding-3-small", "status": "operational"}
                        )
                    else:
                        error_text = await response.text()
                        return ServiceTest(
                            category="LLM",
                            service="OpenRouter",
                            success=False,
                            message=f"HTTP {response.status}",
                            response_time=time.time() - start_time,
                            details={"error": error_text[:200]}
                        )
                        
        except asyncio.TimeoutError:
            return ServiceTest(
                category="LLM",
                service="OpenRouter",
                success=False,
                message="Request timeout",
                response_time=15.0
            )
        except Exception as e:
            return ServiceTest(
                category="LLM",
                service="OpenRouter",
                success=False,
                message=f"Error: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    async def test_portkey_llm(self) -> ServiceTest:
        """Test Portkey LLM service"""
        start_time = time.time()
        
        if not self.portkey_key:
            return ServiceTest(
                category="LLM",
                service="Portkey",
                success=False,
                message="PORTKEY_API_KEY not found",
                response_time=0.0
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-portkey-api-key": self.portkey_key,
                    "Content-Type": "application/json"
                }
                
                # Test with a minimal chat completion
                url = "https://api.portkey.ai/v1/chat/completions"
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                }
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        return ServiceTest(
                            category="LLM",
                            service="Portkey",
                            success=True,
                            message="API responding correctly",
                            response_time=time.time() - start_time,
                            details={"model": "gpt-4o-mini", "status": "operational"}
                        )
                    else:
                        error_text = await response.text()
                        return ServiceTest(
                            category="LLM",
                            service="Portkey",
                            success=False,
                            message=f"HTTP {response.status}",
                            response_time=time.time() - start_time,
                            details={"error": error_text[:200]}
                        )
                        
        except asyncio.TimeoutError:
            return ServiceTest(
                category="LLM",
                service="Portkey",
                success=False,
                message="Request timeout",
                response_time=15.0
            )
        except Exception as e:
            return ServiceTest(
                category="LLM",
                service="Portkey",
                success=False,
                message=f"Error: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    # ========== INFRASTRUCTURE TESTS ==========
    
    async def test_lambda_labs(self) -> ServiceTest:
        """Test Lambda Labs API"""
        start_time = time.time()
        
        if not self.lambda_key:
            return ServiceTest(
                category="Infrastructure",
                service="Lambda Labs",
                success=False,
                message="LAMBDA_API_KEY not found",
                response_time=0.0
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.lambda_key}",
                "Content-Type": "application/json"
            }
            
            # Test by getting instance types
            url = f"{self.lambda_endpoint}/instance-types"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                instance_count = len(data.get("data", {}))
                
                return ServiceTest(
                    category="Infrastructure",
                    service="Lambda Labs",
                    success=True,
                    message=f"API active, {instance_count} instance types available",
                    response_time=time.time() - start_time,
                    details={"instance_types": instance_count}
                )
            else:
                return ServiceTest(
                    category="Infrastructure",
                    service="Lambda Labs",
                    success=False,
                    message=f"HTTP {response.status_code}",
                    response_time=time.time() - start_time
                )
                
        except requests.Timeout:
            return ServiceTest(
                category="Infrastructure",
                service="Lambda Labs",
                success=False,
                message="Request timeout",
                response_time=10.0
            )
        except Exception as e:
            return ServiceTest(
                category="Infrastructure",
                service="Lambda Labs",
                success=False,
                message=f"Error: {str(e)[:100]}",
                response_time=time.time() - start_time
            )
    
    # ========== MAIN VALIDATION FLOW ==========
    
    async def run_category_tests(self, category: str, tests: List):
        """Run tests for a specific category"""
        self.print_section(f"{category} Services")
        
        for test_func in tests:
            result = await test_func()
            self.results.append(result)
            self.print_result(result)
            
            # Small delay between tests
            await asyncio.sleep(0.1)
    
    async def run_all_validations(self):
        """Run all service validations"""
        self.print_header()
        
        # Database tests
        await self.run_category_tests("Database", [
            self.test_neon_database,
            self.test_qdrant_vector_db,
            self.test_redis_cache
        ])
        
        # LLM service tests
        await self.run_category_tests("LLM", [
            self.test_openrouter_llm,
            self.test_portkey_llm
        ])
        
        # Infrastructure tests
        await self.run_category_tests("Infrastructure", [
            self.test_lambda_labs
        ])
        
        # Print summary
        self.print_summary()
        
        # Return exit code based on results
        failed = sum(1 for r in self.results if not r.success)
        return 0 if failed == 0 else 1
    
    def print_summary(self):
        """Print validation summary"""
        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Print summary header
        print(f"\n{Style.BRIGHT}{'='*70}")
        print(f"{Style.BRIGHT}VALIDATION SUMMARY")
        print(f"{Style.BRIGHT}{'='*70}")
        
        # Overall statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Category breakdown
        print(f"\n{Style.BRIGHT}Service Categories:")
        for category, results in categories.items():
            cat_passed = sum(1 for r in results if r.success)
            cat_total = len(results)
            status = f"{Fore.GREEN}✅" if cat_passed == cat_total else f"{Fore.YELLOW}⚠️"
            print(f"  {status} {category}: {cat_passed}/{cat_total} services operational")
            
            # List failed services in category
            failed_services = [r for r in results if not r.success]
            if failed_services:
                for service in failed_services:
                    print(f"      {Fore.RED}❌ {service.service}: {service.message}")
        
        # Overall health status
        print(f"\n{Style.BRIGHT}Overall System Health:")
        if failed == 0:
            health_status = f"{Fore.GREEN}✅ HEALTHY"
            health_msg = "All external services are operational"
        elif failed <= 2:
            health_status = f"{Fore.YELLOW}⚠️  DEGRADED"
            health_msg = f"{failed} service(s) unavailable"
        else:
            health_status = f"{Fore.RED}❌ CRITICAL"
            health_msg = f"{failed} services failing"
        
        print(f"  Status: {health_status}")
        print(f"  {health_msg}")
        print(f"  Pass Rate: {pass_rate:.1f}% ({passed}/{total})")
        
        # Performance metrics
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results) if self.results else 0
        slowest = max(self.results, key=lambda r: r.response_time) if self.results else None
        
        print(f"\n{Style.BRIGHT}Performance Metrics:")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        if slowest:
            print(f"  Slowest Service: {slowest.service} ({slowest.response_time:.3f}s)")
        
        # Recommendations
        if failed > 0:
            print(f"\n{Style.BRIGHT}{Fore.YELLOW}Recommendations:")
            
            # Check for missing credentials
            missing_creds = [r for r in self.results if "not found" in r.message.lower()]
            if missing_creds:
                print(f"  • Set missing environment variables:")
                for cred in missing_creds:
                    if "OpenRouter" in cred.service:
                        print(f"    - OPENROUTER_API_KEY")
                    elif "Portkey" in cred.service:
                        print(f"    - PORTKEY_API_KEY")
                    elif "Lambda" in cred.service:
                        print(f"    - LAMBDA_API_KEY")
                    elif "Neon" in cred.service:
                        print(f"    - DATABASE_URL or NEON_DATABASE_URL")
            
            # Check for connection failures
            conn_failures = [r for r in self.results if "connection" in r.message.lower() or "timeout" in r.message.lower()]
            if conn_failures:
                print(f"  • Check network connectivity and service endpoints")
                print(f"  • Verify firewall rules allow outbound connections")
                print(f"  • Ensure services are running and accessible")
        
        print(f"\n{'='*70}")
        print(f"Validation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")


async def main():
    """Main entry point"""
    validator = ComprehensiveValidator()
    exit_code = await validator.run_all_validations()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)