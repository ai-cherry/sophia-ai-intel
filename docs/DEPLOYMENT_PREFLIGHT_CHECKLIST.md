# 🚀 DEPLOYMENT PREFLIGHT CHECKLIST

**Date:** 2025-08-22
**Status:** READY FOR DEPLOYMENT

---

## ✅ Go/No-Go Preflight (60-120s)

### 1. GitHub Secrets Verification
**Location:** GitHub > Settings > Secrets and variables > Actions

| Secret | Required | Status | Notes |
|--------|----------|--------|-------|
| `FLY_API_TOKEN` | ✅ Required | ✅ Available | For Fly.io deployment |
| `NEON_DATABASE_URL` | ✅ Required | ✅ Available | For mcp-context database |
| `TAVILY_API_KEY` | Optional | ✅ Available | For mcp-research |
| `SERPER_API_KEY` | Optional | ✅ Available | For mcp-research |

### 2. GitHub App Configuration
- **Installation:** ✅ Installed on `ai-cherry/sophia-ai-intel`
- **Permissions:** Contents:Read, Metadata:Read only
- **Runtime:** Uses App installation token (NOT PAT)
- **Proof:** [`proofs/github_app/created.json`](../proofs/github_app/created.json) ✅

### 3. Router Allowlist
**File:** [`proofs/llm/router_allowlist.json`](../proofs/llm/router_allowlist.json)

Best-recent models only:
```json
{
  "primary": ["gpt-5", "gpt-5-mini"],
  "fallback_order": [
    "gpt-5",
    "gpt-5-mini",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "gpt-4o",
    "gpt-4o-mini",
    "deepseek-chat"
  ]
}
```

---

## 🎯 Deploy Now (Cloud-Only)

### Deploy Command:
1. Go to **Actions** tab
2. Select **"Deploy All (Dashboard + MCPs)"**
3. Click **"Run workflow"**
4. Keep defaults (deploy all)
5. Click green **"Run workflow"** button

### Workflow will:
- ✅ Build dashboard dist with npm
- ✅ Deploy static Docker (no buildpacks)
- ✅ Deploy all MCP services
- ✅ Wait for /healthz endpoints
- ✅ Fetch /__build + /assets proofs
- ✅ Auto-commit all proofs to repo

---

## 🔍 Post-Deploy Verification (5 min)

### Health Checks (Must be 200)
- [ ] `proofs/healthz/sophiaai-dashboard.txt` → HTTP/1.1 200
- [ ] `proofs/healthz/sophiaai-mcp-repo.txt` → HTTP/1.1 200
- [ ] `proofs/healthz/sophiaai-mcp-research.txt` → HTTP/1.1 200
- [ ] `proofs/healthz/sophiaai-mcp-context.txt` → HTTP/1.1 200

### Dashboard Bundle
- [ ] `proofs/build/dashboard_build.txt` - Has BUILD_ID
- [ ] `proofs/build/dashboard_asset_head.txt` - HEAD /assets/index-*.js → 200

### MCP-Repo Functionality
- [ ] `proofs/mcp_repo/file_vite_config.json` - Real file content (base64)
- [ ] `proofs/mcp_repo/tree_dashboard.json` - Entries list

### Context MCP
- [ ] `proofs/mcp_context/index.json` - READY index
- [ ] `proofs/mcp_context/search.json` - Returned matches
- **Note:** If NEON not configured, normalized error JSON is acceptable

### If Any Health Fails:
Check `proofs/fly/<app>_logs.txt` - Last 200 lines captured automatically

---

## 🧲 Common Last-Mile Fixes

### Issue: MCP-Repo JWT
**Fix:** Ensure `PyJWT[crypto]` + `cryptography` installed
**Status:** ✅ Already fixed in `services/mcp-github/requirements.txt`

### Issue: MCP-Research Providers
**Fix:** If TAVILY/SERPER keys missing, return normalized failure
**Status:** ✅ Ready (keys available)

### Issue: MCP-Context DB
**Fix:** Only proceed if NEON_DATABASE_URL exists
**Status:** ✅ Ready (URL available)

### Issue: Dashboard Build
**Fix:** Always use `Dockerfile.static`, base: "/", Nginx with /__build + /healthz
**Status:** ✅ Configured correctly

---

## 🧭 Phase 2 Kickoff Plan

### 1. Context Indexing Pipeline
- CI job to index code/docs → publish to Context MCP (Neon) on push
- Add GET /context/index/<id> + symbol metadata

### 2. Read-Only Business MCPs
- Slack: channels, threads with CEO scopes
- Salesforce: opportunities/accounts read endpoints
- Render in Integrations tab (no writes yet)

### 3. Builder PR Workflow
- Add `.github/workflows/sophia-builder.yml`
- CEO: "@sophia propose <change>" → branch → patch → PR with proofs

### 4. Foundational Knowledge & OKRs (Notion)
- Nightly Notion sync → Company Knowledge & OKRs pages
- Pin RPE tile & OKRs at dashboard top

### 5. Observability
- /metrics in each MCP + p95 SLO alarms
- Nightly smoke: curl healthz, capture proof diffs

---

## ✅ Decision Point

**If deploy workflow finishes and proofs are committed:**
→ Stamp **PHASE 1 COMPLETE** in `docs/PHASE1_FINAL_COMPLETION.md`
→ Begin Phase 2 immediately

**If anything fails:**
→ Check `proofs/fly/<app>_logs.txt`
→ Apply fast fix from common issues above
→ Re-run workflow

---

## 📊 Current Status

| Component | Ready | Notes |
|-----------|-------|-------|
| GitHub Secrets | ✅ | All critical secrets available |
| Fly.io Apps | ✅ | All 4 apps created |
| Deploy Workflow | ✅ | `.github/workflows/deploy_all.yml` ready |
| Docker Fixes | ✅ | PyJWT, portkey-ai fixed |
| Router Config | ✅ | Best-recent models only |
| Credentials | ✅ | `.env.vault` secured |

**DEPLOYMENT STATUS: READY TO EXECUTE** 🚀