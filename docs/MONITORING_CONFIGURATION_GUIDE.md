# Sophia AI Monitoring Configuration Guide

## Overview

This guide provides comprehensive instructions for deploying and configuring the monitoring stack for the Sophia AI platform, including Prometheus, Grafana, AlertManager, and Loki.

## Architecture

The monitoring stack consists of:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Loki**: Log aggregation
- **Promtail**: Log shipping from Kubernetes pods

## Prerequisites

- Kubernetes cluster with appropriate permissions
- kubectl configured to access the cluster
- SMTP server for email notifications (optional)
- Slack webhook URL for Slack notifications (optional)

## Deployment

### 1. Deploy Monitoring Stack

```bash
cd k8s-deploy
chmod +x scripts/deploy-monitoring.sh
./scripts/deploy-monitoring.sh
```

This script will:
- Create the monitoring namespace
- Deploy Prometheus with custom scrape configurations
- Deploy AlertManager with notification channels
- Deploy Grafana with enhanced dashboards
- Deploy Loki and Promtail for log aggregation

### 2. Configure Secrets

Create the monitoring secrets with your credentials:

```bash
kubectl create secret generic monitoring-secrets -n monitoring \
  --from-literal=SMTP_USERNAME='your-smtp-username' \
  --from-literal=SMTP_PASSWORD='your-smtp-password' \
  --from-literal=SLACK_WEBHOOK_URL='your-slack-webhook-url' \
  --from-literal=WEBHOOK_URL='your-external-webhook-url' \
  --from-literal=WEBHOOK_USERNAME='your-webhook-username' \
  --from-literal=WEBHOOK_PASSWORD='your-webhook-password'
```

### 3. Access Interfaces

#### Grafana
```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```
- URL: http://localhost:3000
- Default credentials: admin / sophia2024!
- **Change the default password in production!**

#### Prometheus
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```
- URL: http://localhost:9090

#### AlertManager
```bash
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
```
- URL: http://localhost:9093

## Alerting Configuration

### Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Duration |
|--------|------------------|-------------------|----------|
| CPU Usage | 70% | 90% | 10 minutes |
| Memory Usage | 80% | 95% | 10 minutes |
| Pod Restarts | 6/hour | N/A | 15 minutes |
| Response Time | 2 seconds | 5 seconds | 5 minutes |
| Error Rate | 5% | 10% | 5 minutes |
| GPU Utilization | 90% | 95% | 5 minutes |

### Notification Channels

1. **Email**: Team notifications for warnings, critical alerts for immediate response
2. **Slack**: Real-time notifications to dedicated channels
   - `#sophia-alerts`: General alerts
   - `#sophia-critical`: Critical alerts requiring immediate action
   - `#gpu-monitoring`: GPU-specific alerts
   - `#ml-monitoring`: AI/ML model alerts
   - `#sonic-ai-monitoring`: Sonic AI service alerts
3. **Webhook**: External monitoring system integration

### Escalation Policies

- **Warning**: Email notification to team
- **Critical**: Email + Slack notifications with immediate escalation
- **GPU/AI Model**: Specialized channels for domain experts
- **Service-specific**: Dedicated channels per service/component

## Dashboards

### Enhanced Overview Dashboard
- System health status with color-coded indicators
- Active alerts count
- Pod restart tracking
- Response time monitoring
- Resource utilization graphs
- Error rate monitoring
- Pod health overview
- Recent alerts log

### Sonic AI Performance Dashboard
- Service health and active requests
- CPU, memory, and GPU utilization
- Response time distribution
- Code generation success rate
- Reasoning confidence scores
- MCP integration health
- Agentic coding operations metrics

## Service Integration

### Adding Prometheus Metrics to Services

Add these annotations to your Kubernetes service pods:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: 'true'
    prometheus.io/port: '8080'
    prometheus.io/path: '/metrics'
```

### Custom Metrics

For custom metrics, ensure your service exposes a `/metrics` endpoint that returns Prometheus-formatted metrics.

## Alert Rules

### Service Health
- `SophiaServiceDown`: Service unavailable for 5+ minutes
- `HighCPUUsage`: CPU usage > 70% sustained
- `HighMemoryUsage`: Memory usage > 80% sustained
- `PodRestartRateHigh`: Frequent pod restarts
- `ServiceResponseTimeHigh`: Response time > 2 seconds
- `HighErrorRate`: Error rate > 5%

### AI/ML Specific
- `GPUUtilizationHigh`: GPU usage > 90%
- `GPUOutOfMemory`: GPU memory > 95%
- `AIModelHighLatency`: AI inference > 30 seconds
- `AIModelErrorsHigh`: AI error rate > 10%
- `SonicAIHighConfidence`: Sonic AI confidence < 80%

## Maintenance

### Updating Alert Thresholds

Modify the alert rules in `k8s-deploy/manifests/prometheus.yaml`:

```yaml
- alert: HighCPUUsage
  expr: rate(container_cpu_usage_seconds_total{namespace="sophia"}[5m]) > 0.7
  for: 10m
  labels:
    severity: warning
```

### Adding New Dashboards

1. Create JSON dashboard definition
2. Add to ConfigMap: `kubectl create configmap new-dashboard --from-file=dashboard.json -n monitoring`
3. Update Grafana deployment to mount the new ConfigMap

### Log Aggregation

Loki is configured to collect logs from all pods in the `sophia` namespace. Logs are automatically tagged with pod metadata for easy querying.

## Troubleshooting

### Common Issues

1. **Alerts not firing**: Check Prometheus targets and rule evaluation
2. **Notifications not sent**: Verify AlertManager configuration and secrets
3. **Metrics not collected**: Ensure service annotations and `/metrics` endpoint
4. **Grafana login issues**: Reset admin password or check authentication config

### Debugging Commands

```bash
# Check Prometheus status
kubectl get pods -n monitoring -l app=prometheus

# View Prometheus logs
kubectl logs -n monitoring -l app=prometheus

# Check AlertManager status
kubectl get pods -n monitoring -l app=alertmanager

# Validate alert rules
kubectl port-forward -n monitoring svc/prometheus 9090:9090
curl http://localhost:9090/api/v1/rules
```

## Security Considerations

1. **Change default Grafana password**
2. **Use HTTPS for external access**
3. **Restrict network access to monitoring interfaces**
4. **Regular secret rotation**
5. **Audit log access and alerting rules**

## Performance Optimization

- **Scrape intervals**: Balanced between real-time monitoring and resource usage
- **Retention**: Configure appropriate data retention policies
- **Alert grouping**: Prevents alert spam with intelligent grouping
- **Dashboard refresh**: Optimized for real-time monitoring without excessive queries

## Next Steps

1. Customize alert thresholds based on your environment
2. Set up additional notification channels as needed
3. Create service-specific dashboards for complex applications
4. Implement automated alert response and remediation
5. Set up monitoring for additional infrastructure components

---

## Support

For issues with the monitoring setup:

1. Check the logs of individual components
2. Verify configuration files for syntax errors
3. Ensure all required secrets are properly configured
4. Review Kubernetes events for deployment issues

The monitoring stack is designed to be highly available and scalable. All components can be scaled independently based on your monitoring requirements.