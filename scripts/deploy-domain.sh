#!/bin/bash

# Sophia AI Intel - Domain Deployment Script
# Deploys www.sophia-intel.ai configuration to Lambda Labs instance

set -e

# Configuration
DOMAIN="www.sophia-intel.ai"
INSTANCE_IP="192.222.51.223"
SSH_USER="ubuntu"
SSH_KEY_PATH="$HOME/.ssh/lambda-labs-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    log_error "SSH key not found at $SSH_KEY_PATH"
    log_info "Please ensure your Lambda Labs SSH key is available"
    exit 1
fi

# Test SSH connection
log_info "Testing SSH connection to $INSTANCE_IP..."
if ! ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH" -o ConnectTimeout=10 "$SSH_USER@$INSTANCE_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    log_error "Cannot connect to Lambda Labs instance at $INSTANCE_IP"
    log_info "Please check:"
    log_info "  1. Instance is running"
    log_info "  2. SSH key is correct"
    log_info "  3. Security group allows SSH access"
    exit 1
fi

log_success "SSH connection established"

# Deploy domain configuration
log_info "Deploying domain configuration..."

ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH" "$SSH_USER@$INSTANCE_IP" << 'EOF'
    set -e

    echo "📂 Updating system and installing required packages..."

    # Update system
    sudo apt-get update

    # Install required packages
    sudo apt-get install -y curl wget git htop nginx certbot python3-certbot-nginx

    # Enable and start nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx

    echo "📂 Setting up Sophia AI Intel repository..."

    # Navigate to project directory
    cd /home/ubuntu
    if [ ! -d "sophia-ai-intel" ]; then
        git clone https://github.com/ai-cherry/sophia-ai-intel.git
    fi
    cd sophia-ai-intel
    git pull origin main

    echo "🔧 Configuring nginx for www.sophia-intel.ai..."

    # Backup current nginx config
    sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

    # Copy new domain configuration
    sudo cp nginx.sophia-intel.ai.conf /etc/nginx/nginx.conf

    # Test nginx configuration
    if sudo nginx -t; then
        echo "✅ Nginx configuration is valid"
    else
        echo "❌ Nginx configuration is invalid"
        exit 1
    fi

    # Reload nginx
    sudo systemctl reload nginx

    echo "🔐 Setting up SSL certificate for www.sophia-intel.ai..."

    # Generate SSL certificate
    sudo certbot --nginx \
        -d www.sophia-intel.ai \
        --non-interactive \
        --agree-tos \
        --email admin@sophia-intel.ai \
        --redirect \
        --hsts \
        --staple-ocsp

    echo "🐳 Starting Sophia AI services..."

    # Start services with docker-compose
    docker-compose down || true
    docker-compose pull
    docker-compose up -d --build

    echo "⏳ Waiting for services to start..."
    sleep 60

    echo "🏥 Running health checks..."

    # Test services
    services=("sophia-dashboard:3000" "sophia-research:8080" "sophia-context:8080" "sophia-github:8080" "sophia-business:8080" "sophia-lambda:8080" "sophia-hubspot:8080" "sophia-agents:8000")
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        if curl -f http://localhost:$port/healthz &>/dev/null; then
            echo "✅ $name is healthy"
        else
            echo "❌ $name is not responding"
        fi
    done

    echo "🎉 Domain deployment completed!"
    echo ""
    echo "🌐 Your Sophia AI platform is now live at:"
    echo "   https://www.sophia-intel.ai"
    echo ""
    echo "🔧 Management commands:"
    echo "   SSH: ssh ubuntu@$(curl -s ifconfig.me)"
    echo "   Logs: docker-compose logs -f"
    echo "   SSL renewal: sudo certbot renew"
EOF

log_success "Domain deployment completed!"

# Test the deployment
log_info "Testing domain endpoints..."

# Test HTTPS endpoint
if curl -f -k https://www.sophia-intel.ai/health 2>/dev/null; then
    log_success "HTTPS endpoint responding"
else
    log_warning "HTTPS endpoint not responding (DNS may still be propagating)"
fi

# Test HTTP redirect
if curl -f -I http://www.sophia-intel.ai 2>/dev/null | grep -q "301 Moved Permanently"; then
    log_success "HTTP to HTTPS redirect working"
else
    log_warning "HTTP to HTTPS redirect not working (DNS may still be propagating)"
fi

log_info ""
log_info "🎉 Sophia AI Intel domain deployment completed!"
log_info ""
log_info "📋 Next steps:"
log_info "  1. Update DNS A record for www.sophia-intel.ai to point to $INSTANCE_IP"
log_info "  2. Wait for DNS propagation (may take 5-30 minutes)"
log_info "  3. Test https://www.sophia-intel.ai in your browser"
log_info "  4. SSL certificates will auto-renew via certbot"
log_info ""
log_info "🔧 For management:"
log_info "  SSH: ssh -i $SSH_KEY_PATH $SSH_USER@$INSTANCE_IP"
log_info "  Logs: docker-compose logs -f"
log_info "  SSL status: sudo certbot certificates"