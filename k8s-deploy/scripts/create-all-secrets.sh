#!/bin/bash

# Sophia AI - Create all Kubernetes secrets from .env files
# This script reads environment variables and creates K8s secrets

set -e

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
    
    log_info "Running Python script to apply granular secrets..."
    python3 k8s-deploy/scripts/apply_secrets.py
    
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
    # This section is commented out to prevent errors if Cert-Manager is not yet configured or working
    # secret_exists() {
    #     kubectl get secret "$1" -n "$NAMESPACE" &> /dev/null
    # }
    # log_info "Creating placeholder TLS secret (will be replaced by cert-manager)..."
    # if ! secret_exists "sophia-tls-secret"; then
    #     kubectl create secret tls sophia-tls-secret \
    #         --cert=/dev/null \
    #         --key=/dev/null \
    #         -n "$NAMESPACE" \
    #         --dry-run=client -o yaml | kubectl apply -f - || true
    # fi
    
    echo ""
    log_success "All secrets created successfully!"
    echo ""
    log_info "Verify all secrets created with: kubectl get secrets -n $NAMESPACE"
    echo ""
}

# Run main function
main "$@"
