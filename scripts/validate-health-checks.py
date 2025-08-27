#!/usr/bin/env python3
"""
Health Check Validation Script
Tests all service health endpoints
"""

import asyncio
import aiohttp
import json
from typing import Dict, List
from pathlib import Path

async def test_health_endpoint(service_name: str, base_url: str) -> Dict:
    """Test health endpoints for a service"""
    
    endpoints = [
        '/health',
        '/health/quick', 
        '/health/ready',
        '/health/live'
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    results[endpoint] = {
                        "status_code": response.status,
                        "response_time_ms": response.headers.get('X-Response-Time', 'unknown'),
                        "status": "success" if response.status < 400 else "failure"
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            results[endpoint]["response_data"] = data
                        except:
                            results[endpoint]["response_data"] = await response.text()
                            
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
    
    return results

async def validate_all_health_checks():
    """Validate health checks for all services"""
    
    print("🏥 Validating health check implementations...")
    
    # Services to test (adjust based on actual deployment)
    services = [
        ("mcp-context", "http://localhost:8080"),
        ("mcp-agents", "http://localhost:8081"),
        ("mcp-research", "http://localhost:8082"),
        ("agno-coordinator", "http://localhost:8083"),
        ("agno-teams", "http://localhost:8084")
    ]
    
    results = {}
    
    for service_name, base_url in services:
        print(f"  🔍 Testing {service_name}...")
        results[service_name] = await test_health_endpoint(service_name, base_url)
        
        # Summary for this service
        endpoints_tested = len(results[service_name])
        successful_endpoints = sum(1 for result in results[service_name].values() 
                                 if result.get("status") == "success")
        
        print(f"    ✅ {successful_endpoints}/{endpoints_tested} endpoints healthy")
    
    # Generate report
    print("\n📊 Health Check Validation Report:")
    for service, service_results in results.items():
        print(f"\n{service}:")
        for endpoint, result in service_results.items():
            status_icon = "✅" if result.get("status") == "success" else "❌"
            print(f"  {status_icon} {endpoint}: {result.get('status_code', 'N/A')}")
    
    return results

if __name__ == "__main__":
    asyncio.run(validate_all_health_checks())
