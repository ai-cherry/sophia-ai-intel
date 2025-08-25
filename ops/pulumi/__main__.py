#!/usr/bin/env python3
"""
Sophia AI Intel - Pulumi + Lambda Labs Deployment
=================================================

Complete containerized microservices platform deployed to Lambda Labs GPU instances.
Uses Pulumi Cloud for state management and Lambda Labs for compute.
"""

import pulumi
from pulumi import ResourceOptions
from pulumi_lambdalabs import Instance
from pulumi_command import remote

# Get Pulumi configuration
config = pulumi.Config()

# Lambda Labs Configuration
lambda_api_key = config.require_secret("lambda-api-key")
private_key = config.require_secret("lambda-private-ssh-key")
public_key = config.require("lambda-public-ssh-key")

# Application secrets from Pulumi config
neon_url = config.require_secret("neon-database-url")
redis_url = config.require_secret("redis-url")
openai_key = config.require_secret("openai-api-key")

pulumi.log.info("🔐 Lambda Labs + Pulumi Cloud deployment starting")

# 1. Provision a new Lambda Labs instance
instance = Instance(
    "sophia-gpu-node",
    hostname="sophia-gpu",
    instance_type="gpu_1x_a100_sxm4",  # A100 GPU instance
    region="us-west-1",
    ssh_public_key=public_key,
)

# 2. Install Docker via remote command
install_docker = remote.Command(
    "install-docker",
    connection=remote.Connection(
        host=instance.public_ip,
        user="ubuntu",
        private_key=private_key,
    ),
    create="""
        set -e
        echo "🐳 Installing Docker..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker ubuntu
        sudo systemctl enable docker
        sudo systemctl start docker
        
        echo "🔧 Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        echo "📦 Installing Git..."
        sudo apt-get update -y
        sudo apt-get install -y git curl htop
        
        echo "✅ System setup complete"
    """,
)

# 3. Clone repository and setup environment
clone_repo = remote.Command(
    "clone-repo",
    connection=remote.Connection(
        host=instance.public_ip,
        user="ubuntu",
        private_key=private_key,
    ),
    create="""
        set -e
        echo "📂 Cloning Sophia AI Intel repository..."
        cd /home/ubuntu
        if [ ! -d "sophia-ai-intel" ]; then
            git clone https://github.com/ai-cherry/sophia-ai-intel.git
        fi
        cd sophia-ai-intel
        git pull origin main
        echo "✅ Repository cloned and updated"
    """,
    opts=ResourceOptions(depends_on=[install_docker]),
)

# 4. Create environment file with secrets
create_env = remote.Command(
    "create-env",
    connection=remote.Connection(
        host=instance.public_ip,
        user="ubuntu",
        private_key=private_key,
    ),
    create=pulumi.Output.all(neon_url, redis_url, openai_key).apply(
        lambda args: f"""
        set -e
        echo "🔐 Creating environment configuration..."
        cd /home/ubuntu/sophia-ai-intel
        
        cat > .env << 'ENV_EOF'
# Core Infrastructure
TENANT=pay-ready
NODE_ENV=production
BUILD_ID=lambda-labs-production

# Database and Cache
NEON_DATABASE_URL={args[0]}
REDIS_URL={args[1]}

# LLM Provider
OPENAI_API_KEY={args[2]}

# Lambda Labs API (for self-management)
LAMBDA_API_KEY=$LAMBDA_API_KEY
LAMBDA_API_ENDPOINT=https://cloud.lambdalabs.com/api/v1

# Qdrant Vector Database (optional)
QDRANT_URL=${{QDRANT_URL:-http://localhost:6333}}
QDRANT_API_KEY=${{QDRANT_API_KEY:-}}

# Additional provider keys (optional)
ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY:-}}
GROQ_API_KEY=${{GROQ_API_KEY:-}}
TAVILY_API_KEY=${{TAVILY_API_KEY:-}}
PERPLEXITY_API_KEY=${{PERPLEXITY_API_KEY:-}}
PORTKEY_API_KEY=${{PORTKEY_API_KEY:-}}
OPENROUTER_API_KEY=${{OPENROUTER_API_KEY:-}}

# Business integrations (optional)
HUBSPOT_ACCESS_TOKEN=${{HUBSPOT_ACCESS_TOKEN:-}}
APOLLO_API_KEY=${{APOLLO_API_KEY:-}}
GITHUB_APP_ID=${{GITHUB_APP_ID:-}}
ENV_EOF
        
        echo "✅ Environment file created"
        """
    ),
    opts=ResourceOptions(depends_on=[clone_repo]),
)

# 5. Deploy services with Docker Compose
deploy_services = remote.Command(
    "deploy-services",
    connection=remote.Connection(
        host=instance.public_ip,
        user="ubuntu",
        private_key=private_key,
    ),
    create="""
        set -e
        echo "🚀 Starting Sophia AI Intel services..."
        cd /home/ubuntu/sophia-ai-intel
        
        # Build and start services
        docker-compose up -d --build
        
        echo "⏳ Waiting for services to start..."
        sleep 90
        
        echo "🏥 Running health checks..."
        
        # Test core services
        docker-compose ps
        
        # Basic connectivity tests
        curl -f http://localhost:3000/ && echo "✅ Dashboard: OK" || echo "❌ Dashboard: FAIL"
        curl -f http://localhost:8081/healthz && echo "✅ Research: OK" || echo "❌ Research: FAIL"
        curl -f http://localhost:8082/healthz && echo "✅ Context: OK" || echo "❌ Context: FAIL"
        curl -f http://localhost:8083/healthz && echo "✅ GitHub: OK" || echo "❌ GitHub: FAIL"
        curl -f http://localhost:8084/healthz && echo "✅ Business: OK" || echo "❌ Business: FAIL"
        curl -f http://localhost:8085/healthz && echo "✅ Lambda: OK" || echo "❌ Lambda: FAIL"
        curl -f http://localhost:8086/healthz && echo "✅ HubSpot: OK" || echo "❌ HubSpot: FAIL"
        
        echo "🎉 Deployment completed!"
        echo "🌐 Access dashboard at: http://$(curl -s ifconfig.me):3000"
        echo "🔗 API gateway at: http://$(curl -s ifconfig.me)"
    """,
    opts=ResourceOptions(depends_on=[create_env]),
)

# Export outputs
pulumi.export("instance_id", instance.id)
pulumi.export("instance_ip", instance.public_ip)
pulumi.export("instance_type", "gpu_1x_a100_sxm4")
pulumi.export("region", "us-west-1")

# Service URLs
pulumi.export("dashboard_url", instance.public_ip.apply(lambda ip: f"http://{ip}:3000"))
pulumi.export("api_gateway_url", instance.public_ip.apply(lambda ip: f"http://{ip}"))
pulumi.export("research_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8081"))
pulumi.export("context_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8082"))
pulumi.export("github_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8083"))
pulumi.export("business_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8084"))
pulumi.export("lambda_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8085"))
pulumi.export("hubspot_api_url", instance.public_ip.apply(lambda ip: f"http://{ip}:8086"))

# Management info
pulumi.export("ssh_command", instance.public_ip.apply(lambda ip: f"ssh ubuntu@{ip}"))
pulumi.export("deployment_method", "pulumi-lambdalabs-providers")
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

pulumi.log.info("🎉 Sophia AI Intel deployment complete on Lambda Labs!")
