# 🚨 Disaster Recovery Guide

## Overview

This guide provides comprehensive procedures for recovering from critical incidents affecting the Sophia AI production environment. It covers immediate response actions, recovery procedures by severity level, and post-incident procedures.

## Critical Incident Response Plan

### Immediate Actions (Within 15 minutes)

1. **Service Outage Response**
   ```bash
   # Check service status
   kubectl get pods -n sophia --all-namespaces

   # Check node health
   kubectl get nodes

   # Check logs for immediate issues
   kubectl logs -n sophia deployment/sophia-api --tail=100
   ```

2. **Database Connectivity Issues**
   ```bash
   # Test database connection
   kubectl exec -it deployment/postgres -- psql -U sophia -d sophia -c "SELECT version();"

   # Check connection pool
   kubectl exec -it deployment/sophia-api -- nc -zv postgres 5432
   ```

3. **Redis Cache Failure**
   ```bash
   # Test Redis connectivity
   kubectl exec -it deployment/redis -- redis-cli ping

   # Check Redis memory usage
   kubectl exec -it deployment/redis -- redis-cli info memory
   ```

## Recovery Procedures by Severity

### 🟢 Low Severity - Single Service Failure

**Symptoms:**
- Individual microservice unresponsive
- Other services functioning normally
- No data loss

**Recovery Steps:**
```bash
# 1. Restart the failed service
kubectl rollout restart deployment/<service-name> -n sophia

# 2. Monitor recovery
kubectl get pods -n sophia -w

# 3. Check service health
curl https://api.sophia-intel.ai/health/<service-name>
```

### 🟡 Medium Severity - Multiple Service Failure

**Symptoms:**
- Multiple services affected
- Database/Redis still accessible
- Partial functionality loss

**Recovery Steps:**
```bash
# 1. Check cluster resource usage
kubectl top nodes
kubectl top pods -n sophia

# 2. Scale up resources if needed
kubectl scale deployment <service-name> --replicas=2 -n sophia

# 3. Restart affected services
kubectl rollout restart -n sophia deployment

# 4. Verify all services are healthy
./scripts/health-check.sh
```

### 🔴 High Severity - Infrastructure Failure

**Symptoms:**
- Multiple nodes down
- Database/Redis inaccessible
- Complete service outage
- Potential data loss

**Recovery Steps:**

1. **Immediate Assessment**
   ```bash
   # Check cluster status
   kubectl cluster-info
   kubectl get componentstatuses

   # Check persistent volumes
   kubectl get pv,pvc -n sophia
   ```

2. **Database Recovery**
   ```bash
   # If PostgreSQL is down, check backup status
   ./scripts/backup/restore-postgres.sh latest

   # Verify data integrity
   ./scripts/validate-database-integrity.sh
   ```

3. **Service Recovery**
   ```bash
   # Redeploy all services
   ./scripts/deploy-production-secure.sh --force

   # Verify service dependencies
   ./scripts/validate-service-dependencies.sh
   ```

4. **Data Recovery**
   ```bash
   # Restore from latest backup if data loss suspected
   ./scripts/backup/restore-full-system.sh --timestamp latest

   # Verify data consistency
   ./scripts/validate-data-consistency.sh
   ```

## Emergency Contacts & Escalation

**Primary Contacts:**
- DevOps Lead: devops@sophia-intel.ai
- Database Administrator: dba@sophia-intel.ai
- Security Team: security@sophia-intel.ai

**Escalation Path:**
1. **Level 1**: On-call engineer (15-minute response)
2. **Level 2**: DevOps team lead (30-minute response)
3. **Level 3**: Full incident response team (1-hour response)

## Automated Recovery Systems

### Circuit Breakers
- Services automatically isolate failing components
- Automatic failover to healthy instances
- Load shedding during high traffic

### Auto-scaling Response
```yaml
# Horizontal Pod Autoscaler configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sophia-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Automated Backups
- **Database**: Hourly backups, 30-day retention
- **Configuration**: Git-based version control
- **Logs**: 90-day retention with offsite backup

## Recovery Time Objectives (RTO) & Recovery Point Objectives (RPO)

| Service | RTO | RPO | Description |
|---------|-----|-----|-------------|
| Core API | 15 min | 1 hour | Primary business functionality |
| Database | 30 min | 5 min | Data persistence layer |
| Cache (Redis) | 5 min | 0 | In-memory data (reconstructible) |
| Monitoring | 10 min | 1 hour | Observability stack |
| External APIs | 60 min | N/A | Third-party integrations |

## Post-Incident Procedures

1. **Root Cause Analysis**
   ```bash
   # Collect incident data
   ./scripts/incident-data-collection.sh --incident-id <ID>

   # Analyze logs and metrics
   ./scripts/log-analysis.sh --time-range "1h ago"
   ```

2. **Documentation Update**
   - Update incident response runbook
   - Add new monitoring alerts if needed
   - Update recovery procedures based on lessons learned

3. **Team Debrief**
   - Conduct post-mortem meeting within 48 hours
   - Identify improvement opportunities
   - Implement preventive measures

## Backup and Restore Procedures

### Database Backup Strategy
```bash
# Automated hourly backups
0 * * * * ./scripts/backup/postgres-backup.sh

# Manual backup
./scripts/backup/postgres-backup.sh manual

# Restore from specific timestamp
./scripts/backup/restore-postgres.sh 2025-08-26_14:00:00
```

### Configuration Backup
```bash
# Backup Kubernetes configurations
kubectl get all -n sophia -o yaml > k8s-backup-$(date +%Y%m%d_%H%M%S).yaml

# Backup secrets (encrypted)
./scripts/backup/secrets-backup.sh
```

### Full System Restore
```bash
# Complete system restore from backup
./scripts/backup/full-system-restore.sh --backup-id latest

# Point-in-time recovery
./scripts/backup/full-system-restore.sh --timestamp 2025-08-26_14:00:00
```

## Monitoring and Alerting

### Critical Alerts Setup
- CPU usage > 85% for 5 minutes
- Memory usage > 90% for 3 minutes
- Disk usage > 85% for 10 minutes
- Service response time > 5 seconds for 2 minutes
- Error rate > 5% for 1 minute

### Health Check Endpoints
- `/health` - Overall system health
- `/health/database` - Database connectivity
- `/health/cache` - Redis connectivity
- `/health/services` - All microservices status

## Security Incident Response

### Data Breach Response
1. **Immediate Actions**
   - Isolate affected systems
   - Stop all external access
   - Notify security team

2. **Assessment**
   - Determine scope of breach
   - Identify compromised data
   - Assess impact to customers

3. **Recovery**
   - Rotate all credentials and secrets
   - Rebuild affected systems from clean backups
   - Implement additional security measures

### DDoS Attack Response
1. **Detection**
   - Monitor traffic patterns
   - Enable rate limiting
   - Scale up defensive resources

2. **Mitigation**
   - Enable Cloudflare protection
   - Implement IP blocking
   - Route traffic through scrubbing centers

## Testing Recovery Procedures

### Regular Testing Schedule
- **Monthly**: Individual service recovery testing
- **Quarterly**: Full system recovery testing
- **Annually**: Complete disaster recovery simulation

### Recovery Testing Checklist
- [ ] All backups are accessible and valid
- [ ] Recovery scripts are functional
- [ ] Team members know their roles
- [ ] Communication channels are tested
- [ ] Documentation is current

## Continuous Improvement

### Lessons Learned Process
1. **Incident Documentation**
   - Detailed timeline of events
   - Actions taken and their effectiveness
   - Root cause analysis

2. **Process Updates**
   - Update runbooks with new procedures
   - Implement preventive measures
   - Improve monitoring and alerting

3. **Training**
   - Regular training on new procedures
   - Tabletop exercises for major incidents
   - Cross-training between team members

---

**Last Updated:** August 26, 2025
**Version:** 1.0
**Review Date:** Every 6 months