#!/bin/bash

# Minimal Sophia AI Deployment Script
# Deploy core services with nginx reverse proxy

set -e

# Configuration
SSH_KEY_FILE="lambda-ssh-key"
REMOTE_HOST="192.222.51.223"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/sophia-ai-intel"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to run remote commands
remote_exec() {
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" "$REMOTE_USER@$REMOTE_HOST" "$1"
}

# Function to copy files to remote
remote_copy() {
    scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" "$1" "$REMOTE_USER@$REMOTE_HOST:$2"
}

log "🚀 Starting minimal Sophia AI deployment..."

# Step 1: Verify SSH connection
log "Step 1: Testing SSH connection..."
remote_exec "echo 'SSH connection successful'" || {
    error "Cannot connect to server at $REMOTE_HOST"
    exit 1
}

# Step 2: Stop all existing containers
log "Step 2: Stopping existing containers..."
remote_exec "cd $REMOTE_DIR && docker-compose down 2>/dev/null || true"
remote_exec "cd $REMOTE_DIR && docker stop \$(docker ps -aq) 2>/dev/null || true"
remote_exec "cd $REMOTE_DIR && docker rm \$(docker ps -aq) 2>/dev/null || true"

# Step 3: Stop system nginx
log "Step 3: Stopping system nginx..."
remote_exec "sudo systemctl stop nginx 2>/dev/null || true"
remote_exec "sudo systemctl disable nginx 2>/dev/null || true"

# Step 4: Clean up Docker system
log "Step 4: Cleaning Docker system..."
remote_exec "docker system prune -f"

# Step 5: Copy configuration files
log "Step 5: Copying configuration files..."
remote_copy "docker-compose.minimal.yml" "$REMOTE_DIR/docker-compose.yml"
remote_copy "nginx.conf.ssl" "$REMOTE_DIR/nginx.conf.ssl"
remote_copy ".env.production" "$REMOTE_DIR/.env.production"

# Step 6: Create necessary directories
log "Step 6: Creating directories..."
remote_exec "mkdir -p $REMOTE_DIR/ssl $REMOTE_DIR/acme-challenge"

# Step 7: Create basic health check file
log "Step 7: Creating health check file..."
remote_exec "echo 'healthy' > $REMOTE_DIR/acme-challenge/health.txt"

# Step 8: Start minimal deployment
log "Step 8: Starting minimal deployment..."
remote_exec "cd $REMOTE_DIR && docker-compose up -d"

# Step 9: Wait for services
log "Step 9: Waiting for services to start..."
sleep 30

# Step 10: Check service status
log "Step 10: Checking service status..."
remote_exec "cd $REMOTE_DIR && docker-compose ps"

# Step 11: Check logs
log "Step 11: Checking container logs..."
remote_exec "cd $REMOTE_DIR && docker-compose logs --tail=20"

# Step 12: Test internal connectivity
log "Step 12: Testing internal connectivity..."
remote_exec "docker exec \$(docker ps -q -f name=nginx) curl -f http://agno-coordinator:8080/health || echo 'Coordinator health check failed'"

# Step 13: Test external connectivity
log "Step 13: Testing external connectivity..."
sleep 5

# Test HTTP (should redirect to HTTPS)
HTTP_RESPONSE=$(curl -v http://www.sophia-intel.ai --connect-timeout 10 2>&1 | grep -E "HTTP/.* 301|HTTP/.* 200" | wc -l)
if [ "$HTTP_RESPONSE" -gt 0 ]; then
    success "HTTP connection working"
else
    warning "HTTP connection not responding"
fi

# Test HTTPS
HTTPS_RESPONSE=$(curl -k -v https://www.sophia-intel.ai --connect-timeout 10 2>&1 | grep -E "HTTP/.* 200|HTTP/.* 404" | wc -l)
if [ "$HTTPS_RESPONSE" -gt 0 ]; then
    success "HTTPS connection established"

    # Check if still 404
    HTTPS_404=$(curl -k -s https://www.sophia-intel.ai --connect-timeout 10 | grep -i "404" | wc -l)
    if [ "$HTTPS_404" -gt 0 ]; then
        warning "Still getting 404 - checking coordinator logs..."
        remote_exec "docker logs \$(docker ps -q -f name=agno-coordinator) --tail=20"
    else
        success "Application responding correctly!"
    fi
else
    error "HTTPS connection failed"
fi

success "Minimal deployment completed!"
log "Core services should now be running. Check the logs above for any issues."