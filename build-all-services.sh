#!/bin/bash

echo "🔨 Building all Sophia AI services..."

# Base services that others depend on
PRIORITY_SERVICES="mcp-context mcp-agents"

# All MCP services
MCP_SERVICES="mcp-github mcp-hubspot mcp-lambda mcp-research mcp-business mcp-apollo mcp-gong mcp-salesforce mcp-slack"

# AI orchestration services  
AI_SERVICES="agno-coordinator orchestrator agno-teams agno-wrappers"

# Function to build a service
build_service() {
    local service=$1
    echo "Building $service..."
    
    if [ -d "services/$service" ]; then
        cd services/$service
        
        # Use simplified Dockerfile if it exists, otherwise use universal
        if [ -f "Dockerfile.simple" ]; then
            docker build -f Dockerfile.simple -t sophia-$service:latest . &
        elif [ -f "../../Dockerfile.universal" ]; then
            docker build -f ../../Dockerfile.universal -t sophia-$service:latest . &
        else
            docker build -t sophia-$service:latest . &
        fi
        
        cd ../..
    else
        echo "⚠️  Directory services/$service not found"
    fi
}

# Build priority services first
for service in $PRIORITY_SERVICES; do
    build_service $service
done

# Wait for priority builds
wait

# Build remaining services in parallel
for service in $MCP_SERVICES; do
    build_service $service
done

for service in $AI_SERVICES; do
    build_service $service
done

# Wait for all builds to complete
wait

echo "✅ All services built!"
docker images | grep sophia-