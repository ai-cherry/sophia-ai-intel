#!/bin/bash

# Sophia AI - Create all Kubernetes secrets from .env files
# This script reads environment variables and creates K8s secrets

set -e

echo "======================================"
echo "🔐 Creating Kubernetes Secrets"
echo "======================================"
echo ""

# Configuration
NAMESPACE="sophia"

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

# Function to check if secret exists
secret_exists() {
    kubectl get secret "$1" -n "$NAMESPACE" &> /dev/null
}

# Function to load environment variables
load_env() {
    log_info "Loading environment variables..."
    
    # Priority: .env.production > .env.staging > .env
    if [ -f ".env.production" ]; then
        log_info "Loading from .env.production"
        export $(grep -v '^#' .env.production | xargs)
    elif [ -f ".env.staging" ]; then
        log_info "Loading from .env.staging"
        export $(grep -v '^#' .env.staging | xargs)
    elif [ -f ".env" ]; then
        log_info "Loading from .env"
        export $(grep -v '^#' .env | xargs)
    else
        log_error "No .env file found! Please create .env.production or .env"
        exit 1
    fi
}

# Function to create secret from env vars
create_secret() {
    local secret_name=$1
    shift
    local env_vars=("$@")
    
    log_info "Creating secret: $secret_name"
    
    # Check if secret already exists
    if secret_exists "$secret_name"; then
        log_warning "Secret $secret_name already exists. Updating..."
        kubectl delete secret "$secret_name" -n "$NAMESPACE"
    fi
    
    # Build kubectl command
    local cmd="kubectl create secret generic $secret_name -n $NAMESPACE"
    
    # Add each environment variable
    for var in "${env_vars[@]}"; do
        local value="${!var}"
        if [ -z "$value" ]; then
            log_warning "Environment variable $var is not set. Skipping..."
        else
            cmd="$cmd --from-literal=$var=\"$value\""
        fi
    done
    
    # Execute command
    eval $cmd
    
    if [ $? -eq 0 ]; then
        log_success "Secret $secret_name created successfully"
    else
        log_error "Failed to create secret $secret_name"
        return 1
    fi
}

# Main execution
main() {
    # Ensure we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        log_error "Must run from sophia-ai-intel root directory"
        exit 1
    fi
    
    # Check kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    
    # Create namespace if it doesn't exist
    log_info "Ensuring namespace exists..."
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Load environment variables
    load_env
    
    # Create main secrets
    log_info "Creating sophia-secrets..."
    create_secret "sophia-secrets" \
        "OPENAI_API_KEY" \
        "ANTHROPIC_API_KEY" \
        "OPENROUTER_API_KEY" \
        "TAVILY_API_KEY" \
        "PERPLEXITY_API_KEY" \
        "SERPER_API_KEY" \
        "GROQ_API_KEY" \
        "DEEPSEEK_API_KEY" \
        "MISTRAL_API_KEY" \
        "VOYAGE_API_KEY" \
        "COHERE_API_KEY" \
        "GOOGLE_API_KEY" \
        "PORTKEY_API_KEY" \
        "NEON_DATABASE_URL" \
        "NEON_REST_API_ENDPOINT" \
        "REDIS_URL" \
        "REDIS_HOST" \
        "REDIS_PORT" \
        "REDIS_USER_KEY" \
        "QDRANT_URL" \
        "QDRANT_API_KEY" \
        "GITHUB_APP_ID" \
        "GITHUB_INSTALLATION_ID" \
        "GITHUB_PRIVATE_KEY" \
        "APOLLO_API_KEY" \
        "USERGEMS_API_KEY" \
        "HUBSPOT_ACCESS_TOKEN" \
        "HUBSPOT_CLIENT_SECRET" \
        "HUBSPOT_API_TOKEN" \
        "LAMBDA_API_KEY" \
        "LAMBDA_PRIVATE_SSH_KEY" \
        "LAMBDA_PUBLIC_SSH_KEY"
    
    # Create image pull secret (if using private registry)
    if [ ! -z "$DOCKER_REGISTRY" ]; then
        log_info "Creating image pull secret..."
        kubectl create secret docker-registry regcred \
            --docker-server="$DOCKER_REGISTRY" \
            --docker-username="$DOCKER_USERNAME" \
            --docker-password="$DOCKER_PASSWORD" \
            --docker-email="$DOCKER_EMAIL" \
            -n "$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    # Create TLS secret for ingress (placeholder for Let's Encrypt)
    log_info "Creating placeholder TLS secret (will be replaced by cert-manager)..."
    if ! secret_exists "sophia-tls-secret"; then
        kubectl create secret tls sophia-tls-secret \
            --cert=/dev/null \
            --key=/dev/null \
            -n "$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f - || true
    fi
    
    echo ""
    log_success "All secrets created successfully!"
    echo ""
    log_info "Verify secrets with: kubectl get secrets -n $NAMESPACE"
    log_info "View secret details: kubectl describe secret sophia-secrets -n $NAMESPACE"
    echo ""
}

# Run main function
main "$@"
