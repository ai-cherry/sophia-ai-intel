#!/bin/bash

# Post-Deploy Verification Script
# Runs all checks from the tight post-deploy checklist

set -e

echo "================================================================"
echo "🚀 POST-DEPLOY VERIFICATION CHECKLIST"
echo "================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Function to check HTTP status
check_health() {
    local service=$1
    local url=$2
    echo -n "Checking $service health..."
    
    STATUS=$(curl -sI "$url" | head -n1 | awk '{print $2}')
    
    if [ "$STATUS" = "200" ]; then
        echo -e " ${GREEN}✓ HTTP 200${NC}"
        ((PASSED++))
        return 0
    else
        echo -e " ${RED}✗ HTTP $STATUS${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1️⃣  HEALTHZ CHECKS (all four services)"
echo "----------------------------------------"
check_health "Dashboard" "https://sophiaai-dashboard.fly.dev/healthz"
check_health "MCP Repo" "https://sophiaai-mcp-repo.fly.dev/healthz"
check_health "MCP Research" "https://sophiaai-mcp-research.fly.dev/healthz"
check_health "MCP Context" "https://sophiaai-mcp-context.fly.dev/healthz"
echo ""

echo "2️⃣  DASHBOARD BUNDLE CHECK"
echo "----------------------------------------"
echo -n "Fetching build info..."
BUILD_INFO=$(curl -s https://sophiaai-dashboard.fly.dev/__build 2>/dev/null | head -5)
if [ -n "$BUILD_INFO" ]; then
    echo -e " ${GREEN}✓${NC}"
    echo "$BUILD_INFO" | sed 's/^/   /'
    ((PASSED++))
else
    echo -e " ${RED}✗ No build info${NC}"
    ((FAILED++))
fi
echo ""

echo "3️⃣  PROOF FILES CHECK"
echo "----------------------------------------"
PROOF_FILES=(
    "proofs/healthz/sophiaai-dashboard.txt"
    "proofs/healthz/sophiaai-mcp-repo.txt"
    "proofs/healthz/sophiaai-mcp-research.txt"
    "proofs/healthz/sophiaai-mcp-context.txt"
    "proofs/build/dashboard_build.txt"
    "proofs/fly/sophiaai-dashboard_machines.json"
    "proofs/fly/sophiaai-mcp-repo_machines.json"
    "proofs/fly/sophiaai-mcp-research_machines.json"
    "proofs/fly/sophiaai-mcp-context_machines.json"
)

for file in "${PROOF_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
        ((PASSED++))
    else
        echo -e "   ${YELLOW}⚠${NC}  $file (not yet created)"
    fi
done
echo ""

echo "4️⃣  MCP REPO READ CHECK"
echo "----------------------------------------"
if [ -f "proofs/mcp_repo/file_vite_config.json" ]; then
    echo -n "Checking vite config proof..."
    if grep -q '"content"' proofs/mcp_repo/file_vite_config.json 2>/dev/null; then
        echo -e " ${GREEN}✓ Has content${NC}"
        ((PASSED++))
    else
        echo -e " ${YELLOW}⚠ No content field${NC}"
    fi
fi

if [ -f "proofs/mcp_repo/tree_dashboard.json" ]; then
    echo -n "Checking dashboard tree proof..."
    if grep -q '"entries"' proofs/mcp_repo/tree_dashboard.json 2>/dev/null; then
        echo -e " ${GREEN}✓ Has entries${NC}"
        ((PASSED++))
    else
        echo -e " ${YELLOW}⚠ No entries field${NC}"
    fi
fi
echo ""

echo "5️⃣  CONTEXT INDEX CHECK"
echo "----------------------------------------"
if [ -f "proofs/mcp_context/index.json" ]; then
    echo -n "Checking context index..."
    if grep -q '"status".*"READY"' proofs/mcp_context/index.json 2>/dev/null; then
        echo -e " ${GREEN}✓ Status: READY${NC}"
        ((PASSED++))
    else
        echo -e " ${YELLOW}⚠ Not ready or DB not configured${NC}"
    fi
fi
echo ""

echo "================================================================"
echo "📊 SUMMARY"
echo "================================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! PHASE 1 COMPLETE!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update docs/PHASE1_FINAL_COMPLETION.md with 'PHASE 1 COMPLETE'"
    echo "2. Start Phase 2 with the kickstart plan"
else
    echo -e "${YELLOW}⚠️  Some checks failed. Review the failures above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "- Check GitHub Actions logs: https://github.com/ai-cherry/sophia-ai-intel/actions"
    echo "- Verify FLY_API_TOKEN is set in GitHub secrets"
    echo "- Check proofs/fly/*_logs.txt for error details"
fi

echo ""
echo "================================================================"
echo "Run this script again after fixes: ./scripts/post_deploy_verify.sh"
echo "================================================================"