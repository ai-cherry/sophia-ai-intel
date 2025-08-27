#!/bin/bash
set -e

echo "🚀 Sophia MCP Platform Deployment Script"
echo "========================================"

# Load environment
ENV=${1:-staging}
echo "📦 Deploying to environment: $ENV"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required but not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl required but not installed."; exit 1; }

# Load environment variables
if [ -f ".env.$ENV" ]; then
    export $(cat .env.$ENV | xargs)
else
    echo "⚠️  No .env.$ENV file found, using defaults"
fi

# Build images
echo "🔨 Building Docker images..."
docker-compose -f ops/docker-compose.yaml build

# Deploy based on target
case "$2" in
    "fly")
        echo "🚁 Deploying to Fly.io..."
        flyctl deploy --config ops/fly/fly.toml
        ;;
    "k8s")
        echo "☸️  Deploying to Kubernetes..."
        kubectl apply -f ops/k8s/
        kubectl rollout status deployment -n sophia-platform --timeout=300s
        ;;
    "local")
        echo "🏠 Deploying locally..."
        docker-compose -f ops/docker-compose.yaml up -d
        ;;
    *)
        echo "📍 Default: Local deployment"
        docker-compose -f ops/docker-compose.yaml up -d
        ;;
esac

echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  - Analytics MCP: http://localhost:8001"
echo "  - CRM MCP: http://localhost:8002" 
echo "  - Comms MCP: http://localhost:8003"
echo "  - Projects MCP: http://localhost:8004"
echo "  - Gong MCP: http://localhost:8005"
echo "  - Context API: http://localhost:8006"
echo "  - Portkey LLM: http://localhost:8007"
echo "  - Agents Swarm: http://localhost:8008"