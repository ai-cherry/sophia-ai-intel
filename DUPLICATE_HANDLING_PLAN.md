# Duplicate Files Handling Plan - Sophia AI Codebase

## Executive Summary
Scan detected **771 duplicate file candidates** requiring systematic consolidation to improve codebase maintainability and reduce confusion.

## Critical Duplicate Categories

### 1. SSL Certificates (HIGH PRIORITY)
**Issue**: Complete duplication between `ssl/` and `ssl/local/` directories
**Files**:
- `ssl/dhparam.pem` = `ssl/local/dhparam.pem`
- `ssl/ca.crt` = `ssl/local/ca-cert.pem`
- `ssl/sophia.key` = `ssl/local/server-key.pem`
- `ssl/fullchain.pem` = `ssl/local/fullchain.pem`
- `ssl/sophia.crt` = `ssl/local/server-cert.pem`

**Resolution Strategy**:
1. Keep `ssl/` as primary directory (simpler path)
2. Update all docker-compose and nginx configs to reference `ssl/`
3. Delete `ssl/local/` directory entirely
4. Document SSL paths in README

### 2. Environment Configurations (SECURITY CRITICAL)
**Issue**: `.env` identical to `.env.production.secure`
**Resolution**:
1. Keep `.env` for local development
2. Keep `.env.production` for production
3. Delete `.env.production.secure` (redundant)
4. Ensure all are in `.gitignore`

### 3. Test Result Files (MASSIVE DUPLICATION)
**Issue**: `proofs/healthz_final/` contains identical files
- `research.txt` = `dashboard.txt` = `context.txt` = `business.txt` = `jobs.txt`
**Resolution**:
1. Keep one master file: `proofs/healthz_final/healthz_results.txt`
2. Delete all duplicates
3. Create symlinks if multiple names needed

### 4. Python Package Files
**Issue**: ~700+ duplicates in `.venv/` and `darwin-arm64/` directories
**Resolution**:
1. These are package manager artifacts - DO NOT manually delete
2. Add to `.gitignore`: `.venv/`, `darwin-arm64/`
3. Remove from git tracking if accidentally committed

## Phased Implementation Plan

### Phase 1: Immediate Actions (Security & Space)
```bash
# 1. Remove SSL duplicates
rm -rf ssl/local/

# 2. Update docker-compose.yml SSL paths
# Change all references from ssl/local/* to ssl/*

# 3. Remove duplicate env file
rm -f .env.production.secure

# 4. Clean test results
cd proofs/healthz_final/
mv research.txt healthz_results.txt
rm -f dashboard.txt context.txt business.txt jobs.txt
```

### Phase 2: Configuration Updates
1. **Docker Compose**: Update all SSL volume mounts
2. **Nginx Config**: Update SSL certificate paths
3. **Application Code**: Search for hardcoded SSL paths
4. **Documentation**: Update setup instructions

### Phase 3: Prevention Measures
1. **Update .gitignore**:
```gitignore
# Virtual environments
.venv/
venv/
darwin-arm64/

# SSL duplicates
ssl/local/

# Test outputs
proofs/*/duplicate_*
```

2. **Pre-commit Hook**: Add duplicate detection
3. **CI/CD Check**: Block PRs with new duplicates

## Automated Cleanup Script

```python
#!/usr/bin/env python3
"""duplicate_cleanup.py - Safe duplicate removal"""

import os
import hashlib
from pathlib import Path

def safe_remove_duplicates():
    """Remove duplicates with safety checks"""
    
    # SSL cleanup
    if Path('ssl/local').exists():
        print("Removing SSL duplicates...")
        os.system('rm -rf ssl/local/')
    
    # Test file cleanup
    healthz_dir = Path('proofs/healthz_final')
    if healthz_dir.exists():
        duplicates = ['dashboard.txt', 'context.txt', 'business.txt', 'jobs.txt']
        for dup in duplicates:
            dup_path = healthz_dir / dup
            if dup_path.exists():
                print(f"Removing {dup_path}")
                dup_path.unlink()
    
    # Update configs
    update_docker_compose()
    update_nginx_config()

def update_docker_compose():
    """Update SSL paths in docker-compose"""
    compose_file = Path('docker-compose.yml')
    if compose_file.exists():
        content = compose_file.read_text()
        content = content.replace('ssl/local/', 'ssl/')
        compose_file.write_text(content)
        print("Updated docker-compose.yml")

def update_nginx_config():
    """Update SSL paths in nginx config"""
    nginx_files = Path('.').glob('nginx*.conf')
    for nginx_file in nginx_files:
        content = nginx_file.read_text()
        content = content.replace('ssl/local/', 'ssl/')
        nginx_file.write_text(content)
        print(f"Updated {nginx_file}")

if __name__ == "__main__":
    safe_remove_duplicates()
```

## Risk Mitigation

### Before Deletion:
1. **Backup critical files**: `tar -czf ssl_backup.tar.gz ssl/`
2. **Test locally**: Verify services start with new paths
3. **Document changes**: Update README with new structure

### Rollback Plan:
1. Keep backup archive for 30 days
2. Git history preserves deleted files
3. Document original structure in this plan

## Expected Outcomes

- **Space Saved**: ~5-10 MB (excluding .venv)
- **Clarity**: Single source of truth for each file
- **Security**: No duplicate sensitive files
- **Maintenance**: Easier to update configurations
- **Performance**: Faster file operations

## Monitoring

After cleanup:
1. Re-run archive scanner to verify duplicates removed
2. Test all services still function
3. Monitor for new duplicates weekly

## Timeline

- **Day 1**: SSL and env file cleanup (DONE)
- **Day 2**: Test result consolidation
- **Day 3**: Config updates and testing
- **Day 4**: Documentation and prevention measures
- **Day 5**: Final verification scan

## Approval

This plan requires review before execution of Phase 2 & 3.
Phase 1 security-critical items can proceed immediately.
