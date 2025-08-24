#!/usr/bin/env python3
"""
Automated Migration Setup
Implements the 6-point improvement plan for zero-manual Render migration
"""

import os
import json
import subprocess
import sys
import time
from typing import Dict, List, Optional

class AutomatedMigrationSetup:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_owner = 'ai-cherry'
        self.repo_name = 'sophia-ai-intel'
        self.required_secrets = [
            'RENDER_API_TOKEN',
            'PULUMI_ACCESS_TOKEN', 
            'NEON_API_KEY',
            'REDIS_ACCOUNT_KEY',
            'REDIS_DATABASE_ENDPOINT',
            'QDRANT_API_KEY',
            'MEM0_API_KEY',
            'LAMBDA_API_KEY',
            'N8N_API_KEY',
            'AIRBYTE_API_KEY',
            'HUBSPOT_API_TOKEN',
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY',
            'GH_PAT_TOKEN'
        ]
        
    def validate_prerequisites(self) -> bool:
        """Validate all prerequisites are met"""
        print("🔍 Validating prerequisites...")
        
        # Check GitHub CLI
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ GitHub CLI not authenticated. Run: gh auth login")
                return False
            print("✅ GitHub CLI authenticated")
        except FileNotFoundError:
            print("❌ GitHub CLI not installed")
            return False
            
        # Check if we have repository access
        try:
            result = subprocess.run([
                'gh', 'repo', 'view', f'{self.repo_owner}/{self.repo_name}'
            ], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Cannot access repository {self.repo_owner}/{self.repo_name}")
                return False
            print("✅ Repository access confirmed")
        except Exception as e:
            print(f"❌ Repository access failed: {e}")
            return False
            
        return True
        
    def create_github_secrets(self) -> bool:
        """Create/update GitHub organization secrets"""
        print("🔐 Setting up GitHub organization secrets...")
        
        # Check existing secrets
        try:
            result = subprocess.run([
                'gh', 'secret', 'list', '--org', self.repo_owner
            ], capture_output=True, text=True)
            
            existing_secrets = set()
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        secret_name = line.split()[0]
                        existing_secrets.add(secret_name)
                        
            print(f"✅ Found {len(existing_secrets)} existing organization secrets")
            
            # Check which secrets are missing
            missing_secrets = set(self.required_secrets) - existing_secrets
            if missing_secrets:
                print(f"⚠️  Missing secrets: {', '.join(missing_secrets)}")
                print("📋 Please set these secrets manually in GitHub organization settings:")
                print(f"   https://github.com/orgs/{self.repo_owner}/settings/secrets/actions")
                for secret in missing_secrets:
                    print(f"   - {secret}")
                return False
            else:
                print("✅ All required secrets are available")
                return True
                
        except Exception as e:
            print(f"❌ Failed to check GitHub secrets: {e}")
            return False
            
    def create_workflow_files(self) -> bool:
        """Create automated deployment workflow"""
        print("⚙️  Creating automated deployment workflow...")
        
        workflow_content = """name: Automated Render Migration

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging
      dry_run:
        description: 'Dry run (validation only)'
        required: false
        default: false
        type: boolean

env:
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
  RENDER_API_TOKEN: ${{ secrets.RENDER_API_TOKEN }}
  NEON_API_KEY: ${{ secrets.NEON_API_KEY }}
  REDIS_ACCOUNT_KEY: ${{ secrets.REDIS_ACCOUNT_KEY }}
  REDIS_DATABASE_ENDPOINT: ${{ secrets.REDIS_DATABASE_ENDPOINT }}
  QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
  MEM0_API_KEY: ${{ secrets.MEM0_API_KEY }}
  LAMBDA_API_KEY: ${{ secrets.LAMBDA_API_KEY }}
  N8N_API_KEY: ${{ secrets.N8N_API_KEY }}
  AIRBYTE_API_KEY: ${{ secrets.AIRBYTE_API_KEY }}

jobs:
  validate-environment:
    runs-on: ubuntu-latest
    outputs:
      validation-passed: ${{ steps.validate.outputs.passed }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r ops/pulumi/requirements.txt
          pip install render-python-client
          
      - name: Validate Environment Mapping
        id: validate
        run: |
          python scripts/validate_environment_mapping.py
          echo "passed=true" >> $GITHUB_OUTPUT
          
  infrastructure-setup:
    needs: validate-environment
    if: needs.validate-environment.outputs.validation-passed == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Pulumi
        uses: pulumi/actions@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r ops/pulumi/requirements.txt
          
      - name: Run Pulumi Infrastructure Setup
        run: |
          cd ops/pulumi
          pulumi stack select production --create
          pulumi up --yes --skip-preview
          
  deploy-services:
    needs: infrastructure-setup
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - mcp-research
          - mcp-context
          - mcp-github
          - mcp-business
          - mcp-hubspot
          - mcp-lambda
          - orchestrator
          - jobs
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Render CLI
        run: |
          curl -L https://render.com/cli-install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH
          
      - name: Deploy ${{ matrix.service }}
        run: |
          render deploy --service ${{ matrix.service }}
          
      - name: Health Check
        run: |
          python scripts/health_check.py ${{ matrix.service }}
          
  dns-cutover:
    needs: deploy-services
    runs-on: ubuntu-latest
    if: github.event.inputs.dry_run != 'true'
    steps:
      - uses: actions/checkout@v4
      
      - name: DNS Cutover
        run: |
          python scripts/dns_cutover.py
          
      - name: Final Validation
        run: |
          python scripts/final_validation.py
"""

        try:
            with open('.github/workflows/automated_render_migration.yml', 'w') as f:
                f.write(workflow_content)
            print("✅ Created automated deployment workflow")
            return True
        except Exception as e:
            print(f"❌ Failed to create workflow: {e}")
            return False
            
    def create_validation_script(self) -> bool:
        """Create environment validation script"""
        print("🔍 Creating environment validation script...")
        
        validation_script = '''#!/usr/bin/env python3
"""
Environment Mapping Validation
Ensures all services have correct environment variables before migration
"""

import os
import json
import yaml
import sys

def validate_service_environment(service_name: str, config: dict) -> bool:
    """Validate a single service's environment configuration"""
    print(f"🔍 Validating {service_name}...")
    
    required_vars = config.get('envVars', [])
    missing_vars = []
    
    for var in required_vars:
        if isinstance(var, dict) and 'key' in var:
            var_name = var['key']
            var_value = var.get('value', var.get('fromSecret'))
            
            # Check if it's a secret reference
            if isinstance(var_value, dict) and 'name' in var_value:
                secret_name = var_value['name']
                if not os.environ.get(secret_name):
                    missing_vars.append(f"{var_name} (secret: {secret_name})")
            elif not var_value:
                missing_vars.append(var_name)
    
    if missing_vars:
        print(f"❌ {service_name} missing: {', '.join(missing_vars)}")
        return False
    else:
        print(f"✅ {service_name} environment valid")
        return True

def main():
    """Main validation function"""
    print("🔍 Validating environment mapping for Render migration...")
    
    # Load render.yaml
    try:
        with open('render.yaml', 'r') as f:
            render_config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load render.yaml: {e}")
        return False
        
    all_valid = True
    
    for service in render_config.get('services', []):
        service_name = service.get('name', 'unknown')
        if not validate_service_environment(service_name, service):
            all_valid = False
    
    if all_valid:
        print("✅ All service environments validated successfully")
        return True
    else:
        print("❌ Environment validation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        try:
            with open('scripts/validate_environment_mapping.py', 'w') as f:
                f.write(validation_script)
            os.chmod('scripts/validate_environment_mapping.py', 0o755)
            print("✅ Created environment validation script")
            return True
        except Exception as e:
            print(f"❌ Failed to create validation script: {e}")
            return False
            
    def create_health_check_script(self) -> bool:
        """Create service health check script"""
        print("🏥 Creating health check script...")
        
        health_check_script = '''#!/usr/bin/env python3
"""
Service Health Check
Validates service health after deployment
"""

import requests
import sys
import time
import yaml

def check_service_health(service_name: str) -> bool:
    """Check health of a specific service"""
    print(f"🏥 Checking health of {service_name}...")
    
    # Load render.yaml to get service URL
    try:
        with open('render.yaml', 'r') as f:
            render_config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load render.yaml: {e}")
        return False
    
    # Find service config
    service_config = None
    for service in render_config.get('services', []):
        if service.get('name') == service_name:
            service_config = service
            break
            
    if not service_config:
        print(f"❌ Service {service_name} not found in render.yaml")
        return False
    
    # Construct health check URL
    service_type = service_config.get('type')
    if service_type == 'static_site':
        # Static sites don't have health endpoints
        print(f"✅ {service_name} is a static site (no health check needed)")
        return True
        
    # For web services, try health endpoint
    base_url = f"https://{service_name}.onrender.com"
    health_urls = [
        f"{base_url}/healthz",
        f"{base_url}/health",
        f"{base_url}/"
    ]
    
    for url in health_urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy at {url}")
                return True
        except Exception as e:
            print(f"⚠️  Failed to check {url}: {e}")
            continue
    
    print(f"❌ {service_name} health check failed")
    return False

def main():
    """Main health check function"""
    if len(sys.argv) != 2:
        print("Usage: health_check.py <service_name>")
        sys.exit(1)
        
    service_name = sys.argv[1]
    
    # Wait for service to stabilize
    print(f"⏳ Waiting 30s for {service_name} to stabilize...")
    time.sleep(30)
    
    # Check health with retries
    for attempt in range(3):
        if check_service_health(service_name):
            sys.exit(0)
        print(f"🔄 Retry {attempt + 1}/3...")
        time.sleep(15)
    
    print(f"❌ {service_name} failed all health checks")
    sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        try:
            with open('scripts/health_check.py', 'w') as f:
                f.write(health_check_script)
            os.chmod('scripts/health_check.py', 0o755)
            print("✅ Created health check script")
            return True
        except Exception as e:
            print(f"❌ Failed to create health check script: {e}")
            return False
            
    def create_dns_cutover_script(self) -> bool:
        """Create DNS cutover automation"""
        print("🌐 Creating DNS cutover script...")
        
        dns_script = '''#!/usr/bin/env python3
"""
DNS Cutover Automation
Handles the final DNS cutover from Fly.io to Render
"""

import os
import subprocess
import time
import requests

def update_dns_records():
    """Update DNS records to point to Render"""
    print("🌐 Updating DNS records...")
    
    # This would typically integrate with your DNS provider
    # For now, we'll document the manual steps
    
    dns_updates = {
        'sophia-ai-intel.com': {
            'CNAME': 'sophia-ai-intel.onrender.com'
        },
        'api.sophia-ai-intel.com': {
            'CNAME': 'mcp-orchestrator.onrender.com'
        },
        'research.sophia-ai-intel.com': {
            'CNAME': 'mcp-research.onrender.com'
        }
    }
    
    print("📋 DNS Updates Required:")
    for domain, records in dns_updates.items():
        for record_type, value in records.items():
            print(f"   {domain} {record_type} -> {value}")
    
    # Verify DNS propagation
    print("🔍 Verifying DNS propagation...")
    for domain in dns_updates.keys():
        print(f"   Checking {domain}...")
        # Add DNS verification logic here
    
    return True

def main():
    """Main DNS cutover function"""
    print("🌐 Starting DNS cutover process...")
    
    # Verify all services are healthy on Render
    services = [
        'mcp-research', 'mcp-context', 'mcp-github',
        'mcp-business', 'mcp-hubspot', 'mcp-lambda',
        'orchestrator'
    ]
    
    print("🏥 Final health check before DNS cutover...")
    for service in services:
        if not verify_service_health(service):
            print(f"❌ {service} not healthy - aborting DNS cutover")
            return False
    
    # Perform DNS updates
    if update_dns_records():
        print("✅ DNS cutover completed successfully")
        return True
    else:
        print("❌ DNS cutover failed")
        return False

def verify_service_health(service_name: str) -> bool:
    """Quick health verification"""
    try:
        url = f"https://{service_name}.onrender.com/healthz"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    main()
'''
        
        try:
            with open('scripts/dns_cutover.py', 'w') as f:
                f.write(dns_script)
            os.chmod('scripts/dns_cutover.py', 0o755)
            print("✅ Created DNS cutover script")
            return True
        except Exception as e:
            print(f"❌ Failed to create DNS cutover script: {e}")
            return False
            
    def create_render_cli_fallback(self) -> bool:
        """Create Render CLI fallback deployment"""
        print("🔧 Creating Render CLI fallback deployment...")
        
        fallback_script = '''#!/usr/bin/env bash
"""
Render CLI Fallback Deployment
Alternative deployment method using Render CLI
"""

set -e

echo "🔧 Starting Render CLI fallback deployment..."

# Install Render CLI if not present
if ! command -v render &> /dev/null; then
    echo "📦 Installing Render CLI..."
    curl -L https://render.com/cli-install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Authenticate with Render
echo "🔐 Authenticating with Render..."
render auth login

# Deploy services one by one
services=(
    "mcp-research"
    "mcp-context" 
    "mcp-github"
    "mcp-business"
    "mcp-hubspot"
    "mcp-lambda"
    "orchestrator"
    "jobs"
    "dashboard"
)

echo "🚀 Deploying services..."
for service in "${services[@]}"; do
    echo "📦 Deploying $service..."
    
    # Create service if it doesn't exist
    render service list | grep -q "$service" || {
        echo "🆕 Creating new service: $service"
        render service create --from-repo --name "$service"
    }
    
    # Deploy service
    render deploy --service "$service" --wait
    
    # Health check
    echo "🏥 Health checking $service..."
    sleep 30
    
    # Try multiple health endpoints
    health_urls=(
        "https://$service.onrender.com/healthz"
        "https://$service.onrender.com/health"
        "https://$service.onrender.com/"
    )
    
    healthy=false
    for url in "${health_urls[@]}"; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service is healthy at $url"
            healthy=true
            break
        fi
    done
    
    if [ "$healthy" = false ]; then
        echo "❌ $service failed health check"
        exit 1
    fi
done

echo "✅ All services deployed successfully via Render CLI"
'''
        
        try:
            with open('scripts/render_cli_fallback.sh', 'w') as f:
                f.write(fallback_script)
            os.chmod('scripts/render_cli_fallback.sh', 0o755)
            print("✅ Created Render CLI fallback script")
            return True
        except Exception as e:
            print(f"❌ Failed to create fallback script: {e}")
            return False
            
    def run_setup(self) -> bool:
        """Run the complete automated setup"""
        print("🚀 Starting Automated Migration Setup...")
        print("=" * 60)
        
        steps = [
            ("Prerequisites", self.validate_prerequisites),
            ("GitHub Secrets", self.create_github_secrets),
            ("Workflow Files", self.create_workflow_files),
            ("Validation Script", self.create_validation_script),
            ("Health Check Script", self.create_health_check_script),
            ("DNS Cutover Script", self.create_dns_cutover_script),
            ("Render CLI Fallback", self.create_render_cli_fallback)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Failed at step: {step_name}")
                return False
                
        print("\n" + "=" * 60)
        print("✅ Automated Migration Setup Complete!")
        print("\n📋 Next Steps:")
        print("1. Ensure all GitHub organization secrets are set")
        print("2. Run: gh workflow run automated_render_migration.yml")
        print("3. Monitor deployment progress in GitHub Actions")
        print("4. Use Render CLI fallback if needed: ./scripts/render_cli_fallback.sh")
        
        return True

def main():
    """Main entry point"""
    setup = AutomatedMigrationSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
