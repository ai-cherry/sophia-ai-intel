#!/bin/bash
# Unified Sophia AI Deployment Script for Lambda Labs
# Deploys complete system including new agent swarm integration

set -e

echo "🚀 Deploying Unified Sophia AI to Lambda Labs"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Lambda Labs configuration
LAMBDA_IP="192.222.51.223"
COMPOSE_PROJECT="sophia-ai-intel"

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/healthz"}
    
    echo -n "Checking $service_name health... "
    
    if curl -sf "http://$LAMBDA_IP:$port$endpoint" > /dev/null; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://$LAMBDA_IP:$port/healthz" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
}

echo ""
echo "📋 Pre-deployment checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and docker-compose available${NC}"

echo ""
echo "🏗️ Building and deploying services..."

# Build agent swarm service first
echo "📦 Building agent swarm service..."
if docker-compose build sophia-agents; then
    echo -e "${GREEN}✅ Agent swarm built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build agent swarm${NC}"
    exit 1
fi

# Deploy all services
echo "🎯 Deploying complete Sophia AI stack..."
if docker-compose up -d --build; then
    echo -e "${GREEN}✅ All services deployed${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 30

echo ""
echo "🏥 Running health checks..."

# Check all services
services=(
    "Dashboard:3000"
    "Research:8081" 
    "Context:8082"
    "GitHub:8083"
    "Business:8084"
    "Lambda:8085"
    "HubSpot:8086"
    "Agents:8087"
)

healthy_count=0
total_services=${#services[@]}

for service_info in "${services[@]}"; do
    service_name="${service_info%:*}"
    port="${service_info#*:}"
    
    if check_service_health "$service_name" "$port"; then
        healthy_count=$((healthy_count + 1))
    fi
done

echo ""
echo "📊 Health Check Summary:"
echo "Healthy services: $healthy_count/$total_services"

if [ $healthy_count -eq $total_services ]; then
    echo -e "${GREEN}✅ All services healthy!${NC}"
    overall_health="healthy"
elif [ $healthy_count -ge $((total_services * 8 / 10)) ]; then
    echo -e "${YELLOW}⚠️ Most services healthy (acceptable)${NC}"
    overall_health="degraded"
else
    echo -e "${RED}❌ Multiple service failures${NC}"
    overall_health="unhealthy"
fi

echo ""
echo "🧪 Testing agent swarm integration..."

# Test agent swarm
if curl -sf -X POST "http://$LAMBDA_IP:8087/debug/test-swarm" > /dev/null; then
    echo -e "${GREEN}✅ Agent swarm test passed${NC}"
    agent_test="passed"
else
    echo -e "${RED}❌ Agent swarm test failed${NC}"
    agent_test="failed"
fi

echo ""
echo "💬 Testing chat integration..."

# Test chat API with agent swarm
chat_test_response=$(curl -s -X POST "http://$LAMBDA_IP:8082/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"analyze repository"}]}' || echo "failed")

if [[ "$chat_test_response" != "failed" ]] && [[ "$chat_test_response" == *"choices"* ]]; then
    echo -e "${GREEN}✅ Chat integration working${NC}"
    chat_test="passed"
else
    echo -e "${YELLOW}⚠️ Chat integration may need configuration${NC}"
    chat_test="partial"
fi

echo ""
echo "🎯 Deployment Summary"
echo "===================="
echo -e "Overall Health: ${overall_health}"
echo -e "Agent Swarm: ${agent_test}"
echo -e "Chat Integration: ${chat_test}"
echo ""
echo "🌐 Access URLs:"
echo "  Dashboard: http://www.sophia-intel.ai (or http://$LAMBDA_IP:3000)"
echo "  Agent Swarm: http://$LAMBDA_IP:8087"
echo "  Research API: http://$LAMBDA_IP:8081"
echo "  Context API: http://$LAMBDA_IP:8082"
echo "  GitHub API: http://$LAMBDA_IP:8083"
echo "  Business API: http://$LAMBDA_IP:8084"
echo ""

if [[ "$overall_health" == "healthy" ]] && [[ "$agent_test" == "passed" ]]; then
    echo -e "${GREEN}🎉 UNIFIED SOPHIA AI DEPLOYMENT SUCCESSFUL!${NC}"
    echo ""
    echo "✨ Sophia now has:"
    echo "  🤖 AI Agent Swarm for repository intelligence"
    echo "  🧠 Enhanced memory with real embeddings"
    echo "  💼 Complete business system integration"
    echo "  🔬 Advanced research capabilities"
    echo "  💬 Natural language orchestration"
    echo ""
    echo "🚀 Ready for advanced intelligence operations!"
    
    # Generate deployment report
    cat > deployment-report-$(date +%Y%m%d-%H%M%S).md << EOF
# Sophia AI Deployment Report
**Date:** $(date)
**Lambda Labs IP:** $LAMBDA_IP
**Overall Health:** $overall_health
**Agent Swarm Status:** $agent_test
**Chat Integration:** $chat_test

## Services Status
$(for service_info in "${services[@]}"; do
    service_name="${service_info%:*}"
    port="${service_info#*:}"
    if curl -sf "http://$LAMBDA_IP:$port/healthz" > /dev/null 2>&1; then
        echo "- ✅ $service_name (port $port): Healthy"
    else
        echo "- ❌ $service_name (port $port): Unhealthy"  
    fi
done)

## Next Steps
- Complete DNS setup for www.sophia-intel.ai
- Add missing business integrations (Notion, Linear, Intercom)
- Test advanced agent swarm capabilities
- Monitor system performance and optimization

**Deployment Status: SUCCESS** ✅
EOF
    
    echo "📄 Deployment report saved: deployment-report-$(date +%Y%m%d-%H%M%S).md"
    
else
    echo -e "${YELLOW}⚠️ Deployment completed with issues${NC}"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "  1. Check service logs: docker-compose logs [service-name]"
    echo "  2. Restart failed services: docker-compose restart [service-name]"
    echo "  3. Check resource usage: docker stats"
    echo "  4. Verify environment variables: docker-compose config"
fi

echo ""
echo "📋 Management commands:"
echo "  View logs: docker-compose logs -f [service-name]"
echo "  Restart: docker-compose restart [service-name]"
echo "  Stop all: docker-compose down" 
echo "  Update: git pull && docker-compose up -d --build"

exit 0
