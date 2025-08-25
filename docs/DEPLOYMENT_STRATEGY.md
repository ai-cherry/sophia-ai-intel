# 🚀 Sophia AI Intel - Deployment Strategy Guide

**Last Updated**: August 25, 2025  
**Status**: Production Ready  
**Primary Strategy**: Lambda Labs with Pulumi Cloud  
**Fallback Strategy**: Fly.io (Legacy)  

---

## 📋 Executive Summary

Sophia AI Intel supports **two deployment strategies** to provide flexibility and vendor independence. This document clarifies the current recommended approach and explains when to use each strategy.

### **Current Recommendation: Lambda Labs (Primary)**
- **Best for**: Cost-effective GPU compute, full infrastructure control
- **Use when**: Production deployments, GPU-intensive AI workloads
- **Status**: ✅ Production Ready
- **Cost**: ~$200-400/month vs $800+ on other platforms

### **Legacy Support: Fly.io (Fallback)**
- **Best for**: Quick prototyping, managed infrastructure
- **Use when**: Development environments, proof-of-concepts
- **Status**: ✅ Operational but not actively developed
- **Cost**: Higher but more managed

---

## 🎯 Primary Deployment Strategy: Lambda Labs + Pulumi

### **Architecture Overview**
```
Lambda Labs Instance (GPU-enabled)
├── Docker Compose Stack
│   ├── sophia-dashboard:3000
│   ├── sophia-research:8081
│   ├── sophia-context:8082
│   ├── sophia-github:8083
│   ├── sophia-business:8084
│   ├── sophia-lambda:8085
│   ├── sophia-hubspot:8086
│   ├── sophia-agents:8087
│   └── nginx-proxy:80/443
├── External Services
│   ├── Neon PostgreSQL
│   ├── Redis Cloud
│   └── Qdrant Vector DB
└── Pulumi Cloud (Infrastructure as Code)
```

### **Deployment Process**
```bash
# 1. Automated via GitHub Actions (Recommended)
gh workflow run deploy_pulumi.yml

# 2. Manual deployment
cd ops/pulumi
pulumi up --yes
```

### **Key Benefits**
- ✅ GPU acceleration (A100, RTX 4090, RTX 3080 options)
- ✅ 50-70% cost reduction vs traditional cloud
- ✅ Complete infrastructure control
- ✅ Zero vendor lock-in
- ✅ Scalable from development to production

### **Service Configuration**
All 8 microservices run in Docker containers with:
- Automatic health checks and restarts
- Nginx reverse proxy with SSL termination
- Redis-based session management
- Cross-service communication via Docker networking

---

## 🔄 Fallback Deployment Strategy: Fly.io

### **Architecture Overview**
```
Fly.io Global Network
├── sophiaai-dashboard-v2.fly.dev
├── sophiaai-mcp-repo-v2.fly.dev
├── sophiaai-mcp-research-v2.fly.dev
├── sophiaai-mcp-context-v2.fly.dev
├── sophiaai-mcp-business-v2.fly.dev
└── sophiaai-jobs-v2.fly.dev
```

### **Deployment Process**
```bash
# Deploy all services to Fly.io
npm run deploy

# Deploy individual service
npm run deploy:dashboard
```

### **When to Use Fly.io**
- Development environments requiring quick iterations
- Proof-of-concept deployments
- Backup/disaster recovery scenarios
- Teams preferring managed infrastructure

---

## 🔀 Choosing Your Deployment Strategy

### **Use Lambda Labs When:**
- ✅ Production workloads requiring GPU acceleration
- ✅ Cost optimization is a priority
- ✅ You need full infrastructure control
- ✅ AI/ML workloads with heavy compute requirements
- ✅ Long-term stable deployments

### **Use Fly.io When:**
- ✅ Rapid prototyping and development
- ✅ Proof-of-concept demonstrations
- ✅ Teams preferring managed infrastructure
- ✅ Global edge deployment requirements
- ✅ Disaster recovery scenarios

---

## 📊 Deployment Comparison

| Aspect | Lambda Labs | Fly.io |
|--------|-------------|---------|
| **Cost** | $200-400/month | $600-1200/month |
| **GPU Access** | ✅ A100, RTX 4090, RTX 3080 | ❌ No GPU support |
| **Setup Time** | 20-35 minutes | 10-20 minutes |
| **Scalability** | Manual instance scaling | Auto-scaling |
| **Control** | Full infrastructure access | Managed platform |
| **Complexity** | Medium (Docker Compose) | Low (Fly.io handles it) |
| **Vendor Lock-in** | None | Moderate |
| **Global Edge** | Single region | Multi-region |

---

## 🚀 Migration Between Strategies

### **Lambda Labs → Fly.io**
```bash
# 1. Export environment variables
./scripts/export_lambda_env.sh

# 2. Configure Fly.io secrets
npm run deploy:secrets

# 3. Deploy services
npm run deploy
```

### **Fly.io → Lambda Labs**
```bash
# 1. Set up Pulumi configuration
cd ops/pulumi
pulumi config set --secret lambda-api-key "your-key"

# 2. Deploy infrastructure
pulumi up --yes
```

---

## 🎯 Service Mapping

### **Lambda Labs Services (8 Total)**
| Service | Port | Purpose | Fly.io Equivalent |
|---------|------|---------|-------------------|
| sophia-dashboard | 3000 | React frontend | sophiaai-dashboard-v2 |
| sophia-research | 8081 | Research APIs | sophiaai-mcp-research-v2 |
| sophia-context | 8082 | Memory & context | sophiaai-mcp-context-v2 |
| sophia-github | 8083 | GitHub integration | sophiaai-mcp-repo-v2 |
| sophia-business | 8084 | Business intelligence | sophiaai-mcp-business-v2 |
| sophia-lambda | 8085 | Infrastructure mgmt | N/A (Lambda Labs only) |
| sophia-hubspot | 8086 | HubSpot CRM | N/A (Lambda Labs only) |
| sophia-agents | 8087 | AI Agent Swarm | N/A (Lambda Labs only) |

### **Additional Lambda Labs Components**
- **sophia-jobs**: Background processing
- **nginx-proxy**: Reverse proxy and SSL termination
- **health-check**: Service monitoring

---

## 🔧 Environment Configuration

### **Lambda Labs Environment Variables**
```bash
# Core Services
NEON_DATABASE_URL=postgresql://...
REDIS_URL=redis://...
QDRANT_URL=https://...

# Lambda Labs Specific
LAMBDA_API_KEY=your-lambda-key
LAMBDA_PRIVATE_SSH_KEY=your-private-key
LAMBDA_PUBLIC_SSH_KEY=your-public-key

# AI/LLM Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PORTKEY_API_KEY=...
```

### **Fly.io Environment Variables**
```bash
# All Lambda Labs variables plus:
FLY_API_TOKEN=fo1_...

# Fly.io specific secrets are managed via:
flyctl secrets set KEY=VALUE -a app-name
```

---

## 📋 Deployment Checklists

### **Lambda Labs Deployment Checklist**
- [ ] Lambda Labs account configured
- [ ] SSH keys uploaded to Lambda Labs dashboard
- [ ] GitHub secrets configured (LAMBDA_API_KEY, etc.)
- [ ] External services accessible (Neon, Redis, Qdrant)
- [ ] Docker and Docker Compose available
- [ ] Health checks passing post-deployment

### **Fly.io Deployment Checklist**
- [ ] Fly.io CLI installed and authenticated
- [ ] GitHub secrets configured (FLY_API_TOKEN)
- [ ] All fly.toml files present in service directories
- [ ] External services configured
- [ ] Health checks passing post-deployment

---

## 🚨 Emergency Procedures

### **Lambda Labs Service Issues**
```bash
# Check service health
docker-compose ps
docker-compose logs -f service-name

# Restart specific service
docker-compose restart service-name

# Full system restart
docker-compose restart
```

### **Fly.io Service Issues**
```bash
# Check service health
flyctl status -a app-name

# View logs
flyctl logs -a app-name

# Restart service
flyctl machines restart machine-id -a app-name
```

---

## 📈 Monitoring & Health Checks

### **Lambda Labs Monitoring**
- **Health Endpoints**: Each service exposes `/healthz`
- **System Monitoring**: `htop`, `docker stats`
- **Log Aggregation**: `docker-compose logs -f`
- **Resource Usage**: Docker system monitoring

### **Fly.io Monitoring**
- **Built-in Monitoring**: Fly.io dashboard
- **Health Endpoints**: Same `/healthz` endpoints
- **Log Aggregation**: `flyctl logs`
- **Metrics**: Fly.io Prometheus integration

---

## 🎯 Recommended Workflow

### **For Production Teams**
1. **Primary**: Deploy to Lambda Labs for cost-effective GPU compute
2. **Development**: Use Fly.io for rapid iteration and testing
3. **Disaster Recovery**: Maintain both deployments for redundancy

### **For Development Teams**
1. **Primary**: Use Fly.io for managed infrastructure
2. **AI Workloads**: Deploy to Lambda Labs when GPU acceleration needed
3. **Cost Monitoring**: Switch to Lambda Labs for long-running deployments

---

## 📞 Support Resources

### **Lambda Labs Deployment**
- **Documentation**: [DEPLOYMENT_PLAN_COMPLETE.md](DEPLOYMENT_PLAN_COMPLETE.md)
- **Operational Guide**: [PRODUCTION_RUNBOOK.md](PRODUCTION_RUNBOOK.md)
- **Infrastructure Code**: `ops/pulumi/`

### **Fly.io Deployment**
- **Historical Reference**: [PHASE_BC_COMPLETION.md](PHASE_BC_COMPLETION.md)
- **Service Configs**: Individual `fly.toml` files
- **Deployment Scripts**: `package.json` deploy commands

---

**This deployment strategy provides clear guidance on choosing the optimal deployment approach based on your specific requirements while maintaining flexibility and cost efficiency.**
