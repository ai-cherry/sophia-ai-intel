#!/bin/bash
# Sophia AI Kubernetes Deployment Script
# Unified deployment for all services and configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="sophia"
DEPLOY_TIMEOUT="600s"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is installed and configured
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Label namespace for network policies and other resources
    kubectl label namespace "$NAMESPACE" app=sophia-ai --overwrite

    log_success "Namespace created and labeled"
}

# Apply configuration in order
apply_configuration() {
    log_info "Applying Kubernetes configuration..."

    # 1. Apply namespace and RBAC (if exists)
    if [ -f "manifests/namespace.yaml" ]; then
        log_info "Applying namespace configuration..."
        kubectl apply -f manifests/namespace.yaml
    fi

    # 2. Apply ConfigMaps
    if [ -f "manifests/configmap.yaml" ]; then
        log_info "Applying ConfigMaps..."
        kubectl apply -f manifests/configmap.yaml
    fi

    # 3. Apply Secrets
    if [ -d "secrets" ]; then
        log_info "Applying Secrets..."
        kubectl apply -f secrets/
    fi

    # 4. Apply Storage Classes and PVCs (if any)
    # kubectl apply -f storage/

    # 5. Apply Services
    if ls manifests/*service*.yaml 1> /dev/null 2>&1; then
        log_info "Applying Services..."
        kubectl apply -f manifests/*service*.yaml
    fi

    # 6. Apply Deployments
    if ls manifests/*deployment*.yaml 1> /dev/null 2>&1; then
        log_info "Applying Deployments..."
        kubectl apply -f manifests/*deployment*.yaml
    fi

    # 7. Apply StatefulSets
    if ls manifests/*statefulset*.yaml 1> /dev/null 2>&1; then
        log_info "Applying StatefulSets..."
        kubectl apply -f manifests/*statefulset*.yaml
    fi

    # 8. Apply Jobs/CronJobs
    if ls manifests/*job*.yaml 1> /dev/null 2>&1; then
        log_info "Applying Jobs/CronJobs..."
        kubectl apply -f manifests/*job*.yaml
    fi

    # 9. Apply Ingress/Network Policies
    if ls manifests/*ingress*.yaml 1> /dev/null 2>&1; then
        log_info "Applying Ingress resources..."
        kubectl apply -f manifests/*ingress*.yaml
    fi

    if ls manifests/*network*.yaml 1> /dev/null 2>&1; then
        log_info "Applying Network Policies..."
        kubectl apply -f manifests/*network*.yaml
    fi

    log_success "Configuration applied successfully"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."

    # Get all deployments in the namespace
    local deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true)

    if [ -n "$deployments" ]; then
        log_info "Found deployments: $deployments"

        # Wait for each deployment to be ready
        for deployment in $deployments; do
            log_info "Waiting for deployment: $deployment"
            kubectl wait --for=condition=available --timeout="$DEPLOY_TIMEOUT" deployment/"$deployment" -n "$NAMESPACE"
        done
    else
        log_warning "No deployments found in namespace $NAMESPACE"
    fi

    log_success "All deployments are ready"
}

# Wait for statefulsets to be ready
wait_for_statefulsets() {
    log_info "Waiting for StatefulSets to be ready..."

    local statefulsets=$(kubectl get statefulsets -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true)

    if [ -n "$statefulsets" ]; then
        log_info "Found StatefulSets: $statefulsets"

        for statefulset in $statefulsets; do
            log_info "Waiting for StatefulSet: $statefulset"
            kubectl wait --for=condition=ready --timeout="$DEPLOY_TIMEOUT" statefulset/"$statefulset" -n "$NAMESPACE"
        done
    fi

    log_success "All StatefulSets are ready"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pod status
    log_info "Pod status:"
    kubectl get pods -n "$NAMESPACE" --show-labels

    # Check service status
    log_info "Service status:"
    kubectl get services -n "$NAMESPACE"

    # Check ingress status (if any)
    local ingress_count=$(kubectl get ingress -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    if [ "$ingress_count" -gt 0 ]; then
        log_info "Ingress status:"
        kubectl get ingress -n "$NAMESPACE"
    fi

    # Run basic health checks
    run_health_checks

    log_success "Deployment verification completed"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Get all pods
    local pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    for pod in $pods; do
        log_info "Checking pod: $pod"

        # Check if pod is ready
        local ready_status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

        if [ "$ready_status" == "True" ]; then
            log_success "Pod $pod is ready"

            # Try to run a basic health check if the pod has a health endpoint
            # This is a simple example - adjust based on your actual health check endpoints
            local pod_ip=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.podIP}')
            if [ -n "$pod_ip" ]; then
                log_info "Pod IP: $pod_ip"
            fi
        else
            log_warning "Pod $pod is not ready"
        fi
    done
}

# Main deployment function
deploy() {
    log_info "Starting Sophia AI Kubernetes deployment..."

    check_prerequisites
    create_namespace
    apply_configuration
    wait_for_deployments
    wait_for_statefulsets
    verify_deployment

    log_success "Sophia AI deployment completed successfully!"
    log_info "You can now access your services through the configured ingress endpoints."
}

# Rollback function
rollback() {
    log_warning "Starting rollback..."

    log_info "Scaling down deployments..."
    kubectl scale deployment --all --replicas=0 -n "$NAMESPACE"

    log_info "Waiting for pods to terminate..."
    sleep 30

    # Here you could implement more sophisticated rollback logic
    # such as restoring from previous deployment, rolling back to previous image tags, etc.

    log_warning "Rollback completed. Manual intervention may be required to restore services."
}

# Help function
show_help() {
    cat << EOF
Sophia AI Kubernetes Deployment Script

Usage: $0 [COMMAND]

Commands:
  deploy          Deploy all services (default)
  rollback        Rollback to previous state
  status          Show deployment status
  help            Show this help message

Environment Variables:
  NAMESPACE       Kubernetes namespace (default: sophia)
  DEPLOY_TIMEOUT  Deployment timeout (default: 600s)

Examples:
  $0 deploy
  $0 status
  NAMESPACE=staging $0 deploy

EOF
}

# Status function
show_status() {
    log_info "Showing deployment status for namespace: $NAMESPACE"

    echo ""
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    log_info "Services:"
    kubectl get services -n "$NAMESPACE"

    echo ""
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE"

    echo ""
    log_info "ConfigMaps:"
    kubectl get configmaps -n "$NAMESPACE"

    echo ""
    log_info "Secrets:"
    kubectl get secrets -n "$NAMESPACE"

    echo ""
    log_info "Ingress:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || log_warning "No ingress resources found"
}

# Main script logic
main() {
    local command=${1:-deploy}

    case $command in
        deploy)
            deploy
            ;;
        rollback)
            rollback
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"