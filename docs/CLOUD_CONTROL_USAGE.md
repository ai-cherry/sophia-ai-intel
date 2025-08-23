# Cloud Control Usage Guide

## Overview

The enhanced [`reset_deploy.yml`](.github/workflows/reset_deploy.yml:1) workflow now provides complete cloud-based deployment control with three distinct modes of operation:

- **🚀 `deploy`**: Normal deployment (existing behavior)
- **🛑 `cancel`**: Cancel all in-progress workflow runs
- **⏹️ `stop`**: Emergency stop all Fly machines gracefully

## Operation Modes

### 1. Deploy Mode (Default)

**Purpose**: Normal deployment of all services to Fly.io

**Usage**: 
1. Navigate to Actions → "Reset & Deploy (Fly + Proofs) — all cloud"
2. Click "Run workflow"
3. Select `deploy` from the mode dropdown
4. Configure additional options as needed:
   - `recreate_apps`: Force recreate all Fly apps (destroys existing)
   - `seed_secrets`: Seed secrets to all apps from FLY_APP_SECRETS_JSON
   - `skip_dashboard`: Skip dashboard deployment
   - `skip_jobs`: Skip jobs deployment

**Expected Outcome**:
- Creates/recreates Fly apps as configured
- Deploys dashboard (unless skipped)
- Deploys all MCP services (mcp-repo, mcp-research, mcp-context, mcp-business)
- Deploys jobs service (unless skipped)
- Performs comprehensive health checks
- Generates deployment proofs and summaries

**Services Deployed**:
- Dashboard: https://sophiaai-dashboard-v2.fly.dev
- MCP Repository: https://sophiaai-mcp-repo-v2.fly.dev
- MCP Research: https://sophiaai-mcp-research-v2.fly.dev
- MCP Context: https://sophiaai-mcp-context-v2.fly.dev
- MCP Business: https://sophiaai-mcp-business-v2.fly.dev
- Jobs: https://sophiaai-jobs-v2.fly.dev

### 2. Cancel Mode

**Purpose**: Emergency cancellation of runaway or stuck deployment workflows

**Usage**:
1. Navigate to Actions → "Reset & Deploy (Fly + Proofs) — all cloud"
2. Click "Run workflow" 
3. Select `cancel` from the mode dropdown
4. Click "Run workflow" to execute

**Expected Outcome**:
- Immediately cancels all in-progress runs of the reset_deploy.yml workflow
- Excludes the current cancellation run from being cancelled
- Provides summary of cancelled operations
- Fast execution (typically under 1 minute)

**Use Cases**:
- Deployment is taking too long or appears stuck
- Wrong configuration was used for deployment
- Emergency situation requiring immediate halt of deployment activities
- Need to stop multiple concurrent deployment runs

### 3. Stop Mode

**Purpose**: Emergency stop of all running Fly machines without destroying infrastructure

**Usage**:
1. Navigate to Actions → "Reset & Deploy (Fly + Proofs) — all cloud"
2. Click "Run workflow"
3. Select `stop` from the mode dropdown  
4. Click "Run workflow" to execute

**Expected Outcome**:
- Discovers all Fly apps from [`fly.toml`](apps/dashboard/fly.toml:1) files in the repository
- Gracefully stops all running machines across all discovered apps
- Does NOT destroy apps or data - machines can be restarted later
- Provides comprehensive stop operation summary
- Fast execution (typically 2-3 minutes)

**Use Cases**:
- Emergency resource conservation (stop billing for running machines)
- Maintenance window - need to halt all services temporarily
- Security incident - immediate service shutdown required
- Cost control - temporary service suspension

## Safety Features

### Concurrency Control
- Only one deployment can run at a time per branch
- [`cancel-in-progress: true`](.github/workflows/reset_deploy.yml:29) prevents conflicts

### Permissions Model
- [`actions: write`](.github/workflows/reset_deploy.yml:34) permission required for cancel operations
- [`contents: write`](.github/workflows/reset_deploy.yml:32) for proof artifacts
- Minimal required permissions for each operation type

### Rollback Protection
- Automatic rollback on deployment failures
- Previous version detection and restoration
- Health check validation before considering deployment successful

## Emergency Procedures

### Runaway Deployment
```bash
# Use cancel mode to stop all active runs
Mode: cancel
Expected time: < 1 minute
```

### Service Outage Response  
```bash
# Use stop mode for immediate service halt
Mode: stop
Expected time: 2-3 minutes
# All services will be gracefully stopped
```

### Recovery After Emergency Stop
```bash
# Use deploy mode to restart services
Mode: deploy
# Services will be redeployed and restarted
# No data loss - apps and volumes preserved
```

## Monitoring & Observability

### Proof Artifacts
All operations generate comprehensive proof files:
- **Health checks**: `proofs/healthz/`
- **Machine states**: `proofs/fly/`  
- **Deployment summaries**: `proofs/deployment/`
- **Build artifacts**: `proofs/build/`

### GitHub Actions Summary
Each run provides detailed summary including:
- Operation mode and status
- Service health status
- Direct links to all deployed services
- Proof artifact locations

### Real-time Logs
- Live workflow execution logs in GitHub Actions
- Flyctl command output for transparency
- Health check results with retry attempts
- Machine state transitions

## Advanced Configuration

### Environment Variables
```yaml
FLY_ORG: pay-ready                    # Target Fly.io organization
FLY_PRIMARY_REGION: iad              # Primary deployment region  
DASHBOARD_URL: https://sophiaai-dashboard-v2.fly.dev
# ... additional service URLs
```

### Secrets Required
- `FLY_API_TOKEN`: Fly.io API authentication
- `FLY_APP_SECRETS_JSON`: Application secrets (optional)

### Timeouts
- **Deploy mode**: Up to 60 minutes for services, 30 minutes for dashboard/jobs
- **Cancel mode**: 5 minutes maximum
- **Stop mode**: 10 minutes maximum

## Troubleshooting

### Cancel Mode Not Working
- Check if you have `actions: write` permissions
- Verify the workflow name matches exactly
- Try manually cancelling from GitHub Actions UI

### Stop Mode Incomplete
- Some machines may not respond to stop commands
- Check Fly.io dashboard for machine states
- Use Fly CLI manually: `flyctl machines stop <id> -a <app>`

### Deploy Mode Failures
- Check FLY_API_TOKEN validity
- Verify Fly.io organization access
- Review deployment logs for specific errors
- Automatic rollback should restore previous version

## Best Practices

1. **Always use Cancel first** before Stop in emergency situations
2. **Monitor proof artifacts** for deployment validation
3. **Check service health** after any emergency operations
4. **Document emergency actions** in incident reports
5. **Test control modes** in non-production environments first

## Quick Reference

| Mode | Purpose | Time | Destructive | Recovery |
|------|---------|------|-------------|----------|
| `deploy` | Normal deployment | 20-60min | No* | N/A |
| `cancel` | Stop workflows | <1min | No | Resume manually |
| `stop` | Halt services | 2-3min | No | Redeploy |

*Recreate mode (`recreate_apps: true`) is destructive

---

**For immediate assistance with cloud control operations, reference this guide and check the latest workflow run logs in GitHub Actions.**