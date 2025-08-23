# Reset & Deploy Workflow - Secrets Configuration

## Overview

The `Reset & Deploy (Fly + Proofs) — all cloud` workflow requires two critical GitHub secrets to be configured for complete cloud deployment automation.

## Required GitHub Secrets

### 1. FLY_API_TOKEN (Critical - Deployment Access)

**Purpose:** Authenticates with Fly.io to create/manage apps and perform deployments
**Format:** FlyV1 token (starts with `fm2_`)
**Scope:** Full organization access to `pay-ready` org

**Value to use:**
```
fm2_lJPE...
```
*(Use the complete FlyV1 token provided in the deployment request)*

### 2. FLY_APP_SECRETS_JSON (Critical - Runtime Configuration)

**Purpose:** Seeds all Fly apps with runtime secrets (API keys, database URLs, etc.)
**Format:** JSON object with key-value pairs of environment variables
**Scope:** Applied to all deployed services

**Value to use:**
```json
{
  "OPENAI_API_KEY": "sk-svcacct-...",
  "PORTKEY_API_KEY": "...",
  "NEON_DATABASE_URL": "...",
  "TAVILY_API_KEY": "...",
  "SERPER_API_KEY": "...",
  "GITHUB_APP_ID": "...",
  "GITHUB_INSTALLATION_ID": "...",
  "GITHUB_PRIVATE_KEY": "..."
}
```
*(Use the OPENAI_API_KEY provided: `sk-svcacct-...` and add other available secrets)*

## Setting Up Secrets in GitHub

### Method 1: GitHub Web Interface

1. Navigate to repository settings:
   ```
   https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions
   ```

2. Click "New repository secret"

3. For `FLY_API_TOKEN`:
   - **Name:** `FLY_API_TOKEN`
   - **Value:** `fm2_lJPE...` *(the complete FlyV1 token)*

4. For `FLY_APP_SECRETS_JSON`:
   - **Name:** `FLY_APP_SECRETS_JSON`
   - **Value:** The complete JSON object with all available secrets

### Method 2: GitHub CLI

```bash
# Set FLY_API_TOKEN
gh secret set FLY_API_TOKEN --repo ai-cherry/sophia-ai-intel
# When prompted, paste: fm2_lJPE...

# Set FLY_APP_SECRETS_JSON
gh secret set FLY_APP_SECRETS_JSON --repo ai-cherry/sophia-ai-intel
# When prompted, paste the complete JSON object
```

### Method 3: From File (Recommended for JSON)

```bash
# Create temporary file with secrets JSON
cat > /tmp/app_secrets.json <<'EOF'
{
  "OPENAI_API_KEY": "sk-svcacct-...",
  "PORTKEY_API_KEY": "...",
  "NEON_DATABASE_URL": "...",
  "TAVILY_API_KEY": "...",
  "SERPER_API_KEY": "...",
  "GITHUB_APP_ID": "...",
  "GITHUB_INSTALLATION_ID": "...",
  "GITHUB_PRIVATE_KEY": "..."
}
EOF

# Set secret from file
gh secret set FLY_APP_SECRETS_JSON --repo ai-cherry/sophia-ai-intel < /tmp/app_secrets.json

# Clean up
rm /tmp/app_secrets.json
```

## Verification

After setting the secrets, verify they are configured:

```bash
# List all secrets (names only, values are hidden)
gh secret list --repo ai-cherry/sophia-ai-intel

# Should show:
# FLY_API_TOKEN
# FLY_APP_SECRETS_JSON
# ... (other existing secrets)
```

## Workflow Input Options

The workflow supports these configuration inputs:

- **recreate_apps** (boolean, default: false)
  - `true`: Destroys and recreates all Fly apps (fresh start)
  - `false`: Uses existing apps (safer, faster)

- **seed_secrets** (boolean, default: true)
  - `true`: Applies FLY_APP_SECRETS_JSON to all apps
  - `false`: Skips secrets seeding (uses existing secrets)

- **skip_dashboard** (boolean, default: false)
  - `true`: Skips dashboard deployment
  - `false`: Deploys dashboard

- **skip_jobs** (boolean, default: false)
  - `true`: Skips jobs service deployment
  - `false`: Deploys jobs service

## Security Notes

### Token Security
- **Never commit secrets to code** - Always use GitHub Secrets
- **Rotate tokens regularly** - Update FLY_API_TOKEN periodically
- **Minimal permissions** - Use tokens with only required scopes
- **Audit access** - Monitor who can access repository secrets

### JSON Formatting
- **Validate JSON** - Ensure FLY_APP_SECRETS_JSON is valid JSON
- **Escape quotes** - Use proper JSON escaping for string values
- **No trailing commas** - JSON must be strictly formatted

### Example Valid JSON:
```json
{
  "OPENAI_API_KEY": "sk-svcacct-...",
  "DATABASE_URL": "postgresql://user:pass@host:5432/db",
  "API_KEY_WITH_QUOTES": "value\"with\"quotes"
}
```

## Troubleshooting

### Common Issues

**1. Workflow fails with "Missing FLY_API_TOKEN"**
- **Cause:** Secret not set or incorrectly named
- **Fix:** Set `FLY_API_TOKEN` secret with valid Fly.io token

**2. Apps created but secrets not set**
- **Cause:** Invalid JSON in `FLY_APP_SECRETS_JSON`
- **Fix:** Validate JSON format, ensure no trailing commas

**3. Authentication errors during deployment**
- **Cause:** Expired or invalid Fly token
- **Fix:** Generate new token from Fly.io dashboard and update secret

**4. Services deploy but fail health checks**
- **Cause:** Missing runtime secrets (API keys, database URLs)
- **Fix:** Check `FLY_APP_SECRETS_JSON` contains all required secrets

### Validation Commands

```bash
# Test Fly.io token locally
export FLY_API_TOKEN="fm2_lJPE..."
flyctl auth whoami

# Validate JSON locally
echo '{"key": "value"}' | jq .

# Check app secrets are set
flyctl secrets list -a sophiaai-dashboard-v2
```

## Related Documentation

- [Fly.io Token Management](https://fly.io/docs/flyctl/auth/)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Complete Secrets Reference](./SECRETS.md)
- [Deployment Status](./DEPLOYMENT_STATUS.md)

## Emergency Recovery

If deployment fails due to secrets issues:

1. **Check workflow logs** for specific error messages
2. **Verify secrets** are set correctly in GitHub
3. **Test tokens locally** using flyctl/curl
4. **Re-run workflow** with corrected secrets
5. **Use recreate_apps: true** for complete reset if needed

## Success Indicators

After successful secret setup and workflow execution:

- ✅ All Fly apps created/updated successfully
- ✅ Secrets seeded to all services
- ✅ Health checks pass for all services
- ✅ Proof artifacts uploaded
- ✅ Deployment summary generated

The workflow will provide comprehensive proof artifacts and health verification to confirm successful cloud deployment.