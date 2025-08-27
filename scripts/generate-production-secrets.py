#!/usr/bin/env python3
"""
Secure Production Secrets Generator
Generates cryptographically secure secrets to replace placeholder values
"""

import secrets
import string
import base64
import os
from pathlib import Path
from typing import Dict, Any
import uuid
from datetime import datetime

class SecureSecretsGenerator:
    """Generates cryptographically secure secrets for production deployment"""
    
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits
        self.secure_alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        
    def generate_api_key_format(self, prefix: str, length: int = 48) -> str:
        """Generate API key with specific prefix format"""
        secret_part = ''.join(secrets.choice(self.alphabet) for _ in range(length))
        return f"{prefix}{secret_part}"
    
    def generate_secure_password(self, length: int = 32) -> str:
        """Generate cryptographically secure password"""
        return ''.join(secrets.choice(self.secure_alphabet) for _ in range(length))
    
    def generate_jwt_secret(self, length: int = 64) -> str:
        """Generate JWT secret"""
        return secrets.token_urlsafe(length)
    
    def generate_uuid(self) -> str:
        """Generate UUID for account IDs"""
        return str(uuid.uuid4())
    
    def generate_base64_key(self, length: int = 32) -> str:
        """Generate base64 encoded key"""
        random_bytes = secrets.token_bytes(length)
        return base64.b64encode(random_bytes).decode('utf-8')

def generate_production_secrets() -> Dict[str, Any]:
    """Generate all production secrets"""
    generator = SecureSecretsGenerator()
    
    secrets_map = {
        # Infrastructure
        "LAMBDA_API_KEY": f"lambda_prod_{generator.generate_secure_password(24)}",
        
        # Database
        "POSTGRES_PASSWORD": generator.generate_secure_password(32),
        "REDIS_USER_KEY": generator.generate_secure_password(24),
        "REDIS_ACCOUNT_KEY": generator.generate_secure_password(24),
        
        # Qdrant
        "QDRANT_API_KEY": generator.generate_api_key_format("qdrant_", 32),
        "QDRANT_MANAGEMENT_KEY": generator.generate_api_key_format("qdrant_mgmt_", 32),
        "QDRANT_CLUSTER_API_KEY": generator.generate_api_key_format("qdrant_cluster_", 32),
        "QDRANT_ACCOUNT_ID": generator.generate_uuid(),
        
        # LLM APIs (Note: These need to be real API keys from providers)
        "OPENAI_API_KEY": "sk-proj-REPLACE_WITH_REAL_OPENAI_KEY",
        "ANTHROPIC_API_KEY": "sk-ant-REPLACE_WITH_REAL_ANTHROPIC_KEY", 
        "OPENROUTER_API_KEY": "sk-or-REPLACE_WITH_REAL_OPENROUTER_KEY",
        "GROQ_API_KEY": "gsk_REPLACE_WITH_REAL_GROQ_KEY",
        
        # Research APIs (Note: These need to be real API keys from providers)
        "SERPAPI_API_KEY": "REPLACE_WITH_REAL_SERPAPI_KEY",
        "TAVILY_API_KEY": "tvly-REPLACE_WITH_REAL_TAVILY_KEY",
        "PERPLEXITY_API_KEY": "pplx-REPLACE_WITH_REAL_PERPLEXITY_KEY",
        
        # Business Integration (Note: These need to be real credentials)
        "HUBSPOT_API_KEY": "pat-REPLACE_WITH_REAL_HUBSPOT_KEY",
        "HUBSPOT_ACCESS_TOKEN": "pat-REPLACE_WITH_REAL_HUBSPOT_TOKEN",
        "HUBSPOT_CLIENT_SECRET": "REPLACE_WITH_REAL_HUBSPOT_SECRET",
        
        "GONG_ACCESS_KEY": "REPLACE_WITH_REAL_GONG_ACCESS_KEY",
        "GONG_ACCESS_KEY_SECRET": "REPLACE_WITH_REAL_GONG_SECRET",
        
        "SALESFORCE_CLIENT_ID": "REPLACE_WITH_REAL_SF_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET": "REPLACE_WITH_REAL_SF_SECRET",
        "SALESFORCE_USERNAME": "REPLACE_WITH_REAL_SF_USERNAME",
        "SALESFORCE_PASSWORD": "REPLACE_WITH_REAL_SF_PASSWORD",
        
        "SLACK_BOT_TOKEN": "xoxb-REPLACE_WITH_REAL_SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN": "xapp-REPLACE_WITH_REAL_SLACK_APP_TOKEN",
        "SLACK_CLIENT_ID": "REPLACE_WITH_REAL_SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET": "REPLACE_WITH_REAL_SLACK_SECRET",
        "SLACK_SIGNING_SECRET": "REPLACE_WITH_REAL_SLACK_SIGNING_SECRET",
        
        "APOLLO_API_KEY": "REPLACE_WITH_REAL_APOLLO_KEY",
        "TELEGRAM_BOT_TOKEN": "REPLACE_WITH_REAL_TELEGRAM_TOKEN",
        
        # GitHub Integration (Note: These need real GitHub App credentials)
        "GITHUB_APP_ID": "REPLACE_WITH_REAL_GITHUB_APP_ID",
        "GITHUB_INSTALLATION_ID": "REPLACE_WITH_REAL_GITHUB_INSTALLATION_ID",
        "GITHUB_PRIVATE_KEY": "REPLACE_WITH_REAL_GITHUB_PRIVATE_KEY",
        "GITHUB_TOKEN": "ghp_REPLACE_WITH_REAL_GITHUB_TOKEN",
        
        # DNS & Infrastructure (Note: These need real credentials)
        "DNSIMPLE_API_KEY": "REPLACE_WITH_REAL_DNSIMPLE_KEY",
        "DNSIMPLE_ACCOUNT_ID": "REPLACE_WITH_REAL_DNSIMPLE_ACCOUNT",
        "DOCKER_PAT": "REPLACE_WITH_REAL_DOCKER_TOKEN",
        
        # Security - Generated
        "JWT_SECRET": generator.generate_jwt_secret(64),
        "API_SECRET_KEY": generator.generate_jwt_secret(64),
        "GRAFANA_ADMIN_PASSWORD": generator.generate_secure_password(24)
    }
    
    return secrets_map

def create_secrets_template(secrets: Dict[str, Any]) -> str:
    """Create environment file template with secure secrets"""
    template = f"""# Sophia AI Intel Platform - Production Environment (Secure)
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Environment: PRODUCTION
# Target: Lambda Labs + Kubernetes
# WARNING: CONTAINS SENSITIVE DATA - DO NOT COMMIT

# =============================================================================
# DEPLOYMENT CONFIGURATION
# =============================================================================

# Environment
NODE_ENV=production
ENVIRONMENT=production
LOG_LEVEL=info

# Domain Configuration
DOMAIN=www.sophia-intel.ai
API_DOMAIN=api.sophia-intel.ai
APP_DOMAIN=www.sophia-intel.ai

# Lambda Labs Configuration
LAMBDA_API_KEY={secrets['LAMBDA_API_KEY']}
LAMBDA_CLOUD_ENDPOINT=https://cloud.lambdalabs.com/api/v1

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL (Production) - UPDATE WITH NEON CREDENTIALS
POSTGRES_URL=postgresql://sophia:{secrets['POSTGRES_PASSWORD']}@ep-cool-scene-a5a6p2ly.us-east-2.aws.neon.tech/sophia?sslmode=require
POSTGRES_PASSWORD={secrets['POSTGRES_PASSWORD']}
POSTGRES_DB=sophia
POSTGRES_USER=sophia

# Redis (Production) - UPDATE WITH REDIS CLOUD CREDENTIALS  
REDIS_URL=rediss://redis-12345.c1.us-east1-2.gce.cloud.redislabs.com:12345
REDIS_HOST=redis-12345.c1.us-east1-2.gce.cloud.redislabs.com
REDIS_PORT=12345
REDIS_USER_KEY={secrets['REDIS_USER_KEY']}
REDIS_ACCOUNT_KEY={secrets['REDIS_ACCOUNT_KEY']}

# Qdrant Vector Database (Production) - UPDATE WITH QDRANT CLOUD CREDENTIALS
QDRANT_URL=https://your-cluster-url.qdrant.io:6333
QDRANT_API_KEY={secrets['QDRANT_API_KEY']}
QDRANT_MANAGEMENT_KEY={secrets['QDRANT_MANAGEMENT_KEY']}
QDRANT_CLUSTER_API_KEY={secrets['QDRANT_CLUSTER_API_KEY']}
QDRANT_ACCOUNT_ID={secrets['QDRANT_ACCOUNT_ID']}

# =============================================================================
# LLM API KEYS (Production) - REPLACE WITH REAL API KEYS
# =============================================================================

# OpenAI
OPENAI_API_KEY={secrets['OPENAI_API_KEY']}

# Anthropic Claude  
ANTHROPIC_API_KEY={secrets['ANTHROPIC_API_KEY']}

# OpenRouter
OPENROUTER_API_KEY={secrets['OPENROUTER_API_KEY']}

# Groq
GROQ_API_KEY={secrets['GROQ_API_KEY']}

# =============================================================================
# RESEARCH & DATA PROVIDERS - REPLACE WITH REAL API KEYS
# =============================================================================

# Search & Research
SERPAPI_API_KEY={secrets['SERPAPI_API_KEY']}
TAVILY_API_KEY={secrets['TAVILY_API_KEY']}
PERPLEXITY_API_KEY={secrets['PERPLEXITY_API_KEY']}

# =============================================================================
# BUSINESS INTEGRATION KEYS - REPLACE WITH REAL CREDENTIALS
# =============================================================================

# HubSpot
HUBSPOT_API_KEY={secrets['HUBSPOT_API_KEY']}
HUBSPOT_ACCESS_TOKEN={secrets['HUBSPOT_ACCESS_TOKEN']}
HUBSPOT_CLIENT_SECRET={secrets['HUBSPOT_CLIENT_SECRET']}

# Gong
GONG_ACCESS_KEY={secrets['GONG_ACCESS_KEY']}
GONG_ACCESS_KEY_SECRET={secrets['GONG_ACCESS_KEY_SECRET']}
GONG_BASE_URL=https://api.gong.io

# Salesforce
SALESFORCE_CLIENT_ID={secrets['SALESFORCE_CLIENT_ID']}
SALESFORCE_CLIENT_SECRET={secrets['SALESFORCE_CLIENT_SECRET']}
SALESFORCE_USERNAME={secrets['SALESFORCE_USERNAME']}
SALESFORCE_PASSWORD={secrets['SALESFORCE_PASSWORD']}

# Slack
SLACK_BOT_TOKEN={secrets['SLACK_BOT_TOKEN']}
SLACK_APP_TOKEN={secrets['SLACK_APP_TOKEN']}
SLACK_CLIENT_ID={secrets['SLACK_CLIENT_ID']}
SLACK_CLIENT_SECRET={secrets['SLACK_CLIENT_SECRET']}
SLACK_SIGNING_SECRET={secrets['SLACK_SIGNING_SECRET']}

# Other Integrations
APOLLO_API_KEY={secrets['APOLLO_API_KEY']}
TELEGRAM_BOT_TOKEN={secrets['TELEGRAM_BOT_TOKEN']}

# =============================================================================
# GITHUB INTEGRATION - REPLACE WITH REAL GITHUB APP CREDENTIALS
# =============================================================================

# GitHub App
GITHUB_APP_ID={secrets['GITHUB_APP_ID']}
GITHUB_INSTALLATION_ID={secrets['GITHUB_INSTALLATION_ID']}
GITHUB_PRIVATE_KEY={secrets['GITHUB_PRIVATE_KEY']}
GITHUB_TOKEN={secrets['GITHUB_TOKEN']}

# =============================================================================
# INFRASTRUCTURE & MONITORING - REPLACE WITH REAL CREDENTIALS
# =============================================================================

# DNSimple
DNSIMPLE_API_KEY={secrets['DNSIMPLE_API_KEY']}
DNSIMPLE_ACCOUNT_ID={secrets['DNSIMPLE_ACCOUNT_ID']}

# Docker Hub
DOCKER_PAT={secrets['DOCKER_PAT']}

# Monitoring
GRAFANA_ADMIN_PASSWORD={secrets['GRAFANA_ADMIN_PASSWORD']}

# =============================================================================
# SECURITY (GENERATED SECURELY)
# =============================================================================

# JWT & API Security
JWT_SECRET={secrets['JWT_SECRET']}
API_SECRET_KEY={secrets['API_SECRET_KEY']}

# =============================================================================
# SERVICE CONFIGURATION (KUBERNETES INTERNAL)
# =============================================================================

# Service URLs (Internal Kubernetes Network)
DASHBOARD_ORIGIN=http://agno-coordinator:8080
GITHUB_MCP_URL=http://mcp-github:8080
CONTEXT_MCP_URL=http://mcp-context:8080
RESEARCH_MCP_URL=http://mcp-research:8080
BUSINESS_MCP_URL=http://mcp-business:8080

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable production features
ENABLE_MONITORING=true
ENABLE_LOGGING=true
ENABLE_CACHING=true
ENABLE_SSL=true

# Disable development features
DEBUG=false
ENABLE_SWAGGER=false

# =============================================================================
# PERFORMANCE & SCALING
# =============================================================================

# Resource Limits
MAX_WORKERS=4
MAX_REQUESTS=1000

# Cache Settings
CACHE_TTL=3600
REDIS_CACHE_DB=1

# Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
REDIS_POOL_SIZE=20
"""
    
    return template

def main():
    """Main function to generate and save secure production secrets"""
    print("🔐 Generating secure production secrets...")
    
    # Generate secure secrets
    secrets_map = generate_production_secrets()
    
    # Create secure environment file
    env_content = create_secrets_template(secrets_map)
    
    # Write to .env.production.secure
    output_path = Path(".env.production.secure")
    with open(output_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Secure environment file generated: {output_path}")
    print("\n🚨 IMPORTANT NEXT STEPS:")
    print("1. Replace 'REPLACE_WITH_REAL_*' values with actual API keys from providers")
    print("2. Update database URLs with real Neon/Redis Cloud endpoints") 
    print("3. Test all API key connectivity before deployment")
    print("4. Never commit this file to version control")
    print("5. Use Kubernetes secrets for deployment")
    
    # Create a checklist file for tracking API key replacement
    checklist_content = """# Production Secrets Replacement Checklist

## CRITICAL - MUST REPLACE BEFORE DEPLOYMENT:
- [ ] OPENAI_API_KEY - Get from OpenAI platform
- [ ] ANTHROPIC_API_KEY - Get from Anthropic console
- [ ] QDRANT_API_KEY - Get from Qdrant Cloud dashboard
- [ ] REDIS_URL - Get from Redis Cloud console
- [ ] POSTGRES_URL - Get from Neon console

## HIGH PRIORITY - BUSINESS INTEGRATIONS:
- [ ] HUBSPOT_API_KEY - Get from HubSpot developer settings
- [ ] GONG_ACCESS_KEY - Get from Gong admin settings
- [ ] SALESFORCE credentials - Get from Salesforce org
- [ ] SLACK tokens - Get from Slack app settings
- [ ] GITHUB_APP credentials - Create GitHub App

## MEDIUM PRIORITY - RESEARCH & MONITORING:
- [ ] SERPAPI_API_KEY - Get from SerpApi account
- [ ] TAVILY_API_KEY - Get from Tavily account  
- [ ] DNSIMPLE_API_KEY - Get from DNSimple account
- [ ] DOCKER_PAT - Generate from Docker Hub

## VALIDATION REQUIRED:
- [ ] Test all database connections
- [ ] Validate all API key permissions
- [ ] Verify service-to-service connectivity
- [ ] Test health check endpoints

## SECURITY VERIFICATION:
- [ ] Ensure no secrets in git history
- [ ] Validate Kubernetes secret creation
- [ ] Test secret rotation procedures
- [ ] Verify access control policies
"""
    
    with open("PRODUCTION_SECRETS_CHECKLIST.md", 'w') as f:
        f.write(checklist_content)
    
    print("📋 Created PRODUCTION_SECRETS_CHECKLIST.md for tracking progress")

if __name__ == "__main__":
    main()
