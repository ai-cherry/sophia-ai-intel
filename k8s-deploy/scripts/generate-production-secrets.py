#!/usr/bin/env python3
"""
Production Secrets Generator for Sophia AI Platform
Generates Kubernetes secrets from real production environment variables.
This script converts .env.production.real into base64-encoded Kubernetes secrets.
"""

import os
import sys
import base64
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Base directory for the project
BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env.production.real"

class ProductionSecretsGenerator:
    def __init__(self):
        self.namespace = "sophia"
        self.app_label = "sophia-ai"
        
    def load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from .env.production.real file"""
        env_vars = {}
        
        if not ENV_FILE.exists():
            raise FileNotFoundError(f"Environment file not found: {ENV_FILE}")
            
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                        
        print(f"Loaded {len(env_vars)} environment variables")
        return env_vars
    
    def encode_base64(self, value: str) -> str:
        """Encode string to base64"""
        return base64.b64encode(value.encode('utf-8')).decode('utf-8')
    
    def create_secret_manifest(self, name: str, component: str, data: Dict[str, str]) -> Dict[str, Any]:
        """Create Kubernetes secret manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": self.namespace,
                "labels": {
                    "app": self.app_label,
                    "component": component,
                    "generated": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "type": "Opaque",
            "data": {key: self.encode_base64(value) for key, value in data.items()}
        }
    
    def generate_llm_secrets(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Generate LLM API secrets"""
        llm_keys = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
            'COHERE_API_KEY', 'HUGGINGFACE_API_KEY', 'DEEPSEEK_API_KEY',
            'GROQ_API_KEY', 'LLAMA_API_KEY', 'MISTRAL_API_KEY',
            'OPENROUTER_API_KEY', 'PORTKEY_API_KEY', 'TOGETHERAI_API_KEY',
            'VENICE_AI_API_KEY', 'XAI_API_KEY'
        ]
        
        data = {}
        for key in llm_keys:
            if key in env_vars:
                data[key] = env_vars[key]
                
        return self.create_secret_manifest("sophia-llm-secrets", "llm", data)
    
    def generate_database_secrets(self, env_vars: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate database-related secrets"""
        secrets = []
        
        # PostgreSQL secrets
        postgres_keys = [
            'DATABASE_URL', 'POSTGRES_URL', 'POSTGRES_HOST', 'POSTGRES_PORT',
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'NEON_DATABASE_URL', 'NEON_API_TOKEN', 'NEON_PROJECT_ID', 'NEON_BRANCH_ID'
        ]
        postgres_data = {key: env_vars[key] for key in postgres_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-database-secrets", "database", postgres_data))
        
        # Redis secrets
        redis_keys = [
            'REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD',
            'REDIS_API_ACCOUNTKEY', 'REDIS_API_USERKEY', 'REDIS_USER_KEY', 'REDIS_ACCOUNT_KEY'
        ]
        redis_data = {key: env_vars[key] for key in redis_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-redis-secrets", "redis", redis_data))
        
        # Vector database secrets
        qdrant_keys = [
            'QDRANT_URL', 'QDRANT_HOST', 'QDRANT_API_KEY', 'QDRANT_CLUSTER_ID',
            'QDRANT_MANAGEMENT_KEY', 'QDRANT_ACCOUNT_ID', 'QDRANT_CLUSTER_API_KEY'
        ]
        qdrant_data = {key: env_vars[key] for key in qdrant_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-vector-secrets", "vector-db", qdrant_data))
        
        return secrets
    
    def generate_infrastructure_secrets(self, env_vars: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate infrastructure secrets"""
        secrets = []
        
        # Main infrastructure secrets
        infra_keys = [
            'JWT_SECRET', 'API_SECRET_KEY', 'BACKUP_ENCRYPTION_KEY',
            'GRAFANA_ADMIN_PASSWORD', 'LAMBDA_API_KEY', 'LAMBDA_CLOUD_ENDPOINT',
            'LAMBDA_PRIVATE_SSH_KEY', 'LAMBDA_PUBLIC_SSH_KEY',
            'DNSIMPLE_ACCOUNT_ID', 'DNSIMPLE_API_KEY',
            'DOCKERHUB_USERNAME', 'DOCKERHUB_PERSONAL_ACCESS_TOKEN', 'DOCKER_PAT'
        ]
        infra_data = {key: env_vars[key] for key in infra_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-infrastructure-secrets", "infrastructure", infra_data))
        
        # GitHub secrets
        github_keys = [
            'GITHUB_TOKEN', 'GITHUB_APP_ID', 'GITHUB_INSTALLATION_ID',
            'GITHUB_PRIVATE_KEY', 'GH_PAT_TOKEN'
        ]
        github_data = {key: env_vars[key] for key in github_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-github-secrets", "github", github_data))
        
        # Research API secrets
        research_keys = [
            'TAVILY_API_KEY', 'SERPAPI_API_KEY', 'PERPLEXITY_API_KEY', 'VOYAGE_AI_API_KEY'
        ]
        research_data = {key: env_vars[key] for key in research_keys if key in env_vars}
        secrets.append(self.create_secret_manifest("sophia-research-secrets", "research", research_data))
        
        return secrets
    
    def generate_business_secrets(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Generate business integration secrets"""
        business_keys = [
            'HUBSPOT_API_KEY', 'HUBSPOT_ACCESS_TOKEN', 'HUBSPOT_CLIENT_SECRET',
            'APOLLO_API_KEY', 'GONG_ACCESS_KEY', 'GONG_ACCESS_KEY_SECRET',
            'SALESFORCE_CLIENT_ID', 'SALESFORCE_CLIENT_SECRET', 'SALESFORCE_USERNAME',
            'SALESFORCE_PASSWORD', 'SALESFORCE_SECURITY_TOKEN',
            'SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_CLIENT_ID',
            'SLACK_CLIENT_SECRET', 'SLACK_SIGNING_SECRET',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
            'USERGEMS_API_KEY', 'ZILLOW_API_KEY'
        ]
        
        data = {key: env_vars[key] for key in business_keys if key in env_vars}
        return self.create_secret_manifest("sophia-business-secrets", "business-integrations", data)
    
    def write_secrets_to_files(self, secrets_map: Dict[str, Any], output_dir: Path):
        """Write secrets to YAML files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, secrets in secrets_map.items():
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                if isinstance(secrets, list):
                    # Multiple secrets in one file
                    for i, secret in enumerate(secrets):
                        yaml.dump(secret, f, default_flow_style=False, sort_keys=False)
                        if i < len(secrets) - 1:
                            f.write('---\n')
                else:
                    # Single secret
                    yaml.dump(secrets, f, default_flow_style=False, sort_keys=False)
            
            print(f"Generated: {filepath}")
    
    def validate_critical_secrets(self, env_vars: Dict[str, str]) -> bool:
        """Validate that critical secrets are present"""
        critical_secrets = [
            'POSTGRES_PASSWORD', 'JWT_SECRET', 'OPENAI_API_KEY',
            'REDIS_PASSWORD', 'QDRANT_API_KEY'
        ]
        
        missing = []
        for secret in critical_secrets:
            if secret not in env_vars or not env_vars[secret]:
                missing.append(secret)
        
        if missing:
            print(f"ERROR: Missing critical secrets: {', '.join(missing)}")
            return False
        
        print("✓ All critical secrets are present")
        return True
    
    def generate_all_secrets(self, output_dir: Path = None):
        """Generate all production secrets"""
        if output_dir is None:
            output_dir = BASE_DIR / "k8s-deploy" / "secrets"
        
        print("🔐 Generating production secrets from real environment variables...")
        
        # Load environment variables
        env_vars = self.load_env_vars()
        
        # Validate critical secrets
        if not self.validate_critical_secrets(env_vars):
            sys.exit(1)
        
        # Generate all secret manifests
        secrets_map = {
            "llm-secrets.yaml": self.generate_llm_secrets(env_vars),
            "database-secrets.yaml": self.generate_database_secrets(env_vars),
            "infrastructure-secrets.yaml": self.generate_infrastructure_secrets(env_vars),
            "business-secrets.yaml": self.generate_business_secrets(env_vars)
        }
        
        # Write secrets to files
        self.write_secrets_to_files(secrets_map, output_dir)
        
        print(f"\n✅ Successfully generated all production secrets in: {output_dir}")
        print("\n⚠️  SECURITY WARNING:")
        print("- These files contain real production secrets")
        print("- Ensure proper file permissions (600 or 640)")
        print("- Do not commit these files to version control")
        print("- Use proper secret management in production")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Generate Kubernetes secrets from production environment variables')
    parser.add_argument('--output-dir', '-o', type=Path,
                       help='Output directory for secrets files (default: k8s-deploy/secrets)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate secrets without generating files')
    
    args = parser.parse_args()
    
    generator = ProductionSecretsGenerator()
    
    if args.validate_only:
        env_vars = generator.load_env_vars()
        if generator.validate_critical_secrets(env_vars):
            print("✅ Validation passed")
            sys.exit(0)
        else:
            print("❌ Validation failed")
            sys.exit(1)
    
    try:
        generator.generate_all_secrets(args.output_dir)
    except Exception as e:
        print(f"❌ Error generating secrets: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()