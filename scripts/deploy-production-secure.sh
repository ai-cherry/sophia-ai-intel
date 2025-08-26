#!/bin/bash

# Sophia AI - Production Secure Deployment Script
# This script orchestrates the complete production deployment with secrets management

set -e

# Configuration
ENV_FILE=".env.production"
SECURE_ENV_FILE=".env.production.secure"
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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if required tools are installed
    local tools=("docker" "docker-compose" "kubectl" "openssl" "ssh-keygen")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            return 1
        fi
    done

    # Check if required scripts exist
    local scripts=("scripts/env-production-validation.sh" "scripts/generate-secure-secrets.sh")
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            log_error "Required script not found: $script"
            return 1
        fi
    done

    log_success "Prerequisites check passed"
    return 0
}

# Function to generate secure secrets
generate_secrets() {
    log_info "Generating secure secrets..."

    if [ ! -f "$SECURE_ENV_FILE" ]; then
        log_info "Secure environment file not found. Generating..."
        ./scripts/generate-secure-secrets.sh
    else
        read -p "Secure environment file already exists. Regenerate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./scripts/generate-secure-secrets.sh
        fi
    fi

    log_success "Secure secrets ready"
    return 0
}

# Function to validate environment
validate_environment() {
    log_info "Validating environment configuration..."

    if [ -f "$SECURE_ENV_FILE" ]; then
        ENV_FILE="$SECURE_ENV_FILE" ./scripts/env-production-validation.sh
    else
        ./scripts/env-production-validation.sh
    fi

    if [ $? -eq 0 ]; then
        log_success "Environment validation passed"
        return 0
    else
        log_error "Environment validation failed"
        return 1
    fi
}

# Function to create Kubernetes secrets
create_kubernetes_secrets() {
    log_info "Creating Kubernetes secrets..."

    # Check if we're using the secure environment file
    if [ -f "$SECURE_ENV_FILE" ]; then
        cp "$SECURE_ENV_FILE" "$ENV_FILE"
    fi

    # Create Kubernetes secrets
    ./k8s-deploy/scripts/create-all-secrets.sh

    log_success "Kubernetes secrets created"
    return 0
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    # Check if namespace exists, create if not
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Apply manifests in order
    log_info "Applying namespace and RBAC..."
    kubectl apply -f k8s-deploy/manifests/namespace.yaml

    log_info "Applying secrets and configmaps..."
    kubectl apply -f k8s-deploy/manifests/

    log_info "Applying services and deployments..."
    kubectl apply -f k8s-deploy/manifests/

    log_info "Applying ingress..."
    kubectl apply -f k8s-deploy/manifests/

    log_success "Kubernetes deployment completed"
    return 0
}

# Function to deploy via Docker Compose
deploy_docker() {
    log_info "Deploying via Docker Compose..."

    # Use the secure environment file if available
    if [ -f "$SECURE_ENV_FILE" ]; then
        export $(grep -v '^#' "$SECURE_ENV_FILE" | xargs)
    fi

    # Build and deploy
    docker-compose build
    docker-compose up -d

    log_success "Docker Compose deployment completed"
    return 0
}

# Function to run post-deployment checks
post_deployment_checks() {
    log_info "Running post-deployment checks..."

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    # Check pod status
    if command -v kubectl &> /dev/null; then
        kubectl get pods -n "$NAMESPACE"
        kubectl get services -n "$NAMESPACE"
        kubectl get ingress -n "$NAMESPACE"
    fi

    # Check Docker containers
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    fi

    log_success "Post-deployment checks completed"
    return 0
}

# Function to show deployment summary
show_summary() {
    echo ""
    log_info "======================================"
    log_success "🎉 PRODUCTION DEPLOYMENT COMPLETED!"
    log_info "======================================"
    echo ""

    log_info "Next Steps:"
    echo "1. Verify services are running: kubectl get pods -n $NAMESPACE"
    echo "2. Check application logs: kubectl logs -n $NAMESPACE -l app=sophia"
    echo "3. Test endpoints:"
    echo "   - Main app: https://www.sophia-intel.ai"
    echo "   - API: https://api.sophia-intel.ai"
    echo "4. Monitor dashboards:"
    echo "   - Grafana: http://your-server:3001"
    echo "   - Prometheus: http://your-server:9090"
    echo ""

    log_warning "Security Reminders:"
    echo "  🔴 Remove any temporary secret files"
    echo "  🔴 Rotate secrets regularly (90 days)"
    echo "  🔴 Monitor access logs and alerts"
    echo "  🔴 Keep backups secure and encrypted"
    echo ""

    log_success "Production deployment successful! 🚀"
}

# Main function
main() {
    log_info "======================================"
    log_info "🔒 Sophia AI Production Deployment"
    log_info "======================================"
    echo ""

    # Parse command line arguments
    local deploy_mode="kubernetes"  # Default to Kubernetes

    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                deploy_mode="docker"
                shift
                ;;
            --kubernetes)
                deploy_mode="kubernetes"
                shift
                ;;
            --help|-h)
                echo "Sophia AI Production Deployment Script"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --docker       Deploy using Docker Compose"
                echo "  --kubernetes   Deploy using Kubernetes (default)"
                echo "  --help, -h     Show this help message"
                echo ""
                echo "This script performs a complete production deployment"
                echo "with secrets management and validation."
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log_info "Deployment mode: $deploy_mode"
    echo ""

    # Execute deployment steps
    check_prerequisites || exit 1
    echo ""

    generate_secrets || exit 1
    echo ""

    validate_environment || exit 1
    echo ""

    if [ "$deploy_mode" = "kubernetes" ]; then
        create_kubernetes_secrets || exit 1
        echo ""
        deploy_kubernetes || exit 1
    else
        deploy_docker || exit 1
    fi
    echo ""

    post_deployment_checks || exit 1
    echo ""

    show_summary
}

# Run main function
main "$@"