#!/bin/bash

# 🏥 Sophia AI Local Health Check
# Verify all services are running properly

echo "🏥 SOPHIA AI - LOCAL HEALTH CHECK"
echo "================================="
echo

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo "✅ $name: HEALTHY"
        return 0
    else
        echo "❌ $name: UNHEALTHY ($url)"
        return 1
    fi
}

# Check core infrastructure
echo "🔧 CORE INFRASTRUCTURE:"
check_service "Redis" "http://localhost:6380" "000"  # Redis doesn't use HTTP
check_service "PostgreSQL" "localhost:5432" "000"   # PostgreSQL doesn't use HTTP
echo

# Check AI services
echo "🤖 AI SERVICES:"
check_service "AI Coordinator" "http://localhost:8080/health"
check_service "MCP Agents" "http://localhost:8000/healthz"
check_service "Agent Teams" "http://localhost:8087/healthz"
check_service "Agent Swarm" "http://localhost:8008/health"
check_service "LLM Router" "http://localhost:8007/health"
echo

# Check MCP integrations
echo "🔧 MCP INTEGRATIONS:"
check_service "Context Service" "http://localhost:8081/healthz"
check_service "GitHub Integration" "http://localhost:8082/healthz"
check_service "HubSpot CRM" "http://localhost:8083/healthz"
check_service "Lambda Labs" "http://localhost:8084/healthz"
check_service "Research Engine" "http://localhost:8085/healthz"
check_service "Business Tools" "http://localhost:8086/healthz"
check_service "Orchestrator" "http://localhost:8088/healthz"
echo

# Check business integrations
echo "💼 BUSINESS INTEGRATIONS:"
check_service "Salesforce" "http://localhost:8092/healthz"
check_service "Slack" "http://localhost:8093/healthz"
check_service "Apollo" "http://localhost:8090/healthz"
check_service "Gong" "http://localhost:8091/healthz"
echo

# Check monitoring
echo "📈 MONITORING:"
check_service "Grafana" "http://localhost:3000/login"
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Nginx Gateway" "http://localhost:80/health"
echo

# Check container status
echo "🐳 CONTAINER STATUS:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo

# Check resource usage
echo "💻 RESOURCE USAGE:"
echo "Memory usage by container:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
echo

echo "🎉 Health check complete!"
echo "📊 For detailed logs: docker-compose logs -f [service-name]"
echo "🛠️ To restart a service: docker-compose restart [service-name]"