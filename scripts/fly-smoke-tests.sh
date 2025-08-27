#!/bin/bash
set -e

APP_NAME=${1:-sophia-mcp-platform}
BASE_URL="https://$APP_NAME.fly.dev"

echo "🧪 Running Smoke Tests for $APP_NAME"
echo "===================================="

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local service=$3
    
    echo -n "  Testing $service ($endpoint)... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    
    if [ "$status" == "$expected_status" ]; then
        echo "✅ Pass (HTTP $status)"
        return 0
    else
        echo "❌ Fail (HTTP $status, expected $expected_status)"
        return 1
    fi
}

# Test each service
echo ""
echo "Testing service endpoints..."

test_endpoint "/health" 200 "Platform Health"
test_endpoint "/analytics-mcp/health" 200 "Analytics MCP"
test_endpoint "/crm-mcp/health" 200 "CRM MCP"
test_endpoint "/comms-mcp/health" 200 "Communications MCP"
test_endpoint "/projects-mcp/health" 200 "Projects MCP"
test_endpoint "/gong-mcp/health" 200 "Gong MCP"
test_endpoint "/portkey-llm/health" 200 "Portkey LLM"
test_endpoint "/agents-swarm/health" 200 "Agents Swarm"
test_endpoint "/context-api/health" 200 "Context API"
test_endpoint "/mem0/health" 200 "Mem0 Memory"

echo ""
echo "Testing authentication..."
test_endpoint "/auth/verify" 401 "Auth (unauthenticated)"

echo ""
echo "✅ Smoke tests completed!"