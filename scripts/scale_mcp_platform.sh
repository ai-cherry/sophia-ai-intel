#!/bin/bash
# MCP Platform Scaling Script

SERVICES=(
    "sophiaai-dashboard-v2:2"      # 2 machines minimum
    "sophiaai-mcp-repo-v2:2"       # 2 machines minimum
    "sophiaai-mcp-research-v2:3"   # 3 machines (heavy processing)
    "sophiaai-mcp-context-v2:2"    # 2 machines minimum
    "sophiaai-mcp-business-v2:2"   # 2 machines minimum
    "sophiaai-jobs-v2:1"           # 1 machine (scheduled jobs)
)

echo "📈 MCP Platform Scaling - $(date)"

for service_config in "${SERVICES[@]}"; do
    app=$(echo "$service_config" | cut -d':' -f1)
    target_count=$(echo "$service_config" | cut -d':' -f2)
    
    echo "Scaling $app to $target_count machines..."
    
    if flyctl scale count "$target_count" --app "$app"; then
        echo "✅ $app scaled to $target_count machines"
    else
        echo "❌ Failed to scale $app"
    fi
done

echo "🏁 Scaling complete"
