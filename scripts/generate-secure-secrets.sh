#!/bin/bash

# Sophia AI - Secure Secrets Generation Script
# This script generates cryptographically secure random values for production secrets

set -e

# Configuration
OUTPUT_FILE=".env.production.secure"
TEMPLATE_FILE=".env.production"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to generate a secure random string
generate_secret() {
    local length=$1
    openssl rand -base64 $length | tr -d '\n=' | cut -c1-$length
}

# Function to generate a secure JWT secret
generate_jwt_secret() {
    generate_secret 64
}

# Function to generate a secure API key
generate_api_key() {
    generate_secret 32
}

# Function to generate a secure password
generate_password() {
    generate_secret 24
}

# Function to generate SSH keys
generate_ssh_keys() {
    local key_name=$1
    local key_path="./ssh_keys/${key_name}"

    log_info "Generating SSH key pair: $key_name"

    # Create SSH keys directory
    mkdir -p ./ssh_keys

    # Generate SSH key pair
    ssh-keygen -t ed25519 -f "$key_path" -N "" -C "sophia-ai-production-$key_name" &>/dev/null

    # Read the keys
    local private_key=$(cat "${key_path}")
    local public_key=$(cat "${key_path}.pub")

    log_success "SSH key pair generated: $key_name"

    echo "$private_key"
    echo "$public_key"
}

# Main function
main() {
    log_info "======================================"
    log_info "🔐 Secure Secrets Generation"
    log_info "======================================"
    echo ""

    # Check if template exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "Template file not found: $TEMPLATE_FILE"
        exit 1
    fi

    # Check if secure output already exists
    if [ -f "$OUTPUT_FILE" ]; then
        read -p "Secure environment file already exists. Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled"
            exit 0
        fi
    fi

    log_info "Generating secure secrets..."
    echo ""

    # Generate secrets
    log_info "Generating JWT and API secrets..."
    JWT_SECRET=$(generate_jwt_secret)
    API_SECRET_KEY=$(generate_api_key)
    BACKUP_ENCRYPTION_KEY=$(generate_api_key)

    log_info "Generating database and Redis passwords..."
    REDIS_PASSWORD=$(generate_password)
    GRAFANA_ADMIN_PASSWORD=$(generate_password)

    log_info "Generating SSH keys for Lambda Labs..."
    read LAMBDA_PRIVATE_KEY LAMBDA_PUBLIC_KEY <<< $(generate_ssh_keys "lambda-labs")

    log_info "Generating GitHub SSH key..."
    read GITHUB_PRIVATE_KEY GITHUB_PUBLIC_KEY <<< $(generate_ssh_keys "github-app")

    log_info "Creating secure environment file..."
    echo ""

    # Copy template and replace placeholders
    cp "$TEMPLATE_FILE" "$OUTPUT_FILE"

    # Replace generated secrets
    sed -i.bak "s|<GENERATE_SECURE_JWT_SECRET>|$JWT_SECRET|g" "$OUTPUT_FILE"
    sed -i.bak "s|<GENERATE_SECURE_API_SECRET>|$API_SECRET_KEY|g" "$OUTPUT_FILE"
    sed -i.bak "s|<GENERATE_SECURE_BACKUP_KEY>|$BACKUP_ENCRYPTION_KEY|g" "$OUTPUT_FILE"
    sed -i.bak "s|<YOUR_REDIS_PASSWORD>|$REDIS_PASSWORD|g" "$OUTPUT_FILE"
    sed -i.bak "s|<YOUR_GRAFANA_ADMIN_PASSWORD>|$GRAFANA_ADMIN_PASSWORD|g" "$OUTPUT_FILE"
    sed -i.bak "s|<YOUR_LAMBDA_PRIVATE_SSH_KEY>|$LAMBDA_PRIVATE_KEY|g" "$OUTPUT_FILE"
    sed -i.bak "s|<YOUR_LAMBDA_PUBLIC_SSH_KEY>|$LAMBDA_PUBLIC_KEY|g" "$OUTPUT_FILE"
    sed -i.bak "s|<YOUR_GITHUB_PRIVATE_KEY>|$GITHUB_PRIVATE_KEY|g" "$OUTPUT_FILE"

    # Clean up backup file
    rm -f "${OUTPUT_FILE}.bak"

    echo ""
    log_success "Secure secrets generated successfully!"
    log_success "Secure environment file created: $OUTPUT_FILE"
    echo ""

    log_warning "IMPORTANT SECURITY REMINDERS:"
    echo "  🔴 NEVER commit $OUTPUT_FILE to version control"
    echo "  🔴 Store secrets securely (GitHub Secrets, Pulumi ESC, etc.)"
    echo "  🔴 Rotate secrets regularly (90 days max)"
    echo "  🔴 Use different secrets for each environment"
    echo ""

    log_info "Generated SSH Public Keys (add these to respective services):"
    echo ""
    log_info "Lambda Labs SSH Public Key:"
    echo "$LAMBDA_PUBLIC_KEY"
    echo ""
    log_info "GitHub App SSH Public Key:"
    echo "$GITHUB_PUBLIC_KEY"
    echo ""

    log_info "Next steps:"
    echo "1. Add the SSH public keys to Lambda Labs and GitHub"
    echo "2. Update API keys and connection strings in $OUTPUT_FILE"
    echo "3. Run environment validation: ./scripts/env-production-validation.sh"
    echo "4. Deploy securely using your secret management system"
    echo ""

    return 0
}

# Show usage if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Sophia AI Secure Secrets Generator"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "This script generates cryptographically secure random values"
    echo "for all sensitive configuration in the production environment."
    echo ""
    exit 0
fi

# Run main function
main "$@"