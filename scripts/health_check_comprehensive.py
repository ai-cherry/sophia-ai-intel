#!/usr/bin/env python3
"""
Comprehensive Health Check Script for Sophia AI Ecosystem
Tests all deployed services and provides detailed validation report
"""

import requests
import time
import sys
import json
from datetime import datetime
import socket
import subprocess

class SophiaHealthChecker:
    def __init__(self):
        self.base_url = "http://localhost"
        self.services = {
            'mcp-github': 8082,
            'mcp-hubspot': 8083,
            'mcp-business': 8086,
            'agno-coordinator': 8080,
            'agno-teams': 8087,
            'orchestrator': 8088
        }
        self.infrastructure = {
            'postgres': 5432,
            'redis': 6380,
            'qdrant': 6333
        }
        self.results = {}

    def check_service_health(self, service_name, port):
        """Check if a service is responding to health requests"""
        url = f"{self.base_url}:{port}/healthz"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return {"status": "healthy", "response_time": response.elapsed.total_seconds() * 1000}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_infrastructure_health(self, service_name, port):
        """Check infrastructure services (TCP connectivity)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return {"status": "healthy", "message": "TCP connection successful"}
            else:
                return {"status": "unhealthy", "error": "TCP connection failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_docker_containers(self):
        """Check Docker container status"""
        try:
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'],
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
                return containers
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}

    def test_inter_service_communication(self):
        """Test communication between services"""
        results = {}

        # Test coordinator to teams communication
        try:
            coord_url = f"{self.base_url}:{self.services['agno-coordinator']}/health"
            teams_url = f"{self.base_url}:{self.services['agno-teams']}/healthz"

            coord_response = requests.get(coord_url, timeout=10)
            teams_response = requests.get(teams_url, timeout=10)

            results['coordinator_teams'] = {
                "coordinator": coord_response.status_code == 200,
                "teams": teams_response.status_code == 200,
                "communication": "both healthy" if (coord_response.status_code == 200 and teams_response.status_code == 200) else "issues detected"
            }
        except Exception as e:
            results['coordinator_teams'] = {"error": str(e)}

        return results

    def run_comprehensive_check(self):
        """Run all health checks"""
        print("🔍 Starting Comprehensive Sophia AI Health Check")
        print("=" * 60)

        # Check Docker containers
        print("\n📦 Checking Docker Containers...")
        containers = self.check_docker_containers()
        self.results['docker_containers'] = containers

        # Check infrastructure services
        print("\n🏗️ Checking Infrastructure Services...")
        infra_results = {}
        for service, port in self.infrastructure.items():
            print(f"   Checking {service} on port {port}...")
            infra_results[service] = self.check_infrastructure_health(service, port)
        self.results['infrastructure'] = infra_results

        # Check application services
        print("\n🚀 Checking Application Services...")
        service_results = {}
        for service, port in self.services.items():
            print(f"   Checking {service} on port {port}...")
            service_results[service] = self.check_service_health(service, port)
        self.results['services'] = service_results

        # Test inter-service communication
        print("\n🔗 Testing Inter-Service Communication...")
        comm_results = self.test_inter_service_communication()
        self.results['communication'] = comm_results

        return self.generate_report()

    def generate_report(self):
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.analyze_results(),
            "details": self.results
        }

        print("\n" + "=" * 60)
        print("📊 HEALTH CHECK REPORT")
        print("=" * 60)

        # Summary
        summary = report['summary']
        print("
✅ OVERALL STATUS:"        print(f"   Services Healthy: {summary['healthy_services']}/{summary['total_services']}")
        print(f"   Infrastructure Healthy: {summary['healthy_infrastructure']}/{summary['total_infrastructure']}")
        print(f"   Overall Health: {summary['overall_health']}")

        # Detailed results
        print("
📋 DETAILED RESULTS:"        print("
🏗️ INFRASTRUCTURE:"        for service, result in self.results.get('infrastructure', {}).items():
            status = "✅" if result.get('status') == 'healthy' else "❌"
            print(f"   {status} {service}: {result.get('message', result.get('error', 'unknown'))}")

        print("
🚀 APPLICATION SERVICES:"        for service, result in self.results.get('services', {}).items():
            status = "✅" if result.get('status') == 'healthy' else "❌"
            if result.get('status') == 'healthy':
                print(".2f")
            else:
                print(f"   {status} {service}: {result.get('error', 'unknown')}")

        print("
🔗 INTER-SERVICE COMMUNICATION:"        for test, result in self.results.get('communication', {}).items():
            if 'error' not in result:
                coord_status = "✅" if result.get('coordinator') else "❌"
                teams_status = "✅" if result.get('teams') else "❌"
                print(f"   {coord_status} Coordinator ↔ {teams_status} Teams: {result.get('communication')}")
            else:
                print(f"   ❌ {test}: {result['error']}")

        return report

    def analyze_results(self):
        """Analyze results and provide summary"""
        infra_results = self.results.get('infrastructure', {})
        service_results = self.results.get('services', {})

        healthy_infra = sum(1 for r in infra_results.values() if r.get('status') == 'healthy')
        healthy_services = sum(1 for r in service_results.values() if r.get('status') == 'healthy')

        total_infra = len(infra_results)
        total_services = len(service_results)

        # Determine overall health
        infra_health = healthy_infra / total_infra if total_infra > 0 else 0
        service_health = healthy_services / total_services if total_services > 0 else 0

        if infra_health == 1.0 and service_health >= 0.8:
            overall = "EXCELLENT"
        elif infra_health >= 0.8 and service_health >= 0.6:
            overall = "GOOD"
        elif infra_health >= 0.5 or service_health >= 0.3:
            overall = "FAIR"
        else:
            overall = "CRITICAL"

        return {
            "healthy_infrastructure": healthy_infra,
            "total_infrastructure": total_infra,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "infrastructure_health_percent": infra_health * 100,
            "service_health_percent": service_health * 100,
            "overall_health": overall
        }

def main():
    checker = SophiaHealthChecker()
    report = checker.run_comprehensive_check()

    # Save report to file
    with open('health_check_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: health_check_report.json")

    # Exit with appropriate code
    summary = report['summary']
    if summary['overall_health'] in ['EXCELLENT', 'GOOD']:
        print("✅ Health check completed successfully")
        sys.exit(0)
    else:
        print("⚠️ Health check found issues")
        sys.exit(1)

if __name__ == "__main__":
    main()