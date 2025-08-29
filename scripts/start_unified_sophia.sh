#!/bin/bash
# START UNIFIED SOPHIA

echo "🚀 Starting Unified Sophia Services..."

# Start core services
cd services
python3 unified_swarm_service.py &
python3 real_swarm_executor.py &
python3 websocket_hub.py &

# Start MCP services
cd mcp-context && python3 app.py &
cd ../mcp-research && python3 app.py &
cd ../mcp-github && python3 app.py &

# Start dashboard
cd ../../apps/sophia-dashboard
npm run dev &

echo "✅ All services started!"
echo "🌐 Dashboard: http://localhost:3000"
echo "🔧 Swarm API: http://localhost:8100"
