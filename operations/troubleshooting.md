# Sophia AI Operations Troubleshooting Guide

This guide provides solutions for common deployment and operational issues in the Sophia AI infrastructure.

## Table of Contents

- [Deployment Failures](#deployment-failures)
- [Service Health Issues](#service-health-issues)
- [Database Problems](#database-problems)
- [Network Connectivity](#network-connectivity)
- [Resource Constraints](#resource-constraints)
- [Monitoring & Alerting](#monitoring--alerting)
- [Emergency Procedures](#emergency-procedures)

## Deployment Failures

### Issue: Canary Deployment Health Check Fails

**Symptoms:**
- Pipeline fails at canary-deploy job
- Services show red/yellow status in validation
- Error: "CANARY VALIDATION FAILED"

**Causes:**
- Service startup timeout
- Health check endpoint not responding
- Resource constraints in canary namespace
- Configuration errors

**Solutions:**

1. **Check pod status:**
   ```bash
   kubectl get pods -n sophia-canary -o wide
   kubectl describe pod <pod-name> -n sophia-canary
   ```

2. **Check service logs:**
   ```bash
   kubectl logs <pod-name> -n sophia-canary --tail=100
   ```

3. **Verify health endpoints:**
   ```bash
   kubectl port-forward <pod-name> 8080:8080 -n sophia-canary
   curl http://localhost:8080/health
   ```

4. **Check resource usage:**
   ```bash
   kubectl top pods -n sophia-canary
   ```

5. **Restart canary deployment:**
   ```bash
   kubectl rollout restart deployment -n sophia-canary
   ```

### Issue: Database Migration Fails

**Symptoms:**
- Pipeline fails at migrate-neon job
- Error: "Migration failed" or "Connection timeout"
- Neon database shows connection errors

**Causes:**
- Network connectivity issues
- Invalid credentials
- Schema conflicts
- Migration script errors

**Solutions:**

1. **Test database connection:**
   ```bash
   # Try SNI connection
   PGSSLMODE=require psql -h rough-union-72390895.us-east-1.aws.neon.tech \
     -U neondb_owner -d neondb -c "SELECT 1;"

   # Try endpoint fallback
   PGSSLMODE=require psql -h pg.neon.tech \
     -U neondb_owner -d neondb \
     --options=endpoint=ep-rough-dew-af6w48m3 -c "SELECT 1;"
   ```

2. **Check migration script syntax:**
   ```bash
   psql -f ops/sql/001_audit.sql --dry-run
   ```

3. **Verify database permissions:**
   ```sql
   SELECT current_user, current_database();
   SELECT * FROM information_schema.role_table_grants WHERE grantee = current_user;
   ```

4. **Check existing schema:**
   ```sql
   \dt
   SELECT * FROM audit_log LIMIT 1;
   ```

5. **Manual migration:**
   ```bash
   PGSSLMODE=require psql -h pg.neon.tech \
     -U neondb_owner -d neondb \
     --options=endpoint=ep-rough-dew-af6w48m3 \
     -f ops/sql/001_audit.sql
   ```

### Issue: Synthetic Tests Fail

**Symptoms:**
- Pipeline fails at synthetics job
- Error: "SYNTHETIC CHECKS FAILED"
- Individual test failures (Slack/CRM/Database)

**Causes:**
- External service authentication issues
- Network timeouts
- API changes in external services
- Configuration mismatches

**Solutions:**

#### Slack Post Test Failure
```bash
# Test Slack webhook directly
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-type: application/json' \
  -d '{"text":"Test message from troubleshooting"}'
```

#### CRM Task Creation Failure
```bash
# Check CRM API connectivity
curl -H "Authorization: Bearer $CRM_TOKEN" \
  https://api.crm-service.com/health
```

#### Database Query Failure
```bash
# Test analytics-mcp directly
kubectl port-forward svc/analytics-mcp 8080:8080 -n sophia
curl -X POST http://localhost:8080/query/neon \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1", "database": "neondb"}'
```

### Issue: Full Rollout Fails

**Symptoms:**
- Pipeline fails at full-rollout job
- Services fail to start in production
- Traffic migration issues

**Causes:**
- Resource constraints
- Configuration differences
- Service dependencies not ready

**Solutions:**

1. **Check rollout status:**
   ```bash
   kubectl rollout status deployment -n sophia
   ```

2. **Verify service dependencies:**
   ```bash
   kubectl get pods -n sophia -o wide
   kubectl get services -n sophia
   ```

3. **Check Istio configuration:**
   ```bash
   kubectl get virtualservice -n sophia
   kubectl describe virtualservice sophia-production -n sophia
   ```

4. **Manual traffic migration:**
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: networking.istio.io/v1beta1
   kind: VirtualService
   metadata:
     name: sophia-production
     namespace: sophia
   spec:
     http:
     - route:
       - destination:
           host: mcp-research.sophia.svc.cluster.local
         weight: 100
   EOF
   ```

## Service Health Issues

### Issue: Service Shows Red Status

**Symptoms:**
- Service health endpoint returns errors
- Pod restarts frequently
- High error rates in logs

**Solutions:**

1. **Check pod events:**
   ```bash
   kubectl describe pod <pod-name> -n sophia
   ```

2. **Check service logs:**
   ```bash
   kubectl logs <pod-name> -n sophia --tail=100 -f
   ```

3. **Check resource usage:**
   ```bash
   kubectl top pods -n sophia
   kubectl describe node
   ```

4. **Restart service:**
   ```bash
   kubectl rollout restart deployment <service-name> -n sophia
   ```

5. **Scale service:**
   ```bash
   kubectl scale deployment <service-name> --replicas=0 -n sophia
   kubectl scale deployment <service-name> --replicas=3 -n sophia
   ```

### Issue: Service Shows Yellow Status

**Symptoms:**
- Service is starting but not fully ready
- Intermittent failures
- Slow response times

**Solutions:**

1. **Check readiness probes:**
   ```bash
   kubectl describe deployment <service-name> -n sophia
   ```

2. **Check startup logs:**
   ```bash
   kubectl logs <pod-name> -n sophia --tail=200
   ```

3. **Verify dependencies:**
   ```bash
   # Check database connectivity
   kubectl exec <pod-name> -n sophia -- nc -zv neon-host 5432

   # Check service mesh
   kubectl get envoyconfigdump -n sophia
   ```

## Database Problems

### Issue: Connection Pool Exhausted

**Symptoms:**
- Database connection errors
- Service timeouts
- High latency

**Solutions:**

1. **Check connection count:**
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE datname = 'neondb';
   ```

2. **Monitor connection pool:**
   ```bash
   # Check Neon metrics
   curl https://console.neon.tech/api/v1/projects/rough-union-72390895/endpoints/ep-rough-dew-af6w48m3/metrics
   ```

3. **Restart services to clear connections:**
   ```bash
   kubectl rollout restart deployment -n sophia
   ```

4. **Check for connection leaks in application code**

### Issue: Database Query Timeout

**Symptoms:**
- Slow queries
- Timeout errors
- High CPU usage on database

**Solutions:**

1. **Identify slow queries:**
   ```sql
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

2. **Check query plan:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM your_table WHERE condition;
   ```

3. **Add database indexes:**
   ```sql
   CREATE INDEX CONCURRENTLY idx_table_column ON table_name (column_name);
   ```

4. **Optimize connection settings**

## Network Connectivity

### Issue: Service-to-Service Communication Fails

**Symptoms:**
- Inter-service calls fail
- DNS resolution errors
- Network timeouts

**Solutions:**

1. **Check DNS resolution:**
   ```bash
   kubectl exec <pod-name> -n sophia -- nslookup mcp-research.sophia.svc.cluster.local
   ```

2. **Check network policies:**
   ```bash
   kubectl get networkpolicies -n sophia
   kubectl describe networkpolicy <policy-name> -n sophia
   ```

3. **Check service mesh configuration:**
   ```bash
   kubectl get virtualservice -n sophia
   kubectl get destinationrule -n sophia
   ```

4. **Test connectivity:**
   ```bash
   kubectl exec <pod-name> -n sophia -- curl http://mcp-research.sophia.svc.cluster.local:8080/health
   ```

### Issue: External Service Connectivity Fails

**Symptoms:**
- Calls to external APIs fail
- DNS resolution fails for external domains
- SSL/TLS errors

**Solutions:**

1. **Check egress configuration:**
   ```bash
   kubectl get istiooperator -n istio-system
   kubectl get serviceentry -n sophia
   ```

2. **Test external connectivity:**
   ```bash
   kubectl exec <pod-name> -n sophia -- curl -v https://api.slack.com
   ```

3. **Check SSL certificates:**
   ```bash
   kubectl exec <pod-name> -n sophia -- openssl s_client -connect api.slack.com:443
   ```

## Resource Constraints

### Issue: Pod Eviction Due to Resource Pressure

**Symptoms:**
- Pods evicted from nodes
- Out of memory errors
- CPU throttling

**Solutions:**

1. **Check node resources:**
   ```bash
   kubectl describe nodes
   kubectl top nodes
   ```

2. **Check pod resource usage:**
   ```bash
   kubectl top pods -n sophia
   ```

3. **Update resource requests/limits:**
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "100m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

4. **Scale cluster nodes if needed**

### Issue: Storage Issues

**Symptoms:**
- Pod crashes due to storage
- Volume mount errors
- Disk space warnings

**Solutions:**

1. **Check persistent volumes:**
   ```bash
   kubectl get pv,pvc -n sophia
   kubectl describe pvc <pvc-name> -n sophia
   ```

2. **Check storage class:**
   ```bash
   kubectl get storageclass
   kubectl describe storageclass <class-name>
   ```

3. **Monitor disk usage:**
   ```bash
   kubectl exec <pod-name> -n sophia -- df -h
   ```

## Monitoring & Alerting

### Issue: Monitoring Stack Not Working

**Symptoms:**
- Grafana/Prometheus not accessible
- Missing metrics
- Alerting not working

**Solutions:**

1. **Check monitoring pods:**
   ```bash
   kubectl get pods -n monitoring
   kubectl logs <monitoring-pod> -n monitoring
   ```

2. **Check service discovery:**
   ```bash
   kubectl get servicemonitors -n sophia
   kubectl describe servicemonitor <monitor-name> -n sophia
   ```

3. **Restart monitoring stack:**
   ```bash
   kubectl rollout restart deployment -n monitoring
   ```

### Issue: Alerts Not Firing

**Symptoms:**
- No alerts received
- Alertmanager not working
- Slack notifications missing

**Solutions:**

1. **Check alertmanager configuration:**
   ```bash
   kubectl get secrets -n monitoring
   kubectl describe secret alertmanager-main -n monitoring
   ```

2. **Test alert firing:**
   ```bash
   kubectl port-forward svc/alertmanager-main 9093:9093 -n monitoring
   curl -X POST http://localhost:9093/api/v1/alerts \
     -H "Content-Type: application/json" \
     -d '[{"labels":{"alertname":"TestAlert"},"annotations":{"summary":"Test"}}]'
   ```

3. **Check Slack webhook:**
   ```bash
   curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
     -H 'Content-type: application/json' \
     -d '{"text":"Test alert from troubleshooting"}'
   ```

## Emergency Procedures

### Emergency Rollback

**When to use:** Critical production issues requiring immediate rollback

**Procedure:**
```bash
# 1. Stop the pipeline
# 2. Rollback services
kubectl rollout undo deployment/mcp-research -n sophia
kubectl rollout undo deployment/mcp-context -n sophia
kubectl rollout undo deployment/comms-mcp -n sophia
kubectl rollout undo deployment/crm-mcp -n sophia
kubectl rollout undo deployment/analytics-mcp -n sophia

# 3. Restore traffic to previous version
kubectl apply -f k8s-deploy/manifests/traffic-previous.yaml

# 4. Restore database if needed
PGSSLMODE=require pg_restore -h pg.neon.tech \
  -U neondb_owner -d neondb \
  --options=endpoint=ep-rough-dew-af6w48m3 \
  /path/to/backup.sql

# 5. Notify stakeholders
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
  -H 'Content-type: application/json' \
  -d '{"text":"🚨 EMERGENCY ROLLBACK EXECUTED"}'
```

### Database Emergency Recovery

**When to use:** Database corruption or data loss

**Procedure:**
```bash
# 1. Stop all database connections
kubectl scale deployment -l app=analytics --replicas=0 -n sophia

# 2. Create emergency backup
PGSSLMODE=require pg_dump -h pg.neon.tech \
  -U neondb_owner -d neondb \
  --options=endpoint=ep-rough-dew-af6w48m3 \
  > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from backup
PGSSLMODE=require psql -h pg.neon.tech \
  -U neondb_owner -d neondb \
  --options=endpoint=ep-rough-dew-af6w48m3 \
  -f /path/to/backup.sql

# 4. Restart services
kubectl scale deployment -l app=analytics --replicas=3 -n sophia
```

### Complete Infrastructure Reset

**When to use:** Multiple service failures or infrastructure corruption

**Procedure:**
```bash
# 1. Scale down all services
kubectl scale deployment --all --replicas=0 -n sophia

# 2. Clean up resources
kubectl delete pods --all -n sophia --force --grace-period=0

# 3. Reset database connections
# (Contact Neon support for connection pool reset)

# 4. Restart services one by one
kubectl scale deployment mcp-research --replicas=3 -n sophia
kubectl wait --for=condition=available deployment/mcp-research -n sophia

kubectl scale deployment mcp-context --replicas=3 -n sophia
kubectl wait --for=condition=available deployment/mcp-context -n sophia

# Continue with other services...
```

## Diagnostic Commands

### Quick Health Check
```bash
# Overall cluster health
kubectl get nodes
kubectl get pods -n sophia
kubectl get services -n sophia

# Service-specific checks
for svc in mcp-research mcp-context comms-mcp crm-mcp analytics-mcp; do
  echo "=== $svc ==="
  kubectl get pods -l app=$svc -n sophia
  kubectl logs -l app=$svc -n sophia --tail=5
done
```

### Performance Monitoring
```bash
# Resource usage
kubectl top nodes
kubectl top pods -n sophia

# Network traffic
kubectl get virtualservice -n sophia
kubectl get destinationrule -n sophia
```

### Log Aggregation
```bash
# Get recent errors from all services
kubectl logs -n sophia --selector=app --tail=100 | grep -i error

# Get specific service logs
kubectl logs -f deployment/mcp-research -n sophia --tail=50
```

## Contact Information

- **System Administrator**: Available 24/7
- **Database Team**: Neon support team
- **Network Team**: Infrastructure team
- **Application Team**: Development team

## Prevention Measures

1. **Regular Backups**: Daily database backups
2. **Load Testing**: Before major deployments
3. **Monitoring**: 24/7 monitoring and alerting
4. **Documentation**: Keep runbooks updated
5. **Testing**: Comprehensive test coverage
6. **Reviews**: Code and deployment reviews

---

*This guide is continuously updated. Please contribute improvements and new solutions.*