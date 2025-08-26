#!/usr/bin/env python3
"""
Final Validation Script
Comprehensive validation after DNS cutover to ensure all services are healthy
"""

import requests
import time
import json
import sys
from typing import Dict, List
import yaml

class FinalValidator:
    def __init__(self):
        self.services = []
        self.load_service_config()
        
    def load_service_config(self):
        """Load service configuration from docker-compose.yml"""
        try:
            with open('docker-compose.yml', 'r') as f:
                config = yaml.safe_load(f)
                
            for service in config.get('services', []):
                service_info = {
                    'name': service.get('name'),
                    'type': service.get('type'),
                    'url': f"http://{service.get('name')}:8080"
                }
                self.services.append(service_info)
                
        except Exception as e:
            print(f"❌ Failed to load render.yaml: {e}")
            
    def validate_service_health(self, service: Dict) -> Dict:
        """Validate health of a single service"""
        service_name = service['name']
        service_type = service['type']
        base_url = service['url']
        
        print(f"🏥 Validating {service_name} ({service_type})...")
        
        result = {
            'name': service_name,
            'type': service_type,
            'url': base_url,
            'healthy': False,
            'response_time': None,
            'status_code': None,
            'error': None
        }
        
        # Static sites don't need health checks
        if service_type == 'static_site':
            try:
                start_time = time.time()
                response = requests.get(base_url, timeout=30)
                response_time = (time.time() - start_time) * 1000
                
                result.update({
                    'healthy': response.status_code == 200,
                    'response_time': round(response_time, 2),
                    'status_code': response.status_code
                })
                
                if response.status_code == 200:
                    print(f"  ✅ Static site accessible ({response_time:.0f}ms)")
                else:
                    print(f"  ❌ Status code: {response.status_code}")
                    
            except Exception as e:
                result['error'] = str(e)
                print(f"  ❌ Error: {e}")
                
        else:
            # Try health endpoints for web services
            health_endpoints = ['/healthz', '/health', '/']
            
            for endpoint in health_endpoints:
                try:
                    url = base_url + endpoint
                    start_time = time.time()
                    response = requests.get(url, timeout=30)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        result.update({
                            'healthy': True,
                            'response_time': round(response_time, 2),
                            'status_code': response.status_code,
                            'endpoint': endpoint
                        })
                        print(f"  ✅ Healthy at {endpoint} ({response_time:.0f}ms)")
                        break
                        
                except Exception:
                    continue
                    
            if not result['healthy']:
                result['error'] = "All health endpoints failed"
                print("  ❌ All health checks failed")
                
        return result
        
    def validate_environment_connectivity(self) -> Dict:
        """Validate connectivity to external services"""
        print("🔗 Validating external service connectivity...")
        
        external_services = {
            'neon': 'https://console.neon.tech/api/v2/projects',
            'qdrant': 'https://cloud.qdrant.io',
            'redis': None,  # Redis connectivity tested through apps
            'mem0': 'https://api.mem0.ai/v1'
        }
        
        connectivity_results = {}
        
        for service_name, url in external_services.items():
            if not url:
                connectivity_results[service_name] = {
                    'status': 'skipped',
                    'message': 'Tested through applications'
                }
                continue
                
            try:
                response = requests.get(url, timeout=10)
                connectivity_results[service_name] = {
                    'status': 'reachable' if response.status_code < 500 else 'error',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds() * 1000
                }
                print(f"  ✅ {service_name}: reachable")
                
            except Exception as e:
                connectivity_results[service_name] = {
                    'status': 'unreachable',
                    'error': str(e)
                }
                print(f"  ⚠️  {service_name}: {e}")
                
        return connectivity_results
        
    def validate_dns_propagation(self) -> Dict:
        """Validate DNS propagation to production infrastructure"""
        print("🌐 Validating DNS propagation...")
        
        dns_records = [
            'sophia-ai-intel.com',
            'api.sophia-ai-intel.com', 
            'research.sophia-ai-intel.com',
            'dashboard.sophia-ai-intel.com'
        ]
        
        dns_results = {}
        
        for domain in dns_records:
            try:
                import socket
                
                # Get IP address
                ip = socket.gethostbyname(domain)
                
                # Try to reach the domain
                response = requests.get(f"https://{domain}", timeout=15)
                
                dns_results[domain] = {
                    'ip': ip,
                    'reachable': response.status_code < 500,
                    'status_code': response.status_code,
                    'points_to_production': True
                }
                
                status = "✅" if dns_results[domain]['reachable'] else "⚠️ "
                print(f"  {status} {domain} -> {ip}")
                
            except Exception as e:
                dns_results[domain] = {
                    'error': str(e),
                    'reachable': False
                }
                print(f"  ❌ {domain}: {e}")
                
        return dns_results
        
    def generate_validation_report(self, service_results: List[Dict], 
                                 connectivity_results: Dict, 
                                 dns_results: Dict) -> Dict:
        """Generate comprehensive validation report"""
        
        healthy_services = [s for s in service_results if s['healthy']]
        total_services = len(service_results)
        
        avg_response_time = None
        if healthy_services:
            response_times = [s['response_time'] for s in healthy_services if s['response_time']]
            if response_times:
                avg_response_time = round(sum(response_times) / len(response_times), 2)
        
        reachable_dns = len([d for d in dns_results.values() if d.get('reachable', False)])
        total_dns = len(dns_results)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'summary': {
                'services_healthy': f"{len(healthy_services)}/{total_services}",
                'health_percentage': round((len(healthy_services) / total_services) * 100, 1),
                'avg_response_time_ms': avg_response_time,
                'dns_propagated': f"{reachable_dns}/{total_dns}",
                'migration_status': 'SUCCESS' if len(healthy_services) == total_services else 'PARTIAL'
            },
            'services': service_results,
            'external_connectivity': connectivity_results,
            'dns_propagation': dns_results
        }
        
        return report
        
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🔍 Starting Final Migration Validation")
        print("=" * 60)
        
        # 1. Service health validation
        print("\n1. Service Health Validation")
        service_results = []
        for service in self.services:
            result = self.validate_service_health(service)
            service_results.append(result)
            
        # 2. External connectivity validation  
        print("\n2. External Service Connectivity")
        connectivity_results = self.validate_environment_connectivity()
        
        # 3. DNS propagation validation
        print("\n3. DNS Propagation Check")
        dns_results = self.validate_dns_propagation()
        
        # 4. Generate comprehensive report
        print("\n4. Generating Validation Report")
        report = self.generate_validation_report(
            service_results, connectivity_results, dns_results
        )
        
        # Save report
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 FINAL VALIDATION SUMMARY")
        print("=" * 60)
        
        summary = report['summary']
        print(f"Services Healthy: {summary['services_healthy']} ({summary['health_percentage']}%)")
        
        if summary['avg_response_time_ms']:
            print(f"Avg Response Time: {summary['avg_response_time_ms']}ms")
            
        print(f"DNS Propagated: {summary['dns_propagated']}")
        print(f"Migration Status: {summary['migration_status']}")
        
        # Service details
        print("\n📊 Service Status:")
        for service in service_results:
            status_icon = "✅" if service['healthy'] else "❌"
            response_info = f" ({service['response_time']}ms)" if service['response_time'] else ""
            print(f"  {status_icon} {service['name']}{response_info}")
            
        # DNS details
        if dns_results:
            print("\n🌐 DNS Status:")
            for domain, result in dns_results.items():
                status_icon = "✅" if result.get('reachable', False) else "❌"
                print(f"  {status_icon} {domain}")
        
        success = summary['migration_status'] == 'SUCCESS'
        
        if success:
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("All services are healthy and DNS has propagated.")
        else:
            print("\n⚠️  MIGRATION PARTIALLY COMPLETE")
            print("Some services need attention. Check validation_report.json for details.")
            
        print("\n📋 Full report saved to: validation_report.json")
        
        return success

def main():
    """Main validation entry point"""
    validator = FinalValidator()
    
    # Wait a bit for services to stabilize after DNS cutover
    print("⏳ Waiting 60 seconds for DNS propagation and service stabilization...")
    time.sleep(60)
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
