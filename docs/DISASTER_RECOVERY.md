# Sophia AI - Disaster Recovery Plan

## Table of Contents
1. [Overview](#overview)
2. [Recovery Time Objectives](#recovery-time-objectives)
3. [Backup Procedures](#backup-procedures)
4. [Recovery Procedures](#recovery-procedures)
5. [Data Recovery](#data-recovery)
6. [Infrastructure Recovery](#infrastructure-recovery)
7. [Communication Plan](#communication-plan)
8. [Testing and Validation](#testing-and-validation)

## Overview

### Disaster Recovery Objectives
- **RTO (Recovery Time Objective)**: 30 minutes for critical services
- **RPO (Recovery Point Objective)**: 15 minutes maximum data loss
- **Service Priority**: Core MCP services > Dashboard > Integration services
- **Infrastructure**: Lambda Labs + K3s Kubernetes cluster

### Disaster Scenarios
1. **Complete infrastructure failure** (Lambda Labs outage)
2. **Kubernetes cluster failure** (K3s corruption)
3. **Service corruption or compromise** (Application-level failure)
4. **Data loss or corruption** (Database/storage failure)
5. **Network connectivity issues** (DNS/SSL/firewall problems)

## Recovery Time Objectives

### Service Priority Levels

#### Priority 1 (Critical) - RTO: 5-15 minutes
- **mcp-research**: Core research capabilities
- **mcp-context**: Context processing
- **mcp-agents**: Agent orchestration
- **Redis**: Session and cache storage
- **nginx**: Load balancer and ingress

#### Priority 2 (High) - RTO: 15-30 minutes
- **sophia-dashboard**: User interface
- **sophia-business**: Business intelligence
- **Prometheus**: Monitoring and alerting
- **Grafana**: Visualization

#### Priority 3 (Medium) - RTO: 30-60 minutes
- **sophia-hubspot**: HubSpot integration
- **sophia-github**: GitHub integration
- **sophia-lambda**: Infrastructure integration
- **sonic-ai**: AI processing (if not GPU-critical)

#### Priority 4 (Low) - RTO: 1-4 hours
- **Loki**: Log aggregation
- **Additional monitoring**: Advanced metrics
- **Non-critical integrations**

## Backup Procedures

### Automated Backup Schedule

#### Daily Backups (02:00 UTC)
```bash
#!/bin/bash
# Daily backup script - /opt/sophia/scripts/daily-backup.sh

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DIR="/opt/sophia/backups/daily/${BACKUP_DATE}"
mkdir -p "${BACKUP_DIR}"

# Kubernetes configurations
kubectl get all,configmaps,secrets,ingress,networkpolicies -n sophia -o yaml > "${BACKUP_DIR}/k8s-resources.yaml"
kubectl get persistentvolumes,persistentvolumeclaims -o yaml > "${BACKUP_DIR}/storage.yaml"

# Application configurations
cp -r k8s-deploy/manifests/ "${BACKUP_DIR}/manifests/"
cp -r k8s-deploy/secrets/ "${BACKUP_DIR}/secrets/"

# Redis data backup
kubectl exec -n sophia deployment/redis -- redis-cli --rdb /data/backup-${BACKUP_DATE}.rdb
kubectl cp sophia/redis-[pod]:/data/backup-${BACKUP_DATE}.rdb "${BACKUP_DIR}/redis-backup.rdb"

# Application logs (last 24h)
kubectl logs -n sophia --all-containers --since=24h > "${BACKUP_DIR}/application-logs.txt"

# Monitoring data (Prometheus)
kubectl exec -n sophia deployment/prometheus -- tar czf /prometheus/backup-${BACKUP_DATE}.tar.gz /prometheus/data/
kubectl cp sophia/prometheus-[pod]:/prometheus/backup-${BACKUP_DATE}.tar.gz "${BACKUP_DIR}/prometheus-backup.tar.gz"

# Clean up old backups (keep 30 days)
find /opt/sophia/backups/daily/ -type d -mtime +30 -exec rm -rf {} \;

echo "Daily backup completed: ${BACKUP_DIR}"
```

#### Weekly Backups (Sunday 01:00 UTC)
```bash
#!/bin/bash
# Weekly backup script - /opt/sophia/scripts/weekly-backup.sh

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DIR="/opt/sophia/backups/weekly/${BACKUP_DATE}"
mkdir -p "${BACKUP_DIR}"

# Full system state backup
kubectl cluster-info dump --output-directory="${BACKUP_DIR}/cluster-dump"

# Complete container image backup
docker save $(docker images --format "{{.Repository}}:{{.Tag}}" | grep sophia) -o "${BACKUP_DIR}/images.tar"

# Infrastructure configuration
cp -r ops/ "${BACKUP_DIR}/infrastructure/"
cp -r scripts/ "${BACKUP_DIR}/scripts/"
cp -r docs/ "${BACKUP_DIR}/documentation/"

# SSL certificates and keys
kubectl get secrets -n sophia -o yaml | grep -A 10 "type: kubernetes.io/tls" > "${BACKUP_DIR}/tls-certificates.yaml"

echo "Weekly backup completed: ${BACKUP_DIR}"
```

### Backup Verification
```bash
#!/bin/bash
# Backup verification script

verify_backup() {
    local backup_dir="$1"
    
    # Verify YAML files are valid
    kubectl apply --dry-run=client -f "${backup_dir}/k8s-resources.yaml"
    
    # Verify Redis backup integrity
    redis-check-rdb "${backup_dir}/redis-backup.rdb"
    
    # Verify container images
    docker load -i "${backup_dir}/images.tar" --dry-run || echo "Image backup verification failed"
    
    # Check backup file sizes
    find "${backup_dir}" -size 0 -name "*.yaml" -o -name "*.rdb" -o -name "*.tar*" | while read empty_file; do
        echo "WARNING: Empty backup file found: ${empty_file}"
    done
}
```

## Recovery Procedures

### Quick Recovery Checklist

#### Immediate Response (0-5 minutes)
1. **Assess the situation**
   ```bash
   # Check cluster status
   kubectl cluster-info
   kubectl get nodes
   kubectl get pods -n sophia --sort-by='.status.phase'
   ```

2. **Identify failed components**
   ```bash
   # Check failing services
   kubectl get pods -n sophia | grep -v Running
   kubectl get events -n sophia --sort-by='.lastTimestamp'
   ```

3. **Emergency communication**
   ```bash
   # Notify stakeholders via automated alert
   echo "ALERT: Sophia AI disaster recovery initiated at $(date)" | mail -s "URGENT: Sophia AI System Recovery" ops-team@company.com
   ```

#### Service Recovery (5-30 minutes)

##### Scenario 1: Single Service Failure
```bash
# Restart failed service
kubectl rollout restart deployment/[failed-service] -n sophia

# Monitor recovery
kubectl rollout status deployment/[failed-service] -n sophia --timeout=300s

# Verify health
curl -f http://192.222.51.223/[service]/health
```

##### Scenario 2: Multiple Service Failure
```bash
# Restart in dependency order
kubectl rollout restart deployment/redis -n sophia
kubectl wait --for=condition=available --timeout=120s deployment/redis -n sophia

kubectl rollout restart deployment/mcp-research -n sophia
kubectl rollout restart deployment/mcp-context -n sophia
kubectl rollout restart deployment/mcp-agents -n sophia

kubectl wait --for=condition=available --timeout=300s deployment/mcp-research -n sophia
kubectl wait --for=condition=available --timeout=300s deployment/mcp-context -n sophia
kubectl wait --for=condition=available --timeout=300s deployment/mcp-agents -n sophia
```

##### Scenario 3: Kubernetes Cluster Failure
```bash
# SSH to Lambda Labs server
ssh -i ~/.ssh/sophia-prod ubuntu@192.222.51.223

# Restart K3s
sudo systemctl restart k3s
sudo systemctl status k3s

# Wait for cluster to be ready
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Restore from backup
LATEST_BACKUP=$(ls -t /opt/sophia/backups/daily/ | head -1)
kubectl apply -f "/opt/sophia/backups/daily/${LATEST_BACKUP}/k8s-resources.yaml"
```

## Data Recovery

### Redis Data Recovery
```bash
# Stop Redis service
kubectl scale deployment redis --replicas=0 -n sophia

# Restore from backup
BACKUP_DATE="20241125"  # Replace with actual date
kubectl cp "/opt/sophia/backups/daily/${BACKUP_DATE}/redis-backup.rdb" sophia/redis-0:/data/dump.rdb

# Restart Redis
kubectl scale deployment redis --replicas=1 -n sophia
kubectl wait --for=condition=available --timeout=120s deployment/redis -n sophia

# Verify data restoration
kubectl exec -n sophia deployment/redis -- redis-cli info keyspace
```

### Prometheus Data Recovery
```bash
# Stop Prometheus
kubectl scale deployment prometheus --replicas=0 -n sophia

# Restore metrics data
BACKUP_DATE="20241125"
kubectl cp "/opt/sophia/backups/daily/${BACKUP_DATE}/prometheus-backup.tar.gz" sophia/prometheus-0:/prometheus/restore.tar.gz
kubectl exec -n sophia deployment/prometheus -- tar xzf /prometheus/restore.tar.gz -C /prometheus/

# Restart Prometheus
kubectl scale deployment prometheus --replicas=1 -n sophia
kubectl wait --for=condition=available --timeout=180s deployment/prometheus -n sophia
```

### Configuration Recovery
```bash
# Restore ConfigMaps and Secrets
BACKUP_DATE="20241125"
kubectl delete configmaps --all -n sophia
kubectl delete secrets --all -n sophia

kubectl apply -f "/opt/sophia/backups/daily/${BACKUP_DATE}/k8s-resources.yaml"

# Restart all services to pick up new configurations
kubectl rollout restart deployment --all -n sophia
```

## Infrastructure Recovery

### Complete Infrastructure Rebuild

#### Step 1: Prepare New Environment
```bash
# SSH to new Lambda Labs instance (if original is destroyed)
ssh -i ~/.ssh/sophia-prod ubuntu@[NEW-IP]

# Install K3s
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# Install additional tools
sudo apt update && sudo apt install -y docker.io redis-tools postgresql-client
sudo systemctl enable docker
sudo systemctl start docker
```

#### Step 2: Restore Cluster Configuration
```bash
# Copy backup files to new server
scp -r /opt/sophia/backups/daily/[LATEST]/ ubuntu@[NEW-IP]:/tmp/restore/

# Restore namespace and RBAC
kubectl apply -f /tmp/restore/k8s-resources.yaml

# Restore storage
kubectl apply -f /tmp/restore/storage.yaml

# Wait for persistent volumes to be available
kubectl wait --for=condition=Available pvc --all -n sophia --timeout=300s
```

#### Step 3: Restore Services
```bash
# Restore in dependency order
kubectl apply -f /tmp/restore/manifests/redis.yaml
kubectl wait --for=condition=available --timeout=180s deployment/redis -n sophia

kubectl apply -f /tmp/restore/manifests/mcp-*.yaml
kubectl wait --for=condition=available --timeout=300s deployment/mcp-research -n sophia
kubectl wait --for=condition=available --timeout=300s deployment/mcp-context -n sophia
kubectl wait --for=condition=available --timeout=300s deployment/mcp-agents -n sophia

kubectl apply -f /tmp/restore/manifests/sophia-*.yaml
kubectl wait --for=condition=available --timeout=300s deployment/sophia-dashboard -n sophia

kubectl apply -f /tmp/restore/manifests/sonic-ai.yaml
kubectl apply -f /tmp/restore/manifests/monitoring/
```

#### Step 4: Update DNS and SSL
```bash
# Update DNS records to point to new IP
./scripts/configure_dns_token.sh [NEW-IP]

# Restore SSL certificates
kubectl apply -f /tmp/restore/secrets/tls-secrets.yaml

# Or request new certificates
kubectl apply -f k8s-deploy/manifests/cert-manager.yaml
```

### Network Recovery
```bash
# Check network connectivity
kubectl exec -n sophia deployment/mcp-research -- nslookup www.sophia-intel.ai
kubectl exec -n sophia deployment/mcp-research -- curl -I https://api.github.com

# Restore network policies
kubectl apply -f k8s-deploy/manifests/network-policies.yaml

# Verify service-to-service communication
kubectl exec -n sophia deployment/mcp-research -- wget -qO- http://redis:6379/ping
```

## Communication Plan

### Incident Response Team
- **Incident Commander**: Primary on-call engineer
- **Technical Lead**: Senior system administrator
- **Communications Lead**: Business stakeholder
- **Subject Matter Expert**: Service-specific expert

### Communication Channels
1. **Internal**: Slack #incidents channel
2. **Status Page**: Update system status page
3. **Customer Communication**: Email notification system
4. **Stakeholders**: Executive summary email

### Communication Templates

#### Initial Incident Notification
```
INCIDENT ALERT: Sophia AI System Issue Detected

Time: [TIMESTAMP]
Impact: [HIGH/MEDIUM/LOW]
Affected Services: [SERVICE_LIST]
Status: Investigation in progress

We are aware of an issue affecting [DESCRIPTION]. Our team is actively investigating and will provide updates every 15 minutes.

Next Update: [TIME]
Incident Commander: [NAME]
```

#### Recovery Progress Update
```
RECOVERY UPDATE: Sophia AI System Recovery in Progress

Time: [TIMESTAMP]
Status: Recovery initiated
Progress: [PERCENTAGE]% of services restored

Completed:
- [COMPLETED_ITEMS]

In Progress:
- [IN_PROGRESS_ITEMS]

Estimated Full Recovery: [TIME]
```

#### Incident Resolution
```
RESOLVED: Sophia AI System Fully Restored

Time: [TIMESTAMP]
Total Downtime: [DURATION]
Root Cause: [BRIEF_DESCRIPTION]

All services have been restored and are operating normally. A detailed post-mortem will be provided within 24 hours.

Thank you for your patience during this incident.
```

## Testing and Validation

### Monthly Disaster Recovery Tests

#### Test Scenario 1: Service Failure Simulation
```bash
#!/bin/bash
# Monthly DR test - Service failure simulation

echo "=== DR TEST: Service Failure Simulation ==="
echo "Test Date: $(date)"

# Simulate MCP service failure
kubectl scale deployment mcp-research --replicas=0 -n sophia
echo "Simulated mcp-research failure at $(date)"

# Wait 2 minutes
sleep 120

# Measure recovery time
START_TIME=$(date +%s)
kubectl scale deployment mcp-research --replicas=2 -n sophia
kubectl wait --for=condition=available --timeout=300s deployment/mcp-research -n sophia
END_TIME=$(date +%s)

RECOVERY_TIME=$((END_TIME - START_TIME))
echo "Recovery completed in ${RECOVERY_TIME} seconds"

# Validate service health
curl -f http://192.222.51.223/research/health || echo "Health check failed"

echo "=== DR TEST COMPLETED ==="
```

#### Test Scenario 2: Data Recovery Validation
```bash
#!/bin/bash
# Monthly DR test - Data recovery validation

echo "=== DR TEST: Data Recovery Simulation ==="

# Create test data
kubectl exec -n sophia deployment/redis -- redis-cli set "dr_test_key" "test_value_$(date +%s)"

# Backup current state
kubectl exec -n sophia deployment/redis -- redis-cli --rdb /data/dr_test_backup.rdb

# Simulate data corruption
kubectl exec -n sophia deployment/redis -- redis-cli flushall

# Restore from backup
kubectl exec -n sophia deployment/redis -- redis-cli --rdb /data/dr_test_backup.rdb
kubectl rollout restart deployment/redis -n sophia

# Validate data restoration
sleep 30
kubectl exec -n sophia deployment/redis -- redis-cli get "dr_test_key" | grep "test_value" || echo "Data recovery failed"

echo "=== DATA RECOVERY TEST COMPLETED ==="
```

### Quarterly Full DR Tests
1. **Complete infrastructure rebuild** in staging environment
2. **End-to-end service restoration** from backups
3. **Performance validation** after recovery
4. **Security verification** (certificates, secrets, network policies)
5. **Business continuity validation** (user workflows, integrations)

### DR Test Checklist
- [ ] All backups are accessible and valid
- [ ] Recovery procedures execute within RTO
- [ ] All services pass health checks after recovery
- [ ] Data integrity is maintained
- [ ] SSL certificates are valid
- [ ] Monitoring and alerting are functional
- [ ] External integrations are working
- [ ] Performance meets baseline requirements

---

**Document Version**: 1.1.0
**Last Updated**: August 2025
**Next Review**: November 2025
**Owner**: Sophia AI Operations Team