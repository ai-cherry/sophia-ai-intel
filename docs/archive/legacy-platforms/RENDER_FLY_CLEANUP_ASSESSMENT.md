# Render and Fly.io Complete Cleanup Assessment

**Date:** August 25, 2025  
**Objective:** Ensure pure Lambda Labs Kubernetes deployment with zero legacy platform references

## Executive Summary

This assessment provides guidance on handling remaining Render and Fly.io references to achieve a clean, Lambda Labs Kubernetes-only codebase.

## 1. Render References Analysis

### 1.1 Documentation Files (KEEP - Historical Context)
These files provide historical context and migration history. They should be **ARCHIVED** but not deleted:

- `docs/RENDER_MIGRATION_PLAN.md` - Historical migration plan
- `docs/PULUMI_MIGRATION_COMPLETE.md` - Documents completed migration away from Render
- `docs/AUTOMATED_MIGRATION_IMPROVEMENTS.md` - Process improvements documentation
- `DEPLOYMENT_PLAN_COMPLETE.md.backup` - Backup of deployment completion
- `CODESPACES_SECRET_REFRESH.md` - References old secrets, needs update

**Recommendation:** Move to `docs/archive/legacy-platforms/` directory

### 1.2 GitHub Workflows (REMOVE - Active Code)
These workflows are actively harmful and must be **REMOVED**:

- `.github/workflows/deploy_render.yml` - Render deployment workflow
- `.github/workflows/providers/render_ops.yml` - Render operations provider
- `.github/workflows/nightly_health_proofs.yml` - Contains Render URLs
- `.github/workflows/sophia_infra.yml` - References Render platform

**Action Required:** Delete these workflows immediately

### 1.3 Pulumi/Ops Files (REMOVE - Deployment Code)
These are deployment configurations that conflict with Kubernetes:

- `ops/pulumi/render_migration.py` - Render migration script
- `ops/pulumi/components/render_service.py` - Render service components
- `ops/pulumi/automated_infrastructure.py` - Contains RENDER_API_TOKEN references
- Any `render.yaml` files

**Action Required:** Delete entire ops/pulumi directory if not used for Lambda Labs

### 1.4 Virtual Environment (IGNORE - Auto-generated)
- `ops/pulumi/venv/` - Python virtual environment, auto-generated
- These are not source code and should be in .gitignore

**Action Required:** Add `ops/pulumi/venv/` to .gitignore

### 1.5 Scripts (UPDATE - Remove References)
- `scripts/setup_secrets.sh` - Contains Render setup instructions
- `scripts/final_validation.py` - References render.yaml and Render API

**Action Required:** Update these scripts to remove Render references

## 2. Fly.io Status

Based on previous removal efforts:
- ✅ All fly.toml files removed
- ✅ Fly.io workflows removed
- ✅ Fly.io specific scripts removed

## 3. Recommended Actions

### Immediate Actions (Critical)

1. **Remove Active Workflows**
```bash
rm -f .github/workflows/deploy_render.yml
rm -f .github/workflows/providers/render_ops.yml
rm -rf ops/pulumi/  # If not needed for Lambda Labs
```

2. **Update Remaining Workflows**
- Clean `.github/workflows/nightly_health_proofs.yml`
- Clean `.github/workflows/sophia_infra.yml`

3. **Archive Historical Documentation**
```bash
mkdir -p docs/archive/legacy-platforms/
mv docs/RENDER_MIGRATION_PLAN.md docs/archive/legacy-platforms/
mv docs/PULUMI_MIGRATION_COMPLETE.md docs/archive/legacy-platforms/
mv docs/AUTOMATED_MIGRATION_IMPROVEMENTS.md docs/archive/legacy-platforms/
```

### Follow-up Actions

1. **Update .gitignore**
```
# Virtual environments
ops/pulumi/venv/
venv/
.venv/
```

2. **Update Scripts**
- Remove Render references from `scripts/setup_secrets.sh`
- Remove Render validation from `scripts/final_validation.py`

3. **Documentation Updates**
- Update `DEPLOYMENT_CHECKLIST.md` to remove Render references
- Update `DOCUMENTATION_AUDIT_REPORT.md` to reflect current state

## 4. Verification Checklist

After cleanup, verify:
- [ ] No active GitHub workflows reference Render or Fly.io
- [ ] No deployment scripts contain Render/Fly.io logic
- [ ] All Kubernetes manifests use Lambda Labs configuration
- [ ] Documentation clearly states Lambda Labs as the only deployment target
- [ ] No environment variables reference RENDER_* or FLY_*

## 5. Clean State Definition

A clean codebase for Lambda Labs Kubernetes should have:
- **Zero active deployment code** for Render/Fly.io
- **Historical documentation archived** in docs/archive/
- **Pure Kubernetes manifests** in k8s-deploy/
- **Lambda Labs specific scripts** in scripts/
- **Updated CI/CD** targeting only Kubernetes

## Conclusion

The project requires immediate removal of active Render deployment code while preserving historical documentation for reference. This will ensure a clean, conflict-free Lambda Labs Kubernetes deployment environment.
