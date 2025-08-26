# Sophia AI - Clean Kubernetes Deployment Plan (No Conflicts)

## What We're Eliminating (To Avoid Confusion)

### STOP Using These Files/Approaches:
❌ `deploy-sophia-intel.ai.sh` - Contains exposed secrets  
❌ `deploy-and-monitor.sh` - Docker Compose based  
❌ `deploy-and-monitor-fixed.sh` - Duplicate  
❌ `final-deploy.sh` - Another duplicate  
❌ `final-deploy-fixed.sh` - Yet another duplicate  
❌ `fix-nginx-conflict.sh` - Won't need with K8s ingress  
❌ `.github/workflows/deploy-sophia-intel.ai.yml` - Old workflow  
❌ `.github/workflows/deploy-sophia-intel.ai-fixed.yml` - Old workflow  
❌ `nginx.conf`, `nginx.sophia-intel.ai.conf`, `nginx.unified.conf` - Replaced by K8s ingress  
❌ AGNO framework files - Focus on MCP servers only for now  

### Architecture Decision: MCP Servers Only
- **USE**: Existing MCP servers (mcp-research, mcp-context, etc.)
- **IGNORE**: AGNO framework (agno-coordinator, agno-teams) - future consideration
- **REASON**: MCP servers are already working, AGNO adds confusion

## Clean Implementation Plan (8 Prompts)

### PROMPT 1: Clean Slate K3s Setup
**What**: Install K3s on Lambda Labs, remove Docker Compose
```bash
# This script will:
1. Stop all Docker Compose services
2. Clean up Docker volumes
3. Install K3s
4. Verify GPU access
```
**Creates**: 
- `k8s-deploy/scripts/install-k3s-clean.sh`
- Removes all Docker Compose dependencies

### PROMPT 2: Single Source Kubernetes Manifests
**What**: Convert ONLY MCP services to K8s (ignore AGNO)
```yaml
Services to deploy:
- sophia-dashboard (React frontend)
- mcp-research (Research API)
- mcp-context (Context/embeddings API)
- mcp-github (GitHub integration)
- mcp-business (Business logic)
- mcp-hubspot (HubSpot integration)
- mcp-agents (Agent swarm)
- mcp-lambda (Lambda integration)
```
**Creates**:
- `k8s-deploy/manifests/` - All K8s configs in ONE place
- No overlays, no complexity

### PROMPT 3: Single Ingress Configuration
**What**: One nginx-ingress to rule them all
```yaml
# Single ingress for all routes:
www.sophia-intel.ai/ → sophia-dashboard
www.sophia-intel.ai/api/research → mcp-research
www.sophia-intel.ai/api/context → mcp-context
# ... etc
```
**Creates**:
- `k8s-deploy/ingress/single-ingress.yaml`
- Deletes all nginx.conf files

### PROMPT 4: Unified Secrets Management
**What**: One way to manage secrets
```bash
# Single script to create all secrets from .env:
./k8s-deploy/scripts/create-all-secrets.sh
```
**Creates**:
- `k8s-deploy/secrets/create-all-secrets.sh`
- Uses existing .env.production as source

### PROMPT 5: Single Monitoring Solution
**What**: Just Kubernetes Dashboard (no Prometheus/Grafana complexity)
```bash
# Simple monitoring:
kubectl proxy
# Access at http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```
**Creates**:
- `k8s-deploy/monitoring/dashboard-only.yaml`
- Remove all other monitoring configs

### PROMPT 6: One CI/CD Workflow
**What**: Single GitHub Actions workflow
```yaml
name: Deploy to K8s
on: push to main
jobs:
  deploy:
    - Build images
    - Push to registry
    - Update K8s
```
**Creates**:
- `.github/workflows/k8s-deploy-only.yml`
- Archives all other workflows

### PROMPT 7: OpenRouter Integration (Simple)
**What**: Add OpenRouter to existing services
```python
# Simple wrapper that replaces OpenAI calls:
from libs.openrouter import OpenRouterClient
# Drop-in replacement for OpenAI
```
**Creates**:
- `libs/openrouter.py` - Simple client
- Updates to each MCP service

### PROMPT 8: Clean Documentation
**What**: Single source of truth docs
```markdown
1. How to deploy
2. How to monitor
3. How to scale
4. How to rollback
```
**Creates**:
- `k8s-deploy/README.md` - Everything you need
- Archive all conflicting docs

## File Structure After Cleanup

```
sophia-ai-intel/
├── k8s-deploy/                    # ONLY deployment folder
│   ├── manifests/                 # All K8s configs
│   ├── scripts/                   # Clean scripts
│   ├── secrets/                   # Secret templates
│   └── README.md                  # Single doc
├── services/                      
│   ├── mcp-*                      # Keep MCP services only
│   └── orchestrator/              # Keep but don't deploy yet
├── .github/workflows/
│   └── k8s-deploy-only.yml        # Single workflow
└── archived/                      # Move all old deployment files here
```

## What Gets Archived (Not Deleted)

Move to `archived/` folder:
- All old deployment scripts
- All nginx configs  
- All duplicate workflows
- AGNO framework (for future)
- Old monitoring configs

## Simple Commands (No Confusion)

### Deploy Everything:
```bash
cd k8s-deploy
./scripts/deploy-all.sh
```

### Check Status:
```bash
kubectl get pods -n sophia
kubectl get ingress -n sophia
```

### View Logs:
```bash
kubectl logs -n sophia -l app=mcp-research
```

### Rollback:
```bash
kubectl rollout undo deployment/mcp-research -n sophia
```

## Timeline (5 Days Total)

**Day 1**: Clean slate (PROMPT 1)
- Remove Docker Compose
- Install K3s
- Verify GPU works

**Day 2**: Deploy services (PROMPTS 2-3)
- Apply K8s manifests
- Configure ingress
- Test endpoints

**Day 3**: Operations (PROMPTS 4-5)
- Migrate secrets
- Setup monitoring
- Document process

**Day 4**: CI/CD (PROMPT 6)
- Single workflow
- Test deployment
- Archive old files

**Day 5**: Enhancement (PROMPTS 7-8)
- Add OpenRouter
- Final documentation
- Ready for users

## Success Metrics

✅ One way to deploy (no confusion)  
✅ One place for configs (k8s-deploy/)  
✅ One monitoring solution  
✅ One CI/CD pipeline  
✅ Clear what's active vs archived  
✅ No conflicting approaches  

## Key Principles

1. **If it's not in k8s-deploy/, it's not used**
2. **MCP services only (no AGNO yet)**
3. **One way to do everything**
4. **Archive don't delete (can reference later)**
5. **Simple over perfect**

---

**Next Step**: Start with PROMPT 1 to clean slate your Lambda Labs instance
