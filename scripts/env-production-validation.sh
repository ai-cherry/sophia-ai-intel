#!/bin/bash

# Sophia AI - Production Environment Validation Script
# This script validates all required environment variables for production deployment

set -e

# Configuration
ENV_FILE=".env.production"
REQUIRED_SECRETS_FILE="required-secrets.txt"

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

# Function to check if a variable is set and not empty
check_env_var() {
    local var_name=$1
    local var_value="${!var_name}"

    if [ -z "$var_value" ] || [ "$var_value" = "<YOUR_${var_name}>" ] || [[ "$var_value" == *"<GENERATE_SECURE_"* ]]; then
        log_error "Missing or placeholder value for: $var_name"
        return 1
    else
        log_success "✓ $var_name is configured"
        return 0
    fi
}

# Function to validate URL format
validate_url() {
    local url=$1
    local var_name=$2

    if [[ ! $url =~ ^https?:// ]]; then
        log_error "Invalid URL format for $var_name: $url"
        return 1
    fi

    log_success "✓ $var_name URL format is valid"
    return 0
}

# Function to validate connection string
validate_connection_string() {
    local conn_string=$1
    local var_name=$2

    if [[ ! $conn_string =~ ^postgresql:// ]] && [[ ! $conn_string =~ ^redis:// ]]; then
        log_error "Invalid connection string format for $var_name: $conn_string"
        return 1
    fi

    log_success "✓ $var_name connection string format is valid"
    return 0
}

# Function to validate SSH key format
validate_ssh_key() {
    local ssh_key=$1
    local var_name=$2

    if [[ ! $ssh_key =~ ^-----BEGIN\ (RSA\ )?PRIVATE\ KEY----- ]]; then
        log_error "Invalid SSH private key format for $var_name"
        return 1
    fi

    if [[ ! $ssh_key =~ ^-----END\ (RSA\ )?PRIVATE\ KEY-----$ ]]; then
        log_error "SSH private key missing END marker for $var_name"
        return 1
    fi

    log_success "✓ $var_name SSH key format is valid"
    return 0
}

# Main validation function
main() {
    log_info "======================================"
    log_info "🔍 Production Environment Validation"
    log_info "======================================"
    echo ""

    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi

    log_info "Loading environment variables from $ENV_FILE..."
    export $(grep -v '^#' "$ENV_FILE" | xargs)

    local errors=0
    local warnings=0

    echo ""
    log_info "🔐 Checking API Keys and Secrets..."
    echo ""

    # Critical API Keys (required)
    local critical_vars=(
        "OPENAI_API_KEY"
        "ANTHROPIC_API_KEY"
        "DATABASE_URL"
        "REDIS_URL"
        "QDRANT_URL"
        "QDRANT_API_KEY"
        "LAMBDA_API_KEY"
        "LAMBDA_PRIVATE_SSH_KEY"
        "LAMBDA_PUBLIC_SSH_KEY"
        "GITHUB_APP_ID"
        "GITHUB_PRIVATE_KEY"
        "DNSIMPLE_API_KEY"
        "GRAFANA_ADMIN_PASSWORD"
    )

    for var in "${critical_vars[@]}"; do
        if ! check_env_var "$var"; then
            ((errors++))
        fi
    done

    echo ""
    log_info "🔗 Checking Service Integrations..."
    echo ""

    # Business API Keys (optional but recommended)
    local business_vars=(
        "HUBSPOT_ACCESS_TOKEN"
        "GONG_ACCESS_KEY"
        "GONG_ACCESS_KEY_SECRET"
        "SALESFORCE_CLIENT_ID"
        "SALESFORCE_CLIENT_SECRET"
        "SLACK_BOT_TOKEN"
        "APOLLO_API_KEY"
    )

    for var in "${business_vars[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "<YOUR_${var}>" ]; then
            log_warning "Business integration not configured: $var"
            ((warnings++))
        else
            log_success "✓ $var is configured"
        fi
    done

    echo ""
    log_info "🌐 Checking URLs and Endpoints..."
    echo ""

    # URL validations
    if [ ! -z "$DATABASE_URL" ] && [ "$DATABASE_URL" != "<YOUR_POSTGRESQL_CONNECTION_STRING>" ]; then
        validate_connection_string "$DATABASE_URL" "DATABASE_URL" || ((errors++))
    fi

    if [ ! -z "$REDIS_URL" ] && [ "$REDIS_URL" != "<YOUR_REDIS_CONNECTION_STRING>" ]; then
        validate_connection_string "$REDIS_URL" "REDIS_URL" || ((errors++))
    fi

    if [ ! -z "$QDRANT_URL" ] && [ "$QDRANT_URL" != "<YOUR_QDRANT_URL>" ]; then
        validate_url "$QDRANT_URL" "QDRANT_URL" || ((errors++))
    fi

    echo ""
    log_info "🔑 Checking SSH Keys..."
    echo ""

    # SSH Key validations
    if [ ! -z "$LAMBDA_PRIVATE_SSH_KEY" ] && [ "$LAMBDA_PRIVATE_SSH_KEY" != "<YOUR_LAMBDA_PRIVATE_SSH_KEY>" ]; then
        validate_ssh_key "$LAMBDA_PRIVATE_SSH_KEY" "LAMBDA_PRIVATE_SSH_KEY" || ((errors++))
    fi

    if [ ! -z "$GITHUB_PRIVATE_KEY" ] && [ "$GITHUB_PRIVATE_KEY" != "<YOUR_GITHUB_PRIVATE_KEY>" ]; then
        validate_ssh_key "$GITHUB_PRIVATE_KEY" "GITHUB_PRIVATE_KEY" || ((errors++))
    fi

    echo ""
    log_info "🔧 Checking Infrastructure Configuration..."
    echo ""

    # Infrastructure checks
    if [ "$NODE_ENV" != "production" ]; then
        log_error "NODE_ENV is not set to 'production'"
        ((errors++))
    else
        log_success "✓ NODE_ENV is correctly set to production"
    fi

    if [ "$ENABLE_SSL" != "true" ]; then
        log_warning "SSL is not enabled in production"
        ((warnings++))
    else
        log_success "✓ SSL is enabled"
    fi

    if [ "$ENABLE_MONITORING" != "true" ]; then
        log_warning "Monitoring is not enabled"
        ((warnings++))
    else
        log_success "✓ Monitoring is enabled"
    fi

    echo ""
    log_info "📊 Validation Summary..."
    echo ""

    if [ $errors -gt 0 ]; then
        log_error "Found $errors critical errors that must be fixed before deployment"
        echo ""
        log_info "Next steps:"
        echo "1. Update $ENV_FILE with actual values"
        echo "2. Use secure secret management (GitHub Secrets, Pulumi ESC, etc.)"
        echo "3. Run this validation script again"
        echo ""
        exit 1
    fi

    if [ $warnings -gt 0 ]; then
        log_warning "Found $warnings warnings - deployment will work but some features may be disabled"
        echo ""
    fi

    log_success "Environment validation completed successfully!"
    log_success "Ready for production deployment"
    echo ""

    log_info "🚀 Deployment Readiness Checklist:"
    echo "  ☐ All secrets configured securely"
    echo "  ☐ Database connectivity tested"
    echo "  ☐ AI services validated"
    echo "  ☐ Lambda Labs SSH access confirmed"
    echo "  ☐ Domain DNS configured"
    echo "  ☐ SSL certificates ready"
    echo "  ☐ Monitoring stack operational"
    echo "  ☐ Backup strategy implemented"
    echo ""

    return 0
}

# Run main function
main "$@"