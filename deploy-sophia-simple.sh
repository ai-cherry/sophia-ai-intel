#!/bin/bash

echo "🚀 Sophia AI Platform - Simple Local Deployment"
echo "=============================================="
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check Docker
check_docker() {
    if docker ps >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Docker is not running${NC}"
        echo
        echo "Please start Docker Desktop manually:"
        echo "1. Open Docker Desktop from Applications"
        echo "2. Wait for the Docker icon in the menu bar to show 'Docker Desktop is running'"
        echo "3. Then run this script again"
        echo
        return 1
    fi
}

# Check if Docker is running
if ! check_docker; then
    exit 1
fi

echo
echo "Starting Sophia AI Platform deployment..."
echo

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true
docker rm -f postgres redis qdrant 2>/dev/null || true

# Create network if not exists
echo "🌐 Creating Docker network..."
docker network create sophia-network 2>/dev/null || true

# Start infrastructure services
echo "🗄️ Starting infrastructure services..."
echo "  - PostgreSQL (port 5432)"
docker run -d \
    --name postgres \
    --network sophia-network \
    -p 5432:5432 \
    -e POSTGRES_PASSWORD=sophia123 \
    -e POSTGRES_USER=sophia \
    -e POSTGRES_DB=sophia \
    postgres:15-alpine

echo "  - Redis (port 6379)"
docker run -d \
    --name redis \
    --network sophia-network \
    -p 6379:6379 \
    redis:7-alpine

echo "  - Qdrant (ports 6333-6334)"
docker run -d \
    --name qdrant \
    --network sophia-network \
    -p 6333:6333 \
    -p 6334:6334 \
    qdrant/qdrant:latest

# Wait for services to be ready
echo
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check services
echo
echo "🔍 Checking service health..."
if docker exec postgres pg_isready -U sophia >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${YELLOW}⚠️ PostgreSQL is still starting...${NC}"
fi

if docker exec redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${YELLOW}⚠️ Redis is still starting...${NC}"
fi

if curl -sf http://localhost:6333/readyz >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is ready${NC}"
else
    echo -e "${YELLOW}⚠️ Qdrant is still starting...${NC}"
fi

# Try to start pre-built images if available
echo
echo "🚀 Attempting to start Sophia services..."

# Check if pre-built images exist
if docker images | grep -q sophia-registry; then
    echo "Found pre-built Sophia images, starting services..."
    
    docker run -d \
        --name sophia-ai-core \
        --network sophia-network \
        -p 8000:8000 \
        -e POSTGRES_URL=postgresql://sophia:sophia123@postgres:5432/sophia \
        -e REDIS_URL=redis://redis:6379 \
        sophia-registry/sophia-ai-core:latest 2>/dev/null && \
        echo -e "${GREEN}✅ Started sophia-ai-core${NC}" || \
        echo -e "${YELLOW}⚠️ Could not start sophia-ai-core${NC}"
        
    docker run -d \
        --name sophia-dashboard \
        --network sophia-network \
        -p 3001:3000 \
        sophia-dashboard:latest 2>/dev/null && \
        echo -e "${GREEN}✅ Started sophia-dashboard${NC}" || \
        echo -e "${YELLOW}⚠️ Could not start sophia-dashboard${NC}"
else
    echo -e "${YELLOW}Pre-built images not found. You can build them using docker-compose.yml${NC}"
fi

echo
echo "=========================================="
echo -e "${GREEN}🎉 Infrastructure deployment complete!${NC}"
echo "=========================================="
echo
echo "📊 Access URLs:"
echo "  PostgreSQL: localhost:5432 (user: sophia, pass: sophia123)"
echo "  Redis:      localhost:6379"
echo "  Qdrant:     localhost:6333 (Web UI: http://localhost:6333/dashboard)"
echo
echo "📝 View running containers:"
echo "  docker ps"
echo
echo "📋 View logs:"
echo "  docker logs postgres"
echo "  docker logs redis"
echo "  docker logs qdrant"
echo
echo "🛑 To stop all services:"
echo "  docker stop postgres redis qdrant"
echo "  docker rm postgres redis qdrant"
echo
echo "🚀 Next steps:"
echo "  1. Start Docker Desktop if not running"
echo "  2. Use 'docker-compose up -d' to start all services"
echo "  3. Or use 'docker-compose -f docker-compose.prebuilt.yml up -d' for pre-built images"
echo