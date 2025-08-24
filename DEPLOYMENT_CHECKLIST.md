# Sophia AI Intel Migration - Deployment Checklist

## Prerequisites Checklist

### 1. GitHub Organization Secrets Configuration ⚠️ REQUIRED FIRST
Navigate to: `https://github.com/orgs/ai-cherry/settings/secrets/actions`

**Required Secrets** (must be set at organization level):
```
✅ Core Infrastructure
- RENDER_API_TOKEN          # From render.com account settings
- PULUMI_ACCESS_TOKEN        # From pulumi.com account settings

✅ Database & Storage (Existing)
- NEON_DATABASE_URL         # Already configured
- NEON_API_KEY             # Already configured
- REDIS_ACCOUNT_KEY        # Already configured
- REDIS_DATABASE_ENDPOINT  # Already configured

✅ Vector & Memory Services (New - Need to Set)
- QDRANT_API_KEY           # From qdrant.io account
- QDRANT_URL              # Your Qdrant cluster URL
- MEM0_API_KEY            # From mem0.ai account

✅ GPU Compute (Existing)
- LAMBDA_API_KEY          # Already configured
- LAMBDA_PRIVATE_SSH_KEY  # Already configured
- LAMBDA_PUBLIC_SSH_KEY   # Already configured

✅ AI/LLM APIs (Existing)
- ANTHROPIC_API_KEY       # Already configured
- OPENAI_API_KEY         # Already configured

✅ Business Integrations (Existing)
- HUBSPOT_API_TOKEN      # Already configured
- GITHUB_TOKEN           # Already configured

✅ Workflow Automation (New - Need to Set)
- N8N_API_KEY            # From n8n.cloud account
- AIRBYTE_API_KEY        # From airbyte.com account
```

### 2. External Service Accounts Setup ⚠️ ONE-TIME SETUP

**New Accounts to Create:**
1. **Render.com**
   - Sign up at: https://render.com
   - Create API token in Account Settings
   - Add to GitHub secrets as `RENDER_API_TOKEN`

2. **Pulumi.com**  
   - Sign up at: https://pulumi.com
   - Create access token in Settings
   - Add to GitHub secrets as `PULUMI_ACCESS_TOKEN`

3. **Qdrant.io**
   - Sign up at: https://qdrant.io
   - Create cluster and get API key
   - Add to GitHub secrets as `QDRANT_API_KEY` and `QDRANT_URL`

4. **Mem0.ai**
   - Sign up at: https://mem0.ai  
   - Generate API key in dashboard
   - Add to GitHub secrets as `MEM0_API_KEY`

**Optional Services (can be configured later):**
5. **n8n.cloud** - Add `N8N_API_KEY` if using n8n Cloud
6. **Airbyte.com** - Add `AIRBYTE_API_KEY` if using Airbyte Cloud

### 3. GitHub CLI Authentication ✅ READY
```bash
# Verify GitHub CLI is authenticated
gh auth status

# If not authenticated, run:
gh auth login
```

## Deployment Steps

### Step 1: Validate Prerequisites
```bash
# Run validation script
python scripts/automated_migration_setup.py
```

**Expected Output:**
```
🚀 Starting Automated Migration Setup...
============================================================

📋 Prerequisites...
✅ GitHub CLI authenticated
✅ Repository access confirmed

📋 GitHub Secrets...
✅ Found 13 existing organization secrets
✅ All required secrets are available

📋 Workflow Files...
✅ Created automated deployment workflow

📋 Validation Script...
✅ Created environment validation script

📋 Health Check Script...
✅ Created health check script

📋 DNS Cutover Script...
✅ Created DNS cutover script

📋 Render CLI Fallback...
✅ Created Render CLI fallback script

============================================================
✅ Automated Migration Setup Complete!
```

### Step 2: Execute Automated Migration
```bash
# Trigger the automated deployment workflow
gh workflow run automated_render_migration.yml
```

### Step 3: Monitor Progress
```bash
# Check workflow status
gh run list --limit 3

# View detailed logs
gh run view --log
```

## Deployment Timeline

**Total Time: ~30-45 minutes**

1. **Environment Validation** (5 minutes)
   - Secret verification
   - Service configuration validation
   
2. **Infrastructure Setup** (10-15 minutes)
   - Pulumi provisioning
   - External service configuration
   - Neon branch creation
   - Qdrant collections setup
   
3. **Service Deployment** (10-15 minutes)
   - 9 services deployed in parallel
   - Health checks for each service
   
4. **DNS Cutover & Validation** (5-10 minutes)
   - DNS record updates
   - Final health validation
   - Migration completion report

## Success Indicators

### ✅ Deployment Success
- All 9 services show "Healthy" status
- Health endpoints respond with 200 OK
- DNS propagation completed
- Final validation report shows 100% success

### ⚠️ Troubleshooting
If deployment fails:

1. **Check GitHub Actions logs:**
   ```bash
   gh run view --log
   ```

2. **Use Render CLI fallback:**
   ```bash
   ./scripts/render_cli_fallback.sh
   ```

3. **Individual service health check:**
   ```bash
   python scripts/health_check.py [service-name]
   ```

## Post-Migration Verification

### Service URLs (After Migration)
- **Dashboard**: https://sophia-dashboard.onrender.com
- **Research API**: https://sophia-research.onrender.com/healthz
- **Context API**: https://sophia-context.onrender.com/healthz
- **GitHub API**: https://sophia-github.onrender.com/healthz
- **Business API**: https://sophia-business.onrender.com/healthz
- **Lambda API**: https://sophia-lambda.onrender.com/healthz
- **HubSpot API**: https://sophia-hubspot.onrender.com/healthz
- **Orchestrator**: https://sophia-orchestrator.onrender.com/healthz

### Validation Commands
```bash
# Full validation suite
python scripts/final_validation.py

# Check specific service
curl https://sophia-research.onrender.com/healthz

# View migration report
cat validation_report.json
```

## Emergency Procedures

### Rollback to Fly.io (if needed)
1. Update DNS records back to Fly.io endpoints
2. Restart Fly.io services: `flyctl apps restart [app-name]`
3. Monitor service recovery

### Render Service Restart
```bash
# Via Render CLI
render service restart sophia-research

# Via API
curl -X POST https://api.render.com/v1/services/[service-id]/restart \
  -H "Authorization: Bearer $RENDER_API_TOKEN"
```

## Ready to Deploy? 

**✅ YES** - If all secrets are configured and accounts created  
**❌ NO** - Complete the prerequisites section first

**Next Command:**
```bash
python scripts/automated_migration_setup.py
