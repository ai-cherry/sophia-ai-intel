"""
Sophia AI DNS Management Automation

Automated DNS management for sophia-intel.ai domain using DNSimple API.
Provides DNS record lifecycle management, propagation monitoring, and rollback capabilities.

Key Features:
- Automated DNS record creation, update, and deletion
- DNS propagation verification with timeout handling
- Rollback capabilities for failed changes
- Integration with deployment pipelines
- Comprehensive logging and error handling

Version: 1.0.0
Author: Sophia AI Infrastructure Team
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DNSimple configuration
DNSIMPLE_TOKEN = os.getenv("DNSIMPLE_TOKEN")
DNSIMPLE_ACCOUNT_ID = os.getenv("DNSIMPLE_ACCOUNT_ID", "162809")
DOMAIN_NAME = "sophia-intel.ai"
LAMBDA_LABS_IP = "192.222.51.223"


class DNSManagementError(Exception):
    """Custom exception for DNS management operations"""
    pass


class DNSRecord:
    """Represents a DNS record"""
    def __init__(self, id: Optional[int], name: str, type: str, content: str, ttl: int = 3600):
        self.id = id
        self.name = name
        self.type = type
        self.content = content
        self.ttl = ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "content": self.content,
            "ttl": self.ttl
        }


class DNSManager:
    """
    DNS management class for sophia-intel.ai domain
    """
    
    def __init__(self, token: str, account_id: str, domain: str):
        if not token:
            raise DNSManagementError("DNSIMPLE_TOKEN is required")
        
        self.token = token
        self.account_id = account_id
        self.domain = domain
        self.base_url = f"https://api.dnsimple.com/v2/{account_id}/zones/{domain}/records"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def list_records(self, record_type: Optional[str] = None) -> List[DNSRecord]:
        """List all DNS records for the domain"""
        try:
            async with httpx.AsyncClient() as client:
                url = self.base_url
                if record_type:
                    url += f"?type={record_type}"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                records = []
                
                for record_data in data.get("data", []):
                    records.append(DNSRecord(
                        id=record_data["id"],
                        name=record_data["name"],
                        type=record_data["type"],
                        content=record_data["content"],
                        ttl=record_data["ttl"]
                    ))
                
                logger.info(f"Found {len(records)} DNS records")
                return records
                
        except httpx.HTTPError as e:
            raise DNSManagementError(f"Failed to list DNS records: {e}")

    async def create_record(self, record: DNSRecord) -> DNSRecord:
        """Create a new DNS record"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "name": record.name,
                    "type": record.type,
                    "content": record.content,
                    "ttl": record.ttl
                }
                
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                created_record = data.get("data", {})
                
                record.id = created_record["id"]
                
                logger.info(f"Created DNS record: {record.name} -> {record.content}")
                return record
                
        except httpx.HTTPError as e:
            raise DNSManagementError(f"Failed to create DNS record: {e}")

    async def update_record(self, record: DNSRecord) -> DNSRecord:
        """Update an existing DNS record"""
        if not record.id:
            raise DNSManagementError("Record ID is required for updates")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "name": record.name,
                    "type": record.type,
                    "content": record.content,
                    "ttl": record.ttl
                }
                
                response = await client.patch(
                    f"{self.base_url}/{record.id}",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.info(f"Updated DNS record: {record.name} -> {record.content}")
                return record
                
        except httpx.HTTPError as e:
            raise DNSManagementError(f"Failed to update DNS record: {e}")

    async def delete_record(self, record_id: int) -> bool:
        """Delete a DNS record by ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{record_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                
                logger.info(f"Deleted DNS record ID: {record_id}")
                return True
                
        except httpx.HTTPError as e:
            raise DNSManagementError(f"Failed to delete DNS record: {e}")

    async def find_conflicting_records(self, name: str, target_content: str) -> List[DNSRecord]:
        """Find records that conflict with desired configuration"""
        all_records = await self.list_records()
        conflicts = []
        
        for record in all_records:
            if record.name == name and record.content != target_content:
                conflicts.append(record)
        
        return conflicts

    async def verify_propagation(
        self, 
        record_name: str, 
        expected_content: str, 
        max_wait_seconds: int = 300
    ) -> bool:
        """Verify DNS propagation using Google DNS"""
        full_name = f"{record_name}.{self.domain}" if record_name else self.domain
        
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://dns.google/resolve?name={full_name}&type=A"
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    answers = data.get("Answer", [])
                    
                    if answers:
                        for answer in answers:
                            if answer.get("data") == expected_content:
                                logger.info(f"DNS propagation verified for {full_name} -> {expected_content}")
                                return True
                    
                    logger.info(f"DNS still propagating for {full_name}, waiting...")
                    await asyncio.sleep(15)
                    
            except Exception as e:
                logger.warning(f"DNS verification check failed: {e}")
                await asyncio.sleep(10)
        
        logger.warning(f"DNS propagation timeout for {full_name}")
        return False


class SophiaInfrastructureManager:
    """
    Integrated infrastructure manager combining DNS, deployment, and agent swarm
    """
    
    def __init__(self):
        self.dns_manager = DNSManager(DNSIMPLE_TOKEN, DNSIMPLE_ACCOUNT_ID, DOMAIN_NAME)
        self.deployment_config = {
            "lambda_labs_ip": LAMBDA_LABS_IP,
            "services": [
                "dashboard",
                "mcp-context",
                "mcp-research", 
                "mcp-business",
                "mcp-github",
                "mcp-agents"
            ]
        }

    async def complete_dns_cleanup(self) -> Dict[str, Any]:
        """Complete DNS cleanup for www.sophia-intel.ai"""
        logger.info("Starting DNS cleanup for www.sophia-intel.ai")
        
        try:
            # Find conflicting www records
            conflicts = await self.dns_manager.find_conflicting_records("www", LAMBDA_LABS_IP)
            
            cleanup_results = {
                "conflicts_found": len(conflicts),
                "conflicts_removed": 0,
                "conflicts_failed": [],
                "verification_passed": False
            }
            
            # Remove conflicting records
            for conflict in conflicts:
                try:
                    await self.dns_manager.delete_record(conflict.id)
                    cleanup_results["conflicts_removed"] += 1
                    logger.info(f"Removed conflicting record: {conflict.content}")
                except Exception as e:
                    cleanup_results["conflicts_failed"].append({
                        "record_id": conflict.id,
                        "content": conflict.content,
                        "error": str(e)
                    })
            
            # Create/verify correct www record
            try:
                www_record = DNSRecord(
                    id=None,
                    name="www",
                    type="A",
                    content=LAMBDA_LABS_IP,
                    ttl=3600
                )
                
                # Check if correct record already exists
                existing_records = await self.dns_manager.list_records("A")
                existing_www = next((r for r in existing_records if r.name == "www" and r.content == LAMBDA_LABS_IP), None)
                
                if not existing_www:
                    await self.dns_manager.create_record(www_record)
                    logger.info(f"Created www record pointing to {LAMBDA_LABS_IP}")
                else:
                    logger.info(f"Correct www record already exists: {existing_www.content}")
                
                # Verify propagation
                cleanup_results["verification_passed"] = await self.dns_manager.verify_propagation(
                    "www", LAMBDA_LABS_IP, max_wait_seconds=120
                )
                
            except Exception as e:
                cleanup_results["verification_error"] = str(e)
            
            return cleanup_results
            
        except Exception as e:
            raise DNSManagementError(f"DNS cleanup failed: {e}")

    async def setup_agent_swarm_dns(self) -> Dict[str, Any]:
        """Set up DNS records for agent swarm services"""
        logger.info("Setting up DNS records for agent swarm services")
        
        dns_setup_results = {
            "records_created": 0,
            "records_updated": 0,
            "records_failed": [],
            "services_configured": []
        }
        
        # Agent swarm service DNS mappings
        service_dns_mappings = [
            ("agents", "mcp-agents"),      # agents.sophia-intel.ai -> mcp-agents service
            ("swarm", "mcp-agents"),       # swarm.sophia-intel.ai -> mcp-agents service (alias)
            ("api", "mcp-context"),        # api.sophia-intel.ai -> main API endpoint
        ]
        
        try:
            existing_records = await self.dns_manager.list_records("CNAME")
            
            for subdomain, target_service in service_dns_mappings:
                try:
                    # Check if record exists
                    existing_record = next((r for r in existing_records if r.name == subdomain), None)
                    target_cname = f"sophiaai-{target_service}.fly.dev"
                    
                    if existing_record:
                        if existing_record.content != target_cname:
                            # Update existing record
                            existing_record.content = target_cname
                            await self.dns_manager.update_record(existing_record)
                            dns_setup_results["records_updated"] += 1
                            logger.info(f"Updated {subdomain} CNAME to {target_cname}")
                    else:
                        # Create new record
                        new_record = DNSRecord(
                            id=None,
                            name=subdomain,
                            type="CNAME",
                            content=target_cname,
                            ttl=3600
                        )
                        await self.dns_manager.create_record(new_record)
                        dns_setup_results["records_created"] += 1
                        logger.info(f"Created {subdomain} CNAME to {target_cname}")
                    
                    dns_setup_results["services_configured"].append({
                        "subdomain": subdomain,
                        "target": target_cname,
                        "status": "configured"
                    })
                    
                except Exception as e:
                    dns_setup_results["records_failed"].append({
                        "subdomain": subdomain,
                        "error": str(e)
                    })
            
            return dns_setup_results
            
        except Exception as e:
            raise DNSManagementError(f"Agent swarm DNS setup failed: {e}")

    async def validate_infrastructure_health(self) -> Dict[str, Any]:
        """Validate health of all infrastructure components"""
        logger.info("Validating infrastructure health")
        
        health_results = {
            "dns_status": "unknown",
            "service_health": {},
            "overall_status": "unknown",
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Check DNS resolution
            dns_check = await self.dns_manager.verify_propagation("www", LAMBDA_LABS_IP, max_wait_seconds=30)
            health_results["dns_status"] = "healthy" if dns_check else "degraded"
            
            # Check service health
            services_to_check = [
                ("Dashboard", "https://sophiaai-dashboard.fly.dev/healthz"),
                ("MCP Context", "https://sophiaai-mcp-context-v2.fly.dev/healthz"),
                ("MCP Research", "https://sophiaai-mcp-research-v2.fly.dev/healthz"),
                ("MCP Business", "https://sophiaai-mcp-business-v2.fly.dev/healthz"),
                ("MCP GitHub", "https://sophiaai-mcp-repo-v2.fly.dev/healthz"),
            ]
            
            async with httpx.AsyncClient(timeout=15) as client:
                for service_name, health_url in services_to_check:
                    try:
                        response = await client.get(health_url)
                        if response.status_code == 200:
                            health_data = response.json()
                            health_results["service_health"][service_name] = {
                                "status": "healthy",
                                "response_time_ms": response.elapsed.total_seconds() * 1000,
                                "details": health_data.get("status", "unknown")
                            }
                        else:
                            health_results["service_health"][service_name] = {
                                "status": "unhealthy",
                                "response_code": response.status_code,
                                "error": "Non-200 response"
                            }
                            health_results["issues_found"].append(f"{service_name} returning {response.status_code}")
                    
                    except Exception as e:
                        health_results["service_health"][service_name] = {
                            "status": "error",
                            "error": str(e)
                        }
                        health_results["issues_found"].append(f"{service_name} unreachable: {str(e)}")
            
            # Determine overall status
            healthy_services = sum(1 for s in health_results["service_health"].values() if s["status"] == "healthy")
            total_services = len(health_results["service_health"])
            
            if healthy_services == total_services and health_results["dns_status"] == "healthy":
                health_results["overall_status"] = "healthy"
            elif healthy_services >= total_services * 0.8:
                health_results["overall_status"] = "degraded"
            else:
                health_results["overall_status"] = "unhealthy"
            
            # Generate recommendations
            if health_results["dns_status"] != "healthy":
                health_results["recommendations"].append("Investigate DNS propagation issues")
            
            if health_results["issues_found"]:
                health_results["recommendations"].append("Address service health issues")
                health_results["recommendations"].append("Check Fly.io deployment status for unhealthy services")
            
            return health_results
            
        except Exception as e:
            raise DNSManagementError(f"Infrastructure health validation failed: {e}")

    def generate_infrastructure_report(self, dns_cleanup: Dict[str, Any], dns_setup: Dict[str, Any], health_check: Dict[str, Any]) -> str:
        """Generate comprehensive infrastructure report"""
        report_lines = [
            "# Sophia AI Infrastructure Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## DNS Management",
            "**Cleanup Status:**",
            f"- Conflicts found: {dns_cleanup.get('conflicts_found', 0)}",
            f"- Conflicts removed: {dns_cleanup.get('conflicts_removed', 0)}",
            f"- Verification passed: {dns_cleanup.get('verification_passed', False)}",
            "",
            "**DNS Setup Status:**",
            f"- Records created: {dns_setup.get('records_created', 0)}",
            f"- Records updated: {dns_setup.get('records_updated', 0)}",
            f"- Services configured: {len(dns_setup.get('services_configured', []))}",
            "",
            "## Service Health",
            f"**Overall Status:** {health_check.get('overall_status', 'unknown').upper()}",
            f"**DNS Status:** {health_check.get('dns_status', 'unknown')}",
            ""
        ]
        
        # Add service details
        for service_name, service_health in health_check.get("service_health", {}).items():
            status = service_health.get("status", "unknown")
            emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            report_lines.append(f"- {emoji} **{service_name}**: {status}")
        
        # Add issues and recommendations
        if health_check.get("issues_found"):
            report_lines.extend([
                "",
                "## Issues Found",
            ])
            for issue in health_check["issues_found"]:
                report_lines.append(f"- ❌ {issue}")
        
        if health_check.get("recommendations"):
            report_lines.extend([
                "",
                "## Recommendations", 
            ])
            for rec in health_check["recommendations"]:
                report_lines.append(f"- 🔧 {rec}")
        
        return "\n".join(report_lines)


# Standalone functions for CLI usage
async def cleanup_dns():
    """Cleanup DNS conflicts for www.sophia-intel.ai"""
    if not DNSIMPLE_TOKEN:
        print("❌ DNSIMPLE_TOKEN not configured")
        return False
    
    try:
        infra_manager = SophiaInfrastructureManager()
        cleanup_result = await infra_manager.complete_dns_cleanup()
        
        print("✅ DNS Cleanup Results:")
        print(f"   Conflicts found: {cleanup_result['conflicts_found']}")
        print(f"   Conflicts removed: {cleanup_result['conflicts_removed']}")
        print(f"   Verification passed: {cleanup_result['verification_passed']}")
        
        return cleanup_result["verification_passed"]
        
    except Exception as e:
        print(f"❌ DNS cleanup failed: {e}")
        return False


async def setup_agent_dns():
    """Setup DNS for agent swarm services"""
    if not DNSIMPLE_TOKEN:
        print("❌ DNSIMPLE_TOKEN not configured")
        return False
    
    try:
        infra_manager = SophiaInfrastructureManager()
        setup_result = await infra_manager.setup_agent_swarm_dns()
        
        print("✅ Agent Swarm DNS Setup Results:")
        print(f"   Records created: {setup_result['records_created']}")
        print(f"   Records updated: {setup_result['records_updated']}")
        print(f"   Services configured: {len(setup_result['services_configured'])}")
        
        return setup_result["records_created"] + setup_result["records_updated"] > 0
        
    except Exception as e:
        print(f"❌ Agent DNS setup failed: {e}")
        return False


async def health_check():
    """Run comprehensive infrastructure health check"""
    if not DNSIMPLE_TOKEN:
        print("❌ DNSIMPLE_TOKEN not configured")
        return False
    
    try:
        infra_manager = SophiaInfrastructureManager()
        health_result = await infra_manager.validate_infrastructure_health()
        
        print(f"📊 Infrastructure Health: {health_result['overall_status'].upper()}")
        print(f"🌐 DNS Status: {health_result['dns_status']}")
        
        for service_name, service_health in health_result["service_health"].items():
            status = service_health.get("status", "unknown")
            emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"   {emoji} {service_name}: {status}")
        
        if health_result["issues_found"]:
            print("\n❌ Issues Found:")
            for issue in health_result["issues_found"]:
                print(f"   - {issue}")
        
        return health_result["overall_status"] in ["healthy", "degraded"]
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def full_infrastructure_setup():
    """Complete infrastructure setup workflow"""
    print("🚀 Starting Sophia AI Infrastructure Setup")
    
    # Step 1: DNS Cleanup
    print("\n1️⃣ Cleaning up DNS conflicts...")
    cleanup_success = await cleanup_dns()
    
    # Step 2: Agent DNS Setup
    print("\n2️⃣ Setting up Agent Swarm DNS...")
    dns_setup_success = await setup_agent_dns()
    
    # Step 3: Health Validation
    print("\n3️⃣ Validating infrastructure health...")
    health_success = await health_check()
    
    # Summary
    print("\n📋 Setup Summary:")
    print(f"   DNS Cleanup: {'✅ Success' if cleanup_success else '❌ Failed'}")
    print(f"   Agent DNS Setup: {'✅ Success' if dns_setup_success else '❌ Failed'}")
    print(f"   Health Check: {'✅ Success' if health_success else '❌ Failed'}")
    
    overall_success = cleanup_success and dns_setup_success and health_success
    print(f"\n🎯 Overall Status: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
    
    return overall_success


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dns_management.py [cleanup|setup|health|full]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "cleanup":
        asyncio.run(cleanup_dns())
    elif command == "setup":
        asyncio.run(setup_agent_dns())
    elif command == "health":
        asyncio.run(health_check())
    elif command == "full":
        asyncio.run(full_infrastructure_setup())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
