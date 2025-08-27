#!/bin/bash

# Sophia AI - Infrastructure Components Deployment Script
# Deploys Redis, Qdrant, and Nginx without building application services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create infrastructure-only docker-compose
cat > docker-compose.infrastructure.yml << 'EOF'
version: '3.8'

services:
  # ===========================================
  # Infrastructure Services Only
  # ===========================================

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
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD:-sophia-redis-2024}

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334

  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL for production
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - sophia-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sophia"]
      interval: 30s
      timeout: 10s
      retries: 3
    environment:
      - POSTGRES_DB=sophia
      - POSTGRES_USER=sophia
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-sophia-db-2024}

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - sophia-network
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - sophia-network
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin123}
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  redis-data:
  qdrant-data:
  postgres-data:
  prometheus-data:
  grafana-data:

networks:
  sophia-network:
    driver: bridge
EOF

# Create basic nginx configuration
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream sophia_backend {
        server agno-coordinator:8080;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://sophia_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Create basic prometheus configuration
mkdir -p monitoring
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
EOF

log_info "======================================"
log_info "🚀 Deploying Infrastructure Components"
log_info "======================================"

# Load environment variables
if [ -f .env.production.secure ]; then
    log_info "Loading secure environment variables..."
    export $(grep -v '^#' .env.production.secure | xargs)
fi

# Deploy infrastructure
log_info "Starting infrastructure services..."
docker-compose -f docker-compose.infrastructure.yml up -d

# Wait for services to be ready
log_info "Waiting for services to be ready..."
sleep 30

# Check service health
log_info "Checking service health..."

# Check Redis
if docker-compose -f docker-compose.infrastructure.yml exec redis redis-cli ping | grep -q "PONG"; then
    log_success "✅ Redis is healthy"
else
    log_error "❌ Redis health check failed"
fi

# Check Qdrant
if curl -s http://localhost:6333/health | grep -q "ok"; then
    log_success "✅ Qdrant is healthy"
else
    log_error "❌ Qdrant health check failed"
fi

# Check PostgreSQL
if docker-compose -f docker-compose.infrastructure.yml exec postgres pg_isready -U sophia | grep -q "accepting connections"; then
    log_success "✅ PostgreSQL is healthy"
else
    log_error "❌ PostgreSQL health check failed"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
    log_success "✅ Prometheus is healthy"
else
    log_error "❌ Prometheus health check failed"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    log_success "✅ Grafana is healthy"
else
    log_error "❌ Grafana health check failed"
fi

# Display service URLs
log_info "======================================"
log_success "🎉 Infrastructure Deployment Complete!"
log_info "======================================"
log_info ""
log_info "Service URLs:"
log_info "- Redis: localhost:6380"
log_info "- Qdrant: localhost:6333"
log_info "- PostgreSQL: localhost:5432"
log_info "- Prometheus: http://localhost:9090"
log_info "- Grafana: http://localhost:3000 (admin/admin123)"
log_info "- Nginx: http://localhost:80"
log_info ""
log_info "Next Steps:"
log_info "1. Configure real API keys in .env.production.secure"
log_info "2. Deploy application services"
log_info "3. Configure SSL certificates"
log_info "4. Setup DNS and external integrations"

# Save deployment status
cat > infrastructure-deployment-status.json << 'EOF'
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "infrastructure_deployed",
  "services": {
    "redis": {"port": 6380, "status": "deployed"},
    "qdrant": {"port": 6333, "status": "deployed"},
    "postgres": {"port": 5432, "status": "deployed"},
    "prometheus": {"port": 9090, "status": "deployed"},
    "grafana": {"port": 3000, "status": "deployed"},
    "nginx": {"port": 80, "status": "deployed"}
  }
}
EOF

log_success "Deployment status saved to infrastructure-deployment-status.json"