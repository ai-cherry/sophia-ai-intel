#!/bin/bash

# Sonic AI Deployment Script
# Phase 5: Autonomous Deployment and Integration

set -e

# Configuration
NAMESPACE="sophia"
SONIC_AI_IMAGE="ghcr.io/ai-cherry/sophia-sonic-ai:latest"
KUBECONFIG_PATH="${KUBECONFIG:-$HOME/.kube/config}"
SONIC_AI_HOST="sonic-ai.sophia.svc.cluster.local"
SONIC_AI_PORT="8080"

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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if we're connected to a Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to a Kubernetes cluster"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace $NAMESPACE
    fi

    # Check if secrets exist
    if ! kubectl get secret sophia-secrets -n $NAMESPACE &> /dev/null; then
        log_error "Required secrets (sophia-secrets) not found in namespace $NAMESPACE"
        log_info "Please create the required secrets first:"
        log_info "kubectl create secret generic sophia-secrets -n $NAMESPACE \\"
        log_info "  --from-literal=SONIC_API_KEY=your-sonic-api-key \\"
        log_info "  --from-literal=OPENROUTER_API_KEY=your-openrouter-api-key"
        exit 1
    fi

    log_success "Pre-deployment checks passed"
}

# Deploy Sonic AI
deploy_sonic_ai() {
    log_info "Deploying Sonic AI service..."

    # Apply Kubernetes manifests in order
    log_info "Creating PersistentVolumeClaim..."
    kubectl apply -f k8s-deploy/manifests/sonic-ai.yaml

    log_info "Creating Ingress..."
    kubectl apply -f k8s-deploy/manifests/sonic-ai-ingress.yaml

    log_success "Sonic AI deployment manifests applied"
}

# Update Prometheus configuration
update_prometheus_config() {
    log_info "Updating Prometheus configuration for Sonic AI..."

    # Create ConfigMap with Sonic AI specific Prometheus config
    kubectl create configmap sonic-ai-prometheus-config -n $NAMESPACE \
        --from-file=sonic-ai-prometheus.yml=monitoring/sonic-ai-prometheus.yml \
        --dry-run=client -o yaml | kubectl apply -f -

    log_success "Prometheus configuration updated"
}

# Update AlertManager configuration
update_alertmanager_config() {
    log_info "Updating AlertManager configuration for Sonic AI..."

    # Create ConfigMap with Sonic AI specific alerts
    kubectl create configmap sonic-ai-alerts-config -n $NAMESPACE \
        --from-file=sonic-ai-alerts.yml=monitoring/sonic-ai-alerts.yml \
        --dry-run=client -o yaml | kubectl apply -f -

    log_success "AlertManager configuration updated"
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for Sonic AI deployment to be ready..."

    # Wait for deployment to be available
    kubectl wait --for=condition=available --timeout=300s deployment/sonic-ai -n $NAMESPACE

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=sonic-ai -n $NAMESPACE --timeout=300s

    log_success "Sonic AI deployment is ready"
}

# Post-deployment validation
post_deployment_validation() {
    log_info "Running post-deployment validation..."

    # Check if pods are running
    local pods_ready=$(kubectl get pods -l app=sonic-ai -n $NAMESPACE -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
    if [[ "$pods_ready" != *"True"* ]]; then
        log_error "Sonic AI pods are not ready"
        kubectl get pods -l app=sonic-ai -n $NAMESPACE
        exit 1
    fi

    # Test health endpoint
    log_info "Testing Sonic AI health endpoint..."
    local health_response=$(kubectl exec -n $NAMESPACE -l app=sonic-ai -- curl -f http://localhost:8080/healthz 2>/dev/null || echo "failed")

    if [[ "$health_response" == *"failed"* ]]; then
        log_error "Sonic AI health check failed"
        exit 1
    fi

    # Check metrics endpoint
    log_info "Testing Sonic AI metrics endpoint..."
    local metrics_response=$(kubectl exec -n $NAMESPACE -l app=sonic-ai -- curl -f http://localhost:8080/metrics 2>/dev/null || echo "failed")

    if [[ "$metrics_response" == *"failed"* ]]; then
        log_warning "Sonic AI metrics endpoint not accessible (this may be normal if Prometheus is not yet configured)"
    else
        log_success "Sonic AI metrics endpoint is accessible"
    fi

    log_success "Post-deployment validation completed successfully"
}

# Setup monitoring integration
setup_monitoring() {
    log_info "Setting up monitoring integration..."

    # Update Grafana dashboards
    log_info "Updating Grafana dashboards..."
    kubectl create configmap sonic-ai-grafana-dashboard -n $NAMESPACE \
        --from-file=sonic-ai-performance.json=monitoring/grafana/dashboards/sonic-ai-performance.json \
        --dry-run=client -o yaml | kubectl apply -f -

    log_success "Monitoring integration configured"
}

# Generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."

    local report_file="SONIC_AI_DEPLOYMENT_REPORT_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# Sonic AI Deployment Report

**Deployment Date:** $(date)
**Namespace:** $NAMESPACE
**Image:** $SONIC_AI_IMAGE

## Deployment Status

### Kubernetes Resources
\`\`\`bash
# Check deployment status
kubectl get deployment sonic-ai -n $NAMESPACE

# Check pods status
kubectl get pods -l app=sonic-ai -n $NAMESPACE

# Check services
kubectl get svc -l app=sonic-ai -n $NAMESPACE

# Check ingress
kubectl get ingress sonic-ai-ingress -n $NAMESPACE
\`\`\`

### Service Endpoints
- **Internal Service:** http://sonic-ai.sophia.svc.cluster.local:8080
- **Health Check:** http://sonic-ai.sophia.svc.cluster.local:8080/healthz
- **Metrics:** http://sonic-ai.sophia.svc.cluster.local:8080/metrics
- **API Endpoints:**
  - POST /sonic/generate-code - Code generation
  - POST /sonic/reason - AI reasoning
  - POST /sonic/optimize - Code optimization
  - GET /sonic/status - Service status
  - GET /sonic/metrics - Performance metrics
  - GET /sonic/capabilities - AI capabilities

### Monitoring
- **Grafana Dashboard:** Sonic AI Performance Dashboard
- **Prometheus Metrics:** sonic_ai_* metrics
- **Alert Rules:** Sonic AI specific alerts configured

## Configuration

### Environment Variables
- DASHBOARD_ORIGIN: http://sophia-dashboard:3000
- GITHUB_MCP_URL: http://sophia-github:8080
- CONTEXT_MCP_URL: http://sophia-context:8080
- RESEARCH_MCP_URL: http://sophia-research:8080
- BUSINESS_MCP_URL: http://sophia-business:8080
- AGENTS_MCP_URL: http://sophia-agents:8080
- MAX_CONCURRENT_REQUESTS: 10
- REASONING_TIMEOUT_MS: 5000

### Secrets Required
- SONIC_API_KEY: Sonic AI API key
- SONIC_MODEL_ENDPOINT: Sonic AI model endpoint
- OPENROUTER_API_KEY: OpenRouter API key

## Next Steps

1. **Test Sonic AI Endpoints:**
   \`\`\`bash
   # Test code generation
   curl -X POST http://sonic-ai.sophia.svc.cluster.local:8080/sonic/generate-code \\
     -H "Content-Type: application/json" \\
     -d '{"prompt": "Create a Python function to calculate fibonacci", "language": "python"}'

   # Test reasoning
   curl -X POST http://sonic-ai.sophia.svc.cluster.local:8080/sonic/reason \\
     -H "Content-Type: application/json" \\
     -d '{"query": "What is the best approach for optimizing this code?", "context_type": "code"}'
   \`\`\`

2. **Monitor Performance:**
   - Access Grafana dashboard: Sonic AI Performance Dashboard
   - Monitor key metrics: response time, success rate, active requests
   - Set up alerts for performance thresholds

3. **Scale as Needed:**
   - Monitor HPA: kubectl get hpa sonic-ai-hpa -n $NAMESPACE
   - Adjust replica count based on load
   - Consider GPU node scaling for high-demand periods

## Troubleshooting

### Common Issues

1. **Pods Not Starting:**
   \`\`\`bash
   kubectl logs -l app=sonic-ai -n $NAMESPACE
   kubectl describe pod -l app=sonic-ai -n $NAMESPACE
   \`\`\`

2. **Health Check Failures:**
   \`\`\`bash
   kubectl exec -n $NAMESPACE -l app=sonic-ai -- curl -f http://localhost:8080/healthz
   \`\`\`

3. **Metrics Not Available:**
   - Check Prometheus configuration
   - Verify service discovery
   - Check pod annotations

### Logs
\`\`\`bash
# View Sonic AI logs
kubectl logs -f -l app=sonic-ai -n $NAMESPACE

# View specific pod logs
kubectl logs -f <pod-name> -n $NAMESPACE
\`\`\`

## Support

For issues or questions about Sonic AI deployment:
- Check the troubleshooting documentation: docs/troubleshooting.md
- Review the deployment logs
- Contact the Sophia AI Intelligence Team

---

**Deployment completed successfully at $(date)**
EOF

    log_success "Deployment report generated: $report_file"
    log_info "Report saved to: $report_file"
}

# Main deployment function
main() {
    log_info "Starting Sonic AI deployment..."
    log_info "Phase 5: Autonomous Deployment and Integration"

    # Run deployment steps
    pre_deployment_checks
    deploy_sonic_ai
    update_prometheus_config
    update_alertmanager_config
    wait_for_deployment
    post_deployment_validation
    setup_monitoring
    generate_deployment_report

    log_success "🎉 Sonic AI deployment completed successfully!"
    log_info ""
    log_info "Sonic AI is now available at:"
    log_info "  - Internal: http://sonic-ai.sophia.svc.cluster.local:8080"
    log_info "  - Health: http://sonic-ai.sophia.svc.cluster.local:8080/healthz"
    log_info "  - API: /api/sonic/* (via ingress)"
    log_info ""
    log_info "Next steps:"
    log_info "1. Test the Sonic AI endpoints"
    log_info "2. Monitor performance via Grafana dashboard"
    log_info "3. Review the deployment report for detailed information"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Sonic AI Deployment Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --dry-run     Show what would be done without making changes"
        echo "  --rollback    Rollback the Sonic AI deployment"
        echo ""
        echo "Environment Variables:"
        echo "  NAMESPACE     Kubernetes namespace (default: sophia)"
        echo "  KUBECONFIG    Path to kubeconfig file"
        echo ""
        exit 0
        ;;
    --dry-run)
        log_info "Running in dry-run mode..."
        log_warning "This is a dry run - no changes will be made"
        # Add dry-run logic here if needed
        exit 0
        ;;
    --rollback)
        log_info "Rolling back Sonic AI deployment..."
        kubectl delete -f k8s-deploy/manifests/sonic-ai.yaml --ignore-not-found=true
        kubectl delete -f k8s-deploy/manifests/sonic-ai-ingress.yaml --ignore-not-found=true
        kubectl delete configmap sonic-ai-prometheus-config -n $NAMESPACE --ignore-not-found=true
        kubectl delete configmap sonic-ai-alerts-config -n $NAMESPACE --ignore-not-found=true
        kubectl delete configmap sonic-ai-grafana-dashboard -n $NAMESPACE --ignore-not-found=true
        log_success "Sonic AI deployment rolled back"
        exit 0
        ;;
    *)
        main
        ;;
esac