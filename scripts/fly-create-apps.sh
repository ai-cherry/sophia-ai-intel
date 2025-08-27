#!/bin/bash
# Script to create Fly.io applications for Sophia AI Infrastructure

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "   Sophia AI Fly.io Apps Creation"
echo "========================================="
echo ""

# Check if .env file exists and extract FLY_API_TOKEN
ENV_FILE="${ENV_FILE:-/Users/lynnmusil/sophia-ai-intel-1/.env}"

if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓${NC} Found .env file at: $ENV_FILE"
    # Export FLY_API_TOKEN from .env file
    export FLY_API_TOKEN="$(grep -E '^FLY_ORG_TOKEN=|^FLY_API_TOKEN=' "$ENV_FILE" | tail -n1 | cut -d= -f2-)"
    
    if [ -z "$FLY_API_TOKEN" ]; then
        echo -e "${RED}✗${NC} FLY_API_TOKEN not found in .env file"
        echo "Please ensure FLY_API_TOKEN or FLY_ORG_TOKEN is set in your .env file"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} FLY_API_TOKEN configured"
else
    echo -e "${YELLOW}⚠${NC} .env file not found at: $ENV_FILE"
    echo "Checking for FLY_API_TOKEN in environment..."
    
    if [ -z "$FLY_API_TOKEN" ]; then
        echo -e "${RED}✗${NC} FLY_API_TOKEN not found in environment"
        echo "Please set FLY_API_TOKEN or provide ENV_FILE path"
        echo "Usage: ENV_FILE=/path/to/.env ./scripts/fly-create-apps.sh"
        exit 1
    fi
fi

# List of Fly.io applications to create
APPS=(
    "sophia-analytics-mcp"
    "sophia-crm-mcp"
    "sophia-comms-mcp"
    "sophia-projects-mcp"
    "sophia-gong-mcp"
    "sophia-context-api"
    "sophia-agents-swarm"
    "sophia-support-mcp"
    "sophia-enrichment-mcp"
)

echo ""
echo "Creating Fly.io applications..."
echo "================================"

# Function to create an app
create_app() {
    local app_name=$1
    echo ""
    echo "Creating app: $app_name"
    
    # Check if app already exists
    if fly apps list 2>/dev/null | grep -q "^$app_name"; then
        echo -e "${YELLOW}⚠${NC} App '$app_name' already exists, skipping..."
    else
        # Try to create the app
        if fly apps create "$app_name" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Successfully created app: $app_name"
        else
            echo -e "${RED}✗${NC} Failed to create app: $app_name"
            echo "  This might mean the app already exists or there was an error."
        fi
    fi
}

# Create each app
for app in "${APPS[@]}"; do
    create_app "$app"
done

echo ""
echo "========================================="
echo "   App Creation Complete"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure app secrets using: make fly-sync ENV=$ENV_FILE"
echo "2. Deploy applications using: make fly-deploy-all"
echo ""
echo "To verify apps were created, run:"
echo "  fly apps list"
echo ""