#!/usr/bin/env python3
"""
Fly.io Orchestration Script for Sophia AI MCP Services

This script orchestrates the deployment of all MCP services to Fly.io:
- Reads service topology from services.map.json
- Loads environment variables from .env file
- Filters and syncs secrets to each Fly.io app
- Deploys services using their TOML configurations
- Generates dashboard configuration files

Usage:
    python scripts/fly_sync.py [--dry-run]
    
Options:
    --dry-run   Preview operations without executing them
"""

import json
import os
import subprocess
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path("/Users/lynnmusil/sophia-ai-intel-1")
ENV_FILE = BASE_DIR / ".env"
SERVICES_MAP_FILE = BASE_DIR / "services.map.json"
DASHBOARD_ENV_FILE = BASE_DIR / "apps" / "dashboard" / ".env.local"
SERVICES_CONFIG_FILE = BASE_DIR / "config" / "services.json"


class FlyIOOrchestrator:
    """Orchestrates Fly.io deployments for Sophia AI MCP services"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.services_map: Dict[str, Any] = {}
        self.env_vars: Dict[str, str] = {}
        self.fly_token: Optional[str] = None
        
        if self.dry_run:
            logger.info("🔧 Running in DRY-RUN mode - no actual changes will be made")
    
    def load_services_map(self) -> None:
        """Load service configuration from services.map.json"""
        logger.info(f"📖 Loading services map from {SERVICES_MAP_FILE}")
        
        if not SERVICES_MAP_FILE.exists():
            logger.error(f"❌ Services map file not found: {SERVICES_MAP_FILE}")
            sys.exit(1)
        
        try:
            with open(SERVICES_MAP_FILE, 'r') as f:
                self.services_map = json.load(f)
            logger.info(f"✅ Loaded {len(self.services_map)} service configurations")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse services map: {e}")
            sys.exit(1)
    
    def load_environment(self) -> None:
        """Load environment variables from .env file"""
        logger.info(f"🔐 Loading environment variables from {ENV_FILE}")
        
        if not ENV_FILE.exists():
            logger.error(f"❌ Environment file not found: {ENV_FILE}")
            sys.exit(1)
        
        try:
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        self.env_vars[key.strip()] = value
            
            # Check for Fly.io authentication
            self.fly_token = self.env_vars.get('FLY_API_TOKEN') or self.env_vars.get('FLY_ORG_TOKEN')
            if not self.fly_token:
                logger.warning("⚠️  No FLY_API_TOKEN or FLY_ORG_TOKEN found in environment")
                # Try from system environment
                self.fly_token = os.environ.get('FLY_API_TOKEN') or os.environ.get('FLY_ORG_TOKEN')
                if not self.fly_token:
                    logger.error("❌ Fly.io authentication token not found")
                    sys.exit(1)
            
            logger.info(f"✅ Loaded {len(self.env_vars)} environment variables")
        except Exception as e:
            logger.error(f"❌ Failed to load environment: {e}")
            sys.exit(1)
    
    def filter_secrets_for_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, str]:
        """Filter environment variables based on service-specific rules"""
        secrets = {}
        rules = config.get('secrets', {})
        
        # Get specific keys
        specific_keys = rules.get('keys', [])
        for key in specific_keys:
            if key in self.env_vars:
                secrets[key] = self.env_vars[key]
            else:
                logger.warning(f"⚠️  Secret '{key}' not found for service '{service_name}'")
        
        # Get prefixed keys
        prefixes = rules.get('prefixes', [])
        for prefix in prefixes:
            for key, value in self.env_vars.items():
                if key.startswith(prefix):
                    secrets[key] = value
        
        logger.info(f"📦 Filtered {len(secrets)} secrets for '{service_name}'")
        return secrets
    
    def execute_command(self, command: List[str], env: Optional[Dict[str, str]] = None) -> tuple[int, str, str]:
        """Execute a shell command and return result"""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {' '.join(command)}")
            return 0, "", ""
        
        try:
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=process_env,
                cwd=BASE_DIR
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            logger.error(f"❌ Command failed: {e}")
            return 1, "", str(e)
    
    def destroy_existing_machines(self, app_name: str) -> bool:
        """Destroy existing machines for an app"""
        logger.info(f"🗑️  Destroying existing machines for '{app_name}'...")
        
        # Set Fly.io token for authentication
        env = {'FLY_API_TOKEN': self.fly_token}
        
        # List machines
        returncode, stdout, stderr = self.execute_command(
            ['fly', 'machines', 'list', '--app', app_name],
            env=env
        )
        
        if returncode != 0:
            if "Could not find App" in stderr or "not found" in stderr.lower():
                logger.info(f"ℹ️  App '{app_name}' does not exist yet")
                return True
            logger.warning(f"⚠️  Failed to list machines: {stderr}")
            return False
        
        # Parse machine IDs from output
        machine_ids = []
        for line in stdout.split('\n'):
            if line and not line.startswith('ID') and not line.startswith('-'):
                parts = line.split()
                if parts:
                    machine_ids.append(parts[0])
        
        if not machine_ids:
            logger.info(f"ℹ️  No existing machines found for '{app_name}'")
            return True
        
        # Destroy each machine
        for machine_id in machine_ids:
            logger.info(f"  Destroying machine: {machine_id}")
            returncode, _, stderr = self.execute_command(
                ['fly', 'machines', 'destroy', machine_id, '--app', app_name, '--force'],
                env=env
            )
            if returncode != 0:
                logger.warning(f"  ⚠️  Failed to destroy machine {machine_id}: {stderr}")
        
        return True
    
    def sync_secrets(self, app_name: str, secrets: Dict[str, str]) -> bool:
        """Sync secrets to a Fly.io app"""
        if not secrets:
            logger.info(f"ℹ️  No secrets to sync for '{app_name}'")
            return True
        
        logger.info(f"🔑 Syncing {len(secrets)} secrets to '{app_name}'...")
        
        # Set Fly.io token for authentication
        env = {'FLY_API_TOKEN': self.fly_token}
        
        # Build secrets command
        secret_args = []
        for key, value in secrets.items():
            # Escape special characters in values
            escaped_value = value.replace('"', '\\"')
            secret_args.append(f'{key}="{escaped_value}"')
        
        # Execute fly secrets set command
        command = ['fly', 'secrets', 'set', '--app', app_name] + secret_args
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would sync secrets: {list(secrets.keys())}")
            return True
        
        returncode, stdout, stderr = self.execute_command(command, env=env)
        
        if returncode != 0:
            logger.error(f"❌ Failed to sync secrets: {stderr}")
            return False
        
        logger.info(f"✅ Successfully synced secrets to '{app_name}'")
        return True
    
    def deploy_service(self, service_name: str, config: Dict[str, Any]) -> bool:
        """Deploy a service to Fly.io"""
        app_name = config['app']
        toml_path = BASE_DIR / config['config']
        
        logger.info(f"🚀 Deploying '{service_name}' as '{app_name}'...")
        
        # Check if TOML file exists
        if not toml_path.exists():
            logger.error(f"❌ TOML config not found: {toml_path}")
            return False
        
        # Set Fly.io token for authentication
        env = {'FLY_API_TOKEN': self.fly_token}
        
        # Deploy using fly deploy
        command = ['fly', 'deploy', '--config', str(toml_path), '--app', app_name]
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would deploy with config: {toml_path}")
            return True
        
        returncode, stdout, stderr = self.execute_command(command, env=env)
        
        if returncode != 0:
            logger.error(f"❌ Failed to deploy '{service_name}': {stderr}")
            return False
        
        logger.info(f"✅ Successfully deployed '{service_name}'")
        return True
    
    def generate_dashboard_env(self) -> None:
        """Generate .env.local file for the dashboard with NEXT_PUBLIC_ prefixed URLs"""
        logger.info(f"📝 Generating dashboard environment file: {DASHBOARD_ENV_FILE}")
        
        env_content = [
            "# Auto-generated by fly_sync.py",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
            "# Service Endpoints"
        ]
        
        for service_name, config in self.services_map.items():
            domain = config.get('domain', '')
            env_key = f"NEXT_PUBLIC_{service_name.upper().replace('-', '_')}_URL"
            env_content.append(f"{env_key}={domain}")
        
        # Add other NEXT_PUBLIC_ variables from .env
        env_content.append("")
        env_content.append("# Other Public Environment Variables")
        for key, value in self.env_vars.items():
            if key.startswith('NEXT_PUBLIC_') and not any(key in line for line in env_content):
                env_content.append(f"{key}={value}")
        
        if self.dry_run:
            logger.info("[DRY-RUN] Would generate dashboard .env.local with service URLs")
            return
        
        # Ensure directory exists
        DASHBOARD_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(DASHBOARD_ENV_FILE, 'w') as f:
            f.write('\n'.join(env_content))
            f.write('\n')
        
        logger.info(f"✅ Generated {DASHBOARD_ENV_FILE}")
    
    def generate_services_config(self) -> None:
        """Generate services.json configuration file"""
        logger.info(f"📝 Generating services configuration: {SERVICES_CONFIG_FILE}")
        
        services_config = {
            "generated_at": datetime.now().isoformat(),
            "services": {}
        }
        
        for service_name, config in self.services_map.items():
            services_config["services"][service_name] = {
                "name": service_name,
                "app": config['app'],
                "url": config['domain'],
                "health_check": f"{config['domain']}/health"
            }
        
        if self.dry_run:
            logger.info("[DRY-RUN] Would generate config/services.json")
            return
        
        # Ensure directory exists
        SERVICES_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(SERVICES_CONFIG_FILE, 'w') as f:
            json.dump(services_config, f, indent=2)
        
        logger.info(f"✅ Generated {SERVICES_CONFIG_FILE}")
    
    def orchestrate(self) -> None:
        """Main orchestration logic"""
        logger.info("🎯 Starting Fly.io deployment orchestration")
        
        # Load configurations
        self.load_services_map()
        self.load_environment()
        
        # Track deployment status
        successful_deployments = []
        failed_deployments = []
        
        # Process each service
        for service_name, config in self.services_map.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing service: {service_name}")
            logger.info(f"{'='*60}")
            
            app_name = config['app']
            
            try:
                # 1. Filter secrets for this service
                secrets = self.filter_secrets_for_service(service_name, config)
                
                # 2. Destroy existing machines
                if not self.destroy_existing_machines(app_name):
                    logger.warning(f"⚠️  Failed to destroy machines for '{app_name}', continuing...")
                
                # 3. Sync secrets
                if not self.sync_secrets(app_name, secrets):
                    logger.error(f"❌ Failed to sync secrets for '{service_name}'")
                    failed_deployments.append(service_name)
                    continue
                
                # 4. Deploy the service
                if not self.deploy_service(service_name, config):
                    logger.error(f"❌ Failed to deploy '{service_name}'")
                    failed_deployments.append(service_name)
                    continue
                
                successful_deployments.append(service_name)
                logger.info(f"✨ Successfully processed '{service_name}'")
                
            except Exception as e:
                logger.error(f"❌ Unexpected error processing '{service_name}': {e}")
                failed_deployments.append(service_name)
        
        # Generate configuration files
        logger.info(f"\n{'='*60}")
        logger.info("Generating configuration files...")
        logger.info(f"{'='*60}")
        
        self.generate_dashboard_env()
        self.generate_services_config()
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("DEPLOYMENT SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Successful: {len(successful_deployments)} services")
        for service in successful_deployments:
            logger.info(f"   - {service}")
        
        if failed_deployments:
            logger.info(f"❌ Failed: {len(failed_deployments)} services")
            for service in failed_deployments:
                logger.info(f"   - {service}")
            sys.exit(1)
        else:
            logger.info("\n🎉 All services deployed successfully!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Orchestrate Fly.io deployments for Sophia AI MCP services"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview operations without executing them'
    )
    
    args = parser.parse_args()
    
    try:
        orchestrator = FlyIOOrchestrator(dry_run=args.dry_run)
        orchestrator.orchestrate()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Deployment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()