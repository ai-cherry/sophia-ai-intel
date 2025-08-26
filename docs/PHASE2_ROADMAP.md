# 🚀 Phase 2 Roadmap - Post-Deployment Implementation

## Prerequisites
- ⚠️ Phase 1 Status: PARTIAL DEPLOYMENT — Only 2/6 services operational as of 2025-08-23. See [`proofs/deployment/FINAL_DEPLOYMENT_STATUS_2025_08_23_2200.json`](../proofs/deployment/FINAL_DEPLOYMENT_STATUS_2025_08_23_2200.json) for details.
- ⚠️ Not all healthz endpoints are healthy. See known issues in deployment proof.
- ✅ Proof artifacts committed to `proofs/` (partial, pending full deployment)

---

## Phase 2 Components

### 1. Context Indexing Pipeline (Week 1)

#### Implementation
```yaml
# .github/workflows/context_index.yml
name: Context Indexing Pipeline
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run indexer
        run: |
          # Tree-sitter or ripgrep analysis
          python scripts/index_codebase.py
      - name: POST to mcp-context
        run: |
          curl -X POST https://sophiaai-mcp-context.fly.dev/context/index \
            -H "Content-Type: application/json" \
            -d @proofs/context_index/payload.json
      - name: Commit proof
        run: |
          git add proofs/context_index/${{ github.run_id }}.json
          git commit -m "[proof] context index run ${{ github.run_id }}"
          git push
```

### 2. Read-Only Business MCPs (Week 1-2)

#### A. Slack MCP
```
services/mcp-slack/
├── Dockerfile
├── fly.toml
├── requirements.txt
└── app.py
    ├── GET /healthz
    ├── GET /slack/channels
    ├── GET /slack/threads/{channel_id}
    └── GET /slack/users
```

#### B. Salesforce MCP
```
services/mcp-salesforce/
├── Dockerfile
├── fly.toml
├── requirements.txt
└── app.py
    ├── GET /healthz
    ├── GET /salesforce/accounts
    ├── GET /salesforce/opportunities
    └── GET /salesforce/contacts
```

#### Proofs Required
- `proofs/healthz/sophiaai-mcp-slack.txt`
- `proofs/healthz/sophiaai-mcp-salesforce.txt`
- `proofs/business/slack_channels.json`
- `proofs/business/salesforce_accounts.json`

### 3. Builder PR Workflow (Week 2)

#### Workflow: `.github/workflows/sophia-builder.yml`
```yaml
name: Sophia Builder - PR from Chat
on:
  workflow_dispatch:
    inputs:
      change_request:
        description: 'Change description'
        required: true
      paths:
        description: 'Target paths'
        required: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Builder
        run: |
          python scripts/builder.py \
            --request "${{ inputs.change_request }}" \
            --paths "${{ inputs.paths }}"
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "Builder: ${{ inputs.change_request }}"
          branch: builder/${{ github.run_id }}
          
      - name: Deploy to staging
        run: |
          docker-compose deploy --app sophiaai-staging
          
      - name: Playwright screenshot
        run: |
          npx playwright test --screenshot
          
      - name: Commit proofs
        run: |
          git add proofs/builder/
          git commit -m "[proof] builder PR ${{ github.run_id }}"
```

#### CEO Dashboard Integration
```typescript
// Command in chat:
// @sophia propose "Add dark mode toggle" paths="apps/dashboard/src"
```

### 4. Notion Sync (Week 2-3)

#### Nightly Sync Workflow
```yaml
# .github/workflows/notion_sync.yml
name: Notion Knowledge & OKRs Sync
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch from Notion
        env:
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
        run: |
          python scripts/notion_sync.py \
            --database-id ${{ secrets.NOTION_KNOWLEDGE_DB }} \
            --output proofs/notion/knowledge.json
            
      - name: Update context
        run: |
          curl -X POST https://sophiaai-mcp-context.fly.dev/context/knowledge \
            -d @proofs/notion/knowledge.json
            
      - name: Extract OKRs
        run: |
          python scripts/extract_okrs.py \
            --input proofs/notion/knowledge.json \
            --output proofs/notion/okrs.json
            
      - name: Pin RPE KR in dashboard
        run: |
          echo "RPE_KR=$(jq -r '.rpe_kr' proofs/notion/okrs.json)" >> $GITHUB_ENV
```

### 5. Observability (Week 3)

#### Metrics Endpoints
```python
# Add to each MCP service
@app.get("/metrics")
async def metrics():
    return {
        "counters": {
            "requests_total": REQUESTS_TOTAL,
            "errors_total": ERRORS_TOTAL
        },
        "latencies": {
            "p50": calculate_p50(),
            "p95": calculate_p95(),
            "p99": calculate_p99()
        },
        "slo": {
            "error_rate": ERRORS_TOTAL / REQUESTS_TOTAL,
            "target": 0.05  # <5% error rate
        }
    }
```

#### Nightly Smoke Tests
```yaml
# .github/workflows/nightly_smoke.yml
name: Nightly Smoke Tests
on:
  schedule:
    - cron: '0 3 * * *'

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Check all healthz
        run: |
          for service in dashboard mcp-repo mcp-research mcp-context; do
            curl -f https://sophiaai-${service}.fly.dev/healthz
          done
          
      - name: Test minimal endpoints
        run: |
          curl -f https://sophiaai-mcp-repo.fly.dev/repo/tree
          curl -f https://sophiaai-mcp-context.fly.dev/context/search?q=test
          
      - name: Collect metrics
        run: |
          for service in mcp-repo mcp-research mcp-context; do
            curl https://sophiaai-${service}.fly.dev/metrics \
              > proofs/metrics/${service}_$(date +%Y%m%d).json
          done
          
      - name: Commit fresh proofs
        run: |
          git add proofs/
          git commit -m "[proof] nightly smoke $(date +%Y-%m-%d)"
          git push
```

---

## Implementation Timeline

### Week 1 (Immediately after Phase 1)
- [ ] Context indexing pipeline
- [ ] Slack MCP (read-only)
- [ ] Post-deploy verification script running

### Week 2
- [ ] Salesforce MCP (read-only)
- [ ] Builder PR workflow
- [ ] CEO dashboard integration

### Week 3
- [ ] Notion sync (Knowledge & OKRs)
- [ ] Observability endpoints
- [ ] Nightly smoke tests

### Week 4
- [ ] Performance optimization
- [ ] SLO monitoring
- [ ] Documentation updates

---

## Safety Notes

### 🔒 Security
- **Writes only in Actions** - Runtime uses GitHub App read-only
- **No direct DB writes** - All mutations via GitHub Actions
- **Secrets rotation** - Quarterly rotation schedule

### 📊 Reliability
- **Model fallbacks** - Router allowlist with fallback chains
- **Normalized errors** - All failures return structured JSON
- **Static Docker** - Eliminated buildpack detection issues

### 🚨 Monitoring
- **Health checks** - Every service has `/healthz`
- **Proof artifacts** - Immutable evidence trail
- **SLO targets** - p95 latency, <5% error rate

---

## Quick Commands

### Check deployment status
```bash
./scripts/post_deploy_verify.sh
```

### Trigger context indexing
```bash
gh workflow run context_index.yml
```

### Trigger builder
```bash
gh workflow run sophia-builder.yml \
  -f change_request="Add dark mode" \
  -f paths="apps/dashboard"
```

### View latest proofs
```bash
ls -la proofs/healthz/
ls -la proofs/context_index/
ls -la proofs/builder/
```

---

## Phase 2 Success Criteria

1. **Context Index**: Daily updates with proof artifacts
2. **Business MCPs**: Slack & Salesforce read-only access
3. **Builder Flow**: CEO can create PRs from chat
4. **Notion Sync**: Knowledge & OKRs updated nightly
5. **Observability**: Metrics, SLOs, and smoke tests

---

## Support & Troubleshooting

### Common Issues
- **CORS errors**: Ensure `DASHBOARD_ORIGIN` matches production URL
- **Missing secrets**: Add via GitHub Settings → Secrets → Actions
- **Import errors**: Check requirements.txt/package.json versions

### Failed Proofs
If any proof fails, check:
1. `proofs/fly/<app>_logs.txt` for deployment logs
2. GitHub Actions run logs
3. Fly.io dashboard for machine status

### Contact
- GitHub Issues: `ai-cherry/sophia-ai-intel`
- Workflow runs: https://github.com/ai-cherry/sophia-ai-intel/actions

---

**Last Updated:** 2025-08-22
**Status:** Ready for Phase 2 implementation