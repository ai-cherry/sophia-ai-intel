# Sophia AI - Lambda Labs Kubernetes Deployment Plan

## Overview
Pragmatic deployment plan for Sophia AI on Lambda Labs GPU infrastructure using Kubernetes. Designed for immediate single-user deployment with scaling to 5-6 users next week.

## Current Situation
- **Infrastructure**: Lambda Labs GPU instance (192.222.51.223)
- **Current State**: Docker Compose deployment
- **Target State**: Kubernetes deployment with minimal complexity
- **Timeline**: Immediate deployment, scale to 5 users next week

## Multi-Prompt Implementation Plan

### PROMPT 1: Kubernetes Setup on Lambda Labs
**Goal**: Install and configure K3s (lightweight Kubernetes) on Lambda Labs instance

```yaml
Tasks:
1. SSH into Lambda Labs instance
2. Install K3s (single-node cluster)
3. Configure kubectl access
4. Install Helm package manager
5. Set up local storage class
```

**Expected Deliverables**:
- `scripts/setup-k3s-lambda.sh` - Automated K3s installation
- `scripts/k3s-healthcheck.sh` - Verify cluster health
- Updated `.github/workflows/lambda-k8s-deploy.yml`

### PROMPT 2: Convert Services to Kubernetes Manifests
**Goal**: Transform Docker Compose services into Kubernetes deployments

```yaml
Services to Convert:
1. sophia-dashboard → Deployment + Service
2. mcp-research → Deployment + Service  
3. mcp-context → Deployment + Service + PVC
4. mcp-github → Deployment + Service
5. mcp-business → Deployment + Service
6. mcp-hubspot → Deployment + Service
7. mcp-agents → Deployment + Service
8. mcp-lambda → Deployment + Service
```

**Expected Deliverables**:
- `k8s/base/` - Base Kubernetes manifests
- `k8s/overlays/lambda-labs/` - Lambda Labs specific configs
- `scripts/generate-k8s-manifests.py` - Auto-convert docker-compose

### PROMPT 3: Ingress and Domain Configuration
**Goal**: Configure nginx-ingress for www.sophia-intel.ai

```yaml
Components:
1. Install nginx-ingress controller
2. Configure Ingress rules for all services
3. Set up cert-manager for Let's Encrypt
4. Configure DNS with DNSimple
```

**Expected Deliverables**:
- `k8s/ingress/nginx-values.yaml`
- `k8s/ingress/ingress-routes.yaml`
- `k8s/ingress/cert-manager.yaml`
- `scripts/configure-ingress.sh`

### PROMPT 4: Secrets and ConfigMaps Management
**Goal**: Migrate environment variables to Kubernetes secrets

```yaml
Secrets to Create:
1. openai-credentials
2. database-credentials
3. redis-credentials
4. external-api-keys
5. openrouter-config (future-ready)
```

**Expected Deliverables**:
- `k8s/secrets/secrets-template.yaml`
- `scripts/create-k8s-secrets.sh`
- `k8s/configmaps/app-config.yaml`

### PROMPT 5: Monitoring and Basic Observability
**Goal**: Deploy minimal monitoring stack

```yaml
Components:
1. metrics-server (resource monitoring)
2. kubernetes-dashboard (visual management)
3. Basic Prometheus + Grafana (optional)
```

**Expected Deliverables**:
- `k8s/monitoring/metrics-server.yaml`
- `k8s/monitoring/dashboard.yaml`
- `scripts/setup-monitoring.sh`

### PROMPT 6: CI/CD Pipeline Update
**Goal**: Update GitHub Actions for Kubernetes deployment

```yaml
Pipeline Steps:
1. Build and push images to registry
2. Update Kubernetes manifests
3. Apply manifests to cluster
4. Run health checks
5. Basic rollback capability
```

**Expected Deliverables**:
- `.github/workflows/k8s-deploy.yml`
- `scripts/k8s-rollback.sh`
- `scripts/k8s-health-check.sh`

### PROMPT 7: OpenRouter Integration (Quick Win)
**Goal**: Add OpenRouter support to existing services

```yaml
Implementation:
1. Create OpenRouter client wrapper
2. Update service configurations
3. Add model routing logic
4. Cost tracking basics
```

**Expected Deliverables**:
- `libs/openrouter_client.py`
- Updated service configurations
- `k8s/configmaps/openrouter-config.yaml`

### PROMPT 8: User Scaling Preparation
**Goal**: Prepare for 5-6 users next week

```yaml
Preparations:
1. Resource limits for services
2. Basic auth mechanism
3. Service mesh setup (Linkerd-viz)
4. Database connection pooling
```

**Expected Deliverables**:
- `k8s/base/resource-limits.yaml`
- `k8s/auth/basic-auth.yaml`
- `docs/scaling-checklist.md`

## Execution Timeline

### Day 1-2: Foundation (Prompts 1-2)
- Get K3s running on Lambda Labs
- Convert core services to Kubernetes

### Day 3-4: Networking (Prompts 3-4)
- Configure ingress and domain
- Migrate secrets management

### Day 5: Operations (Prompts 5-6)
- Set up monitoring
- Update CI/CD pipeline

### Week 2: Enhancement (Prompts 7-8)
- Add OpenRouter integration
- Prepare for user scaling

## Minimal Security Practices

1. **Secrets Management**
   - Use Kubernetes secrets (not ConfigMaps) for sensitive data
   - Enable RBAC with basic roles
   - Rotate database passwords monthly

2. **Network Security**
   - Enable NetworkPolicies for pod communication
   - Use HTTPS for all external traffic
   - Basic rate limiting on ingress

3. **Access Control**
   - SSH key-only access to Lambda Labs
   - kubectl access via kubeconfig
   - Basic auth for dashboard access

## Resource Allocation (Single GPU Node)

```yaml
Node Resources:
- GPU: 1x A100 (shared across AI services)
- CPU: 24 cores (allocate 20)
- Memory: 96GB (allocate 80GB)
- Storage: 1TB NVMe

Service Allocation:
- mcp-research: 4 CPU, 16GB RAM, GPU access
- mcp-context: 4 CPU, 16GB RAM, GPU access
- mcp-agents: 4 CPU, 16GB RAM, GPU access
- Others: 1-2 CPU, 4-8GB RAM each
```

## Quick Start Commands

```bash
# After each prompt implementation:

# 1. Deploy to Lambda Labs
ssh ubuntu@192.222.51.223

# 2. Apply Kubernetes manifests
kubectl apply -k k8s/overlays/lambda-labs/

# 3. Check deployment status
kubectl get pods -n sophia-ai
kubectl get ingress -n sophia-ai

# 4. Access services
curl https://www.sophia-intel.ai/health
```

## Success Criteria

### Immediate (1 User)
- [ ] All services running on K3s
- [ ] Domain accessible via HTTPS
- [ ] Basic health monitoring
- [ ] Single GitHub Action deployment

### Next Week (5-6 Users)
- [ ] Resource limits enforced
- [ ] Basic auth implemented
- [ ] OpenRouter integrated
- [ ] Monitoring dashboard available

### Future (120 Days)
- [ ] Ready for multi-node scaling
- [ ] Full observability stack
- [ ] Advanced security practices
- [ ] Multi-region capability

## Risk Mitigation

1. **Single Node Failure**: Daily backups to S3
2. **Resource Exhaustion**: Set hard limits, monitor usage
3. **Deployment Failures**: Keep Docker Compose as fallback
4. **GPU Sharing**: Use NVIDIA device plugin for Kubernetes

## Notes

- K3s chosen over full Kubernetes for simplicity
- Single-node start, multi-node ready architecture
- Focus on getting services running vs. perfect architecture
- Security debt acceptable for 120-day runway
- OpenRouter integration provides immediate cost savings

---

**Next Step**: Execute PROMPT 1 to install K3s on Lambda Labs instance
