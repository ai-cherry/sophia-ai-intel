#!/usr/bin/env python3
"""
MCP Services Readiness Check Script
Verifies all MCP services are properly configured and ready for deployment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

# Add color support
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    # Fallback if colorama is not installed
    class Fore:
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        RESET_ALL = '\033[0m'

# Try importing required libraries
try:
    from dotenv import load_dotenv
    import yaml
    import requests
except ImportError as e:
    missing_lib = str(e).split("'")[1]
    print(f"{Fore.RED}❌ Missing required library: {missing_lib}")
    print(f"{Fore.YELLOW}Please install: pip install python-dotenv pyyaml requests")
    sys.exit(1)


@dataclass
class MCPServiceCheck:
    """Result of an MCP service check"""
    service_name: str
    check_type: str
    success: bool
    message: str
    details: Optional[Dict] = None


class MCPReadinessChecker:
    """Check MCP services readiness for deployment"""
    
    def __init__(self):
        """Initialize the checker"""
        # Base directory
        self.base_dir = Path("/Users/lynnmusil/sophia-ai-intel-1")
        
        # Load environment variables
        env_path = self.base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # MCP service directories
        self.mcp_dirs = ["mcp", "services"]
        
        # Known MCP services
        self.known_services = [
            "mcp-context",
            "mcp-salesforce",
            "mcp-slack",
            "mcp-gong",
            "mcp-hubspot",
            "mcp-github",
            "analytics-mcp",
            "comms-mcp",
            "crm-mcp",
            "enrichment-mcp",
            "gong-mcp",
            "projects-mcp",
            "support-mcp",
            "agents-swarm"
        ]
        
        # Required environment variables per service category
        self.required_env_vars = {
            "database": [
                "DATABASE_URL",
                "QDRANT_URL",
                "REDIS_URL"
            ],
            "llm": [
                "OPENROUTER_API_KEY",
                "PORTKEY_API_KEY"
            ],
            "business": [
                "GITHUB_APP_ID",
                "GITHUB_APP_PRIVATE_KEY",
                "HUBSPOT_ACCESS_TOKEN",
                "SALESFORCE_ACCESS_TOKEN",
                "SLACK_BOT_TOKEN",
                "GONG_ACCESS_KEY"
            ],
            "infrastructure": [
                "LAMBDA_API_KEY",
                "FLY_API_TOKEN"
            ]
        }
        
        # Fly.io configuration
        self.fly_config_file = self.base_dir / "fly.toml"
        self.services_map_file = self.base_dir / "services.map.json"
        
        # Store check results
        self.checks: List[MCPServiceCheck] = []
    
    def print_header(self):
        """Print header"""
        print(f"\n{Style.BRIGHT}{'='*70}")
        print(f"{Style.BRIGHT}MCP Services Readiness Check")
        print(f"{Style.BRIGHT}{'='*70}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Base Directory: {self.base_dir}")
        print(f"{'='*70}\n")
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'─'*60}")
        print(f"{Style.BRIGHT}{Fore.CYAN}{title}")
        print(f"{Style.BRIGHT}{Fore.CYAN}{'─'*60}")
    
    def print_check_result(self, check: MCPServiceCheck):
        """Print individual check result"""
        status = f"{Fore.GREEN}✅" if check.success else f"{Fore.RED}❌"
        print(f"{status} {check.service_name}: {check.message}")
        if check.details and not check.success:
            for key, value in check.details.items():
                print(f"    {Fore.YELLOW}{key}: {value}")
    
    # ========== SERVICE DISCOVERY ==========
    
    def discover_mcp_services(self) -> List[Dict]:
        """Discover all MCP services in the project"""
        services = []
        
        for mcp_dir in self.mcp_dirs:
            dir_path = self.base_dir / mcp_dir
            if not dir_path.exists():
                continue
            
            # Look for MCP service directories
            for item in dir_path.iterdir():
                if item.is_dir() and ("mcp" in item.name.lower() or item.name in self.known_services):
                    service_info = {
                        "name": item.name,
                        "path": item,
                        "has_dockerfile": (item / "Dockerfile").exists(),
                        "has_app": (item / "app.py").exists() or (item / "main.py").exists(),
                        "has_requirements": (item / "requirements.txt").exists(),
                        "has_fly_config": (item / "fly.toml").exists()
                    }
                    services.append(service_info)
        
        return services
    
    # ========== ENVIRONMENT CHECKS ==========
    
    def check_environment_variables(self) -> List[MCPServiceCheck]:
        """Check if required environment variables are set"""
        checks = []
        
        for category, vars_list in self.required_env_vars.items():
            missing_vars = []
            set_vars = []
            
            for var in vars_list:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
                else:
                    set_vars.append(var)
            
            if missing_vars:
                checks.append(MCPServiceCheck(
                    service_name=f"Environment ({category})",
                    check_type="env_vars",
                    success=False,
                    message=f"{len(missing_vars)} required variables missing",
                    details={"missing": missing_vars}
                ))
            else:
                checks.append(MCPServiceCheck(
                    service_name=f"Environment ({category})",
                    check_type="env_vars",
                    success=True,
                    message=f"All {len(vars_list)} required variables set",
                    details={"variables": set_vars}
                ))
        
        return checks
    
    # ========== SERVICE STRUCTURE CHECKS ==========
    
    def check_service_structure(self, services: List[Dict]) -> List[MCPServiceCheck]:
        """Check if services have proper structure"""
        checks = []
        
        for service in services:
            issues = []
            
            # Check for required files
            if not service["has_dockerfile"]:
                issues.append("Missing Dockerfile")
            
            if not service["has_app"]:
                issues.append("Missing app.py or main.py")
            
            if not service["has_requirements"]:
                issues.append("Missing requirements.txt")
            
            # Create check result
            if issues:
                checks.append(MCPServiceCheck(
                    service_name=service["name"],
                    check_type="structure",
                    success=False,
                    message=f"{len(issues)} structural issues found",
                    details={"issues": issues}
                ))
            else:
                checks.append(MCPServiceCheck(
                    service_name=service["name"],
                    check_type="structure",
                    success=True,
                    message="Service structure valid",
                    details={"path": str(service["path"])}
                ))
        
        return checks
    
    # ========== DOCKERFILE VALIDATION ==========
    
    def validate_dockerfiles(self, services: List[Dict]) -> List[MCPServiceCheck]:
        """Validate Dockerfile contents"""
        checks = []
        
        for service in services:
            if not service["has_dockerfile"]:
                continue
            
            dockerfile_path = service["path"] / "Dockerfile"
            issues = []
            
            try:
                with open(dockerfile_path, 'r') as f:
                    content = f.read()
                    
                    # Check for essential Dockerfile components
                    if "FROM" not in content:
                        issues.append("Missing FROM instruction")
                    
                    if "COPY" not in content and "ADD" not in content:
                        issues.append("No COPY/ADD instructions found")
                    
                    if "RUN" not in content:
                        issues.append("No RUN instructions found")
                    
                    if "CMD" not in content and "ENTRYPOINT" not in content:
                        issues.append("Missing CMD or ENTRYPOINT")
                    
                    # Check for Python-specific patterns
                    if "requirements.txt" in content:
                        if "pip install" not in content:
                            issues.append("requirements.txt referenced but no pip install found")
                
                if issues:
                    checks.append(MCPServiceCheck(
                        service_name=f"{service['name']}/Dockerfile",
                        check_type="dockerfile",
                        success=False,
                        message=f"{len(issues)} Dockerfile issues",
                        details={"issues": issues}
                    ))
                else:
                    checks.append(MCPServiceCheck(
                        service_name=f"{service['name']}/Dockerfile",
                        check_type="dockerfile",
                        success=True,
                        message="Dockerfile valid",
                        details=None
                    ))
                    
            except Exception as e:
                checks.append(MCPServiceCheck(
                    service_name=f"{service['name']}/Dockerfile",
                    check_type="dockerfile",
                    success=False,
                    message=f"Error reading Dockerfile: {str(e)}",
                    details=None
                ))
        
        return checks
    
    # ========== SERVICES MAP VALIDATION ==========
    
    def check_services_map(self) -> MCPServiceCheck:
        """Check if services.map.json exists and is valid"""
        if not self.services_map_file.exists():
            return MCPServiceCheck(
                service_name="services.map.json",
                check_type="config",
                success=False,
                message="File not found",
                details={"expected_path": str(self.services_map_file)}
            )
        
        try:
            with open(self.services_map_file, 'r') as f:
                services_map = json.load(f)
            
            # Validate structure
            if not isinstance(services_map, dict):
                return MCPServiceCheck(
                    service_name="services.map.json",
                    check_type="config",
                    success=False,
                    message="Invalid format: expected object",
                    details=None
                )
            
            # Check for service entries
            service_count = len(services_map)
            
            # Validate each service entry
            issues = []
            for service_name, config in services_map.items():
                if not isinstance(config, dict):
                    issues.append(f"{service_name}: Invalid configuration format")
                    continue
                
                # Check for required fields
                required_fields = ["type", "path"]
                for field in required_fields:
                    if field not in config:
                        issues.append(f"{service_name}: Missing required field '{field}'")
            
            if issues:
                return MCPServiceCheck(
                    service_name="services.map.json",
                    check_type="config",
                    success=False,
                    message=f"Configuration has {len(issues)} issues",
                    details={"issues": issues[:5]}  # Show first 5 issues
                )
            else:
                return MCPServiceCheck(
                    service_name="services.map.json",
                    check_type="config",
                    success=True,
                    message=f"Valid configuration with {service_count} services",
                    details={"services": list(services_map.keys())[:10]}  # Show first 10
                )
                
        except json.JSONDecodeError as e:
            return MCPServiceCheck(
                service_name="services.map.json",
                check_type="config",
                success=False,
                message=f"Invalid JSON: {str(e)}",
                details=None
            )
        except Exception as e:
            return MCPServiceCheck(
                service_name="services.map.json",
                check_type="config",
                success=False,
                message=f"Error reading file: {str(e)}",
                details=None
            )
    
    # ========== FLY.IO READINESS ==========
    
    def check_fly_readiness(self) -> List[MCPServiceCheck]:
        """Check Fly.io deployment readiness"""
        checks = []
        
        # Check Fly CLI installation
        try:
            result = subprocess.run(
                ["which", "flyctl"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Get Fly version
                version_result = subprocess.run(
                    ["flyctl", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                checks.append(MCPServiceCheck(
                    service_name="Fly CLI",
                    check_type="fly",
                    success=True,
                    message=f"Installed: {version_result.stdout.strip()}",
                    details=None
                ))
            else:
                checks.append(MCPServiceCheck(
                    service_name="Fly CLI",
                    check_type="fly",
                    success=False,
                    message="Not installed",
                    details={"install": "curl -L https://fly.io/install.sh | sh"}
                ))
        except Exception as e:
            checks.append(MCPServiceCheck(
                service_name="Fly CLI",
                check_type="fly",
                success=False,
                message=f"Error checking CLI: {str(e)}",
                details=None
            ))
        
        # Check Fly API token
        fly_token = os.getenv("FLY_API_TOKEN")
        if fly_token:
            checks.append(MCPServiceCheck(
                service_name="Fly API Token",
                check_type="fly",
                success=True,
                message="Token configured",
                details=None
            ))
        else:
            checks.append(MCPServiceCheck(
                service_name="Fly API Token",
                check_type="fly",
                success=False,
                message="FLY_API_TOKEN not set",
                details={"action": "Set FLY_API_TOKEN environment variable"}
            ))
        
        # Check if authenticated with Fly
        if fly_token:
            try:
                result = subprocess.run(
                    ["flyctl", "auth", "whoami"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={**os.environ, "FLY_API_TOKEN": fly_token}
                )
                
                if result.returncode == 0:
                    checks.append(MCPServiceCheck(
                        service_name="Fly Authentication",
                        check_type="fly",
                        success=True,
                        message=f"Authenticated as: {result.stdout.strip()}",
                        details=None
                    ))
                else:
                    checks.append(MCPServiceCheck(
                        service_name="Fly Authentication",
                        check_type="fly",
                        success=False,
                        message="Authentication failed",
                        details={"error": result.stderr.strip()}
                    ))
            except Exception as e:
                checks.append(MCPServiceCheck(
                    service_name="Fly Authentication",
                    check_type="fly",
                    success=False,
                    message=f"Error checking auth: {str(e)}",
                    details=None
                ))
        
        return checks
    
    # ========== DEPLOYMENT SCRIPT CHECK ==========
    
    def check_deployment_scripts(self) -> List[MCPServiceCheck]:
        """Check for deployment scripts"""
        checks = []
        
        # Check for common deployment scripts
        deployment_scripts = [
            "scripts/fly-deploy.sh",
            "scripts/fly-create-apps.sh",
            "scripts/deploy-production-secure.sh",
            "k8s-deploy/scripts/deploy-production-readiness.sh"
        ]
        
        found_scripts = []
        missing_scripts = []
        
        for script in deployment_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                found_scripts.append(script)
                
                # Check if executable
                if not os.access(script_path, os.X_OK):
                    checks.append(MCPServiceCheck(
                        service_name=script,
                        check_type="deployment",
                        success=False,
                        message="Not executable",
                        details={"fix": f"chmod +x {script}"}
                    ))
            else:
                missing_scripts.append(script)
        
        if found_scripts:
            checks.append(MCPServiceCheck(
                service_name="Deployment Scripts",
                check_type="deployment",
                success=True,
                message=f"Found {len(found_scripts)} deployment scripts",
                details={"scripts": found_scripts}
            ))
        
        if missing_scripts:
            checks.append(MCPServiceCheck(
                service_name="Missing Scripts",
                check_type="deployment",
                success=False,
                message=f"{len(missing_scripts)} scripts not found",
                details={"missing": missing_scripts}
            ))
        
        return checks
    
    # ========== MAIN EXECUTION ==========
    
    def run_all_checks(self):
        """Run all readiness checks"""
        self.print_header()
        
        # Discover MCP services
        self.print_section("Service Discovery")
        services = self.discover_mcp_services()
        
        if services:
            print(f"{Fore.GREEN}✅ Found {len(services)} MCP services")
            for service in services:
                print(f"   • {service['name']} at {service['path'].relative_to(self.base_dir)}")
        else:
            print(f"{Fore.RED}❌ No MCP services found")
        
        # Check environment variables
        self.print_section("Environment Variables")
        env_checks = self.check_environment_variables()
        for check in env_checks:
            self.checks.append(check)
            self.print_check_result(check)
        
        # Check service structure
        if services:
            self.print_section("Service Structure")
            structure_checks = self.check_service_structure(services)
            for check in structure_checks:
                self.checks.append(check)
                self.print_check_result(check)
            
            # Validate Dockerfiles
            self.print_section("Dockerfile Validation")
            dockerfile_checks = self.validate_dockerfiles(services)
            for check in dockerfile_checks:
                self.checks.append(check)
                self.print_check_result(check)
        
        # Check services.map.json
        self.print_section("Service Configuration")
        services_map_check = self.check_services_map()
        self.checks.append(services_map_check)
        self.print_check_result(services_map_check)
        
        # Check Fly.io readiness
        self.print_section("Fly.io Readiness")
        fly_checks = self.check_fly_readiness()
        for check in fly_checks:
            self.checks.append(check)
            self.print_check_result(check)
        
        # Check deployment scripts
        self.print_section("Deployment Scripts")
        script_checks = self.check_deployment_scripts()
        for check in script_checks:
            self.checks.append(check)
            self.print_check_result(check)
        
        # Print summary
        self.print_summary()
        
        # Return exit code
        failed_checks = sum(1 for c in self.checks if not c.success)
        return 0 if failed_checks == 0 else 1
    
    def print_summary(self):
        """Print readiness summary"""
        print(f"\n{Style.BRIGHT}{'='*70}")
        print(f"{Style.BRIGHT}READINESS SUMMARY")
        print(f"{Style.BRIGHT}{'='*70}")
        
        # Count check results by type
        check_types = {}
        for check in self.checks:
            if check.check_type not in check_types:
                check_types[check.check_type] = {"passed": 0, "failed": 0}
            
            if check.success:
                check_types[check.check_type]["passed"] += 1
            else:
                check_types[check.check_type]["failed"] += 1
        
        # Print check type summary
        print(f"\n{Style.BRIGHT}Check Results by Type:")
        for check_type, counts in check_types.items():
            total = counts["passed"] + counts["failed"]
            if counts["failed"] == 0:
                status = f"{Fore.GREEN}✅"
            elif counts["passed"] == 0:
                status = f"{Fore.RED}❌"
            else:
                status = f"{Fore.YELLOW}⚠️"
            
            print(f"  {status} {check_type.title()}: {counts['passed']}/{total} passed")
        
        # Overall readiness
        total_checks = len(self.checks)
        passed_checks = sum(1 for c in self.checks if c.success)
        failed_checks = total_checks - passed_checks
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n{Style.BRIGHT}Overall Readiness:")
        
        if failed_checks == 0:
            print(f"  {Fore.GREEN}✅ READY FOR DEPLOYMENT")
            print(f"  All {total_checks} checks passed successfully!")
        elif failed_checks <= 3:
            print(f"  {Fore.YELLOW}⚠️  PARTIALLY READY")
            print(f"  {failed_checks} issues need attention before deployment")
        else:
            print(f"  {Fore.RED}❌ NOT READY")
            print(f"  {failed_checks} critical issues must be resolved")
        
        print(f"  Pass Rate: {pass_rate:.1f}% ({passed_checks}/{total_checks})")
        
        # List critical failures
        critical_failures = [c for c in self.checks if not c.success and c.check_type in ["env_vars", "structure", "fly"]]
        if critical_failures:
            print(f"\n{Style.BRIGHT}{Fore.RED}Critical Issues to Resolve:")
            for failure in critical_failures[:5]:  # Show top 5
                print(f"  • {failure.service_name}: {failure.message}")
                if failure.details and "missing" in failure.details:
                    for item in failure.details["missing"][:3]:  # Show first 3
                        print(f"    - {item}")
        
        # Next steps
        if failed_checks > 0:
            print(f"\n{Style.BRIGHT}Next Steps:")
            
            # Check for missing environment variables
            env_failures = [c for c in self.checks if not c.success and c.check_type == "env_vars"]
            if env_failures:
                print(f"  1. Set missing environment variables in .env file")
            
            # Check for structural issues
            struct_failures = [c for c in self.checks if not c.success and c.check_type == "structure"]
            if struct_failures:
                print(f"  2. Fix service structure issues (add missing files)")
            
            # Check for Fly.io issues
            fly_failures = [c for c in self.checks if not c.success and c.check_type == "fly"]
            if fly_failures:
                print(f"  3. Configure Fly.io CLI and authentication")
            
            print(f"  4. Run this script again to verify fixes")
        
        print(f"\n{'='*70}")
        print(f"Check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    checker = MCPReadinessChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)