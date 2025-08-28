#!/bin/bash
# Sophia AI + Claude Integration Script

export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH

echo "Sophia AI Development Environment Status"
echo "======================================="
echo "🔧 Running Services:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo
echo "🌐 Access Points:"
echo "  • Adminer (DB):      http://localhost:8080"
echo "  • Redis Commander:   http://localhost:8081"
echo "  • Qdrant Vector DB:  http://localhost:6333"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Jaeger Tracing:    http://localhost:16686"
echo
echo "💡 MCP Server Endpoints:"
echo "  • Qdrant:           localhost:6333"
echo "  • PostgreSQL:       localhost:5432"  
echo "  • Redis:            localhost:6380"
echo
echo "🤖 AI Development Ready - Use MCP context with running services"
