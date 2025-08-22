#!/bin/bash
# Setup Fly.io apps for Sophia AI Intel
# This script creates the apps but does NOT store any secrets

set -euo pipefail

echo "Setting up Fly.io apps for Sophia AI Intel..."
echo "================================================"

# Set flyctl path
FLYCTL="/home/codespace/.fly/bin/flyctl"
if [ ! -f "$FLYCTL" ]; then
    FLYCTL="flyctl"
fi

# Check if FLY_API_TOKEN is set
if [ -z "${FLY_API_TOKEN:-}" ]; then
    echo "❌ FLY_API_TOKEN environment variable not set"
    echo "Please export FLY_API_TOKEN before running this script"
    exit 1
fi

echo "✅ Fly.io token detected (not displayed)"

# Apps to create
APPS=(
    "sophiaai-dashboard"
    "sophiaai-mcp-repo"
    "sophiaai-mcp-research"
    "sophiaai-mcp-context"
)

# Create apps if they don't exist
for APP in "${APPS[@]}"; do
    echo ""
    echo "Checking app: $APP"
    if $FLYCTL apps show "$APP" >/dev/null 2>&1; then
        echo "  ✓ App $APP already exists"
    else
        echo "  → Creating app $APP..."
        if $FLYCTL apps create "$APP" --machines --yes; then
            echo "  ✓ App $APP created successfully"
        else
            echo "  ⚠ Failed to create $APP (may already exist)"
        fi
    fi
done

echo ""
echo "================================================"
echo "✅ Fly.io app setup complete!"
echo ""
echo "Apps configured:"
for APP in "${APPS[@]}"; do
    echo "  • https://$APP.fly.dev"
done

echo ""
echo "Next steps:"
echo "1. Run the GitHub workflow: .github/workflows/deploy_all.yml"
echo "2. The workflow will handle all deployments and proof collection"
echo ""
echo "Note: Secrets will be set by the workflow from GitHub secrets"