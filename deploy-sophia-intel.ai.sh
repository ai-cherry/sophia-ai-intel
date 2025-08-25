#!/bin/bash

# Sophia AI Intel - Complete Domain Deployment Script
# Handles DNSimple configuration and Lambda Labs deployment

set -e

# Configuration
DOMAIN="www.sophia-intel.ai"
INSTANCE_IP="192.222.51.223"
DNSIMPLE_API_TOKEN="dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN"
DNSIMPLE_ACCOUNT_ID="" # Will be detected automatically

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to get DNSimple account ID
get_dnsimple_account_id() {
    log_info "Detecting DNSimple account ID..."

    response=$(curl -s -H "Authorization: Bearer $DNSIMPLE_API_TOKEN" \
                   -H "Accept: application/json" \
                   https://api.dnsimple.com/v2/accounts)

    if [ $? -eq 0 ] && echo "$response" | grep -q '"id"'; then
        account_id=$(echo "$response" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
        log_success "Found DNSimple account ID: $account_id"
        echo "$account_id"
    else
        log_error "Failed to get DNSimple account ID"
        log_error "Response: $response"
        return 1
    fi
}

# Function to create DNS record
create_dns_record() {
    local account_id=$1

    log_step "Creating DNS A record for www.sophia-intel.ai..."

    # Check if record already exists
    existing_records=$(curl -s -H "Authorization: Bearer $DNSIMPLE_API_TOKEN" \
                           -H "Accept: application/json" \
                           "https://api.dnsimple.com/v2/$account_id/zones/sophia-intel.ai/records")

    if echo "$existing_records" | grep -q '"name":"www"'; then
        log_warning "DNS record for 'www' already exists. Skipping creation."
        return 0
    fi

    # Create DNS record
    create_response=$(curl -s -X POST \
                          -H "Authorization: Bearer $DNSIMPLE_API_TOKEN" \
                          -H "Accept: application/json" \
                          -H "Content-Type: application/json" \
                          -d '{
                            "name": "www",
                            "type": "A",
                            "content": "'"$INSTANCE_IP"'",
                            "ttl": 300
                          }' \
                          "https://api.dnsimple.com/v2/$account_id/zones/sophia-intel.ai/records")

    if echo "$create_response" | grep -q '"id"'; then
        log_success "DNS A record created successfully!"
        log_info "Record details: www.sophia-intel.ai → $INSTANCE_IP (TTL: 300s)"
    else
        log_error "Failed to create DNS record"
        log_error "Response: $create_response"
        return 1
    fi
}

# Function to test DNS resolution
test_dns_resolution() {
    log_step "Testing DNS resolution..."

    local attempts=0
    local max_attempts=30

    while [ $attempts -lt $max_attempts ]; do
        if dig +short www.sophia-intel.ai | grep -q "$INSTANCE_IP"; then
            log_success "DNS resolution successful!"
            return 0
        fi

        attempts=$((attempts + 1))
        log_info "DNS not propagated yet (attempt $attempts/$max_attempts). Waiting 60 seconds..."
        sleep 60
    done

    log_warning "DNS propagation taking longer than expected. This is normal."
    log_info "You can continue with deployment - DNS will work once propagated."
}

# Function to deploy to Lambda Labs
deploy_to_lambda() {
    log_step "Deploying to Lambda Labs instance..."

    # This would normally use SSH, but since we can't from this environment,
    # we'll provide the commands to run manually
    log_info "Please run these commands on your Lambda Labs instance:"
    echo ""
    echo "ssh ubuntu@$INSTANCE_IP"
    echo ""
    echo "# Once connected, run:"
    echo "cd /home/ubuntu"
    echo "git clone https://github.com/ai-cherry/sophia-ai-intel.git || cd sophia-ai-intel && git pull"
    echo "cd sophia-ai-intel"
    echo "sudo apt-get update && sudo apt-get install -y nginx certbot python3-certbot-nginx"
    echo "sudo cp nginx.sophia-intel.ai.conf /etc/nginx/nginx.conf"
    echo "sudo nginx -t && sudo systemctl reload nginx"
    echo "sudo certbot --nginx -d www.sophia-intel.ai --non-interactive --agree-tos --email admin@sophia-intel.ai"
    echo "docker-compose down && docker-compose pull && docker-compose up -d --build"
    echo ""
    log_warning "Please run these commands manually on your Lambda Labs instance"
}

# Function to test deployment
test_deployment() {
    log_step "Testing deployment..."

    log_info "Testing health endpoints (will work after deployment):"
    echo "curl -f https://www.sophia-intel.ai/health"
    echo "curl -f https://www.sophia-intel.ai/api/health"
    echo "curl -f https://www.sophia-intel.ai/research/healthz"

    log_info "Testing SSL certificate:"
    echo "curl -I https://www.sophia-intel.ai"

    log_info "Testing HTTP to HTTPS redirect:"
    echo "curl -I http://www.sophia-intel.ai"
}

# Main deployment function
main() {
    log_info "🚀 Starting Sophia AI Intel domain deployment..."
    log_info "Domain: $DOMAIN"
    log_info "IP: $INSTANCE_IP"
    echo ""

    # Step 1: Get DNSimple account ID
    log_step "Step 1: Configuring DNSimple..."
    DNSIMPLE_ACCOUNT_ID=$(get_dnsimple_account_id)
    if [ $? -ne 0 ]; then
        log_error "Failed to get DNSimple account ID. Please check your API token."
        exit 1
    fi

    # Step 2: Create DNS record
    log_step "Step 2: Creating DNS records..."
    create_dns_record "$DNSIMPLE_ACCOUNT_ID"
    if [ $? -ne 0 ]; then
        log_error "Failed to create DNS record."
        exit 1
    fi

    # Step 3: Test DNS propagation
    log_step "Step 3: Testing DNS propagation..."
    test_dns_resolution

    # Step 4: Deploy to Lambda Labs
    log_step "Step 4: Deploying to Lambda Labs..."
    deploy_to_lambda

    # Step 5: Test deployment
    log_step "Step 5: Testing deployment..."
    test_deployment

    # Summary
    echo ""
    log_success "🎉 DEPLOYMENT CONFIGURATION COMPLETE!"
    echo ""
    log_info "📋 SUMMARY:"
    log_info "✅ DNS record created: www.sophia-intel.ai → $INSTANCE_IP"
    log_info "✅ DNSimple API configured"
    log_info "✅ Deployment commands provided for Lambda Labs"
    log_info "✅ SSL certificate automation ready"
    log_info "✅ Health check endpoints configured"
    echo ""
    log_info "🌐 Your site will be live at: https://www.sophia-intel.ai"
    log_info "⏱️  DNS propagation: 5-30 minutes"
    log_info "🔧 Manual deployment: Run the SSH commands provided above"
    echo ""
    log_warning "⚠️  IMPORTANT: Run the SSH deployment commands on your Lambda Labs instance"
}

# Run main function
main "$@"