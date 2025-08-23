#!/bin/bash
# Real-time health monitoring script

SERVICES=(
    "sophiaai-dashboard-v2"
    "sophiaai-mcp-repo-v2"
    "sophiaai-mcp-research-v2"
    "sophiaai-mcp-context-v2"
    "sophiaai-mcp-business-v2"
    "sophiaai-jobs-v2"
)

echo "🔍 MCP Platform Health Check - $(date)"
echo "=========================================="

total_services=0
healthy_services=0

for app in "${SERVICES[@]}"; do
    total_services=$((total_services + 1))
    
    if status=$(flyctl status --app "$app" 2>/dev/null); then
        if echo "$status" | grep -q "started"; then
            echo "✅ $app: HEALTHY"
            healthy_services=$((healthy_services + 1))
        else
            echo "⚠️ $app: DEGRADED"
            echo "   Status: $(echo "$status" | grep -o "started\|stopped\|crashed" | head -1)"
        fi
    else
        echo "❌ $app: UNREACHABLE"
    fi
done

echo "=========================================="
echo "📊 Overall Health: $healthy_services/$total_services services healthy"

# Calculate health percentage
health_percentage=$((healthy_services * 100 / total_services))

if [[ $health_percentage -ge 80 ]]; then
    echo "🟢 System Status: HEALTHY ($health_percentage%)"
    exit 0
elif [[ $health_percentage -ge 50 ]]; then
    echo "🟡 System Status: DEGRADED ($health_percentage%)"
    exit 1
else
    echo "🔴 System Status: CRITICAL ($health_percentage%)"
    exit 2
fi
