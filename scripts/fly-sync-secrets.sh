#!/bin/bash
set -e

echo "🔐 Fly.io Secrets Sync Script"
echo "============================="

# Configuration
APP_NAME=${FLY_APP_NAME:-sophia-mcp-platform}
ENV_FILE=${1:-.env}

# Check prerequisites
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Please install: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "📝 Please log in to Fly.io..."
    flyctl auth login
fi

# Check if app exists
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "⚠️  App $APP_NAME not found. Creating..."
    flyctl apps create "$APP_NAME"
fi

# Function to set secret
set_secret() {
    local key=$1
    local value=$2
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $key (empty value)"
        return
    fi
    
    echo "  Setting $key..."
    echo "$value" | flyctl secrets set "$key"=- --app "$APP_NAME" --stage
}

echo ""
echo "📋 Loading environment from $ENV_FILE..."

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    exit 1
fi

# Parse .env file and sync secrets
declare -a secrets_array
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove quotes from value
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    
    # Add to array for batch update
    secrets_array+=("$key=$value")
    
done < "$ENV_FILE"

# Deploy secrets in batch (more efficient)
echo ""
echo "🚀 Deploying ${#secrets_array[@]} secrets to Fly.io..."

if [ ${#secrets_array[@]} -gt 0 ]; then
    printf '%s\n' "${secrets_array[@]}" | flyctl secrets import --app "$APP_NAME"
fi

echo ""
echo "✅ Secrets synced successfully!"

# Show current secrets (without values)
echo ""
echo "📊 Current secrets in $APP_NAME:"
flyctl secrets list --app "$APP_NAME"