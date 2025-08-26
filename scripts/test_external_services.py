#!/usr/bin/env python3
"""
External Services Connectivity Test Script
Tests connectivity and authentication for all external services in Sophia AI platform
"""

import os
import sys
import json
import time
import requests
import psycopg2
import redis
import logging
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import subprocess
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceTester:
    def __init__(self, env_file: str = ".env.production"):
        self.env_file = env_file
        self.results = {}
        self.load_env()

    def load_env(self):
        """Load environment variables from file"""
        if not os.path.exists(self.env_file):
            logger.error(f"Environment file {self.env_file} not found")
            return

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

    def log_result(self, service: str, status: str, message: str, details: dict = None):
        """Log test result"""
        self.results[service] = {
            'status': status,
            'message': message,
            'timestamp': time.time(),
            'details': details or {}
        }
        logger.info(f"{service}: {status.upper()} - {message}")

    def test_lambda_labs(self) -> Dict:
        """Test Lambda Labs API connectivity"""
        api_key = os.getenv('LAMBDA_API_KEY')
        endpoint = os.getenv('LAMBDA_CLOUD_ENDPOINT', 'https://cloud.lambdalabs.com/api/v1')

        if not api_key or api_key.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo API key detected', 'details': {}}

        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(f"{endpoint}/instances", headers=headers, timeout=10)

            if response.status_code == 200:
                return {'status': 'OK', 'message': 'Lambda Labs API accessible', 'details': {'instances': len(response.json().get('data', []))}}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {'response': response.text[:200]}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_qdrant(self) -> Dict:
        """Test Qdrant vector database connectivity"""
        url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
        api_key = os.getenv('QDRANT_API_KEY')

        try:
            headers = {}
            if api_key:
                headers['api-key'] = api_key

            response = requests.get(f"{url}/health", headers=headers, timeout=10)

            if response.status_code == 200:
                # Test collections endpoint
                collections_response = requests.get(f"{url}/collections", headers=headers, timeout=10)
                collections = collections_response.json().get('result', {}).get('collections', [])
                return {'status': 'OK', 'message': 'Qdrant accessible', 'details': {'collections_count': len(collections)}}
            else:
                return {'status': 'ERROR', 'message': f'Health check failed: {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_redis(self) -> Dict:
        """Test Redis connectivity"""
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        password = os.getenv('REDIS_PASSWORD')

        try:
            parsed = urlparse(redis_url)
            host = parsed.hostname or 'redis'
            port = parsed.port or 6379

            r = redis.Redis(host=host, port=port, password=password, decode_responses=True, socket_timeout=10)

            # Test connection
            if r.ping():
                info = r.info('server')
                return {'status': 'OK', 'message': 'Redis accessible', 'details': {'version': info.get('redis_version', 'unknown')}}
            else:
                return {'status': 'ERROR', 'message': 'Redis ping failed', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Redis connection failed: {str(e)}', 'details': {}}

    def test_openrouter(self) -> Dict:
        """Test OpenRouter API access"""
        api_key = os.getenv('OPENROUTER_API_KEY')

        if not api_key or api_key.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo API key detected', 'details': {}}

        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get('https://openrouter.ai/api/v1/auth/key', headers=headers, timeout=10)

            if response.status_code == 200:
                return {'status': 'OK', 'message': 'OpenRouter API accessible', 'details': response.json()}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_postgresql(self) -> Dict:
        """Test PostgreSQL database connectivity"""
        db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

        if not db_url:
            return {'status': 'ERROR', 'message': 'No database URL configured', 'details': {}}

        try:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Get database info
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]

            # Get database size
            cursor.execute('SELECT pg_size_pretty(pg_database_size(current_database()))')
            size = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return {'status': 'OK', 'message': 'PostgreSQL accessible', 'details': {'version': version, 'size': size}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Database connection failed: {str(e)}', 'details': {}}

    def test_github(self) -> Dict:
        """Test GitHub API access"""
        token = os.getenv('GITHUB_TOKEN')

        if not token or token.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo token detected', 'details': {}}

        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                return {'status': 'OK', 'message': 'GitHub API accessible', 'details': {'username': user_data.get('login', 'unknown')}}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_hubspot(self) -> Dict:
        """Test HubSpot API access"""
        api_key = os.getenv('HUBSPOT_API_KEY')

        if not api_key or api_key.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo API key detected', 'details': {}}

        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get('https://api.hubapi.com/crm/v3/objects/contacts', headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {'status': 'OK', 'message': 'HubSpot API accessible', 'details': {'contacts_count': len(data.get('results', []))}}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_slack(self) -> Dict:
        """Test Slack API access"""
        token = os.getenv('SLACK_BOT_TOKEN')

        if not token or token.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo token detected', 'details': {}}

        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post('https://slack.com/api/auth.test', headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {'status': 'OK', 'message': 'Slack API accessible', 'details': {'team': data.get('team', 'unknown')}}
                else:
                    return {'status': 'ERROR', 'message': f'Slack API error: {data.get("error", "unknown")}', 'details': {}}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def test_dnsimple(self) -> Dict:
        """Test DNSimple API access"""
        token = os.getenv('DNSIMPLE_TOKEN')

        if not token or token.startswith('demo'):
            return {'status': 'ERROR', 'message': 'Demo token detected', 'details': {}}

        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            response = requests.get('https://api.dnsimple.com/v2/accounts', headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {'status': 'OK', 'message': 'DNSimple API accessible', 'details': {'accounts_count': len(data.get('data', []))}}
            else:
                return {'status': 'ERROR', 'message': f'API returned {response.status_code}', 'details': {}}

        except Exception as e:
            return {'status': 'ERROR', 'message': f'Connection failed: {str(e)}', 'details': {}}

    def run_all_tests(self) -> Dict:
        """Run all service connectivity tests"""
        logger.info("Starting external services connectivity tests...")

        tests = {
            'lambda_labs': self.test_lambda_labs,
            'qdrant': self.test_qdrant,
            'redis': self.test_redis,
            'openrouter': self.test_openrouter,
            'postgresql': self.test_postgresql,
            'github': self.test_github,
            'hubspot': self.test_hubspot,
            'slack': self.test_slack,
            'dnsimple': self.test_dnsimple,
        }

        for service_name, test_func in tests.items():
            logger.info(f"Testing {service_name}...")
            result = test_func()
            self.log_result(service_name, result['status'], result['message'], result.get('details', {}))

        return self.results

    def generate_report(self) -> str:
        """Generate a summary report of all test results"""
        report_lines = ["External Services Connectivity Test Report", "=" * 50, ""]

        total_tests = len(self.results)
        passed = sum(1 for r in self.results.values() if r['status'] == 'OK')
        failed = total_tests - passed

        report_lines.extend([
            f"Total Services Tested: {total_tests}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            f"Success Rate: {passed/total_tests*100:.1f}%" if total_tests > 0 else "Success Rate: 0%",
            "",
            "Detailed Results:",
            "-" * 20,
        ])

        for service, result in self.results.items():
            status_icon = "✅" if result['status'] == 'OK' else "❌"
            report_lines.append(f"{status_icon} {service.upper()}: {result['message']}")

            if result.get('details'):
                for key, value in result['details'].items():
                    report_lines.append(f"   {key}: {value}")

            report_lines.append("")

        # Identify key issues
        report_lines.extend([
            "Key Issues Identified:",
            "-" * 20,
        ])

        demo_keys = []
        connection_failures = []

        for service, result in self.results.items():
            if 'demo' in result['message'].lower():
                demo_keys.append(service)
            elif result['status'] == 'ERROR':
                connection_failures.append(service)

        if demo_keys:
            report_lines.append(f"🔑 {len(demo_keys)} services using demo/placeholder keys: {', '.join(demo_keys)}")

        if connection_failures:
            report_lines.append(f"🔌 {len(connection_failures)} services with connection issues: {', '.join(connection_failures)}")

        if not demo_keys and not connection_failures:
            report_lines.append("✅ All services configured correctly")

        return "\n".join(report_lines)

def main():
    """Main function"""
    tester = ServiceTester()

    # Run all tests
    results = tester.run_all_tests()

    # Generate and print report
    report = tester.generate_report()
    print(report)

    # Save detailed results to file
    with open('external_services_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\nDetailed results saved to external_services_test_results.json")

    # Exit with appropriate code
    failed_services = [s for s, r in results.items() if r['status'] != 'OK']
    sys.exit(0 if not failed_services else 1)

if __name__ == "__main__":
    main()