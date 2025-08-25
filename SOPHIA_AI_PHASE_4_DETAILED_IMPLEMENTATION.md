# Sophia AI Phase 4: Production Deployment & Monitoring - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 3 Weeks (Weeks 13-15)  
**Priority**: CRITICAL - Following Phase 3B  
**Goal**: Deploy Sophia AI to production on Lambda Labs Kubernetes with comprehensive monitoring and observability

## Executive Summary

Phase 4 focuses on deploying the complete Sophia AI system to production on Lambda Labs' GPU-enabled Kubernetes infrastructure. This phase implements enterprise-grade monitoring, observability, security hardening, and ensures zero-downtime deployments with comprehensive rollback capabilities.

### Key Objectives
1. Deploy to Lambda Labs Kubernetes with GPU support
2. Implement comprehensive Prometheus + Grafana monitoring
3. Set up distributed tracing with OpenTelemetry
4. Configure auto-scaling and self-healing capabilities
5. Establish SLOs and incident response procedures

## Production Architecture

### Infrastructure Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container Orchestration | Kubernetes 1.29 | Service management, scaling |
| GPU Infrastructure | Lambda Labs A100/H100 | ML model inference |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Logging | Loki + Promtail | Centralized logging |
| Tracing | Jaeger + OpenTelemetry | Distributed tracing |
| Service Mesh | Istio | Traffic management, security |
| Secrets Management | External Secrets Operator | Secure secret injection |
| CI/CD | GitHub Actions + ArgoCD | GitOps deployment |

### Deployment Strategy

1. **Blue-Green Deployment**: Zero-downtime updates with instant rollback
2. **Canary Releases**: Gradual rollout with automated rollback on errors
3. **Feature Flags**: Controlled feature enablement
4. **Database Migrations**: Zero-downtime schema updates
5. **GPU Allocation**: Smart GPU scheduling and sharing

## Week 13: Infrastructure Setup

### Day 1-2: Lambda Labs Kubernetes Configuration

#### 13.1 Kubernetes Cluster Setup
```yaml
# ops/kubernetes/lambda-labs/cluster-config.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sophia-production
  labels:
    environment: production
    monitoring: enabled
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sophia-resource-quota
  namespace: sophia-production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    requests.nvidia.com/gpu: "8"  # 8 GPUs allocated
    persistentvolumeclaims: "20"
    services.loadbalancers: "10"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: sophia-critical
value: 1000
globalDefault: false
description: "Critical Sophia AI services"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: sophia-high
value: 900
description: "High priority Sophia AI services"
---
# GPU Node Affinity Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-scheduling-config
  namespace: sophia-production
data:
  gpu-sharing: |
    # NVIDIA GPU sharing configuration
    # Allows multiple pods to share GPU resources
    nvidia.com/gpu.sharing.strategy: "mps"
    nvidia.com/gpu.sharing.max-clients: "4"
```

#### 13.2 Service Deployment Manifests
```yaml
# ops/kubernetes/deployments/agno-coordinator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-coordinator
  namespace: sophia-production
  labels:
    app: agno-coordinator
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: agno-coordinator
  template:
    metadata:
      labels:
        app: agno-coordinator
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      priorityClassName: sophia-critical
      serviceAccountName: agno-coordinator
      containers:
      - name: agno-coordinator
        image: sophia-ai/agno-coordinator:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        - name: ENABLE_TRACING
          value: "true"
        - name: JAEGER_ENDPOINT
          value: "http://jaeger-collector.monitoring:14268/api/traces"
        envFrom:
        - secretRef:
            name: agno-coordinator-secrets
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: agno-coordinator-config
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - agno-coordinator
            topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: agno-coordinator
  namespace: sophia-production
  labels:
    app: agno-coordinator
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    name: http
  - port: 9090
    targetPort: 9090
    name: metrics
  selector:
    app: agno-coordinator
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agno-coordinator-hpa
  namespace: sophia-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agno-coordinator
  minReplicas: 3
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
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### Day 3: GPU-Enabled Services

#### 13.3 GPU Service Deployment
```yaml
# ops/kubernetes/deployments/mcp-agents-gpu.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-agents-gpu
  namespace: sophia-production
  labels:
    app: mcp-agents
    gpu: required
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-agents
      gpu: required
  template:
    metadata:
      labels:
        app: mcp-agents
        gpu: required
    spec:
      priorityClassName: sophia-high
      containers:
      - name: mcp-agents
        image: sophia-ai/mcp-agents:latest-gpu
        resources:
          requests:
            cpu: "4"
            memory: "16Gi"
            nvidia.com/gpu: "1"
          limits:
            cpu: "8"
            memory: "32Gi"
            nvidia.com/gpu: "1"
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        - name: GPU_MEMORY_FRACTION
          value: "0.8"
        - name: MODEL_CACHE_DIR
          value: "/models"
        volumeMounts:
        - name: model-cache
          mountPath: /models
        - name: shm
          mountPath: /dev/shm
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: 16Gi
      nodeSelector:
        node.kubernetes.io/gpu: "true"
        gpu.nvidia.com/class: "A100"
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

### Day 4: Service Mesh & Security

#### 13.4 Istio Service Mesh Configuration
```yaml
# ops/kubernetes/istio/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sophia-ai-vs
  namespace: sophia-production
spec:
  hosts:
  - sophia-ai.production.internal
  gateways:
  - sophia-gateway
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: agno-coordinator
        subset: canary
      weight: 100
  - route:
    - destination:
        host: agno-coordinator
        subset: stable
      weight: 90
    - destination:
        host: agno-coordinator
        subset: canary
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: agno-coordinator-dr
  namespace: sophia-production
spec:
  host: agno-coordinator
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
    loadBalancer:
      simple: LEAST_REQUEST
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: sophia-auth-policy
  namespace: sophia-production
spec:
  selector:
    matchLabels:
      app: agno-coordinator
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/sophia-production/sa/dashboard"]
    - source:
        principals: ["cluster.local/ns/sophia-production/sa/mcp-*"]
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/health/*", "/metrics"]
```

## Week 14: Monitoring & Observability

### Day 5-6: Prometheus & Grafana Setup

#### 14.1 Prometheus Configuration
```yaml
# monitoring/prometheus/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'sophia-production'
        environment: 'production'
    
    # Alerting configuration
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
    
    # Rule files
    rule_files:
      - '/etc/prometheus/rules/*.yml'
    
    # Scrape configurations
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['sophia-production']
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
    
    - job_name: 'gpu-metrics'
      static_configs:
      - targets: ['nvidia-dcgm-exporter:9400']
      metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'DCGM_.*'
        action: keep
```

#### 14.2 Grafana Dashboards
```json
// monitoring/grafana/dashboards/sophia-production-overview.json
{
  "dashboard": {
    "title": "Sophia AI Production Overview",
    "uid": "sophia-prod-overview",
    "tags": ["sophia", "production", "overview"],
    "timezone": "browser",
    "schemaVersion": 30,
    "panels": [
      {
        "title": "Request Rate",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"agno-coordinator\"}[5m])) by (status)",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Response Time (p50, p95, p99)",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, sum(rate(http_request_duration_seconds_bucket{job=\"agno-coordinator\"}[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"agno-coordinator\"}[5m])) by (le))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job=\"agno-coordinator\"}[5m])) by (le))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "type": "graph",
        "targets": [
          {
            "expr": "avg(DCGM_FI_DEV_GPU_UTIL) by (gpu, kubernetes_pod_name)",
            "legendFormat": "{{kubernetes_pod_name}} - GPU {{gpu}}"
          }
        ]
      },
      {
        "title": "GPU Memory Usage",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "type": "graph",
        "targets": [
          {
            "expr": "DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL * 100",
            "legendFormat": "{{kubernetes_pod_name}} - GPU {{gpu}}"
          }
        ]
      },
      {
        "title": "AI Agent Activity",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(agno_agent_tasks_completed_total[5m])) by (agent_type)",
            "legendFormat": "{{agent_type}}"
          }
        ]
      },
      {
        "title": "Cost per Request",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(llm_api_cost_dollars[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Avg Cost/Request"
          }
        ]
      }
    ]
  }
}
```

### Day 7: Distributed Tracing

#### 14.3 OpenTelemetry Integration
```typescript
// libs/telemetry/src/tracing.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';

export function initializeTracing(serviceName: string): NodeSDK {
  const jaegerExporter = new JaegerExporter({
    endpoint: process.env.JAEGER_ENDPOINT || 'http://jaeger-collector:14268/api/traces',
  });

  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.SERVICE_VERSION || '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.ENVIRONMENT || 'production',
  });

  const sdk = new NodeSDK({
    resource,
    instrumentations: [
      getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-fs': {
          enabled: false, // Disable fs instrumentation to reduce noise
        },
      }),
    ],
    spanProcessor: new BatchSpanProcessor(jaegerExporter),
  });

  sdk.start();
  return sdk;
}

// Middleware for Express
export function tracingMiddleware(serviceName: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const tracer = opentelemetry.trace.getTracer(serviceName);
    const span = tracer.startSpan(`${req.method} ${req.path}`);
    
    // Add span attributes
    span.setAttributes({
      'http.method': req.method,
      'http.url': req.url,
      'http.target': req.path,
      'user.id': req.user?.id,
      'request.id': req.headers['x-request-id'],
    });

    // Store span in request for manual instrumentation
    req.span = span;

    // End span when response is finished
    res.on('finish', () => {
      span.setAttributes({
        'http.status_code': res.statusCode,
      });
      
      if (res.statusCode >= 400) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: `HTTP ${res.statusCode}`,
        });
      }
      
      span.end();
    });

    next();
  };
}
```

### Day 8: Log Aggregation

#### 14.4 Loki & Promtail Configuration
```yaml
# monitoring/loki/loki-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: monitoring
data:
  loki.yaml: |
    auth_enabled: false
    
    server:
      http_listen_port: 3100
    
    ingester:
      lifecycler:
        address: 127.0.0.1
        ring:
          kvstore:
            store: inmemory
          replication_factor: 1
        final_sleep: 0s
      chunk_idle_period: 1h
      max_chunk_age: 1h
      chunk_target_size: 1048576
      chunk_retain_period: 30s
      max_transfer_retries: 0
    
    schema_config:
      configs:
      - from: 2023-01-01
        store: boltdb-shipper
        object_store: filesystem
        schema: v11
        index:
          prefix: index_
          period: 24h
    
    storage_config:
      boltdb_shipper:
        active_index_directory: /loki/boltdb-shipper-active
        cache_location: /loki/boltdb-shipper-cache
        cache_ttl: 24h
        shared_store: filesystem
      filesystem:
        directory: /loki/chunks
    
    limits_config:
      reject_old_samples: true
      reject_old_samples_max_age: 168h
      ingestion_rate_mb: 16
      ingestion_burst_size_mb: 32
    
    chunk_store_config:
      max_look_back_period: 0s
    
    table_manager:
      retention_deletes_enabled: true
      retention_period: 720h
---
# monitoring/promtail/promtail-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: monitoring
data:
  promtail.yaml: |
    server:
      http_listen_port: 9080
      grpc_listen_port: 0
    
    positions:
      filename: /tmp/positions.yaml
    
    clients:
    - url: http://loki:3100/loki/api/v1/push
    
    scrape_configs:
    - job_name: kubernetes-pods
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['sophia-production']
      pipeline_stages:
      - docker: {}
      - multiline:
          firstline: '^\d{4}-\d{2}-\d{2}'
          max_wait_time: 3s
      - regex:
          expression: '^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<level>\w+)\s+\[(?P<service>[^\]]+)\]\s+(?P<message>.*)'
      - labels:
          level:
          service:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

## Week 15: Production Readiness

### Day 9-10: SLO Definition & Alerting

#### 15.1 Service Level Objectives
```yaml
# monitoring/slos/sophia-slos.yaml
apiVersion: sloth.slok.dev/v1
kind: PrometheusServiceLevel
metadata:
  name: sophia-ai-slos
  namespace: monitoring
spec:
  service: "sophia-ai"
  labels:
    team: "platform"
    tier: "critical"
  slos:
  - name: "availability"
    objective: 99.9  # 99.9% availability
    description: "Sophia AI API availability"
    sli:
      events:
        error_query: sum(rate(http_requests_total{job="agno-coordinator",status=~"5.."}[5m]))
        total_query: sum(rate(http_requests_total{job="agno-coordinator"}[5m]))
    alerting:
      name: SophiaAvailabilityAlert
      page_alert:
        labels:
          severity: critical
      annotations:
        summary: "Sophia AI availability is below SLO"
        
  - name: "latency"
    objective: 99  # 99% of requests under 1s
    description: "Sophia AI API latency"
    sli:
      raw:
        error_ratio_query: |
          sum(rate(http_request_duration_seconds_bucket{job="agno-coordinator",le="1"}[5m]))
          /
          sum(rate(http_request_duration_seconds_count{job="agno-coordinator"}[5m]))
    alerting:
      name: SophiaLatencyAlert
      page_alert:
        labels:
          severity: warning
          
  - name: "gpu-availability"
    objective: 95  # 95% GPU availability
    description: "GPU resource availability for AI workloads"
    sli:
      events:
        error_query: |
          count(DCGM_FI_DEV_GPU_UTIL < 10 or absent(DCGM_FI_DEV_GPU_UTIL))
        total_query: |
          count(DCGM_FI_DEV_GPU_UTIL) or vector(0)
```

#### 15.2 Alert Rules
```yaml
# monitoring/prometheus/alerts.yaml
groups:
- name: sophia-critical
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: |
      (
        sum(rate(http_requests_total{status=~"5..",job="agno-coordinator"}[5m]))
        /
        sum(rate(http_requests_total{job="agno-coordinator"}[5m]))
      ) > 0.05
    for: 5m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"
      runbook_url: "https://docs.sophia-ai.com/runbooks/high-error-rate"
      
  - alert: PodCrashLooping
    expr: |
      rate(kube_pod_container_status_restarts_total{namespace="sophia-production"}[5m]) > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Pod {{ $labels.pod }} is crash looping"
      description: "Pod has restarted {{ $value }} times in the last 5 minutes"
      
  - alert: GPUMemoryExhaustion
    expr: |
      (DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL) > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "GPU memory usage high"
      description: "GPU {{ $labels.gpu }} memory usage is {{ $value | humanizePercentage }}"
      
  - alert: HighLLMCosts
    expr: |
      sum(rate(llm_api_cost_dollars[1h])) > 100
    for: 30m
    labels:
      severity: warning
      team: finance
    annotations:
      summary: "High LLM API costs detected"
      description: "LLM API costs are ${{ $value | printf \"%.2f\" }}/hour"
      
- name: sophia-performance
  interval: 1m
  rules:
  - alert: HighLatency
    expr: |
      histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="agno-coordinator"}[5m])) by (le)) > 3
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High request latency"
      description: "P99 latency is {{ $value }}s"
      
  - alert: HighMemoryUsage
    expr: |
      container_memory_usage_bytes{namespace="sophia-production"} / container_spec_memory_limit_bytes > 0.8
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage for {{ $labels.pod }}"
      description: "Memory usage is {{ $value | humanizePercentage }} of limit"
```

### Day 11-12: Deployment Automation

#### 15.3 GitOps with ArgoCD
```yaml
# ops/argocd/sophia-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sophia-ai-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/ai-cherry/sophia-ai-intel
    targetRevision: production
    path: ops/kubernetes/production
    helm:
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: sophia-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

#### 15.4 Rollback Strategy
```bash
#!/bin/bash
# ops/scripts/emergency-rollback.sh

set -euo pipefail

# Configuration
NAMESPACE="sophia-production"
DEPLOYMENT_PREFIX="sophia-"
ROLLBACK_VERSION="${1:-}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${YELLOW}Sophia AI Emergency Rollback Script${NC}"
echo "======================================"

# Check if version provided
if [ -z "$ROLLBACK_VERSION" ]; then
    echo -e "${RED}Error: No version specified${NC
