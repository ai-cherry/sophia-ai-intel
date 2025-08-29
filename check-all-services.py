#!/usr/bin/env python3
"""
Service Health Check Script
Checks the health status of all Sophia AI services
"""

import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any
import json

# Service endpoints
SERVICES = {
    "context": {
        "base_url": "http://localhost:8081",
        "description": "Document storage and semantic search"
    },
    "research": {
        "base_url": "http://localhost:8085", 
        "description": "Research and web search capabilities"
    },
    "github": {
        "base_url": "http://localhost:8082",
        "description": "GitHub repository integration"
    },
    "hubspot": {
        "base_url": "http://localhost:8083",
        "description": "HubSpot CRM integration"
    },
    "salesforce": {
        "base_url": "http://localhost:8092",
        "description": "Salesforce CRM integration"
    },
    "gong": {
        "base_url": "http://localhost:8091",
        "description": "Gong call analytics"
    },
    "agents": {
        "base_url": "http://localhost:8000",
        "description": "AI agent orchestration"
    },
    "coordinator": {
        "base_url": "http://localhost:8080",
        "description": "AGNO coordinator service"
    },
    "orchestrator": {
        "base_url": "http://localhost:8088",
        "description": "Workflow orchestration"
    }
}

async def check_service_health(service_name: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check health of a single service."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{service_info['base_url']}/health")
            response.raise_for_status()
            return {
                "name": service_name,
                "status": "✅ HEALTHY",
                "url": service_info['base_url'],
                "description": service_info['description'],
                "details": response.json() if response.text else None
            }
        except httpx.TimeoutException:
            return {
                "name": service_name,
                "status": "⏱️ TIMEOUT",
                "url": service_info['base_url'],
                "description": service_info['description'],
                "error": "Health check timed out after 5 seconds"
            }
        except httpx.ConnectError:
            return {
                "name": service_name,
                "status": "❌ OFFLINE",
                "url": service_info['base_url'],
                "description": service_info['description'],
                "error": "Service is not running or not accessible"
            }
        except Exception as e:
            return {
                "name": service_name,
                "status": "⚠️ ERROR",
                "url": service_info['base_url'],
                "description": service_info['description'],
                "error": str(e)
            }

async def check_all_services():
    """Check health of all services in parallel."""
    print("=" * 70)
    print(" SOPHIA AI SERVICE HEALTH CHECK")
    print("=" * 70)
    print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Run all health checks in parallel
    tasks = [
        check_service_health(name, info) 
        for name, info in SERVICES.items()
    ]
    results = await asyncio.gather(*tasks)
    
    # Categorize results
    healthy = []
    unhealthy = []
    
    for result in results:
        if "HEALTHY" in result["status"]:
            healthy.append(result)
        else:
            unhealthy.append(result)
    
    # Display results
    if healthy:
        print("🟢 HEALTHY SERVICES:")
        print("-" * 70)
        for service in healthy:
            print(f"  ✅ {service['name'].upper()}")
            print(f"     URL: {service['url']}")
            print(f"     Description: {service['description']}")
            if service.get('details'):
                print(f"     Details: {json.dumps(service['details'], indent=8)}")
            print()
    
    if unhealthy:
        print("🔴 UNHEALTHY SERVICES:")
        print("-" * 70)
        for service in unhealthy:
            print(f"  {service['status']} {service['name'].upper()}")
            print(f"     URL: {service['url']}")
            print(f"     Description: {service['description']}")
            if service.get('error'):
                print(f"     Error: {service['error']}")
            print()
    
    # Summary
    print("=" * 70)
    print(" SUMMARY")
    print("=" * 70)
    print(f"  Total Services: {len(SERVICES)}")
    print(f"  ✅ Healthy: {len(healthy)}")
    print(f"  ❌ Unhealthy: {len(unhealthy)}")
    print(f"  Health Score: {len(healthy)}/{len(SERVICES)} ({len(healthy)*100//len(SERVICES)}%)")
    print("=" * 70)
    
    # Return structured data
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(SERVICES),
            "healthy": len(healthy),
            "unhealthy": len(unhealthy),
            "health_percentage": len(healthy) * 100 // len(SERVICES)
        },
        "services": {
            "healthy": healthy,
            "unhealthy": unhealthy
        }
    }

async def main():
    """Main entry point."""
    try:
        result = await check_all_services()
        
        # Save results to file
        with open("service_health_report.json", "w") as f:
            json.dump(result, f, indent=2)
        print()
        print("📄 Report saved to: service_health_report.json")
        
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
