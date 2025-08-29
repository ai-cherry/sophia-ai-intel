#!/bin/bash

# Sophia AI Local Services Stop Script
# ====================================
# This script stops all locally running Sophia AI services

echo "🛑 STOPPING SOPHIA AI LOCAL SERVICES"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to stop a service
stop_service() {
    local service_name=$1
    local process_pattern=$2
    
    echo -n "Stopping $service_name..."
    
    pids=$(pgrep -f "$process_pattern" 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo -e " ${YELLOW}(not running)${NC}"
    else
        kill $pids 2>/dev/null
        echo -e " ${GREEN}✅${NC}"
    fi
}

# Stop services
stop_service "MCP Research Service" "real_search.py"
stop_service "Sophia Chat Service" "sophia_chat_simple.py"
stop_service "Dashboard" "next-server.*3001"

# Also check for any services on known ports
echo ""
echo "Checking for services on known ports..."

# Function to kill process on port
kill_port() {
    local port=$1
    local service=$2
    
    pid=$(lsof -t -i:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "Stopping $service on port $port... ${GREEN}✅${NC}"
        kill $pid 2>/dev/null
    fi
}

kill_port 8000 "MCP Research"
kill_port 8100 "Sophia Chat"
kill_port 3001 "Dashboard"

echo ""
echo -e "${GREEN}✅ All Sophia AI services stopped${NC}"
echo ""
echo "To restart services, run:"
echo "  ./scripts/deploy-local.sh"