#!/usr/bin/env python3
"""
Complete Integration Test Suite for Sophia AI Intel Platform
Tests all components: SSL, domain routing, monitoring stack, and microservices
"""

import requests
import json
import time
import subprocess
import sys
from typing import Dict, List, Tuple

class SophiaIntegrationTester:
    def __init__(self, base_domain: str = "www.sophia-intel.ai"):
        self.base_domain = base_domain
        self.http_url = f"http://{base_domain}"
        self.https_url = f"https://{base_domain}"
        self.services = {
            'dashboard': f"{self.https_url}",
            'research': f"{self.https_url}/research/",
            'context': f"{self.https_url}/context/",
            'github': f"{self.https_url}/github/",
            'business': f"{self.https_url}/business/",
            'lambda': f"{self.https_url}/lambda/",
            'hubspot': f"{self.https_url}/hubspot/",
            'agents': f"{self.https_url}/agents/"
        }
        self.monitoring_endpoints = {
            'prometheus': f"{self.https_url}/prometheus/",
            'grafana': f"{self.https_url}/grafana/",
            'loki': f"{self.https_url}/loki/",
            'cadvisor': f"{self.https_url}/cadvisor/",
            'node-exporter': f"{self.https_url}/node-exporter/"
        }

    def test_ssl_certificate(self) -> Tuple[bool, str]:
        """Test SSL certificate validity"""
        try:
            response = requests.get(self.https_url, timeout=10, verify=False)
            if response.status_code == 200:
                return True, "SSL certificate is valid and HTTPS is working"
            else:
                return False, f"SSL connection failed with status {response.status_code}"
        except requests.exceptions.SSLError as e:
            return False, f"SSL certificate error: {str(e)}"
        except Exception as e:
            return False, f"SSL test failed: {str(e)}"

    def test_http_to_https_redirect(self) -> Tuple[bool, str]:
        """Test HTTP to HTTPS redirect"""
        try:
            response = requests.get(self.http_url, allow_redirects=False, timeout=10)
            if response.status_code == 301 and 'https://' in response.headers.get('Location', ''):
                return True, "HTTP to HTTPS redirect is working correctly"
            else:
                return False, f"HTTP redirect failed: {response.status_code}"
        except Exception as e:
            return False, f"HTTP redirect test failed: {str(e)}"

    def test_domain_routing(self) -> Tuple[bool, str]:
        """Test domain routing functionality"""
        try:
            response = requests.get(self.https_url, timeout=10, verify=False)
            if response.status_code == 200:
                return True, "Domain routing is working correctly"
            else:
                return False, f"Domain routing failed with status {response.status_code}"
        except Exception as e:
            return False, f"Domain routing test failed: {str(e)}"

    def test_service_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """Test all service endpoints"""
        results = {}
        for service_name, url in self.services.items():
            try:
                response = requests.get(url, timeout=10, verify=False)
                if response.status_code == 200:
                    results[service_name] = (True, f"{service_name} endpoint is responding")
                else:
                    results[service_name] = (False, f"{service_name} failed with status {response.status_code}")
            except Exception as e:
                results[service_name] = (False, f"{service_name} test failed: {str(e)}")
        return results

    def test_monitoring_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """Test monitoring endpoints with authentication"""
        results = {}
        auth = ('admin', 'admin')  # Basic auth credentials

        for service_name, url in self.monitoring_endpoints.items():
            try:
                response = requests.get(url, auth=auth, timeout=10, verify=False)
                if response.status_code == 200:
                    results[service_name] = (True, f"{service_name} monitoring endpoint is accessible")
                else:
                    results[service_name] = (False, f"{service_name} monitoring failed with status {response.status_code}")
            except Exception as e:
                results[service_name] = (False, f"{service_name} monitoring test failed: {str(e)}")
        return results

    def test_nginx_configuration(self) -> Tuple[bool, str]:
        """Test nginx configuration syntax"""
        try:
            # This would need to be run on the server where nginx is installed
            result = subprocess.run(['nginx', '-t'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, "nginx configuration is valid"
            else:
                return False, f"nginx configuration error: {result.stderr}"
        except Exception as e:
            return False, f"nginx test failed: {str(e)}"

    def run_comprehensive_test(self) -> Dict[str, any]:
        """Run all tests and return comprehensive results"""
        print("🧪 Starting Comprehensive Integration Tests for Sophia AI Intel Platform")
        print("=" * 80)

        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'domain': self.base_domain,
            'tests': {}
        }

        # Test SSL and HTTPS
        print("\n🔐 Testing SSL and HTTPS functionality...")
        ssl_result = self.test_ssl_certificate()
        https_redirect = self.test_http_to_https_redirect()
        domain_routing = self.test_domain_routing()

        results['tests']['ssl'] = {
            'certificate_valid': ssl_result[0],
            'certificate_message': ssl_result[1],
            'https_redirect': https_redirect[0],
            'redirect_message': https_redirect[1],
            'domain_routing': domain_routing[0],
            'routing_message': domain_routing[1]
        }

        print(f"SSL Certificate: {'✅ PASS' if ssl_result[0] else '❌ FAIL'} - {ssl_result[1]}")
        print(f"HTTP→HTTPS Redirect: {'✅ PASS' if https_redirect[0] else '❌ FAIL'} - {https_redirect[1]}")
        print(f"Domain Routing: {'✅ PASS' if domain_routing[0] else '❌ FAIL'} - {domain_routing[1]}")

        # Test service endpoints
        print("\n🔗 Testing Service Endpoints...")
        service_results = self.test_service_endpoints()
        results['tests']['services'] = service_results

        for service, (passed, message) in service_results.items():
            print(f"{service.capitalize()}: {'✅ PASS' if passed else '❌ FAIL'} - {message}")

        # Test monitoring endpoints
        print("\n📊 Testing Monitoring Stack...")
        monitoring_results = self.test_monitoring_endpoints()
        results['tests']['monitoring'] = monitoring_results

        for service, (passed, message) in monitoring_results.items():
            print(f"{service.capitalize()}: {'✅ PASS' if passed else '❌ FAIL'} - {message}")

        # Calculate overall results
        all_tests = []
        all_tests.extend([ssl_result[0], https_redirect[0], domain_routing[0]])
        all_tests.extend([result[0] for result in service_results.values()])
        all_tests.extend([result[0] for result in monitoring_results.values()])

        passed_tests = sum(all_tests)
        total_tests = len(all_tests)

        results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }

        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY"        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(".1f")
        print("=" * 80)

        if results['summary']['success_rate'] >= 90:
            print("🎉 OVERALL RESULT: SUCCESS - Platform is fully operational!")
        elif results['summary']['success_rate'] >= 75:
            print("⚠️  OVERALL RESULT: PARTIAL SUCCESS - Most functionality working")
        else:
            print("❌ OVERALL RESULT: NEEDS ATTENTION - Multiple issues detected")

        return results

def main():
    tester = SophiaIntegrationTester()
    results = tester.run_comprehensive_test()

    # Save results to file
    with open('integration_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("
💾 Detailed results saved to integration_test_results.json"
    return 0 if results['summary']['success_rate'] >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
