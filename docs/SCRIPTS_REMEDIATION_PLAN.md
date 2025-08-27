# Sophia AI Scripts Remediation Plan

## Overview
This plan addresses the cleanup of scripts in the `scripts/` directory (and subdirectories) based on a comprehensive analysis of the codebase. The goal is to remove or update one-time use scripts that no longer serve an important purpose, while preserving essential ongoing functionality. The analysis identified 60+ scripts, with ~40% appearing to be one-time or migration-related.

### Key Findings
- **Total Scripts**: 62 (including subdirs like load_testing)
- **One-Time/Migration Scripts**: 25 (e.g., deployment fixes, legacy audits)
- **Testing/Validation Scripts**: 15 (many can be consolidated)
- **Setup/Configuration Scripts**: 12 (some outdated post-K8s migration)
- **Active/Essential Scripts**: 10 (e.g., health checks, monitoring)
- **Potential Savings**: Remove ~30 files, reduce maintenance burden by 50%

Scripts were categorized based on naming patterns, content (via read_file on samples), and usage in the codebase (via search_files for references). Focus on post-migration cleanup from Fly.io/Render to Kubernetes/Lambda Labs.

## Remediation Strategy
1. **Backup First**: Create a git branch or archive directory before changes.
2. **Categorize & Action**: Group scripts and apply actions (delete, update, consolidate).
3. **Validation**: Run tests (e.g., `scripts/validate_all_services.py`) post-cleanup.
4. **Documentation**: Update `docs/OPERATIONAL_RUNBOOK.md` with remaining scripts.
5. **Git History**: Use `git filter-branch` if removing sensitive data.

### Phase 1: Immediate Removal (One-Time Use Scripts)
These are migration-specific or fix scripts no longer needed in K8s environment.
- `comprehensive-404-fix.sh`: One-time fix for legacy error.
- `deploy-minimal.sh`: Legacy minimal deployment script.
- `flyio-cleanup.py`: Fly.io removal script (completed).
- `fix-kubeconfig-permissions.sh`: One-time Kubeconfig fix.
- `fix_qdrant_health_check.py`: Legacy Qdrant fix.
- `fly-*.sh` (all 6): Fly.io related, superseded.
- `neon_fix_conn.py`, `neon_reset_password.py`: One-time Neon fixes.
- `phase0-preflight.py`, `phase4-legacy-audit.py`: Phase-specific audits (completed).

**Action**: Delete these 15+ files. 
**Rationale**: No references in active code; phases completed per proofs/.
**Command**: `rm scripts/{list of files}` then `git add -A && git commit -m "Remove obsolete one-time scripts"`.

### Phase 2: Update & Consolidate (Outdated but Useful)
These have ongoing value but need updates for current architecture.
- `deploy-production-secure.sh`: Update to reference only K8s (remove Docker refs).
- `env-production-validation.sh`: Enhance with K8s-specific checks.
- `generate-secure-secrets.sh`: Integrate with `k8s-deploy/scripts/create-all-secrets.sh`.
- `health_check_*.{py,sh}` (3 files): Consolidate into single `comprehensive-health-check.sh`.
- `setup_*.sh` (SSL, monitoring): Merge duplicates (e.g., simple vs comprehensive).

**Action**: Use replace_in_file to update paths/references; delete duplicates.
**Rationale**: Referenced in docs/; essential for operations but redundant.
**Estimated Changes**: 8 files updated, 4 deleted.

### Phase 3: Retain & Document (Essential Scripts)
Keep these as they support ongoing operations.
- `check-deployment-status.sh`: Core monitoring.
- `external_api_connectivity_test.py`: Integration testing.
- `init_databases.py`: DB setup.
- `load_testing/*`: Performance testing suite.
- `validate_all_services.py`: Validation.

**Action**: Add comments/headers explaining purpose; update README.md.
**Rationale**: Actively used; no alternatives.

### Risks & Mitigations
- **Breakage**: Test full deployment cycle post-cleanup.
- **Dependencies**: Search for script references before deletion.
- **Recovery**: Use git for rollback.

### Timeline
- **Day 1**: Backup & Phase 1 removal.
- **Day 2**: Phase 2 updates.
- **Day 3**: Validation & documentation.

This plan ensures a leaner codebase while maintaining functionality. Toggle to Act mode if you'd like me to implement any phase.
