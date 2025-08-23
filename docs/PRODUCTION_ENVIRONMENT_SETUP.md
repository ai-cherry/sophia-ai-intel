# Production Environment Setup Guide

## Overview

This document outlines the setup process for GitHub Environments with production-grade security and approval workflows for the Sophia AI Intel deployment infrastructure.

## GitHub Environment Configuration

### 1. Create Production Environment

Navigate to your repository settings and create a new environment:

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Configure protection rules as outlined below

### 2. Environment Protection Rules

#### Required Reviewers
- **Reviewer**: CEO/Repository Owner
- **Required review count**: 1
- **Prevent self-review**: ✅ Enabled
- **Required review from CODEOWNERS**: ✅ Enabled

#### Deployment Branches
- **Selected branches only**:
  - `main`
  - `release/*`
- **Protected branches only**: ✅ Enabled

#### Environment Secrets Restriction
- **Environment secrets**: Restrict to selected environments
- **Selected environments**: `production` only

### 3. Environment Secrets Configuration

The following secrets must be configured at the environment level:

#### Core Infrastructure Secrets
```bash
# Fly.io Production Secrets
FLY_API_TOKEN=<production-fly-token>
FLY_ORG=pay-ready

# Application Secrets (JSON formatted)
FLY_APP_SECRETS_JSON='{
  "NEON_DATABASE_URL": "<production-neon-url>",
  "QDRANT_URL": "<production-qdrant-url>",
  "QDRANT_API_KEY": "<production-qdrant-key>",
  "REDIS_URL": "<production-redis-url>",
  "OPENAI_API_KEY": "<production-openai-key>",
  "ANTHROPIC_API_KEY": "<production-anthropic-key>",
  "GITHUB_TOKEN": "<production-github-token>",
  "PERPLEXITY_API_KEY": "<production-perplexity-key>",
  "TELEGRAM_BOT_TOKEN": "<production-telegram-token>",
  "TELEGRAM_CHAT_ID": "<production-telegram-chat>"
}'
```

#### GitHub API Access
```bash
GITHUB_TOKEN=<production-github-token>
```

#### External Service Providers
```bash
# LLM Providers
OPENAI_API_KEY=<production-openai-key>
ANTHROPIC_API_KEY=<production-anthropic-key>
PERPLEXITY_API_KEY=<production-perplexity-key>

# Infrastructure Services
NEON_DATABASE_URL=<production-neon-url>
QDRANT_URL=<production-qdrant-url>
QDRANT_API_KEY=<production-qdrant-key>
REDIS_URL=<production-redis-url>

# Communication
TELEGRAM_BOT_TOKEN=<production-telegram-token>
TELEGRAM_CHAT_ID=<production-telegram-chat>
```

## Workflow Integration

### 1. Update Workflow Files

Add environment protection to deployment workflows:

```yaml
name: Production Deploy
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy to Production
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
          FLY_APP_SECRETS_JSON: ${{ secrets.FLY_APP_SECRETS_JSON }}
        run: |
          echo "Deploying to ${{ inputs.environment }}"
          # Deployment commands here
```

### 2. CEO Approval Workflow

When a production deployment is triggered:

1. **Automatic Hold**: Deployment will pause and request CEO approval
2. **Notification**: CEO receives email notification of pending deployment
3. **Review Process**: 
   - CEO reviews the changes and deployment request
   - CEO can view the full diff and deployment plan
   - CEO approves or rejects the deployment
4. **Execution**: Upon approval, deployment proceeds automatically

### 3. Deployment Verification

Each production deployment includes comprehensive verification:

#### Health Check SLOs
- **Target**: 3 consecutive 200 responses within 90 seconds
- **Retry Policy**: 8 attempts with 15-20 second intervals
- **Rollback Trigger**: Automatic rollback on SLO failure

#### Service Verification Matrix
```yaml
services:
  dashboard: "https://sophiaai-dashboard-v2.fly.dev/healthz"
  mcp-repo: "https://sophiaai-mcp-repo-v2.fly.dev/healthz"
  mcp-research: "https://sophiaai-mcp-research-v2.fly.dev/healthz"
  mcp-context: "https://sophiaai-mcp-context-v2.fly.dev/healthz"
  mcp-business: "https://sophiaai-mcp-business-v2.fly.dev/healthz"
```

## Security Considerations

### 1. Secret Management
- **Environment Isolation**: Production secrets isolated from staging/development
- **Rotation Policy**: Regular secret rotation (quarterly minimum)
- **Access Logging**: All secret access logged and monitored
- **Principle of Least Privilege**: Each service gets only required secrets

### 2. Deployment Security
- **Branch Protection**: Only protected branches can deploy to production
- **Required Reviews**: CEO approval required for all production changes
- **Audit Trail**: Complete deployment history and approval logs
- **Rollback Capability**: Automatic rollback on failure detection

### 3. Monitoring and Alerting
- **Health Monitoring**: Continuous health check monitoring
- **Performance Metrics**: Response time and availability tracking
- **Alert Integration**: Slack/email alerts for production issues
- **Deployment Notifications**: Success/failure notifications to stakeholders

## Emergency Procedures

### 1. Emergency Rollback
```bash
# Manual rollback command
flyctl releases rollback <previous-version> -a <app-name> --yes

# Automated rollback (configured in workflows)
# Triggers automatically on health check failures
```

### 2. Emergency Bypass
In critical situations where CEO approval bypass is required:

1. Use the `emergency-deploy` workflow (requires 2 admin approvals)
2. Document the emergency in the deployment commit message
3. Follow up with CEO notification within 1 hour
4. Complete post-emergency review within 24 hours

### 3. Incident Response
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Determine impact and severity
3. **Response**: Execute appropriate recovery procedures
4. **Communication**: Notify stakeholders via configured channels
5. **Resolution**: Implement fix and verify restoration
6. **Post-mortem**: Document incident and improve processes

## Compliance and Auditing

### 1. Deployment Audit Trail
- All deployments logged with timestamps and approvers
- Complete change history maintained in Git
- Deployment artifacts preserved for 90 days minimum

### 2. Access Control Audit
- Regular review of environment access permissions
- Documentation of all secret access and modifications
- Quarterly access certification by CEO

### 3. Compliance Reporting
- Monthly deployment summary reports
- Security incident documentation
- Performance and availability metrics

## Best Practices

### 1. Deployment Timing
- **Preferred Windows**: Tuesday-Thursday, 10 AM - 2 PM EST
- **Avoid**: Fridays, weekends, holidays, or outside business hours
- **Emergency Only**: Weekend/holiday deployments for critical issues

### 2. Change Management
- **Small Batches**: Deploy small, incremental changes when possible
- **Testing**: Comprehensive testing in staging before production
- **Documentation**: Clear deployment notes and rollback plans
- **Communication**: Stakeholder notification for significant changes

### 3. Monitoring
- **Pre-deployment**: Verify staging environment health
- **During deployment**: Real-time monitoring of deployment progress
- **Post-deployment**: Extended monitoring for 24 hours minimum
- **Performance**: Baseline performance metrics before/after changes

## Troubleshooting

### Common Issues and Solutions

#### 1. Environment Secret Access Issues
```bash
# Verify environment configuration
gh api repos/:owner/:repo/environments/production

# Check secret availability
gh secret list --env production
```

#### 2. Approval Timeout
- Default timeout: 30 days
- CEO notification escalation after 24 hours
- Emergency bypass procedures available

#### 3. Deployment Failures
- Automatic rollback triggered on health check failures
- Manual intervention available through Fly.io dashboard
- Complete deployment logs available in GitHub Actions

#### 4. Health Check Failures
- Investigate service logs: `flyctl logs -a <app-name>`
- Check machine status: `flyctl status -a <app-name>`
- Review recent deployments: `flyctl releases -a <app-name>`

## Contact Information

### Support Escalation
1. **Primary**: Repository administrators
2. **Secondary**: Fly.io support (for infrastructure issues)
3. **Emergency**: CEO direct contact

### Service Providers
- **Fly.io**: Infrastructure platform
- **GitHub**: CI/CD and approval workflows
- **External Services**: As configured in secrets

---

*This document is maintained by the infrastructure team and reviewed quarterly by the CEO.*