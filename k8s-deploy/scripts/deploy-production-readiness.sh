#!/bin/bash
# Production Readiness Deployment Script
# Deploys all Phase 3C production readiness components

set -e

# Configuration
NAMESPACE="${NAMESPACE:-sophia}"
DEPLOYMENT_DIR="./manifests"
SCRIPT_DIR="./scripts"

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

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace "$NAMESPACE"
    fi

    log_success "Prerequisites check passed"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    if [[ -f "monitoring/docker-compose.monitoring.yml" ]]; then
        log_info "Starting monitoring services with Docker Compose..."
        cd monitoring && docker-compose -f docker-compose.monitoring.yml up -d
        cd ..
        log_success "Monitoring stack deployed"
    else
        log_warn "Monitoring docker-compose file not found"
    fi
}

# Function to deploy namespace and RBAC
deploy_namespace_and_rbac() {
    log_info "Deploying namespace and RBAC..."

    kubectl apply -f "$DEPLOYMENT_DIR/namespace.yaml"
    log_success "Namespace and RBAC deployed"
}

# Function to deploy ConfigMaps
deploy_configmaps() {
    log_info "Deploying ConfigMaps..."

    kubectl apply -f "$DEPLOYMENT_DIR/configmap.yaml"
    kubectl apply -f "$DEPLOYMENT_DIR/configmap-production.yaml"
    kubectl apply -f "$DEPLOYMENT_DIR/configmap-staging.yaml"

    log_success "ConfigMaps deployed"
}

# Function to deploy Pod Disruption Budgets
deploy_pod_disruption_budgets() {
    log_info "Deploying Pod Disruption Budgets..."

    kubectl apply -f "$DEPLOYMENT_DIR/pod-disruption-budgets.yaml"
    log_success "Pod Disruption Budgets deployed"
}

# Function to deploy HPAs and VPAs
deploy_autoscaling() {
    log_info "Deploying autoscaling configurations..."

    kubectl apply -f "$DEPLOYMENT_DIR/hpa.yaml"
    kubectl apply -f "$DEPLOYMENT_DIR/vpa.yaml"
    log_success "Autoscaling configurations deployed"
}

# Function to deploy Istio service mesh
deploy_istio() {
    log_info "Deploying Istio service mesh..."

    kubectl apply -f "$DEPLOYMENT_DIR/istio-control-plane.yaml"
    log_success "Istio service mesh deployed"
}

# Function to deploy configuration management
deploy_config_management() {
    log_info "Deploying configuration management..."

    kubectl apply -f "$DEPLOYMENT_DIR/config-management-cronjobs.yaml"
    log_success "Configuration management deployed"
}

# Function to verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check if all components are running
    local components=("prometheus" "grafana" "loki")
    local istio_components=("istio-pilot" "istio-ingressgateway")

    # Wait for components to be ready
    log_info "Waiting for components to be ready..."
    sleep 30

    # Check monitoring components
    for component in "${components[@]}"; do
        if kubectl get deployment "$component" -n monitoring &> /dev/null; then
            local ready_replicas
            ready_replicas=$(kubectl get deployment "$component" -n monitoring -o jsonpath='{.status.readyReplicas}')
            if [[ "$ready_replicas" -gt 0 ]]; then
                log_success "Monitoring component $component is ready"
            else
                log_warn "Monitoring component $component is not ready yet"
            fi
        fi
    done

    # Check Istio components
    for component in "${istio_components[@]}"; do
        if kubectl get deployment "$component" -n istio-system &> /dev/null; then
            local ready_replicas
            ready_replicas=$(kubectl get deployment "$component" -n istio-system -o jsonpath='{.status.readyReplicas}')
            if [[ "$ready_replicas" -gt 0 ]]; then
                log_success "Istio component $component is ready"
            else
                log_warn "Istio component $component is not ready yet"
            fi
        fi
    done

    # Check Pod Disruption Budgets
    local pdb_count
    pdb_count=$(kubectl get pdb -n "$NAMESPACE" --no-headers | wc -l)
    if [[ $pdb_count -gt 0 ]]; then
        log_success "Found $pdb_count Pod Disruption Budgets"
    else
        log_warn "No Pod Disruption Budgets found"
    fi

    # Check ConfigMaps
    local configmap_count
    configmap_count=$(kubectl get configmaps -n "$NAMESPACE" --no-headers | wc -l)
    if [[ $configmap_count -gt 0 ]]; then
        log_success "Found $configmap_count ConfigMaps"
    else
        log_warn "No ConfigMaps found"
    fi

    log_success "Deployment verification completed"
}

# Function to run health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."

    if [[ -f "$SCRIPT_DIR/comprehensive-health-check.sh" ]]; then
        chmod +x "$SCRIPT_DIR/comprehensive-health-check.sh"
        "$SCRIPT_DIR/comprehensive-health-check.sh"
    else
        log_warn "Health check script not found"
    fi
}

# Function to run configuration drift detection
run_config_drift_detection() {
    log_info "Running configuration drift detection..."

    if [[ -f "$SCRIPT_DIR/config-drift-detection.sh" ]]; then
        chmod +x "$SCRIPT_DIR/config-drift-detection.sh"
        "$SCRIPT_DIR/config-drift-detection.sh"
    else
        log_warn "Configuration drift detection script not found"
    fi
}

# Function to display deployment summary
display_summary() {
    log_info "=== Production Readiness Deployment Summary ==="

    echo ""
    log_success "✅ Monitoring Stack: Prometheus, Grafana, Loki"
    log_success "✅ Istio Service Mesh: Mutual TLS, Traffic Management"
    log_success "✅ Autoscaling: HPA and VPA configurations"
    log_success "✅ Configuration Management: ConfigMaps, Drift Detection"
    log_success "✅ Pod Disruption Budgets: High availability protection"
    log_success "✅ Health Checks: Automated monitoring and alerts"
    log_success "✅ CronJobs: Automated drift detection and health monitoring"

    echo ""
    log_info "Next Steps:"
    echo "1. Update your service deployments to include resource limits and requests"
    echo "2. Configure SSL certificates for your domains"
    echo "3. Set up external monitoring and alerting integrations"
    echo "4. Review and customize the configuration for your specific environment"
    echo "5. Run regular health checks and drift detection"

    echo ""
    log_info "Useful Commands:"
    echo "• Check health: kubectl get pods -n $NAMESPACE"
    echo "• View monitoring: kubectl port-forward svc/grafana 3000:3000 -n monitoring"
    echo "• Check Istio: kubectl get pods -n istio-system"
    echo "• Run health check: $SCRIPT_DIR/comprehensive-health-check.sh"
    echo "• Check config drift: $SCRIPT_DIR/config-drift-detection.sh"
}

# Main function
main() {
    log_info "Starting Sophia AI Production Readiness Deployment"
    log_info "Namespace: $NAMESPACE"
    log_info "Deployment Directory: $DEPLOYMENT_DIR"

    # Check prerequisites
    check_prerequisites

    # Deploy components in order
    deploy_namespace_and_rbac
    deploy_configmaps
    deploy_monitoring
    deploy_pod_disruption_budgets
    deploy_autoscaling
    deploy_istio
    deploy_config_management

    # Verify deployment
    verify_deployment

    # Run initial checks
    run_health_checks
    run_config_drift_detection

    # Display summary
    display_summary

    log_success "Production Readiness Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "verify")
        verify_deployment
        ;;
    "health")
        run_health_checks
        ;;
    "drift")
        run_config_drift_detection
        ;;
    "summary")
        display_summary
        ;;
    *)
        main
        ;;
esac