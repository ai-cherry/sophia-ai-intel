#!/bin/bash
set -euo pipefail

# Sophia AI Deployment Fix Script
# Fixes all identified issues in the deployment infrastructure

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${SCRIPT_DIR}/.."

echo "=== Sophia AI Deployment Fix Script ==="
echo "This script will fix all deployment issues identified in the analysis"
echo

# Function to check if running with sufficient privileges
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
       echo "Please do not run this script as root for security reasons."
       exit 1
    fi
}

# Function to create backup
create_backup() {
    echo "Creating backup of configuration files..."
    BACKUP_DIR="${PROJECT_ROOT}/backups/deployment-fix-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup critical files
    cp -r "${PROJECT_ROOT}/docker-compose.yml" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/k8s-deploy" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/.env"* "$BACKUP_DIR/" 2>/dev/null || true
    
    echo "Backup created at: $BACKUP_DIR"
}

# Fix 1: Remove deprecated Fly.io configurations
fix_flyio_configs() {
    echo "Removing deprecated Fly.io configurations..."
    find "$PROJECT_ROOT" -name "fly.toml*" -type f | while read -r file; do
        echo "  Removing: $file"
        rm -f "$file"
    done
}

# Fix 2: Standardize environment variables
fix_env_variables() {
    echo "Standardizing environment variables..."
    
    # Create standardized env template
    cat > "${PROJECT_ROOT}/.env.standardized" << 'EOF'
# Standardized Environment Variables
# Use this as the source of truth

# Database
DATABASE_URL=${NEON_DATABASE_URL}
POSTGRES_URL=${DATABASE_URL}

# Vector Database
VECTOR_DB_URL=${QDRANT_URL}
VECTOR_DB_KEY=${QDRANT_API_KEY}

# Cache
CACHE_URL=${REDIS_URL}

# API Keys - Consistent naming
HUBSPOT_API_KEY=${HUBSPOT_ACCESS_TOKEN}
GONG_API_KEY=${GONG_ACCESS_KEY}
GONG_API_SECRET=${GONG_ACCESS_KEY_SECRET}
EOF
    
    echo "  Created .env.standardized"
}

# Fix 3: Update Redis configuration
create_redis_config() {
    echo "Creating optimized Redis configuration..."
    
    mkdir -p "${PROJECT_ROOT}/configs/redis"
    
    cat > "${PROJECT_ROOT}/configs/redis/redis.conf" << 'EOF'
# Sophia AI Redis Configuration

# Network
bind 0.0.0.0
protected-mode no
port 6379

# Memory
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Performance
tcp-backlog 511
tcp-keepalive 60
timeout 300
hz 100
databases 16

# Logging
loglevel notice
logfile /var/log/redis/redis.log
syslog-enabled yes
syslog-ident redis

# Security
requirepass ${REDIS_PASSWORD}

# Cluster (disabled for now)
# cluster-enabled yes
# cluster-config-file nodes.conf
# cluster-node-timeout 5000
EOF
    
    echo "  Created configs/redis/redis.conf"
}

# Fix 4: Create missing service directories
create_missing_services() {
    echo "Creating directories for missing MCP services..."
    
    local missing_services=(
        "mcp-gong"
        "mcp-salesforce"
        "mcp-slack"
        "mcp-apollo"
        "mcp-intercom"
        "mcp-linear"
        "mcp-looker"
        "mcp-asana"
        "mcp-notion"
        "mcp-gdrive"
        "mcp-costar"
        "mcp-phantom"
        "mcp-outlook"
        "mcp-sharepoint"
        "mcp-elevenlabs"
    )
    
    for service in "${missing_services[@]}"; do
        local service_dir="${PROJECT_ROOT}/services/${service}"
        if [ ! -d "$service_dir" ]; then
            echo "  Creating $service_dir"
            mkdir -p "$service_dir"
            
            # Create basic Dockerfile
            cat > "$service_dir/Dockerfile" << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
EOF
            
            # Create requirements.txt
            cat > "$service_dir/requirements.txt" << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
httpx==0.25.2
redis==5.0.1
EOF
            
            # Create basic app.py
            cat > "$service_dir/app.py" << EOF
"""
${service} MCP Service
TODO: Implement integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="${service}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health():
    return {"status": "healthy", "service": "${service}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF
        fi
    done
}

# Fix 5: Create Nginx cache configuration
create_nginx_cache_config() {
    echo "Creating Nginx cache configuration..."
    
    mkdir -p "${PROJECT_ROOT}/configs/nginx"
    
    cat > "${PROJECT_ROOT}/configs/nginx/cache.conf" << 'EOF'
# Nginx Cache Configuration

# Cache paths
proxy_cache_path /var/cache/nginx/api levels=1:2 keys_zone=api_cache:100m max_size=1g inactive=60m;
proxy_cache_path /var/cache/nginx/static levels=1:2 keys_zone=static_cache:100m max_size=10g inactive=24h;

# Cache settings for API responses
location ~* ^/api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_valid 404 1m;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;
    proxy_cache_background_update on;
    
    # Add cache status header
    add_header X-Cache-Status $upstream_cache_status;
}

# Cache settings for static assets
location ~* \.(jpg|jpeg|png|gif|ico|css|js|pdf|woff|woff2|ttf|svg)$ {
    proxy_cache static_cache;
    proxy_cache_valid 200 24h;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    
    # Browser cache
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Cache bypass for authenticated requests
proxy_cache_bypass $http_authorization;
proxy_no_cache $http_authorization;
EOF
    
    echo "  Created configs/nginx/cache.conf"
}

# Fix 6: Update deployment script
update_deployment_script() {
    echo "Updating Kubernetes deployment script..."
    
    cat > "${PROJECT_ROOT}/k8s-deploy/scripts/deploy-all-services.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

# Complete deployment script for all services

echo "=== Deploying ALL Sophia AI Services ==="

# Apply all manifests in correct order
kubectl apply -f k8s-deploy/manifests/namespace.yaml

# Infrastructure
kubectl apply -f k8s-deploy/manifests/redis.yaml
echo "Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n sophia --timeout=300s

# Core MCP Services
for manifest in k8s-deploy/manifests/mcp-*.yaml; do
    echo "Deploying $(basename $manifest)"
    kubectl apply -f "$manifest"
done

# Agno Services
kubectl apply -f k8s-deploy/manifests/agno-coordinator.yaml
kubectl apply -f k8s-deploy/manifests/agno-teams.yaml

# Orchestrator
kubectl apply -f k8s-deploy/manifests/orchestrator.yaml

# Frontend
kubectl apply -f k8s-deploy/manifests/sophia-dashboard.yaml

# Ingress
kubectl apply -f k8s-deploy/manifests/single-ingress.yaml

# Wait for all deployments
echo "Waiting for all deployments to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment --all -n sophia

echo "Deployment complete!"
kubectl get pods -n sophia
EOF
    
    chmod +x "${PROJECT_ROOT}/k8s-deploy/scripts/deploy-all-services.sh"
}

# Fix 7: Create caching library
create_caching_library() {
    echo "Creating caching library..."
    
    mkdir -p "${PROJECT_ROOT}/libs/cache"
    
    cat > "${PROJECT_ROOT}/libs/cache/__init__.py" << 'EOF'
"""
Sophia AI Caching Library
Provides unified caching interface for all services
"""

from .redis_cache import RedisCache, cache_decorator
from .llm_cache import LLMCache
from .invalidator import CacheInvalidator

__all__ = ['RedisCache', 'cache_decorator', 'LLMCache', 'CacheInvalidator']
EOF

    cat > "${PROJECT_ROOT}/libs/cache/redis_cache.py" << 'EOF'
"""Redis caching implementation"""

import json
import hashlib
import redis
from functools import wraps
from typing import Any, Optional, Callable
import asyncio

class RedisCache:
    def __init__(self, redis_url: str, db: int = 0, default_ttl: int = 300):
        self.redis = redis.from_url(redis_url, db=db, decode_responses=True)
        self.default_ttl = default_ttl
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = {"args": args, "kwargs": kwargs}
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        self.redis.setex(key, ttl or self.default_ttl, json.dumps(value))
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self.redis.delete(key)
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        keys = list(self.redis.scan_iter(match=pattern))
        if keys:
            return self.redis.delete(*keys)
        return 0

def cache_decorator(
    cache: RedisCache,
    ttl: Optional[int] = None,
    key_prefix: str = ""
) -> Callable:
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = cache._generate_key(key_prefix or func.__name__, *args, **kwargs)
            
            # Try cache first
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = cache._generate_key(key_prefix or func.__name__, *args, **kwargs)
            
            # Try cache first
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
EOF

    echo "  Created libs/cache/"
}

# Fix 8: Create service health checker
create_health_checker() {
    echo "Creating comprehensive health checker..."
    
    cat > "${PROJECT_ROOT}/scripts/health-check-all.sh" << 'EOF'
#!/bin/bash

# Health check all services

echo "=== Sophia AI Service Health Check ==="
echo

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url/healthz" > /dev/null 2>&1; then
        echo "✓ $name: Healthy"
    else
        echo "✗ $name: Unhealthy or unreachable"
    fi
}

# Docker Compose services
if [ "$1" = "docker" ]; then
    echo "Checking Docker Compose services..."
    check_service "Dashboard" "http://localhost:3000"
    check_service "Research" "http://localhost:8081"
    check_service "Context" "http://localhost:8082"
    check_service "GitHub" "http://localhost:8083"
    check_service "Business" "http://localhost:8084"
    check_service "Lambda" "http://localhost:8085"
    check_service "HubSpot" "http://localhost:8086"
    check_service "Agents" "http://localhost:8087"
    check_service "Prometheus" "http://localhost:9090"
    check_service "Grafana" "http://localhost:3001"
fi

# Kubernetes services
if [ "$1" = "k8s" ]; then
    echo "Checking Kubernetes services..."
    kubectl get pods -n sophia
    echo
    kubectl get services -n sophia
fi
EOF
    
    chmod +x "${PROJECT_ROOT}/scripts/health-check-all.sh"
}

# Main execution
main() {
    check_privileges
    create_backup
    
    echo "Starting fixes..."
    echo
    
    fix_flyio_configs
    fix_env_variables
    create_redis_config
    create_missing_services
    create_nginx_cache_config
    update_deployment_script
    create_caching_library
    create_health_checker
    
    echo
    echo "=== Deployment fixes completed! ==="
    echo
    echo "Next steps:"
    echo "1. Review and merge .env.standardized with your .env"
    echo "2. Update docker-compose.yml to use the new Redis config"
    echo "3. Run: docker-compose build --no-cache"
    echo "4. For Kubernetes: ./k8s-deploy/scripts/deploy-all-services.sh"
    echo "5. Monitor services: ./scripts/health-check-all.sh docker"
    echo
    echo "Port allocation summary:"
    echo "  - Frontend: 3000-3999"
    echo "  - Core services: 8000-8499"
    echo "  - Monitoring: 9000-9999"
    echo "  - Infrastructure: 5000-6999"
    echo
}

# Run main function
main "$@"
