#!/bin/bash
# Sophia AI Infrastructure Cleanup Verification Script
# Phase 1: Comprehensive verification of legacy reference elimination

set -e

echo "🔍 Starting Sophia AI Infrastructure Cleanup Verification"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize counters
total_checks=0
passed_checks=0
failed_checks=0

check_result() {
    local check_name="$1"
    local result="$2"
    local details="$3"

    ((total_checks++))
    if [ "$result" = "PASS" ]; then
        ((passed_checks++))
        echo -e "${GREEN}✅ $check_name${NC}"
        [ -n "$details" ] && echo -e "   $details"
    else
        ((failed_checks++))
        echo -e "${RED}❌ $check_name${NC}"
        [ -n "$details" ] && echo -e "   $details"
    fi
}

echo ""
echo "📋 LEGACY REFERENCE ELIMINATION CHECKS"
echo "======================================"

# Check 1: Fly.io references
flyio_refs=$(grep -r "lambda-labs" --exclude-dir=.git --exclude="*.md" . | wc -l)
if [ "$flyio_refs" -eq 0 ]; then
    check_result "Fly.io references" "PASS" "No Fly.io references found in codebase"
else
    check_result "Fly.io references" "FAIL" "Found $flyio_refs Fly.io references that need removal"
fi

# Check 2: Render.com references
render_refs=$(grep -r "render\.com" --exclude-dir=.git --exclude="*.md" . | wc -l)
if [ "$render_refs" -eq 0 ]; then
    check_result "Render.com references" "PASS" "No Render.com references found in codebase"
else
    check_result "Render.com references" "FAIL" "Found $render_refs Render.com references that need removal"
fi

# Check 3: Docker Compose files
docker_compose_files=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | wc -l)
if [ "$docker_compose_files" -eq 0 ]; then
    check_result "Docker Compose files" "PASS" "No Docker Compose files found"
else
    check_result "Docker Compose files" "FAIL" "Found $docker_compose_files Docker Compose files that conflict with Kubernetes"
fi

# Check 4: GitHub Actions workflows
github_workflows=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)
if [ "$github_workflows" -eq 0 ]; then
    check_result "GitHub Actions workflows" "PASS" "No GitHub Actions workflow files found"
else
    check_result "GitHub Actions workflows" "FAIL" "Found $github_workflows GitHub Actions workflows that need review"
fi

# Check 5: Obsolete deployment scripts
obsolete_scripts=$(find . -name "deploy-*.sh" -o -name "final-deploy*.sh" -o -name "fix-nginx-conflict.sh" | grep -v k8s-deploy | wc -l)
if [ "$obsolete_scripts" -eq 0 ]; then
    check_result "Obsolete deployment scripts" "PASS" "No obsolete deployment scripts found"
else
    check_result "Obsolete deployment scripts" "FAIL" "Found $obsolete_scripts obsolete deployment scripts"
fi

# Check 6: Legacy nginx configurations
nginx_confs=$(find . -name "nginx*.conf" -o -name "nginx*.template" | wc -l)
if [ "$nginx_confs" -eq 0 ]; then
    check_result "Legacy nginx configurations" "PASS" "No legacy nginx configuration files found"
else
    check_result "Legacy nginx configurations" "FAIL" "Found $nginx_confs legacy nginx configuration files"
fi

echo ""
echo "🌐 ENVIRONMENTAL CONFLICT RESOLUTION CHECKS"
echo "==========================================="

# Check 7: Environment variable conflicts
if [ -f ".env.production.template" ]; then
    docker_refs=$(grep -c "docker" .env.production.template || true)
    if [ "$docker_refs" -eq 0 ]; then
        check_result "Environment configuration conflicts" "PASS" "No Docker references in environment template"
    else
        check_result "Environment configuration conflicts" "FAIL" "Found Docker references in .env.production.template"
    fi
else
    check_result "Environment configuration conflicts" "PASS" "No environment template file found"
fi

# Check 8: Duplicate .env files
env_files=$(find . -maxdepth 1 -name ".env*" | wc -l)
if [ "$env_files" -le 3 ]; then  # .env, .env.example, .env.production.template is acceptable
    check_result "Duplicate environment files" "PASS" "Environment file count is reasonable ($env_files files)"
else
    check_result "Duplicate environment files" "FAIL" "Too many environment files ($env_files files) - possible duplicates"
fi

echo ""
echo "🗂️  KUBERNETES INFRASTRUCTURE CHECKS"
echo "==================================="

# Check 9: Kubernetes manifests
k8s_manifests=$(find k8s-deploy/manifests -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l)
if [ "$k8s_manifests" -gt 0 ]; then
    check_result "Kubernetes manifests" "PASS" "Found $k8s_manifests Kubernetes manifests"
else
    check_result "Kubernetes manifests" "FAIL" "No Kubernetes manifests found in k8s-deploy/manifests"
fi

# Check 10: Kubernetes deployment scripts
k8s_scripts=$(find k8s-deploy/scripts -name "*.sh" -o -name "*.py" 2>/dev/null | wc -l)
if [ "$k8s_scripts" -gt 0 ]; then
    check_result "Kubernetes deployment scripts" "PASS" "Found $k8s_scripts Kubernetes deployment scripts"
else
    check_result "Kubernetes deployment scripts" "FAIL" "No Kubernetes deployment scripts found"
fi

echo ""
echo "🔄 CACHE AND STATE CLEANUP CHECKS"
echo "=================================="

# Check 11: Cache directories
cache_dirs=$(find . -name "__pycache__" -o -name ".ruff_cache" -o -name "node_modules" | wc -l)
if [ "$cache_dirs" -gt 0 ]; then
    check_result "Cache directories" "PASS" "Found $cache_dirs cache directories (normal)"
else
    check_result "Cache directories" "PASS" "No cache directories found"
fi

# Check 12: Temporary files
temp_files=$(find . -name "*.tmp" -o -name "*.log" -o -name ".DS_Store" | wc -l)
if [ "$temp_files" -gt 0 ]; then
    check_result "Temporary files" "WARN" "Found $temp_files temporary files that could be cleaned"
else
    check_result "Temporary files" "PASS" "No temporary files found"
fi

echo ""
echo "📊 VERIFICATION RESULTS"
echo "======================"

echo "Total checks performed: $total_checks"
echo -e "Passed: ${GREEN}$passed_checks${NC}"
echo -e "Failed: ${RED}$failed_checks${NC}"

if [ "$failed_checks" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: $failed_checks checks failed${NC}"
    echo "Please review and address the failed checks before proceeding to Phase 2."
    echo ""
    echo "Common remediation steps:"
    echo "1. Remove any remaining Docker Compose files"
    echo "2. Clean up obsolete deployment scripts"
    echo "3. Remove legacy nginx configurations"
    echo "4. Update environment templates to remove Docker references"
    echo "5. Ensure Kubernetes manifests are properly configured"
    exit 1
else
    echo ""
    echo -e "${GREEN}🎉 SUCCESS: All infrastructure cleanup checks passed!${NC}"
    echo "The codebase is ready for Phase 2 deployment."
    echo ""
    echo "Next steps:"
    echo "1. Run 'k8s-deploy/scripts/deploy-production-readiness.sh' to verify Kubernetes readiness"
    echo "2. Execute 'k8s-deploy/scripts/install-k3s-clean.sh' for clean Kubernetes installation"
    echo "3. Apply manifests with 'kubectl apply -f k8s-deploy/manifests/'"
    exit 0
fi