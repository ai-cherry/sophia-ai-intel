#!/usr/bin/env python3
"""
Secrets Validation Script for Sophia AI Platform
Validates that all required secrets are present and properly formatted
across different deployment environments (Docker, Kubernetes, Local).
"""

import os
import sys
import re
import base64
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse
import subprocess

# Base directory for the project
BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env.production.real"
K8S_SECRETS_DIR = BASE_DIR / "k8s-deploy" / "secrets"

class SecretsValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.critical_secrets = {
            # Database
            'POSTGRES_PASSWORD', 'POSTGRES_URL', 'DATABASE_URL',
            # Authentication
            'JWT_SECRET', 'API_SECRET_KEY',
            # LLM APIs (at least one required)
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
            # Infrastructure
            'REDIS_PASSWORD', 'QDRANT_API_KEY',
        }
        
        self.all_expected_secrets = {
            # Database secrets
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'POSTGRES_URL', 'DATABASE_URL', 'NEON_DATABASE_URL', 'NEON_API_TOKEN', 'NEON_PROJECT_ID', 'NEON_BRANCH_ID',
            
            # Redis secrets  
            'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'REDIS_URL',
            'REDIS_API_ACCOUNTKEY', 'REDIS_API_USERKEY', 'REDIS_USER_KEY', 'REDIS_ACCOUNT_KEY',
            
            # Vector database
            'QDRANT_URL', 'QDRANT_HOST', 'QDRANT_API_KEY', 'QDRANT_CLUSTER_ID',
            'QDRANT_MANAGEMENT_KEY', 'QDRANT_ACCOUNT_ID', 'QDRANT_CLUSTER_API_KEY',
            
            # LLM APIs
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'COHERE_API_KEY',
            'HUGGINGFACE_API_KEY', 'DEEPSEEK_API_KEY', 'GROQ_API_KEY', 'LLAMA_API_KEY',
            'MISTRAL_API_KEY', 'OPENROUTER_API_KEY', 'PORTKEY_API_KEY', 'TOGETHERAI_API_KEY',
            'VENICE_AI_API_KEY', 'XAI_API_KEY',
            
            # Infrastructure
            'JWT_SECRET', 'API_SECRET_KEY', 'BACKUP_ENCRYPTION_KEY', 'GRAFANA_ADMIN_PASSWORD',
            'LAMBDA_API_KEY', 'LAMBDA_CLOUD_ENDPOINT', 'LAMBDA_PRIVATE_SSH_KEY', 'LAMBDA_PUBLIC_SSH_KEY',
            'DNSIMPLE_ACCOUNT_ID', 'DNSIMPLE_API_KEY', 'DOCKERHUB_USERNAME', 'DOCKERHUB_PERSONAL_ACCESS_TOKEN',
            'DOCKER_PAT',
            
            # GitHub
            'GITHUB_TOKEN', 'GITHUB_APP_ID', 'GITHUB_INSTALLATION_ID', 'GITHUB_PRIVATE_KEY', 'GH_PAT_TOKEN',
            
            # Research APIs
            'TAVILY_API_KEY', 'SERPAPI_API_KEY', 'PERPLEXITY_API_KEY', 'VOYAGE_AI_API_KEY',
            
            # Business integrations
            'HUBSPOT_API_KEY', 'HUBSPOT_ACCESS_TOKEN', 'HUBSPOT_CLIENT_SECRET',
            'APOLLO_API_KEY', 'GONG_ACCESS_KEY', 'GONG_ACCESS_KEY_SECRET',
            'SALESFORCE_CLIENT_ID', 'SALESFORCE_CLIENT_SECRET', 'SALESFORCE_USERNAME',
            'SALESFORCE_PASSWORD', 'SALESFORCE_SECURITY_TOKEN',
            'SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_CLIENT_ID', 'SLACK_CLIENT_SECRET', 'SLACK_SIGNING_SECRET',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'USERGEMS_API_KEY', 'ZILLOW_API_KEY'
        }
    
    def log_error(self, message: str):
        """Log an error message"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message: str):
        """Log a warning message"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_info(self, message: str):
        """Log an info message"""
        print(f"ℹ️  INFO: {message}")
    
    def log_success(self, message: str):
        """Log a success message"""
        print(f"✅ SUCCESS: {message}")
    
    def load_env_file(self, env_file_path: Path) -> Dict[str, str]:
        """Load environment variables from file"""
        env_vars = {}
        
        if not env_file_path.exists():
            self.log_error(f"Environment file not found: {env_file_path}")
            return env_vars
            
        try:
            with open(env_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                        else:
                            self.log_warning(f"Malformed line {line_num} in {env_file_path}: {line}")
                            
            self.log_info(f"Loaded {len(env_vars)} environment variables from {env_file_path}")
        except Exception as e:
            self.log_error(f"Failed to load environment file {env_file_path}: {e}")
            
        return env_vars
    
    def validate_secret_format(self, key: str, value: str) -> bool:
        """Validate secret format based on key type"""
        if not value:
            return False
            
        # URL validation
        if any(url_key in key.upper() for url_key in ['URL', 'ENDPOINT']):
            try:
                result = urlparse(value)
                return all([result.scheme, result.netloc])
            except:
                return False
        
        # API Key validation patterns
        api_key_patterns = {
            'OPENAI_API_KEY': r'^sk-[a-zA-Z0-9]{48}$',
            'ANTHROPIC_API_KEY': r'^sk-ant-[a-zA-Z0-9\-_]{95,}$',
            'GITHUB_TOKEN': r'^gh[ps]_[a-zA-Z0-9]{36}$',
            'HUGGINGFACE_API_KEY': r'^hf_[a-zA-Z0-9]{37}$',
            'COHERE_API_KEY': r'^[a-zA-Z0-9\-_]{40}$',
            'GOOGLE_API_KEY': r'^AIza[a-zA-Z0-9\-_]{35}$',
        }
        
        if key in api_key_patterns:
            pattern = api_key_patterns[key]
            if not re.match(pattern, value):
                return False
        
        # Minimum length check for secrets
        if any(secret_type in key.upper() for secret_type in ['SECRET', 'KEY', 'TOKEN', 'PASSWORD']):
            if len(value) < 8:
                return False
        
        return True
    
    def validate_env_secrets(self, env_vars: Dict[str, str]) -> bool:
        """Validate environment file secrets"""
        self.log_info("Validating environment file secrets...")
        
        success = True
        
        # Check critical secrets
        missing_critical = []
        for secret in self.critical_secrets:
            if secret not in env_vars or not env_vars[secret]:
                missing_critical.append(secret)
        
        if missing_critical:
            self.log_error(f"Missing critical secrets: {', '.join(missing_critical)}")
            success = False
        else:
            self.log_success("All critical secrets are present")
        
        # Check LLM API keys (at least one should be valid)
        llm_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'COHERE_API_KEY']
        valid_llm_keys = 0
        for key in llm_keys:
            if key in env_vars and env_vars[key] and self.validate_secret_format(key, env_vars[key]):
                valid_llm_keys += 1
        
        if valid_llm_keys == 0:
            self.log_error("No valid LLM API keys found")
            success = False
        else:
            self.log_success(f"Found {valid_llm_keys} valid LLM API keys")
        
        # Validate secret formats
        format_errors = 0
        for key, value in env_vars.items():
            if key in self.all_expected_secrets:
                if not self.validate_secret_format(key, value):
                    self.log_warning(f"Invalid format for {key}")
                    format_errors += 1
        
        if format_errors > 0:
            self.log_warning(f"Found {format_errors} secrets with potentially invalid formats")
        
        return success
    
    def validate_kubernetes_secrets(self) -> bool:
        """Validate Kubernetes secret files"""
        self.log_info("Validating Kubernetes secret files...")
        
        success = True
        
        if not K8S_SECRETS_DIR.exists():
            self.log_error(f"Kubernetes secrets directory not found: {K8S_SECRETS_DIR}")
            return False
        
        expected_files = [
            'llm-secrets.yaml',
            'database-secrets.yaml', 
            'infrastructure-secrets.yaml',
            'business-secrets.yaml'
        ]
        
        for filename in expected_files:
            filepath = K8S_SECRETS_DIR / filename
            if not filepath.exists():
                self.log_error(f"Missing Kubernetes secrets file: {filepath}")
                success = False
                continue
                
            try:
                with open(filepath, 'r') as f:
                    docs = list(yaml.safe_load_all(f))
                    
                for doc in docs:
                    if doc and doc.get('kind') == 'Secret':
                        # Validate secret structure
                        if 'data' not in doc:
                            self.log_error(f"Secret in {filename} missing 'data' field")
                            success = False
                        else:
                            # Validate base64 encoding
                            for key, value in doc['data'].items():
                                try:
                                    base64.b64decode(value)
                                except:
                                    self.log_error(f"Invalid base64 encoding for {key} in {filename}")
                                    success = False
                        
                        # Validate metadata
                        if 'metadata' not in doc or 'name' not in doc['metadata']:
                            self.log_error(f"Secret in {filename} missing proper metadata")
                            success = False
                            
            except Exception as e:
                self.log_error(f"Failed to parse {filepath}: {e}")
                success = False
        
        if success:
            self.log_success("All Kubernetes secret files are valid")
        
        return success
    
    def validate_docker_compose(self) -> bool:
        """Validate docker-compose.yml environment configuration"""
        self.log_info("Validating Docker Compose configuration...")
        
        compose_file = BASE_DIR / "docker-compose.yml"
        if not compose_file.exists():
            self.log_error(f"Docker Compose file not found: {compose_file}")
            return False
        
        try:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            env_file_refs = 0
            env_var_refs = 0
            
            for service_name, service_config in services.items():
                # Check for env_file references
                if 'env_file' in service_config:
                    env_file_refs += 1
                
                # Check for environment variable references
                if 'environment' in service_config:
                    for env_var in service_config['environment']:
                        if isinstance(env_var, str) and '${' in env_var:
                            env_var_refs += 1
            
            self.log_info(f"Found {env_file_refs} services with env_file references")
            self.log_info(f"Found {env_var_refs} environment variable references")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to parse docker-compose.yml: {e}")
            return False
    
    def check_file_permissions(self) -> bool:
        """Check file permissions for secret files"""
        self.log_info("Checking file permissions...")
        
        success = True
        sensitive_files = [ENV_FILE]
        
        # Add Kubernetes secret files
        if K8S_SECRETS_DIR.exists():
            sensitive_files.extend(K8S_SECRETS_DIR.glob("*.yaml"))
        
        for file_path in sensitive_files:
            if file_path.exists():
                # Get file permissions
                stat = file_path.stat()
                permissions = oct(stat.st_mode)[-3:]
                
                # Check if file is readable by others
                if int(permissions[2]) > 0:
                    self.log_warning(f"File {file_path} is readable by others (permissions: {permissions})")
                    success = False
                else:
                    self.log_info(f"File {file_path} has secure permissions ({permissions})")
        
        return success
    
    def validate_secret_consistency(self, env_vars: Dict[str, str]) -> bool:
        """Validate consistency between related secrets"""
        self.log_info("Validating secret consistency...")
        
        success = True
        
        # Check PostgreSQL URL consistency
        if all(key in env_vars for key in ['POSTGRES_URL', 'DATABASE_URL']):
            if env_vars['POSTGRES_URL'] != env_vars['DATABASE_URL']:
                self.log_warning("POSTGRES_URL and DATABASE_URL are not identical")
        
        # Check Redis URL consistency
        redis_host = env_vars.get('REDIS_HOST', '')
        redis_port = env_vars.get('REDIS_PORT', '')
        redis_url = env_vars.get('REDIS_URL', '')
        
        if redis_host and redis_port:
            expected_url = f"redis://{redis_host}:{redis_port}"
            if redis_url and not redis_url.startswith(f"redis://{redis_host}"):
                self.log_warning(f"Redis URL inconsistent with host/port: {redis_url}")
        
        return success
    
    def run_security_checks(self, env_vars: Dict[str, str]) -> bool:
        """Run security-focused checks"""
        self.log_info("Running security checks...")
        
        success = True
        
        # Check for placeholder values
        placeholder_patterns = [
            'dummy', 'test', 'placeholder', 'replace', 'changeme',
            'example', 'sample', 'foobar', 'your-key-here'
        ]
        
        for key, value in env_vars.items():
            value_lower = value.lower()
            for pattern in placeholder_patterns:
                if pattern in value_lower:
                    self.log_error(f"Placeholder value detected in {key}: {value}")
                    success = False
        
        # Check for weak passwords/secrets
        weak_secrets = []
        for key, value in env_vars.items():
            if any(term in key.upper() for term in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                if len(value) < 16:
                    weak_secrets.append(key)
        
        if weak_secrets:
            self.log_warning(f"Potentially weak secrets (< 16 chars): {', '.join(weak_secrets)}")
        
        return success
    
    def generate_report(self) -> Dict[str, any]:
        """Generate validation report"""
        return {
            'timestamp': sys.argv[0],  # Could be improved with actual timestamp
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'status': 'PASSED' if len(self.errors) == 0 else 'FAILED'
        }
    
    def validate_all(self, env_file_path: Optional[Path] = None) -> bool:
        """Run all validation checks"""
        print("🔍 Starting comprehensive secrets validation...\n")
        
        # Use provided file or default
        env_file = env_file_path or ENV_FILE
        
        # Load environment variables
        env_vars = self.load_env_file(env_file)
        if not env_vars:
            return False
        
        # Run all validation checks
        checks = [
            ("Environment Secrets", lambda: self.validate_env_secrets(env_vars)),
            ("Kubernetes Secrets", self.validate_kubernetes_secrets),
            ("Docker Compose", self.validate_docker_compose),
            ("File Permissions", self.check_file_permissions),
            ("Secret Consistency", lambda: self.validate_secret_consistency(env_vars)),
            ("Security Checks", lambda: self.run_security_checks(env_vars))
        ]
        
        overall_success = True
        for check_name, check_func in checks:
            print(f"\n--- {check_name} ---")
            try:
                result = check_func()
                if not result:
                    overall_success = False
            except Exception as e:
                self.log_error(f"Failed to run {check_name}: {e}")
                overall_success = False
        
        # Print summary
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        if overall_success and len(self.errors) == 0:
            print("🎉 ALL VALIDATIONS PASSED!")
            print(f"Warnings: {len(self.warnings)}")
        else:
            print("💥 VALIDATION FAILED!")
            print(f"Errors: {len(self.errors)}")
            print(f"Warnings: {len(self.warnings)}")
        
        return overall_success and len(self.errors) == 0

def main():
    parser = argparse.ArgumentParser(description='Validate Sophia AI Platform secrets')
    parser.add_argument('--env-file', '-e', type=Path,
                       help='Path to environment file (default: .env.production.real)')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Generate detailed validation report')
    
    args = parser.parse_args()
    
    validator = SecretsValidator()
    
    try:
        success = validator.validate_all(args.env_file)
        
        if args.report:
            report = validator.generate_report()
            print(f"\n📊 Validation Report:")
            print(f"Status: {report['status']}")
            print(f"Errors: {report['error_count']}")
            print(f"Warnings: {report['warning_count']}")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()