#!/bin/bash
set -e

echo "⏪ Fly.io Rollback Script"
echo "======================="

APP_NAME=${FLY_APP_NAME:-sophia-mcp-platform}
VERSION=${1:-}

# Check prerequisites
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found"
    exit 1
fi

# List recent releases
echo "📋 Recent releases:"
flyctl releases list --app "$APP_NAME" -n 10

if [ -z "$VERSION" ]; then
    echo ""
    echo "Enter the version to rollback to (or 'latest' for previous version):"
    read -r VERSION
fi

if [ "$VERSION" == "latest" ]; then
    echo "⏪ Rolling back to previous version..."
    flyctl rollback --app "$APP_NAME"
else
    echo "⏪ Rolling back to version $VERSION..."
    flyctl deploy --image "registry.fly.io/$APP_NAME:$VERSION" --app "$APP_NAME"
fi

# Verify rollback
echo ""
echo "🔍 Verifying rollback..."
sleep 10

flyctl status --app "$APP_NAME"

# Run smoke tests
echo ""
echo "🧪 Running smoke tests..."
./scripts/fly-smoke-tests.sh "$APP_NAME"

echo ""
echo "✅ Rollback completed!"