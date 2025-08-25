#!/bin/bash

# Sophia AI Intel - Secure Deployment Script
# This script validates environment variables and deploys services securely

set -e

echo "🔐 Starting secure deployment process for Sophia AI Intel..."
echo "======================================================"

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Validate environment variables
log "Step 1: Validating environment variables..."
if ! ./scripts/validate-env.sh; then
    log "❌ Environment validation failed. Aborting deployment."
    exit 1
fi

# Check if .env file exists and has proper permissions
if [[ -f ".env" ]]; then
    log "Checking .env file permissions..."
    env_permissions=$(stat -c "%a" .env 2>/dev/null || stat -f "%Lp" .env | cut -c -3)
    if [[ "$env_permissions" != "600" ]]; then
        log "⚠️  WARNING: .env file has permissions $env_permissions. Recommended: 600"
        log "Setting secure permissions on .env file..."
        chmod 600 .env
    fi
else
    log "⚠️  WARNING: .env file not found. Using environment variables."
fi

# Check if docker-compose.yml exists
if [[ ! -f "docker-compose.yml" ]]; then
    log "❌ ERROR: docker-compose.yml not found in current directory"
    exit 1
fi

# Validate docker-compose configuration
log "Step 2: Validating Docker Compose configuration..."
if ! docker-compose config --quiet; then
    log "❌ ERROR: Invalid docker-compose.yml configuration"
    exit 1
fi

# Check available resources
log "Step 3: Checking system resources..."
available_memory=$(docker system info --format '{{.MemTotal}}' 2>/dev/null || echo "unknown")
if [[ "$available_memory" != "unknown" ]]; then
    available_gb=$((available_memory / 1024 / 1024 / 1024))
    log "Available memory: ${available_gb}GB"
    if [[ $available_gb -lt 4 ]]; then
        log "⚠️  WARNING: Less than 4GB available memory. Deployment may fail."
    fi
fi

# Stop existing services gracefully
log "Step 4: Stopping existing services..."
docker-compose down --timeout 30 2>/dev/null || true

# Clean up unused resources
log "Step 5: Cleaning up Docker resources..."
docker system prune -f >/dev/null 2>&1 || true

# Deploy services
log "Step 6: Starting services..."
if ! docker-compose up -d --build; then
    log "❌ ERROR: Failed to start services"
    log "Checking service status..."
    docker-compose ps
    exit 1
fi

# Wait for services to be healthy
log "Step 7: Waiting for services to become healthy..."
max_attempts=30
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    log "Health check attempt $attempt/$max_attempts..."

    # Check if all services are running
    running_services=$(docker-compose ps --format json | jq -r '.[] | select(.State == "running") | .Name' | wc -l)
    total_services=$(docker-compose ps --format json | jq -r '.[].Name' | wc -l)

    if [[ $running_services -eq $total_services ]]; then
        log "✅ All services are running ($running_services/$total_services)"
        break
    else
        log "⏳ Services status: $running_services/$total_services running"
    fi

    sleep 10
    ((attempt++))
done

if [[ $attempt -gt $max_attempts ]]; then
    log "⚠️  WARNING: Not all services are healthy after $max_attempts attempts"
    log "Current service status:"
    docker-compose ps
else
    log "✅ Deployment completed successfully!"
fi

# Show final status
log "Final service status:"
docker-compose ps --format table

# Show resource usage
log "Resource usage summary:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

log "======================================================"
log "🎉 Secure deployment process completed!"
log ""
log "Next steps:"
log "  - Monitor services: docker-compose logs -f"
log "  - Check health: curl http://localhost/health"
log "  - View resource usage: docker stats"
log ""
log "For production deployment, ensure:"
log "  - .env file is not committed to version control"
log "  - All API keys are properly configured"
log "  - SSL certificates are installed"
log "  - Monitoring and logging are configured"