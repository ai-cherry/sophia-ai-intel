# Sophia AI - Service Dependencies and Communication Patterns

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Service Dependency Map](#service-dependency-map)
3. [Communication Patterns](#communication-patterns)
4. [Data Flow](#data-flow)
5. [Network Policies](#network-policies)
6. [Failure Impact Analysis](#failure-impact-analysis)
7. [Monitoring Dependencies](#monitoring-dependencies)

## System Architecture Overview

### Service Topology
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 Internet                                         │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                        nginx (Ingress)                                          │
│                   Load Balancer + SSL                                           │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼─────────┐ ┌───▼────────┐ ┌────▼─────────────┐
│ sophia-dashboard  │ │ MCP Core   │ │ Integration      │
│ (Frontend UI)     │ │ Services   │ │ Services         │
│ Port: 3000        │ │            │ │                  │
└─────────┬─────────┘ └───┬────────┘ └────┬─────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Cache Layer                        │
│                 Session + Cache Storage                     │
└─────────────────────────────────────────────────────────────┘
```

### Core Service Groups

#### 1. MCP (Model Context Protocol) Services
- **mcp-research** (Port 8001): Research and analysis engine
- **mcp-context** (Port 8002): Context management and processing
- **mcp-agents** (Port 8003): Agent orchestration and workflow management

#### 2. Business Intelligence Services
- **sophia-dashboard** (Port 3000): Main user interface and dashboard
- **sophia-business** (Port 8004): Business logic and analytics engine

#### 3. Integration Services
- **sophia-hubspot** (Port 8005): HubSpot CRM integration
- **sophia-github** (Port 8006): GitHub API and workflow integration
- **sophia-lambda** (Port 8007): Lambda Labs infrastructure management

#### 4. MCP Additional Services
- **mcp-business** (Port 8008): Business logic and analytics processing

#### 5. Infrastructure Services
- **Redis** (Port 6379): Caching and session storage
- **nginx**: Load balancing and SSL termination
- **Prometheus** (Port 9090): Metrics collection
- **Grafana** (Port 3000): Monitoring dashboards
- **Loki** (Port 3100): Log aggregation

## Service Dependency Map

### Primary Dependencies (Critical Path)

```
nginx → sophia-dashboard → sophia-business → mcp-context → Redis
  │                           │                 │
  └→ mcp-research ←───────────┘                 │
  │                                             │
  └→ mcp-agents ←─────────────────────────────────┘
```

### Integration Dependencies (Secondary)

```
sophia-hubspot → HubSpot API (External)
     │
     └→ sophia-business → mcp-context

sophia-github → GitHub API (External)
     │
     └→ mcp-agents → mcp-research

sophia-lambda → Lambda Labs API (External)
     │
     └→ mcp-agents
```

### AI Processing Dependencies

```
sonic-ai → GPU Resources (Optional)
    │
    └→ mcp-research → mcp-context → Redis
```

### Detailed Dependency Matrix

| Service | Direct Dependencies | Indirect Dependencies | External Dependencies |
|---------|-------------------|---------------------|----------------------|
| **nginx** | None | All services | Internet, DNS, SSL Certs |
| **sophia-dashboard** | sophia-business, Redis | mcp-*, sonic-ai | None |
| **sophia-business** | mcp-context, Redis | mcp-research, mcp-agents | None |
| **mcp-research** | mcp-context, Redis | None | Research APIs |
| **mcp-context** | Redis | None | None |
| **mcp-agents** | mcp-research, mcp-context, Redis | sonic-ai | Agent APIs |
| **sophia-hubspot** | sophia-business, Redis | mcp-* | HubSpot API |
| **sophia-github** | mcp-agents, Redis | mcp-research | GitHub API |
| **sophia-lambda** | mcp-agents, Redis | None | Lambda Labs API |
| **sonic-ai** | mcp-research, Redis | mcp-context | GPU Hardware |
| **Redis** | None | None | Persistent Storage |

## Communication Patterns

### HTTP/REST API Communication
All inter-service communication uses HTTP/REST with JSON payloads:

```yaml
# Service-to-Service Communication
sophia-dashboard → sophia-business:
  - GET /api/analytics/summary
  - POST /api/analytics/query
  - GET /api/health

sophia-business → mcp-context:
  - POST /api/context/analyze
  - GET /api/context/retrieve/{id}
  - PUT /api/context/update/{id}

mcp-agents → mcp-research:
  - POST /api/research/request
  - GET /api/research/status/{task_id}
  - GET /api/research/results/{task_id}
```

### Service Discovery
Services discover each other using Kubernetes DNS:
- **Internal DNS**: `[service-name].sophia.svc.cluster.local`
- **Short DNS**: `[service-name]` (within same namespace)

### Authentication and Authorization
```yaml
# JWT Token Flow
Client → nginx → sophia-dashboard:
  Headers:
    Authorization: "Bearer [jwt_token]"
    Content-Type: "application/json"

# Inter-service Authentication
sophia-dashboard → sophia-business:
  Headers:
    X-Service-Token: "[internal_service_token]"
    X-Request-ID: "[correlation_id]"
```

### Error Handling and Retries
```yaml
# Retry Strategy
Initial Request → Immediate Retry (if timeout)
                → Exponential Backoff (if 5xx error)
                → Circuit Breaker (if consistent failures)

# Circuit Breaker Thresholds
Failure Rate: > 50% over 10 requests
Response Time: > 5 seconds average
Recovery: 30 second window
```

## Data Flow

### Request Processing Flow

#### 1. User Dashboard Request
```
User → nginx → sophia-dashboard → sophia-business → mcp-context → Redis
                     │                    │              │
                     └→ Static Assets     └→ Analytics   └→ Cache Check
```

#### 2. Research Request Flow
```
Dashboard → sophia-business → mcp-agents → mcp-research → mcp-context
     │              │              │             │            │
     └→ Request ID  └→ Task Queue  └→ Agent      └→ Research  └→ Context Store
                                   Selection     Processing   
```

#### 3. AI Processing Flow
```
mcp-agents → sonic-ai → GPU Processing → mcp-research → mcp-context → Redis
     │           │           │               │              │           │
     └→ AI Task  └→ Model    └→ Inference    └→ Results     └→ Store   └→ Cache
        Creation    Loading     Processing     Processing     Context    Results
```

### Data Storage Patterns

#### Redis Data Structure
```redis
# Session Data
session:[user_id] → {user_data, preferences, auth_tokens}
TTL: 24 hours

# Cache Data
cache:research:[query_hash] → {results, metadata, timestamp}
TTL: 6 hours

# Context Data
context:[context_id] → {context_data, relationships, metadata}
TTL: 7 days

# Agent State
agent:[agent_id]:state → {current_task, status, metadata}
TTL: 1 hour
```

## Network Policies

### Service-to-Service Access Control

```yaml
# Core Services Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-core-policy
  namespace: sophia
spec:
  podSelector:
    matchLabels:
      group: mcp-core
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: sophia-business
    - podSelector:
        matchLabels:
          app: sophia-dashboard
    ports:
    - protocol: TCP
      port: 8001  # mcp-research
    - protocol: TCP
      port: 8002  # mcp-context
    - protocol: TCP
      port: 8003  # mcp-agents
```

### External Access Policies

```yaml
# Integration Services - External API Access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: integration-external-policy
  namespace: sophia
spec:
  podSelector:
    matchLabels:
      group: integration
  policyTypes:
  - Egress
  egress:
  - to: []  # Allow all external traffic
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 80   # HTTP
  - to:
    - podSelector:
        matchLabels:
          group: mcp-core
    ports:
    - protocol: TCP
      port: 8001
    - protocol: TCP
      port: 8002
    - protocol: TCP
      port: 8003
```

## Failure Impact Analysis

### Critical Service Failures

#### Redis Failure
**Impact**: Complete system failure
**Affected Services**: All services (session storage, caching)
**Recovery Time**: 2-5 minutes
**Mitigation**: 
```bash
# Immediate restart
kubectl rollout restart deployment/redis -n sophia
# Monitor recovery
kubectl wait --for=condition=available --timeout=120s deployment/redis -n sophia
```

#### mcp-context Failure
**Impact**: High - Core functionality unavailable
**Affected Services**: mcp-research, mcp-agents, sophia-business
**Recovery Time**: 3-10 minutes
**Mitigation**: Horizontal scaling, circuit breakers

#### nginx Failure
**Impact**: Complete external access failure
**Affected Services**: All user-facing services
**Recovery Time**: 1-3 minutes
**Mitigation**: Load balancer redundancy

### Non-Critical Service Failures

#### Integration Service Failures
**Impact**: Medium - Specific integrations unavailable
**Affected Services**: Dependent on specific integration
**Recovery Time**: 5-15 minutes
**Mitigation**: Graceful degradation, external API timeouts

#### Monitoring Service Failures
**Impact**: Low - Observability reduced
**Affected Services**: None (operational impact only)
**Recovery Time**: 10-30 minutes
**Mitigation**: External monitoring, alerting redundancy

### Cascading Failure Scenarios

#### Scenario 1: Database Connection Pool Exhaustion
```
Redis Connection Issues → mcp-context Failures → mcp-research Timeouts → 
mcp-agents Queue Backup → System-wide Degradation
```

**Prevention**:
- Connection pool monitoring
- Circuit breaker implementation
- Timeout configuration

#### Scenario 2: Memory Pressure
```
sonic-ai Memory Leak → Node Resource Pressure → Pod Evictions → 
Service Unavailability → Cascading Restarts
```

**Prevention**:
- Resource limits and requests
- Memory usage monitoring
- Horizontal Pod Autoscaling

## Monitoring Dependencies

### Health Check Dependencies
```yaml
# Health Check Hierarchy
nginx:
  checks:
    - Load balancer status
    - SSL certificate validity
    - Upstream service availability

sophia-dashboard:
  checks:
    - UI responsiveness
    - sophia-business connectivity
    - Redis session access

sophia-business:
  checks:
    - mcp-context connectivity
    - Redis cache access
    - Database queries

mcp-services:
  checks:
    - Inter-service communication
    - Redis connectivity
    - External API availability
```

### Monitoring Metrics by Dependency

#### Service Availability Metrics
```prometheus
# Service Up/Down Status
up{job="kubernetes-pods", service="mcp-research"}

# Service Response Time
http_request_duration_seconds{service="mcp-research", quantile="0.95"}

# Service Error Rate
rate(http_requests_total{service="mcp-research", status=~"5.."}[5m])
```

#### Dependency Health Metrics
```prometheus
# Redis Connection Pool
redis_connected_clients
redis_blocked_clients
redis_used_memory_peak

# External API Health
http_requests_total{job="external-api-health", api="hubspot"}
http_request_duration_seconds{job="external-api-health", api="github"}
```

### Alerting Rules for Dependencies

```yaml
# Critical Dependency Failure
- alert: RedisCriticalFailure
  expr: up{job="redis"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Redis is down - system failure imminent"
    description: "Redis has been down for more than 1 minute"

# Service Dependency Failure
- alert: MCPServiceDependencyFailure
  expr: |
    (
      rate(http_requests_total{service=~"mcp-.*", status=~"5.."}[5m]) > 0.1
    ) * on(service) group_left
    (
      up{service=~"mcp-.*"} == 1
    )
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "MCP service experiencing dependency issues"
```

---

**Document Version**: 1.1.0  
**Last Updated**: August 2025  
**Next Review**: November 2025  
**Owner**: Sophia AI Operations Team