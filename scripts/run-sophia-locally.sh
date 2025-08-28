#!/bin/bash

# 🚀 Sophia AI - Complete Local Development Setup
# Run the entire platform from your laptop!

set -e

echo "🏠 SOPHIA AI - LOCAL DEVELOPMENT DEPLOYMENT"
echo "==========================================="
echo
echo "This will run the complete Sophia AI platform locally:"
echo "• 17 microservices (AI agents, MCP integrations, business tools)"
echo "• Next.js dashboard with chat interface"
echo "• Redis, PostgreSQL, monitoring stack"
echo "• Complete business integrations (Salesforce, HubSpot, Slack, etc.)"
echo

# Check requirements
echo "1️⃣ Checking system requirements..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    echo "   Download: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Check environment file
echo "2️⃣ Checking environment configuration..."
if [ ! -f .env.production.real ]; then
    echo "❌ Environment file not found. Creating template..."
    cat > .env.production.real << 'EOF'
# Sophia AI Local Development Environment
# Copy this file and update with your API keys

# Core Database
POSTGRES_PASSWORD=sophia_dev_password_123
POSTGRES_URL=postgresql://sophia:sophia_dev_password_123@postgres:5432/sophia
JWT_SECRET=your-super-secret-jwt-key-here-min-32-chars

# Redis Cache
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_USER_KEY=default
REDIS_ACCOUNT_KEY=your-redis-key

# AI Models (Optional - some features need these)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
LAMBDA_API_KEY=your-lambda-labs-key-here
LAMBDA_CLOUD_ENDPOINT=https://api.lambdalabs.com

# Business Integrations (Optional - comment out if not needed)
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password

HUBSPOT_API_KEY=your-hubspot-key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
GITHUB_TOKEN=ghp_your-github-token

# Research & Data (Optional)
TAVILY_API_KEY=your-tavily-key
SERPAPI_API_KEY=your-serpapi-key

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
PORTKEY_API_KEY=your-portkey-key

# External Services (Optional)
APOLLO_API_KEY=your-apollo-key
GONG_ACCESS_KEY=your-gong-key
GONG_ACCESS_KEY_SECRET=your-gong-secret
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
DNSIMPLE_API_KEY=your-dnsimple-key
DOCKER_PAT=your-docker-pat
EOF
    
    echo "📝 Created .env.production.real template"
    echo "⚠️  Please edit .env.production.real and add your API keys"
    echo "💡 You can start with minimal config - most integrations are optional"
    echo
    read -p "Press Enter to continue with current config, or Ctrl+C to exit and edit first..."
fi

echo "✅ Environment configuration found"

# Clean up any existing containers
echo "3️⃣ Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
echo "✅ Cleanup complete"

# Build and start services
echo "4️⃣ Building and starting Sophia AI services..."
echo "⏳ This may take 5-10 minutes on first run..."
echo

# Start core infrastructure first
echo "🔧 Starting core infrastructure (Redis, PostgreSQL)..."
docker-compose up -d redis postgres

# Wait for infrastructure
echo "⏳ Waiting for infrastructure to be ready..."
sleep 10

# Start all services
echo "🚀 Starting all Sophia AI services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 30

echo
echo "✅ SOPHIA AI LOCAL DEPLOYMENT COMPLETE!"
echo "======================================"
echo
echo "🌐 Access your local Sophia AI platform:"
echo
echo "📊 MAIN DASHBOARD:"
echo "   http://localhost:80 (Nginx gateway)"
echo
echo "🤖 AI SERVICES:"
echo "   • AI Coordinator:     http://localhost:8080"
echo "   • MCP Agents:         http://localhost:8000" 
echo "   • Agent Teams:        http://localhost:8087"
echo "   • Agent Swarm:        http://localhost:8008"
echo "   • LLM Router:         http://localhost:8007"
echo
echo "🔧 MCP INTEGRATIONS:"
echo "   • Context Service:    http://localhost:8081"
echo "   • GitHub Integration: http://localhost:8082"
echo "   • HubSpot CRM:        http://localhost:8083"
echo "   • Lambda Labs:        http://localhost:8084"
echo "   • Research Engine:    http://localhost:8085"
echo "   • Business Tools:     http://localhost:8086"
echo "   • Orchestrator:       http://localhost:8088"
echo
echo "💼 BUSINESS INTEGRATIONS:"
echo "   • Salesforce:         http://localhost:8092"
echo "   • Slack:              http://localhost:8093"
echo "   • Apollo:             http://localhost:8090"
echo "   • Gong:               http://localhost:8091"
echo
echo "📈 MONITORING & DATA:"
echo "   • Grafana Dashboard:  http://localhost:3000 (admin/admin123)"
echo "   • Prometheus:         http://localhost:9090"
echo "   • PostgreSQL:         localhost:5432 (sophia/password)"
echo "   • Redis:              localhost:6380"
echo
echo "🔍 HEALTH CHECKS:"
echo "   docker-compose ps      # View service status"
echo "   docker-compose logs -f # View live logs"
echo "   ./scripts/health-check-local.sh # Run health checks"
echo
echo "🛑 TO STOP:"
echo "   docker-compose down"
echo
echo "🎉 Your complete AI platform is now running locally!"
echo "📱 Start chatting with AI agents, manage business data, and more!"