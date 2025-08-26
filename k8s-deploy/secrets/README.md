# Sophia AI Kubernetes Secrets Management

This directory contains Kubernetes Secret manifests for managing sensitive configuration data securely.

## Secret Categories

### 1. Database Secrets (`database-secrets.yaml`)
- PostgreSQL/Neon database connection strings
- Redis connection details
- Qdrant vector database credentials

### 2. LLM API Secrets (`llm-secrets.yaml`)
- OpenAI, Anthropic, DeepSeek, Groq, Mistral API keys
- Together AI, Venice AI, xAI, Portkey, OpenRouter tokens

### 3. Business Integration Secrets (`business-secrets.yaml`)
- HubSpot, Salesforce, Gong, Slack integrations
- Apollo, UserGems, Zillow, Telegram credentials

### 4. Infrastructure Secrets (`infrastructure-secrets.yaml`)
- Lambda Labs, DNSimple, Docker Hub credentials
- GitHub App and PAT tokens
- Monitoring and security keys

## Usage

### Applying Secrets to Kubernetes

```bash
# Apply all secrets
kubectl apply -f k8s-deploy/secrets/

# Apply individual secret categories
kubectl apply -f k8s-deploy/secrets/database-secrets.yaml
kubectl apply -f k8s-deploy/secrets/llm-secrets.yaml
kubectl apply -f k8s-deploy/secrets/business-secrets.yaml
kubectl apply -f k8s-deploy/secrets/infrastructure-secrets.yaml
```

### Base64 Encoding

All secret values must be base64 encoded:

```bash
# Encode a secret value
echo -n "your-secret-value" | base64

# Decode a secret value
echo -n "base64-encoded-value" | base64 -d
```

### Environment Variable Mapping

Secrets are mounted as environment variables in pods:

```yaml
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: sophia-llm-secrets
      key: OPENAI_API_KEY
```

## Security Best Practices

1. **Never commit actual secret values** - only the manifest templates
2. **Use separate secrets for different environments** (dev, staging, prod)
3. **Rotate secrets regularly** - especially API keys and database passwords
4. **Limit secret access** using Kubernetes RBAC
5. **Monitor secret usage** through audit logs
6. **Use external secret management** (AWS Secrets Manager, Vault) for production

## Deployment Automation

For CI/CD pipelines, create the secrets programmatically:

```bash
#!/bin/bash
# Example: Create LLM secrets from environment variables
kubectl create secret generic sophia-llm-secrets \
  --from-literal=OPENAI_API_KEY=$OPENAI_API_KEY \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Backup and Recovery

- Regularly backup secret manifests (without sensitive data)
- Document secret rotation procedures
- Maintain inventory of all secrets and their purposes
- Test secret recovery procedures regularly

## Compliance

- Ensure secrets comply with organizational security policies
- Document data classification for each secret
- Implement proper access controls and audit trails
- Regular security assessments and penetration testing