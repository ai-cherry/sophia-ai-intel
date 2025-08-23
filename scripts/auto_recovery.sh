#!/bin/bash
# Automated recovery for failed services

SERVICES=(
    "sophiaai-dashboard-v2"
    "sophiaai-mcp-repo-v2"
    "sophiaai-mcp-research-v2"
    "sophiaai-mcp-context-v2"
    "sophiaai-mcp-business-v2"
    "sophiaai-jobs-v2"
)

echo "🚑 Starting automated recovery - $(date)"

for app in "${SERVICES[@]}"; do
    echo "Checking $app..."
    
    if status=$(flyctl status --app "$app" 2>/dev/null); then
        if echo "$status" | grep -q "stopped\|crashed"; then
            echo "🔄 Restarting $app..."
            
            # Try to restart the service
            if flyctl machine restart --app "$app" 2>/dev/null; then
                echo "✅ $app restarted successfully"
            else
                echo "❌ Failed to restart $app - manual intervention required"
                
                # Try to redeploy if restart fails
                echo "🔄 Attempting redeploy of $app..."
                flyctl deploy --app "$app" --ha=false --wait-timeout=300 2>/dev/null || \
                echo "❌ Redeploy failed for $app"
            fi
        else
            echo "✅ $app is healthy"
        fi
    else
        echo "❌ Cannot check status of $app"
    fi
done

echo "🏁 Recovery process complete - $(date)"
