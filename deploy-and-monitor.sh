#!/bin/bash

# Sophia AI Intel - Complete Deployment and Monitoring Script
# Deploys to Lambda Labs and monitors all services

set -e

# Configuration
INSTANCE_IP="192.222.51.223"
SSH_USER="ubuntu"
DOMAIN="www.sophia-intel.ai"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to test SSH connection
test_ssh() {
    log_step "Testing SSH connection to Lambda Labs..."
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$INSTANCE_IP" "echo 'SSH connection successful'" 2>/dev/null; then
        log_success "SSH connection established"
        return 0
    else
        log_error "Cannot connect to Lambda Labs instance"
        log_info "Please ensure:"
        log_info "  1. Instance is running"
        log_info "  2. SSH key is correct"
        log_info "  3. Security group allows SSH access"
        return 1
    fi
}

# Function to deploy services
deploy_services() {
    log_step "Deploying Sophia AI Intel services..."

    ssh -o StrictHostKeyChecking=no "$SSH_USER@$INSTANCE_IP" << 'EOF'
        set -e

        echo "📂 Setting up deployment directory..."
        cd /home/ubuntu

        # Clone or update repository
        if [ -d "sophia-ai-intel" ]; then
            cd sophia-ai-intel
            git pull origin main
        else
            git clone https://github.com/ai-cherry/sophia-ai-intel.git
            cd sophia-ai-intel
        fi

        echo "📦 Installing system dependencies..."
        sudo apt-get update
        sudo apt-get install -y nginx certbot python3-certbot-nginx curl wget htop

        echo "🔧 Configuring nginx for www.sophia-intel.ai..."
        sudo cp nginx.sophia-intel.ai.conf /etc/nginx/nginx.conf

        # Test nginx configuration
        if sudo nginx -t; then
            echo "✅ Nginx configuration is valid"
        else
            echo "❌ Nginx configuration is invalid"
            exit 1
        fi

        # Reload nginx
        sudo systemctl enable nginx
        sudo systemctl reload nginx

        echo "🔐 Setting up SSL certificate..."
        # Generate SSL certificate (will work after DNS propagates)
        sudo certbot --nginx \
          -d www.sophia-intel.ai \
          --non-interactive \
          --agree-tos \
          --email admin@sophia-intel.ai || echo "SSL certificate setup (will complete after DNS propagation)"

        echo "🐳 Deploying Docker services..."
        docker-compose down || true
        docker-compose pull
        docker-compose up -d --build

        echo "⏳ Waiting for services to start..."
        sleep 60

        echo "✅ Deployment completed!"
EOF

    log_success "Services deployed successfully"
}

# Function to monitor services
monitor_services() {
    log_step "Monitoring deployed services..."

    while true; do
        clear
        echo "🔍 SOPHIA AI INTEL - SERVICE MONITORING"
        echo "🌐 Domain: $DOMAIN"
        echo "🖥️  Instance: $INSTANCE_IP"
        echo "⏰ $(date)"
        echo "========================================"

        # Test SSH and get service status
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$SSH_USER@$INSTANCE_IP" << 'EOF' 2>/dev/null; then
            echo "🐳 DOCKER CONTAINERS:"
            docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

            echo ""
            echo "📊 SERVICE HEALTH CHECKS:"

            # Test each service
            services=("sophia-dashboard:3000" "sophia-research:8080" "sophia-context:8080" "sophia-github:8080" "sophia-business:8080" "sophia-lambda:8080" "sophia-hubspot:8080" "sophia-agents:8000")
            for service in "${services[@]}"; do
                name=$(echo $service | cut -d: -f1)
                port=$(echo $service | cut -d: -f2)
                if curl -f --max-time 5 http://localhost:$port/healthz &>/dev/null; then
                    echo -e "  ✅ $name (port $port)"
                else
                    echo -e "  ❌ $name (port $port)"
                fi
            done

            echo ""
            echo "🌐 DOMAIN ENDPOINTS:"
            if curl -f --max-time 10 https://www.sophia-intel.ai/health &>/dev/null; then
                echo "  ✅ https://www.sophia-intel.ai/health"
            else
                echo "  ❌ https://www.sophia-intel.ai/health (DNS/SSL may still propagating)"
            fi

            if curl -f --max-time 10 https://www.sophia-intel.ai/api/health &>/dev/null; then
                echo "  ✅ https://www.sophia-intel.ai/api/health"
            else
                echo "  ❌ https://www.sophia-intel.ai/api/health"
            fi

            echo ""
            echo "💾 SYSTEM RESOURCES:"
            echo "  CPU: $(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1 | xargs)%"
            echo "  Memory: $(free -h | awk 'NR==2{printf "%.1fG/%.1fG", $3/1024, $2/1024}')"
            echo "  Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5" used)"}')"

            echo ""
            echo "🔐 SSL CERTIFICATE STATUS:"
            if sudo certbot certificates 2>/dev/null | grep -q "www.sophia-intel.ai"; then
                echo "  ✅ SSL certificate active"
                sudo certbot certificates 2>/dev/null | grep -A5 "www.sophia-intel.ai" | grep "Expiry Date" | sed 's/.*Expiry Date: /  📅 Expires: /'
            else
                echo "  ⏳ SSL certificate pending (DNS propagation)"
            fi

        else
            echo "❌ Cannot connect to Lambda Labs instance"
            echo "   Please check instance status and SSH connection"
        fi

        echo ""
        echo "========================================"
        echo "🔄 Refreshing in 30 seconds... (Ctrl+C to stop)"
        sleep 30
    done
}

# Function to show deployment summary
show_summary() {
    echo ""
    log_success "🎉 DEPLOYMENT SUMMARY"
    echo ""
    log_info "✅ Services Deployed:"
    echo "   • 8 microservices (dashboard, research, context, github, business, lambda, hubspot, agents)"
    echo "   • nginx reverse proxy with SSL"
    echo "   • Docker Compose orchestration"
    echo ""
    log_info "🌐 Production URLs:"
    echo "   • https://www.sophia-intel.ai (Main Dashboard)"
    echo "   • https://www.sophia-intel.ai/api/ (API Gateway)"
    echo "   • https://www.sophia-intel.ai/research/ (Research API)"
    echo "   • https://www.sophia-intel.ai/context/ (Context API)"
    echo "   • https://www.sophia-intel.ai/agents/ (Agent Swarm)"
    echo ""
    log_info "🔧 Management:"
    echo "   • SSH: ssh ubuntu@$INSTANCE_IP"
    echo "   • Logs: docker-compose logs -f"
    echo "   • Restart: docker-compose restart"
    echo "   • SSL renewal: sudo certbot renew"
    echo ""
    log_info "📊 Monitoring:"
    echo "   • Health: https://www.sophia-intel.ai/health"
    echo "   • Resources: htop, docker stats"
    echo "   • SSL status: sudo certbot certificates"
}

# Main function
main() {
    log_info "🚀 Starting Sophia AI Intel deployment and monitoring..."
    log_info "Domain: $DOMAIN"
    log_info "Instance: $INSTANCE_IP"
    echo ""

    # Test SSH connection
    if ! test_ssh; then
        log_error "SSH connection failed. Please check your connection and try again."
        exit 1
    fi

    # Deploy services
    deploy_services

    # Show summary
    show_summary

    # Start monitoring
    log_info "Starting continuous monitoring... (Ctrl+C to stop)"
    sleep 3
    monitor_services
}

# Run main function
main "$@"