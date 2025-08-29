# 🧹 Cleanup & Remediation Plan

## Overview
Based on the recent audit findings from your other AI agent, this plan addresses the cleanup of archived files and duplicate handling to improve security, organization, and efficiency.

## ✅ Completed Actions

### Archived Files Removed (16.29 MB freed)
- ✅ Removed sensitive backup files (`.env.production.real.backup`, `.env.production.secure.bak`)
- ✅ Deleted script backups (`run-sophia-locally.sh.backup`, `synthetic_checks.py.backup`)
- ✅ Removed large archive (`helm.tar.gz` - 16.24 MB)
- ✅ Cleaned old deployment reports and deprecated files

## 📋 Immediate Actions Required

### Phase 1: Security & Critical Cleanup (TODAY)

#### 1. SSL Certificate Consolidation
```bash
# Backup current SSL configuration
cp -r ssl/ ssl_backup_$(date +%Y%m%d)/

# Consolidate certificates
mv ssl/local/* ssl/
rmdir ssl/local/

# Update Docker and Nginx configs
find . -name "*.yml" -o -name "*.conf" | xargs grep -l "ssl/local" | xargs sed -i 's|ssl/local|ssl|g'
```

#### 2. Environment File Cleanup
```bash
# Remove redundant production secure file
rm .env.production.secure

# Ensure all services use standard .env files
grep -r "\.env\.production\.secure" services/ apps/ --include="*.py" --include="*.js" --include="*.ts"
```

#### 3. Update .gitignore
```bash
cat >> .gitignore << 'EOF'

# Virtual environments
.venv/
venv/
env/

# Platform-specific builds
darwin-arm64/
linux-amd64/
windows-amd64/

# Test outputs
proofs/
test-results/
coverage/

# Backup files
*.backup
*.bak
*.old

# SSL certificates (local development)
ssl/local/
*.pem
*.key
*.crt

# Archive files
*.tar.gz
*.zip
EOF
```

### Phase 2: Test Results Consolidation

#### 1. Merge Duplicate Test Files
```bash
# Remove duplicate health check results
cd proofs/healthz_final/
for file in healthz_test_*; do
  if [ -f "../$file" ]; then
    rm "$file"
  fi
done
cd ../..
```

#### 2. Create Test Result Archive
```bash
# Archive old test results
mkdir -p archive/test-results-$(date +%Y%m%d)
mv proofs/* archive/test-results-$(date +%Y%m%d)/
```

### Phase 3: Prevention Measures

#### 1. Pre-commit Hook Setup
```bash
# Create pre-commit hook to prevent duplicates
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Prevent committing backup and duplicate files

# Check for backup files
if git diff --cached --name-only | grep -E '\.(backup|bak|old)$'; then
  echo "Error: Backup files detected. Remove them before committing."
  exit 1
fi

# Check for duplicate SSL certificates
if git diff --cached --name-only | grep -E 'ssl/local/'; then
  echo "Error: Use ssl/ directory instead of ssl/local/"
  exit 1
fi

# Check for large archives
if git diff --cached --name-only | grep -E '\.(tar\.gz|zip)$'; then
  echo "Warning: Archive files should not be committed"
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

#### 2. Automated Cleanup Script
```bash
cat > scripts/cleanup-duplicates.sh << 'EOF'
#!/bin/bash
# Automated cleanup script for duplicate files

echo "🧹 Starting cleanup..."

# Remove backup files
find . -name "*.backup" -o -name "*.bak" -o -name "*.old" -type f -delete

# Remove empty directories
find . -type d -empty -delete

# Report duplicate files
fdupes -r . > duplicate_report.txt

echo "✅ Cleanup complete. Check duplicate_report.txt for remaining duplicates."
EOF

chmod +x scripts/cleanup-duplicates.sh
```

## 🎯 Expected Outcomes

### Immediate Benefits
- **Security**: No sensitive backup files exposed
- **Space**: 16.29 MB freed (potential 5-10 MB additional)
- **Organization**: Clear directory structure

### Long-term Benefits
- **Maintenance**: Easier codebase navigation
- **CI/CD**: Faster builds without unnecessary files
- **Collaboration**: Cleaner git history

## 📊 Metrics & Validation

### Success Criteria
- [ ] Zero `.backup`, `.bak`, `.old` files in repository
- [ ] Single SSL certificate directory
- [ ] No duplicate test result files
- [ ] Updated .gitignore preventing future issues
- [ ] Pre-commit hooks active

### Validation Commands
```bash
# Check for remaining backup files
find . -name "*.backup" -o -name "*.bak" -o -name "*.old" | wc -l

# Check for duplicate SSL directories
ls -la ssl/

# Verify gitignore updates
git check-ignore .venv/test.txt

# Test pre-commit hook
touch test.backup && git add test.backup && git commit -m "test"
```

## 🔄 Rollback Plan

If issues arise:
1. Restore SSL backup: `cp -r ssl_backup_*/ ssl/`
2. Revert gitignore: `git checkout HEAD -- .gitignore`
3. Remove pre-commit hook: `rm .git/hooks/pre-commit`

## 📅 Timeline

- **Hour 1**: Phase 1 - Security & Critical Cleanup
- **Hour 2**: Phase 2 - Test Results Consolidation  
- **Hour 3**: Phase 3 - Prevention Measures
- **Hour 4**: Validation & Documentation

## ⚠️ Risk Mitigation

### Before Starting
1. Create full backup: `tar -czf sophia-backup-$(date +%Y%m%d).tar.gz .`
2. Document current file structure
3. Notify team of maintenance window

### During Cleanup
1. Test each change incrementally
2. Verify services still function after config updates
3. Keep detailed log of changes

### After Completion
1. Run full test suite
2. Verify all services healthy
3. Monitor for 24 hours

## 🚀 Next Steps

After completing this cleanup:
1. Implement continuous monitoring for duplicates
2. Set up automated weekly cleanup job
3. Document file organization standards
4. Train team on new conventions

---

**Note**: This plan complements the test coverage implementation currently in progress. Both initiatives will significantly improve code quality and maintainability.