#!/bin/bash

# Sophia AI Production Deployment Script
# Deploy complete application stack to Lambda Labs server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="192.222.51.223"
PRODUCTION_USER="ubuntu"
SSH_KEY="lambda-ssh-key"
PROJECT_DIR="/home/ubuntu/sophia-ai-intel"
LOCAL_PROJECT_DIR="."

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if SSH key exists
    if [[ ! -f "$SSH_KEY" ]]; then
        error "SSH key '$SSH_KEY' not found!"
    fi
    
    # Check SSH key permissions
    chmod 600 "$SSH_KEY"
    
    # Check if docker-compose.yml exists
    if [[ ! -f "docker-compose.yml" ]]; then
        error "docker-compose.yml not found in current directory!"
    fi
    
    # Check if services directory exists
    if [[ ! -d "services" ]]; then
        error "services directory not found!"
    fi
    
    log "✅ Prerequisites check passed"
}

# Test SSH connection
test_ssh_connection() {
    log "🔗 Testing SSH connection..."
    
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" "echo 'SSH connection successful'"; then
        log "✅ SSH connection successful"
    else
        error "SSH connection failed!"
    fi
}

# Create production environment file
create_production_env() {
    log "🔧 Creating production environment file..."
    
    # Create .env.production from template
    if [[ -f ".env.production.template" ]]; then
        cp .env.production.template .env.production
        
        # Generate secure secrets
        JWT_SECRET=$(openssl rand -base64 32)
        API_SECRET_KEY=$(openssl rand -base64 32)
        BACKUP_ENCRYPTION_KEY=$(openssl rand -base64 32)
        POSTGRES_PASSWORD=$(openssl rand -base64 16)
        GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)
        
        # Replace placeholders with generated values
        sed -i.bak "s|<GENERATE_SECURE_JWT_SECRET>|$JWT_SECRET|g" .env.production
        sed -i.bak "s|<GENERATE_SECURE_API_SECRET>|$API_SECRET_KEY|g" .env.production
        sed -i.bak "s|<GENERATE_SECURE_BACKUP_KEY>|$BACKUP_ENCRYPTION_KEY|g" .env.production
        sed -i.bak "s|<YOUR_POSTGRES_PASSWORD>|$POSTGRES_PASSWORD|g" .env.production
        sed -i.bak "s|<YOUR_GRAFANA_ADMIN_PASSWORD>|$GRAFANA_ADMIN_PASSWORD|g" .env.production
        
        # Set database URL
        sed -i.bak "s|<YOUR_POSTGRESQL_CONNECTION_STRING>|postgresql://sophia:$POSTGRES_PASSWORD@postgres:5432/sophia|g" .env.production
        sed -i.bak "s|<YOUR_REDIS_CONNECTION_STRING>|redis://redis:6379|g" .env.production
        sed -i.bak "s|<YOUR_QDRANT_URL>|http://qdrant:6333|g" .env.production
        
        # Remove backup file
        rm -f .env.production.bak
        
        log "✅ Production environment file created"
    else
        warn "No .env.production.template found, using existing .env if available"
    fi
}

# Sync source code to production server
sync_source_code() {
    log "📦 Syncing source code to production server..."
    
    # Create project directory on server
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" \
        "sudo mkdir -p $PROJECT_DIR && sudo chown ubuntu:ubuntu $PROJECT_DIR"
    
    # Rsync project files (excluding node_modules, .git, etc.)
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='*.pyc' \
        --exclude='.env.local' \
        --exclude='.env.development' \
        --exclude='darwin-arm64' \
        --exclude='.ruff_cache' \
        --exclude='proofs' \
        --exclude='backups' \
        -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
        "$LOCAL_PROJECT_DIR/" "$PRODUCTION_USER@$PRODUCTION_SERVER:$PROJECT_DIR/"
    
    log "✅ Source code synced successfully"
}

# Setup production environment on server
setup_production_environment() {
    log "🛠️ Setting up production environment on server..."
    
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" << 'EOF'
        set -e
        cd /home/ubuntu/sophia-ai-intel
        
        echo "🐳 Updating Docker and Docker Compose..."
        sudo apt-get update -qq
        sudo apt-get install -y docker.io docker-compose-plugin
        sudo usermod -aG docker ubuntu
        sudo systemctl enable docker
        sudo systemctl start docker
        
        echo "🔧 Stopping system nginx if running..."
        sudo systemctl stop nginx || true
        sudo systemctl disable nginx || true
        
        echo "🗂️ Creating required directories..."
        mkdir -p ssl acme-challenge logs monitoring/grafana/dashboards
        sudo chown -R ubuntu:ubuntu /home/ubuntu/sophia-ai-intel
        
        echo "🔑 Setting up environment file..."
        if [[ -f ".env.production" ]]; then
            cp .env.production .env
            echo "✅ Production environment configured"
        else
            echo "⚠️ No .env.production found, using template"
            if [[ -f ".env.production.template" ]]; then
                cp .env.production.template .env
            fi
        fi
        
        echo "📂 Verifying critical directories..."
        for dir in services libs jobs monitoring scripts; do
            if [[ -d "$dir" ]]; then
                echo "✅ Directory $dir exists"
            else
                echo "❌ Missing directory: $dir"
            fi
        done
EOF
    
    log "✅ Production environment setup complete"
}

# Optimize Dockerfiles for production
optimize_dockerfiles() {
    log "🚀 Optimizing Dockerfiles for production builds..."
    
    # Create .dockerignore if it doesn't exist
    if [[ ! -f ".dockerignore" ]]; then
        cat > .dockerignore << 'EOF'
.git
.github
node_modules
__pycache__
.pytest_cache
*.pyc
.env.local
.env.development
proofs
backups
darwin-arm64
.ruff_cache
*.md
docs
tests
.vscode
EOF
    fi
    
    log "✅ Docker optimization complete"
}

# Build and deploy services
build_and_deploy_services() {
    log "🏗️ Building and deploying services..."
    
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" << 'EOF'
        set -e
        cd /home/ubuntu/sophia-ai-intel
        
        echo "🐳 Setting Docker BuildKit environment..."
        export DOCKER_BUILDKIT=1
        export COMPOSE_DOCKER_CLI_BUILD=1
        
        echo "🛑 Stopping any existing services..."
        docker-compose down --remove-orphans || true
        
        echo "🧹 Cleaning up old images and volumes..."
        docker system prune -f
        docker volume prune -f
        
        echo "🏗️ Building services with optimizations..."
        docker-compose build --parallel --compress --no-cache
        
        echo "🚀 Starting services..."
        docker-compose up -d
        
        echo "⏳ Waiting for services to initialize..."
        sleep 30
        
        echo "📊 Checking service status..."
        docker-compose ps
        
        echo "🔍 Checking logs for any immediate issues..."
        docker-compose logs --tail=10 nginx || true
        docker-compose logs --tail=10 agno-coordinator || true
EOF
    
    log "✅ Services built and deployed"
}

# Verify deployment health
verify_deployment() {
    log "🩺 Verifying deployment health..."
    
    # Check service status
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" << 'EOF'
        set -e
        cd /home/ubuntu/sophia-ai-intel
        
        echo "📊 Service container status:"
        docker-compose ps
        
        echo ""
        echo "🔍 Health check results:"
        
        # Test internal health endpoints
        for service in redis postgres qdrant; do
            if docker-compose exec -T $service echo "Service $service is accessible" 2>/dev/null; then
                echo "✅ $service: Running"
            else
                echo "❌ $service: Not accessible"
            fi
        done
        
        echo ""
        echo "🌐 Testing nginx configuration..."
        if docker-compose exec -T nginx nginx -t; then
            echo "✅ Nginx configuration is valid"
        else
            echo "❌ Nginx configuration has errors"
        fi
        
        echo ""
        echo "📈 Resource usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
EOF
    
    log "✅ Health verification complete"
}

# Test domain connectivity
test_domain_connectivity() {
    log "🌍 Testing domain connectivity..."
    
    # Test from local machine
    info "Testing www.sophia-intel.ai from local machine..."
    
    if curl -s -o /dev/null -w "%{http_code}" "http://www.sophia-intel.ai/health" | grep -q "200"; then
        log "✅ Domain health check successful"
    else
        warn "Domain health check failed - services may still be starting"
    fi
    
    # Test from production server
    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" << 'EOF'
        echo "🌐 Testing services from production server..."
        
        # Test nginx health
        if curl -s localhost:80/health | grep -q "healthy"; then
            echo "✅ Nginx health endpoint working"
        else
            echo "❌ Nginx health endpoint failed"
        fi
        
        # Test internal service connectivity
        for port in 8080 8000 8081 8082 8083 8084 8085 8086; do
            if curl -s --connect-timeout 5 "localhost:$port/healthz" >/dev/null 2>&1; then
                echo "✅ Service on port $port responding"
            else
                echo "⚠️ Service on port $port not responding (may still be starting)"
            fi
        done
EOF
    
    log "✅ Domain connectivity test complete"
}

# Generate deployment report
generate_deployment_report() {
    log "📋 Generating deployment report..."
    
    REPORT_FILE="deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "Sophia AI Production Deployment Report"
        echo "========================================"
        echo "Deployment Date: $(date)"
        echo "Production Server: $PRODUCTION_SERVER"
        echo "Project Directory: $PROJECT_DIR"
        echo ""
        
        echo "Services Deployed:"
        echo "------------------"
        ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" \
            "cd $PROJECT_DIR && docker-compose ps --format table"
        
        echo ""
        echo "Service Health Status:"
        echo "----------------------"
        ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" \
            "cd $PROJECT_DIR && docker-compose ps --services" | while read service; do
            if ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$PRODUCTION_USER@$PRODUCTION_SERVER" \
                "cd $PROJECT_DIR && docker-compose exec -T $service echo 'OK' 2>/dev/null" >/dev/null; then
                echo "✅ $service: Healthy"
            else
                echo "❌ $service: Unhealthy"
            fi
        done
        
        echo ""
        echo "Deployment Complete!"
        echo "Access URLs:"
        echo "- Main Application: http://www.sophia-intel.ai/"
        echo "- Health Check: http://www.sophia-intel.ai/health"
        echo "- Grafana: http://www.sophia-intel.ai/grafana/"
        echo "- Prometheus: http://www.sophia-intel.ai/prometheus/"
    } > "$REPORT_FILE"
    
    log "✅ Deployment report saved to: $REPORT_FILE"
    cat "$REPORT_FILE"
}

# Main deployment function
main() {
    log "🚀 Starting Sophia AI Production Deployment"
    log "Target Server: $PRODUCTION_SERVER"
    log "Project Directory: $PROJECT_DIR"
    
    check_prerequisites
    test_ssh_connection
    create_production_env
    optimize_dockerfiles
    sync_source_code
    setup_production_environment
    build_and_deploy_services
    verify_deployment
    test_domain_connectivity
    generate_deployment_report
    
    log "🎉 Deployment Complete!"
    log "🌐 Access your application at: http://www.sophia-intel.ai/"
    log "📊 Monitor at: http://www.sophia-intel.ai/grafana/"
}

# Run main function
main "$@"