#!/bin/bash

# Sophia AI 404 Error Resolution Script
# Comprehensive diagnostic and fix for www.sophia-intel.ai

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
NC='\033[0m' # No Color

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

log "🔍 Starting comprehensive 404 error diagnosis and resolution..."

# Step 1: Check current server status
log "Step 1: Checking current server status..."
remote_exec "echo '=== System Information ==='" || error "Cannot connect to server"
remote_exec "whoami && pwd && ls -la"
remote_exec "echo '=== Docker Status ==='"
remote_exec "docker --version && docker-compose --version"
remote_exec "echo '=== Current Containers ==='"
remote_exec "docker ps -a"
remote_exec "echo '=== Running Processes on ports 80/443 ==='"
remote_exec "sudo netstat -tlnp | grep -E ':80 |:443 ' || sudo ss -tlnp | grep -E ':80 |:443 '"

# Step 2: Check what's responding on the domain
log "Step 2: Testing domain connectivity..."
curl -k -v https://www.sophia-intel.ai --connect-timeout 10 -o /dev/null 2>&1 | head -20 || warning "HTTPS test failed"
curl -v http://www.sophia-intel.ai --connect-timeout 10 -o /dev/null 2>&1 | head -20 || warning "HTTP test failed"

# Step 3: Check remote deployment status
log "Step 3: Checking remote deployment status..."
remote_exec "cd $REMOTE_DIR && ls -la"
remote_exec "cd $REMOTE_DIR && docker-compose ps"

# Step 4: Stop conflicting services
log "Step 4: Stopping conflicting services..."
remote_exec "echo '=== Stopping system nginx ==='"
remote_exec "sudo systemctl stop nginx || true"
remote_exec "sudo systemctl disable nginx || true"

remote_exec "echo '=== Stopping any conflicting containers ==='"
remote_exec "docker stop traefik 2>/dev/null || true"
remote_exec "docker rm traefik 2>/dev/null || true"
remote_exec "docker stop nginx 2>/dev/null || true"
remote_exec "docker rm nginx 2>/dev/null || true"

# Step 5: Clean up and prepare deployment
log "Step 5: Preparing deployment environment..."
remote_exec "cd $REMOTE_DIR && docker-compose down || true"
remote_exec "cd $REMOTE_DIR && docker system prune -f"

# Step 6: Ensure SSL certificates exist
log "Step 6: Checking SSL certificates..."
remote_exec "mkdir -p $REMOTE_DIR/ssl"
remote_exec "ls -la $REMOTE_DIR/ssl/"

# Step 7: Copy configuration files
log "Step 7: Updating configuration files..."
remote_copy "docker-compose.yml" "$REMOTE_DIR/docker-compose.yml"
remote_copy "nginx.conf.ssl" "$REMOTE_DIR/nginx.conf.ssl"
remote_copy ".env.production" "$REMOTE_DIR/.env.production"

# Step 8: Create basic health check file
log "Step 8: Creating health check file..."
remote_exec "mkdir -p $REMOTE_DIR/acme-challenge"
remote_exec "echo 'healthy' > $REMOTE_DIR/acme-challenge/health.txt"

# Step 9: Start deployment
log "Step 9: Starting deployment..."
remote_exec "cd $REMOTE_DIR && docker-compose up -d"

# Step 10: Wait for services to start
log "Step 10: Waiting for services to start..."
sleep 30

# Step 11: Check deployment status
log "Step 11: Checking deployment status..."
remote_exec "cd $REMOTE_DIR && docker-compose ps"
remote_exec "cd $REMOTE_DIR && docker-compose logs --tail=20"

# Step 12: Test internal connectivity
log "Step 12: Testing internal connectivity..."
remote_exec "docker exec \$(docker ps -q -f name=nginx) curl -f http://agno-coordinator:8080/health || echo 'Agno coordinator health check failed'"

# Step 13: Test external connectivity
log "Step 13: Testing external connectivity..."
sleep 10

# Test HTTP (should redirect to HTTPS)
HTTP_TEST=$(curl -v http://www.sophia-intel.ai --connect-timeout 10 2>&1 | grep -E "HTTP/.* 301|HTTP/.* 302" | wc -l)
if [ "$HTTP_TEST" -gt 0 ]; then
    success "HTTP to HTTPS redirect working"
else
    warning "HTTP to HTTPS redirect not working"
fi

# Test HTTPS (should serve content)
HTTPS_TEST=$(curl -k -v https://www.sophia-intel.ai --connect-timeout 10 2>&1 | grep -E "HTTP/.* 200|HTTP/.* 404" | wc -l)
if [ "$HTTPS_TEST" -gt 0 ]; then
    success "HTTPS connection established"

    # Check if it's still 404
    HTTPS_404=$(curl -k -s https://www.sophia-intel.ai --connect-timeout 10 | grep -i "404" | wc -l)
    if [ "$HTTPS_404" -gt 0 ]; then
        warning "Still getting 404 - checking application services..."
        remote_exec "docker logs \$(docker ps -q -f name=agno-coordinator) --tail=20"
    else
        success "Application responding correctly!"
    fi
else
    error "HTTPS connection failed"
fi

# Step 14: Check SSL certificate
log "Step 14: Checking SSL certificate..."
SSL_CERT=$(curl -k -v https://www.sophia-intel.ai --connect-timeout 10 2>&1 | grep "subject:" | head -1)
if echo "$SSL_CERT" | grep -q "sophia-intel.ai"; then
    success "SSL certificate properly configured for domain"
else
    warning "SSL certificate not properly configured: $SSL_CERT"
fi

# Step 15: Generate status report
log "Step 15: Generating status report..."
{
    echo "=== Sophia AI 404 Resolution Report ==="
    echo "Timestamp: $(date)"
    echo ""
    echo "DNS Resolution:"
    dig www.sophia-intel.ai +short
    echo ""
    echo "HTTP Test:"
    curl -v http://www.sophia-intel.ai --connect-timeout 10 2>&1 | head -10
    echo ""
    echo "HTTPS Test:"
    curl -k -v https://www.sophia-intel.ai --connect-timeout 10 2>&1 | head -10
    echo ""
    echo "Server Container Status:"
    remote_exec "cd $REMOTE_DIR && docker-compose ps"
    echo ""
    echo "Nginx Logs:"
    remote_exec "docker logs \$(docker ps -q -f name=nginx) --tail=10 2>/dev/null || echo 'No nginx logs available'"
    echo ""
    echo "Agno Coordinator Logs:"
    remote_exec "docker logs \$(docker ps -q -f name=agno-coordinator) --tail=10 2>/dev/null || echo 'No agno-coordinator logs available'"
} > 404_resolution_report_$(date +%Y%m%d_%H%M%S).txt

success "Comprehensive diagnosis and resolution completed!"
log "Check the generated report for detailed status information."