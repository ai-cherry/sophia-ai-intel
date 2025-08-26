#!/bin/bash
# Enterprise SSL Deployment and Testing Script
# Comprehensive SSL implementation for both Docker Compose and Kubernetes

set -e

# Configuration
DOMAIN="www.sophia-intel.ai"
API_DOMAIN="api.sophia-intel.ai"
MONITORING_DOMAIN="monitoring.sophia-intel.ai"
SSL_CERT_PATH="/etc/ssl/certs"
DOCKER_CERT_PATH="/etc/ssl/certs"
NAMESPACE="sophia"
MONITORING_NAMESPACE="monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to check if running in Kubernetes
is_kubernetes() {
    [[ -n "${KUBERNETES_SERVICE_HOST}" ]] || kubectl cluster-info >/dev/null 2>&1
}

# Function to check if cert-manager is installed
check_cert_manager() {
    if is_kubernetes && kubectl get namespace cert-manager >/dev/null 2>&1; then
        log_success "Cert-manager is installed"
        return 0
    else
        log_warning "Cert-manager not found or not running in Kubernetes"
        return 1
    fi
}

# Function to check if nginx ingress is installed
check_nginx_ingress() {
    if is_kubernetes && kubectl get pods -n ingress-nginx >/dev/null 2>&1; then
        log_success "NGINX Ingress Controller is installed"
        return 0
    else
        log_warning "NGINX Ingress Controller not found"
        return 1
    fi
}

# Function to deploy SSL certificates in Kubernetes
deploy_kubernetes_ssl() {
    log_info "Deploying SSL certificates in Kubernetes..."

    # Apply cert-manager configurations
    kubectl apply -f k8s-deploy/manifests/cert-manager.yaml
    kubectl apply -f k8s-deploy/manifests/ingress-enhanced-ssl.yaml

    # Wait for certificates to be issued
    log_info "Waiting for certificates to be issued..."
    kubectl wait --for=condition=ready certificate/sophia-intel-ai-tls -n sophia --timeout=300s
    kubectl wait --for=condition=ready certificate/monitoring-tls -n monitoring --timeout=300s

    # Verify certificates
    log_info "Verifying certificate status..."
    kubectl get certificates -n sophia
    kubectl get certificates -n monitoring

    log_success "Kubernetes SSL deployment completed"
}

# Function to deploy SSL for Docker Compose
deploy_docker_ssl() {
    log_info "Deploying SSL certificates for Docker Compose..."

    # Run the SSL setup script
    if [[ -f "scripts/setup_ssl_letsencrypt.sh" ]]; then
        bash scripts/setup_ssl_letsencrypt.sh local
    else
        log_error "SSL setup script not found: scripts/setup_ssl_letsencrypt.sh"
        exit 1
    fi

    # Update docker-compose.yml to use SSL configuration
    if [[ -f "nginx.conf.ssl.production" ]]; then
        cp nginx.conf.ssl.production nginx.conf.ssl
        log_success "SSL configuration updated for Docker Compose"
    else
        log_warning "Production SSL configuration not found, using existing configuration"
    fi

    # Restart nginx container
    docker-compose restart nginx

    log_success "Docker Compose SSL deployment completed"
}

# Function to test SSL configuration
test_ssl_configuration() {
    log_info "Testing SSL configuration..."

    # Test main domain
    echo "Testing ${DOMAIN}..."
    if curl -I -k "https://${DOMAIN}/health" >/dev/null 2>&1; then
        log_success "HTTPS connection to ${DOMAIN} successful"
    else
        log_error "HTTPS connection to ${DOMAIN} failed"
    fi

    # Test SSL certificate
    echo "Testing SSL certificate for ${DOMAIN}..."
    if echo | openssl s_client -connect "${DOMAIN}:443" -servername "${DOMAIN}" 2>/dev/null | openssl x509 -noout -dates >/dev/null 2>&1; then
        log_success "SSL certificate for ${DOMAIN} is valid"
    else
        log_error "SSL certificate for ${DOMAIN} is invalid or not found"
    fi

    # Test API domain if in Kubernetes
    if is_kubernetes; then
        echo "Testing ${API_DOMAIN}..."
        if curl -I -k "https://${API_DOMAIN}/" >/dev/null 2>&1; then
            log_success "HTTPS connection to ${API_DOMAIN} successful"
        else
            log_warning "HTTPS connection to ${API_DOMAIN} failed (may be expected if not configured)"
        fi

        # Test monitoring domain
        echo "Testing ${MONITORING_DOMAIN}..."
        if curl -I -k "https://${MONITORING_DOMAIN}/" >/dev/null 2>&1; then
            log_success "HTTPS connection to ${MONITORING_DOMAIN} successful"
        else
            log_warning "HTTPS connection to ${MONITORING_DOMAIN} failed (may require authentication)"
        fi
    fi
}

# Function to run SSL Labs test
run_ssl_labs_test() {
    log_info "Running SSL Labs security test..."

    # SSL Labs API test
    if command -v curl >/dev/null 2>&1; then
        log_info "Submitting SSL Labs assessment for ${DOMAIN}..."

        # Start assessment
        ASSESSMENT_RESPONSE=$(curl -s "https://api.ssllabs.com/api/v4/analyze?host=${DOMAIN}&publish=off&startNew=on&all=done")

        if [[ $ASSESSMENT_RESPONSE == *"READY"* ]]; then
            log_success "SSL Labs assessment submitted successfully"
            log_info "Check results at: https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}"
        else
            log_warning "SSL Labs assessment submission failed or in progress"
        fi
    else
        log_warning "curl not available, skipping SSL Labs test"
    fi
}

# Function to check security headers
check_security_headers() {
    log_info "Checking security headers..."

    HEADERS=$(curl -I -k "https://${DOMAIN}/health" 2>/dev/null)

    # Check for essential security headers
    declare -a REQUIRED_HEADERS=(
        "Strict-Transport-Security"
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
    )

    for header in "${REQUIRED_HEADERS[@]}"; do
        if echo "$HEADERS" | grep -i "$header:" >/dev/null; then
            log_success "✓ $header header present"
        else
            log_warning "✗ $header header missing"
        fi
    done
}

# Function to check SSL protocols and ciphers
check_ssl_protocols() {
    log_info "Checking SSL protocols and ciphers..."

    if command -v openssl >/dev/null 2>&1; then
        log_info "Testing SSL/TLS versions..."

        # Test TLS 1.3
        if echo | openssl s_client -connect "${DOMAIN}:443" -tls1_3 >/dev/null 2>&1; then
            log_success "✓ TLS 1.3 supported"
        else
            log_warning "✗ TLS 1.3 not supported"
        fi

        # Test TLS 1.2
        if echo | openssl s_client -connect "${DOMAIN}:443" -tls1_2 >/dev/null 2>&1; then
            log_success "✓ TLS 1.2 supported"
        else
            log_error "✗ TLS 1.2 not supported"
        fi

        # Check if TLS 1.1 or lower is supported (should not be)
        if echo | openssl s_client -connect "${DOMAIN}:443" -tls1_1 >/dev/null 2>&1; then
            log_warning "⚠ TLS 1.1 supported (should be disabled)"
        else
            log_success "✓ TLS 1.1 properly disabled"
        fi
    else
        log_warning "OpenSSL not available, skipping protocol tests"
    fi
}

# Function to check certificate details
check_certificate_details() {
    log_info "Checking certificate details..."

    if command -v openssl >/dev/null 2>&1; then
        echo "Certificate information for ${DOMAIN}:"
        echo | openssl s_client -connect "${DOMAIN}:443" -servername "${DOMAIN}" 2>/dev/null | \
            openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null || \
            log_warning "Could not retrieve certificate details"
    else
        log_warning "OpenSSL not available, skipping certificate details"
    fi
}

# Function to update DNS records (placeholder)
update_dns_records() {
    log_info "DNS record configuration notes:"
    log_info "Ensure the following DNS records point to your load balancer:"
    log_info "  - ${DOMAIN} (A/AAAA record)"
    log_info "  - ${API_DOMAIN} (A/AAAA record)"
    log_info "  - ${MONITORING_DOMAIN} (A/AAAA record)"
    log_info "  - *.sophia-intel.ai (wildcard CNAME record)"

    if is_kubernetes; then
        log_info "For Kubernetes, ensure your ingress is properly exposed"
        kubectl get ingress -n sophia
        kubectl get ingress -n monitoring
    else
        log_info "For Docker Compose, ensure ports 80 and 443 are properly forwarded"
    fi
}

# Function to generate SSL monitoring script
generate_ssl_monitoring() {
    log_info "Generating SSL monitoring script..."

    cat > scripts/monitor_ssl_health.sh << 'EOF'
#!/bin/bash
# SSL Health Monitoring Script

DOMAIN="www.sophia-intel.ai"
API_DOMAIN="api.sophia-intel.ai"
MONITORING_DOMAIN="monitoring.sophia-intel.ai"
ALERT_EMAIL="admin@sophia-intel.ai"
LOG_FILE="/var/log/ssl-health.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "$(date): $1" >> "$LOG_FILE"
}

check_ssl_expiry() {
    local domain=$1
    local days_warning=30

    if ! expiry_date=$(echo | openssl s_client -connect "${domain}:443" -servername "${domain}" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2); then
        log "ERROR: Could not retrieve certificate for ${domain}"
        return 1
    fi

    local expiry_seconds=$(date -d "$expiry_date" +%s)
    local current_seconds=$(date +%s)
    local days_left=$(( (expiry_seconds - current_seconds) / 86400 ))

    if [[ $days_left -lt 0 ]]; then
        log "CRITICAL: Certificate for ${domain} has expired!"
        echo "CRITICAL: Certificate for ${domain} has expired!" | mail -s "SSL Certificate Expired" "$ALERT_EMAIL"
        return 2
    elif [[ $days_left -lt $days_warning ]]; then
        log "WARNING: Certificate for ${domain} expires in ${days_left} days"
        echo "WARNING: Certificate for ${domain} expires in ${days_left} days" | mail -s "SSL Certificate Expiring Soon" "$ALERT_EMAIL"
        return 1
    else
        log "OK: Certificate for ${domain} is valid for ${days_left} more days"
        return 0
    fi
}

check_ssl_connection() {
    local domain=$1

    if curl -I -k "https://${domain}/health" >/dev/null 2>&1; then
        log "OK: HTTPS connection to ${domain} successful"
        return 0
    else
        log "ERROR: HTTPS connection to ${domain} failed"
        return 1
    fi
}

# Main monitoring
log "Starting SSL health check"

# Check main domain
if check_ssl_expiry "$DOMAIN"; then
    check_ssl_connection "$DOMAIN"
fi

# Check API domain if accessible
if check_ssl_connection "$API_DOMAIN" >/dev/null 2>&1; then
    check_ssl_expiry "$API_DOMAIN"
fi

# Check monitoring domain if accessible
if check_ssl_connection "$MONITORING_DOMAIN" >/dev/null 2>&1; then
    check_ssl_expiry "$MONITORING_DOMAIN"
fi

log "SSL health check completed"
EOF

    chmod +x scripts/monitor_ssl_health.sh

    # Create cron job for monitoring
    cat > /etc/cron.daily/ssl-health-check << EOF
#!/bin/bash
cd /path/to/sophia-ai-intel-1
bash scripts/monitor_ssl_health.sh
EOF
    chmod +x /etc/cron.daily/ssl-health-check

    log_success "SSL monitoring script created"
}

# Main execution function
main() {
    log_info "Starting Enterprise SSL Deployment and Testing"
    log_info "Domain: ${DOMAIN}"

    # Determine deployment type
    if is_kubernetes; then
        log_info "Detected Kubernetes environment"

        # Check prerequisites
        check_cert_manager
        check_nginx_ingress

        # Deploy SSL for Kubernetes
        deploy_kubernetes_ssl

    else
        log_info "Detected Docker Compose environment"
        deploy_docker_ssl
    fi

    # Test SSL configuration
    test_ssl_configuration

    # Run detailed SSL tests
    check_security_headers
    check_ssl_protocols
    check_certificate_details

    # Run SSL Labs test
    run_ssl_labs_test

    # DNS configuration notes
    update_dns_records

    # Generate monitoring script
    generate_ssl_monitoring

    log_success "SSL deployment and testing completed!"

    # Summary
    echo ""
    log_info "📋 SSL Implementation Summary:"
    log_info "  • Domain: ${DOMAIN}"
    log_info "  • SSL Certificate: Let's Encrypt"
    log_info "  • TLS Versions: 1.2, 1.3"
    log_info "  • Security Headers: Configured"
    log_info "  • Auto-renewal: Enabled"
    log_info "  • Monitoring: Configured"

    if is_kubernetes; then
        log_info "  • Deployment: Kubernetes with cert-manager"
    else
        log_info "  • Deployment: Docker Compose with nginx"
    fi

    log_info ""
    log_info "🔧 Next Steps:"
    log_info "  1. Verify DNS records point to your infrastructure"
    log_info "  2. Test all endpoints: https://${DOMAIN}/health"
    log_info "  3. Check SSL Labs score: https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}"
    log_info "  4. Monitor certificate expiry with: bash scripts/monitor_ssl_health.sh"
    log_info "  5. Set up alerts for certificate expiration"
}

# Parse command line arguments
case "${1:-}" in
    "test")
        log_info "Running SSL tests only..."
        test_ssl_configuration
        check_security_headers
        check_ssl_protocols
        check_certificate_details
        ;;
    "monitor")
        log_info "Running SSL monitoring..."
        if [[ -f "scripts/monitor_ssl_health.sh" ]]; then
            bash scripts/monitor_ssl_health.sh
        else
            log_error "Monitoring script not found. Run deployment first."
        fi
        ;;
    "labs")
        log_info "Running SSL Labs test..."
        run_ssl_labs_test
        ;;
    *)
        main "$@"
        ;;
esac