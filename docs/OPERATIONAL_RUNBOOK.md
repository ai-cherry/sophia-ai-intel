# Sophia AI - Operational Runbook

## Table of Contents
1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Maintenance Procedures](#maintenance-procedures)
4. [Scaling Operations](#scaling-operations)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Emergency Procedures](#emergency-procedures)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Performance Optimization](#performance-optimization)

## System Overview

### Production Environment v1.1.0
- **Domain**: www.sophia-intel.ai
- **Infrastructure**: Lambda Labs (192.222.51.223) + K3s Kubernetes
- **Container Registry**: GitHub Container Registry (ghcr.io)
- **CI/CD**: GitHub Actions with automated deployment and health proofs
- **Monitoring**: Prometheus + Grafana + Loki stack

### Key Components
- **Kubernetes Cluster**: K3s on Lambda Labs infrastructure
- **Load Balancer**: nginx with SSL termination
- **Service Mesh**: Istio (optional)
- **Storage**: Persistent volumes for stateful services
- **Secrets Management**: External Secrets Operator

## Service Architecture

### Core Services (v1.1.0)

#### MCP Services
- **mcp-research**: Research and analysis capabilities
  - Port: 8001
  - Health Check: `/health`
  - Resource Requirements: 1-2 CPU, 2-4Gi memory

- **mcp-context**: Context management and processing
  - Port: 8002
  - Health Check: `/health`
  - Resource Requirements: 1-2 CPU, 2-4Gi memory

- **mcp-agents**: Agent orchestration and management
  - Port: 8003
  - Health Check: `/health`
  - Resource Requirements: 2-4 CPU, 4-8Gi memory

#### Business Intelligence Services
- **sophia-dashboard**: Main dashboard interface
  - Port: 3000
  - Health Check: `/api/health`
  - Resource Requirements: 1 CPU, 1-2Gi memory

- **sophia-business**: Business logic and analytics
  - Port: 8004
  - Health Check: `/health`
  - Resource Requirements: 1-2 CPU, 2-4Gi memory

#### Integration Services
- **sophia-hubspot**: HubSpot CRM integration
  - Port: 8005
  - Health Check: `/health`
  - Resource Requirements: 0.5-1 CPU, 1-2Gi memory

- **sophia-github**: GitHub integration and workflows
  - Port: 8006
  - Health Check: `/health`
  - Resource Requirements: 0.5-1 CPU, 1-2Gi memory

- **sophia-lambda**: Lambda Labs infrastructure integration
  - Port: 8007
  - Health Check: `/health`
  - Resource Requirements: 0.5-1 CPU, 1-2Gi memory

#### AI Services
- **mcp-business**: Business logic and analytics processing
  - Port: 8008
  - Health Check: `/health`
  - Resource Requirements: 1-2 CPU, 2-4Gi memory

### Infrastructure Services
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation and analysis
- **nginx**: Ingress controller and load balancer

## Maintenance Procedures

### Daily Maintenance
```bash
# Check system health
kubectl get pods -n sophia -o wide

# Check resource utilization
kubectl top pods -n sophia
kubectl top nodes

# Review logs for errors
kubectl logs -n sophia --selector=app --tail=100 | grep -i error

# Validate monitoring stack
curl -f http://192.222.51.223:9090/-/healthy
curl -f http://192.222.51.223:3000/api/health
```

### Weekly Maintenance
```bash
# Update container images (if needed)
kubectl rollout restart deployment/mcp-research -n sophia
kubectl rollout restart deployment/mcp-context -n sophia
kubectl rollout restart deployment/mcp-agents -n sophia

# Clean up old pods and resources
kubectl delete pods --field-selector=status.phase=Succeeded -n sophia
kubectl delete pods --field-selector=status.phase=Failed -n sophia

# Backup configurations
kubectl get configmaps -n sophia -o yaml > backup/configmaps-$(date +%Y%m%d).yaml
kubectl get secrets -n sophia -o yaml > backup/secrets-$(date +%Y%m%d).yaml
```

### Monthly Maintenance
```bash
# Review and update resource limits
kubectl describe deployments -n sophia | grep -A 5 "Resource Requests"

# Certificate renewal (if using Let's Encrypt)
kubectl get certificates -n sophia

# Security patches review
kubectl get pods -n sophia -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'

# Performance analysis
./scripts/load_testing/comprehensive_load_test.py --duration=1800
```

## Scaling Operations

### Horizontal Pod Autoscaler (HPA)
```yaml
# HPA is configured for key services
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-research-hpa
  namespace: sophia
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Manual Scaling Commands
```bash
# Scale up critical services during high load
kubectl scale deployment mcp-research --replicas=5 -n sophia
kubectl scale deployment mcp-context --replicas=5 -n sophia
kubectl scale deployment mcp-agents --replicas=3 -n sophia

# Scale down during low usage
kubectl scale deployment mcp-research --replicas=2 -n sophia
kubectl scale deployment mcp-context --replicas=2 -n sophia
kubectl scale deployment mcp-agents --replicas=1 -n sophia

# Check scaling status
kubectl get hpa -n sophia
```

### Resource Optimization
```bash
# Monitor resource usage patterns
kubectl top pods -n sophia --sort-by=cpu
kubectl top pods -n sophia --sort-by=memory

# Adjust resource requests/limits based on usage
kubectl patch deployment mcp-research -n sophia -p '{"spec":{"template":{"spec":{"containers":[{"name":"mcp-research","resources":{"requests":{"cpu":"2","memory":"4Gi"},"limits":{"cpu":"4","memory":"8Gi"}}}]}}}}'
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Service Unavailable (503 Errors)
```bash
# Check pod status
kubectl get pods -n sophia | grep -v Running

# Check service endpoints
kubectl get endpoints -n sophia

# Restart problematic services
kubectl rollout restart deployment/[service-name] -n sophia

# Check ingress configuration
kubectl describe ingress sophia-ingress -n sophia
```

#### High Memory Usage
```bash
# Identify memory-intensive pods
kubectl top pods -n sophia --sort-by=memory

# Check for memory leaks in logs
kubectl logs [pod-name] -n sophia | grep -i "memory\|heap\|oom"

# Scale up or add memory limits
kubectl patch deployment [service-name] -n sophia -p '{"spec":{"template":{"spec":{"containers":[{"name":"[container-name]","resources":{"limits":{"memory":"8Gi"}}}]}}}}'
```

#### Database Connection Issues
```bash
# Check Redis connectivity
kubectl exec -it deployment/redis -n sophia -- redis-cli ping

# Test database connections from services
kubectl exec -it deployment/mcp-context -n sophia -- wget -qO- http://redis:6379/ping

# Reset connections
kubectl rollout restart deployment/redis -n sophia
sleep 30
kubectl rollout restart deployment/mcp-research -n sophia
```

#### SSL/TLS Certificate Issues
```bash
# Check certificate status
kubectl get certificates -n sophia
kubectl describe certificate sophia-tls -n sophia

# Force certificate renewal
kubectl delete certificate sophia-tls -n sophia
kubectl apply -f k8s-deploy/secrets/tls-secrets.yaml

# Verify SSL configuration
openssl s_client -connect www.sophia-intel.ai:443 -servername www.sophia-intel.ai
```

### Log Analysis Commands
```bash
# Search for specific errors across all services
kubectl logs -n sophia --selector=app=mcp-research --tail=1000 | grep -i "error\|exception\|failed"

# Monitor real-time logs
kubectl logs -f -n sophia --selector=app=mcp-research

# Export logs for analysis
kubectl logs -n sophia --selector=app --since=24h > logs/sophia-$(date +%Y%m%d).log
```

## Emergency Procedures

### Rollback Deployment
```bash
# Check rollout history
kubectl rollout history deployment/mcp-research -n sophia

# Rollback to previous version
kubectl rollout undo deployment/mcp-research -n sophia

# Rollback to specific revision
kubectl rollout undo deployment/mcp-research --to-revision=2 -n sophia

# Verify rollback
kubectl rollout status deployment/mcp-research -n sophia
```

### Emergency Scale Down
```bash
# Scale down non-critical services during emergencies
kubectl scale deployment sophia-hubspot --replicas=0 -n sophia
kubectl scale deployment sophia-github --replicas=0 -n sophia
kubectl scale deployment sophia-lambda --replicas=0 -n sophia

# Maintain only core services
kubectl scale deployment mcp-research --replicas=1 -n sophia
kubectl scale deployment mcp-context --replicas=1 -n sophia
kubectl scale deployment sophia-dashboard --replicas=1 -n sophia
```

### Disaster Recovery
```bash
# Export all configurations
mkdir -p disaster-recovery/$(date +%Y%m%d)
kubectl get all,configmaps,secrets,ingress -n sophia -o yaml > disaster-recovery/$(date +%Y%m%d)/full-backup.yaml

# Backup persistent data
kubectl exec -it deployment/redis -n sophia -- redis-cli --rdb /data/backup.rdb

# Test restore procedure (in staging)
kubectl apply -f disaster-recovery/[backup-date]/full-backup.yaml -n sophia-staging
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Service Health**: Pod status, restart counts
- **Performance**: Response times, throughput, error rates
- **Resource Usage**: CPU, memory, disk, network
- **Business Metrics**: Request volumes, user activity

### Alert Thresholds
- **CPU Usage**: >80% for 5 minutes
- **Memory Usage**: >85% for 5 minutes
- **Pod Restart**: >3 restarts in 10 minutes
- **Response Time**: >2000ms average for 5 minutes
- **Error Rate**: >5% for 5 minutes

### Monitoring Commands
```bash
# Check Prometheus targets
curl http://192.222.51.223:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# Query metrics
curl "http://192.222.51.223:9090/api/v1/query?query=up{job=\"kubernetes-pods\"}" | jq .

# Check Grafana dashboards
curl -f http://192.222.51.223:3000/api/health
```

## Performance Optimization

### CPU Optimization
```bash
# Analyze CPU usage patterns
kubectl top pods -n sophia --sort-by=cpu

# Adjust CPU requests based on actual usage
kubectl patch deployment mcp-research -n sophia -p '{"spec":{"template":{"spec":{"containers":[{"name":"mcp-research","resources":{"requests":{"cpu":"1500m"}}}]}}}}'
```

### Memory Optimization
```bash
# Monitor memory usage trends
kubectl top pods -n sophia --sort-by=memory

# Set appropriate memory limits to prevent OOM
kubectl patch deployment sonic-ai -n sophia -p '{"spec":{"template":{"spec":{"containers":[{"name":"sonic-ai","resources":{"limits":{"memory":"16Gi"}}}]}}}}'
```

### Network Optimization
```bash
# Monitor network usage
kubectl exec -it deployment/mcp-research -n sophia -- netstat -i

# Optimize service-to-service communication
kubectl get networkpolicies -n sophia
```

### Database Optimization
```bash
# Monitor Redis performance
kubectl exec -it deployment/redis -n sophia -- redis-cli info stats

# Optimize Redis configuration
kubectl exec -it deployment/redis -n sophia -- redis-cli config set maxmemory-policy allkeys-lru
```

## Contact Information

### Emergency Contacts
- **Primary On-Call**: Available 24/7
- **System Administrator**: Lambda Labs support
- **Development Team**: GitHub issues for non-urgent matters

### Escalation Procedures
1. **Level 1**: Automated alerts and basic troubleshooting
2. **Level 2**: Manual intervention and service restarts
3. **Level 3**: Emergency procedures and disaster recovery
4. **Level 4**: External vendor support (Lambda Labs)

---
*This runbook is maintained by the Sophia AI operations team. Last updated: $(date)*