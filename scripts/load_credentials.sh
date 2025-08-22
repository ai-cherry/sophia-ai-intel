#!/bin/bash
# Secure credential loader for Sophia AI Intel
# Loads from .env.vault without exposing values

set -euo pipefail

VAULT_FILE=".env.vault"
LOADED_COUNT=0
TOTAL_COUNT=0

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "================================================"
echo "   Sophia AI Intel - Credential Loader"
echo "================================================"
echo ""

# Check if vault exists
if [ ! -f "$VAULT_FILE" ]; then
    echo -e "${RED}❌ .env.vault file not found${NC}"
    echo "Please ensure .env.vault exists with your credentials"
    exit 1
fi

# Load and export credentials
echo "Loading credentials from vault..."
echo "--------------------------------"

while IFS='=' read -r key value; do
    # Skip comments and empty lines
    if [[ "$key" =~ ^#.*$ ]] || [ -z "$key" ]; then
        continue
    fi
    
    # Remove any leading/trailing whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    if [ -n "$key" ] && [ -n "$value" ]; then
        export "$key=$value"
        ((LOADED_COUNT++))
        # Show key name but not value
        echo -e "${GREEN}✓${NC} Loaded: $key"
    fi
    ((TOTAL_COUNT++))
done < "$VAULT_FILE"

echo ""
echo "================================"
echo -e "${GREEN}✅ Loaded $LOADED_COUNT credentials${NC}"
echo ""

# Verify critical credentials for deployment
echo "Verifying critical deployment credentials..."
echo "-------------------------------------------"

CRITICAL_VARS=(
    "FLY_API_TOKEN"
    "NEON_DATABASE_URL"
    "GITHUB_PAT"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "PORTKEY_API_KEY"
    "TAVILY_API_KEY"
    "SERPER_API_KEY"
)

ALL_CRITICAL_PRESENT=true
for var in "${CRITICAL_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}✗${NC} Missing: $var"
        ALL_CRITICAL_PRESENT=false
    else
        # Show first 4 chars only for verification
        preview="${!var:0:4}..."
        echo -e "${GREEN}✓${NC} Found: $var (${preview})"
    fi
done

echo ""
if [ "$ALL_CRITICAL_PRESENT" = true ]; then
    echo -e "${GREEN}✅ All critical credentials present${NC}"
else
    echo -e "${YELLOW}⚠️  Some critical credentials missing${NC}"
    echo "You may need to add them before deployment"
fi

# Optional: Export to GitHub Actions format (without values)
if [ "${1:-}" = "--github-actions" ]; then
    echo ""
    echo "GitHub Secrets to configure (names only):"
    echo "-----------------------------------------"
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^#.*$ ]] && [ -n "$key" ]; then
            echo "  gh secret set $key"
        fi
    done < "$VAULT_FILE"
fi

echo ""
echo "================================================"
echo "Credentials loaded into environment"
echo "You can now run deployment scripts"
echo ""
echo "Security reminders:"
echo "  • Never commit .env.vault"
echo "  • Never echo credential values"
echo "  • Use GitHub Secrets for CI/CD"
echo "================================================"