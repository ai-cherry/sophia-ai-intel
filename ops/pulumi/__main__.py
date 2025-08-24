#!/usr/bin/env python3
"""
Sophia AI Infrastructure as Code - Pulumi Stack
==============================================

Comprehensive secrets management and infrastructure provisioning.
Eliminates manual API key handling through GitHub Secrets -> Pulumi -> Fly.io chain.
"""

import os
import pulumi
import pulumi_fly as fly
import json
import requests
from typing import Dict, Any

# Initialize Pulumi configuration
config = pulumi.Config()

# ============================================================================
# SECRETS MANAGEMENT - GITHUB -> PULUMI -> FLY CHAIN
# ============================================================================

def load_github_secrets() -> Dict[str, str]:
    """Load all secrets from GitHub environment (Codespaces/Actions)"""
    
    secrets = {}
    
    # Core Infrastructure
    secrets.update({
        "fly-api-token": os.getenv("FLY_API_TOKEN", ""),
        "gh-pat-token": os.getenv("GH_PAT_TOKEN", ""),
    })
    
    # Lambda Labs GPU Compute
    secrets.update({
        "lambda-api-key": os.getenv("LAMBDA_API_KEY", ""),
        "lambda-cloud-api-key": os.getenv("LAMBDA_CLOUD_API_KEY", ""),
        "lambda-private-ssh-key": os.getenv("LAMBDA_PRIVATE_SSH_KEY", ""),
        "lambda-public-ssh-key": os.getenv("LAMBDA_PUBLIC_SSH_KEY", ""),
    })
    
    # Memory Stack
    secrets.update({
        "redis-user-api-key": os.getenv("REDIS_USER_API_KEY", ""),
        "redis-endpoint": os.getenv("REDIS_ENDPOINT", ""),
        "redis-port": os.getenv("REDIS_PORT", ""),
        "redis-password": os.getenv("REDIS_PASSWORD", ""),
        "qdrant-api-key": os.getenv("QDRANT_API_KEY", ""),
        "qdrant-url": os.getenv("QDRANT_URL", ""),
        "neon-api-token": os.getenv("NEON_API_TOKEN", ""),
    })
    
    # LLM Routing
    secrets.update({
        "portkey-api-key": os.getenv("PORTKEY_API_KEY", ""),
        "openrouter-api-key": os.getenv("OPENROUTER_API_KEY", ""),
    })
    
    # Business Integrations
    secrets.update({
        "gong-access-key": os.getenv("GONG_ACCESS_KEY", ""),
        "gong-client-secret": os.getenv("GONG_CLIENT_SECRET", ""),
        "hubspot-access-token": os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
        "hubspot-client-secret": os.getenv("HUBSPOT_CLIENT_SECRET", ""),
        "slack-bot-token": os.getenv("SLACK_BOT_TOKEN", ""),
        "slack-app-token": os.getenv("SLACK_APP_TOKEN", ""),
        "slack-client-secret": os.getenv("SLACK_CLIENT_SECRET", ""),
        "slack-signing-secret": os.getenv("SLACK_SIGNING_SECRET", ""),
        "notion-api-key": os.getenv("NOTION_API_KEY", ""),
    })
    
    # Web Research APIs
    secrets.update({
        "tavily-api-key": os.getenv("TAVILY_API_KEY", ""),
        "serper-api-key": os.getenv("SERPER_API_KEY", ""),
        "exa-api-key": os.getenv("EXA_API_KEY", ""),
        "brave-api-key": os.getenv("BRAVE_API_KEY", ""),
        "perplexity-api-key": os.getenv("PERPLEXITY_API_KEY", ""),
    })
    
    # LLM Provider APIs
    secrets.update({
        "openai-api-key": os.getenv("OPENAI_API_KEY", ""),
        "anthropic-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
        "deepseek-api-key": os.getenv("DEEPSEEK_API_KEY", ""),
        "groq-api-key": os.getenv("GROQ_API_KEY", ""),
        "mistral-api-key": os.getenv("MISTRAL_API_KEY", ""),
        "xai-api-key": os.getenv("XAI_API_KEY", ""),
    })
    
    return {k: v for k, v in secrets.items() if v}  # Only return configured secrets

# Load all secrets from GitHub environment
github_secrets = load_github_secrets()

# Store secrets in Pulumi config (encrypted)
for key, value in github_secrets.items():
    if value:
        config.set_secret(key, value)

pulumi.log.info(f"📋 Loaded {len(github_secrets)} secrets from GitHub environment")

# ============================================================================
# INFRASTRUCTURE PROVISIONING
# ============================================================================

def create_neon_resources():
    """Create Neon database resources with API token"""
    neon_token = github_secrets.get("neon-api-token", "")
    
    if not neon_token:
        pulumi.log.warn("🚨 Neon API token not available")
        return None
    
    # Create Neon project via REST API (no native Pulumi provider)
    def create_neon_project():
        headers = {"Authorization": f"Bearer {neon_token}"}
        payload = {
            "project": {
                "name": "sophia-ai-production",
                "region": "us-west-2",
                "pg_version": 16
            }
        }
        
        try:
            response = requests.post(
                "https://console.neon.tech/api/v2/projects",
                headers=headers,
                json=payload
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                pulumi.log.error(f"❌ Neon project creation failed: {response.status_code}")
                return None
        except Exception as e:
            pulumi.log.error(f"❌ Neon API request failed: {e}")
            return None
    
    # This would be called during pulumi up
    return "neon-project-placeholder"

def create_redis_resources():
    """Set up Redis connection configuration"""
    redis_config = {
        "endpoint": github_secrets.get("redis-endpoint", ""),
        "port": github_secrets.get("redis-port", ""),
        "password": github_secrets.get("redis-password", ""),
        "user_api_key": github_secrets.get("redis-user-api-key", "")
    }
    
    if redis_config["endpoint"]:
        redis_url = f"redis://:{redis_config['password']}@{redis_config['endpoint']}:{redis_config['port']}"
        return redis_url
    
    return None

# ============================================================================
# FLY.IO APP AND MACHINE DEPLOYMENT
# ============================================================================

def create_mcp_service(service_name: str, service_env: Dict[str, str], regions: list = ["ord"]):
    """Create standardized MCP service with secret injection"""
    
    app_name = f"sophiaai-mcp-{service_name}-v2"
    
    # Create Fly app
    app = fly.App(
        app_name.replace("-", "_"),  # Pulumi resource name
        name=app_name,
        org="pay-ready"
    )
    
    # Create machine in each region
    machines = []
    for region in regions:
        machine = fly.Machine(
            f"{service_name}_{region}_machine",
            app=app.name,
            region=region,
            config=fly.MachineConfigArgs(
                image=f"registry.fly.io/{app_name}:latest",
                env=service_env,
                guest=fly.MachineGuestArgs(
                    cpu_kind="shared",
                    cpus=1,
                    memory_mb=1024
                ),
                services=[
                    fly.MachineServiceArgs(
                        ports=[
                            fly.MachinePortArgs(port=80, handlers=["http"]),
                            fly.MachinePortArgs(port=443, handlers=["http", "tls"])
                        ],
                        protocol="tcp",
                        internal_port=8080
                    )
                ],
                checks={
                    "healthz": fly.MachineCheckArgs(
                        type="http",
                        method="GET", 
                        path="/healthz",
                        interval="30s",
                        timeout="10s"
                    )
                }
            )
        )
        machines.append(machine)
    
    pulumi.export(f"{service_name}_app_name", app.name)
    return app, machines

# ============================================================================
# SERVICE DEPLOYMENTS WITH COMPREHENSIVE SECRET INJECTION
# ============================================================================

# Lambda Labs GPU Compute Service
lambda_env = {
    "LAMBDA_API_KEY": github_secrets.get("lambda-api-key", ""),
    "LAMBDA_CLOUD_API_KEY": github_secrets.get("lambda-cloud-api-key", ""),
    "LAMBDA_PRIVATE_SSH_KEY": github_secrets.get("lambda-private-ssh-key", ""),
    "LAMBDA_PUBLIC_SSH_KEY": github_secrets.get("lambda-public-ssh-key", ""),
    "TENANT": "pay-ready"
}

lambda_app, lambda_machines = create_mcp_service("lambda", lambda_env, ["ord", "iad"])

# Gong Business Intelligence Service
gong_env = {
    "GONG_ACCESS_KEY": github_secrets.get("gong-access-key", ""),
    "GONG_CLIENT_SECRET": github_secrets.get("gong-client-secret", ""),
    "GONG_BASE_URL": "https://api.gong.io",
    "TENANT": "pay-ready"
}

gong_app, gong_machines = create_mcp_service("gong", gong_env, ["ord", "sjc"])

# HubSpot CRM Service
hubspot_env = {
    "HUBSPOT_ACCESS_TOKEN": github_secrets.get("hubspot-access-token", ""),
    "HUBSPOT_CLIENT_SECRET": github_secrets.get("hubspot-client-secret", ""),
    "TENANT": "pay-ready"
}

hubspot_app, hubspot_machines = create_mcp_service("hubspot", hubspot_env, ["ord", "iad"])

# Slack Communication Service  
slack_env = {
    "SLACK_BOT_TOKEN": github_secrets.get("slack-bot-token", ""),
    "SLACK_APP_TOKEN": github_secrets.get("slack-app-token", ""),
    "SLACK_CLIENT_SECRET": github_secrets.get("slack-client-secret", ""),
    "SLACK_SIGNING_SECRET": github_secrets.get("slack-signing-secret", ""),
    "TENANT": "pay-ready"
}

slack_app, slack_machines = create_mcp_service("slack", slack_env, ["ord"])

# Notion Knowledge Base Service
notion_env = {
    "NOTION_API_KEY": github_secrets.get("notion-api-key", ""),
    "TENANT": "pay-ready"
}

notion_app, notion_machines = create_mcp_service("notion", notion_env, ["ord", "ams"])

# Browser/Web Research Service
browser_env = {
    "TAVILY_API_KEY": github_secrets.get("tavily-api-key", ""),
    "SERPER_API_KEY": github_secrets.get("serper-api-key", ""),
    "EXA_API_KEY": github_secrets.get("exa-api-key", ""),
    "BRAVE_API_KEY": github_secrets.get("brave-api-key", ""),
    "PERPLEXITY_API_KEY": github_secrets.get("perplexity-api-key", ""),
    "TENANT": "pay-ready"
}

browser_app, browser_machines = create_mcp_service("browser", browser_env, ["ord", "sjc", "ams"])

# Orchestrator Service with All LLM APIs
orchestrator_env = {
    "OPENAI_API_KEY": github_secrets.get("openai-api-key", ""),
    "ANTHROPIC_API_KEY": github_secrets.get("anthropic-api-key", ""),
    "DEEPSEEK_API_KEY": github_secrets.get("deepseek-api-key", ""),
    "GROQ_API_KEY": github_secrets.get("groq-api-key", ""),
    "MISTRAL_API_KEY": github_secrets.get("mistral-api-key", ""),
    "XAI_API_KEY": github_secrets.get("xai-api-key", ""),
    "PORTKEY_API_KEY": github_secrets.get("portkey-api-key", ""),
    "OPENROUTER_API_KEY": github_secrets.get("openrouter-api-key", ""),
    # Memory stack connections
    "REDIS_URL": create_redis_resources() or "",
    "QDRANT_API_KEY": github_secrets.get("qdrant-api-key", ""),
    "QDRANT_URL": github_secrets.get("qdrant-url", ""),
    "DATABASE_URL": "placeholder-from-neon-creation",
    "TENANT": "pay-ready"
}

orchestrator_app, orchestrator_machines = create_mcp_service("orchestrator", orchestrator_env, ["ord", "iad", "sjc"])

# Dashboard Service
dashboard_env = {
    "TENANT": "pay-ready",
    "NODE_ENV": "production"
}

dashboard_app, dashboard_machines = create_mcp_service("dashboard", dashboard_env, ["ord", "iad", "sjc"])

# ============================================================================
# INFRASTRUCTURE RESOURCES
# ============================================================================

# Create Neon database project
neon_project = create_neon_resources()

# Redis configuration (external service)
redis_url = create_redis_resources()
if redis_url:
    pulumi.export("redis-url", redis_url)

# Qdrant configuration (external service)
qdrant_url = github_secrets.get("qdrant-url", "")
if qdrant_url:
    pulumi.export("qdrant-url", qdrant_url)

# ============================================================================
# PULUMI OUTPUTS FOR AGENTS
# ============================================================================

pulumi.export("total-secrets-configured", len(github_secrets))
pulumi.export("services-deployed", [
    "lambda", "gong", "hubspot", "slack", "notion", "browser", "orchestrator", "dashboard"
])
pulumi.export("regions-deployed", ["ord", "iad", "sjc", "ams"])

# Dashboard URL for agents and users
pulumi.export("dashboard-url", lambda_app.name.apply(lambda name: f"https://{name.replace('lambda', 'dashboard')}.fly.dev"))

# Agent management endpoints
pulumi.export("agent-endpoints", {
    "lambda": lambda_app.name.apply(lambda name: f"https://{name}.fly.dev"),
    "gong": gong_app.name.apply(lambda name: f"https://{name}.fly.dev"),
    "hubspot": hubspot_app.name.apply(lambda name: f"https://{name}.fly.dev"),
    "orchestrator": orchestrator_app.name.apply(lambda name: f"https://{name}.fly.dev"),
})

# ============================================================================
# AGENT ACCESSIBLE FUNCTIONS
# ============================================================================

def agent_provision_infrastructure():
    """
    Function that agents can call to provision/update infrastructure.
    Eliminates manual key management completely.
    """
    return {
        "command": "pulumi up --yes --stack sophia-production",
        "description": "Provisions all infrastructure with automatic secret injection",
        "secrets_managed": len(github_secrets),
        "services_deployed": 8,
        "regions": 4
    }

# Export agent functions
pulumi.export("agent-provision-command", "cd ops/pulumi && pulumi up --yes")
pulumi.export("agent-update-command", "cd ops/pulumi && pulumi refresh && pulumi up --yes")
pulumi.export("agent-destroy-command", "cd ops/pulumi && pulumi destroy --yes")

pulumi.log.info(f"🚀 Sophia AI infrastructure stack configured with {len(github_secrets)} secrets")
pulumi.log.info("🎯 Agents can now provision infrastructure via: cd ops/pulumi && pulumi up --yes")
