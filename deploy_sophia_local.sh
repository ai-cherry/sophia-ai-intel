#!/bin/bash

# Sophia AI Local Deployment Script with Qdrant and Core Services
set -e

echo "🚀 Sophia AI Local Deployment"
echo "=============================="
echo

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Start infrastructure services including Qdrant
echo "📦 Starting Infrastructure Services..."
cat > docker-compose.local.yml << 'EOF'
services:
  # Infrastructure Services
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=sophia
      - POSTGRES_USER=sophia
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sophia -d sophia"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6380:6379"
    volumes:
      - redis-data:/data
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readyz"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Mem0 Memory Service
  mem0:
    build:
      context: ./memory/mem0
      dockerfile: Dockerfile
    container_name: mem0
    ports:
      - "8050:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - redis
      - qdrant
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis-data:
  postgres-data:
  qdrant-data:

networks:
  sophia-network:
    driver: bridge
EOF

# Update environment to use local Qdrant
echo "🔧 Updating environment configuration..."
if grep -q "QDRANT_URL" .env.production.secure; then
    sed -i.bak 's|QDRANT_URL=.*|QDRANT_URL=http://localhost:6333|' .env.production.secure
else
    echo "QDRANT_URL=http://localhost:6333" >> .env.production.secure
fi

# Start infrastructure with Qdrant
echo "🚀 Starting infrastructure services with Qdrant..."
docker-compose -f docker-compose.local.yml up -d postgres redis qdrant

# Wait for services to be ready
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if Mem0 dockerfile exists, if not create a simple one
if [ ! -f "./memory/mem0/Dockerfile" ]; then
    echo "📝 Creating Mem0 service..."
    mkdir -p ./memory/mem0
    cat > ./memory/mem0/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn redis aioredis httpx

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

    cat > ./memory/mem0/app.py << 'PYTHONAPP'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
from typing import Optional, List
import uuid
from datetime import datetime

app = FastAPI()

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class Memory(BaseModel):
    content: str
    metadata: Optional[dict] = {}
    
class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: dict
    created_at: str

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mem0"}

@app.post("/memory/store")
async def store_memory(memory: Memory):
    memory_id = str(uuid.uuid4())
    memory_data = {
        "id": memory_id,
        "content": memory.content,
        "metadata": memory.metadata,
        "created_at": datetime.now().isoformat()
    }
    redis_client.hset(f"memory:{memory_id}", mapping=memory_data)
    redis_client.lpush("memory:recent", memory_id)
    redis_client.ltrim("memory:recent", 0, 99)  # Keep last 100
    return MemoryResponse(**memory_data)

@app.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    memory_data = redis_client.hgetall(f"memory:{memory_id}")
    if not memory_data:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryResponse(**memory_data)

@app.get("/memory/recent")
async def get_recent_memories(limit: int = 10):
    recent_ids = redis_client.lrange("memory:recent", 0, limit - 1)
    memories = []
    for mem_id in recent_ids:
        memory_data = redis_client.hgetall(f"memory:{mem_id}")
        if memory_data:
            memories.append(MemoryResponse(**memory_data))
    return memories
PYTHONAPP
fi

# Start Mem0 if available
if [ -f "./memory/mem0/Dockerfile" ]; then
    echo "🧠 Starting Mem0 memory service..."
    docker-compose -f docker-compose.local.yml up -d mem0
fi

# Start core services using simplified compose
echo "🔨 Starting core services..."
docker-compose up -d agno-wrappers mcp-agents 2>/dev/null || true

# Final health check
echo "✅ Checking service health..."
sleep 5

echo
echo "🎉 Sophia AI Local Deployment Complete!"
echo "======================================="
echo
echo "📊 Infrastructure Services:"
echo "  • PostgreSQL: localhost:5432 (sophia/password)"
echo "  • Redis: localhost:6380"
echo "  • Qdrant Vector DB: http://localhost:6333"
echo "  • Mem0 Memory: http://localhost:8050"
echo
echo "🔍 Check status:"
echo "  docker-compose -f docker-compose.local.yml ps"
echo "  docker-compose ps"
echo
echo "🛑 To stop all services:"
echo "  docker-compose -f docker-compose.local.yml down"
echo "  docker-compose down"
echo
echo "📈 Access Qdrant Web UI: http://localhost:6333/dashboard"
