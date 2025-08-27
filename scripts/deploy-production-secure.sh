#!/bin/bash
set -e

# Production Deployment Script with Secure Secrets Management
# This script handles deployment across Docker, Kubernetes, and local environments
# with proper secrets validation and security checks.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
ENV_FILE="$PROJECT_ROOT/.env.production.real"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
K8S_SECRETS_DIR="$PROJECT_ROOT/k8s-deploy/secrets"
K8S_MANIFESTS_DIR="$PROJECT_ROOT/k8s-deploy/manifests"

# Default values
DEPLOYMENT_MODE="docker"
SKIP_VALIDATION=false
FORCE_DEPLOY=false
DRY_RUN=false
VERBOSE=false

# Function definitions
log_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}🔍 DEBUG:${NC} $1"
    fi
}

show_help() {
    cat << EOF
Production Deployment Script with Secure Secrets Management

Usage: $0 [OPTIONS]

OPTIONS:
    --docker, -d            Deploy using Docker Compose (default)
    --kubernetes, -k        Deploy to Kubernetes cluster
    --local, -l             Deploy for local development
    --skip-validation       Skip secrets validation
    --force                 Force deployment even with warnings
    --dry-run              Show what would be deployed without deploying
    --verbose, -v           Enable verbose logging
    --help, -h             Show this help message

EXAMPLES:
    $0 --docker                # Deploy with Docker Compose
    $0 --kubernetes            # Deploy to Kubernetes
    $0 --local --verbose       # Local deployment with verbose output
    $0 --kubernetes --dry-run  # See what would be deployed to K8s

SECURITY NOTES:
    - This script requires real production secrets in .env.production.real
    - Secrets are validated before deployment
    - File permissions are checked for security
    - All deployments use encrypted secrets
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root (security risk)
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
    
    # Check required files
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Production environment file not found: $ENV_FILE"
        log_info "Please create the production environment file with real secrets"
        exit 1
    fi
    
    # Check file permissions
    local env_perms=$(stat -f "%A" "$ENV_FILE" 2>/dev/null || stat -c "%a" "$ENV_FILE" 2>/dev/null)
    if [[ "$env_perms" -gt 600 ]]; then
        log_warning "Environment file has loose permissions: $env_perms"
        log_info "Setting secure permissions (600) on $ENV_FILE"
        chmod 600 "$ENV_FILE"
    fi
    
    # Check Docker/Kubernetes tools based on deployment mode
    case "$DEPLOYMENT_MODE" in
        "docker")
            if ! command -v docker &> /dev/null; then
                log_error "Docker is required but not installed"
                exit 1
            fi
            if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
                log_error "Docker Compose is required but not installed"
                exit 1
            fi
            ;;
        "kubernetes")
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is required for Kubernetes deployment"
                exit 1
            fi
            if ! kubectl cluster-info &> /dev/null; then
                log_error "Cannot connect to Kubernetes cluster"
                exit 1
            fi
            ;;
    esac
    
    log_success "Prerequisites check passed"
}

validate_secrets() {
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        log_warning "Skipping secrets validation (--skip-validation flag set)"
        return 0
    fi
    
    log_info "Validating production secrets..."
    
    # Check if validation script exists
    local validation_script="$PROJECT_ROOT/scripts/validate-secrets.py"
    if [[ ! -f "$validation_script" ]]; then
        log_warning "Secrets validation script not found: $validation_script"
        return 0
    fi
    
    # Make validation script executable
    chmod +x "$validation_script"
    
    # Run validation
    if python3 "$validation_script" --env-file "$ENV_FILE"; then
        log_success "Secrets validation passed"
        return 0
    else
        log_error "Secrets validation failed"
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log_warning "Continuing deployment due to --force flag"
            return 0
        else
            log_error "Deployment aborted. Use --force to override or fix validation errors"
            exit 1
        fi
    fi
}

source_environment() {
    log_info "Loading production environment variables..."
    
    # Validate environment file format
    if ! grep -q "=" "$ENV_FILE"; then
        log_error "Environment file appears to be empty or malformed"
        exit 1
    fi
    
    # Source the environment file
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Turn off automatic export
    
    # Check critical variables are loaded
    local critical_vars=("POSTGRES_PASSWORD" "JWT_SECRET" "REDIS_PASSWORD")
    local missing_vars=()
    
    for var in "${critical_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Critical environment variables not loaded: ${missing_vars[*]}"
        exit 1
    fi
    
    log_debug "Loaded ${#critical_vars[@]} critical environment variables"
    log_success "Environment variables loaded successfully"
}

generate_kubernetes_secrets() {
    log_info "Generating Kubernetes secrets from environment file..."
    
    local generator_script="$PROJECT_ROOT/k8s-deploy/scripts/generate-production-secrets.py"
    if [[ ! -f "$generator_script" ]]; then
        log_error "Kubernetes secrets generator not found: $generator_script"
        exit 1
    fi
    
    # Make generator script executable
    chmod +x "$generator_script"
    
    # Generate secrets
    if python3 "$generator_script" --output-dir "$K8S_SECRETS_DIR"; then
        log_success "Kubernetes secrets generated successfully"
    else
        log_error "Failed to generate Kubernetes secrets"
        exit 1
    fi
}

deploy_docker() {
    log_info "Deploying with Docker Compose..."
    
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Change to project root for Docker Compose
    cd "$PROJECT_ROOT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would execute Docker Compose deployment"
        docker-compose config --quiet && log_info "Docker Compose configuration is valid"
        return 0
    fi
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose pull
    
    # Build and start services
    log_info "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    local timeout=300
    local count=0
    
    while [[ $count -lt $timeout ]]; do
        local unhealthy=$(docker-compose ps --filter "health=starting" --filter "health=unhealthy" -q | wc -l)
        if [[ $unhealthy -eq 0 ]]; then
            break
        fi
        sleep 5
        count=$((count + 5))
        log_debug "Waiting for services... ($count/$timeout seconds)"
    done
    
    if [[ $count -ge $timeout ]]; then
        log_warning "Some services may not be fully healthy after $timeout seconds"
        docker-compose ps
    else
        log_success "All services are healthy"
    fi
    
    # Show deployment status
    docker-compose ps
    log_success "Docker deployment completed"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Generate fresh secrets
    generate_kubernetes_secrets
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would deploy to Kubernetes"
        log_info "Would apply secrets from: $K8S_SECRETS_DIR"
        log_info "Would apply manifests from: $K8S_MANIFESTS_DIR"
        return 0
    fi
    
    # Apply secrets first
    log_info "Applying Kubernetes secrets..."
    if [[ -d "$K8S_SECRETS_DIR" ]]; then
        kubectl apply -f "$K8S_SECRETS_DIR/"
    fi
    
    # Apply manifests
    log_info "Applying Kubernetes manifests..."
    if [[ -d "$K8S_MANIFESTS_DIR" ]]; then
        kubectl apply -f "$K8S_MANIFESTS_DIR/"
    fi
    
    # Wait for rollout
    log_info "Waiting for deployments to be ready..."
    kubectl rollout status deployment --all --namespace=sophia --timeout=600s
    
    # Show deployment status
    kubectl get pods --namespace=sophia
    log_success "Kubernetes deployment completed"
}

deploy_local() {
    log_info "Setting up local development environment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would set up local environment"
        return 0
    fi
    
    # Create local .env symlink
    local local_env="$PROJECT_ROOT/.env"
    if [[ -L "$local_env" ]] || [[ -f "$local_env" ]]; then
        log_info "Backing up existing .env file"
        mv "$local_env" "$local_env.backup.$(date +%s)"
    fi
    
    ln -s "$(basename "$ENV_FILE")" "$local_env"
    log_info "Created .env symlink to production secrets"
    
    # Set up Python virtual environment if needed
    if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv "$PROJECT_ROOT/.venv"
    fi
    
    log_info "Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    # Install dependencies if requirements file exists
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    log_success "Local development environment ready"
    log_info "To activate: source .venv/bin/activate"
}

cleanup() {
    log_info "Performing cleanup..."
    
    # Remove temporary files if any were created
    # This is a placeholder for any cleanup needed
    
    log_debug "Cleanup completed"
}

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker|-d)
                DEPLOYMENT_MODE="docker"
                shift
                ;;
            --kubernetes|-k)
                DEPLOYMENT_MODE="kubernetes"
                shift
                ;;
            --local|-l)
                DEPLOYMENT_MODE="local"
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Main deployment flow
    log_info "Starting secure production deployment..."
    log_info "Deployment mode: $DEPLOYMENT_MODE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual deployment will occur"
    fi
    
    # Core deployment steps
    check_prerequisites
    validate_secrets
    source_environment
    
    # Deploy based on mode
    case "$DEPLOYMENT_MODE" in
        "docker")
            deploy_docker
            ;;
        "kubernetes")
            deploy_kubernetes
            ;;
        "local")
            deploy_local
            ;;
        *)
            log_error "Unknown deployment mode: $DEPLOYMENT_MODE"
            exit 1
            ;;
    esac
    
    log_success "🎉 Production deployment completed successfully!"
    
    # Security reminders
    echo
    log_warning "SECURITY REMINDERS:"
    log_warning "- Monitor your deployment for any issues"
    log_warning "- Rotate secrets regularly"
    log_warning "- Keep .env.production.real secure and never commit it"
    log_warning "- Review logs for any security concerns"
}

# Run main function with all arguments
main "$@"