# 🔐 Secrets Management Guide

## Overview
This guide documents the proper handling of secrets, API keys, and sensitive configuration for the Sophia AI Intelligence platform.

## ⚠️ Critical Security Rules

1. **NEVER commit secrets to the repository**
2. **NEVER use hardcoded fallback values for API keys**
3. **ALWAYS use environment variables for sensitive data**
4. **ALWAYS validate required secrets at startup**

## Environment Variables Setup

### Required Variables

All services require these environment variables to be set. The application will fail to start if they are missing.

#### Core Database
```bash
# PostgreSQL (Neon)
NEON_DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sophia
POSTGRES_USER=sophia
POSTGRES_PASSWORD=<secure-password>

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=<secure-password-if-enabled>
```

#### Vector Database
```bash
# Weaviate (REQUIRED - no defaults)
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=<your-api-key>

# Qdrant (optional)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=<your-api-key>
```

#### LLM Providers
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Other providers
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...
```

#### Portkey Virtual Keys
```bash
# For secure multi-provider routing
PORTKEY_API_KEY=<your-portkey-api-key>
PORTKEY_VK_OPENAI=vk_...
PORTKEY_VK_DEEPSEEK=vk_...
PORTKEY_VK_QWEN=vk_...
PORTKEY_VK_GROK=vk_...
PORTKEY_VK_GROQ=vk_...
PORTKEY_VK_ANTHROPIC=vk_...
PORTKEY_VK_PERPLEXITY=vk_...
PORTKEY_VK_MISTRAL=vk_...
PORTKEY_VK_HUGGINGFACE=vk_...
```

## Local Development Setup

### 1. Create `.env.local` file
```bash
cp .env.example .env.local
```

### 2. Edit `.env.local` with your secrets
```bash
# Edit with your preferred editor
nano .env.local
```

### 3. Verify `.env.local` is gitignored
```bash
grep ".env.local" .gitignore
# Should output: .env.local
```

### 4. Source environment variables
```bash
# For bash/zsh
source .env.local

# Or use direnv for automatic loading
direnv allow .
```

## Production Deployment

### Docker Secrets
```bash
# Create secrets
docker secret create weaviate_api_key ./weaviate_key.txt
docker secret create openai_api_key ./openai_key.txt

# Reference in docker-compose.yml
services:
  mcp-context:
    secrets:
      - weaviate_api_key
      - openai_api_key
    environment:
      WEAVIATE_API_KEY_FILE: /run/secrets/weaviate_api_key
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key
```

### Kubernetes Secrets
```bash
# Create secret
kubectl create secret generic sophia-secrets \
  --from-literal=WEAVIATE_API_KEY='your-key' \
  --from-literal=OPENAI_API_KEY='sk-...'

# Reference in deployment
env:
  - name: WEAVIATE_API_KEY
    valueFrom:
      secretKeyRef:
        name: sophia-secrets
        key: WEAVIATE_API_KEY
```

### Cloud Provider Secret Managers

#### AWS Secrets Manager
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('sophia/production/api-keys')
WEAVIATE_API_KEY = secrets['WEAVIATE_API_KEY']
```

#### Google Secret Manager
```python
from google.cloud import secretmanager

def get_secret(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
WEAVIATE_API_KEY = get_secret("sophia-project", "weaviate-api-key")
```

#### Azure Key Vault
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_secret(vault_url, secret_name):
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# Usage
WEAVIATE_API_KEY = get_secret("https://sophia.vault.azure.net/", "weaviate-api-key")
```

## CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
env:
  WEAVIATE_API_KEY: ${{ secrets.WEAVIATE_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### GitLab CI
```yaml
# .gitlab-ci.yml
variables:
  WEAVIATE_API_KEY: ${CI_WEAVIATE_API_KEY}
  OPENAI_API_KEY: ${CI_OPENAI_API_KEY}
```

## Security Best Practices

### 1. Rotation Policy
- Rotate API keys every 90 days
- Use versioned secrets for zero-downtime rotation
- Log key usage for audit trails

### 2. Access Control
- Use least privilege principle
- Separate keys for dev/staging/production
- Implement key-level rate limiting

### 3. Monitoring
- Alert on unauthorized access attempts
- Monitor for exposed keys in logs
- Use secret scanning tools in CI

### 4. Secret Scanning
Add pre-commit hooks to prevent accidental commits:

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 5. Emergency Response
If a secret is exposed:
1. **Immediately rotate the compromised key**
2. **Audit access logs for unauthorized usage**
3. **Update all services with new key**
4. **Document incident for post-mortem**

## Validation Script

Use this script to validate all required environment variables are set:

```python
#!/usr/bin/env python3
"""validate_secrets.py - Ensure all required secrets are configured"""

import os
import sys

REQUIRED_SECRETS = [
    'WEAVIATE_URL',
    'WEAVIATE_API_KEY',
    'OPENAI_API_KEY',
    'NEON_DATABASE_URL',
]

missing = []
for secret in REQUIRED_SECRETS:
    if not os.getenv(secret):
        missing.append(secret)
        
if missing:
    print("❌ Missing required environment variables:")
    for var in missing:
        print(f"  - {var}")
    print("\nPlease set these in your .env.local file or environment")
    sys.exit(1)
else:
    print("✅ All required secrets are configured")
    sys.exit(0)
```

## Troubleshooting

### Service fails with "Missing required environment variables"
- Ensure `.env.local` exists and contains all required variables
- Source the environment file: `source .env.local`
- Check variables are exported: `echo $WEAVIATE_API_KEY`

### Docker container can't find secrets
- Verify secrets are created: `docker secret ls`
- Check mount paths in docker-compose.yml
- Ensure service has permission to read secrets

### Kubernetes pod fails to start
- Check secret exists: `kubectl get secrets`
- Verify secret keys match deployment spec
- Check pod logs: `kubectl logs <pod-name>`

## References
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12 Factor App - Config](https://12factor.net/config)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)