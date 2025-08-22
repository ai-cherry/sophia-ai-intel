#!/bin/bash
# Setup all external service connections for Roo

set -euo pipefail

echo "================================================"
echo "   External Services Setup for Sophia AI Intel"
echo "================================================"

# Check for required environment variables
REQUIRED_VARS=(
    "LAMBDA_LABS_API_KEY"
    "PULUMI_ACCESS_TOKEN"
    "GITHUB_PAT"
    "QDRANT_API_KEY"
    "REDIS_PASSWORD"
    "NEON_DATABASE_URL"
    "MEM0_API_KEY"
    "PORTKEY_API_KEY"
    "OPENROUTER_API_KEY"
    "SLACK_BOT_TOKEN"
    "GONG_API_KEY"
    "SALESFORCE_USERNAME"
    "HUBSPOT_API_KEY"
    "LOOKER_CLIENT_ID"
    "USERGEMS_API_KEY"
)

echo ""
echo "Checking external service credentials..."
echo "----------------------------------------"

missing_count=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "⚠️  Missing: $var"
        ((missing_count++))
    else
        echo "✅ Found: $var"
    fi
done

echo ""
echo "Summary: $((${#REQUIRED_VARS[@]} - missing_count))/${#REQUIRED_VARS[@]} credentials configured"

# Create MCP server directories
echo ""
echo "Creating MCP server directories..."
echo "----------------------------------"

SERVICES=(
    "lambda"
    "pulumi"
    "qdrant"
    "redis"
    "memory"
    "openrouter"
    "slack"
    "gong"
    "salesforce"
    "hubspot"
    "looker"
    "usergems"
)

for service in "${SERVICES[@]}"; do
    if [ ! -d "services/mcp-$service" ]; then
        mkdir -p "services/mcp-$service"
        echo "📁 Created services/mcp-$service"
    else
        echo "✓ Exists: services/mcp-$service"
    fi
done

# Create .env.services template if it doesn't exist
if [ ! -f ".env.services" ]; then
    echo ""
    echo "Creating .env.services template..."
    cat > .env.services <<'EOF'
# External Services Configuration
# DO NOT COMMIT THIS FILE

# Infrastructure
LAMBDA_LABS_API_KEY=
LAMBDA_LABS_INSTANCE_ID=
PULUMI_ACCESS_TOKEN=
PULUMI_ORG=

# Databases
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=
REDIS_URL=
REDIS_PASSWORD=
REDIS_HOST=
REDIS_PORT=
NEON_DATABASE_URL=
NEON_API_KEY=

# AI Services
MEM0_API_KEY=
MEM0_ORG_ID=
MEM0_USER_ID=
PORTKEY_API_KEY=
PORTKEY_WORKSPACE_ID=
OPENROUTER_API_KEY=
OPENROUTER_SITE_URL=
OPENROUTER_SITE_NAME=

# Business Tools
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SLACK_SIGNING_SECRET=
SLACK_WORKSPACE_ID=
GONG_API_KEY=
GONG_API_SECRET=
GONG_WORKSPACE_ID=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
SALESFORCE_INSTANCE_URL=
HUBSPOT_API_KEY=
HUBSPOT_ACCESS_TOKEN=
HUBSPOT_APP_ID=
HUBSPOT_PORTAL_ID=
LOOKER_CLIENT_ID=
LOOKER_CLIENT_SECRET=
LOOKER_BASE_URL=
LOOKER_VERIFY_SSL=true
USERGEMS_API_KEY=
USERGEMS_WORKSPACE_ID=
EOF
    echo "✅ Created .env.services template"
    echo "⚠️  Remember to add this to .gitignore"
else
    echo ""
    echo "✓ .env.services already exists"
fi

# Update .gitignore if needed
if ! grep -q ".env.services" .gitignore 2>/dev/null; then
    echo ".env.services" >> .gitignore
    echo "✅ Added .env.services to .gitignore"
fi

echo ""
echo "================================================"
echo "✅ External services setup complete!"
echo ""
echo "Next steps:"
echo "1. Fill in the credentials in .env.services"
echo "2. Source the file: source .env.services"
echo "3. Create MCP servers for each service you need"
echo "4. Deploy MCP servers to Fly.io"
echo ""
echo "MCP server template available in:"
echo "  docs/ROO_EXTERNAL_SERVICES_CONFIG.md"
echo ""