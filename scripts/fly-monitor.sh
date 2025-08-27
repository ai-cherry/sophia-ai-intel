#!/bin/bash

echo "📊 Fly.io Monitoring Dashboard"
echo "============================="

APP_NAME=${FLY_APP_NAME:-sophia-mcp-platform}
REFRESH_INTERVAL=${1:-5}

# Function to get metrics
get_metrics() {
    clear
    echo "📊 Fly.io Monitoring Dashboard - $(date)"
    echo "============================="
    echo ""
    
    # App status
    echo "📱 Application Status:"
    flyctl status --app "$APP_NAME"
    
    echo ""
    echo "🔧 Instances:"
    flyctl scale show --app "$APP_NAME"
    
    echo ""
    echo "💾 Resource Usage:"
    flyctl vm status --app "$APP_NAME"
    
    echo ""
    echo "📈 Recent Logs:"
    flyctl logs --app "$APP_NAME" -n 10
    
    echo ""
    echo "Refreshing in $REFRESH_INTERVAL seconds... (Ctrl+C to exit)"
}

# Monitoring loop
while true; do
    get_metrics
    sleep "$REFRESH_INTERVAL"
done