#!/bin/bash
echo "Deploying all MCP services..."

# MCP Context (using enhanced version)
docker run -d --name mcp-context \
  --network sophia-network \
  -p 8081:8081 \
  -v $(pwd)/services/mcp-context:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python app_simple.py"

# MCP Research  
docker run -d --name mcp-research \
  --network sophia-network \
  -p 8085:8085 \
  -v $(pwd)/services/mcp-research:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python app.py"

# MCP GitHub
docker run -d --name mcp-github \
  --network sophia-network \
  -p 8082:8082 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python mcp-github-app.py"

# MCP HubSpot
docker run -d --name mcp-hubspot \
  --network sophia-network \
  -p 8083:8083 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python mcp-hubspot-app.py"

# MCP Salesforce
docker run -d --name mcp-salesforce \
  --network sophia-network \
  -p 8092:8092 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python mcp-salesforce-app.py"

# MCP Gong
docker run -d --name mcp-gong \
  --network sophia-network \
  -p 8091:8091 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python mcp-gong-app.py"

# MCP Agents
docker run -d --name mcp-agents \
  --network sophia-network \
  -p 8000:8000 \
  -v $(pwd)/services/mcp-agents:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python app.py"

# AGNO Coordinator
docker run -d --name agno-coordinator \
  --network sophia-network \
  -p 8080:8080 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python agno-coordinator-app.py"

# Orchestrator
docker run -d --name orchestrator \
  --network sophia-network \
  -p 8088:8088 \
  -v $(pwd)/services:/app \
  -w /app \
  python:3.11-slim sh -c "pip install fastapi uvicorn pydantic && python orchestrator-app.py"

echo "All services deployed. Waiting for startup..."
sleep 10

echo "Checking service health..."
for port in 8081 8085 8082 8083 8092 8091 8000 8080 8088; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | grep -o "healthy" || echo "starting..."
done
