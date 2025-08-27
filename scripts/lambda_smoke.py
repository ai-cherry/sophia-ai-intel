#!/usr/bin/env python3
"""
Lambda Labs API Smoke Test Script
Tests Lambda Labs cloud API connectivity and functionality.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
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
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"{Fore.RED}❌ Missing required library: {e}")
    print(f"{Fore.YELLOW}Please install: pip install requests python-dotenv")
    sys.exit(1)


@dataclass
class TestResult:
    """Result of a Lambda Labs API test"""
    test_name: str
    success: bool
    message: str
    response_time: float
    details: Optional[Dict] = None


class LambdaLabsSmokeTester:
    """Test Lambda Labs API connectivity and functionality"""
    
    def __init__(self):
        """Initialize the tester with environment variables"""
        # Load environment variables
        env_path = Path("/Users/lynnmusil/sophia-ai-intel-1/.env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Get API configuration
        self.api_key = os.getenv("LAMBDA_API_KEY")
        self.api_endpoint = os.getenv("LAMBDA_CLOUD_ENDPOINT", "https://cloud.lambdalabs.com/api/v1")
        
        # Ensure endpoint doesn't have trailing slash
        self.api_endpoint = self.api_endpoint.rstrip("/")
        
        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json"
        }
        
        # Test results storage
        self.results: List[TestResult] = []
        
        # Target region for GH200 availability check
        self.target_region = "us-west-1"
        self.target_instance_type = "gpu_8x_h100_sxm5"  # GH200 instance type
    
    def print_header(self):
        """Print test header"""
        print(f"\n{Style.BRIGHT}{'='*60}")
        print(f"{Style.BRIGHT}Lambda Labs API Smoke Test")
        print(f"{Style.BRIGHT}{'='*60}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Endpoint: {self.api_endpoint}")
        print(f"{'='*60}\n")
    
    def print_result(self, result: TestResult):
        """Print a single test result"""
        status = f"{Fore.GREEN}✅ PASS" if result.success else f"{Fore.RED}❌ FAIL"
        print(f"\n{status} {result.test_name}")
        print(f"  Response Time: {result.response_time:.3f}s")
        print(f"  Message: {result.message}")
        if result.details:
            print(f"  Details:")
            self._print_details(result.details, indent=4)
    
    def _print_details(self, details: Any, indent: int = 0):
        """Pretty print details with proper indentation"""
        prefix = " " * indent
        
        if isinstance(details, dict):
            for key, value in details.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{key}:")
                    self._print_details(value, indent + 2)
                else:
                    print(f"{prefix}{key}: {value}")
        elif isinstance(details, list):
            for i, item in enumerate(details):
                if isinstance(item, dict):
                    print(f"{prefix}[{i}]:")
                    self._print_details(item, indent + 2)
                else:
                    print(f"{prefix}- {item}")
        else:
            print(f"{prefix}{details}")
    
    def test_list_instances(self) -> TestResult:
        """Test listing existing instances"""
        test_name = "List Existing Instances"
        
        if not self.api_key:
            return TestResult(
                test_name=test_name,
                success=False,
                message="LAMBDA_API_KEY not found in environment",
                response_time=0.0
            )
        
        start_time = time.time()
        
        try:
            url = f"{self.api_endpoint}/instances"
            response = requests.get(url, headers=self.headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                instances = data.get("data", [])
                
                instance_info = []
                for instance in instances:
                    instance_info.append({
                        "id": instance.get("id"),
                        "name": instance.get("name"),
                        "status": instance.get("status"),
                        "instance_type": instance.get("instance_type", {}).get("name"),
                        "region": instance.get("region", {}).get("name"),
                        "ip": instance.get("ip_address")
                    })
                
                return TestResult(
                    test_name=test_name,
                    success=True,
                    message=f"Successfully listed {len(instances)} instance(s)",
                    response_time=response_time,
                    details={"instances": instance_info} if instance_info else {"message": "No active instances"}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time=response_time
                )
                
        except requests.Timeout:
            return TestResult(
                test_name=test_name,
                success=False,
                message="Request timeout (30s)",
                response_time=30.0
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Exception: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def test_list_instance_types(self) -> TestResult:
        """Test listing available instance types"""
        test_name = "List Available Instance Types"
        
        if not self.api_key:
            return TestResult(
                test_name=test_name,
                success=False,
                message="LAMBDA_API_KEY not found in environment",
                response_time=0.0
            )
        
        start_time = time.time()
        
        try:
            url = f"{self.api_endpoint}/instance-types"
            response = requests.get(url, headers=self.headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                instance_types = data.get("data", {})
                
                # Extract and format instance type information
                type_info = []
                for type_key, type_data in instance_types.items():
                    regions_available = type_data.get("regions_with_capacity_available", [])
                    
                    type_info.append({
                        "name": type_key,
                        "price_per_hour": type_data.get("instance_type", {}).get("price_cents_per_hour", 0) / 100,
                        "specs": type_data.get("instance_type", {}).get("specs", {}),
                        "available_regions": [r.get("name") for r in regions_available]
                    })
                
                # Sort by price
                type_info.sort(key=lambda x: x["price_per_hour"])
                
                return TestResult(
                    test_name=test_name,
                    success=True,
                    message=f"Successfully listed {len(type_info)} instance type(s)",
                    response_time=response_time,
                    details={"instance_types": type_info[:5]}  # Show top 5 for brevity
                )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time=response_time
                )
                
        except requests.Timeout:
            return TestResult(
                test_name=test_name,
                success=False,
                message="Request timeout (30s)",
                response_time=30.0
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Exception: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def test_gh200_availability(self) -> TestResult:
        """Check GH200 availability in us-west region"""
        test_name = f"Check GH200 Availability in {self.target_region}"
        
        if not self.api_key:
            return TestResult(
                test_name=test_name,
                success=False,
                message="LAMBDA_API_KEY not found in environment",
                response_time=0.0
            )
        
        start_time = time.time()
        
        try:
            url = f"{self.api_endpoint}/instance-types"
            response = requests.get(url, headers=self.headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                instance_types = data.get("data", {})
                
                # Look for GH200 instance types
                gh200_types = []
                for type_key, type_data in instance_types.items():
                    # Check if it's a GH200 or H100 type (high-performance GPUs)
                    if "h100" in type_key.lower() or "gh200" in type_key.lower() or "8x" in type_key:
                        regions = type_data.get("regions_with_capacity_available", [])
                        region_names = [r.get("name") for r in regions]
                        
                        gh200_types.append({
                            "type": type_key,
                            "available": self.target_region in region_names,
                            "regions": region_names,
                            "price_per_hour": type_data.get("instance_type", {}).get("price_cents_per_hour", 0) / 100,
                            "specs": type_data.get("instance_type", {}).get("specs", {})
                        })
                
                # Check if any GH200-class instances are available in target region
                available_in_region = [t for t in gh200_types if t["available"]]
                
                if available_in_region:
                    return TestResult(
                        test_name=test_name,
                        success=True,
                        message=f"Found {len(available_in_region)} GH200-class instance(s) available in {self.target_region}",
                        response_time=response_time,
                        details={"available_types": available_in_region}
                    )
                elif gh200_types:
                    return TestResult(
                        test_name=test_name,
                        success=False,
                        message=f"GH200-class instances found but not available in {self.target_region}",
                        response_time=response_time,
                        details={"gh200_types": gh200_types}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        success=False,
                        message="No GH200-class instances found",
                        response_time=response_time
                    )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time=response_time
                )
                
        except requests.Timeout:
            return TestResult(
                test_name=test_name,
                success=False,
                message="Request timeout (30s)",
                response_time=30.0
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Exception: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def print_launch_example(self):
        """Print commented launch example"""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'='*60}")
        print(f"{Style.BRIGHT}{Fore.CYAN}Launch Instance Example (Commented)")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'='*60}")
        print(f"""
{Fore.YELLOW}# Example code to launch a Lambda Labs instance:
{Fore.YELLOW}# Uncomment and run to actually launch an instance

{Fore.MAGENTA}'''
import requests
import os

# Configuration
api_key = os.getenv("LAMBDA_API_KEY")
api_endpoint = "https://cloud.lambdalabs.com/api/v1"

# Launch parameters
launch_config = {{
    "region_name": "us-west-1",
    "instance_type_name": "gpu_1x_a100_sxm4",  # Or "gpu_8x_h100_sxm5" for GH200
    "ssh_key_names": ["your-ssh-key-name"],  # Must be pre-registered
    "file_system_names": [],  # Optional persistent storage
    "quantity": 1,
    "name": "sophia-ai-gpu-node"
}}

# Make the request
headers = {{
    "Authorization": f"Bearer {{api_key}}",
    "Content-Type": "application/json"
}}

response = requests.post(
    f"{{api_endpoint}}/instance-operations/launch",
    headers=headers,
    json=launch_config
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Instance launched successfully!")
    print(f"Instance ID: {{result['data']['instance_ids'][0]}}")
else:
    print(f"❌ Failed to launch: {{response.text}}")
'''
{Fore.MAGENTA}

{Fore.YELLOW}# Important notes:
{Fore.YELLOW}# 1. SSH keys must be registered first via the Lambda Labs dashboard
{Fore.YELLOW}# 2. Instance charges begin immediately upon launch
{Fore.YELLOW}# 3. Remember to terminate instances when done to avoid charges
{Fore.YELLOW}# 4. GH200 instances may have limited availability

{Fore.CYAN}# To terminate an instance:
{Fore.MAGENTA}'''
instance_id = "your-instance-id"
response = requests.post(
    f"{{api_endpoint}}/instance-operations/terminate",
    headers=headers,
    json={{"instance_ids": [instance_id]}}
)
'''
""")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'='*60}\n")
    
    def run_tests_with_retry(self, test_func, max_retries: int = 3) -> TestResult:
        """Run a test with retry logic"""
        for attempt in range(max_retries):
            result = test_func()
            
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  {Fore.YELLOW}Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        return result
    
    def run_all_tests(self):
        """Run all Lambda Labs API tests"""
        self.print_header()
        
        if not self.api_key:
            print(f"{Fore.RED}❌ LAMBDA_API_KEY not found in environment")
            print(f"{Fore.YELLOW}Please set the LAMBDA_API_KEY environment variable")
            return 1
        
        # Test 1: List existing instances
        print(f"\n{Style.BRIGHT}Testing: List Existing Instances...")
        result = self.run_tests_with_retry(self.test_list_instances)
        self.results.append(result)
        self.print_result(result)
        
        # Test 2: List available instance types
        print(f"\n{Style.BRIGHT}Testing: List Available Instance Types...")
        result = self.run_tests_with_retry(self.test_list_instance_types)
        self.results.append(result)
        self.print_result(result)
        
        # Test 3: Check GH200 availability
        print(f"\n{Style.BRIGHT}Testing: GH200 Availability Check...")
        result = self.run_tests_with_retry(self.test_gh200_availability)
        self.results.append(result)
        self.print_result(result)
        
        # Print launch example
        self.print_launch_example()
        
        # Print summary
        self.print_summary()
        
        # Return exit code
        failed = sum(1 for r in self.results if not r.success)
        return 0 if failed == 0 else 1
    
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
        
        # List failed tests
        if failed > 0:
            print(f"\n{Fore.RED}Failed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.message}")
        
        # Performance summary
        print(f"\n{Style.BRIGHT}Performance Summary:")
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            print(f"  {status_icon} {result.test_name}: {result.response_time:.3f}s")
        
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results) if self.results else 0
        print(f"\nAverage Response Time: {avg_response_time:.3f}s")
        
        print(f"\n{'='*60}\n")


def main():
    """Main entry point"""
    tester = LambdaLabsSmokeTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)