# Production SLO & Monitoring Documentation

## Service Level Objectives (SLOs)

### Health Check SLO
- **Target**: 3 consecutive HTTP 200 responses within 90 seconds of deployment
- **Measurement Window**: Post-deployment verification period
- **Retry Policy**: Up to 8 attempts with progressive backoff (15-20 second intervals)
- **Failure Action**: Automatic rollback trigger

### Availability SLO
- **Target**: 99.9% uptime per service per month
- **Measurement**: Health endpoint availability over 30-day rolling window
- **Downtime Budget**: 43.8 minutes per month per service
- **Alerting Threshold**: 99.5% (early warning)

### Performance SLO
- **Health Endpoint Response Time**: < 500ms (95th percentile)
- **API Endpoint Response Time**: < 2000ms (95th percentile)
- **Search Operations**: < 5000ms (90th percentile)
- **Measurement Window**: 24-hour rolling average

### Error Rate SLO
- **Target**: < 1% error rate across all endpoints
- **Measurement**: HTTP 5xx responses / total requests
- **Window**: 1-hour rolling window
- **Alert Threshold**: > 0.5% error rate

## Service Matrix & Monitoring

### Production Services

#### Dashboard Service
```yaml
service: sophiaai-dashboard-v2
url: https://sophiaai-dashboard-v2.fly.dev
health_endpoint: /healthz
build_endpoint: /__build
slo_targets:
  availability: 99.9%
  response_time_p95: 500ms
  error_rate: <1%
monitoring:
  interval: 15s
  timeout: 2s
  grace_period: 30s
```

#### MCP Repository Service
```yaml
service: sophiaai-mcp-repo-v2
url: https://sophiaai-mcp-repo-v2.fly.dev
health_endpoint: /healthz
slo_targets:
  availability: 99.9%
  response_time_p95: 500ms
  error_rate: <1%
monitoring:
  interval: 15s
  timeout: 2s
  grace_period: 30s
```

#### MCP Research Service
```yaml
service: sophiaai-mcp-research-v2
url: https://sophiaai-mcp-research-v2.fly.dev
health_endpoint: /healthz
search_endpoint: /search
slo_targets:
  availability: 99.9%
  response_time_p95: 500ms
  search_response_time_p90: 5000ms
  error_rate: <1%
monitoring:
  health_interval: 15s
  health_timeout: 2s
  search_interval: 60s
  search_timeout: 10s
  grace_period: 30s
```

#### MCP Context Service
```yaml
service: sophiaai-mcp-context-v2
url: https://sophiaai-mcp-context-v2.fly.dev
health_endpoint: /healthz
stats_endpoint: /context/stats
slo_targets:
  availability: 99.9%
  response_time_p95: 500ms
  error_rate: <1%
monitoring:
  health_interval: 15s
  health_timeout: 2s
  stats_interval: 30s
  stats_timeout: 5s
  grace_period: 30s
```

#### MCP Business Service
```yaml
service: sophiaai-mcp-business-v2
url: https://sophiaai-mcp-business-v2.fly.dev
health_endpoint: /healthz
slo_targets:
  availability: 99.9%
  response_time_p95: 500ms
  error_rate: <1%
monitoring:
  interval: 15s
  timeout: 2s
  grace_period: 30s
```

#### Jobs Service
```yaml
service: sophiaai-jobs-v2
url: https://sophiaai-jobs-v2.fly.dev
health_endpoint: /healthz
schedule: "0 */1 * * *"  # Hourly execution
slo_targets:
  availability: 99.5%  # Lower due to scheduled nature
  job_success_rate: 95%
  response_time_p95: 500ms
monitoring:
  interval: 15s
  timeout: 2s
  grace_period: 30s
```

## Rollback Policy

### Automatic Rollback Triggers
1. **Health Check Failure**: 8 consecutive failed health checks post-deployment
2. **Error Rate Breach**: > 5% error rate within 5 minutes of deployment
3. **Response Time Degradation**: > 5000ms response time for health endpoints
4. **Service Unavailability**: Complete service outage detected

### Rollback Process
```bash
# Automatic rollback (configured in fly.toml)
[experimental]
  auto_rollback = true

# Manual rollback command
flyctl releases rollback <previous-version> -a <app-name> --yes

# Emergency rollback script
./scripts/emergency_rollback.sh <service-name>
```

### Rollback Verification
1. **Post-Rollback Health Checks**: Verify service restoration
2. **Performance Validation**: Confirm response times return to baseline
3. **Error Rate Monitoring**: Ensure error rates drop below threshold
4. **Stakeholder Notification**: Alert team of rollback completion

## Monitoring Implementation

### Fly.io Built-in Monitoring
Each service includes comprehensive health checks configured in [`fly.toml`](../apps/dashboard/fly.toml):

```toml
[vm]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1

[[http_service.checks]]
  method = "GET"
  path = "/healthz"
  interval = "15s"
  timeout = "2s"
  grace_period = "30s"

[http_service.concurrency]
  type = "requests"
  soft_limit = 50
  hard_limit = 75

[experimental]
  auto_rollback = true
```

### GitHub Actions Monitoring
Deployment workflows include comprehensive health verification:

```yaml
- name: Health check with retries
  run: |
    for i in {1..8}; do
      if curl -f -sS "${SERVICE_URL}/healthz"; then
        echo "✅ Health check passed on attempt $i"
        break
      else
        echo "⚠️  Health check failed on attempt $i, retrying..."
        if [ $i -eq 8 ]; then
          echo "❌ Health check failed after 8 attempts - triggering rollback"
          exit 1
        fi
        sleep 15
      fi
    done
```

### External Monitoring Integration

#### Prometheus Metrics (Future Enhancement)
```yaml
metrics:
  - name: http_requests_total
    help: Total number of HTTP requests
    type: counter
    labels: [method, endpoint, status_code]
  
  - name: http_request_duration_seconds
    help: HTTP request duration in seconds
    type: histogram
    labels: [method, endpoint]
  
  - name: service_health_status
    help: Current health status of service (1=healthy, 0=unhealthy)
    type: gauge
    labels: [service, region]
```

#### Alert Manager Configuration
```yaml
alerts:
  - name: ServiceDown
    condition: service_health_status == 0
    duration: 2m
    severity: critical
    
  - name: HighErrorRate
    condition: rate(http_requests_total{status_code~"5.."}[5m]) > 0.01
    duration: 2m
    severity: warning
    
  - name: SlowResponse
    condition: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
    duration: 5m
    severity: warning
```

## Audit Trail & Logging

### Deployment Logs
All deployment activities are logged with complete audit trail:

```json
{
  "timestamp": "2025-08-23T08:38:00Z",
  "deployment_id": "run_12345",
  "service": "sophiaai-dashboard-v2",
  "version": "v1.2.3",
  "status": "success",
  "health_checks": {
    "attempts": 3,
    "success_count": 3,
    "duration": "45s"
  },
  "rollback_triggered": false,
  "approver": "ceo@company.com"
}
```

### Machine State Snapshots
Post-deployment machine state capture:

```bash
# Captured automatically in workflows
flyctl machines list -a <app-name> --json > proofs/fly/<app-name>_machines.json
flyctl status -a <app-name> --json > proofs/fly/<app-name>_status.json
```

### Health Check History
Comprehensive health check logging:

```bash
# Example health proof
====== 2025-08-23T08:38:00Z https://sophiaai-dashboard-v2.fly.dev/healthz ======
HTTP/1.1 200 OK
Date: Fri, 23 Aug 2025 08:38:00 GMT
Content-Type: application/json
Content-Length: 85

{"status":"healthy","version":"v1.2.3","uptime":"15m42s","checks":{"db":"ok","redis":"ok"}}
```

## SLO Reporting

### Daily SLO Report
Automated daily report generation:

```json
{
  "date": "2025-08-23",
  "slo_compliance": {
    "dashboard": {
      "availability": "99.95%",
      "response_time_p95": "245ms",
      "error_rate": "0.02%",
      "status": "✅ COMPLIANT"
    },
    "mcp-research": {
      "availability": "99.89%",
      "response_time_p95": "456ms",
      "search_response_time_p90": "3200ms",
      "error_rate": "0.15%",
      "status": "✅ COMPLIANT"
    }
  },
  "incidents": [],
  "deployments": 2,
  "rollbacks": 0
}
```

### Weekly SLO Summary
```yaml
week_ending: "2025-08-23"
overall_slo_compliance: 99.92%
services_meeting_slo: 5/5
critical_incidents: 0
total_deployments: 14
successful_deployments: 14
rollbacks: 0
downtime_budget_consumed:
  dashboard: "2.1 minutes / 43.8 minutes (4.8%)"
  mcp_services: "1.8 minutes / 43.8 minutes (4.1%)"
```

### Monthly Business Review
```markdown
## Monthly SLO Business Review - August 2025

### Executive Summary
- **Overall Availability**: 99.94%
- **SLO Compliance**: 100% of services met their SLOs
- **Deployment Success Rate**: 98.5%
- **Customer Impact**: Zero customer-facing outages

### Key Metrics
- **Total Deployments**: 56
- **Successful Deployments**: 55
- **Automatic Rollbacks**: 1
- **Mean Time to Recovery**: 3.2 minutes
- **Error Budget Remaining**: 89.2%

### Improvements This Month
- Enhanced health check retry logic (8 attempts)
- Implemented automatic rollback capability
- Reduced deployment-to-healthy time by 40%

### Action Items for Next Month
- Implement Prometheus monitoring integration
- Add predictive alerting for capacity planning
- Enhance error rate tracking granularity
```

## Troubleshooting SLO Violations

### Health Check Failures
```bash
# Investigation steps
1. Check service logs: flyctl logs -a <app-name> --since=1h
2. Verify machine status: flyctl status -a <app-name>
3. Check recent releases: flyctl releases -a <app-name>
4. Review health endpoint: curl -v https://<app-name>.fly.dev/healthz
```

### Performance Degradation
```bash
# Performance investigation
1. Check machine resources: flyctl machine list -a <app-name>
2. Review response times: grep "response_time" logs/
3. Database connection health: Check NEON_DATABASE_URL connectivity
4. External service latency: Test Qdrant, Redis connections
```

### Error Rate Spikes
```bash
# Error investigation
1. Filter error logs: flyctl logs -a <app-name> | grep "ERROR\|5[0-9][0-9]"
2. Check dependency health: Verify external service status
3. Review recent changes: git log --oneline --since="1 hour ago"
4. Validate configuration: Check environment variables
```

## Continuous Improvement

### SLO Evolution
- **Quarterly Review**: Assess SLO targets against business needs
- **Benchmark Analysis**: Compare against industry standards
- **Customer Feedback**: Incorporate user experience metrics
- **Technology Changes**: Adjust SLOs for new infrastructure capabilities

### Monitoring Enhancements
- **Predictive Alerting**: Implement trend-based alerts
- **Synthetic Monitoring**: Add end-to-end user journey tests
- **Real User Monitoring**: Track actual user experience metrics
- **Chaos Engineering**: Regular resilience testing

### Documentation Maintenance
- **Monthly Updates**: Review and update SLO targets
- **Incident Learning**: Incorporate post-incident improvements
- **Process Refinement**: Streamline monitoring and response procedures
- **Team Training**: Regular SLO awareness sessions

---

*This document is reviewed monthly and updated based on operational experience and business requirements.*