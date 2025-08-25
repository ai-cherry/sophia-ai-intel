# Secrets Configuration Guide

## Overview
This document describes the canonical environment variables required by each service in the Sophia AI Intel platform and how to configure them in GitHub Actions for deployment.

## Canonical Environment Variables by Service

### Dashboard (`apps/dashboard`)
**Build-time only variables:**
- `VITE_BUILD_ID` (optional) - Build identifier for cache busting
- `VITE_GIT_COMMIT` (optional) - Git commit hash for versioning

**Notes:** No runtime secrets required. Variables are injected during build process.

### MCP Repository Service (`services/mcp-github`)
**Required:**
- `GITHUB_APP_ID` - GitHub App identifier
- `GITHUB_INSTALLATION_ID` - GitHub App installation ID for the repository
- `GITHUB_PRIVATE_KEY` - Private key for GitHub App authentication (can be base64 encoded)

**Optional:**
- `GITHUB_REPO` - Default repository to operate on (format: `owner/repo`)

**Error Handling:** Service returns normalized error JSON when credentials are missing.

### MCP Research Service (`services/mcp-research`)
**Required:**
- `PORTKEY_API_KEY` - API key for Portkey LLM routing

**Optional:**
- `TAVILY_API_KEY` - API key for Tavily search provider
- `SERPER_API_KEY` - API key for Serper search provider

**Error Handling:** `/search` endpoint returns normalized error if no search providers are configured.

### MCP Context Service (`services/mcp-context`)
**Required:**
- `NEON_DATABASE_URL` - PostgreSQL connection string for Neon database

**Error Handling:** Service returns normalized error JSON and reports NOT READY if database is unavailable.

### Router Service
**Required:**
- `PORTKEY_API_KEY` - API key for Portkey LLM routing

**Optional:**
- `OPENROUTER_API_KEY` - API key for OpenRouter as fallback provider

### Slack Integration (future)
**Required:**
- `SLACK_BOT_TOKEN` - Bot token for Slack API
- `SLACK_SIGNING_SECRET` - Secret for verifying Slack requests

**Optional:**
- `SLACK_APP_TOKEN` - App-level token for Socket Mode (if used)

### Salesforce Integration (future)
**Required:**
- `SALESFORCE_CLIENT_ID` - OAuth client ID
- `SALESFORCE_CLIENT_SECRET` - OAuth client secret
- `SALESFORCE_USERNAME` - Salesforce username
- `SALESFORCE_PASSWORD` - Salesforce password
- `SALESFORCE_SECURITY_TOKEN` - Security token for API access
- `SALESFORCE_DOMAIN` - Salesforce instance domain

### Vector Database Options

#### Qdrant (default)
**Optional:**
- `QDRANT_URL` - Qdrant server URL
- `QDRANT_API_KEY` - API key for Qdrant authentication

#### Weaviate
**Optional:**
- `WEAVIATE_REST_ENDPOINT` - REST API endpoint
- `WEAVIATE_GRPC_ENDPOINT` - gRPC endpoint
- `WEAVIATE_API_KEY` - API key for Weaviate

### Redis Cache
**Optional:**
- `REDIS_URL` - Redis connection string

## Setting Secrets in GitHub Actions

### Step 1: Add Secrets to Repository
Navigate to your repository settings:
```
https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions
```

Click "New repository secret" and add each required secret.

### Step 2: Critical Secrets Required for Deployment

At minimum, you need:
- `FLY_API_TOKEN` - For deploying to Fly.io (already configured)

For full functionality, add:
- `GITHUB_APP_ID`
- `GITHUB_INSTALLATION_ID`
- `GITHUB_PRIVATE_KEY`
- `PORTKEY_API_KEY`
- `NEON_DATABASE_URL`

### Step 3: Using GitHub CLI
You can also set secrets using the GitHub CLI (values not shown for security):

```bash
# Set a secret
gh secret set GITHUB_APP_ID --repo ai-cherry/sophia-ai-intel

# List secrets (names only)
gh secret list --repo ai-cherry/sophia-ai-intel

# Set from file (useful for private keys)
gh secret set GITHUB_PRIVATE_KEY --repo ai-cherry/sophia-ai-intel < private-key.pem
```

## Deployment Workflow Integration

The `deploy_all.yml` workflow automatically:
1. Reads secrets from GitHub Actions
2. Sets them as Fly.io app secrets for each service
3. Only sets secrets that are defined (handles optional secrets gracefully)

Example from workflow:
```yaml
- name: Set Fly secrets (names only)
  env:
    TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
    SERPER_API_KEY: ${{ secrets.SERPER_API_KEY }}
  run: |
    if [ "${TAVILY_API_KEY}" != "" ]; then
      flyctl secrets set TAVILY_API_KEY=${TAVILY_API_KEY} -a ${{ matrix.app }}
    fi
```

## Canonical Environment Variables (Sophia Infra Control Plane)

### Provider Mapping
Based on [`proofs/secrets/matrix.json`](../proofs/secrets/matrix.json) and [`.infra/secrets_map.json`](../.infra/secrets_map.json):

#### Fly.io Operations
- `FLY_API_TOKEN` → `FLY_API_TOKEN` ✅ Ready

#### GitHub App Operations
- `GITHUB_APP_ID` → `GITHUB_APP_ID` ✅ Ready
- `GITHUB_INSTALLATION_ID` → `GITHUB_INSTALLATION_ID` ✅ Ready
- `GITHUB_PRIVATE_KEY` → `GITHUB_APP_PRIVATE_KEY` ✅ Ready

#### LLM Router Operations
- `PORTKEY_API_KEY` → `PORTKEY_API_KEY` ✅ Ready
- `OPENAI_API_KEY` → `OPENAI_API_KEY` ✅ Ready
- `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY` ✅ Ready
- `OPENROUTER_API_KEY` → null ❌ Missing
- `GROQ_API_KEY` → null ❌ Missing
- `DEEPSEEK_API_KEY` → null ❌ Missing

#### Research Operations
- `TAVILY_API_KEY` → `TAVILY_API_KEY` ✅ Ready
- `SERPER_API_KEY` → `SERPER_API_KEY` ✅ Ready

#### Context Database Operations
- `NEON_DATABASE_URL` → `NEON_DATABASE_URL` ✅ Ready

#### Vector Database (Paused)
- `QDRANT_URL` → null ❌ Missing
- `QDRANT_API_KEY` → null ❌ Missing

#### Memory Management (Paused)
- `MEM0_API_KEY` → null ❌ Missing

#### Cache Operations (Paused)
- `REDIS_URL` → null ❌ Missing

#### Slack Integration (Paused)
- `SLACK_BOT_TOKEN` → null ❌ Missing
- `SLACK_SIGNING_SECRET` → null ❌ Missing
- `SLACK_APP_TOKEN` → null ❌ Missing

#### Gong Integration (Paused)
- `GONG_BASE_URL` → null ❌ Missing
- `GONG_ACCESS_KEY` → null ❌ Missing
- `GONG_ACCESS_KEY_SECRET` → null ❌ Missing
- `GONG_CLIENT_ACCESS_KEY` → null ❌ Missing
- `GONG_CLIENT_SECRET` → null ❌ Missing

#### DNS Management (Infrastructure)
- `DNSIMPLE_TOKEN` → null ❌ Missing
- `DNSIMPLE_ACCOUNT_ID` → "162809" (hardcoded)

#### Lambda Labs Compute (Paused)  
- `LAMBDA_LABS_API_KEY` → null ❌ Missing
- `LAMBDA_API_CLOUD_ENDPOINT` → null ❌ Missing
- `LAMBDA_SSH_PRIVATE_KEY` → null ❌ Missing

## Current Status (as of 2025-08-22)

### ✅ Ready Providers (4)
- **fly**: Full deployment and operations capabilities
- **github_app**: Branch protection and secrets auditing
- **context_db**: Database operations via Neon PostgreSQL
- **research**: Web search via Tavily and Serper APIs

### ⚠️ Partial Providers (1)
- **router**: Primary provider (Portkey) ready, backup providers missing

### ⏸️ Paused Providers (6)
- **qdrant**: Vector database operations (needs QDRANT_URL)
- **mem0**: Memory management (needs MEM0_API_KEY)
- **redis**: Cache operations (needs REDIS_URL)
- **slack**: Messaging operations (needs SLACK_BOT_TOKEN)
- **gong**: Call recording operations (needs GONG_BASE_URL)
- **lambda**: GPU compute operations (needs LAMBDA_LABS_API_KEY)

### 📊 Summary
- **10 secrets found** out of 23 total expected
- **Ready for production**: Fly deployments, GitHub operations, database access, web research
- **Missing critical infrastructure**: Vector storage, caching, messaging, compute

## Security Best Practices

1. **Never commit secrets to code** - Always use environment variables
2. **Use GitHub Secrets** - Store all sensitive values in GitHub Actions secrets
3. **Rotate regularly** - Update API keys and tokens periodically
4. **Minimal permissions** - Use tokens with only required scopes
5. **Base64 encode if needed** - For multi-line secrets like private keys:
   ```bash
   cat private-key.pem | base64 | gh secret set GITHUB_PRIVATE_KEY --repo ai-cherry/sophia-ai-intel
   ```

## Troubleshooting

### Service returns "missing credentials" error
1. Check `proofs/secrets/matrix.json` for missing secrets list
2. Verify secret is set in GitHub Actions
3. Check workflow logs to ensure secret was passed to Fly.io
4. Use `flyctl secrets list -a <app-name>` to verify on Fly.io

### Authentication failures
1. Verify token format (e.g., Fly tokens start with `fo1_`)
2. Check for extra spaces or newlines in secret values
3. Ensure tokens haven't expired
4. Test locally with export commands before setting in GitHub

## Sophia Infra Control Plane Integration

The [`sophia_infra.yml`](../.github/workflows/sophia_infra.yml) workflow provides CEO-gated access to all providers:

```yaml
# Example: Deploy dashboard
provider: fly
action: deploy
app: sophiaai-dashboard-v2

# Example: Update branch protection
provider: github
action: protect
payload_json: '{"required_checks": ["Deploy All"]}'

# Example: Search web
provider: research
action: search
payload_json: '{"query": "AI infrastructure trends", "max_results": 10}'
```

All operations require manual CEO approval via `environment: production`.

## Adding New Providers

To activate paused providers:

1. **Add secrets to GitHub Actions**:
   ```bash
   gh secret set REDIS_URL --repo ai-cherry/sophia-ai-intel
   gh secret set QDRANT_URL --repo ai-cherry/sophia-ai-intel
   gh secret set QDRANT_API_KEY --repo ai-cherry/sophia-ai-intel
   ```

2. **Verify in secrets matrix**:
   - Next workflow run will update `proofs/secrets/matrix.json`
   - Provider status changes from "paused" to "ready"
   - Operations become available immediately

3. **Test via Sophia Infra**:
   ```yaml
   provider: qdrant
   action: health
   ```

## Related Documentation

- [Sophia Infra Operations](docs/INFRA_OPERATIONS.md)
- [Deployment Workflow](.github/workflows/deploy_all.yml)
- [Secrets Matrix](proofs/secrets/matrix.json)
- [Secrets Mapping](.infra/secrets_map.json)
- [External Services Config](docs/ROO_EXTERNAL_SERVICES_CONFIG.md)
