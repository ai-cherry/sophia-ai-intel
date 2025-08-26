#!/bin/bash
set -euo pipefail

# Sophia AI Deployment Script
# Handles environment setup and deployment

echo "=== Sophia AI Deployment Script ==="
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.production.template" ]; then
        cp .env.production.template .env
        echo "✓ Created .env from production template"
        echo "⚠️  Please fill in the API keys in .env before proceeding"
        echo "   Press Ctrl+C to cancel and edit .env, or Enter to continue with defaults"
        read -p ""
    else
        echo "Creating minimal .env file..."
        cat > .env << 'EOF'
# Minimal environment for local testing
NODE_ENV=development
ENVIRONMENT=development

# Redis (using local)
REDIS_URL=redis://localhost:6379

# PostgreSQL (using local or Docker)
DATABASE_URL=postgresql://sophia:sophia@localhost:5432/sophia
NEON_DATABASE_URL=${DATABASE_URL}

# Qdrant (using local or Docker)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=local-dev-key

# OpenAI (required for embeddings)
OPENAI_API_KEY=sk-your-openai-api-key

# Other LLMs (optional)
ANTHROPIC_API_KEY=your-key
OPENROUTER_API_KEY=your-key

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin

# Feature flags
DEBUG=true
TENANT=local-dev
EOF
        echo "✓ Created minimal .env file"
    fi
fi

# Check Docker
echo "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi
echo "✓ Docker is running"

# Create required directories
echo "Creating required directories..."
mkdir -p apps/dashboard configs/redis configs/nginx

# Build services
echo
echo "Building services (this may take a while)..."
docker-compose build --no-cache

echo
echo "Starting services..."
docker-compose up -d

# Wait for services to start
echo
echo "Waiting for services to start..."
sleep 30

# Check health
echo
echo "Checking service health..."
echo

# Function to check service
check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url/healthz" > /dev/null 2>&1; then
        echo "✓ $name: Healthy at $url"
        return 0
    else
        echo "✗ $name: Not responding at $url"
        return 1
    fi
}

# Check each service
services_healthy=true

check_service "Dashboard" "http://localhost:3000" || services_healthy=false
check_service "Research" "http://localhost:8081" || services_healthy=false
check_service "Context" "http://localhost:8082" || services_healthy=false
check_service "GitHub" "http://localhost:8083" || services_healthy=false
check_service "Business" "http://localhost:8084" || services_healthy=false
check_service "Lambda" "http://localhost:8085" || services_healthy=false
check_service "HubSpot" "http://localhost:8086" || services_healthy=false
check_service "Agents" "http://localhost:8087" || services_healthy=false

echo
echo "Monitoring Services:"
check_service "Prometheus" "http://localhost:9090" || true
check_service "Grafana" "http://localhost:3001" || true

echo
echo "=== Deployment Summary ==="
echo

if [ "$services_healthy" = true ]; then
    echo "✅ All core services are running!"
else
    echo "⚠️  Some services are not healthy. Check logs with:"
    echo "   docker-compose logs <service-name>"
fi

echo
echo "Access points:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - View service status: docker-compose ps"
echo
echo "To deploy to Lambda Labs Kubernetes:"
echo "  ./k8s-deploy/scripts/deploy-to-lambda.sh"
echo
