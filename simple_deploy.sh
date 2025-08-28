#!/bin/bash
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH

echo "🚀 Sophia AI - Simple Consolidated Deployment"
echo "============================================="

# Clean up any existing containers
docker rm -f sophia-redis sophia-postgres sophia-ai-core sophia-dashboard 2>/dev/null

# Start Redis
echo "Starting Redis..."
docker run -d --name sophia-redis -p 6380:6379 redis:7-alpine

# Start PostgreSQL  
echo "Starting PostgreSQL..."
docker run -d --name sophia-postgres -p 5433:5432 
  -e POSTGRES_DB=sophia 
  -e POSTGRES_USER=sophia 
  -e POSTGRES_PASSWORD=sophia_secure_password_2024 
  postgres:15-alpine

# Wait for databases
echo "Waiting for databases..."
sleep 15

# Start Sophia AI Core
echo "Starting Sophia AI Core..."
docker run -d --name sophia-ai-core 
  --link sophia-redis:redis 
  --link sophia-postgres:postgres 
  -p 8080:8080 
  -e NODE_ENV=production 
  -e REDIS_URL=redis://redis:6379 
  -e DATABASE_URL=postgresql://sophia:sophia_secure_password_2024@postgres:5432/sophia 
  sophia-registry/sophia-ai-core:latest

# Start Dashboard
echo "Starting Sophia Dashboard..."  
docker run -d --name sophia-dashboard 
  --link sophia-ai-core:api 
  -p 3000:3000 
  -e NODE_ENV=production 
  -e NEXT_PUBLIC_API_BASE_URL=http://localhost:8080 
  sophia-dashboard:latest

echo ""
echo "✅ Basic Sophia AI Deployment Complete!"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard:    http://localhost:3000"
echo "   AI Core API:  http://localhost:8080"  
echo "   PostgreSQL:   localhost:5433"
echo "   Redis:        localhost:6380"
echo ""
echo "📊 Check Status: docker ps"
echo "📋 View Logs:    docker logs [container-name]"
