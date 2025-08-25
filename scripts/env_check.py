#!/usr/bin/env python3
"""
Sophia AI Environment/Secrets Checker
====================================

Comprehensive verification of ALL GitHub org secrets and API keys.
Maps every possible integration and tests connectivity.
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any
import asyncio
import aiohttp

# Comprehensive list of ALL possible environment variables from GitHub org secrets
REQUIRED_SECRETS = {
    # Core Infrastructure
    "FLY_API_TOKEN": "Fly.io deployment and machine management",
    "GH_PAT_TOKEN": "GitHub repository access and automation",
    
    # Lambda Labs GPU Compute
    "LAMBDA_API_KEY": "Lambda Labs GPU instance management",
    "LAMBDA_PRIVATE_SSH_KEY": "SSH access to Lambda GPU instances",
    "LAMBDA_PUBLIC_SSH_KEY": "SSH public key for Lambda instances",
    
    # Memory Stack - Redis (L1 Cache)
    "REDIS_URL": "Redis connection URL",
    "REDIS_PASSWORD": "Redis authentication password",
    "REDIS_DATABASE_NAME": "Redis database name",
    "REDIS_API_ACCOUNTKEY": "Redis account API key",
    "REDIS_API_USERKEY": "Redis user API key",
    "REDIS_DATABASE_ENDPOINT": "Redis database endpoint",
    
    # Memory Stack - Qdrant (L2 Vector)
    "QDRANT_API_KEY": "Qdrant vector database API key",
    "QDRANT_ENDPOINT": "Qdrant service endpoint",
    "QDRANT_CLUSTER_ID": "Qdrant cluster identifier",
    "QDRANT_CLUSTER_NAME": "Qdrant cluster name",
    "QDRANT_URL": "Qdrant service URL",
    
    # Memory Stack - Neon (L3 Structured)
    "NEON_API_TOKEN": "Neon serverless Postgres API token",
    "DATABASE_URL": "Neon database connection URL",
    
    # LLM Routing and Embeddings
    "PORTKEY_API_KEY": "Portkey LLM routing and management",
    "PORTKEY_CONFIG_ID": "Portkey configuration ID",
    "OPENROUTER_API_KEY": "OpenRouter model aggregation",
    
    # Data Pipeline - Airbyte/Estuary
    "ESTUARY_ACCESS_TOKEN": "Estuary data flow platform",
    "ESTUARY_ENDPOINT": "Estuary service endpoint",
    "ESTUARY_REFRESH_TOKEN": "Estuary token refresh",
    "ESTUARY_TENANT": "Estuary tenant identifier",
    "DATA_PIPELINE_URL": "Data pipeline endpoint URL",
    
    # Workflow Automation - n8n
    "N8N_API_KEY": "n8n workflow automation API key",
    
    # Infrastructure as Code - Pulumi
    "PULUMI_ACCESS_TOKEN": "Pulumi IaC management token",
    "PULUMI_CONFIGURE_PASSPHRASE": "Pulumi config encryption",
    "PULUMI_ORG": "Pulumi organization",
    "PULUMI_IP_ADDRESS": "Pulumi service IP",
    
    # Business Integrations - Gong
    "GONG_ACCESS_KEY": "Gong call recording access key",
    "GONG_SECRET": "Gong API secret",
    "GONG_BASE_URL": "Gong service base URL",
    "GONG_CLIENT_ACCESS_KEY": "Gong client access key",
    "GONG_CLIENT_SECRET": "Gong client secret",
    
    # Business Integrations - HubSpot
    "HUBSPOT_ACCESS_TOKEN": "HubSpot CRM access token",
    "HUBSPOT_API_KEY": "HubSpot API key",
    "HUBSPOT_CLIENT_SECRET": "HubSpot client secret",
    
    # Business Integrations - Slack
    "SLACK_APP_TOKEN": "Slack app token",
    "SLACK_APP_TOKEN_2": "Slack secondary app token",
    "SLACK_BOT_TOKEN": "Slack bot token",
    "SLACK_CLIENT_ID": "Slack client ID",
    "SLACK_CLIENT_SECRET": "Slack client secret", 
    "SLACK_REFRESH_TOKEN": "Slack refresh token",
    "SLACK_SIGNING_SECRET": "Slack signing secret",
    "SLACK_SOCKET_TOKEN": "Slack socket token",
    
    # Business Integrations - Notion
    "NOTION_API_KEY": "Notion workspace API key",
    "NOTION_WORKSPACE_ID": "Notion workspace identifier",
    
    # Project Management
    "LINEAR_API_KEY": "Linear project management API",
    "LOOKER_CLIENT_ID": "Looker BI client ID",
    "LOOKER_CLIENT_SECRET": "Looker BI client secret", 
    "ASANA_API_TOKEN": "Asana project management token",
    
    # Web Research APIs
    "TAVILY_API_KEY": "Tavily web research API",
    "SERPER_API_KEY": "Serper Google search API",
    "EXA_API_KEY": "Exa semantic search API",
    "BRAVE_API_KEY": "Brave search API",
    "PERPLEXITY_API_KEY": "Perplexity AI search API",
    "BROWSER_USE_API_KEY": "Browser automation API",
    "BRIGHTDATA_API_KEY": "BrightData web scraping",
    "PHANTOMBUSTER_API_KEY": "PhantomBuster automation",
    "RESEMBLE_API_KEY": "Resemble AI voice synthesis",
    "STREAMING_ENDPOINT": "Streaming service endpoint",
    "SYNTHESIS_ENDPOINT": "Voice synthesis endpoint",
    
    # LLM Provider APIs
    "OPENAI_API_KEY": "OpenAI GPT models",
    "ANTHROPIC_API_KEY": "Anthropic Claude models",
    "DEEPSEEK_API_KEY": "DeepSeek coding models",
    "GROQ_API_KEY": "Groq high-speed inference",
    "MISTRAL_API_KEY": "Mistral AI models",
    "COHERE_API_KEY": "Cohere language models",
    "CODESTRAL_API_KEY": "Codestral coding models",
    "LLAMA_API_KEY": "Meta Llama models",
    "QWEN_API_KEY": "Qwen language models",
    "TOGETHERAI_API_KEY": "Together AI models",
    "VENICE_AI_API_KEY": "Venice AI models",
    "XAI_API_KEY": "xAI Grok models",
    "RECRAFT_API_KEY": "Recraft AI models",
    "SLIDESPEAK_API_KEY": "SlideSpeak presentation AI",
    "MUREKA_API_KEY": "Mureka AI models",
    "MEM0_API_KEY": "Mem0 memory management",
    "PATRONUS_API_KEY": "Patronus AI evaluation",
    "CONTINUE_API_KEY": "Continue AI coding",
    
    # GitHub Integration
    "GH_USERNAME": "GitHub username",
    "GITHUB_APP_ID": "GitHub app identifier",
    "GITHUB_INSTALLATION_ID": "GitHub installation ID",
    "GITHUB_PRIVATE_KEY": "GitHub app private key",
    
    # Docker Registry
    "DOCKERHUB_USERNAME": "Docker Hub username",
    "DOCKERHUB_PERSONAL_ACCESS_TOKEN": "Docker Hub access token",
    "DOCKER_TOKEN": "Docker registry token",
    "DOCKER_USER_NAME": "Docker username",
    
    # Additional Infrastructure
    "DNSIMPLE_ACCOUNT_ID": "DNSimple DNS management",
    "DNSIMPLE_API_KEY": "DNSimple API key",
    "RAILWAY_TOKEN": "Railway deployment token",
    "NORTHFLANK_API_TOKEN": "Northflank container platform",
    "TERRAFORM_API_TOKEN": "Terraform infrastructure",
    "KONG_ACCESS_TOKEN": "Kong API gateway",
    "KUBERNETES_CONTEXT": "Kubernetes cluster context",
    "KUBERNETES_NAMESPACE": "Kubernetes namespace",
    
    # AI/ML Platform APIs
    "LANGCHAIN_API_KEY": "LangChain framework",
    "LANGSMITH_API_KEY": "LangSmith tracing",
    "LANGGRAPH_API_KEY": "LangGraph workflows",
    "PRISMA_API_KEY": "Prisma database toolkit",
    "WEAVIATE_API_KEY": "Weaviate vector database",
    "REPLICATE_API_TOKEN": "Replicate model hosting",
    "STABILITY_API_KEY": "Stability AI models",
    "ELEVEN_LABS_API_KEY": "ElevenLabs voice synthesis",
    "EDEN_API_KEY": "Eden AI aggregation",
    "APIFY_API_TOKEN": "Apify web scraping",
    "PIPEDREAM_API_KEY": "Pipedream workflow automation",
    
    # Additional Configurations
    "SOPHIA_AI_TOKEN": "Sophia AI internal token",
    "API_DOMAIN": "API service domain",
    "APP_DOMAIN": "Application domain", 
    "BACKEND_URL": "Backend service URL",
    "DEPLOYMENT_KEY_2025": "2025 deployment key",
    "SOURCEGRAPH_API_TOKEN": "Sourcegraph code search",
    "FIGMA_PROJECT_ID": "Figma design project",
    "NGROK_AUTHTOKEN": "ngrok tunnel authentication",
    "NPM_API_TOKEN": "npm registry token",
    "BACKUP_ENCRYPTION_KEY": "Backup encryption key",
    "JWT_SECRET": "JWT token secret",
    "API_SECRET_KEY": "API authentication secret"
}

class EnvironmentAuditor:
    def __init__(self):
        self.found_secrets = {}
        self.missing_secrets = []
        self.connectivity_results = {}
        self.total_secrets = len(REQUIRED_SECRETS)
    
    def audit_environment(self) -> Dict[str, Any]:
        """Audit all environment variables and secrets"""
        print(f"🔍 Auditing {self.total_secrets} potential secrets...")
        
        for key, description in REQUIRED_SECRETS.items():
            value = os.getenv(key)
            if value:
                # Don't log actual secret values, just confirm existence
                self.found_secrets[key] = {
                    "description": description,
                    "length": len(value),
                    "configured": True
                }
                print(f"✅ {key}: {len(value)} chars - {description}")
            else:
                self.missing_secrets.append(key)
                print(f"❌ {key}: MISSING - {description}")
        
        coverage = (len(self.found_secrets) / self.total_secrets) * 100
        print(f"\n📊 SECRET COVERAGE: {len(self.found_secrets)}/{self.total_secrets} ({coverage:.1f}%)")
        
        return {
            "total_secrets": self.total_secrets,
            "found_count": len(self.found_secrets),
            "missing_count": len(self.missing_secrets),
            "coverage_percentage": coverage,
            "found_secrets": self.found_secrets,
            "missing_secrets": self.missing_secrets,
            "audit_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to all configured services"""
        print("\n🧪 Testing connectivity to configured services...")
        
        # Test Redis if configured
        if "REDIS_URL" in self.found_secrets:
            try:
                import redis.asyncio as redis
                client = redis.from_url(os.getenv("REDIS_URL"))
                await client.ping()
                self.connectivity_results["redis"] = "✅ Connected"
                await client.close()
            except Exception as e:
                self.connectivity_results["redis"] = f"❌ Failed: {e}"
        
        # Test Qdrant if configured
        if "QDRANT_URL" in self.found_secrets and "QDRANT_API_KEY" in self.found_secrets:
            try:
                from qdrant_client import QdrantClient
                client = QdrantClient(
                    url=os.getenv("QDRANT_URL"),
                    api_key=os.getenv("QDRANT_API_KEY")
                )
                collections = client.get_collections()
                self.connectivity_results["qdrant"] = f"✅ Connected ({len(collections.collections)} collections)"
            except Exception as e:
                self.connectivity_results["qdrant"] = f"❌ Failed: {e}"
        
        # Test Neon if configured
        if "DATABASE_URL" in self.found_secrets:
            try:
                import asyncpg
                conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
                await conn.fetchval("SELECT version()")
                await conn.close()
                self.connectivity_results["neon"] = "✅ Connected (PostgreSQL)"
            except Exception as e:
                self.connectivity_results["neon"] = f"❌ Failed: {e}"
        
        # Test Portkey if configured
        if "PORTKEY_API_KEY" in self.found_secrets:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('PORTKEY_API_KEY')}"}
                    async with session.get("https://api.portkey.ai/v1/models", headers=headers) as response:
                        if response.status == 200:
                            self.connectivity_results["portkey"] = "✅ Connected"
                        else:
                            self.connectivity_results["portkey"] = f"❌ HTTP {response.status}"
            except Exception as e:
                self.connectivity_results["portkey"] = f"❌ Failed: {e}"
        
        # Test OpenRouter if configured  
        if "OPENROUTER_API_KEY" in self.found_secrets:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
                    async with session.get("https://openrouter.ai/api/v1/models", headers=headers) as response:
                        if response.status == 200:
                            self.connectivity_results["openrouter"] = "✅ Connected"
                        else:
                            self.connectivity_results["openrouter"] = f"❌ HTTP {response.status}"
            except Exception as e:
                self.connectivity_results["openrouter"] = f"❌ Failed: {e}"
        
        # Test Lambda Labs connectivity
        if "LAMBDA_API_KEY" in self.found_secrets:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {os.getenv('LAMBDA_API_KEY')}"}
                    async with session.get("https://cloud.lambdalabs.com/api/v1/instances", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            instances = len(data.get("data", []))
                            self.connectivity_results["lambda"] = f"✅ Connected ({instances} instances)"
                        else:
                            self.connectivity_results["lambda"] = f"❌ HTTP {response.status}"
            except Exception as e:
                self.connectivity_results["lambda"] = f"❌ Failed: {e}"
        
        print("\n🔗 CONNECTIVITY RESULTS:")
        for service, status in self.connectivity_results.items():
            print(f"  {service}: {status}")
        
        return self.connectivity_results

def generate_env_file():
    """Generate .env file from all available secrets"""
    print("\n📝 Generating comprehensive .env file...")
    
    env_content = "# Sophia AI Comprehensive Environment Configuration\n"
    env_content += f"# Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
    
    for key, description in REQUIRED_SECRETS.items():
        value = os.getenv(key)
        if value:
            env_content += f"# {description}\n"
            env_content += f"{key}={value}\n\n"
        else:
            env_content += f"# {description} - MISSING\n"
            env_content += f"# {key}=\n\n"
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(f"✅ Generated .env file with {len([k for k in REQUIRED_SECRETS.keys() if os.getenv(k)])} configured secrets")

async def main():
    """Main environment audit execution"""
    print("🚀 SOPHIA AI ENVIRONMENT/SECRETS TOTAL DOMINATION")
    print("=" * 60)
    
    # Initialize auditor
    auditor = EnvironmentAuditor()
    
    # Audit environment
    audit_results = auditor.audit_environment()
    
    # Test connectivity
    connectivity_results = await auditor.test_connectivity()
    
    # Generate .env file
    generate_env_file()
    
    # Create comprehensive report
    report = {
        "execution_id": f"env_audit_{int(datetime.now().timestamp())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_results": audit_results,
        "connectivity_tests": connectivity_results,
        "recommendations": []
    }
    
    # Add recommendations based on findings
    if audit_results["coverage_percentage"] < 50:
        report["recommendations"].append("CRITICAL: Less than 50% of secrets configured")
    if audit_results["coverage_percentage"] < 80:
        report["recommendations"].append("WARNING: Missing key integrations")
    if len(connectivity_results) == 0:
        report["recommendations"].append("ERROR: No connectivity tests possible")
    
    # Save report
    with open("proofs/env_audit.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n📋 Environment audit saved to proofs/env_audit.json")
    
    # Final summary
    print("\n🎯 ENVIRONMENT AUDIT SUMMARY:")
    print(f"  📊 Secrets Found: {audit_results['found_count']}/{audit_results['total_secrets']}")
    print(f"  📈 Coverage: {audit_results['coverage_percentage']:.1f}%")
    print(f"  🔗 Connectivity Tests: {len(connectivity_results)}")
    print(f"  ✅ Services Working: {len([r for r in connectivity_results.values() if '✅' in r])}")
    
    if audit_results['coverage_percentage'] >= 80:
        print("  🎉 ENVIRONMENT READY FOR PHASE 1 BLITZ!")
    elif audit_results['coverage_percentage'] >= 50:
        print("  ⚠️ PARTIAL READINESS - Some integrations will be limited")
    else:
        print("  🚨 CRITICAL - Insufficient secrets for comprehensive setup")
    
    return audit_results['coverage_percentage'] >= 50

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
