# Sophia AI Complete Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for the Sophia AI platform, incorporating all infrastructure fixes, port allocations, and caching strategies.

## Pre-Deployment Checklist

- [ ] All port conflicts resolved (cAdvisor moved to 8900)
- [ ] Environment variables standardized
- [ ] Redis caching strategy implemented
- [ ] Missing services scaffolded
- [ ] Deployment scripts updated

## Port Allocation Summary

### Service Port Map

```yaml
# Frontend (3000-3999)
sophia-dashboard: 3000
agno-coordinator: 3002

# Core Services (8000-8499)
orchestrator: 8080
mcp-research: 8081
mcp-context: 8082
mcp-github: 8083
mcp-business: 8084
mcp-lambda: 8085
mcp-hubspot: 8086
mcp-agents: 8087

# New Business Services (8088-8102)
mcp-gong: 8088
mcp-salesforce: 8089
mcp-slack: 8090
mcp-apollo: 8091
mcp-intercom: 8092
mcp-linear: 8093
mcp-looker: 8094
mcp-asana: 8095
mcp-notion: 8096
mcp-gdrive: 8097
mcp-costar: 8098
mcp-phantom: 8099
mcp-outlook: 8100
mcp-sharepoint: 8101
mcp-elevenlabs: 8102

# Agno Framework
agno-teams: 8008

# Monitoring (9000-9999)
prometheus: 9090
grafana: 3001
loki: 3100
promtail: 9080
cadvisor: 8900  # Fixed from 8080
node-exporter: 9100
dcgm-exporter: 9400

# Infrastructure (5000-6999)
redis: 6379
postgresql: 5432
qdrant: 6333
```

## Caching Implementation

### Redis Database Allocation

```yaml
DB 0: Session store
DB 1: API response cache
DB 2: LLM response cache
DB 3: Embedding cache
DB 4: Business data cache
DB 5: Rate limiting
DB 6: Job queue
DB 7: Pub/Sub events
DB 8: Feature flags
DB 9: Metrics
DB 10: Search cache
DB 11: Graph cache
DB 12: Temp storage
DB 13: Distributed locks
DB 14: Analytics
DB 15: Backup/restore
```

### Cache TTL Strategy

```yaml
static_assets: 1 year
llm_responses: 1-6 hours
api_responses: 5-60 minutes
business_data: 5-60 minutes
embeddings: 24 hours
session_data: 24 hours
search_results: 30 minutes
```

## Deployment Options

### Option 1: Docker Compose (Development/Testing)

```bash
# 1. Apply fixes
./scripts/fix-deployment-issues.sh

# 2. Build all services
docker-compose build --no-cache

# 3. Start services
docker-compose up -d

# 4. Monitor health
./scripts/health-check-all.sh docker

# 5. View logs
docker-compose logs -f
```

### Option 2: Kubernetes on Lambda Labs (Production)

```bash
# 1. Prepare Lambda Labs server
ssh ubuntu@192.222.51.223

# 2. Install K3s
curl -sfL https://get.k3s.io | sh -

# 3. Deploy all services
./k8s-deploy/scripts/deploy-all-services.sh

# 4. Check deployment
kubectl get pods -n sophia
kubectl get services -n sophia

# 5. Access dashboard
kubectl port-forward -n sophia svc/sophia-dashboard 3000:3000
```

### Option 3: Hybrid Deployment

```bash
# Core services on Kubernetes
kubectl apply -f k8s-deploy/manifests/

# Development services on Docker
docker-compose up -d mcp-gong mcp-salesforce mcp-slack
```

## Service Implementation Status

### ✅ Implemented Services
- sophia-dashboard (React frontend)
- mcp-research (Deep research)
- mcp-context (Embeddings & knowledge)
- mcp-github (GitHub integration)
- mcp-business (Business services)
- mcp-lambda (Lambda integration)
- mcp-hubspot (HubSpot CRM)
- mcp-agents (Agent swarm)
- agno-coordinator (Coordination)
- agno-teams (Business teams)

### 🚧 Partially Implemented
- orchestrator (TypeScript issues)
- Redis (needs config update)

### ❌ Missing Services (Created Scaffolds)
- mcp-gong
- mcp-salesforce
- mcp-slack
- mcp-apollo
- mcp-intercom
- mcp-linear
- mcp-looker
- mcp-asana
- mcp-notion
- mcp-gdrive
- mcp-costar
- mcp-phantom
- mcp-outlook
- mcp-sharepoint
- mcp-elevenlabs

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.production.template .env.production
# Fill in all API keys and secrets
```

### 2. Standardize Variables

```bash
# Merge standardized variables
cat .env.standardized >> .env.production
```

### 3. Validate Configuration

```bash
./scripts/env_check.py
```

## Monitoring Setup

### Prometheus Metrics

```yaml
# Access at http://localhost:9090
targets:
  - sophia-dashboard:3000
  - mcp-research:8081
  - mcp-context:8082
  - mcp-agents:8087
  - redis:6379
```

### Grafana Dashboards

```bash
# Access at http://localhost:3001
# Default: admin/admin

# Import dashboards:
- Service Health
- Resource Usage
- Cache Performance
- API Latency
```

### Health Checks

```bash
# Docker Compose
./scripts/health-check-all.sh docker

# Kubernetes
./scripts/health-check-all.sh k8s

# Individual service
curl http://localhost:8081/healthz
```

## Security Considerations

### 1. SSL/TLS Configuration

```bash
# Generate certificates
./scripts/setup_ssl_certificates.py

# Configure Nginx
cp configs/nginx/ssl.conf /etc/nginx/conf.d/
```

### 2. API Gateway Security

```yaml
# Kong configuration
plugins:
  - name: rate-limiting
    config:
      minute: 100
  - name: key-auth
  - name: cors
  - name: request-transformer
```

### 3. Network Policies

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sophia-network-policy
  namespace: sophia
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   sudo lsof -i :8080
   # Kill process if needed
   sudo kill -9 <PID>
   ```

2. **Service Not Starting**
   ```bash
   # Check logs
   docker-compose logs <service-name>
   # or
   kubectl logs -n sophia deployment/<service-name>
   ```

3. **Cache Not Working**
   ```bash
   # Connect to Redis
   redis-cli
   # Check keys
   KEYS *
   # Monitor commands
   MONITOR
   ```

4. **Database Connection Issues**
   ```bash
   # Test connection
   psql $DATABASE_URL
   # Check Qdrant
   curl http://localhost:6333/collections
   ```

## Performance Optimization

### 1. Resource Allocation

```yaml
# Docker Compose
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

### 2. Horizontal Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-research
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3. Cache Warming

```bash
# Run cache warming script
./scripts/cache-warmer.py --services all --data business
```

## Backup and Recovery

### 1. Database Backup

```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Redis
redis-cli --rdb dump.rdb

# Qdrant
curl -X POST http://localhost:6333/collections/backup
```

### 2. Configuration Backup

```bash
# Backup all configs
tar -czf sophia-config-backup.tar.gz \
  .env* \
  docker-compose.yml \
  k8s-deploy/ \
  configs/
```

## Next Steps

### Week 1: Stabilization
1. Run deployment fix script
2. Deploy core services
3. Verify all health checks pass
4. Set up monitoring

### Week 2: Integration
1. Implement Gong integration
2. Implement Salesforce integration
3. Implement Slack integration
4. Test end-to-end flows

### Week 3: Optimization
1. Tune cache settings
2. Optimize database queries
3. Implement auto-scaling
4. Load testing

### Week 4: Production
1. SSL certificates
2. API gateway configuration
3. Security audit
4. Go live!

## Support

### Documentation
- Infrastructure: `SOPHIA_AI_DEPLOYMENT_INFRASTRUCTURE_ANALYSIS.md`
- Port Strategy: `SOPHIA_AI_PORT_CACHING_STRATEGY.md`
- Architecture: `SOPHIA_AI_COMPREHENSIVE_ARCHITECTURE_ANALYSIS.md`

### Scripts
- Fix Issues: `./scripts/fix-deployment-issues.sh`
- Deploy K8s: `./k8s-deploy/scripts/deploy-all-services.sh`
- Health Check: `./scripts/health-check-all.sh`

### Monitoring
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- K8s Dashboard: http://localhost:31443

---

**Remember**: Always backup before making changes and test in staging first!
