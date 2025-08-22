#!/bin/bash
# Script to update FLY_API_TOKEN after generating a new one
# Usage: ./scripts/update_fly_token.sh <new_token>

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide the new FLY_API_TOKEN as an argument"
    echo "Usage: $0 <new_token>"
    exit 1
fi

NEW_TOKEN="$1"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo "🔧 Updating Fly.io Authentication Token"
echo "========================================"
echo ""

# Test the new token locally
echo "📝 Step 1: Testing new token locally..."
export FLY_API_TOKEN="$NEW_TOKEN"

if $HOME/.fly/bin/flyctl auth whoami 2>&1; then
    echo "✅ Token authentication successful!"
else
    echo "❌ Token authentication failed. Please check your token."
    exit 1
fi

echo ""
echo "📝 Step 2: Verifying app access..."
if $HOME/.fly/bin/flyctl apps list | grep -q sophiaai; then
    echo "✅ Can access sophiaai apps!"
else
    echo "⚠️  Warning: Cannot see sophiaai apps. They may need to be created."
fi

echo ""
echo "📝 Step 3: Updating GitHub Actions secret..."
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set. Please set it first:"
    echo '   export GITHUB_TOKEN="your_github_pat"'
    exit 1
fi

# Update GitHub secret
gh secret set FLY_API_TOKEN -b "$NEW_TOKEN" \
    -R ai-cherry/sophia-ai-intel

echo "✅ GitHub Actions secret updated!"

echo ""
echo "📝 Step 4: Creating proof of update..."
mkdir -p proofs/fly

cat > proofs/fly/token_update.json << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "action": "token_update",
  "status": "success",
  "token_prefix": "${NEW_TOKEN:0:10}...",
  "validated": true,
  "github_secret_updated": true
}
EOF

echo "✅ Token update complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: gh workflow run deploy_all.yml -f deploy_dashboard=true -f deploy_services=true"
echo "2. Monitor: https://github.com/ai-cherry/sophia-ai-intel/actions"
echo "3. Verify deployments are successful"