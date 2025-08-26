#!/usr/bin/env python3
"""
Simple Health Check Script for Sophia AI Ecosystem
Tests deployed services and provides basic validation
"""

import requests
import time
import sys
import json
from datetime import datetime
import socket
import subprocess

def check_service_health(service_name, port):
    """Check if a service is responding to health requests"""
    url = f"http://localhost:{port}/healthz"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"status": "healthy", "response_time": response.elapsed.total_seconds() * 1000}
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "unhealthy", "error": str(e)}

def check_infrastructure_health(service_name, port):
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

def check_docker_containers():
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

def run_health_check():
    """Run basic health checks"""
    print("🔍 Starting Sophia AI Health Check")
    print("=" * 50)

    results = {}

    # Check Docker containers
    print("\n📦 Checking Docker Containers...")
    containers = check_docker_containers()
    results['docker_containers'] = containers

    # Infrastructure services
    infrastructure = {
        'postgres': 5432,
        'redis': 6380,
        'qdrant': 6333
    }

    print("\n🏗️ Checking Infrastructure Services...")
    infra_results = {}
    for service, port in infrastructure.items():
        print(f"   Checking {service} on port {port}...")
        infra_results[service] = check_infrastructure_health(service, port)
    results['infrastructure'] = infra_results

    # Application services
    services = {
        'mcp-github': 8082,
        'mcp-hubspot': 8083,
        'mcp-business': 8086,
        'agno-coordinator': 8080,
        'agno-teams': 8087,
        'orchestrator': 8088
    }

    print("\n🚀 Checking Application Services...")
    service_results = {}
    for service, port in services.items():
        print(f"   Checking {service} on port {port}...")
        service_results[service] = check_service_health(service, port)
    results['services'] = service_results

    # Generate report
    print("\n" + "=" * 50)
    print("📊 HEALTH CHECK REPORT")
    print("=" * 50)

    # Summary
    infra_healthy = sum(1 for r in infra_results.values() if r.get('status') == 'healthy')
    services_healthy = sum(1 for r in service_results.values() if r.get('status') == 'healthy')

    print("
✅ OVERALL STATUS:"    print(f"   Infrastructure: {infra_healthy}/{len(infrastructure)} healthy")
    print(f"   Services: {services_healthy}/{len(services)} healthy")

    # Detailed results
    print("
🏗️ INFRASTRUCTURE:"    for service, result in infra_results.items():
        status = "✅" if result.get('status') == 'healthy' else "❌"
        print(f"   {status} {service}: {result.get('message', result.get('error', 'unknown'))}")

    print("
🚀 APPLICATION SERVICES:"    for service, result in service_results.items():
        status = "✅" if result.get('status') == 'healthy' else "❌"
        if result.get('status') == 'healthy':
            print(".2f")
        else:
            print(f"   {status} {service}: {result.get('error', 'unknown')}")

    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

    with open('health_check_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: health_check_report.json")

    if infra_healthy == len(infrastructure) and services_healthy >= len(services) * 0.5:
        print("✅ Health check completed successfully")
        return True
    else:
        print("⚠️ Health check found issues")
        return False

if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)