#!/usr/bin/env python3
"""
Sophia AI Service Validation Script

Validates all services in the Sophia AI infrastructure and fails on any red status.
Used by the CI/CD pipeline to ensure service health before proceeding with deployments.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests
from kubernetes import client, config


class ServiceValidator:
    """Validates Sophia AI services health and status."""

    def __init__(self, namespace: str = "sophia", canary: bool = False, production: bool = False):
        self.namespace = namespace
        self.canary = canary
        self.production = production
        self.k8s_client = None
        self._init_k8s_client()

    def _init_k8s_client(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Kubernetes client: {e}")
            print("Running in offline mode - some checks will be skipped")

    def get_service_endpoints(self) -> Dict[str, str]:
        """Get service endpoints from Kubernetes or use defaults."""
        endpoints = {}

        if self.k8s_client:
            try:
                services = self.k8s_client.list_namespaced_service(self.namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(('mcp-', 'sophia-', 'comms-', 'crm-', 'analytics-')):
                        # Get service port
                        port = None
                        for p in svc.spec.ports:
                            if p.name == 'http' or p.port == 80 or p.port == 8080:
                                port = p.port
                                break
                        if port:
                            endpoints[svc.metadata.name] = f"http://{svc.metadata.name}.{self.namespace}.svc.cluster.local:{port}"
            except Exception as e:
                print(f"⚠️  Could not fetch service endpoints: {e}")

        # Fallback to default endpoints if Kubernetes discovery fails
        if not endpoints:
            default_endpoints = {
                'mcp-research': 'http://mcp-research.sophia.svc.cluster.local:8080',
                'mcp-context': 'http://mcp-context.sophia.svc.cluster.local:8080',
                'mcp-agents': 'http://mcp-agents.sophia.svc.cluster.local:8080',
                'mcp-business': 'http://mcp-business.sophia.svc.cluster.local:8080',
                'comms-mcp': 'http://comms-mcp.sophia.svc.cluster.local:8080',
                'crm-mcp': 'http://crm-mcp.sophia.svc.cluster.local:8080',
                'analytics-mcp': 'http://analytics-mcp.sophia.svc.cluster.local:8080',
                'sophia-dashboard': 'http://sophia-dashboard.sophia.svc.cluster.local:8080',
                'sophia-business': 'http://sophia-business.sophia.svc.cluster.local:8080',
                'sophia-hubspot': 'http://sophia-hubspot.sophia.svc.cluster.local:8080',
                'sophia-github': 'http://sophia-github.sophia.svc.cluster.local:8080',
                'sophia-lambda': 'http://sophia-lambda.sophia.svc.cluster.local:8080'
            }
            endpoints = default_endpoints

        return endpoints

    async def check_service_health(self, service_name: str, endpoint: str, session: aiohttp.ClientSession) -> Tuple[str, Dict]:
        """Check individual service health."""
        status = "unknown"
        details = {"endpoint": endpoint, "response_time": None, "error": None}

        try:
            start_time = time.time()
            async with session.get(f"{endpoint}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_time = time.time() - start_time
                details["response_time"] = round(response_time * 1000, 2)  # ms

                if response.status == 200:
                    try:
                        data = await response.json()
                        if isinstance(data, dict) and data.get("status") == "healthy":
                            status = "green"
                        else:
                            status = "yellow"
                            details["error"] = f"Service returned non-healthy status: {data}"
                    except:
                        # If we can't parse JSON but got 200, consider it healthy
                        status = "green"
                elif response.status >= 500:
                    status = "red"
                    details["error"] = f"Server error: {response.status}"
                else:
                    status = "yellow"
                    details["error"] = f"Client error: {response.status}"

        except asyncio.TimeoutError:
            status = "red"
            details["error"] = "Timeout"
        except aiohttp.ClientError as e:
            status = "red"
            details["error"] = str(e)
        except Exception as e:
            status = "red"
            details["error"] = f"Unexpected error: {str(e)}"

        return service_name, {"status": status, **details}

    def check_kubernetes_resources(self) -> Dict[str, Dict]:
        """Check Kubernetes resource status."""
        results = {}

        if not self.k8s_client:
            return results

        try:
            # Check pods
            pods = self.k8s_client.list_namespaced_pod(self.namespace)
            pod_statuses = {}

            for pod in pods.items:
                if pod.metadata.name.startswith(('mcp-', 'sophia-', 'comms-', 'crm-', 'analytics-')):
                    service_name = pod.metadata.name.split('-')[0] + '-' + pod.metadata.name.split('-')[1]
                    if service_name not in pod_statuses:
                        pod_statuses[service_name] = []

                    phase = pod.status.phase
                    if phase == "Running":
                        pod_statuses[service_name].append("green")
                    elif phase in ["Pending", "ContainerCreating"]:
                        pod_statuses[service_name].append("yellow")
                    else:
                        pod_statuses[service_name].append("red")

            # Aggregate pod statuses
            for service, statuses in pod_statuses.items():
                if "red" in statuses:
                    results[f"{service}-pods"] = {"status": "red", "error": "Some pods are not running"}
                elif "yellow" in statuses:
                    results[f"{service}-pods"] = {"status": "yellow", "error": "Some pods are still starting"}
                else:
                    results[f"{service}-pods"] = {"status": "green"}

        except Exception as e:
            print(f"⚠️  Could not check Kubernetes resources: {e}")

        return results

    async def validate_all_services(self) -> Tuple[bool, Dict[str, Dict]]:
        """Validate all services and return overall health status."""
        print(f"🔍 Validating services in namespace: {self.namespace}")
        if self.canary:
            print("🏷️  Running in canary mode")
        if self.production:
            print("🏭 Running in production mode")

        endpoints = self.get_service_endpoints()
        print(f"📋 Found {len(endpoints)} services to validate")

        # Check Kubernetes resources
        k8s_results = self.check_kubernetes_resources()

        # Check service health endpoints
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service_name, endpoint in endpoints.items():
                tasks.append(self.check_service_health(service_name, endpoint, session))

            service_results = {}
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"❌ Error during validation: {result}")
                    else:
                        service_name, details = result
                        service_results[service_name] = details

        # Combine results
        all_results = {**k8s_results, **service_results}

        # Determine overall status
        overall_healthy = True
        red_services = []
        yellow_services = []

        for service_name, details in all_results.items():
            status = details["status"]
            if status == "red":
                overall_healthy = False
                red_services.append(service_name)
            elif status == "yellow":
                yellow_services.append(service_name)

        # Print results
        print("\n📊 Validation Results:")
        print("=" * 50)

        for service_name, details in sorted(all_results.items()):
            status = details["status"]
            status_icon = "🟢" if status == "green" else "🟡" if status == "yellow" else "🔴"
            response_time = f" ({details['response_time']}ms)" if details.get("response_time") else ""
            print(f"{status_icon} {service_name}: {status.upper()}{response_time}")

            if details.get("error"):
                print(f"   ❌ {details['error']}")

        print("=" * 50)

        if red_services:
            print(f"🔴 RED SERVICES ({len(red_services)}): {', '.join(red_services)}")
            overall_healthy = False

        if yellow_services:
            print(f"🟡 YELLOW SERVICES ({len(yellow_services)}): {', '.join(yellow_services)}")

        if overall_healthy:
            print("✅ ALL SERVICES HEALTHY - Pipeline can proceed")
        else:
            print("❌ SERVICE VALIDATION FAILED - Pipeline will stop")

        return overall_healthy, all_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Sophia AI services")
    parser.add_argument("--namespace", "-n", default="sophia", help="Kubernetes namespace")
    parser.add_argument("--canary", action="store_true", help="Run in canary mode")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    parser.add_argument("--output-json", help="Output results to JSON file")

    args = parser.parse_args()

    validator = ServiceValidator(
        namespace=args.namespace,
        canary=args.canary,
        production=args.production
    )

    async def run_validation():
        healthy, results = await validator.validate_all_services()

        if args.output_json:
            with open(args.output_json, 'w') as f:
                json.dump({
                    "healthy": healthy,
                    "timestamp": time.time(),
                    "namespace": args.namespace,
                    "results": results
                }, f, indent=2)

        return healthy

    healthy = asyncio.run(run_validation())

    if not healthy:
        print("\n💥 VALIDATION FAILED: Exiting with code 1")
        sys.exit(1)
    else:
        print("\n🎉 VALIDATION PASSED: All services are healthy")


if __name__ == "__main__":
    main()