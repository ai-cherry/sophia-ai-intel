#!/usr/bin/env python3
"""
LLM Services Smoke Test Script
Tests OpenRouter embeddings and Portkey chat completions API connectivity.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        RESET_ALL = '\033[0m'

# Try importing required libraries
try:
    import aiohttp
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"{Fore.RED}❌ Missing required library: {e}")
    print(f"{Fore.YELLOW}Please install: pip install aiohttp requests python-dotenv")
    sys.exit(1)


@dataclass
class TestResult:
    """Result of a service test"""
    service: str
    success: bool
    message: str
    response_time: float
    details: Optional[Dict] = None


class LLMSmokeTester:
    """Test LLM service connectivity"""
    
    def __init__(self):
        """Initialize the tester with environment variables"""
        # Load environment variables
        env_path = Path("/Users/lynnmusil/sophia-ai-intel-1/.env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Get API keys
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        
        # API endpoints
        self.openrouter_base = "https://openrouter.ai/api/v1"
        self.portkey_base = "https://api.portkey.ai/v1"
        
        # Test configurations
        self.test_embedding_text = "This is a test message for embedding generation."
        self.test_chat_message = "Hello, this is a connectivity test. Please respond briefly."
        
        self.results: List[TestResult] = []
    
    def print_header(self):
        """Print test header"""
        print(f"\n{Style.BRIGHT}{'='*60}")
        print(f"{Style.BRIGHT}LLM Services Smoke Test")
        print(f"{Style.BRIGHT}{'='*60}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
    
    def print_result(self, result: TestResult):
        """Print a single test result"""
        status = f"{Fore.GREEN}✅ PASS" if result.success else f"{Fore.RED}❌ FAIL"
        print(f"\n{status} {result.service}")
        print(f"  Response Time: {result.response_time:.3f}s")
        print(f"  Message: {result.message}")
        if result.details:
            print(f"  Details: {json.dumps(result.details, indent=2)}")
    
    async def test_openrouter_embeddings(self) -> TestResult:
        """Test OpenRouter embeddings API"""
        service = "OpenRouter Embeddings (text-embedding-3-large)"
        
        if not self.openrouter_key:
            return TestResult(
                service=service,
                success=False,
                message="OPENROUTER_API_KEY not found in environment",
                response_time=0.0
            )
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                # OpenRouter embeddings endpoint
                url = f"{self.openrouter_base}/embeddings"
                
                payload = {
                    "model": "openai/text-embedding-3-large",
                    "input": self.test_embedding_text,
                    "encoding_format": "float"
                }
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        if "data" in data and len(data["data"]) > 0:
                            embedding = data["data"][0].get("embedding", [])
                            
                            return TestResult(
                                service=service,
                                success=True,
                                message=f"Successfully generated embedding (dimension: {len(embedding)})",
                                response_time=response_time,
                                details={
                                    "model": "text-embedding-3-large",
                                    "dimension": len(embedding),
                                    "usage": data.get("usage", {})
                                }
                            )
                        else:
                            return TestResult(
                                service=service,
                                success=False,
                                message="Invalid response structure",
                                response_time=response_time,
                                details={"response": data}
                            )
                    else:
                        error_text = await response.text()
                        return TestResult(
                            service=service,
                            success=False,
                            message=f"HTTP {response.status}: {error_text[:200]}",
                            response_time=response_time
                        )
                        
        except asyncio.TimeoutError:
            return TestResult(
                service=service,
                success=False,
                message="Request timeout (30s)",
                response_time=30.0
            )
        except Exception as e:
            return TestResult(
                service=service,
                success=False,
                message=f"Exception: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def test_portkey_chat(self) -> TestResult:
        """Test Portkey chat completions API"""
        service = "Portkey Chat Completions"
        
        if not self.portkey_key:
            return TestResult(
                service=service,
                success=False,
                message="PORTKEY_API_KEY not found in environment",
                response_time=0.0
            )
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-portkey-api-key": self.portkey_key,
                    "Content-Type": "application/json"
                }
                
                # Portkey chat completions endpoint
                url = f"{self.portkey_base}/chat/completions"
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant. Keep responses brief."
                        },
                        {
                            "role": "user",
                            "content": self.test_chat_message
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7
                }
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        if "choices" in data and len(data["choices"]) > 0:
                            message = data["choices"][0].get("message", {})
                            content = message.get("content", "")
                            
                            return TestResult(
                                service=service,
                                success=True,
                                message=f"Successfully received response: {content[:100]}...",
                                response_time=response_time,
                                details={
                                    "model": data.get("model", "unknown"),
                                    "usage": data.get("usage", {}),
                                    "response_length": len(content)
                                }
                            )
                        else:
                            return TestResult(
                                service=service,
                                success=False,
                                message="Invalid response structure",
                                response_time=response_time,
                                details={"response": data}
                            )
                    else:
                        error_text = await response.text()
                        return TestResult(
                            service=service,
                            success=False,
                            message=f"HTTP {response.status}: {error_text[:200]}",
                            response_time=response_time
                        )
                        
        except asyncio.TimeoutError:
            return TestResult(
                service=service,
                success=False,
                message="Request timeout (30s)",
                response_time=30.0
            )
        except Exception as e:
            return TestResult(
                service=service,
                success=False,
                message=f"Exception: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def run_tests_with_retry(self, test_func, max_retries: int = 3):
        """Run a test with retry logic"""
        for attempt in range(max_retries):
            result = await test_func()
            
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  {Fore.YELLOW}Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        return result
    
    async def run_all_tests(self):
        """Run all LLM service tests"""
        self.print_header()
        
        # Test OpenRouter Embeddings
        print(f"\n{Style.BRIGHT}Testing OpenRouter Embeddings...")
        result = await self.run_tests_with_retry(self.test_openrouter_embeddings)
        self.results.append(result)
        self.print_result(result)
        
        # Test Portkey Chat
        print(f"\n{Style.BRIGHT}Testing Portkey Chat Completions...")
        result = await self.run_tests_with_retry(self.test_portkey_chat)
        self.results.append(result)
        self.print_result(result)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        print(f"\n{Style.BRIGHT}{'='*60}")
        print(f"{Style.BRIGHT}Test Summary")
        print(f"{'='*60}")
        
        if failed == 0:
            print(f"{Fore.GREEN}✅ All tests passed! ({passed}/{total})")
        else:
            print(f"{Fore.YELLOW}⚠️  Some tests failed: {passed}/{total} passed, {failed}/{total} failed")
        
        # List failed services
        if failed > 0:
            print(f"\n{Fore.RED}Failed Services:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.service}: {result.message}")
        
        # Performance summary
        print(f"\n{Style.BRIGHT}Performance Summary:")
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            print(f"  {status_icon} {result.service}: {result.response_time:.3f}s")
        
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results)
        print(f"\nAverage Response Time: {avg_response_time:.3f}s")
        
        print(f"\n{'='*60}\n")
        
        # Return exit code
        return 0 if failed == 0 else 1


async def main():
    """Main entry point"""
    tester = LLMSmokeTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        sys.exit(1)