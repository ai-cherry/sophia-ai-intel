# Sophia AI - Production Environment Setup

## Overview

This document provides comprehensive instructions for configuring and deploying Sophia AI in a production environment with secure secrets management.

## 🔐 Environment Configuration

### Production Environment File

The `.env.production` file contains all required environment variables for production deployment. This file includes:

- **Database Connections**: PostgreSQL, Redis, Qdrant
- **AI Service API Keys**: OpenAI, Anthropic, Grok, and others
- **Business Integrations**: HubSpot, Salesforce, Gong, Slack
- **Infrastructure**: Lambda Labs, DNSimple, GitHub
- **Security**: JWT secrets, API keys, encryption keys

### Secure Secrets Generation

Use the automated script to generate cryptographically secure secrets:

```bash
# Generate secure secrets with SSH keys
./scripts/generate-secure-secrets.sh

# This creates:
# - .env.production.secure (with generated secrets)
# - ssh_keys/ directory (with Lambda Labs and GitHub SSH keys)
```

## 🛡️ Secrets Management Implementation

### Architecture

The secrets management follows this hierarchy:

1. **GitHub Organization Secrets** (Deployment-time)
   - PULUMI_ACCESS_TOKEN
   - LAMBDA_API_KEY
   - DOCKERHUB_TOKEN
   - DNSIMPLE_API_TOKEN

2. **Pulumi ESC** (Runtime)
   - API keys that rotate frequently
   - Database credentials
   - Service-specific configurations

3. **Kubernetes Secrets** (Application)
   - Automatically injected into pods
   - Environment variables for services

### Implementation Steps

#### 1. GitHub Organization Secrets Setup

Navigate to your GitHub organization settings and add these secrets:

```yaml
# Infrastructure Secrets
PULUMI_ACCESS_TOKEN: "your-pulumi-token"
LAMBDA_API_KEY: "your-lambda-labs-api-key"
DOCKERHUB_TOKEN: "your-dockerhub-token"
DNSIMPLE_API_TOKEN: "your-dnsimple-token"
```

#### 2. Pulumi ESC Environment Setup

Create a Pulumi ESC environment file:

```yaml
# environments/production.yaml
values:
  # Database connections
  database:
    url:
      fn::secret: ${neon.connectionString}

  # AI Service API Keys
  openai:
    key:
      fn::secret: ${encrypted_openai_key}

  # Business Integrations
  hubspot:
    accessToken:
      fn::secret: ${encrypted_hubspot_token}
```

#### 3. Kubernetes Secrets Creation

The automated script creates all necessary Kubernetes secrets:

```bash
# Create all secrets from environment variables
./k8s-deploy/scripts/create-all-secrets.sh
```

## 🚀 Deployment Process

### Automated Production Deployment

Use the comprehensive deployment script:

```bash
# Deploy to Kubernetes (default)
./scripts/deploy-production-secure.sh

# Deploy to Docker Compose
./scripts/deploy-production-secure.sh --docker

# Deploy to Kubernetes explicitly
./scripts/deploy-production-secure.sh --kubernetes
```

### Manual Deployment Steps

If you prefer manual deployment:

1. **Generate Secrets**
   ```bash
   ./scripts/generate-secure-secrets.sh
   ```

2. **Validate Configuration**
   ```bash
   ./scripts/env-production-validation.sh
   ```

3. **Create Kubernetes Secrets**
   ```bash
   ./k8s-deploy/scripts/create-all-secrets.sh
   ```

4. **Deploy Services**
   ```bash
   kubectl apply -f k8s-deploy/manifests/
   ```

## 🔍 Environment Validation

### Automated Validation

Run comprehensive environment validation:

```bash
# Validate production environment
./scripts/env-production-validation.sh

# This checks:
# - All required API keys are configured
# - SSH keys are valid
# - URLs and connection strings are properly formatted
# - Production settings are correctly configured
```

### Manual Validation Checklist

- [ ] All API keys and secrets configured
- [ ] Database connectivity verified
- [ ] AI services validated
- [ ] Lambda Labs SSH access confirmed
- [ ] Domain DNS configured
- [ ] SSL certificates ready
- [ ] Monitoring stack operational
- [ ] Backup strategy implemented

## 🏗️ Infrastructure Configuration

### Lambda Labs Setup

1. **SSH Key Configuration**
   - Add the generated Lambda Labs public SSH key to your Lambda Labs account
   - Verify SSH connectivity: `ssh -i ssh_keys/lambda-labs ubuntu@your-instance`

2. **Instance Requirements**
   - Ubuntu 22.04 LTS
   - At least 32GB RAM
   - 500GB SSD storage
   - GPU access (GH200 recommended)

### DNSimple Configuration

1. **Domain Setup**
   - Point `www.sophia-intel.ai` to your Lambda Labs instance
   - Configure API domain: `api.sophia-intel.ai`

2. **SSL Certificate Automation**
   - Let's Encrypt certificates are automatically provisioned
   - Certificate renewal is handled by cert-manager

## 📊 Monitoring & Logging

### Production Monitoring Stack

- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping
- **DCGM Exporter**: GPU monitoring

### Access URLs

- **Grafana**: http://your-server:3001
- **Prometheus**: http://your-server:9090
- **Loki**: http://your-server:3100

## 🔄 Secrets Rotation

### Automated Rotation

Set up automated secret rotation:

```bash
# Rotate a specific secret
pulumi config set --secret openai-key "new-key-value"

# Rotate all secrets (quarterly)
# 1. Generate new secrets
./scripts/generate-secure-secrets.sh

# 2. Update Pulumi ESC
pulumi up

# 3. Redeploy services
./scripts/deploy-production-secure.sh
```

### Manual Rotation Process

1. Generate new secrets with the generation script
2. Update secrets in GitHub/Pulumi ESC
3. Update Kubernetes secrets
4. Restart affected services
5. Verify functionality
6. Remove old secrets

## 🛠️ Troubleshooting

### Common Issues

1. **Secret Not Found**
   ```bash
   # Check if secret exists in Kubernetes
   kubectl get secrets -n sophia

   # Recreate secrets
   ./k8s-deploy/scripts/create-all-secrets.sh
   ```

2. **SSH Connection Failed**
   ```bash
   # Verify SSH key
   ssh-keygen -l -f ssh_keys/lambda-labs

   # Test connection
   ssh -i ssh_keys/lambda-labs ubuntu@your-instance
   ```

3. **Environment Validation Failed**
   ```bash
   # Check environment file
   cat .env.production | grep -v '^#' | grep '<YOUR_'

   # Regenerate secrets
   ./scripts/generate-secure-secrets.sh
   ```

### Health Checks

- **Service Health**: Check pod status with `kubectl get pods -n sophia`
- **Application Health**: Visit https://www.sophia-intel.ai/health
- **Database Health**: Verify connection strings and connectivity

## 🔒 Security Best Practices

### Secret Storage

- Never commit secrets to version control
- Use separate secrets for each environment
- Rotate secrets regularly (90 days maximum)
- Use encryption at rest and in transit

### Access Control

- Limit SSH access to specific IP ranges
- Use role-based access control (RBAC) for Kubernetes
- Implement audit logging for all secret access
- Regular security assessments and penetration testing

### Compliance

- GDPR compliance for user data
- SOC 2 compliance for business operations
- Regular security audits and compliance checks
- Incident response plan documentation

## 📚 Additional Resources

- [Pulumi ESC Documentation](https://www.pulumi.com/docs/esc/)
- [Kubernetes Secrets Management](https://kubernetes.io/docs/concepts/configuration/secret/)
- [GitHub Organization Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Lambda Labs API Documentation](https://cloud.lambdalabs.com/api/v1/docs)
- [DNSimple API Documentation](https://dnsimple.com/api)

## 🎯 Next Steps

1. **Complete Environment Setup**
   - Run `./scripts/generate-secure-secrets.sh`
   - Configure API keys and connection strings
   - Run `./scripts/env-production-validation.sh`

2. **Infrastructure Deployment**
   - Set up Lambda Labs instance
   - Configure DNSimple domain
   - Run `./scripts/deploy-production-secure.sh`

3. **Service Validation**
   - Test all endpoints
   - Verify monitoring dashboards
   - Set up backup procedures

4. **Production Readiness**
   - Configure alerting and notifications
   - Set up log retention policies
   - Document incident response procedures

---

**Production Environment Setup Complete** ✅

For additional support or questions, refer to the troubleshooting section or create an issue in the project repository.