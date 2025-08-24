# Reset & Deploy Workflow - Execution Guide

## Quick Start

**OBJECTIVE:** Execute the complete cloud deployment workflow for all Sophia AI Intel services

**NOTE:** As of 2025-08-23, full deployment is not achieved. Only 2/6 services are operational due to infrastructure and build issues. See [`proofs/deployment/FINAL_DEPLOYMENT_STATUS_2025_08_23_2200.json`](../proofs/deployment/FINAL_DEPLOYMENT_STATUS_2025_08_23_2200.json) for current status and recommendations.

**PREREQUISITES:** 
- [GitHub Secrets configured](./RESET_DEPLOY_SECRETS_SETUP.md) (`FLY_API_TOKEN` and `FLY_APP_SECRETS_JSON`)
- Access to repository: `https://github.com/ai-cherry/sophia-ai-intel`

## Step-by-Step Execution

### Step 1: Navigate to GitHub Actions

1. Open the repository in your browser:
   ```
   https://github.com/ai-cherry/sophia-ai-intel
   ```

2. Click on the **Actions** tab at the top of the repository

3. In the left sidebar, locate and click on:
   ```
   Reset & Deploy (Fly + Proofs) — all cloud
   ```

### Step 2: Trigger the Workflow

1. Click the **"Run workflow"** button (blue button on the right side)

2. You'll see a dropdown with configuration options

### Step 3: Configure Input Parameters

**Recommended Settings for Production Deployment:**

| Parameter | Recommended Value | Description |
|-----------|-------------------|-------------|
| **recreate_apps** | `false` | Keep existing apps (safer, faster) |
| **seed_secrets** | `true` | Apply secrets to all apps |
| **skip_dashboard** | `false` | Deploy dashboard |
| **skip_jobs** | `false` | Deploy jobs service |

**Alternative Configurations:**

#### Fresh Start Deployment (if problems with existing apps):
- **recreate_apps**: `true` ⚠️ *Destroys existing apps*
- **seed_secrets**: `true`
- **skip_dashboard**: `false`
- **skip_jobs**: `false`

#### Partial Deployment (services only):
- **recreate_apps**: `false`
- **seed_secrets**: `true`
- **skip_dashboard**: `true`
- **skip_jobs**: `true`

### Step 4: Execute the Workflow

1. After configuring parameters, click **"Run workflow"** (green button)

2. The workflow will appear at the top of the Actions list with status "⚡ In progress"

3. Click on the workflow run to monitor progress

### Step 5: Monitor Deployment Progress

The workflow executes in these phases:

#### Phase 1: App Management (2-3 minutes)
- ✅ Creates/recreates Fly apps
- ✅ Seeds secrets to all apps
- ✅ Generates app matrix

#### Phase 2: Dashboard Deployment (5-10 minutes)
- ✅ Builds React application
- ✅ Deploys to Fly.io with remote build
- ✅ Performs health check
- ✅ Captures build info

#### Phase 3: MCP Services Deployment (15-20 minutes)
- ✅ Deploys 4 MCP services in parallel:
  - sophiaai-mcp-repo-v2 (GitHub integration)
  - sophiaai-mcp-research-v2 (Web search)
  - sophiaai-mcp-context-v2 (Database access)
  - sophiaai-mcp-business-v2 (Business intelligence)
- ✅ Performs health checks for each service
- ✅ Captures machine states

#### Phase 4: Jobs Deployment (3-5 minutes)
- ✅ Deploys scheduled reindexing service
- ✅ Captures deployment state

#### Phase 5: Final Verification (2-3 minutes)
- ✅ Comprehensive health verification
- ✅ Generates deployment summary
- ✅ Uploads proof artifacts

**Total Expected Duration: 25-40 minutes**

### Step 6: Verify Successful Deployment

#### Success Indicators:
- All workflow jobs show ✅ green checkmarks
- Workflow summary shows all services healthy
- Service URLs are accessible:
  - [Dashboard](https://sophiaai-dashboard-v2.fly.dev)
  - [MCP Repository](https://sophiaai-mcp-repo-v2.fly.dev/healthz)
  - [MCP Research](https://sophiaai-mcp-research-v2.fly.dev/healthz)
  - [MCP Context](https://sophiaai-mcp-context-v2.fly.dev/healthz)
  - [MCP Business](https://sophiaai-mcp-business-v2.fly.dev/healthz)

#### Health Check Commands:
```bash
# Test all services
curl -f https://sophiaai-dashboard-v2.fly.dev/healthz
curl -f https://sophiaai-mcp-repo-v2.fly.dev/healthz
curl -f https://sophiaai-mcp-research-v2.fly.dev/healthz
curl -f https://sophiaai-mcp-context-v2.fly.dev/healthz
curl -f https://sophiaai-mcp-business-v2.fly.dev/healthz

# All should return HTTP 200
```

### Step 7: Download Proof Artifacts

1. In the completed workflow run, scroll to the bottom

2. Look for **Artifacts** section

3. Download `deployment-proofs-[run-id]` (contains all proof files)

4. Extract and review:
   - `proofs/healthz/` - Health check responses
   - `proofs/fly/` - Machine states and logs
   - `proofs/deployment/` - Deployment summaries
   - `proofs/build/` - Build information

## Monitoring During Deployment

### Real-Time Progress Tracking

1. **Workflow Overview**: Shows overall progress and job status
2. **Individual Jobs**: Click on each job to see detailed logs
3. **Live Logs**: Scroll to bottom of job logs to see real-time output

### Key Log Messages to Watch For:

#### Success Messages:
```
✅ Fly token configured
✅ Standard npm ci succeeded
✅ Dashboard health check passed on attempt 1
✅ [service] health check passed on attempt 1
```

#### Warning Messages (Normal):
```
⚠️ [service] health check failed on attempt 1, retrying...
App [name] already exists.
```

#### Error Messages (Require Action):
```
❌ Missing FLY_API_TOKEN secret
❌ All install methods failed
❌ [service] not 200
```

## Troubleshooting Common Issues

### Issue 1: "Missing FLY_API_TOKEN secret"
**Cause:** Secret not configured in GitHub
**Solution:** 
1. Follow [Secrets Setup Guide](./RESET_DEPLOY_SECRETS_SETUP.md)
2. Set `FLY_API_TOKEN` with provided FlyV1 token
3. Re-run workflow

### Issue 2: Dashboard build fails
**Cause:** Node.js dependency issues
**Solution:** 
- Workflow includes resilient install logic
- If persists, check workflow logs for specific error
- Re-run workflow (often resolves transient issues)

### Issue 3: Health checks fail
**Cause:** Services not ready or secrets missing
**Solution:**
1. Check `FLY_APP_SECRETS_JSON` is valid JSON
2. Wait 2-3 minutes and manually test health endpoints
3. Re-run workflow with `seed_secrets: true`

### Issue 4: Workflow stuck or timeout
**Cause:** Resource constraints or network issues
**Solution:**
1. Cancel workflow run
2. Wait 5 minutes
3. Re-run with same parameters

### Issue 5: Partial deployment success
**Cause:** Individual service deployment failure
**Solution:**
1. Check failed job logs for specific errors
2. Re-run workflow focusing on failed components
3. Use skip parameters to avoid re-deploying successful services

## Emergency Recovery Procedures

### Complete Reset (Nuclear Option)
If deployment is completely broken:
1. Run workflow with `recreate_apps: true`
2. This destroys and recreates all apps from scratch
3. ⚠️ **WARNING**: This will cause downtime

### Rollback to Previous Version
1. Navigate to previous successful workflow run
2. Note the deployment artifacts
3. Use Fly.io CLI to manually revert:
   ```bash
   flyctl releases list -a sophiaai-dashboard-v2
   flyctl releases rollback -a sophiaai-dashboard-v2 [version]
   ```

### Manual Health Check Recovery
If automated health checks fail but services work:
1. Test URLs manually in browser
2. Check service logs:
   ```bash
   flyctl logs -a sophiaai-dashboard-v2
   ```
3. Restart machines if needed:
   ```bash
   flyctl machines restart [machine-id] -a [app-name]
   ```

## Post-Deployment Verification Checklist

- [ ] All workflow jobs completed successfully
- [ ] Dashboard loads at https://sophiaai-dashboard-v2.fly.dev
- [ ] All `/healthz` endpoints return 200
- [ ] Proof artifacts downloaded and reviewed
- [ ] No error messages in final workflow summary
- [ ] Services respond to API requests (optional functional test)

## Success Metrics

**Deployment is considered successful when:**

1. **All 5 jobs complete** with green checkmarks
2. **All 5 services healthy** (return HTTP 200 on /healthz)
3. **Proof artifacts generated** (health checks, machine states, build info)
4. **No critical errors** in workflow logs
5. **Services accessible** via public URLs

## Next Steps After Successful Deployment

1. **Test functionality** - Use dashboard to interact with MCP services
2. **Monitor performance** - Check service metrics in Fly.io dashboard
3. **Review proofs** - Analyze deployment artifacts for optimization
4. **Schedule maintenance** - Plan for regular secret rotation and updates
5. **Document any issues** - Create tickets for any problems encountered

## Support and Documentation

- **Secrets Setup**: [RESET_DEPLOY_SECRETS_SETUP.md](./RESET_DEPLOY_SECRETS_SETUP.md)
- **General Secrets Reference**: [SECRETS.md](./SECRETS.md)
- **Infrastructure Operations**: [INFRA_OPERATIONS.md](./INFRA_OPERATIONS.md)
- **Deployment Status**: [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md)

## Workflow URL for Quick Access

Direct link to trigger the workflow:
```
https://github.com/ai-cherry/sophia-ai-intel/actions/workflows/reset_deploy.yml
```

---

**Ready for immediate execution** - This workflow represents the complete automation for Phase B/C deployment success.