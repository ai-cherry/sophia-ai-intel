# Sophia AI Deployment Guide - Fly.io & Kubernetes

This document outlines the advanced CI/CD deployment strategy for Sophia AI, incorporating canary deployments, database migrations, and synthetic end-to-end testing.

## Overview

The Sophia AI deployment pipeline follows a sophisticated multi-stage approach:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lint/Test     │ -> │  Build/Cache    │ -> │   Canary        │ -> │   Migration     │ -> │   Synthetics     │
│                 │    │                 │    │   Deployment    │    │                 │    │                 │
│ • Code Quality  │    │ • Multi-arch    │    │ • 10% Traffic   │    │ • Neon DB       │    │ • E2E Tests      │
│ • Unit Tests    │    │ • Security Scan │    │ • Health Check  │    │ • Audit Schema  │    │ • Slack/CRM/DB   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                                                      │
                                                                                                      v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                         ┌─────────────────┐
│ Full Rollout    │ -> │   Readiness     │ -> │   Success       │ <- - - - - - - - - - - - │   Rollback       │
│                 │    │   Check         │    │                 │                         │                 │
│ • 100% Traffic  │    │ • Final Health  │    │ • Deploy Live   │                         │ • Auto Rollback  │
│ • Monitoring    │    │ • Performance   │    │ • Notify Teams  │                         │ • Alert Teams    │
└─────────────────┘    └─────────────────┘    └─────────────────┘                         └─────────────────┘
```

## Prerequisites

- Kubernetes cluster with Istio service mesh
- Neon PostgreSQL database
- GitHub repository with proper secrets configured
- Slack webhook for notifications
- CRM system access

## Deployment Stages

### 1. Lint & Test Stage

**Purpose**: Ensure code quality and functionality before deployment

**Actions**:
- Run Ruff linting across all Python code
- Execute unit test suite with pytest
- Generate coverage reports
- Fail pipeline on any test failures or linting errors

**Files**: `.github/workflows/sophia_infra.yml` (lint-test job)

### 2. Build & Cache Stage

**Purpose**: Create optimized container images for all services

**Actions**:
- Build multi-architecture Docker images (AMD64/ARM64)
- Push images to GitHub Container Registry
- Implement build caching for faster subsequent builds
- Tag images with commit SHA and branch information

**Services Built**:
- MCP Services: `mcp-research`, `mcp-context`, `mcp-agents`, `mcp-business`
- Communication Services: `comms-mcp`, `crm-mcp`, `analytics-mcp`
- Business Services: `sophia-dashboard`, `sophia-business`, `sophia-hubspot`, `sophia-github`, `sophia-lambda`

**Files**: `.github/workflows/sophia_infra.yml` (build-cache job)

### 3. Canary Deployment Stage

**Purpose**: Test new version with minimal traffic before full rollout

**Actions**:
- Deploy new version to canary namespace (`sophia-canary`)
- Route 10% of traffic to canary pods using Istio VirtualService
- Run comprehensive health checks on canary services
- Validate Kubernetes resource status (pods, services, ingresses)

**Traffic Configuration**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sophia-canary
spec:
  http:
  - route:
    - destination:
        host: mcp-research.sophia-canary.svc.cluster.local
      weight: 10  # Canary traffic percentage
    - destination:
        host: mcp-research.sophia.svc.cluster.local
      weight: 90  # Production traffic percentage
```

**Validation Script**: `scripts/validate_all_services.py --canary`

**Files**:
- `.github/workflows/sophia_infra.yml` (canary-deploy job)
- `scripts/validate_all_services.py`

### 4. Database Migration Stage

**Purpose**: Apply database schema changes safely

**Actions**:
- Connect to Neon database using passwordless authentication
- Apply migrations from `ops/sql/001_audit.sql`
- Use SNI connection first, fallback to `--options=endpoint=ep-...`
- Verify migration success with test queries
- Rollback migrations on failure

**Connection Strategy**:
```bash
# Primary: SNI connection
PGSSLMODE=require psql -h ${NEON_PROJECT_ID}.us-east-1.aws.neon.tech \
  -U ${NEON_USER} -d ${NEON_DB} -f ops/sql/001_audit.sql

# Fallback: Endpoint option
PGSSLMODE=require psql -h pg.neon.tech \
  -U ${NEON_USER} -d ${NEON_DB} \
  --options=endpoint=${NEON_ENDPOINT_ID} -f ops/sql/001_audit.sql
```

**Environment Variables**:
- `NEON_PROJECT_ID`: rough-union-72390895
- `NEON_ENDPOINT_ID`: ep-rough-dew-af6w48m3
- `NEON_USER`: neondb_owner
- `NEON_DB`: neondb

**Files**: `.github/workflows/sophia_infra.yml` (migrate-neon job)

### 5. Synthetic End-to-End Testing Stage

**Purpose**: Validate critical business functionality with real integrations

**Actions**:
- Test Slack messaging via `comms-mcp`
- Test CRM task creation via `crm-mcp`
- Test database connectivity via `analytics-mcp`
- Require all tests to pass (green status) before full rollout
- Generate detailed test reports

**Test Details**:

#### Slack Post Test
- **Endpoint**: `POST /slack/post`
- **Payload**: Channel, message, username
- **Expected**: HTTP 200 with success confirmation
- **Timeout**: 15 seconds

#### CRM Task Creation Test
- **Endpoint**: `POST /tasks/create`
- **Payload**: Subject, description, priority, assignee
- **Expected**: HTTP 200 with task ID
- **Timeout**: 15 seconds

#### Neon Database Test
- **Endpoint**: `POST /query/neon`
- **Payload**: SELECT 1 query
- **Expected**: HTTP 200 with query results
- **Timeout**: 15 seconds

**Validation Script**: `scripts/synthetic_checks.py`

**Files**:
- `.github/workflows/sophia_infra.yml` (synthetics job)
- `scripts/synthetic_checks.py`

### 6. Full Production Rollout Stage

**Purpose**: Deploy new version to 100% of production traffic

**Actions**:
- Update Istio VirtualService to route 100% traffic to new version
- Scale down canary deployment
- Monitor rollout progress
- Validate all services are running correctly

**Traffic Migration**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sophia-production
spec:
  http:
  - route:
    - destination:
        host: mcp-research.sophia.svc.cluster.local
      weight: 100  # Full production traffic
```

**Files**: `.github/workflows/sophia_infra.yml` (full-rollout job)

### 7. Production Readiness Check Stage

**Purpose**: Final validation of production deployment

**Actions**:
- Run comprehensive health checks on all services
- Validate service mesh configuration
- Check resource utilization and performance metrics
- Generate deployment report
- Send notifications to stakeholders

**Validation Areas**:
- Service health endpoints
- Kubernetes resource status
- Network connectivity
- Database connectivity
- Monitoring stack (Prometheus/Grafana)

**Files**:
- `.github/workflows/sophia_infra.yml` (readiness-check job)
- `scripts/validate_all_services.py --production`

## Rollback Strategy

### Automatic Rollback Triggers
- Canary deployment health check failures
- Database migration failures
- Synthetic test failures
- Production readiness check failures

### Manual Rollback Process
```bash
# Rollback services to previous version
kubectl rollout undo deployment/mcp-research -n sophia
kubectl rollout undo deployment/mcp-context -n sophia
# ... other services

# Restore database from backup if needed
PGSSLMODE=require pg_restore -h pg.neon.tech \
  -U ${NEON_USER} -d ${NEON_DB} \
  --options=endpoint=${NEON_ENDPOINT_ID} backup.sql
```

## Monitoring & Alerting

### Health Checks
- **Interval**: Every 30 seconds during deployment
- **Timeout**: 10 seconds per service
- **Failure Threshold**: 3 consecutive failures

### Alerts
- Slack notifications on deployment status
- PagerDuty integration for critical failures
- Email notifications for stakeholders

### Metrics Collected
- Response times for all services
- Error rates and success rates
- Resource utilization (CPU/Memory)
- Database connection pool status

## Configuration

### Required Secrets
```bash
# GitHub Secrets
GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
NEON_API_KEY: ${{ secrets.NEON_API_KEY }}

# Optional Secrets
SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
PAGERDUTY_INTEGRATION_KEY: ${{ secrets.PAGERDUTY_INTEGRATION_KEY }}
```

### Environment Variables
```bash
# Deployment Configuration
CANARY_PERCENTAGE: 10
PRODUCTION_TAG: v1.1.0
REGISTRY: ghcr.io

# Database Configuration
NEON_PROJECT_ID: rough-union-72390895
NEON_ENDPOINT_ID: ep-rough-dew-af6w48m3
NEON_USER: neondb_owner
NEON_DB: neondb
```

## Troubleshooting

See `operations/troubleshooting.md` for common deployment issues and solutions.

## Best Practices

1. **Always test migrations on staging first**
2. **Monitor canary traffic patterns before full rollout**
3. **Keep database backups before migrations**
4. **Use feature flags for risky changes**
5. **Monitor error rates and latency after deployment**
6. **Document all deployment changes**
7. **Test rollback procedures regularly**

## Performance Benchmarks

- **Canary Deployment**: < 5 minutes
- **Database Migration**: < 2 minutes
- **Synthetic Tests**: < 1 minute
- **Full Rollout**: < 10 minutes
- **Total Pipeline**: < 30 minutes

## Security Considerations

- All database connections use SSL/TLS
- Secrets are managed via Kubernetes secrets
- Images are scanned for vulnerabilities
- Network policies restrict service communication
- RBAC controls deployment permissions