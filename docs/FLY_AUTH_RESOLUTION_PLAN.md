# Fly.io Authentication Issue Resolution Plan

## Problem Summary
- **Issue**: Deployment workflow fails immediately (3-5 seconds) after preflight passes
- **Pattern**: Both dashboard and MCP services fail with same pattern
- **Failed Runs**: #17162233137, #17162486592
- **Current Token**: fly_pat_9bvEjpZdQOqkLo3VZvRO75MBBzj1G1VH1GW6pKXvzKTnZCnz

## Root Cause Hypothesis
1. **Token Scope Issue**: Token may have read-only permissions
2. **Organization Mismatch**: Apps belong to different org than token
3. **Token Expiration**: Token might be expired or revoked
4. **Regional Restrictions**: Token might have regional limitations

## Resolution Strategy

### Phase 1: Diagnostic Testing (Local)

#### Step 1.1: Verify Token Authentication
```bash
# Test basic authentication
export FLY_API_TOKEN="fly_pat_9bvEjpZdQOqkLo3VZvRO75MBBzj1G1VH1GW6pKXvzKTnZCnz"
flyctl auth whoami

# Expected output: Email and organization details
# If fails: Token is invalid/expired
```

#### Step 1.2: Check Token Permissions
```bash
# List apps to verify read permissions
flyctl apps list

# Check specific app details
flyctl apps show sophiaai-dashboard
flyctl apps show sophiaai-mcp-repo
flyctl apps show sophiaai-mcp-research
flyctl apps show sophiaai-mcp-context

# If apps not visible: Organization mismatch
```

#### Step 1.3: Test Deployment Permissions
```bash
# Try to deploy a simple test app
cd /tmp
mkdir fly-test
cd fly-test
echo "FROM nginx:alpine" > Dockerfile
flyctl launch --no-deploy --name test-deploy-perms
flyctl deploy --app test-deploy-perms

# If fails: Token lacks deployment permissions
```

### Phase 2: Token Generation & Validation

#### Step 2.1: Generate New Token with Full Permissions
```bash
# Login with browser (use actual account)
flyctl auth login

# Generate new token with deployment permissions
flyctl auth token

# Document the new token securely
```

#### Step 2.2: Validate New Token Capabilities
```bash
# Set new token
export FLY_API_TOKEN="<new_token>"

# Verify authentication
flyctl auth whoami

# Check organization
flyctl orgs list

# Verify app access
flyctl apps list | grep sophiaai
```

### Phase 3: GitHub Actions Configuration

#### Step 3.1: Update GitHub Secret
```bash
# Using GitHub CLI
gh secret set FLY_API_TOKEN -b "<new_token>" \
  -R ai-cherry/sophia-ai-intel

# Verify secret was updated
gh secret list -R ai-cherry/sophia-ai-intel | grep FLY_API_TOKEN
```

#### Step 3.2: Add Debug Logging to Workflow
Update `.github/workflows/deploy_all.yml`:

```yaml
- name: Debug Fly Authentication
  env:
    FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
  run: |
    echo "::add-mask::$FLY_API_TOKEN"
    echo "Token length: ${#FLY_API_TOKEN}"
    echo "Token prefix: ${FLY_API_TOKEN:0:7}..."
    
    # Test authentication
    flyctl auth whoami || echo "Auth failed"
    
    # List organizations
    flyctl orgs list || echo "Orgs list failed"
    
    # Check app access
    flyctl apps show ${{ env.APP }} || echo "App show failed"
    
    # Test deployment permissions
    flyctl regions list -a ${{ env.APP }} || echo "Regions list failed"
```

### Phase 4: Alternative Solutions

#### Option A: Use Fly Deploy Action
Replace manual flyctl commands with official GitHub Action:

```yaml
- uses: superfly/flyctl-actions/deploy@v2
  with:
    app: ${{ env.APP }}
    config: ./fly.toml
    dockerfile: ./Dockerfile
```

#### Option B: Local-Only Deployment
Modify deployment to use local builds:

```yaml
- name: Deploy with local build
  run: |
    flyctl deploy \
      --app ${{ env.APP }} \
      --local-only \
      --config ./fly.toml \
      --dockerfile ./Dockerfile
```

#### Option C: Use Deploy Tokens
Create app-specific deploy tokens:

```bash
# For each app
flyctl tokens create deploy -a sophiaai-dashboard
flyctl tokens create deploy -a sophiaai-mcp-repo
flyctl tokens create deploy -a sophiaai-mcp-research
flyctl tokens create deploy -a sophiaai-mcp-context
```

### Phase 5: Verification & Testing

#### Step 5.1: Local Deployment Test
```bash
# Test dashboard deployment locally
cd apps/dashboard
npm ci && npm run build
flyctl deploy --local-only

# Test MCP service deployment
cd services/mcp-github
flyctl deploy --local-only
```

#### Step 5.2: Trigger GitHub Actions Test
```bash
# Trigger workflow with new token
gh workflow run deploy_all.yml \
  -f deploy_dashboard=true \
  -f deploy_services=true
  
# Monitor execution
gh run watch
```

### Phase 6: Monitoring & Validation

#### Success Criteria
1. ✅ Preflight passes with token validation
2. ✅ Dashboard builds and deploys successfully
3. ✅ All MCP services deploy without errors
4. ✅ Health checks return 200 OK
5. ✅ Proof artifacts are generated

#### Proof Collection
```bash
# After successful deployment
curl -I https://sophiaai-dashboard.fly.dev/healthz
curl -I https://sophiaai-mcp-repo.fly.dev/healthz
curl -I https://sophiaai-mcp-research.fly.dev/healthz
curl -I https://sophiaai-mcp-context.fly.dev/healthz

# Save deployment logs
gh run view <run_id> --log > proofs/deployment/success_logs.txt
```

## Timeline Estimate
- Phase 1 (Diagnostic): 15 minutes
- Phase 2 (Token Generation): 10 minutes
- Phase 3 (GitHub Config): 10 minutes
- Phase 4 (Alternative Setup): 20 minutes (if needed)
- Phase 5 (Testing): 15 minutes
- Phase 6 (Validation): 10 minutes

**Total: 1-1.5 hours**

## Risk Mitigation
1. **Backup Current Token**: Save current token before generating new one
2. **Test in Staging**: Create test apps first before modifying production
3. **Rollback Plan**: Keep workflow backups before modifications
4. **Documentation**: Document all changes and new tokens securely

## Next Steps
1. Switch to Code mode to execute Phase 1 diagnostics
2. Based on findings, proceed with appropriate solution
3. Update GitHub secrets and workflow as needed
4. Verify deployment success
5. Commit all proof artifacts