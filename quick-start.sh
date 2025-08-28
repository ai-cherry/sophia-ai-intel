#!/bin/bash
# Quick Start Script for Sophia AI Intel Platform
# Run from the project directory: ./quick-start.sh

set -e

echo "🚀 Starting Sophia AI Intel Platform..."
echo "📍 Working Directory: $(pwd)"

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the sophia-ai-intel-1 directory."
    exit 1
fi

echo "📦 Step 1: Starting Core Infrastructure (PostgreSQL, Redis)..."
docker-compose --env-file .env.local up -d postgres redis

echo "⏳ Waiting for databases to be ready..."
sleep 10

echo "📊 Step 2: Starting Monitoring Stack..."
docker-compose --env-file .env.local up -d prometheus grafana loki jaeger

echo "🛠️ Step 3: Starting Development Tools..."
docker-compose --env-file .env.local up -d adminer redis-commander

echo "⏳ Waiting for services to initialize..."
sleep 15

echo "✅ Deployment Complete!"
echo ""
echo "🌐 Access Your Services:"
echo "   📊 Grafana Dashboard:    http://localhost:3000 (admin/admin)"
echo "   📈 Prometheus:           http://localhost:9090"
echo "   🔍 Jaeger Tracing:       http://localhost:16686"
echo "   🗄️  Database Admin:       http://localhost:8080"
echo "   📊 Redis Commander:      http://localhost:8081"
echo ""
echo "🔧 Development Commands:"
echo "   Health Check:     ./scripts/health-monitor.sh start"
echo "   Dev Workflow:     ./scripts/dev-workflow.sh start"
echo "   Run Tests:        pytest tests/ --cov=services/"
echo ""
echo "🛑 To Stop Everything:"
echo "   docker-compose down --volumes"
echo ""
docker-compose --env-file .env.local ps