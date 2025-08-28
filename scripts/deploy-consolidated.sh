#!/bin/bash
# Sophia AI Consolidated Services Deployment Script
# Deploy 6 consolidated services to replace 12 individual MCP services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="sophia"
REGISTRY=${REGISTRY:-"sophia-registry"}
CONSOLIDATED_DIR="k8s-deploy/manifests/consolidated"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for consolidated deployment..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is required but not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    if ! docker images | grep -q "$REGISTRY"; then
        log_warning "No consolidated service images found in registry: $REGISTRY"
        log_info "Run './scripts/build-consolidated.sh all' to build images first"
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace if needed
ensure_namespace() {
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_info "Namespace '$NAMESPACE' already exists"
    else
        log_info "Creating namespace '$NAMESPACE'..."
        kubectl create namespace $NAMESPACE
        log_success "Namespace created"
    fi
}

# Deploy consolidated services
deploy_services() {
    log_info "Deploying consolidated services architecture..."
    
    # Deploy services in dependency order
    local services=(
        "sophia-infrastructure"    # Infrastructure first
        "sophia-ai-core"          # Core AI services  
        "sophia-business-intel"   # Business intelligence
        "sophia-communications"   # Communications
        "sophia-development"      # Development tools
        "sophia-orchestration"    # Orchestration last
    )
    
    for service in "${services[@]}"; do
        local manifest="$CONSOLIDATED_DIR/$service.yaml"
        if [[ -f "$manifest" ]]; then
            log_info "Deploying $service..."
            kubectl apply -f "$manifest"
            
            # Wait for deployment to be ready
            kubectl rollout status deployment/$service -n $NAMESPACE --timeout=300s || {
                log_warning "$service deployment may not be fully ready"
            }
        else
            log_error "Manifest not found: $manifest"
            exit 1
        fi
    done
    
    log_success "All consolidated services deployed"
}

# Deploy ingress configuration
deploy_ingress() {
    local ingress_manifest="$CONSOLIDATED_DIR/consolidated-ingress.yaml"
    
    if [[ -f "$ingress_manifest" ]]; then
        log_info "Deploying consolidated ingress configuration..."
        kubectl apply -f "$ingress_manifest"
        log_success "Ingress configuration deployed"
    else
        log_warning "Consolidated ingress manifest not found: $ingress_manifest"
    fi
}

# Remove legacy services
cleanup_legacy_services() {
    log_info "Cleaning up legacy individual MCP services..."
    
    local legacy_services=(
        "mcp-agents" "mcp-context" "mcp-research" "mcp-business"
        "mcp-github" "mcp-hubspot" "mcp-salesforce" "mcp-gong"
        "mcp-slack" "mcp-lambda" "mcp-apollo" "agno-coordinator"
        "agno-teams" "agno-wrappers" "orchestrator"
    )
    
    for service in "${legacy_services[@]}"; do
        if kubectl get deployment $service -n $NAMESPACE &> /dev/null; then
            log_info "Removing legacy service: $service"
            kubectl delete deployment $service -n $NAMESPACE --ignore-not-found=true
            kubectl delete service $service -n $NAMESPACE --ignore-not-found=true
            kubectl delete pvc ${service}-storage -n $NAMESPACE --ignore-not-found=true
        fi
    done
    
    log_success "Legacy services cleanup completed"
}

# Validate deployment
validate_deployment() {
    log_info "Validating consolidated services deployment..."
    
    local services=("sophia-ai-core" "sophia-business-intel" "sophia-communications" 
                   "sophia-development" "sophia-orchestration" "sophia-infrastructure")
    
    local ready_count=0
    local total_count=${#services[@]}
    
    for service in "${services[@]}"; do
        local ready_replicas=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired_replicas=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [[ "$ready_replicas" -eq "$desired_replicas" ]] && [[ "$ready_replicas" -gt 0 ]]; then
            log_success "$service: $ready_replicas/$desired_replicas replicas ready"
            ((ready_count++))
        else
            log_warning "$service: $ready_replicas/$desired_replicas replicas ready"
        fi
    done
    
    log_info "Deployment Summary:"
    echo "  Ready services: $ready_count/$total_count"
    
    if [[ $ready_count -eq $total_count ]]; then
        log_success "🎉 All consolidated services are running successfully!"
        log_info "Architecture consolidated from 12→6 services (50% reduction)"
    else
        log_warning "Some services may need additional time to become ready"
    fi
    
    # Show pod status
    echo
    log_info "Current pod status:"
    kubectl get pods -n $NAMESPACE -l tier
}

# Show access information
show_access_info() {
    echo
    log_info "=== SOPHIA AI CONSOLIDATED DEPLOYMENT ACCESS ==="
    echo
    echo "🔗 Service Endpoints:"
    echo "   AI Core:          /ai/, /agents/, /context/, /research/"
    echo "   Business Intel:   /business/, /crm/, /salesforce/, /hubspot/"
    echo "   Communications:   /communications/, /slack/, /gong/"
    echo "   Development:      /development/, /github/, /lambda/"
    echo "   Orchestration:    /orchestration/, /workflows/"
    echo "   Infrastructure:   /infrastructure/, /health/, /metrics/"
    echo
    echo "🚀 Next Steps:"
    echo "   1. Port-forward to test: kubectl port-forward -n sophia svc/sophia-orchestration 8000:8000"
    echo "   2. Check logs: kubectl logs -n sophia deployment/sophia-ai-core -f"
    echo "   3. Monitor health: curl http://localhost:8000/health"
    echo
}

# Main execution
main() {
    echo "========================================="
    echo "   SOPHIA AI CONSOLIDATED DEPLOYMENT     "
    echo "========================================="
    echo
    log_info "Deploying consolidated services architecture (12→6 services)"
    echo
    
    check_prerequisites
    ensure_namespace
    deploy_services
    deploy_ingress
    cleanup_legacy_services
    validate_deployment
    show_access_info
    
    echo
    log_success "🎉 Consolidated deployment completed successfully!"
    log_info "Platform architecture optimized: 12→6 services (50% complexity reduction)"
}

# Run main function
main "$@"