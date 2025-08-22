#!/bin/bash
# Sophia AI Intel - One-Click Deployment Script
# This script performs final checks and initiates deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Sophia AI Intel - Production Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Preflight checks
echo "Running preflight checks..."
echo "-------------------------"

# Check for critical files
CRITICAL_FILES=(
    ".github/workflows/deploy_all.yml"
    "services/mcp-github/requirements.txt"
    "services/mcp-research/requirements.txt"
    "services/mcp-context/requirements.txt"
    "apps/dashboard/package.json"
    "apps/dashboard/Dockerfile.static"
    "apps/dashboard/nginx.conf"
)

ALL_FILES_PRESENT=true
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} Found: $file"
    else
        echo -e "${RED}✗${NC} Missing: $file"
        ALL_FILES_PRESENT=false
    fi
done

if [ "$ALL_FILES_PRESENT" = false ]; then
    echo -e "${RED}❌ Critical files missing. Cannot proceed.${NC}"
    exit 1
fi

echo ""
echo "Checking critical fixes..."
echo "-------------------------"

# Check PyJWT fix
if grep -q "PyJWT\[crypto\]" services/mcp-github/requirements.txt; then
    echo -e "${GREEN}✓${NC} PyJWT[crypto] fix applied"
else
    echo -e "${RED}✗${NC} PyJWT[crypto] fix missing"
fi

# Check portkey-ai fix
if grep -q "portkey-ai>=1.14.0" services/mcp-research/requirements.txt; then
    echo -e "${GREEN}✓${NC} portkey-ai version fix applied"
else
    echo -e "${RED}✗${NC} portkey-ai version fix missing"
fi

# Check Vite base path
if grep -q "base: '/'," apps/dashboard/vite.config.ts; then
    echo -e "${GREEN}✓${NC} Vite base path correct"
else
    echo -e "${YELLOW}⚠${NC} Check Vite base path"
fi

# Check Nginx endpoints
if grep -q "/healthz" apps/dashboard/nginx.conf && grep -q "/__build" apps/dashboard/nginx.conf; then
    echo -e "${GREEN}✓${NC} Nginx endpoints configured"
else
    echo -e "${RED}✗${NC} Nginx endpoints missing"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}   PREFLIGHT CHECKS COMPLETE${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Display deployment instructions
cat << EOF
${YELLOW}📋 DEPLOYMENT INSTRUCTIONS${NC}

1. ${BLUE}Verify GitHub Secrets:${NC}
   Go to: https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions
   
   Required:
   - FLY_API_TOKEN ✅
   - NEON_DATABASE_URL ✅
   
   Optional but helpful:
   - TAVILY_API_KEY
   - SERPER_API_KEY

2. ${BLUE}Deploy via GitHub Actions:${NC}
   a. Go to: https://github.com/ai-cherry/sophia-ai-intel/actions
   b. Click "Deploy All (Dashboard + MCPs)"
   c. Click "Run workflow"
   d. Keep defaults (deploy all)
   e. Click green "Run workflow" button

3. ${BLUE}Monitor Deployment:${NC}
   The workflow will:
   • Build dashboard with npm
   • Deploy static Docker to Fly
   • Deploy all MCP services
   • Wait for health checks
   • Auto-commit proofs

4. ${BLUE}Verify Post-Deploy:${NC}
   Check these auto-committed proofs:
   • proofs/healthz/*.txt (all should be 200)
   • proofs/build/dashboard_build.txt (BUILD_ID present)
   • proofs/fly/*_machines.json (deployment status)

${GREEN}═══════════════════════════════════════════════${NC}
${GREEN}   Ready to deploy! Follow steps above.${NC}
${GREEN}═══════════════════════════════════════════════${NC}

${YELLOW}URLs after deployment:${NC}
• Dashboard: https://sophiaai-dashboard.fly.dev
• MCP Repo: https://sophiaai-mcp-repo.fly.dev
• MCP Research: https://sophiaai-mcp-research.fly.dev
• MCP Context: https://sophiaai-mcp-context.fly.dev

${YELLOW}If any issues:${NC}
Check proofs/fly/<app>_logs.txt for error details

EOF