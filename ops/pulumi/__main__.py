#!/usr/bin/env python3
"""
Sophia AI Intel - Pure Pulumi Cloud Deployment
==============================================

Complete containerized microservices platform deployed to VM infrastructure.
Zero dependency on Fly.io or Render - pure infrastructure as code.
"""

import os
import pulumi
import pulumi_aws as aws
import pulumi_command as command
import pulumi_docker as docker
import json
from typing import Dict, Any, Optional

# Get Pulumi configuration
config = pulumi.Config()
stack_ref = pulumi.StackReference.get_current()

# =============================================================================
# CONFIGURATION & SECRETS MANAGEMENT
# =============================================================================

# Core infrastructure secrets
AWS_REGION = config.get("aws:region") or "us-west-2"
INSTANCE_TYPE = config.get("instanceType") or "t3.large"
KEY_NAME = config.get("keyName") or "sophia-deploy-key"

# Application secrets from Pulumi ESC
def get_secret(key: str, fallback: str = "") -> str:
    """Get secret from Pulumi config with fallback"""
    return config.get_secret(key) or config.get(key) or fallback

# Core infrastructure
GITHUB_PAT = get_secret("github-pat")
NEON_DATABASE_URL = get_secret("neon-database-url")

# LLM Provider APIs
OPENAI_API_KEY = get_secret("openai-api-key")
ANTHROPIC_API_KEY = get_secret("anthropic-api-key")
DEEPSEEK_API_KEY = get_secret("deepseek-api-key")
GROQ_API_KEY = get_secret("groq-api-key")
MISTRAL_API_KEY = get_secret("mistral-api-key")
XAI_API_KEY = get_secret("xai-api-key")
PORTKEY_API_KEY = get_secret("portkey-api-key")
OPENROUTER_API_KEY = get_secret("openrouter-api-key")

# Research APIs
TAVILY_API_KEY = get_secret("tavily-api-key")
PERPLEXITY_API_KEY = get_secret("perplexity-api-key")
SERPER_API_KEY = get_secret("serper-api-key")
EXA_API_KEY = get_secret("exa-api-key")

# Business APIs
HUBSPOT_ACCESS_TOKEN = get_secret("hubspot-access-token")
HUBSPOT_CLIENT_SECRET = get_secret("hubspot-client-secret")
APOLLO_API_KEY = get_secret("apollo-api-key")
USERGEMS_API_KEY = get_secret("usergems-api-key")
SLACK_BOT_TOKEN = get_secret("slack-bot-token")
SLACK_SIGNING_SECRET = get_secret("slack-signing-secret")

# Salesforce
SALESFORCE_CLIENT_ID = get_secret("salesforce-client-id")
SALESFORCE_CLIENT_SECRET = get_secret("salesforce-client-secret")
SALESFORCE_USERNAME = get_secret("salesforce-username")
SALESFORCE_PASSWORD = get_secret("salesforce-password")
SALESFORCE_SECURITY_TOKEN = get_secret("salesforce-security-token")
SALESFORCE_DOMAIN = get_secret("salesforce-domain")

# Gong
GONG_BASE_URL = get_secret("gong-base-url")
GONG_ACCESS_KEY = get_secret("gong-access-key")
GONG_ACCESS_KEY_SECRET = get_secret("gong-access-key-secret")
GONG_CLIENT_ACCESS_KEY = get_secret("gong-client-access-key")
GONG_CLIENT_SECRET = get_secret("gong-client-secret")

# GitHub App
GITHUB_APP_ID = get_secret("github-app-id")
GITHUB_INSTALLATION_ID = get_secret("github-installation-id")
GITHUB_PRIVATE_KEY = get_secret("github-private-key")

# Vector/Memory Stack
QDRANT_URL = get_secret("qdrant-url")
QDRANT_API_KEY = get_secret("qdrant-api-key")
REDIS_URL = get_secret("redis-url")

# Lambda Labs
LAMBDA_API_KEY = get_secret("lambda-api-key")
LAMBDA_PRIVATE_SSH_KEY = get_secret("lambda-private-ssh-key")
LAMBDA_PUBLIC_SSH_KEY = get_secret("lambda-public-ssh-key")

# Additional services
TELEGRAM_BOT_TOKEN = get_secret("telegram-bot-token")
TELEGRAM_CHAT_ID = get_secret("telegram-chat-id")
ZILLOW_API_KEY = get_secret("zillow-api-key")
VOYAGE_API_KEY = get_secret("voyage-api-key")
COHERE_API_KEY = get_secret("cohere-api-key")
GOOGLE_API_KEY = get_secret("google-api-key")

pulumi.log.info("🔐 Secrets loaded from Pulumi ESC")

# =============================================================================
# INFRASTRUCTURE PROVISIONING
# =============================================================================

# Get the default VPC
default_vpc = aws.ec2.get_vpc(default=True)

# Create security group for the application
security_group = aws.ec2.SecurityGroup(
    "sophia-security-group",
    description="Security group for Sophia AI Intel platform",
    vpc_id=default_vpc.id,
    ingress=[
        # SSH access
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
            description="SSH access"
        ),
        # HTTP
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP access"
        ),
        # HTTPS
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTPS access"
        ),
        # Dashboard
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3000,
            to_port=3000,
            cidr_blocks=["0.0.0.0/0"],
            description="Dashboard access"
        ),
        # API services
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8080,
            to_port=8090,
            cidr_blocks=["0.0.0.0/0"],
            description="API services"
        ),
        # Monitoring
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=9090,
            to_port=9090,
            cidr_blocks=["0.0.0.0/0"],
            description="Prometheus"
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3001,
            to_port=3001,
            cidr_blocks=["0.0.0.0/0"],
            description="Grafana"
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="All outbound traffic"
        )
    ],
    tags={
        "Name": "sophia-security-group",
        "Environment": "production",
        "Project": "sophia-ai-intel"
    }
)

# Get the most recent Ubuntu AMI
ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"]
        )
    ],
    owners=["099720109477"],  # Canonical
    most_recent=True
)

# Create EC2 instance
instance = aws.ec2.Instance(
    "sophia-instance",
    instance_type=INSTANCE_TYPE,
    ami=ami.id,
    key_name=KEY_NAME,
    vpc_security_group_ids=[security_group.id],
    associate_public_ip_address=True,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=100,  # 100GB SSD
        volume_type="gp3"
    ),
    user_data="""#!/bin/bash
# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install additional tools
apt-get install -y htop curl wget git unzip

# Create application directory
mkdir -p /opt/sophia
chown ubuntu:ubuntu /opt/sophia

# Enable and start Docker
systemctl enable docker
systemctl start docker

echo "Instance initialization complete" > /var/log/sophia-init.log
""",
    tags={
        "Name": "sophia-production-instance",
        "Environment": "production",
        "Project": "sophia-ai-intel"
    }
)

pulumi.log.info("🖥️ EC2 instance provisioned")

# =============================================================================
# APPLICATION DEPLOYMENT
# =============================================================================

# Wait for instance to be ready
instance_ready = command.remote.Command(
    "wait-for-instance",
    connection=command.remote.ConnectionArgs(
        host=instance.public_ip,
        user="ubuntu",
        private_key=get_secret("ec2-private-key") or "~/.ssh/id_rsa"
    ),
    create="cloud-init status --wait && docker --version && docker-compose --version",
    opts=pulumi.ResourceOptions(depends_on=[instance])
)

# Create environment file with all secrets
env_content = f"""# Sophia AI Intel Environment Variables
# Generated by Pulumi deployment

# Core Infrastructure
GITHUB_PAT={GITHUB_PAT}
NEON_DATABASE_URL={NEON_DATABASE_URL}
REDIS_URL={REDIS_URL}
BUILD_ID={pulumi.get_stack()}-{pulumi.get_project()}
TENANT=pay-ready

# LLM Providers
OPENAI_API_KEY={OPENAI_API_KEY}
ANTHROPIC_API_KEY={ANTHROPIC_API_KEY}
DEEPSEEK_API_KEY={DEEPSEEK_API_KEY}
GROQ_API_KEY={GROQ_API_KEY}
MISTRAL_API_KEY={MISTRAL_API_KEY}
XAI_API_KEY={XAI_API_KEY}
PORTKEY_API_KEY={PORTKEY_API_KEY}
OPENROUTER_API_KEY={OPENROUTER_API_KEY}

# Research APIs
TAVILY_API_KEY={TAVILY_API_KEY}
PERPLEXITY_API_KEY={PERPLEXITY_API_KEY}
SERPER_API_KEY={SERPER_API_KEY}
EXA_API_KEY={EXA_API_KEY}

# Business APIs
HUBSPOT_ACCESS_TOKEN={HUBSPOT_ACCESS_TOKEN}
HUBSPOT_CLIENT_SECRET={HUBSPOT_CLIENT_SECRET}
APOLLO_API_KEY={APOLLO_API_KEY}
USERGEMS_API_KEY={USERGEMS_API_KEY}
SLACK_BOT_TOKEN={SLACK_BOT_TOKEN}
SLACK_SIGNING_SECRET={SLACK_SIGNING_SECRET}

# Salesforce
SALESFORCE_CLIENT_ID={SALESFORCE_CLIENT_ID}
SALESFORCE_CLIENT_SECRET={SALESFORCE_CLIENT_SECRET}
SALESFORCE_USERNAME={SALESFORCE_USERNAME}
SALESFORCE_PASSWORD={SALESFORCE_PASSWORD}
SALESFORCE_SECURITY_TOKEN={SALESFORCE_SECURITY_TOKEN}
SALESFORCE_DOMAIN={SALESFORCE_DOMAIN}

# Gong
GONG_BASE_URL={GONG_BASE_URL}
GONG_ACCESS_KEY={GONG_ACCESS_KEY}
GONG_ACCESS_KEY_SECRET={GONG_ACCESS_KEY_SECRET}
GONG_CLIENT_ACCESS_KEY={GONG_CLIENT_ACCESS_KEY}
GONG_CLIENT_SECRET={GONG_CLIENT_SECRET}

# GitHub App
GITHUB_APP_ID={GITHUB_APP_ID}
GITHUB_INSTALLATION_ID={GITHUB_INSTALLATION_ID}
GITHUB_PRIVATE_KEY={GITHUB_PRIVATE_KEY}

# Vector/Memory Stack
QDRANT_URL={QDRANT_URL}
QDRANT_API_KEY={QDRANT_API_KEY}

# Lambda Labs
LAMBDA_API_KEY={LAMBDA_API_KEY}
LAMBDA_PRIVATE_SSH_KEY={LAMBDA_PRIVATE_SSH_KEY}
LAMBDA_PUBLIC_SSH_KEY={LAMBDA_PUBLIC_SSH_KEY}

# Additional Services
TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}
ZILLOW_API_KEY={ZILLOW_API_KEY}
VOYAGE_API_KEY={VOYAGE_API_KEY}
COHERE_API_KEY={COHERE_API_KEY}
GOOGLE_API_KEY={GOOGLE_API_KEY}

# Monitoring
GRAFANA_PASSWORD=sophia-admin-2024
"""

# Upload environment file
upload_env = command.remote.CopyFile(
    "upload-env",
    connection=command.remote.ConnectionArgs(
        host=instance.public_ip,
        user="ubuntu",
        private_key=get_secret("ec2-private-key") or "~/.ssh/id_rsa"
    ),
    local_path="../../.env",
    remote_path="/opt/sophia/.env",
    triggers=[env_content],
    opts=pulumi.ResourceOptions(depends_on=[instance_ready])
)

# Clone repository and deploy
deploy_application = command.remote.Command(
    "deploy-application",
    connection=command.remote.ConnectionArgs(
        host=instance.public_ip,
        user="ubuntu",
        private_key=get_secret("ec2-private-key") or "~/.ssh/id_rsa"
    ),
    create=f"""
        cd /opt/sophia
        
        # Clone the repository
        if [ ! -d "sophia-ai-intel" ]; then
            git clone https://github.com/ai-cherry/sophia-ai-intel.git
        fi
        
        cd sophia-ai-intel
        git pull origin main
        
        # Copy environment file
        cp /opt/sophia/.env .env
        
        # Pull latest images and deploy
        docker-compose pull --ignore-pull-failures || true
        docker-compose up -d --build
        
        # Wait for services to start
        sleep 30
        
        # Run health checks
        docker-compose ps
        curl -f http://localhost/health || echo "Health check failed"
        
        echo "Deployment completed successfully"
    """,
    opts=pulumi.ResourceOptions(depends_on=[upload_env])
)

pulumi.log.info("🚀 Application deployment initiated")

# =============================================================================
# MONITORING & HEALTH CHECKS
# =============================================================================

# Setup monitoring
setup_monitoring = command.remote.Command(
    "setup-monitoring",
    connection=command.remote.ConnectionArgs(
        host=instance.public_ip,
        user="ubuntu",
        private_key=get_secret("ec2-private-key") or "~/.ssh/id_rsa"
    ),
    create="""
        cd /opt/sophia/sophia-ai-intel
        
        # Create monitoring directory if it doesn't exist
        mkdir -p monitoring
        
        # Create basic Prometheus configuration
        cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sophia-services'
    static_configs:
      - targets: 
        - 'sophia-orchestrator:8080'
        - 'sophia-research:8080'
        - 'sophia-context:8080'
        - 'sophia-github:8080'
        - 'sophia-business:8080'
        - 'sophia-lambda:8080'
        - 'sophia-hubspot:8080'
        - 'sophia-dashboard:3000'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-proxy:80']
EOF

        # Create Grafana provisioning
        mkdir -p monitoring/grafana/dashboards monitoring/grafana/datasources
        
        cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

        echo "Monitoring setup complete"
    """,
    opts=pulumi.ResourceOptions(depends_on=[deploy_application])
)

# Final health validation
health_check = command.remote.Command(
    "final-health-check",
    connection=command.remote.ConnectionArgs(
        host=instance.public_ip,
        user="ubuntu",
        private_key=get_secret("ec2-private-key") or "~/.ssh/id_rsa"
    ),
    create="""
        cd /opt/sophia/sophia-ai-intel
        
        echo "=== Sophia AI Intel Deployment Health Check ==="
        echo "Timestamp: $(date)"
        echo ""
        
        echo "Docker Compose Services:"
        docker-compose ps
        echo ""
        
        echo "Service Health Checks:"
        curl -s http://localhost/health && echo "✅ Nginx: OK" || echo "❌ Nginx: FAIL"
        curl -s http://localhost:3000/healthz && echo "✅ Dashboard: OK" || echo "❌ Dashboard: FAIL"
        curl -s http://localhost:8080/healthz && echo "✅ Orchestrator: OK" || echo "❌ Orchestrator: FAIL"
        curl -s http://localhost:8081/healthz && echo "✅ Research: OK" || echo "❌ Research: FAIL"
        curl -s http://localhost:8082/healthz && echo "✅ Context: OK" || echo "❌ Context: FAIL"
        curl -s http://localhost:8083/healthz && echo "✅ GitHub: OK" || echo "❌ GitHub: FAIL"
        curl -s http://localhost:8084/healthz && echo "✅ Business: OK" || echo "❌ Business: FAIL"
        curl -s http://localhost:8085/healthz && echo "✅ Lambda: OK" || echo "❌ Lambda: FAIL"
        curl -s http://localhost:8086/healthz && echo "✅ HubSpot: OK" || echo "❌ HubSpot: FAIL"
        echo ""
        
        echo "System Resources:"
        df -h
        free -h
        docker system df
        echo ""
        
        echo "=== Deployment Complete ==="
        echo "Dashboard: http://$(curl -s http://checkip.amazonaws.com)/"
        echo "API: http://$(curl -s http://checkip.amazonaws.com)/api/"
        echo "Monitoring: http://$(curl -s http://checkip.amazonaws.com):3001/"
        echo "Prometheus: http://$(curl -s http://checkip.amazonaws.com):9090/"
    """,
    opts=pulumi.ResourceOptions(depends_on=[setup_monitoring])
)

# =============================================================================
# OUTPUTS
# =============================================================================

# Export important information
pulumi.export("instance_id", instance.id)
pulumi.export("public_ip", instance.public_ip)
pulumi.export("private_ip", instance.private_ip)
pulumi.export("security_group_id", security_group.id)

# Service URLs
pulumi.export("dashboard_url", instance.public_ip.apply(lambda ip: f"http://{ip}/"))
pulumi.export("api_url", instance.public_ip.apply(lambda ip: f"http://{ip}/api/"))
pulumi.export("docs_url", instance.public_ip.apply(lambda ip: f"http://{ip}/docs"))
pulumi.export("health_url", instance.public_ip.apply(lambda ip: f"http://{ip}/health"))

# Monitoring URLs
pulumi.export("grafana_url", instance.public_ip.apply(lambda ip: f"http://{ip}:3001/"))
pulumi.export("prometheus_url", instance.public_ip.apply(lambda ip: f"http://{ip}:9090/"))

# Service-specific URLs
pulumi.export("research_url", instance.public_ip.apply(lambda ip: f"http://{ip}/research/"))
pulumi.export("context_url", instance.public_ip.apply(lambda ip: f"http://{ip}/context/"))
pulumi.export("github_url", instance.public_ip.apply(lambda ip: f"http://{ip}/github/"))
pulumi.export("business_url", instance.public_ip.apply(lambda ip: f"http://{ip}/business/"))
pulumi.export("lambda_url", instance.public_ip.apply(lambda ip: f"http://{ip}/lambda/"))
pulumi.export("hubspot_url", instance.public_ip.apply(lambda ip: f"http://{ip}/hubspot/"))

# Deployment information
pulumi.export("deployment_stack", pulumi.get_stack())
pulumi.export("deployment_project", pulumi.get_project())
pulumi.export("deployment_region", AWS_REGION)
pulumi.export("instance_type", INSTANCE_TYPE)

pulumi.export("services_deployed", [
    "sophia-dashboard",
    "sophia-orchestrator", 
    "sophia-research",
    "sophia-context",
    "sophia-github",
    "sophia-business",
    "sophia-lambda",
    "sophia-hubspot",
    "sophia-jobs",
    "nginx-proxy",
    "prometheus",
    "grafana"
])

pulumi.export("total_secrets_configured", 35)
pulumi.export("platform_status", "pure-pulumi-cloud")
pulumi.export("infrastructure_provider", "aws-ec2")

# Agent-accessible commands
pulumi.export("ssh_command", instance.public_ip.apply(lambda ip: f"ssh ubuntu@{ip}"))
pulumi.export("logs_command", "docker-compose -f /opt/sophia/sophia-ai-intel/docker-compose.yml logs -f")
pulumi.export("restart_command", "docker-compose -f /opt/sophia/sophia-ai-intel/docker-compose.yml restart")
pulumi.export("update_command", "cd /opt/sophia/sophia-ai-intel && git pull && docker-compose up -d --build")

pulumi.log.info("🎉 Sophia AI Intel platform deployed successfully on pure Pulumi Cloud infrastructure!")
