# Sophia Infra — CEO-Gated Control Plane

## Overview

Comprehensive infrastructure operations control plane for Sophia AI Intel, providing CEO-gated access to all production providers through a unified workflow interface. All operations require manual approval and generate proof artifacts for audit trails.

## Architecture

### Trust Boundaries
- **Runtime Services**: Use GitHub App (read-only access)  
- **Infrastructure Operations**: Use GitHub Actions secrets (write operations)
- **CEO Control**: All production changes require manual approval via environment gates

### Canonical Environment

#### Fly.io (Production Apps)
- **Organization**: Pay Ready (`pay-ready`)
- **Apps**: 
  - `sophiaai-dashboard-v2` - React dashboard
  - `sophiaai-mcp-repo-v2` - GitHub repository MCP
  - `sophiaai-mcp-research-v2` - Web research MCP
  - `sophiaai-mcp-context-v2` - Context database MCP

#### Provider Status Matrix
Based on [`proofs/secrets/matrix.json`](../proofs/secrets/matrix.json):

| Provider | Status | Required Secrets | Present |
|----------|--------|------------------|---------|
| **fly** | ✅ ready | FLY_API_TOKEN | ✅ |
| **github_app** | ✅ ready | GITHUB_APP_ID, GITHUB_INSTALLATION_ID, GITHUB_PRIVATE_KEY | ✅ |
| **router** | ⚠️ partial | PORTKEY_API_KEY | ✅ (backup providers missing) |
| **research** | ✅ ready | TAVILY_API_KEY, SERPER_API_KEY | ✅ |
| **context_db** | ✅ ready | NEON_DATABASE_URL | ✅ |
| **qdrant** | ⏸️ paused | QDRANT_URL, QDRANT_API_KEY | ❌ |
| **mem0** | ⏸️ paused | MEM0_API_KEY | ❌ |
| **redis** | ⏸️ paused | REDIS_URL | ❌ |
| **slack** | ⏸️ paused | SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET | ❌ |
| **gong** | ⏸️ paused | GONG_BASE_URL, GONG_ACCESS_KEY | ❌ |
| **lambda** | ⏸️ paused | LAMBDA_LABS_API_KEY | ❌ |

## Front Door Control Interface

### Workflow: `.github/workflows/sophia_infra.yml`

**Trigger**: Manual dispatch (CEO approval required via `environment: production`)

**Inputs**:
- `provider`: Select provider (fly, github, router, qdrant, mem0, redis, slack, gong, lambda, context_db, research)
- `action`: Select operation (varies by provider)
- `app`: App name (Fly operations only)
- `payload_json`: Operation-specific JSON payload

**Routing**: Automatically routes to provider-specific workflows in `.github/workflows/providers/`

### Example Operations

#### Fly Operations
```yaml
provider: fly
action: health
app: sophiaai-dashboard-v2
```

```yaml
provider: fly
action: deploy
app: sophiaai-mcp-research-v2
```

```yaml
provider: fly
action: set-secrets
app: sophiaai-mcp-context-v2
payload_json: '{"secret_names": ["NEON_DATABASE_URL"]}'
```

#### Research Operations
```yaml
provider: research
action: search
payload_json: '{"query": "AI infrastructure trends", "max_results": 10}'
```

#### GitHub Operations
```yaml
provider: github
action: protect
payload_json: '{"required_checks": ["Deploy All"], "require_review": true}'
```

## Provider-Specific Operations

### Fly Operations (`fly_ops.yml`)
**Ready** - Full implementation
- `health`: Check `/healthz` endpoints
- `deploy`: Deploy individual applications
- `machines`: List Fly machines and status
- `logs`: Show recent application logs (last 30 minutes)
- `set-secrets`: Update app secrets (values masked, names logged)

**Features**:
- GraphQL proofs (viewer orgs, app ownership)
- Automatic Node.js setup for dashboard builds  
- Explicit `--access-token` and `--org` on all docker-compose commands
- Health verification with retry logic
- Proof collection: `proofs/fly/`, `proofs/healthz/`

### Router Operations (`router_ops.yml`)
**Partial** - Primary provider ready
- `allowlist`: Generate LLM provider allowlist
- `route-test`: Test route (stub - needs implementation)

**Features**:
- Multi-provider support (Portkey, OpenAI, Anthropic, OpenRouter, Groq, DeepSeek)
- Fallback routing strategy
- Proof collection: `proofs/llm/router_allowlist.json`

### GitHub Operations (`github_ops.yml`)
**Ready** - Full implementation
- `protect`: Update branch protection rules
- `audit`: List Actions secrets (names only, values never exposed)

**Features**:
- GitHub App authentication
- Branch protection with CODEOWNERS requirement
- Secrets audit with security controls
- Proof collection: `proofs/github/`, `proofs/repo/`

### Research Operations (`research_ops.yml`)
**Ready** - Full implementation
- `search`: Execute web searches via Tavily/Serper
- `validate`: Test API connectivity

**Features**:
- Dual provider support (Tavily + Serper)
- API validation with health checks
- Proof collection: `proofs/research/`

### Context Database Operations (`context_db_ops.yml`)
**Ready** - Full implementation
- `ping`: Basic database connectivity test
- `health`: Extended health check with schema info
- `query`: Execute custom SQL (read-only recommended)

**Features**:
- PostgreSQL client setup
- Connection validation
- Safe query execution
- Proof collection: `proofs/context_db/`

### Paused Providers
All paused providers return normalized errors when secrets are missing:

- **Qdrant** (`qdrant_ops.yml`): Vector database operations
- **Mem0** (`mem0_ops.yml`): Memory management operations  
- **Redis** (`redis_ops.yml`): Cache operations
- **Slack** (`slack_ops.yml`): Channel and messaging operations
- **Gong** (`gong_ops.yml`): Call recording operations
- **Lambda** (`lambda_ops.yml`): GPU compute operations

## Proof System

### Normalized Error Format
All operations use consistent error reporting:
```json
{
  "status": "failure",
  "query": "<operation>",
  "results": [],
  "summary": {
    "text": "<what failed>",
    "confidence": 1.0,
    "model": "n/a",
    "sources": []
  },
  "timestamp": "2025-08-22T19:01:22.352Z",
  "execution_time_ms": 0,
  "errors": [
    {
      "provider": "<system>",
      "code": "<error_code>",
      "message": "<human readable description>"
    }
  ]
}
```

### Proof Directories
```
proofs/
├── fly/                    # Fly.io operations
│   ├── viewer.json         # GraphQL org membership
│   ├── *_org.json         # App org ownership
│   ├── *_machines.json    # Machine status
│   └── *_logs.txt         # Application logs
├── healthz/               # Health check responses
├── github/                # GitHub operations
│   ├── secrets_audit.json # Secrets list (names only)
│   └── protection_*.json  # Branch protection
├── llm/                   # LLM router operations
│   └── router_allowlist.json # Provider allowlist
├── research/              # Research operations
│   ├── tavily_search.json
│   └── serper_search.json
├── context_db/            # Database operations
├── qdrant/                # Vector database (when configured)
├── redis/                 # Cache operations (when configured)
├── slack/                 # Slack operations (when configured)
└── secrets/               # Secrets management
    ├── matrix.json        # Provider status matrix
    └── github_api_blocked.json # API limitations
```

## Security Controls

### CEO Approval Gate
- All operations require `environment: production` approval
- Manual trigger only - no automated infrastructure changes
- GitHub audit trail for all approvals

### Secret Handling
- Values never logged or exposed in workflows
- Only secret names are recorded in proofs
- Secrets sourced from GitHub Actions secrets store
- Automatic masking in workflow logs

### Trust Boundaries
- Runtime services (MCP servers) use GitHub App with read-only access
- Infrastructure operations use Actions secrets with write capabilities
- Clear separation between runtime and infrastructure contexts

## Usage Examples

### Deploy Dashboard
1. Navigate to GitHub Actions → Sophia Infra
2. Run workflow:
   - Provider: `fly`
   - Action: `deploy` 
   - App: `sophiaai-dashboard-v2`
3. CEO approves in production environment
4. Dashboard builds and deploys automatically
5. Health check verifies deployment
6. Proofs committed to repository

### Update Branch Protection
1. Navigate to GitHub Actions → Sophia Infra
2. Run workflow:
   - Provider: `github`
   - Action: `protect`
   - Payload: `{"required_checks": ["Deploy All"], "require_review": true}`
3. CEO approves operation
4. Branch protection rules updated
5. Proof committed to `proofs/repo/branch_protection.json`

### Research Web Search
1. Run workflow:
   - Provider: `research`
   - Action: `search`
   - Payload: `{"query": "AI infrastructure trends", "max_results": 10}`
2. CEO approves (if needed)
3. Searches executed via Tavily and Serper APIs
4. Results stored in `proofs/research/`

## Troubleshooting

### Common Issues

**Workflow Dispatch Blocked**
```
Error: Resource not accessible by integration (HTTP 403)
```
Solution: Manual trigger required from GitHub UI - CLI/API dispatch lacks permissions

**Fly GraphQL Auth Failed**
```  
{"errors": [{"message": "You must be authenticated to view this."}]}
```
Solution: Current token is org-scoped, lacks GraphQL access - GraphQL proofs show auth failures

**Provider Not Configured**
```
{"status": "failure", "errors": [{"code": "not-configured", "message": "REDIS_URL not set"}]}
```
Solution: Add required secrets to GitHub Actions secrets

### Provider Activation

To activate paused providers:
1. Add required secrets to GitHub Actions
2. Secrets appear in next matrix generation
3. Provider status changes from "paused" to "ready"
4. Operations become available immediately

### Secret Management

View current status: [`proofs/secrets/matrix.json`](../proofs/secrets/matrix.json)
Secret mapping: [`.infra/secrets_map.json`](../.infra/secrets_map.json)

Add secrets via GitHub UI: Settings → Secrets and variables → Actions

## Integration with Deploy All

The existing [`deploy_all.yml`](../.github/workflows/deploy_all.yml) workflow has been updated to:
- Use Pay Ready org (`pay-ready`) exclusively
- Target canonical `-v2` app names
- Pass `--access-token` on every docker-compose command
- Pass `--org` on app creation
- Generate comprehensive proofs

Both workflows coexist:
- **Deploy All**: Full production deployment of all services
- **Sophia Infra**: Individual provider operations with CEO control

## Future Enhancements

### GraphQL Access
- Generate user token for Fly GraphQL API access
- Enable real-time org/app ownership verification
- Automated infrastructure topology mapping

### Advanced Proofs
- Build artifact checksums and signatures
- Performance metrics collection
- Security vulnerability scanning
- Infrastructure cost tracking

### Enhanced Automation
- Automated rollback capabilities
- Blue-green deployment patterns
- Infrastructure drift detection
- Policy compliance validation

## Quick Reference

**Trigger Sophia Infra**: GitHub UI → Actions → Sophia Infra → Run workflow

**Check Provider Status**: View `proofs/secrets/matrix.json`

**View Recent Operations**: `git log --oneline | grep "\[proof\]"`

**Emergency Fly Operations**: 
```bash
docker-compose status -a sophiaai-dashboard-v2 --access-token "$TOKEN"
docker-compose logs -a sophiaai-dashboard-v2 --access-token "$TOKEN"
```

**Add New Provider**: 
1. Create workflow in `.github/workflows/providers/`
2. Add to front door routing in `sophia_infra.yml` 
3. Update secrets matrix
4. Document operations in this file