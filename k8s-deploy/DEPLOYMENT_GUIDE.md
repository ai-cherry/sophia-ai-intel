# Sophia AI Kubernetes Deployment Guide

## Overview
This guide covers the deployment of Sophia AI to Lambda Labs GPU infrastructure using Kubernetes (K3s).

**Target Server**: Lambda Labs GPU Instance  
**IP Address**: 192.222.51.223  
**Domain**: www.sophia-intel.ai

## Pre-requisites

1. SSH access to Lambda Labs instance
2. `.env.production` file with all required API keys and credentials
3. SSH key configured for passwordless access to the server
4. Domain DNS management access

## Deployment Structure

### Services to Deploy
- **sophia-dashboard**: React frontend application
- **mcp-research**: Research service with GPU access
- **mcp-context**: Context/embeddings service with GPU and persistent storage
- **mcp-agents**: Agent coordination service with GPU access
- **sophia-business**: Business intelligence and CRM integrations (NEW)
- **sophia-hubspot**: HubSpot CRM integration (NEW)
- **sophia-github**: GitHub repository and webhook integration (NEW)
- **sophia-lambda**: Lambda Labs GPU compute orchestration (NEW)
- **redis**: In-memory cache and session storage

### Key Features
- GPU support for AI workloads
- Persistent storage for embeddings and data
- nginx-ingress for domain routing and TLS
- Kubernetes Dashboard for monitoring
- OpenRouter integration for multi-model LLM support

## Deployment Steps

### 1. Run the Deployment Script

```bash
cd k8s-deploy
./scripts/deploy-to-lambda.sh
```

This script will:
1. Copy all deployment files to Lambda Labs
2. Install K3s with GPU support
3. Create Kubernetes secrets from `.env.production`
4. Deploy all services in order (Redis first, then others)
5. Set up nginx-ingress controller
6. Deploy Kubernetes Dashboard
7. Display deployment status

### 2. Update DNS

After deployment, update your DNS records:
- Create an A record for `www.sophia-intel.ai` pointing to `192.222.51.223`

### 3. Test the Deployment

Run the test script to verify everything is working:

```bash
./scripts/test-deployment.sh
```

This will check:
- Pod status
- Service connectivity
- GPU availability
- Persistent volumes
- Log output
- HTTP endpoints

## Post-Deployment

### Access Kubernetes Dashboard

1. Get the admin token:
```bash
ssh ubuntu@192.222.51.223 kubectl -n kubernetes-dashboard create token admin-user
```

2. Access dashboard at: `https://192.222.51.223:31443`
3. Use the token to log in

### Monitor Services

Check pod status:
```bash
ssh ubuntu@192.222.51.223 kubectl get pods -n sophia
```

Watch pods continuously:
```bash
ssh ubuntu@192.222.51.223 watch kubectl get pods -n sophia
```

Check logs:
```bash
ssh ubuntu@192.222.51.223 kubectl logs -n sophia deployment/[service-name]
```

### Troubleshooting

#### If pods are not starting:
1. Check events: `kubectl describe pod [pod-name] -n sophia`
2. Check logs: `kubectl logs [pod-name] -n sophia`
3. Verify secrets: `kubectl get secrets -n sophia`

#### If GPU is not available:
1. Check node resources: `kubectl describe nodes | grep nvidia`
2. Verify NVIDIA plugin: `kubectl get pods -n kube-system | grep nvidia`

#### If services are not accessible:
1. Check ingress: `kubectl describe ingress sophia-ingress -n sophia`
2. Verify DNS propagation: `nslookup www.sophia-intel.ai`
3. Check ingress controller: `kubectl get pods -n ingress-nginx`

## Service URLs (after DNS propagation)

- **Dashboard**: https://www.sophia-intel.ai
- **Research API**: https://www.sophia-intel.ai/research/
- **Context API**: https://www.sophia-intel.ai/context/
- **Agents API**: https://www.sophia-intel.ai/agents/
- **Business API**: https://www.sophia-intel.ai/business/
- **HubSpot API**: https://www.sophia-intel.ai/hubspot/
- **GitHub API**: https://www.sophia-intel.ai/github/
- **Lambda API**: https://www.sophia-intel.ai/lambda/

## Resource Allocation

### GPU Distribution
- mcp-research: 1 GPU
- mcp-context: 1 GPU (shared)
- mcp-agents: 1 GPU

### Memory Allocation
- sophia-dashboard: 512Mi - 1Gi
- mcp-research: 8Gi - 16Gi
- mcp-context: 8Gi - 16Gi
- mcp-agents: 4Gi - 8Gi
- sophia-business: 256Mi - 512Mi
- sophia-hubspot: 128Mi - 256Mi
- sophia-github: 128Mi - 256Mi
- sophia-lambda: 128Mi - 256Mi
- redis: 512Mi - 2Gi

## Rollback Procedure

If you need to rollback:

1. Delete the deployment:
```bash
ssh ubuntu@192.222.51.223 kubectl delete -f ~/k8s-deploy/manifests/
```

2. Restore previous version:
```bash
# Update image tags in manifests to previous version
# Re-apply manifests
```

## Security Notes

- All secrets are stored in Kubernetes secrets
- TLS is handled by cert-manager via Let's Encrypt
- Services communicate internally via ClusterIP
- Only ingress is exposed externally

## Maintenance

### Update a Service
```bash
# Edit the manifest
kubectl apply -f ~/k8s-deploy/manifests/[service].yaml
```

### Scale a Service
```bash
kubectl scale deployment/[service-name] -n sophia --replicas=2
```

### Update Secrets
```bash
kubectl delete secret sophia-secrets -n sophia
# Re-run create-all-secrets.sh with updated .env.production
```

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/k8s-deploy-only.yml`) automates:
1. Building Docker images
2. Pushing to GitHub Container Registry
3. Deploying to Kubernetes
4. Automatic rollback on failure

To trigger a deployment:
```bash
git push origin main
```

## Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure backup procedures
3. Implement auto-scaling policies
4. Set up log aggregation
5. Plan for multi-user access (currently single-user)
