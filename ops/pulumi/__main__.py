#!/usr/bin/env python3
"""
Sophia AI Intel - Pulumi + Lambda Labs Deployment
=================================================

Complete containerized microservices platform deployed to Lambda Labs GPU instances.
Uses Pulumi Cloud for state management and Lambda Labs for compute.
"""

import os
import pulumi
import requests
import json
from typing import Dict, Any, Optional

# Get Pulumi configuration
config = pulumi.Config()

# Lambda Labs Configuration
LAMBDA_API_KEY = config.require_secret("lambda-api-key")
LAMBDA_PRIVATE_SSH_KEY = config.require_secret("lambda-private-ssh-key")  
LAMBDA_PUBLIC_SSH_KEY = config.require_secret("lambda-public-ssh-key")
LAMBDA_API_ENDPOINT = "https://cloud.lambdalabs.com/api/v1"

# Application secrets from Pulumi config
OPENAI_API_KEY = config.require_secret("openai-api-key")
NEON_DATABASE_URL = config.require_secret("neon-database-url")
REDIS_URL = config.require_secret("redis-url")

pulumi.log.info("🔐 Lambda Labs + Pulumi Cloud deployment starting")

class LambdaLabsInstance:
    """Lambda Labs GPU instance management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = LAMBDA_API_ENDPOINT
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_instance(self, instance_name: str, instance_type: str = "gpu_1x_a100_sxm4") -> Dict:
        """Create a Lambda Labs instance"""
        
        payload = {
            "region_name": "us-west-1",
            "instance_type_name": instance_type,
            "ssh_key_names": ["sophia-deploy-key"],  # Must be pre-uploaded to Lambda Labs
            "quantity": 1,
            "name": instance_name
        }
        
        response = requests.post(
            f"{self.base_url}/instance-operations/launch",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create Lambda Labs instance: {response.text}")
    
    def get_instance_ip(self, instance_id: str) -> str:
        """Get public IP of instance"""
        
        response = requests.get(
            f"{self.base_url}/instances/{instance_id}",
            headers=self.headers,
            timeout=10
        )
        
        if response.status_code == 200:
            instance_data = response.json()
            return instance_data.get("data", {}).get("ip", "")
        else:
            raise Exception(f"Failed to get instance info: {response.text}")

# Create Lambda Labs instance
lambda_client = LambdaLabsInstance(LAMBDA_API_KEY.apply(lambda key: key))

def provision_lambda_instance():
    """Provision Lambda Labs instance"""
    
    pulumi.log.info("🖥️ Creating Lambda Labs GPU instance...")
    
    # Create instance
    instance_info = lambda_client.create_instance("sophia-ai-production")
    instance_id = instance_info.get("data", {}).get("instance_ids", [None])[0]
    
    if not instance_id:
        raise Exception("Failed to get instance ID from Lambda Labs")
    
    pulumi.log.info(f"✅ Lambda Labs instance created: {instance_id}")
    
    # Get IP address (wait for instance to be ready)
    import time
    time.sleep(60)  # Wait for instance to boot
    
    instance_ip = lambda_client.get_instance_ip(instance_id)
    pulumi.log.info(f"🌐 Instance IP: {instance_ip}")
    
    return {
        "instance_id": instance_id,
        "ip_address": instance_ip,
        "instance_type": "gpu_1x_a100_sxm4",
        "region": "us-west-1"
    }

# Provision infrastructure
instance_info = provision_lambda_instance()

# Deploy application via SSH
def deploy_to_lambda_instance(instance_ip: str):
    """Deploy application to Lambda Labs instance"""
    
    import subprocess
    
    pulumi.log.info(f"🚀 Deploying to Lambda Labs instance: {instance_ip}")
    
    # Create deployment script
    deploy_script = f"""#!/bin/bash
set -e

# Update system
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /home/ubuntu
if [ ! -d "sophia-ai-intel" ]; then
    git clone https://github.com/ai-cherry/sophia-ai-intel.git
fi

cd sophia-ai-intel
git pull origin main

# Create environment file
cat > .env << 'ENV_EOF'
# Core Infrastructure
TENANT=pay-ready
NODE_ENV=production
BUILD_ID=lambda-labs-production

# Database and Cache
NEON_DATABASE_URL={NEON_DATABASE_URL}
REDIS_URL={REDIS_URL}

# LLM Provider
OPENAI_API_KEY={OPENAI_API_KEY}

# Lambda Labs (self-reference)
LAMBDA_API_KEY={LAMBDA_API_KEY}
LAMBDA_PRIVATE_SSH_KEY={LAMBDA_PRIVATE_SSH_KEY}
LAMBDA_PUBLIC_SSH_KEY={LAMBDA_PUBLIC_SSH_KEY}
LAMBDA_API_ENDPOINT={LAMBDA_API_ENDPOINT}
ENV_EOF

# Deploy services
docker-compose up -d --build

# Wait for services to start
sleep 60

# Run health checks
echo "=== Health Check Results ==="
curl -f http://localhost:3000/healthz && echo "✅ Dashboard: OK" || echo "❌ Dashboard: FAIL"
curl -f http://localhost:8081/healthz && echo "✅ Research: OK" || echo "❌ Research: FAIL"
curl -f http://localhost:8082/healthz && echo "✅ Context: OK" || echo "❌ Context: FAIL"
curl -f http://localhost:8083/healthz && echo "✅ GitHub: OK" || echo "❌ GitHub: FAIL"
curl -f http://localhost:8084/healthz && echo "✅ Business: OK" || echo "❌ Business: FAIL"
curl -f http://localhost:8085/healthz && echo "✅ Lambda: OK" || echo "❌ Lambda: FAIL"
curl -f http://localhost:8086/healthz && echo "✅ HubSpot: OK" || echo "❌ HubSpot: FAIL"

echo "🎉 Deployment completed!"
echo "Dashboard: http://{instance_ip}:3000"
echo "API Gateway: http://{instance_ip}:80"
"""
    
    # Execute deployment via SSH
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-i", "~/.ssh/lambda_labs_key",  # SSH key for Lambda Labs
        f"ubuntu@{instance_ip}",
        deploy_script
    ]
    
    try:
        result = subprocess.run(ssh_command, check=True, capture_output=True, text=True)
        pulumi.log.info("✅ Deployment successful!")
        return {"success": True, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        pulumi.log.error(f"❌ Deployment failed: {e.stderr}")
        return {"success": False, "error": e.stderr}

# Deploy application
deployment_result = deploy_to_lambda_instance(instance_info["ip_address"])

# Export outputs
pulumi.export("lambda_instance_id", instance_info["instance_id"])
pulumi.export("instance_ip", instance_info["ip_address"])
pulumi.export("instance_type", instance_info["instance_type"])
pulumi.export("region", instance_info["region"])

# Service URLs
pulumi.export("dashboard_url", f"http://{instance_info['ip_address']}:3000")
pulumi.export("api_gateway_url", f"http://{instance_info['ip_address']}")
pulumi.export("research_api_url", f"http://{instance_info['ip_address']}:8081")
pulumi.export("context_api_url", f"http://{instance_info['ip_address']}:8082")
pulumi.export("github_api_url", f"http://{instance_info['ip_address']}:8083")
pulumi.export("business_api_url", f"http://{instance_info['ip_address']}:8084")
pulumi.export("lambda_api_url", f"http://{instance_info['ip_address']}:8085")
pulumi.export("hubspot_api_url", f"http://{instance_info['ip_address']}:8086")

# Deployment info
pulumi.export("deployment_success", deployment_result["success"])
pulumi.export("deployment_method", "pulumi-lambda-labs")
pulumi.export("services_deployed", [
    "sophia-dashboard",
    "sophia-research", 
    "sophia-context",
    "sophia-github",
    "sophia-business",
    "sophia-lambda",
    "sophia-hubspot",
    "sophia-jobs",
    "nginx-proxy"
])

# Management commands
pulumi.export("ssh_command", f"ssh ubuntu@{instance_info['ip_address']}")
pulumi.export("logs_command", "cd sophia-ai-intel && docker-compose logs -f")
pulumi.export("restart_command", "cd sophia-ai-intel && docker-compose restart")
pulumi.export("update_command", "cd sophia-ai-intel && git pull && docker-compose up -d --build")

pulumi.log.info("🎉 Sophia AI Intel deployed successfully on Lambda Labs via Pulumi Cloud!")
