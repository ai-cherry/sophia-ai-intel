#!/bin/bash

# Sophia AI ARM64 Deployment Script
# This script deploys the Sophia AI system on ARM64 Lambda Labs K3s cluster
# It replaces Qdrant with Weaviate and deploys services in dependency order

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="sophia-ai"
KUBECONFIG_FILE="./kubeconfig_lambda.yaml"
SSH_KEY="./lambda_kube_ssh_key.pem"
LAMBDA_IP="192.222.51.223"

# Function to print colored messages
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

# Function to check if SSH tunnel is active
check_ssh_tunnel() {
    if ! pgrep -f "8443:${LAMBDA_IP}:6443" > /dev/null; then
        log_warning "SSH tunnel not active. Starting tunnel..."
        ssh -i "$SSH_KEY" -L 8443:${LAMBDA_IP}:6443 -N -f ubuntu@${LAMBDA_IP}
        sleep 3
        log_success "SSH tunnel established"
    else
        log_info "SSH tunnel is already active"
    fi
}

# Function to verify kubectl connectivity
verify_kubectl() {
    export KUBECONFIG="$KUBECONFIG_FILE"
    
    log_info "Verifying kubectl connectivity..."
    if kubectl get nodes > /dev/null 2>&1; then
        log_success "kubectl connectivity verified"
        kubectl get nodes
    else
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
}

# Function to wait for pod to be ready
wait_for_pod() {
    local app_label=$1
    local timeout=${2:-300}  # Default 5 minutes
    local elapsed=0
    
    log_info "Waiting for $app_label to be ready (timeout: ${timeout}s)..."
    
    while [ $elapsed -lt $timeout ]; do
        # Check if pod exists and is running
        if kubectl get pods -n $NAMESPACE -l app=$app_label 2>/dev/null | grep -q "Running"; then
            # Check if pod is ready
            if kubectl get pods -n $NAMESPACE -l app=$app_label -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; then
                log_success "$app_label is ready!"
                return 0
            fi
        fi
        
        echo -n "."
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    echo ""
    log_error "$app_label failed to become ready within ${timeout} seconds"
    return 1
}

# Function to check service health
check_service_health() {
    local service=$1
    local port=$2
    local endpoint=${3:-"/health"}
    
    log_info "Checking health of $service on port $port..."
    
    # Start port-forward in background
    kubectl port-forward -n $NAMESPACE svc/$service $port:$port > /dev/null 2>&1 &
    local pf_pid=$!
    sleep 3
    
    # Check health endpoint
    if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        log_success "$service health check passed"
        kill $pf_pid 2>/dev/null
        return 0
    else
        log_warning "$service health check failed or not implemented"
        kill $pf_pid 2>/dev/null
        return 1
    fi
}

# Phase 0: Pre-flight checks
phase_0_preflight() {
    echo ""
    log_info "=== PHASE 0: PRE-FLIGHT CHECKS ==="
    
    # Check for required files
    if [ ! -f "$SSH_KEY" ]; then
        log_error "SSH key file not found: $SSH_KEY"
        exit 1
    fi
    
    if [ ! -f "$KUBECONFIG_FILE" ]; then
        log_error "Kubeconfig file not found: $KUBECONFIG_FILE"
        exit 1
    fi
    
    # Check SSH tunnel
    check_ssh_tunnel
    
    # Verify kubectl
    verify_kubectl
    
    # Check cluster resources
    log_info "Cluster resources:"
    kubectl top nodes 2>/dev/null || log_warning "Metrics server not available"
    
    log_success "Pre-flight checks completed"
}

# Phase 1: Replace Qdrant with Weaviate
phase_1_replace_vector_db() {
    echo ""
    log_info "=== PHASE 1: REPLACE VECTOR DATABASE ==="
    
    # Check if Qdrant exists
    if kubectl get deployment qdrant -n $NAMESPACE > /dev/null 2>&1; then
        log_warning "Removing incompatible Qdrant deployment..."
        kubectl delete deployment qdrant -n $NAMESPACE --ignore-not-found=true
        kubectl delete service qdrant -n $NAMESPACE --ignore-not-found=true
        kubectl delete pvc qdrant-storage -n $NAMESPACE --ignore-not-found=true
        log_success "Qdrant removed"
    else
        log_info "Qdrant not found, skipping removal"
    fi
    
    # Deploy Weaviate
    log_info "Deploying Weaviate (ARM64 compatible vector database)..."
    kubectl apply -f k8s-deploy/manifests/weaviate.yaml
    
    # Wait for Weaviate to be ready
    wait_for_pod "weaviate" 180
    
    # Verify Weaviate is accessible
    check_service_health "weaviate" 8080 "/v1/.well-known/ready"
    
    log_success "Weaviate deployed successfully"
}

# Phase 2: Deploy Core Infrastructure
phase_2_core_infrastructure() {
    echo ""
    log_info "=== PHASE 2: DEPLOY CORE INFRASTRUCTURE ==="
    
    # Check if Redis manifest exists
    if [ -f "k8s-deploy/manifests/redis.yaml" ]; then
        log_info "Deploying Redis event bus..."
        kubectl apply -f k8s-deploy/manifests/redis.yaml
        wait_for_pod "redis" 120
    else
        log_warning "Redis manifest not found, may already be deployed"
    fi
    
    # Deploy ConfigMaps
    if [ -f "k8s-deploy/manifests/configmap.yaml" ]; then
        log_info "Applying configuration..."
        kubectl apply -f k8s-deploy/manifests/configmap.yaml
    fi
    
    # Apply secrets
    log_info "Applying secrets..."
    if [ -f "k8s-deploy/scripts/apply_secrets.py" ]; then
        python3 k8s-deploy/scripts/apply_secrets.py || log_warning "Some secrets may have failed"
    else
        log_warning "apply_secrets.py not found"
    fi
    
    log_success "Core infrastructure deployed"
}

# Phase 3: Deploy Services
phase_3_deploy_services() {
    echo ""
    log_info "=== PHASE 3: DEPLOY SERVICES ==="
    
    # Group 1: Independent external integrations
    log_info "Deploying Group 1: External Integrations..."
    local group1_services=(
        "mcp-github"
        "mcp-hubspot"
        "mcp-salesforce"
        "mcp-gong"
        "mcp-slack"
    )
    
    for service in "${group1_services[@]}"; do
        if [ -f "k8s-deploy/manifests/${service}.yaml" ]; then
            log_info "Deploying $service..."
            kubectl apply -f "k8s-deploy/manifests/${service}.yaml" || log_warning "Failed to deploy $service"
        else
            log_warning "$service manifest not found"
        fi
    done
    
    # Wait for Group 1 services
    log_info "Waiting for external integration services..."
    sleep 10
    
    # Group 2: Core services (sequential)
    log_info "Deploying Group 2: Core Services (in order)..."
    local group2_services=(
        "mcp-context"
        "mcp-research"
        "mcp-agents"
        "mcp-business"
    )
    
    for service in "${group2_services[@]}"; do
        if [ -f "k8s-deploy/manifests/${service}.yaml" ]; then
            log_info "Deploying $service..."
            kubectl apply -f "k8s-deploy/manifests/${service}.yaml"
            wait_for_pod "$service" 120 || log_warning "$service may not be ready"
        else
            log_warning "$service manifest not found"
        fi
    done
    
    # Group 3: Orchestration layer
    log_info "Deploying Group 3: Orchestration Layer..."
    local group3_services=(
        "agno-coordinator"
        "orchestrator"
        "agno-teams"
    )
    
    for service in "${group3_services[@]}"; do
        if [ -f "k8s-deploy/manifests/${service}.yaml" ]; then
            log_info "Deploying $service..."
            kubectl apply -f "k8s-deploy/manifests/${service}.yaml" || log_warning "Failed to deploy $service"
        else
            log_warning "$service manifest not found"
        fi
    done
    
    log_success "Service deployment completed"
}

# Phase 4: Verification
phase_4_verification() {
    echo ""
    log_info "=== PHASE 4: VERIFICATION ==="
    
    # List all pods
    log_info "Current pod status:"
    kubectl get pods -n $NAMESPACE
    
    # Check for CrashLoopBackOff pods
    if kubectl get pods -n $NAMESPACE | grep -q "CrashLoopBackOff"; then
        log_warning "Some pods are in CrashLoopBackOff state:"
        kubectl get pods -n $NAMESPACE | grep "CrashLoopBackOff"
    fi
    
    # Check for ImagePullBackOff pods
    if kubectl get pods -n $NAMESPACE | grep -q "ImagePullBackOff"; then
        log_warning "Some pods have image pull issues:"
        kubectl get pods -n $NAMESPACE | grep "ImagePullBackOff"
        log_info "You may need to update the GitHub registry credentials"
    fi
    
    # Summary
    echo ""
    log_info "=== DEPLOYMENT SUMMARY ==="
    local total_pods=$(kubectl get pods -n $NAMESPACE --no-headers | wc -l)
    local running_pods=$(kubectl get pods -n $NAMESPACE --no-headers | grep "Running" | wc -l)
    local ready_pods=$(kubectl get pods -n $NAMESPACE -o json | jq '[.items[] | select(.status.conditions[] | select(.type=="Ready" and .status=="True"))] | length')
    
    echo "Total pods: $total_pods"
    echo "Running pods: $running_pods"
    echo "Ready pods: $ready_pods"
    
    if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
        log_success "All pods are ready! Deployment successful!"
    else
        log_warning "Some pods are not ready. Check logs for details."
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "   SOPHIA AI ARM64 DEPLOYMENT SCRIPT    "
    echo "========================================="
    echo ""
    log_info "Starting deployment on Lambda Labs ARM64 cluster"
    log_info "Target namespace: $NAMESPACE"
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Deployment cancelled"
        exit 0
    fi
    
    # Execute phases
    phase_0_preflight
    
    read -p "Continue with Phase 1 (Replace Vector DB)? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        phase_1_replace_vector_db
    fi
    
    read -p "Continue with Phase 2 (Core Infrastructure)? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        phase_2_core_infrastructure
    fi
    
    read -p "Continue with Phase 3 (Deploy Services)? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        phase_3_deploy_services
    fi
    
    phase_4_verification
    
    echo ""
    log_info "Deployment script completed!"
    log_info "Next steps:"
    echo "  1. Check pod logs for any errors: kubectl logs -n $NAMESPACE <pod-name>"
    echo "  2. Update GitHub registry credentials if seeing ImagePullBackOff"
    echo "  3. Run health checks: ./scripts/verify-health.sh"
    echo "  4. Access dashboard when ready: kubectl port-forward -n $NAMESPACE svc/sophia-dashboard 3000:3000"
}

# Run main function
main "$@"
