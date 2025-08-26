#!/usr/bin/env python3
"""
Comprehensive External API Connectivity Testing for Sophia AI Stack

This script tests connectivity to all 6 external services:
1. Lambda Labs - GPU cloud infrastructure
2. Qdrant - Vector database
3. Redis - Caching and session storage
4. OpenRouter - LLM routing and management
5. GitHub - Repository and API management
6. HubSpot - CRM and business automation

Features:
- Comprehensive authentication validation
- Response time measurement
- Retry logic for transient failures
- Detailed error logging and diagnostics
- Success/failure rate tracking
- Performance metrics collection
"""

import os
import json
import time
import asyncio
import aiohttp
import redis
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from urllib.parse import urlparse
import ssl
import socket
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('external_api_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Data class for storing individual test results"""
    service_name: str
    test_type: str
    status: str
    response_time: float
    error_message: Optional[str] = None
    http_status: Optional[int] = None
    details: Optional[Dict] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

@dataclass
class ServiceMetrics:
    """Data class for service-level metrics"""
    service_name: str
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    error_types: List[str] = None

    def __post_init__(self):
        if self.error_types is None:
            self.error_types = []

class ExternalAPIConnectivityTester:
    """Main class for testing external API connectivity"""

    def __init__(self):
        """Initialize the tester with environment variables"""
        self.load_environment_variables()
        self.results: List[TestResult] = []
        self.metrics: Dict[str, ServiceMetrics] = {}
        self.retry_attempts = 3
        self.retry_delay = 2

    def load_environment_variables(self):
        """Load all required environment variables"""
        # Lambda Labs
        self.lambda_api_key = os.getenv('LAMBDA_API_KEY')
        self.lambda_endpoint = os.getenv('LAMBDA_CLOUD_ENDPOINT', 'https://cloud.lambdalabs.com/api/v1')

        # Qdrant
        self.qdrant_url = os.getenv('QDRANT_URL')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')

        # Redis
        self.redis_url = os.getenv('REDIS_URL')
        self.redis_host = os.getenv('REDIS_HOST')
        self.redis_port = os.getenv('REDIS_PORT')
        self.redis_username = os.getenv('REDIS_USERNAME')
        self.redis_password = os.getenv('REDIS_PASSWORD')

        # OpenRouter
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

        # GitHub
        self.github_token = os.getenv('GH_PAT_TOKEN')

        # HubSpot
        self.hubspot_token = os.getenv('HUBSPOT_ACCESS_TOKEN')

        logger.info("Environment variables loaded successfully")

    def update_metrics(self, result: TestResult):
        """Update service metrics based on test result"""
        service = result.service_name
        if service not in self.metrics:
            self.metrics[service] = ServiceMetrics(service_name=service)

        metrics = self.metrics[service]
        metrics.total_tests += 1

        if result.status == 'success':
            metrics.successful_tests += 1
            metrics.last_success = result.timestamp
        else:
            metrics.failed_tests += 1
            metrics.last_failure = result.timestamp
            if result.error_message and result.error_message not in metrics.error_types:
                metrics.error_types.append(result.error_message)

        # Update response time metrics
        if result.response_time > 0:
            metrics.average_response_time = (
                (metrics.average_response_time * (metrics.total_tests - 1)) + result.response_time
            ) / metrics.total_tests
            metrics.min_response_time = min(metrics.min_response_time, result.response_time)
            metrics.max_response_time = max(metrics.max_response_time, result.response_time)

    async def make_request_with_retry(self, session: aiohttp.ClientSession, url: str,
                                    method: str = 'GET', headers: Dict = None,
                                    data: Dict = None, timeout: int = 30) -> Tuple[Dict, float]:
        """Make HTTP request with retry logic"""
        start_time = time.time()

        for attempt in range(self.retry_attempts):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()

                    try:
                        json_data = json.loads(response_data) if response_data else {}
                    except json.JSONDecodeError:
                        json_data = {"raw_response": response_data}

                    return {
                        "status_code": response.status,
                        "response": json_data,
                        "headers": dict(response.headers),
                        "response_time": response_time
                    }, response_time

            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                continue
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1} for {url}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                continue

        response_time = time.time() - start_time
        return {
            "status_code": 0,
            "response": {"error": "All retry attempts failed"},
            "headers": {},
            "response_time": response_time
        }, response_time

    async def test_lambda_labs(self) -> List[TestResult]:
        """Test Lambda Labs API connectivity"""
        results = []
        service_name = "Lambda Labs"

        if not self.lambda_api_key:
            result = TestResult(
                service_name=service_name,
                test_type="Authentication Check",
                status="failed",
                response_time=0.0,
                error_message="LAMBDA_API_KEY not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        async with aiohttp.ClientSession() as session:
            # Test 1: Get instances
            headers = {
                'Authorization': f'Bearer {self.lambda_api_key}',
                'Content-Type': 'application/json'
            }

            response, response_time = await self.make_request_with_retry(
                session, f"{self.lambda_endpoint}/instances", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get Instances",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

            # Test 2: Get instance types
            response, response_time = await self.make_request_with_retry(
                session, f"{self.lambda_endpoint}/instance-types", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get Instance Types",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

        return results

    async def test_qdrant(self) -> List[TestResult]:
        """Test Qdrant vector database connectivity"""
        results = []
        service_name = "Qdrant"

        if not self.qdrant_url or not self.qdrant_api_key:
            result = TestResult(
                service_name=service_name,
                test_type="Configuration Check",
                status="failed",
                response_time=0.0,
                error_message="QDRANT_URL or QDRANT_API_KEY not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self.qdrant_api_key}',
                'Content-Type': 'application/json'
            }

            # Test 1: Health check
            response, response_time = await self.make_request_with_retry(
                session, f"{self.qdrant_url}/health", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Health Check",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

            # Test 2: List collections
            response, response_time = await self.make_request_with_retry(
                session, f"{self.qdrant_url}/collections", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="List Collections",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

        return results

    def test_redis(self) -> List[TestResult]:
        """Test Redis Cloud connectivity"""
        results = []
        service_name = "Redis"

        if not self.redis_url:
            result = TestResult(
                service_name=service_name,
                test_type="Configuration Check",
                status="failed",
                response_time=0.0,
                error_message="REDIS_URL not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        # Test 1: Connection test
        start_time = time.time()
        try:
            client = redis.from_url(self.redis_url, decode_responses=True)
            pong = client.ping()
            response_time = time.time() - start_time

            status = "success" if pong else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Ping Test",
                status=status,
                response_time=response_time,
                details={"pong_response": pong}
            )
            results.append(result)
            self.update_metrics(result)

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                service_name=service_name,
                test_type="Ping Test",
                status="failed",
                response_time=response_time,
                error_message=str(e)
            )
            results.append(result)
            self.update_metrics(result)
            return results

        # Test 2: Basic operations
        start_time = time.time()
        try:
            # Set a test key
            test_key = "sophia_test_key"
            test_value = "test_value"
            client.set(test_key, test_value)

            # Get the test key
            retrieved_value = client.get(test_key)

            # Clean up
            client.delete(test_key)

            response_time = time.time() - start_time

            status = "success" if retrieved_value == test_value else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Basic Operations",
                status=status,
                response_time=response_time,
                details={
                    "set_value": test_value,
                    "retrieved_value": retrieved_value,
                    "operation_success": retrieved_value == test_value
                }
            )
            results.append(result)
            self.update_metrics(result)

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                service_name=service_name,
                test_type="Basic Operations",
                status="failed",
                response_time=response_time,
                error_message=str(e)
            )
            results.append(result)
            self.update_metrics(result)

        # Test 3: Connection info
        start_time = time.time()
        try:
            info = client.info()
            response_time = time.time() - start_time

            result = TestResult(
                service_name=service_name,
                test_type="Connection Info",
                status="success",
                response_time=response_time,
                details={
                    "redis_version": info.get('redis_version', 'unknown'),
                    "connected_clients": info.get('connected_clients', 0),
                    "used_memory": info.get('used_memory_human', 'unknown')
                }
            )
            results.append(result)
            self.update_metrics(result)

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                service_name=service_name,
                test_type="Connection Info",
                status="failed",
                response_time=response_time,
                error_message=str(e)
            )
            results.append(result)
            self.update_metrics(result)

        return results

    async def test_openrouter(self) -> List[TestResult]:
        """Test OpenRouter API connectivity"""
        results = []
        service_name = "OpenRouter"

        if not self.openrouter_api_key:
            result = TestResult(
                service_name=service_name,
                test_type="Configuration Check",
                status="failed",
                response_time=0.0,
                error_message="OPENROUTER_API_KEY not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json'
            }

            # Test 1: Get models
            response, response_time = await self.make_request_with_retry(
                session, "https://openrouter.ai/api/v1/models", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get Models",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

            # Test 2: Get auth key info
            response, response_time = await self.make_request_with_retry(
                session, "https://openrouter.ai/api/v1/auth/key", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Auth Key Info",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

        return results

    async def test_github(self) -> List[TestResult]:
        """Test GitHub API connectivity"""
        results = []
        service_name = "GitHub"

        if not self.github_token:
            result = TestResult(
                service_name=service_name,
                test_type="Configuration Check",
                status="failed",
                response_time=0.0,
                error_message="GH_PAT_TOKEN not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Test 1: Get user info
            response, response_time = await self.make_request_with_retry(
                session, "https://api.github.com/user", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get User Info",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

            # Test 2: List repositories
            response, response_time = await self.make_request_with_retry(
                session, "https://api.github.com/user/repos?per_page=5", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="List Repositories",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

        return results

    async def test_hubspot(self) -> List[TestResult]:
        """Test HubSpot API connectivity"""
        results = []
        service_name = "HubSpot"

        if not self.hubspot_token:
            result = TestResult(
                service_name=service_name,
                test_type="Configuration Check",
                status="failed",
                response_time=0.0,
                error_message="HUBSPOT_ACCESS_TOKEN not found in environment"
            )
            results.append(result)
            self.update_metrics(result)
            return results

        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self.hubspot_token}',
                'Content-Type': 'application/json'
            }

            # Test 1: Get account info
            response, response_time = await self.make_request_with_retry(
                session, "https://api.hubapi.com/integrations/v1/me", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get Account Info",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

            # Test 2: Get companies (basic CRM test)
            response, response_time = await self.make_request_with_retry(
                session, "https://api.hubapi.com/crm/v3/objects/companies?limit=1", headers=headers
            )

            status = "success" if response["status_code"] == 200 else "failed"
            result = TestResult(
                service_name=service_name,
                test_type="Get Companies",
                status=status,
                response_time=response_time,
                http_status=response["status_code"],
                details=response["response"]
            )
            if status == "failed":
                result.error_message = f"HTTP {response['status_code']}: {response['response']}"
            results.append(result)
            self.update_metrics(result)

        return results

    async def run_all_tests(self) -> Dict:
        """Run all external API connectivity tests"""
        logger.info("Starting comprehensive external API connectivity testing...")

        start_time = time.time()

        # Run all tests concurrently
        tasks = [
            self.test_lambda_labs(),
            self.test_qdrant(),
            asyncio.to_thread(self.test_redis),
            self.test_openrouter(),
            self.test_github(),
            self.test_hubspot()
        ]

        # Execute tests
        results = []
        for task in tasks:
            try:
                if asyncio.iscoroutine(task):
                    task_results = await task
                else:
                    task_results = await asyncio.get_event_loop().run_in_executor(None, task)
                results.extend(task_results)
            except Exception as e:
                logger.error(f"Error running test: {str(e)}")
                logger.error(traceback.format_exc())

        self.results = results
        end_time = time.time()

        # Generate comprehensive report
        report = self.generate_report(end_time - start_time)

        logger.info("External API connectivity testing completed")
        return report

    def generate_report(self, total_execution_time: float) -> Dict:
        """Generate comprehensive test report"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Overall statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.status == 'success')
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # Service breakdown
        service_breakdown = {}
        for service, metrics in self.metrics.items():
            service_tests = [r for r in self.results if r.service_name == service]
            service_successful = sum(1 for r in service_tests if r.status == 'success')
            service_failed = len(service_tests) - service_successful

            service_breakdown[service] = {
                "total_tests": len(service_tests),
                "successful_tests": service_successful,
                "failed_tests": service_failed,
                "success_rate": (service_successful / len(service_tests) * 100) if service_tests else 0,
                "average_response_time": metrics.average_response_time,
                "min_response_time": metrics.min_response_time if metrics.min_response_time != float('inf') else 0,
                "max_response_time": metrics.max_response_time,
                "last_success": metrics.last_success,
                "last_failure": metrics.last_failure,
                "error_types": metrics.error_types
            }

        # Detailed results by service
        detailed_results = {}
        for result in self.results:
            service = result.service_name
            if service not in detailed_results:
                detailed_results[service] = []
            detailed_results[service].append(asdict(result))

        report = {
            "test_summary": {
                "timestamp": timestamp,
                "total_execution_time": total_execution_time,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "services_tested": len(self.metrics)
            },
            "service_breakdown": service_breakdown,
            "detailed_results": detailed_results,
            "configuration_status": {
                "lambda_labs": bool(self.lambda_api_key),
                "qdrant": bool(self.qdrant_url and self.qdrant_api_key),
                "redis": bool(self.redis_url),
                "openrouter": bool(self.openrouter_api_key),
                "github": bool(self.github_token),
                "hubspot": bool(self.hubspot_token)
            }
        }

        return report

    def save_report(self, report: Dict, filename: str = "external_api_test_report.json"):
        """Save test report to file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Test report saved to {filename}")

        # Also save human-readable summary
        summary_filename = filename.replace('.json', '_summary.txt')
        with open(summary_filename, 'w') as f:
            f.write("EXTERNAL API CONNECTIVITY TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")

            summary = report["test_summary"]
            f.write(f"Test Timestamp: {summary['timestamp']}\n")
            f.write(f"Execution Time: {summary['total_execution_time']:.2f} seconds\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Successful Tests: {summary['successful_tests']}\n")
            f.write(f"Failed Tests: {summary['failed_tests']}\n")
            f.write(f"Success Rate: {summary['success_rate']:.1f}%\n")
            f.write(f"Services Tested: {summary['services_tested']}\n\n")

            f.write("SERVICE BREAKDOWN:\n")
            f.write("-" * 30 + "\n")

            for service, metrics in report["service_breakdown"].items():
                f.write(f"\n{service}:\n")
                f.write(f"  Tests: {metrics['total_tests']}\n")
                f.write(f"  Success Rate: {metrics['success_rate']:.1f}%\n")
                f.write(f"  Avg Response Time: {metrics['average_response_time']:.3f}s\n")
                if metrics['error_types']:
                    f.write(f"  Errors: {', '.join(metrics['error_types'])}\n")

            f.write("\n\nCONFIGURATION STATUS:\n")
            f.write("-" * 25 + "\n")
            for service, configured in report["configuration_status"].items():
                status = "✓ Configured" if configured else "✗ Missing"
                f.write(f"{service}: {status}\n")

        logger.info(f"Human-readable summary saved to {summary_filename}")

async def main():
    """Main function to run the external API connectivity tests"""
    tester = ExternalAPIConnectivityTester()

    try:
        logger.info("Starting external API connectivity testing...")
        report = await tester.run_all_tests()

        # Save results
        tester.save_report(report)

        # Print summary to console
        summary = report["test_summary"]
        print("\n" + "="*60)
        print("EXTERNAL API CONNECTIVITY TEST RESULTS")
        print("="*60)
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Execution Time: {summary['total_execution_time']:.2f} seconds")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful Tests: {summary['successful_tests']}")
        print(f"Failed Tests: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Services Tested: {summary['services_tested']}")

        print("\nSERVICE BREAKDOWN:")
        for service, metrics in report["service_breakdown"].items():
            print(f"\n{service}:")
            print(f"  Success Rate: {metrics['success_rate']:.1f}%")
            print(f"  Avg Response Time: {metrics['average_response_time']:.3f}s")
            if metrics['error_types']:
                print(f"  Errors: {', '.join(metrics['error_types'])}")

        print("\n" + "="*60)
        print("Detailed results saved to external_api_test_report.json")
        print("Human-readable summary saved to external_api_test_report_summary.txt")
        print("Full logs saved to external_api_test_results.log")
        print("="*60)

        return report

    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    asyncio.run(main())