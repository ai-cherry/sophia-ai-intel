#!/usr/bin/env python3
"""
Agent Infrastructure Management Script
=====================================

Allows agents to provision and manage infrastructure without manual API key handling.
Uses GitHub Secrets -> Pulumi -> Fly.io chain for automated secrets management.
"""

import os
import subprocess
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AgentInfraManager:
    """Infrastructure management for AI agents - no manual key handling"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.pulumi_dir = self.project_root / "ops" / "pulumi"
        self.secrets_count = 0
        self.services_managed = []
    
    def provision_infrastructure(self) -> Dict[str, Any]:
        """Provision all infrastructure using Pulumi with automatic secret injection"""
        
        print("🚀 Agent Infrastructure Provisioning Started")
        print("=" * 60)
        
        # Verify secrets are loaded from GitHub
        github_secrets = self._audit_github_secrets()
        
        if github_secrets["count"] < 10:
            print(f"⚠️ Warning: Only {github_secrets['count']} secrets available")
            print("   GitHub Codespaces should auto-load org secrets")
        else:
            print(f"✅ {github_secrets['count']} secrets loaded from GitHub org")
        
        # Initialize Pulumi if needed
        self._ensure_pulumi_initialized()
        
        # Run Pulumi deployment
        result = self._run_pulumi_up()
        
        return {
            "provision_success": result["success"],
            "secrets_managed": github_secrets["count"],
            "services_deployed": result.get("services", []),
            "pulumi_outputs": result.get("outputs", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_accessible": True,
            "manual_keys_required": False  # This is the key win
        }
    
    def update_infrastructure(self) -> Dict[str, Any]:
        """Update infrastructure (add services, modify configs, etc.)"""
        
        print("🔄 Agent Infrastructure Update Started")
        
        # Refresh Pulumi state
        refresh_result = self._run_command(
            ["pulumi", "refresh", "--yes"],
            cwd=self.pulumi_dir,
            description="Refreshing infrastructure state"
        )
        
        # Apply updates
        update_result = self._run_pulumi_up()
        
        return {
            "update_success": update_result["success"],
            "refresh_success": refresh_result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def add_mcp_service(self, service_name: str, api_keys_needed: list) -> Dict[str, Any]:
        """Add new MCP service with automatic secret injection"""
        
        print(f"➕ Adding MCP service: {service_name}")
        
        # This would modify the Pulumi stack to add a new service
        # For now, return the pattern agents can follow
        
        return {
            "service_name": service_name,
            "app_name": f"sophiaai-mcp-{service_name}-v2",
            "secrets_required": api_keys_needed,
            "pulumi_command": f"# Add to ops/pulumi/__main__.py:\n{service_name}_app, {service_name}_machines = create_mcp_service('{service_name}', {service_name}_env, ['ord', 'iad'])",
            "agent_accessible": True
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of all managed services"""
        
        try:
            # Get Pulumi stack outputs
            outputs_result = self._run_command(
                ["pulumi", "stack", "output", "--json"],
                cwd=self.pulumi_dir,
                description="Getting stack outputs"
            )
            
            if outputs_result["success"]:
                outputs = json.loads(outputs_result["output"])
                return {
                    "stack_outputs": outputs,
                    "services_managed": outputs.get("services-deployed", []),
                    "regions_active": outputs.get("regions-deployed", []),
                    "dashboard_url": outputs.get("dashboard-url", ""),
                    "agent_endpoints": outputs.get("agent-endpoints", {}),
                    "total_secrets": outputs.get("total-secrets-configured", 0)
                }
            else:
                return {"error": "Could not retrieve stack status"}
                
        except Exception as e:
            return {"error": f"Status check failed: {e}"}
    
    def _audit_github_secrets(self) -> Dict[str, Any]:
        """Audit available GitHub secrets in environment"""
        
        critical_secrets = [
            "GH_PAT_TOKEN", "LAMBDA_API_KEY", "LAMBDA_CLOUD_API_KEY",
            "REDIS_USER_API_KEY", "QDRANT_API_KEY", "NEON_API_TOKEN",
            "GONG_ACCESS_KEY", "HUBSPOT_ACCESS_TOKEN", "SLACK_BOT_TOKEN",
            "NOTION_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
        ]
        
        found_secrets = []
        for secret in critical_secrets:
            if os.getenv(secret):
                found_secrets.append(secret)
        
        return {
            "count": len(found_secrets),
            "critical_found": found_secrets,
            "percentage": (len(found_secrets) / len(critical_secrets)) * 100
        }
    
    def _ensure_pulumi_initialized(self):
        """Ensure Pulumi project is initialized with non-interactive auth"""
        
        # Set environment for non-interactive auth
        env = os.environ.copy()
        env["PULUMI_ACCESS_TOKEN"] = os.getenv("PULUMI_ACCESS_TOKEN")
        
        if not env["PULUMI_ACCESS_TOKEN"]:
            raise ValueError("Missing PULUMI_ACCESS_TOKEN environment variable")
        
        # Login non-interactively
        login_result = self._run_command(
            ["pulumi", "login", "--non-interactive"],
            cwd=self.pulumi_dir,
            description="Logging in to Pulumi",
            env=env
        )
        
        if not login_result["success"]:
            print(f"⚠️ Pulumi login issue: {login_result['error']}")
        
        # Initialize or select stack
        if not (self.pulumi_dir / "Pulumi.sophia-production.yaml").exists():
            print("🔧 Initializing Pulumi stack...")
            
            init_result = self._run_command(
                ["pulumi", "stack", "init", "sophia-production"],
                cwd=self.pulumi_dir,
                description="Initializing Pulumi stack",
                env=env
            )
            
            if not init_result["success"]:
                print(f"⚠️ Stack may already exist: {init_result['error']}")
        else:
            # Select existing stack
            self._run_command(
                ["pulumi", "stack", "select", "sophia-production"],
                cwd=self.pulumi_dir,
                description="Selecting Pulumi stack",
                env=env
            )
    
    def _run_pulumi_up(self) -> Dict[str, Any]:
        """Run Pulumi deployment"""
        
        print("🚀 Running Pulumi deployment...")
        
        result = self._run_command(
            ["pulumi", "up", "--yes", "--skip-preview"],
            cwd=self.pulumi_dir,
            description="Deploying infrastructure",
            timeout=1800  # 30 minutes
        )
        
        if result["success"]:
            # Get outputs
            outputs_result = self._run_command(
                ["pulumi", "stack", "output", "--json"],
                cwd=self.pulumi_dir,
                description="Getting deployment outputs"
            )
            
            if outputs_result["success"]:
                try:
                    outputs = json.loads(outputs_result["output"])
                    result["outputs"] = outputs
                    result["services"] = outputs.get("services-deployed", [])
                except Exception as e:
                    logger.warning(f"Failed to parse outputs: {e}")
                    result["outputs"] = {}
        
        return result
    
    def _run_command(self, cmd: list, cwd: Optional[Path] = None, 
                    description: str = "", timeout: int = 300, env: Optional[Dict] = None) -> Dict[str, Any]:
        """Run command with comprehensive error handling"""
        
        if description:
            print(f"⚙️ {description}...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env or os.environ
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1
            }

# ============================================================================
# AGENT CALLABLE FUNCTIONS
# ============================================================================

def agent_provision() -> Dict[str, Any]:
    """Main function agents call to provision infrastructure"""
    manager = AgentInfraManager()
    return manager.provision_infrastructure()

def agent_update() -> Dict[str, Any]:
    """Function agents call to update infrastructure"""
    manager = AgentInfraManager()
    return manager.update_infrastructure()

def agent_status() -> Dict[str, Any]:
    """Function agents call to get infrastructure status"""
    manager = AgentInfraManager()
    return manager.get_service_status()

def agent_add_service(service_name: str, api_keys: list) -> Dict[str, Any]:
    """Function agents call to add new MCP services"""
    manager = AgentInfraManager()
    return manager.add_mcp_service(service_name, api_keys)

# ============================================================================
# CLI INTERFACE FOR AGENTS
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_infrastructure.py [provision|update|status|add-service]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "provision":
        result = agent_provision()
        print("\n🎯 PROVISIONING RESULT:")
        print(f"   Success: {result['provision_success']}")
        print(f"   Secrets Managed: {result['secrets_managed']}")
        print(f"   Services: {result['services_deployed']}")
        
    elif command == "update":
        result = agent_update()
        print("\n🔄 UPDATE RESULT:")
        print(f"   Success: {result['update_success']}")
        
    elif command == "status":
        result = agent_status()
        print("\n📊 INFRASTRUCTURE STATUS:")
        if "error" not in result:
            print(f"   Services: {result.get('services_managed', [])}")
            print(f"   Regions: {result.get('regions_active', [])}")
            print(f"   Dashboard: {result.get('dashboard_url', 'N/A')}")
        else:
            print(f"   Error: {result['error']}")
    
    elif command == "add-service":
        if len(sys.argv) < 3:
            print("Usage: python agent_infrastructure.py add-service <service-name>")
            sys.exit(1)
        
        service_name = sys.argv[2]
        result = agent_add_service(service_name, [])
        print("\n➕ ADD SERVICE RESULT:")
        print(f"   Service: {result['service_name']}")
        print(f"   App Name: {result['app_name']}")
        print(f"   Agent Accessible: {result['agent_accessible']}")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
