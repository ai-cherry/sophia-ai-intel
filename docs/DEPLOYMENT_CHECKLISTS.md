# Sophia AI - Deployment Checklists

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Deployment Checklist](#production-deployment-checklist)
3. [Staging Deployment Checklist](#staging-deployment-checklist)
4. [Rollback Checklist](#rollback-checklist)
5. [Post-Deployment Validation](#post-deployment-validation)
6. [Environment-Specific Considerations](#environment-specific-considerations)

## Pre-Deployment Checklist

### Planning and Preparation
- [ ] **Release notes prepared** - Document all changes, features, and fixes
- [ ] **Backup verification** - Confirm recent backups are available and tested
- [ ] **Change approval** - Obtain necessary approvals for production changes
- [ ] **Maintenance window scheduled** - Coordinate with stakeholders
- [ ] **Team availability** - Ensure key personnel are available during deployment
- [ ] **Rollback plan prepared** - Define rollback procedures and criteria

### Code and Configuration Review
- [ ] **Code review completed** - All changes peer-reviewed and approved
- [ ] **CI/CD pipeline passing** - All automated tests successful
- [ ] **Security scan passed** - Vulnerability scanning completed
- [ ] **Performance testing** - Load testing results meet acceptance criteria
- [ ] **Configuration validation** - Environment-specific configs reviewed
- [ ] **Secret management** - Verify all secrets are properly managed

### Infrastructure Readiness
- [ ] **Kubernetes cluster healthy** - All nodes ready and resources available
- [ ] **Storage availability** - Persistent volumes and storage capacity confirmed
- [ ] **Network connectivity** - External dependencies and APIs accessible
- [ ] **DNS configuration** - Domain records and SSL certificates valid
- [ ] **Monitoring systems** - Prometheus, Grafana, and alerting operational
- [ ] **Log aggregation** - Loki and logging pipeline functional

## Production Deployment Checklist

### Phase 1: Pre-deployment Validation (T-30 minutes)
- [ ] **System health check** - All services running and healthy
  ```bash
  kubectl get pods -n sophia --sort-by='.status.phase'
  ./k8s-deploy/scripts/comprehensive-health-check.sh
  ```

- [ ] **Resource utilization review** - Check current system load
  ```bash
  kubectl top pods -n sophia
  kubectl top nodes
  ```

- [ ] **Backup current state** - Create deployment-specific backup
  ```bash
  kubectl get all,configmaps,secrets -n sophia -o yaml > backup/pre-deployment-$(date +%Y%m%d-%H%M%S).yaml
  ```

- [ ] **Communication sent** - Notify stakeholders of deployment start

### Phase 2: Container Image Build and Push (T-20 minutes)
- [ ] **Build images for all services**
  - [ ] mcp-research: `ghcr.io/[repo]/sophia-mcp-research:v1.1.0`
  - [ ] mcp-context: `ghcr.io/[repo]/sophia-mcp-context:v1.1.0`
  - [ ] mcp-agents: `ghcr.io/[repo]/sophia-mcp-agents:v1.1.0`
  - [ ] sophia-dashboard: `ghcr.io/[repo]/sophia-dashboard:v1.1.0`
  - [ ] sophia-business: `ghcr.io/[repo]/sophia-business:v1.1.0`
  - [ ] sophia-hubspot: `ghcr.io/[repo]/sophia-hubspot:v1.1.0`
  - [ ] sophia-github: `ghcr.io/[repo]/sophia-github:v1.1.0`
  - [ ] sophia-lambda: `ghcr.io/[repo]/sophia-lambda:v1.1.0`
  - [ ] mcp-business: `ghcr.io/[repo]/sophia-mcp-business:v1.1.0`

- [ ] **Image security scanning** - Verify no critical vulnerabilities
- [ ] **Image registry push** - All images successfully pushed to GitHub Container Registry

### Phase 3: Infrastructure Preparation (T-15 minutes)
- [ ] **Update configurations**
  ```bash
  kubectl apply -f k8s-deploy/manifests/configmap-production.yaml
  kubectl apply -f k8s-deploy/secrets/
  ```

- [ ] **Network policies updated**
  ```bash
  kubectl apply -f k8s-deploy/manifests/network-policies.yaml
  ```

- [ ] **RBAC and security**
  ```bash
  kubectl apply -f k8s-deploy/manifests/rbac.yaml
  kubectl apply -f k8s-deploy/manifests/cert-manager.yaml
  ```

### Phase 4: Core Service Deployment (T-10 minutes)
- [ ] **Deploy Redis (cache/session store)**
  ```bash
  kubectl apply -f k8s-deploy/manifests/redis.yaml
  kubectl wait --for=condition=available --timeout=120s deployment/redis -n sophia
  ```

- [ ] **Deploy MCP services (core functionality)**
  ```bash
  kubectl apply -f k8s-deploy/manifests/mcp-research.yaml
  kubectl apply -f k8s-deploy/manifests/mcp-context.yaml
  kubectl apply -f k8s-deploy/manifests/mcp-agents.yaml
  
  kubectl wait --for=condition=available --timeout=300s deployment/mcp-research -n sophia
  kubectl wait --for=condition=available --timeout=300s deployment/mcp-context -n sophia
  kubectl wait --for=condition=available --timeout=300s deployment/mcp-agents -n sophia
  ```

### Phase 5: Business Services Deployment (T-5 minutes)
- [ ] **Deploy dashboard and business logic**
  ```bash
  kubectl apply -f k8s-deploy/manifests/sophia-dashboard.yaml
  kubectl apply -f k8s-deploy/manifests/sophia-business.yaml
  
  kubectl wait --for=condition=available --timeout=300s deployment/sophia-dashboard -n sophia
  kubectl wait --for=condition=available --timeout=300s deployment/sophia-business -n sophia
  ```

### Phase 6: Integration Services Deployment (T-0 minutes)
- [ ] **Deploy integration services**
  ```bash
  kubectl apply -f k8s-deploy/manifests/sophia-hubspot.yaml
  kubectl apply -f k8s-deploy/manifests/sophia-github.yaml
  kubectl apply -f k8s-deploy/manifests/sophia-lambda.yaml
  
  kubectl wait --for=condition=available --timeout=180s deployment/sophia-hubspot -n sophia
  kubectl wait --for=condition=available --timeout=180s deployment/sophia-github -n sophia
  kubectl wait --for=condition=available --timeout=180s deployment/sophia-lambda -n sophia
  ```

- [ ] **Deploy MCP Business service**
  ```bash
  kubectl apply -f k8s-deploy/manifests/mcp-business.yaml
  kubectl wait --for=condition=available --timeout=300s deployment/mcp-business -n sophia
  ```

### Phase 7: Networking and Monitoring (T+5 minutes)
- [ ] **Deploy ingress and networking**
  ```bash
  kubectl apply -f k8s-deploy/manifests/ingress-enhanced-ssl.yaml
  kubectl apply -f k8s-deploy/manifests/hpa.yaml
  ```

- [ ] **Deploy monitoring stack**
  ```bash
  kubectl apply -f k8s-deploy/manifests/prometheus.yaml
  kubectl apply -f k8s-deploy/manifests/grafana.yaml
  kubectl apply -f k8s-deploy/manifests/loki.yaml
  kubectl apply -f k8s-deploy/manifests/advanced-alerts.yaml
  
  kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n sophia
  kubectl wait --for=condition=available --timeout=300s deployment/grafana -n sophia
  ```

## Staging Deployment Checklist

### Pre-Staging Validation
- [ ] **Staging environment clean** - Remove previous test data
- [ ] **Resource allocation** - Ensure adequate resources for staging
- [ ] **Test data prepared** - Load representative test datasets
- [ ] **External dependencies** - Configure staging-specific integrations

### Staging Deployment Steps
- [ ] **Deploy to staging namespace**
  ```bash
  kubectl create namespace sophia-staging --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -f k8s-deploy/manifests/ -n sophia-staging
  ```

- [ ] **Configure staging-specific settings**
  ```bash
  kubectl apply -f k8s-deploy/manifests/configmap-staging.yaml
  ```

- [ ] **Validate staging deployment**
  ```bash
  kubectl get pods -n sophia-staging
  ./scripts/test_complete_integration.py --environment=staging
  ```

### Staging Testing Checklist
- [ ] **Functional testing** - Core features work as expected
- [ ] **Integration testing** - External API integrations functional
- [ ] **Performance testing** - Load testing within acceptable parameters
- [ ] **Security testing** - Authentication and authorization working
- [ ] **User acceptance testing** - Business stakeholder sign-off
- [ ] **Regression testing** - Previously working features still function

## Rollback Checklist

### Immediate Rollback (< 5 minutes)
- [ ] **Stop current deployment**
  ```bash
  kubectl rollout pause deployment/[service-name] -n sophia
  ```

- [ ] **Rollback to previous version**
  ```bash
  kubectl rollout undo deployment/[service-name] -n sophia
  kubectl rollout status deployment/[service-name] -n sophia --timeout=300s
  ```

- [ ] **Verify rollback success**
  ```bash
  curl -f http://192.222.51.223/[service]/health
  kubectl get pods -n sophia | grep [service-name]
  ```

### Complete System Rollback (< 15 minutes)
- [ ] **Rollback all services in reverse dependency order**
  ```bash
  # Rollback in reverse order
  kubectl rollout undo deployment/sonic-ai -n sophia
  kubectl rollout undo deployment/sophia-lambda -n sophia
  kubectl rollout undo deployment/sophia-github -n sophia
  kubectl rollout undo deployment/sophia-hubspot -n sophia
  kubectl rollout undo deployment/sophia-business -n sophia
  kubectl rollout undo deployment/sophia-dashboard -n sophia
  kubectl rollout undo deployment/mcp-agents -n sophia
  kubectl rollout undo deployment/mcp-context -n sophia
  kubectl rollout undo deployment/mcp-research -n sophia
  ```

- [ ] **Restore previous configuration**
  ```bash
  kubectl apply -f backup/pre-deployment-[timestamp].yaml
  ```

- [ ] **Verify system stability**
  ```bash
  ./k8s-deploy/scripts/comprehensive-health-check.sh
  ./scripts/test_complete_integration.py
  ```

## Post-Deployment Validation

### Immediate Validation (T+10 minutes)
- [ ] **Service health checks** - All services responding to health endpoints
  ```bash
  for service in mcp-research mcp-context mcp-agents sophia-dashboard sophia-business sonic-ai; do
    echo "Checking $service health..."
    curl -f http://192.222.51.223/$service/health || echo "$service health check failed"
  done
  ```

- [ ] **Database connectivity** - All services can connect to Redis
  ```bash
  kubectl exec -n sophia deployment/mcp-research -- redis-cli -h redis ping
  ```

- [ ] **External API connectivity** - Integration services can reach external APIs
  ```bash
  kubectl exec -n sophia deployment/sophia-github -- curl -I https://api.github.com
  kubectl exec -n sophia deployment/sophia-hubspot -- curl -I https://api.hubapi.com
  ```

### Extended Validation (T+30 minutes)
- [ ] **Load testing** - Performance meets baseline requirements
  ```bash
  cd scripts/load_testing
  python comprehensive_load_test.py --url=http://192.222.51.223 --duration=300
  ```

- [ ] **Integration testing** - End-to-end workflows functional
  ```bash
  python scripts/test_complete_integration.py --environment=production
  ```

- [ ] **Monitoring validation** - Metrics collection and alerting operational
  ```bash
  curl -f http://192.222.51.223:9090/-/healthy
  curl -f http://192.222.51.223:3000/api/health
  ```

### Business Validation (T+60 minutes)
- [ ] **User workflows** - Critical business processes tested
- [ ] **Dashboard functionality** - UI responds correctly
- [ ] **Data consistency** - Verify data integrity across services
- [ ] **External integrations** - HubSpot, GitHub, and other APIs functional
- [ ] **Performance metrics** - Response times within acceptable ranges

## Environment-Specific Considerations

### Production Environment
- **Deployment Window**: Off-peak hours (typically 2-6 AM UTC)
- **Approval Required**: Change management approval
- **Notification**: Stakeholders, customers (if applicable)
- **Monitoring**: Enhanced alerting during deployment
- **Rollback Criteria**: >5% error rate or >2s average response time

### Staging Environment
- **Deployment Window**: Any time during business hours
- **Approval Required**: Technical lead approval
- **Notification**: Development team only
- **Monitoring**: Basic health checks
- **Rollback Criteria**: Any functional failure

### Development Environment
- **Deployment Window**: Any time
- **Approval Required**: Self-service
- **Notification**: Developer only
- **Monitoring**: Basic health checks
- **Rollback Criteria**: Developer discretion

## Emergency Procedures

### Critical System Failure During Deployment
1. **Immediate Response**
   ```bash
   # Stop all deployments
   kubectl get deployments -n sophia -o name | xargs -I {} kubectl rollout pause {}
   ```

2. **Assess Impact**
   ```bash
   kubectl get events -n sophia --sort-by='.lastTimestamp' | tail -20
   kubectl logs -n sophia --selector=app --tail=100 | grep -i error
   ```

3. **Execute Rollback**
   ```bash
   # Use rollback checklist above
   ```

4. **Incident Communication**
   - Notify incident response team
   - Update status page
   - Prepare stakeholder communication

### Partial Service Failure
1. **Isolate Failed Service**
   ```bash
   kubectl scale deployment/[failed-service] --replicas=0 -n sophia
   ```

2. **Route Traffic Around Failure**
   ```bash
   kubectl patch service [failed-service] -n sophia -p '{"spec":{"selector":{"app":"maintenance"}}}'
   ```

3. **Investigate and Fix**
   - Review logs and metrics
   - Identify root cause
   - Apply targeted fix

4. **Gradual Recovery**
   ```bash
   kubectl scale deployment/[fixed-service] --replicas=1 -n sophia
   # Monitor and scale up gradually
   ```

---

**Document Version**: 1.1.0  
**Last Updated**: August 2025  
**Next Review**: November 2025  
**Owner**: Sophia AI Operations Team