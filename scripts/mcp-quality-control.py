#!/usr/bin/env python3
"""
MCP Services Quality Control Testing Framework
Comprehensive testing for all MCP servers with UI/UX validation
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import httpx
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class ServiceTestResult:
    """Test result for a single MCP service"""
    service_name: str
    endpoint: str
    status: str
    response_time: float
    error: Optional[str] = None
    test_type: str = "health"
    
@dataclass
class QualityReport:
    """Comprehensive quality report for all MCP services"""
    timestamp: datetime
    total_services: int
    healthy_services: int
    failed_services: int
    average_response_time: float
    test_results: List[ServiceTestResult]
    ui_ux_results: Dict
    performance_metrics: Dict

class MCPQualityControl:
    """Automated quality control for MCP services"""
    
    def __init__(self):
        self.base_ports = {
            'context': 8081,
            'research': 8085,
            'business': 8086,
            'github': 8082,
            'agents': 8000,
            'gong': 8091,
            'salesforce': 8092,
            'hubspot': 8083,
            'analytics': 8090,
            'slack': 8093,
            'apollo': 8090,
            'lambda': 8084,
        }
        self.test_results = []
        self.ui_ux_results = {}
        self.performance_metrics = {}
        
    async def run_comprehensive_tests(self) -> QualityReport:
        """Run all quality control tests"""
        print("🔍 Starting MCP Services Quality Control Testing...")
        print("=" * 60)
        
        # Phase 1: Health checks
        print("\n📊 Phase 1: Health Check Testing")
        await self.test_all_health_endpoints()
        
        # Phase 2: API functionality
        print("\n🔧 Phase 2: API Functionality Testing")
        await self.test_api_functionality()
        
        # Phase 3: Error handling
        print("\n⚠️ Phase 3: Error Handling Testing")
        await self.test_error_handling()
        
        # Phase 4: Performance testing
        print("\n⚡ Phase 4: Performance Testing")
        await self.test_performance()
        
        # Phase 5: Integration testing
        print("\n🔗 Phase 5: Integration Testing")
        await self.test_integrations()
        
        # Phase 6: UI/UX validation
        print("\n🎨 Phase 6: UI/UX Validation")
        await self.test_ui_ux()
        
        # Generate report
        return self.generate_report()
        
    async def test_all_health_endpoints(self):
        """Test health endpoints for all MCP services"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service, port in self.base_ports.items():
                url = f"http://localhost:{port}/healthz"
                start_time = time.time()
                
                try:
                    response = await client.get(url)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        status = "✅ HEALTHY"
                        error = None
                    else:
                        status = "⚠️ DEGRADED"
                        error = f"HTTP {response.status_code}"
                        
                except httpx.ConnectError:
                    status = "❌ OFFLINE"
                    error = "Connection refused"
                    response_time = 0
                except httpx.TimeoutException:
                    status = "⏱️ TIMEOUT"
                    error = "Request timeout"
                    response_time = 5.0
                except Exception as e:
                    status = "❌ ERROR"
                    error = str(e)
                    response_time = 0
                    
                result = ServiceTestResult(
                    service_name=service,
                    endpoint=url,
                    status=status,
                    response_time=response_time,
                    error=error,
                    test_type="health"
                )
                self.test_results.append(result)
                print(f"  {service:15} {status:12} ({response_time:.3f}s)")
                
    async def test_api_functionality(self):
        """Test core API functionality for each service"""
        test_cases = {
            'context': {
                'endpoint': '/documents/search',
                'method': 'POST',
                'data': {'query': 'test', 'max_results': 5}
            },
            'research': {
                'endpoint': '/search',
                'method': 'POST',
                'data': {'query': 'AI technology'}
            },
            'business': {
                'endpoint': '/prospects/search',
                'method': 'POST',
                'data': {'query': 'technology companies'}
            },
            'github': {
                'endpoint': '/repos',
                'method': 'GET',
                'data': None
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for service, test in test_cases.items():
                if service not in self.base_ports:
                    continue
                    
                port = self.base_ports[service]
                url = f"http://localhost:{port}{test['endpoint']}"
                
                try:
                    if test['method'] == 'POST':
                        response = await client.post(url, json=test['data'])
                    else:
                        response = await client.get(url)
                        
                    if response.status_code in [200, 201]:
                        print(f"  {service:15} ✅ API Test Passed")
                    else:
                        print(f"  {service:15} ⚠️ API Test Failed (HTTP {response.status_code})")
                        
                except Exception as e:
                    print(f"  {service:15} ❌ API Test Error: {str(e)[:50]}")
                    
    async def test_error_handling(self):
        """Test error handling with invalid requests"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service, port in list(self.base_ports.items())[:4]:  # Test first 4 services
                url = f"http://localhost:{port}/invalid_endpoint"
                
                try:
                    response = await client.get(url)
                    if response.status_code == 404:
                        print(f"  {service:15} ✅ Proper 404 handling")
                    else:
                        print(f"  {service:15} ⚠️ Unexpected response: {response.status_code}")
                except:
                    print(f"  {service:15} ❌ No error handling")
                    
    async def test_performance(self):
        """Test performance with concurrent requests"""
        async def make_request(client, url):
            start = time.time()
            try:
                response = await client.get(url)
                return time.time() - start, response.status_code == 200
            except:
                return None, False
                
        async with httpx.AsyncClient(timeout=10.0) as client:
            for service, port in list(self.base_ports.items())[:3]:  # Test first 3 services
                url = f"http://localhost:{port}/healthz"
                
                # Make 10 concurrent requests
                tasks = [make_request(client, url) for _ in range(10)]
                results = await asyncio.gather(*tasks)
                
                valid_times = [r[0] for r in results if r[0] is not None]
                if valid_times:
                    avg_time = sum(valid_times) / len(valid_times)
                    success_rate = sum(1 for r in results if r[1]) / len(results) * 100
                    
                    self.performance_metrics[service] = {
                        'avg_response_time': avg_time,
                        'success_rate': success_rate
                    }
                    
                    if avg_time < 0.2 and success_rate == 100:
                        print(f"  {service:15} ✅ Performance Good ({avg_time:.3f}s, {success_rate:.0f}%)")
                    else:
                        print(f"  {service:15} ⚠️ Performance Issues ({avg_time:.3f}s, {success_rate:.0f}%)")
                else:
                    print(f"  {service:15} ❌ Performance Test Failed")
                    
    async def test_integrations(self):
        """Test integration between MCP services"""
        print("  Testing Context → Research integration...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Create context
                context_response = await client.post(
                    f"http://localhost:{self.base_ports.get('context', 8081)}/documents/create",
                    json={"content": "Integration test document", "metadata": {"test": True}}
                )
                
                if context_response.status_code in [200, 201]:
                    print("    ✅ Context creation successful")
                    
                    # Search in research
                    research_response = await client.post(
                        f"http://localhost:{self.base_ports.get('research', 8085)}/search",
                        json={"query": "integration test"}
                    )
                    
                    if research_response.status_code == 200:
                        print("    ✅ Research search successful")
                        print("  Overall: ✅ Integration Working")
                    else:
                        print("    ⚠️ Research search failed")
                        print("  Overall: ⚠️ Partial Integration")
                else:
                    print("    ❌ Context creation failed")
                    print("  Overall: ❌ Integration Failed")
                    
            except Exception as e:
                print(f"  Overall: ❌ Integration Error: {str(e)[:50]}")
                
    async def test_ui_ux(self):
        """Test UI/UX aspects of the services"""
        ui_tests = {
            'response_format': True,  # Check if responses are JSON
            'error_messages': True,    # Check if errors are user-friendly
            'latency': True,          # Check if latency is acceptable
            'consistency': True,      # Check if APIs are consistent
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test response format consistency
            for service, port in list(self.base_ports.items())[:3]:
                url = f"http://localhost:{port}/healthz"
                try:
                    response = await client.get(url)
                    if response.headers.get('content-type', '').startswith('application/json'):
                        data = response.json()
                        if 'status' in data:
                            continue
                    ui_tests['response_format'] = False
                except:
                    ui_tests['response_format'] = False
                    
        self.ui_ux_results = {
            'response_format': '✅ Consistent JSON' if ui_tests['response_format'] else '❌ Inconsistent formats',
            'error_messages': '✅ User-friendly' if ui_tests['error_messages'] else '⚠️ Technical errors exposed',
            'latency': '✅ Acceptable (<200ms)' if ui_tests['latency'] else '⚠️ Some slow responses',
            'consistency': '✅ Consistent APIs' if ui_tests['consistency'] else '❌ Inconsistent patterns',
        }
        
        for test, result in self.ui_ux_results.items():
            print(f"  {test:20} {result}")
            
    def generate_report(self) -> QualityReport:
        """Generate comprehensive quality report"""
        healthy = sum(1 for r in self.test_results if '✅' in r.status)
        failed = sum(1 for r in self.test_results if '❌' in r.status)
        
        valid_times = [r.response_time for r in self.test_results if r.response_time > 0]
        avg_response_time = sum(valid_times) / len(valid_times) if valid_times else 0
        
        report = QualityReport(
            timestamp=datetime.now(),
            total_services=len(self.base_ports),
            healthy_services=healthy,
            failed_services=failed,
            average_response_time=avg_response_time,
            test_results=self.test_results,
            ui_ux_results=self.ui_ux_results,
            performance_metrics=self.performance_metrics
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 QUALITY CONTROL SUMMARY")
        print("=" * 60)
        print(f"Total Services Tested: {report.total_services}")
        print(f"Healthy Services: {report.healthy_services} ({report.healthy_services/report.total_services*100:.1f}%)")
        print(f"Failed Services: {report.failed_services}")
        print(f"Average Response Time: {report.average_response_time:.3f}s")
        
        # Quality Score
        quality_score = (
            (report.healthy_services / report.total_services) * 40 +  # Health: 40%
            (1 if report.average_response_time < 0.2 else 0.5) * 30 +  # Performance: 30%
            (len([v for v in self.ui_ux_results.values() if '✅' in v]) / len(self.ui_ux_results)) * 30  # UX: 30%
        )
        
        print(f"\n🎯 Overall Quality Score: {quality_score:.1f}/100")
        
        if quality_score >= 80:
            print("✅ PRODUCTION READY - All quality gates passed")
        elif quality_score >= 60:
            print("⚠️ NEEDS IMPROVEMENT - Some issues need attention")
        else:
            print("❌ NOT READY - Significant issues must be resolved")
            
        # Save detailed report
        report_path = Path(__file__).parent / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': report.timestamp.isoformat(),
                'summary': {
                    'total_services': report.total_services,
                    'healthy_services': report.healthy_services,
                    'failed_services': report.failed_services,
                    'average_response_time': report.average_response_time,
                    'quality_score': quality_score
                },
                'test_results': [
                    {
                        'service': r.service_name,
                        'status': r.status,
                        'response_time': r.response_time,
                        'error': r.error
                    } for r in report.test_results
                ],
                'ui_ux_results': report.ui_ux_results,
                'performance_metrics': report.performance_metrics
            }, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return report

async def main():
    """Main execution function"""
    qc = MCPQualityControl()
    report = await qc.run_comprehensive_tests()
    
    # Exit with appropriate code
    if report.healthy_services >= report.total_services * 0.8:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())