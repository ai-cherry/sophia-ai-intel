#!/bin/bash

# ===========================================
# Local SSL Certificate Generator
# ===========================================
# Generates self-signed SSL certificates for local development
# Supports multiple domains and services with proper SAN configuration

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSL_DIR="$(pwd)/ssl/local"
CERTS_DIR="$(pwd)/certs"
NGINX_SSL_DIR="$(pwd)/ssl"
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORGANIZATION="Sophia AI Development"
ORGANIZATIONAL_UNIT="Local Development"
EMAIL="dev@sophia.local"

# Service domains for local development
DOMAINS=(
    "localhost"
    "sophia.local"
    "api.sophia.local"
    "agno-coordinator.sophia.local"
    "mcp-agents.sophia.local"
    "mcp-context.sophia.local"
    "mcp-github.sophia.local"
    "mcp-hubspot.sophia.local"
    "mcp-lambda.sophia.local"
    "mcp-research.sophia.local"
    "mcp-business.sophia.local"
    "agno-teams.sophia.local"
    "agno-wrappers.sophia.local"
    "mcp-apollo.sophia.local"
    "mcp-gong.sophia.local"
    "mcp-salesforce.sophia.local"
    "mcp-slack.sophia.local"
    "portkey-llm.sophia.local"
    "agents-swarm.sophia.local"
    "orchestrator.sophia.local"
    "grafana.sophia.local"
    "prometheus.sophia.local"
    "adminer.sophia.local"
    "redis-commander.sophia.local"
    "jaeger.sophia.local"
    "127.0.0.1"
    "0.0.0.0"
)

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Sophia AI - Local SSL Certificate Generator${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

print_step() {
    echo -e "${YELLOW}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Create directories
create_directories() {
    print_step "Creating SSL directories..."
    mkdir -p "$SSL_DIR"
    mkdir -p "$CERTS_DIR"
    mkdir -p "$NGINX_SSL_DIR"
    print_success "SSL directories created"
}

# Generate Root CA
generate_root_ca() {
    print_step "Generating Root Certificate Authority..."
    
    # Generate CA private key
    openssl genrsa -out "$SSL_DIR/ca-key.pem" 4096
    
    # Generate CA certificate
    openssl req -new -x509 -days 365 -key "$SSL_DIR/ca-key.pem" -sha256 -out "$SSL_DIR/ca-cert.pem" -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/OU=$ORGANIZATIONAL_UNIT CA/CN=Sophia AI Local CA/emailAddress=$EMAIL"
    
    print_success "Root CA generated"
}

# Generate server certificate with SAN
generate_server_cert() {
    print_step "Generating server certificate with SAN extensions..."
    
    # Generate server private key
    openssl genrsa -out "$SSL_DIR/server-key.pem" 4096
    
    # Create SAN configuration
    cat > "$SSL_DIR/server.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $ORGANIZATIONAL_UNIT
CN = sophia.local
emailAddress = $EMAIL

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
EOF
    
    # Add all domains to SAN
    local counter=1
    for domain in "${DOMAINS[@]}"; do
        echo "DNS.$counter = $domain" >> "$SSL_DIR/server.conf"
        ((counter++))
    done
    
    # Add IP addresses
    echo "IP.1 = 127.0.0.1" >> "$SSL_DIR/server.conf"
    echo "IP.2 = ::1" >> "$SSL_DIR/server.conf"
    
    # Generate certificate signing request
    openssl req -new -key "$SSL_DIR/server-key.pem" -out "$SSL_DIR/server.csr" -config "$SSL_DIR/server.conf"
    
    # Generate server certificate signed by CA
    openssl x509 -req -in "$SSL_DIR/server.csr" -CA "$SSL_DIR/ca-cert.pem" -CAkey "$SSL_DIR/ca-key.pem" -CAcreateserial -out "$SSL_DIR/server-cert.pem" -days 365 -extensions v3_req -extfile "$SSL_DIR/server.conf"
    
    print_success "Server certificate with SAN extensions generated"
}

# Generate service-specific certificates
generate_service_certificates() {
    print_step "Generating service-specific certificates..."
    
    local services=(
        "agno-coordinator:8080"
        "mcp-agents:8000"
        "mcp-context:8081"
        "mcp-github:8082"
        "mcp-hubspot:8083"
        "mcp-lambda:8084"
        "mcp-research:8085"
        "mcp-business:8086"
        "agno-teams:8087"
        "orchestrator:8088"
        "agno-wrappers:8089"
        "mcp-apollo:8090"
        "mcp-gong:8091"
        "mcp-salesforce:8092"
        "mcp-slack:8093"
        "portkey-llm:8007"
        "agents-swarm:8008"
        "grafana:3000"
        "prometheus:9090"
    )
    
    for service_port in "${services[@]}"; do
        local service=$(echo "$service_port" | cut -d: -f1)
        local port=$(echo "$service_port" | cut -d: -f2)
        
        print_info "Generating certificate for $service..."
        
        # Generate service private key
        openssl genrsa -out "$SSL_DIR/$service-key.pem" 2048
        
        # Create service configuration
        cat > "$SSL_DIR/$service.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $ORGANIZATIONAL_UNIT
CN = $service.sophia.local
emailAddress = $EMAIL

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $service.sophia.local
DNS.2 = $service
DNS.3 = localhost
DNS.4 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
        
        # Generate CSR
        openssl req -new -key "$SSL_DIR/$service-key.pem" -out "$SSL_DIR/$service.csr" -config "$SSL_DIR/$service.conf"
        
        # Generate certificate
        openssl x509 -req -in "$SSL_DIR/$service.csr" -CA "$SSL_DIR/ca-cert.pem" -CAkey "$SSL_DIR/ca-key.pem" -CAcreateserial -out "$SSL_DIR/$service-cert.pem" -days 365 -extensions v3_req -extfile "$SSL_DIR/$service.conf"
        
        # Clean up CSR
        rm "$SSL_DIR/$service.csr" "$SSL_DIR/$service.conf"
    done
    
    print_success "Service-specific certificates generated"
}

# Copy certificates to nginx directory
copy_to_nginx() {
    print_step "Copying certificates to nginx directory..."
    
    cp "$SSL_DIR/server-cert.pem" "$NGINX_SSL_DIR/sophia.crt"
    cp "$SSL_DIR/server-key.pem" "$NGINX_SSL_DIR/sophia.key"
    cp "$SSL_DIR/ca-cert.pem" "$NGINX_SSL_DIR/ca.crt"
    
    print_success "Certificates copied to nginx directory"
}

# Create certificate bundle
create_certificate_bundle() {
    print_step "Creating certificate bundle..."
    
    # Create full chain certificate
    cat "$SSL_DIR/server-cert.pem" "$SSL_DIR/ca-cert.pem" > "$SSL_DIR/fullchain.pem"
    cat "$SSL_DIR/server-cert.pem" "$SSL_DIR/ca-cert.pem" > "$NGINX_SSL_DIR/fullchain.pem"
    
    # Create combined cert and key for some applications
    cat "$SSL_DIR/server-cert.pem" "$SSL_DIR/server-key.pem" > "$SSL_DIR/combined.pem"
    
    print_success "Certificate bundle created"
}

# Generate DH parameters for nginx
generate_dh_params() {
    print_step "Generating Diffie-Hellman parameters (this may take a while)..."
    
    if [[ ! -f "$SSL_DIR/dhparam.pem" ]]; then
        openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048
        cp "$SSL_DIR/dhparam.pem" "$NGINX_SSL_DIR/dhparam.pem"
        print_success "DH parameters generated"
    else
        print_info "DH parameters already exist, skipping..."
    fi
}

# Create certificate info file
create_cert_info() {
    print_step "Creating certificate information file..."
    
    cat > "$SSL_DIR/cert-info.txt" << EOF
# Sophia AI Local Development SSL Certificates
# Generated: $(date)

## Root CA Certificate
- Location: $SSL_DIR/ca-cert.pem
- Validity: 365 days from generation
- Usage: Import this into your browser/system trust store

## Server Certificate
- Location: $SSL_DIR/server-cert.pem
- Private Key: $SSL_DIR/server-key.pem
- SAN Domains: All Sophia services and localhost variants
- Validity: 365 days from generation

## Service Certificates
Individual certificates generated for each microservice in $SSL_DIR/

## Browser Installation Instructions

### Chrome/Chromium (macOS):
1. Open Chrome Settings > Privacy and Security > Security
2. Manage Certificates > Import
3. Select '$SSL_DIR/ca-cert.pem'
4. Choose "System" keychain and "Always Trust"

### Firefox:
1. Open Firefox Settings > Privacy & Security
2. View Certificates > Import
3. Select '$SSL_DIR/ca-cert.pem'
4. Check "Trust this CA to identify websites"

### Safari (macOS):
1. Double-click '$SSL_DIR/ca-cert.pem'
2. Add to System keychain
3. Open Keychain Access, find "Sophia AI Local CA"
4. Double-click > Trust > When using this certificate: Always Trust

## Testing
curl -k https://sophia.local/
curl --cacert $SSL_DIR/ca-cert.pem https://sophia.local/

## Domains Configured
$(printf '%s\n' "${DOMAINS[@]}" | sed 's/^/- /')

EOF
    
    print_success "Certificate information file created"
}

# Set proper permissions
set_permissions() {
    print_step "Setting secure permissions..."
    
    # Secure private keys
    find "$SSL_DIR" -name "*-key.pem" -exec chmod 600 {} \;
    find "$NGINX_SSL_DIR" -name "*.key" -exec chmod 600 {} \;
    
    # Public certificates can be readable
    find "$SSL_DIR" -name "*-cert.pem" -exec chmod 644 {} \;
    find "$SSL_DIR" -name "*.crt" -exec chmod 644 {} \;
    find "$NGINX_SSL_DIR" -name "*.crt" -exec chmod 644 {} \;
    
    print_success "Permissions set securely"
}

# Validate certificates
validate_certificates() {
    print_step "Validating generated certificates..."
    
    # Validate CA certificate
    if openssl x509 -in "$SSL_DIR/ca-cert.pem" -text -noout > /dev/null 2>&1; then
        print_success "CA certificate is valid"
    else
        print_error "CA certificate validation failed"
        exit 1
    fi
    
    # Validate server certificate
    if openssl x509 -in "$SSL_DIR/server-cert.pem" -text -noout > /dev/null 2>&1; then
        print_success "Server certificate is valid"
    else
        print_error "Server certificate validation failed"
        exit 1
    fi
    
    # Verify certificate chain
    if openssl verify -CAfile "$SSL_DIR/ca-cert.pem" "$SSL_DIR/server-cert.pem" > /dev/null 2>&1; then
        print_success "Certificate chain verification passed"
    else
        print_error "Certificate chain verification failed"
        exit 1
    fi
    
    print_success "All certificates validated successfully"
}

# Display certificate details
display_certificate_details() {
    print_step "Certificate Details:"
    echo
    
    print_info "CA Certificate Subject:"
    openssl x509 -in "$SSL_DIR/ca-cert.pem" -noout -subject | sed 's/subject=/  /'
    
    print_info "Server Certificate Subject:"
    openssl x509 -in "$SSL_DIR/server-cert.pem" -noout -subject | sed 's/subject=/  /'
    
    print_info "Server Certificate SAN:"
    openssl x509 -in "$SSL_DIR/server-cert.pem" -noout -text | grep -A 10 "Subject Alternative Name" | sed 's/^/  /'
    
    print_info "Certificate Validity:"
    echo "  CA Valid Until: $(openssl x509 -in "$SSL_DIR/ca-cert.pem" -noout -enddate | cut -d= -f2)"
    echo "  Server Valid Until: $(openssl x509 -in "$SSL_DIR/server-cert.pem" -noout -enddate | cut -d= -f2)"
    echo
}

# Clean old certificates
clean_old_certificates() {
    if [[ -d "$SSL_DIR" ]] && [[ "$1" == "--clean" ]]; then
        print_step "Cleaning old certificates..."
        rm -rf "$SSL_DIR"/*
        print_success "Old certificates removed"
    fi
}

# Main execution
main() {
    print_header
    
    # Handle clean flag
    if [[ "${1:-}" == "--clean" ]]; then
        clean_old_certificates "--clean"
    fi
    
    # Check for openssl
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL is required but not installed"
        exit 1
    fi
    
    create_directories
    generate_root_ca
    generate_server_cert
    generate_service_certificates
    copy_to_nginx
    create_certificate_bundle
    generate_dh_params
    create_cert_info
    set_permissions
    validate_certificates
    display_certificate_details
    
    print_success "SSL certificate generation completed successfully!"
    echo
    print_info "Next steps:"
    echo "  1. Import the CA certificate into your browser trust store"
    echo "  2. Add '127.0.0.1 sophia.local' to your /etc/hosts file"
    echo "  3. Add domain mappings for all services to /etc/hosts"
    echo "  4. Restart nginx to use the new certificates"
    echo "  5. Test with: curl --cacert $SSL_DIR/ca-cert.pem https://sophia.local/"
    echo
    print_info "Certificate information saved to: $SSL_DIR/cert-info.txt"
    echo
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi