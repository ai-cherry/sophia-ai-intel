#!/bin/bash

# Simple Health Check Script for Sophia AI Ecosystem
echo "🔍 Starting Sophia AI Health Check"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
INFRA_HEALTHY=0
INFRA_TOTAL=0
SERVICES_HEALTHY=0
SERVICES_TOTAL=0

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local url="http://localhost:$port/healthz"

    echo -n "   Checking $service on port $port... "

    if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        ((SERVICES_HEALTHY++))
    else
        echo -e "${RED}❌ Unhealthy${NC}"
    fi
    ((SERVICES_TOTAL++))
}

# Function to check infrastructure
check_infrastructure() {
    local service=$1
    local port=$2

    echo -n "   Checking $service on port $port... "

    if nc -z -w 5 localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ Connected${NC}"
        ((INFRA_HEALTHY++))
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
    ((INFRA_TOTAL++))
}

# Check Docker containers
echo -e "\n📦 Checking Docker Containers..."
docker-compose ps --format "table {{.Name}}\t{{.Status}}" | head -n 1
docker-compose ps --format "table {{.Name}}\t{{.Status}}" | tail -n +2

# Check infrastructure services
echo -e "\n🏗️ Checking Infrastructure Services..."
check_infrastructure "postgres" 5432
check_infrastructure "redis" 6380
check_infrastructure "qdrant" 6333

# Check application services
echo -e "\n🚀 Checking Application Services..."
check_service "mcp-github" 8082
check_service "mcp-hubspot" 8083
check_service "mcp-business" 8086
check_service "agno-coordinator" 8080
check_service "agno-teams" 8087
check_service "orchestrator" 8088

# Generate report
echo -e "\n====================================="
echo "📊 HEALTH CHECK REPORT"
echo "====================================="

echo -e "\n✅ OVERALL STATUS:"
echo "   Infrastructure: $INFRA_HEALTHY/$INFRA_TOTAL healthy"
echo "   Services: $SERVICES_HEALTHY/$SERVICES_TOTAL healthy"

# Calculate percentages
INFRA_PERCENT=$(( INFRA_TOTAL > 0 ? (INFRA_HEALTHY * 100) / INFRA_TOTAL : 0 ))
SERVICES_PERCENT=$(( SERVICES_TOTAL > 0 ? (SERVICES_HEALTHY * 100) / SERVICES_TOTAL : 0 ))

echo "   Infrastructure Health: ${INFRA_PERCENT}%"
echo "   Services Health: ${SERVICES_PERCENT}%"

# Determine overall health
if [ "$INFRA_PERCENT" -eq 100 ] && [ "$SERVICES_PERCENT" -ge 50 ]; then
    echo -e "   Overall Health: ${GREEN}GOOD${NC}"
    RESULT=0
elif [ "$INFRA_PERCENT" -ge 50 ] || [ "$SERVICES_PERCENT" -ge 25 ]; then
    echo -e "   Overall Health: ${YELLOW}FAIR${NC}"
    RESULT=0
else
    echo -e "   Overall Health: ${RED}CRITICAL${NC}"
    RESULT=1
fi

# Save results to file
cat > health_check_report.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "summary": {
    "infrastructure_healthy": $INFRA_HEALTHY,
    "infrastructure_total": $INFRA_TOTAL,
    "services_healthy": $SERVICES_HEALTHY,
    "services_total": $SERVICES_TOTAL,
    "infrastructure_percent": $INFRA_PERCENT,
    "services_percent": $SERVICES_PERCENT,
    "overall_result": $RESULT
  }
}
EOF

echo -e "\n📄 Report saved to: health_check_report.json"

if [ $RESULT -eq 0 ]; then
    echo -e "✅ Health check completed successfully"
else
    echo -e "⚠️ Health check found issues"
fi

exit $RESULT